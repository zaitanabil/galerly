"""
Gallery management handlers
"""
import os
import uuid
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, photos_table, s3_client, S3_BUCKET, client_favorites_table
from utils.response import create_response
from handlers.subscription_handler import enforce_gallery_limit
from utils.email import send_gallery_shared_email
from utils.cache import cached, invalidate_user_galleries, invalidate_gallery

def enrich_photos_with_any_favorites(photos, gallery):
    """Add is_favorite field to photos - TRUE if ANY client favorited it (for photographer view)"""
    if not photos:
        return photos
    
    try:
        gallery_id = gallery.get('id')
        # Get client emails array
        client_emails = gallery.get('client_emails', [])
        
        if not gallery_id or not client_emails:
            # No clients assigned, no favorites
            for photo in photos:
                photo['is_favorite'] = False
            return photos
        
        # Get favorites from ALL clients
        favorited_photo_ids = set()
        for client_email in client_emails:
            favorites_response = client_favorites_table.query(
                KeyConditionExpression=Key('client_email').eq(client_email.lower()),
                FilterExpression='gallery_id = :gid',
                ExpressionAttributeValues={':gid': gallery_id}
            )
            favorited_photo_ids.update(fav['photo_id'] for fav in favorites_response.get('Items', []))
        
        # Add is_favorite field to each photo
        for photo in photos:
            photo['is_favorite'] = photo['id'] in favorited_photo_ids
        
        return photos
    except Exception as e:
        print(f"Error enriching photos with favorites: {str(e)}")
        # If error, just set all to False
        for photo in photos:
            photo['is_favorite'] = False
        return photos

def handle_list_galleries(user, query_params=None):
    """List all galleries for THIS USER ONLY with optional search and filters"""
    from utils.cache import application_cache, generate_cache_key
    
    # Generate cache key for this request
    user_id = user['id']
    cache_params = query_params or {}
    ck = generate_cache_key('gallery_list', user_id, **cache_params)
    
    # Try to get from cache
    cached_result = application_cache.retrieve(ck)
    if cached_result is not None:
        print(f"✅ Cache HIT: gallery_list for user {user_id}")
        return cached_result
    
    print(f"⚠️  Cache MISS: gallery_list for user {user_id}")
    
    try:
        # Query galleries by user_id (partition key) with projection (only fetch needed fields for list view)
        # This reduces data transfer and improves performance
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id']),
            ProjectionExpression='id, #n, created_at, updated_at, client_emails, cover_photo, #st, photo_count, archived, tags, description',
            ExpressionAttributeNames={
                '#n': 'name',  # 'name' is a reserved word in DynamoDB
                '#st': 'status'  # 'status' is a reserved word in DynamoDB
            }
        )
        
        user_galleries = response.get('Items', [])
        
        # Apply search filter if provided
        if query_params:
            search_query = query_params.get('search', '').strip().lower()
            client_filter = query_params.get('client', '').strip().lower()
            sort_by = query_params.get('sort', 'date_desc')  # date_desc, date_asc, name_asc, name_desc
            
            # Filter by archived status (default: exclude archived)
            include_archived = query_params.get('include_archived', 'false').lower() == 'true'
            if not include_archived:
                user_galleries = [g for g in user_galleries if not g.get('archived', False)]
            
            # Filter by search query (name or description)
            if search_query:
                user_galleries = [
                    g for g in user_galleries
                    if search_query in g.get('name', '').lower() or
                       search_query in g.get('description', '').lower() or
                       search_query in g.get('client_name', '').lower()
                ]
            
            # Filter by client name/email
            if client_filter:
                user_galleries = [
                    g for g in user_galleries
                    if client_filter in g.get('client_name', '').lower() or
                       any(client_filter in email.lower() for email in g.get('client_emails', []))
                ]
            
            # Filter by tags
            tags_filter = query_params.get('tags', '').strip()
            if tags_filter:
                filter_tags = [t.strip().lower() for t in tags_filter.split(',')]
                user_galleries = [
                    g for g in user_galleries
                    if any(tag in [t.lower() for t in g.get('tags', [])] for tag in filter_tags)
                ]
            
            # Sort galleries
            if sort_by == 'date_desc':
                user_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            elif sort_by == 'date_asc':
                user_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=False)
            elif sort_by == 'name_asc':
                user_galleries.sort(key=lambda x: x.get('name', '').lower(), reverse=False)
            elif sort_by == 'name_desc':
                user_galleries.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
        else:
            # Default: Sort by created date (newest first), exclude archived
            user_galleries = [g for g in user_galleries if not g.get('archived', False)]
            user_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        result = create_response(200, {
            'galleries': user_galleries,
            'total': len(user_galleries)
        })
        
        # Cache the result (5 minutes TTL)
        application_cache.store(ck, result, ttl=300)
        
        return result
    except Exception as e:
        print(f"Error listing galleries: {str(e)}")
        return create_response(200, {'galleries': [], 'total': 0})

def handle_create_gallery(user, body):
    """Create new gallery for THIS USER - PHOTOGRAPHERS ONLY"""
    
    # Check if user is a photographer
    if user.get('role') != 'photographer':
        return create_response(403, {'error': 'Only photographers can create galleries'})
    
    # Enforce subscription limits
    allowed, error_message = enforce_gallery_limit(user)
    if not allowed:
        return create_response(403, {'error': error_message})
    
    name = body.get('name', '').strip()
    description = body.get('description', '').strip()
    client_name = body.get('clientName', '').strip()
    
    # Support both single clientEmail (legacy) and clientEmails array (new)
    client_emails = body.get('clientEmails', [])
    if not client_emails and body.get('clientEmail'):
        # Legacy support: convert single email to array
        client_emails = [body.get('clientEmail').strip()]
    
    # Normalize and validate emails
    client_emails = [email.strip().lower() for email in client_emails if email.strip()]
    
    if not name:
        return create_response(400, {'error': 'Gallery name is required'})
    
    if len(name) > 200:
        return create_response(400, {'error': 'Gallery name must be less than 200 characters'})
    
    if len(description) > 5000:
        return create_response(400, {'error': 'Description must be less than 5000 characters'})
    
    if len(client_name) > 100:
        return create_response(400, {'error': 'Client name must be less than 100 characters'})
    
    # Validate all client emails
    for email in client_emails:
        if len(email) > 255:
            return create_response(400, {'error': f'Client email "{email}" must be less than 255 characters'})
    
    gallery_id = str(uuid.uuid4())
    share_token = secrets.token_urlsafe(16)
    current_time = datetime.utcnow().isoformat() + 'Z'
    
    # Get frontend URL from environment
    frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
    
    # ⏰ AUTOMATIC EXPIRATION FOR FREE PLAN
    # Free plan (started pack) galleries ALWAYS expire after 7 days MAXIMUM
    user_plan = user.get('plan', 'free').lower()
    expiry_days = None
    expiry_date = None
    
    if user_plan == 'free':
        # Force 7-day expiration for free users (MAXIMUM, NOT NEGOTIABLE)
        expiry_days = 7
        expiry_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        print(f"🆓 FREE PLAN: Enforcing 7-day maximum expiration (expires: {expiry_date})")
    
    gallery = {
        'user_id': user['id'],  # PARTITION KEY - ensures isolation
        'id': gallery_id,        # SORT KEY
        'galleryId': gallery_id,
        'name': name,
        'client_name': client_name,
        'client_emails': client_emails,
        'description': description,
        'share_token': share_token,
        'share_token_created_at': current_time,  # Track token creation for expiration
        'share_url': f"{frontend_url}/client-gallery?token={share_token}",
        'privacy': body.get('privacy', 'private'),
        'password': body.get('password', ''),
        'allow_downloads': body.get('allowDownload', True),
        'allow_comments': body.get('allowComments', True),
        'expiry_days': expiry_days,  # 7 for free plan, null for paid plans
        'expiry_date': expiry_date,  # ISO timestamp for free plan, null for paid
        'photo_count': 0,
        'view_count': 0,
        'storage_used': 0,
        'tags': body.get('tags', []),  # Gallery tags for organization
        'created_at': current_time,
        'updated_at': current_time
    }
    
    # Store in DynamoDB with user_id partition
    galleries_table.put_item(Item=gallery)
    
    # Send email notification to ALL clients
    # Check notification preferences before sending
    if client_emails:
        try:
            # Check if photographer has gallery_shared notifications enabled
            from handlers.notification_handler import should_send_notification
            
            if should_send_notification(user['id'], 'gallery_shared'):
                photographer_name = user.get('name') or user.get('username', 'Your photographer')
                for client_email in client_emails:
                    try:
                        send_gallery_shared_email(
                            client_email,
                            client_name,
                            photographer_name,
                            name,
                            gallery['share_url'],
                            description
                        )
                    except Exception as e:
                        print(f"Failed to send email to {client_email}: {str(e)}")
            else:
                print(f"ℹ️  Email notification skipped: photographer {user['id']} has 'gallery_shared' disabled")
        except:
            pass  # Don't fail gallery creation if email fails
    
    print(f"✅ Gallery created for user {user['id']}: {gallery_id} with {len(client_emails)} clients")
    # Invalidate user's gallery list cache
    invalidate_user_galleries(user['id'])
    
    return create_response(201, gallery)

def handle_get_gallery(gallery_id, user=None, query_params=None):
    """Get gallery details with optional pagination - CHECK USER OWNERSHIP"""
    from utils.cache import application_cache, generate_cache_key
    
    try:
        if not user:
            return create_response(401, {'error': 'Authentication required'})
        
        # Generate cache key for this request
        user_id = user['id']
        cache_params = query_params or {}
        ck = generate_cache_key('gallery', gallery_id, user_id, **cache_params)
        
        # Try to get from cache
        cached_result = application_cache.retrieve(ck)
        if cached_result is not None:
            print(f"✅ Cache HIT: gallery {gallery_id} for user {user_id}")
            return cached_result
        
        print(f"⚠️  Cache MISS: gallery {gallery_id} for user {user_id}")
        
        # Parse pagination parameters
        page_size = 50  # Default page size
        last_evaluated_key = None
        pagination_requested = False  # Track if pagination params were provided
        
        if query_params:
            try:
                # Check if pagination parameters were explicitly provided
                if 'page_size' in query_params or 'last_key' in query_params:
                    pagination_requested = True
                
                # Enforce min 1, max 100 for page_size
                page_size = max(1, min(int(query_params.get('page_size', 50)), 100))
            except:
                page_size = 50
            
            # Get last evaluated key for pagination
            if 'last_key' in query_params:
                try:
                    import json
                    last_evaluated_key = json.loads(query_params['last_key'])
                except:
                    last_evaluated_key = None
        
        # Query with both partition key (user_id) and sort key (id)
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = response['Item']
        
        # Get photos for this gallery with optimized projection and pagination
        # Only fetch essential fields needed for display
        # Initialize variables before try block to ensure they exist in except block
        gallery_photos = []
        next_key = None
        has_more = False
        
        try:
            query_kwargs = {
                'IndexName': 'GalleryIdIndex',
                'KeyConditionExpression': Key('gallery_id').eq(gallery_id),
                'ProjectionExpression': 'id, gallery_id, #st, created_at, updated_at, thumbnail_url, medium_url, url, title, description, filename, #sz, width, height, favorites',
                'ExpressionAttributeNames': {
                    '#st': 'status',  # reserved word
                    '#sz': 'size'  # reserved word
                },
                'Limit': page_size
            }
            
            # Add pagination key if provided
            if last_evaluated_key:
                query_kwargs['ExclusiveStartKey'] = last_evaluated_key
            
            photos_response = photos_table.query(**query_kwargs)
            gallery_photos = photos_response.get('Items', [])
            gallery_photos.sort(key=lambda x: x.get('created_at', ''))
            
            # Enrich photos with is_favorite field (shows which photos clients favorited)
            gallery_photos = enrich_photos_with_any_favorites(gallery_photos, gallery)
            
            # Pagination metadata
            next_key = photos_response.get('LastEvaluatedKey')
            has_more = next_key is not None
            
        except Exception as e:
            print(f"Error loading photos: {str(e)}")
            gallery_photos = []
            next_key = None
            has_more = False
        
        # Set gallery data (works whether try succeeded or failed)
        gallery['photos'] = gallery_photos
        gallery['photo_count'] = len(gallery_photos)
        
        # Add pagination metadata to response only if pagination was explicitly requested
        response_data = gallery
        if pagination_requested:
            response_data['pagination'] = {
                'page_size': page_size,
                'has_more': has_more,
                'next_key': next_key,
                'returned_count': len(gallery_photos)
            }
        
        result = create_response(200, response_data)
        
        # Cache the result (5 minutes TTL)
        application_cache.store(ck, result, ttl=300)
        
        return result
    except Exception as e:
        print(f"Error getting gallery: {str(e)}")
        return create_response(404, {'error': 'Gallery not found'})

def handle_update_gallery(gallery_id, user, body):
    """Update gallery - VERIFY USER OWNERSHIP"""
    try:
        # Get existing gallery
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found or access denied'})
        
        gallery = response['Item']
        
        # Update fields with validation
        if 'name' in body or 'galleryName' in body:
            name = (body.get('name') or body.get('galleryName', '')).strip()
            if len(name) > 200:
                return create_response(400, {'error': 'Gallery name must be less than 200 characters'})
            gallery['name'] = name
        if 'client_name' in body or 'clientName' in body:
            client_name = (body.get('client_name') or body.get('clientName', '')).strip()
            if len(client_name) > 100:
                return create_response(400, {'error': 'Client name must be less than 100 characters'})
            gallery['client_name'] = client_name
        
        # Handle client_emails array
        if 'client_emails' in body or 'clientEmails' in body:
            client_emails = body.get('client_emails') or body.get('clientEmails', [])
            # Normalize and validate emails
            client_emails = [email.strip().lower() for email in client_emails if email.strip()]
            for email in client_emails:
                if len(email) > 255:
                    return create_response(400, {'error': f'Client email "{email}" must be less than 255 characters'})
            gallery['client_emails'] = client_emails
        if 'description' in body:
            description = body['description'].strip() if isinstance(body['description'], str) else ''
            if len(description) > 5000:
                return create_response(400, {'error': 'Description must be less than 5000 characters'})
            gallery['description'] = description
        if 'privacy' in body:
            gallery['privacy'] = body['privacy']
        if 'password' in body:
            gallery['password'] = body['password']
        if 'allow_downloads' in body or 'allowDownloads' in body:
            val = body.get('allow_downloads') or body.get('allowDownloads')
            gallery['allow_downloads'] = val
        if 'allow_comments' in body or 'allowComments' in body:
            val = body.get('allow_comments') or body.get('allowComments')
            gallery['allow_comments'] = val
        
        # Handle expiry_days and calculate expiry_date
        if 'expiry_days' in body:
            expiry_days = body.get('expiry_days')
            
            # Get user's plan
            user_plan = user.get('plan', 'free').lower()
            
            # ⏰ FREE PLAN RESTRICTION: MAXIMUM 7 DAYS, CANNOT BE EXTENDED
            if user_plan == 'free':
                # Free users are LOCKED to 7 days maximum - cannot extend or set to "never"
                if expiry_days is None or expiry_days == '' or str(expiry_days).lower() == 'never':
                    # Cannot set to "never" - force 7 days
                    gallery['expiry_days'] = 7
                    gallery['expiry_date'] = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
                    print(f"🆓 FREE PLAN: Cannot set to NEVER, enforcing 7-day MAXIMUM")
                else:
                    try:
                        expiry_days_int = int(expiry_days)
                        # Free plan MAXIMUM: 7 days (hard limit)
                        if expiry_days_int > 7:
                            expiry_days_int = 7
                            print(f"🆓 FREE PLAN: Requested {body.get('expiry_days')} days, limiting to 7-day MAXIMUM")
                        
                        if expiry_days_int > 0 and expiry_days_int <= 7:
                            gallery['expiry_days'] = expiry_days_int
                            expiry_date = datetime.utcnow() + timedelta(days=expiry_days_int)
                            gallery['expiry_date'] = expiry_date.isoformat() + 'Z'
                            print(f"✅ Gallery expiry set to {expiry_days_int} days (expires on {gallery['expiry_date']})")
                        else:
                            # Invalid or 0, force 7 days
                            gallery['expiry_days'] = 7
                            gallery['expiry_date'] = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
                    except (ValueError, TypeError):
                        # Invalid value, force 7 days for free plan
                        gallery['expiry_days'] = 7
                        gallery['expiry_date'] = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
                        print(f"⚠️  Invalid expiry_days value: {expiry_days}, enforcing 7-day MAXIMUM for FREE plan")
            else:
                # PLUS/PRO PLANS: Can set to "never" or any valid number
                if expiry_days is None or expiry_days == '' or str(expiry_days).lower() == 'never':
                    gallery['expiry_days'] = None
                    gallery['expiry_date'] = None
                    print(f"✅ Gallery expiry set to NEVER (PLUS/PRO plan)")
                else:
                    try:
                        expiry_days_int = int(expiry_days)
                        if expiry_days_int > 0:
                            gallery['expiry_days'] = expiry_days_int
                            expiry_date = datetime.utcnow() + timedelta(days=expiry_days_int)
                            gallery['expiry_date'] = expiry_date.isoformat() + 'Z'
                            print(f"✅ Gallery expiry set to {expiry_days_int} days (expires on {gallery['expiry_date']})")
                        else:
                            gallery['expiry_days'] = None
                            gallery['expiry_date'] = None
                    except (ValueError, TypeError):
                        gallery['expiry_days'] = None
                        gallery['expiry_date'] = None
                        print(f"⚠️  Invalid expiry_days value: {expiry_days}, setting to NEVER")
        
        if 'tags' in body:
            # Ensure tags is a list
            tags = body.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            gallery['tags'] = tags
        
        gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save back to DynamoDB
        galleries_table.put_item(Item=gallery)
        
        # Invalidate caches for this gallery and user's gallery list
        invalidate_gallery(gallery_id)
        invalidate_user_galleries(user['id'])
        
        return create_response(200, gallery)
    except Exception as e:
        print(f"Error updating gallery: {str(e)}")
        return create_response(500, {'error': 'Failed to update gallery'})

def handle_duplicate_gallery(gallery_id, user, body):
    """Duplicate/clone an existing gallery - VERIFY USER OWNERSHIP"""
    try:
        # Verify ownership and get original gallery
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found or access denied'})
        
        original_gallery = response['Item']
        
        # Check subscription limits
        allowed, error_message = enforce_gallery_limit(user)
        if not allowed:
            return create_response(403, {'error': error_message})
        
        # Create new gallery ID and share token
        new_gallery_id = str(uuid.uuid4())
        new_share_token = secrets.token_urlsafe(16)
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Get new name from body or use default
        new_name = body.get('name', '').strip() or f"{original_gallery.get('name', 'Gallery')} (Copy)"
        
        # Get frontend URL from environment
        frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
        
        # Create duplicate gallery (without photos initially)
        new_gallery = {
            'user_id': user['id'],
            'id': new_gallery_id,
            'galleryId': new_gallery_id,
            'name': new_name,
            'client_name': original_gallery.get('client_name', ''),
            'client_emails': original_gallery.get('client_emails', []),
            'description': original_gallery.get('description', ''),
            'share_token': new_share_token,
            'share_token_created_at': current_time,  # Track token creation for expiration
            'share_url': f"{frontend_url}/client-gallery?token={new_share_token}",
            'privacy': original_gallery.get('privacy', 'private'),
            'password': original_gallery.get('password', ''),
            'allow_downloads': original_gallery.get('allow_downloads', True),  # Standardized to plural
            'allow_comments': original_gallery.get('allow_comments', True),
            'photo_count': 0,
            'view_count': 0,
            'storage_used': 0,
            'tags': original_gallery.get('tags', []),  # Copy tags from original
            'created_at': current_time,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'archived': False  # New gallery is not archived
        }
        
        # Save new gallery
        galleries_table.put_item(Item=new_gallery)
        
        # Optionally copy photos if requested
        copy_photos = body.get('copy_photos', False)
        if copy_photos:
            try:
                photos_response = photos_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery_id)
                )
                copied_photos = 0
                for photo in photos_response.get('Items', []):
                    try:
                        # Create new photo entry pointing to same S3 object
                        new_photo_id = str(uuid.uuid4())
                        new_photo = {
                            'id': new_photo_id,
                            'gallery_id': new_gallery_id,
                            'user_id': user['id'],
                            'url': photo.get('url'),
                            's3_key': photo.get('s3_key'),
                            'filename': photo.get('filename'),
                            'size_mb': photo.get('size_mb', 0),
                            'status': 'pending',  # Reset status for copied photos
                            'created_at': datetime.utcnow().isoformat() + 'Z',
                            'updated_at': datetime.utcnow().isoformat() + 'Z'
                        }
                        photos_table.put_item(Item=new_photo)
                        copied_photos += 1
                    except Exception as e:
                        print(f"⚠️  Error copying photo: {str(e)}")
                
                # Update photo count
                new_gallery['photo_count'] = copied_photos
                galleries_table.put_item(Item=new_gallery)
            except Exception as e:
                print(f"⚠️  Error copying photos: {str(e)}")
        
        print(f"✅ Gallery duplicated: {gallery_id} -> {new_gallery_id}")
        return create_response(201, new_gallery)
    except Exception as e:
        print(f"Error duplicating gallery: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to duplicate gallery'})

def handle_archive_gallery(gallery_id, user, archive=True):
    """Archive or unarchive a gallery - VERIFY USER OWNERSHIP"""
    try:
        # Verify ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found or access denied'})
        
        gallery = response['Item']
        gallery['archived'] = archive
        gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save updated gallery
        galleries_table.put_item(Item=gallery)
        
        action = 'archived' if archive else 'unarchived'
        print(f"✅ Gallery {action}: {gallery_id}")
        return create_response(200, {
            'message': f'Gallery {action} successfully',
            'archived': archive
        })
    except Exception as e:
        print(f"Error archiving gallery: {str(e)}")
        return create_response(500, {'error': f'Failed to {"archive" if archive else "unarchive"} gallery'})

def handle_delete_gallery(gallery_id, user):
    """Delete gallery - VERIFY USER OWNERSHIP"""
    try:
        # Verify ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found or access denied'})
        
        # Delete all photos
        try:
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            for photo in photos_response.get('Items', []):
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET, Key=photo['s3_key'])
                    photos_table.delete_item(Key={'id': photo['id']})
                except:
                    pass
        except:
            pass
        
        # Delete gallery
        galleries_table.delete_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        # Invalidate caches for this gallery and user's gallery list
        invalidate_gallery(gallery_id)
        invalidate_user_galleries(user['id'])
        
        return create_response(200, {'message': 'Gallery deleted successfully'})
    except Exception as e:
        print(f"Error deleting gallery: {str(e)}")
        return create_response(500, {'error': 'Failed to delete gallery'})
