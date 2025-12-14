"""
Gallery management handlers
"""
import os
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, photos_table, s3_client, S3_BUCKET, client_favorites_table
from utils.response import create_response
from handlers.subscription_handler import enforce_gallery_limit
from utils.email import send_gallery_shared_email
from utils.gallery_layouts import get_layout, get_all_layouts, get_layouts_by_category, get_layout_categories, validate_layout_photos
from utils.gallery_layouts import get_all_layouts, get_layout, get_layouts_by_category, get_layout_categories
from utils.plan_enforcement import require_role, require_plan  # Added require_plan

def enrich_photos_with_any_favorites(photos, gallery, photographer_email=None):
    """Add is_favorite field and favorites_count to photos - TRUE if ANY client (or photographer) favorited it"""
    if not photos:
        return photos
    
    try:
        gallery_id = gallery.get('id')
        # Get client emails array
        client_emails = gallery.get('client_emails', [])
        
        # Add photographer email to the list to check if they also favorited
        emails_to_check = set(client_emails)
        if photographer_email:
            emails_to_check.add(photographer_email.lower())
        
        emails_list = list(emails_to_check)
        
        if not gallery_id or not emails_list:
            # No clients/emails assigned, no favorites
            for photo in photos:
                photo['is_favorite'] = False
                photo['favorites_count'] = 0
            return photos
        
        # Get favorites from ALL clients + photographer
        favorited_photo_ids = set()
        photo_fav_counts = {}  # Map photo_id -> count

        for email in emails_list:
            favorites_response = client_favorites_table.query(
                KeyConditionExpression=Key('client_email').eq(email.lower()),
                FilterExpression='gallery_id = :gid',
                ExpressionAttributeValues={':gid': gallery_id}
            )
            
            for fav in favorites_response.get('Items', []):
                pid = fav['photo_id']
                favorited_photo_ids.add(pid)
                photo_fav_counts[pid] = photo_fav_counts.get(pid, 0) + 1
        
        # Add is_favorite and favorites_count fields to each photo
        for photo in photos:
            pid = photo['id']
            photo['is_favorite'] = pid in favorited_photo_ids
            photo['favorites_count'] = photo_fav_counts.get(pid, 0)
        
        return photos
    except Exception as e:
        print(f"Error enriching photos with favorites: {str(e)}")
        # If error, just set all to False/0
        for photo in photos:
            photo['is_favorite'] = False
            photo['favorites_count'] = 0
        return photos

@require_role('photographer')
def handle_list_galleries(user, query_params=None):
    """List all galleries for THIS USER ONLY with optional search and filters"""
    try:
        # Query galleries by user_id (partition key) with projection (only fetch needed fields for list view)
        # This reduces data transfer and improves performance
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id']),
            ProjectionExpression='id, #n, created_at, updated_at, client_name, client_emails, cover_photo, thumbnail_url, cover_photo_url, #st, photo_count, archived, tags, description',
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
        
        return create_response(200, {
            'galleries': user_galleries,
            'total': len(user_galleries)
        })
    except Exception as e:
        print(f"Error listing galleries: {str(e)}")
        return create_response(200, {'galleries': [], 'total': 0})

@require_role('photographer')
def handle_create_gallery(user, body):
    """Create new gallery for THIS USER - PHOTOGRAPHERS ONLY"""
    
    # Role check handled by @require_role decorator
    
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
    current_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
    
    # Get frontend URL from environment
    frontend_url = os.environ.get('FRONTEND_URL')
    
    # Check plan features for edit requests
    from handlers.subscription_handler import get_user_features
    features, _, _ = get_user_features(user)
    
    # Default to True if allowed by plan, False if not
    allow_edits_requested = body.get('allowEdits', True)
    allow_edits = False  # Default for free plan
    
    if allow_edits_requested:
        if features.get('edit_requests'):
            allow_edits = True
        # If Free plan tries to enable, silently disable (no error on creation)
    
    # No expiration for galleries - they never expire
    # Only storage quota matters
    
    # Layout configuration - photographers can choose a predefined layout
    layout_id = body.get('layout_id', 'grid_classic')  # Default to classic grid
    layout_config = body.get('layout_config', {})  # Custom layout configuration if needed
    
    gallery = {
        'user_id': user['id'],  # PARTITION KEY - ensures isolation
        'id': gallery_id,        # SORT KEY
        'galleryId': gallery_id,
        'name': name,
        'client_name': client_name,
        'client_emails': client_emails,
        'description': description,
            'share_token': share_token,
            'share_token_created_at': current_time,
            'share_url': f"{frontend_url}/client-gallery?token={share_token}",
        'privacy': body.get('privacy', 'private'),
        'password': body.get('password', ''),
        'allow_downloads': body.get('allowDownload', True),
        'allow_comments': body.get('allowComments', True),
        'allow_edits': allow_edits,  # Use plan-checked value
        'layout_id': layout_id,  # Predefined layout template
        'layout_config': layout_config,  # Custom layout settings
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
                            description,
                            user_id=user['id']  # Pass user_id for custom templates
                        )
                    except Exception as e:
                        print(f"Failed to send email to {client_email}: {str(e)}")
            else:
                print(f"Email notification skipped: photographer {user['id']} has 'gallery_shared' disabled")
        except:
            pass  # Don't fail gallery creation if email fails
    
    print(f"Gallery created for user {user['id']}: {gallery_id} with {len(client_emails)} clients")
    
    return create_response(201, gallery)

def handle_get_gallery(gallery_id, user=None, query_params=None):
    """Get gallery details with optional pagination - CHECK USER OWNERSHIP"""
    try:
        if not user:
            return create_response(401, {'error': 'Authentication required'})
        
        # Parse pagination parameters
        # Get from environment at runtime
        page_size = int(os.environ.get('DEFAULT_PAGE_SIZE'))
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
                page_size = int(os.environ.get('DEFAULT_PAGE_SIZE'))
            
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
                'ProjectionExpression': 'id, gallery_id, #st, created_at, updated_at, thumbnail_url, medium_url, #url, original_download_url, original_filename, title, description, filename, #sz, width, height, favorites, comments, #typ, duration_seconds, duration_minutes, codec',
                'ExpressionAttributeNames': {
                    '#st': 'status',  # reserved word
                    '#sz': 'size',  # reserved word
                    '#url': 'url',  # reserved word
                    '#typ': 'type'  # Include type field for video detection
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
            gallery_photos = enrich_photos_with_any_favorites(gallery_photos, gallery, user.get('email'))
            
            # Ensure favorites_count is not negative
            for p in gallery_photos:
                if p.get('favorites_count', 0) < 0:
                    p['favorites_count'] = 0
            
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
        
        # Inject Plan-based Features (Branding only - favorites are now free for all)
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        gallery['hide_branding'] = features.get('remove_branding', False)
        # Client favorites are now available to all plans - no restriction needed
        
        # Override allow_edits if plan doesn't support it
        if gallery.get('allow_edits') and not features.get('edit_requests'):
            gallery['allow_edits'] = False
        
        # SELF-HEALING: Verify and fix photo_count if needed
        # This ensures the dashboard and list views show the correct number
        try:
            count_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id),
                Select='COUNT'
            )
            actual_count = count_response.get('Count', 0)
            
            # If stored count is different (or missing), update it in DB
            stored_count = gallery.get('photo_count')
            update_updates = []
            update_values = {}
            
            if stored_count != actual_count:
                print(f"Fixing photo count for gallery {gallery_id}: {stored_count} -> {actual_count}")
                gallery['photo_count'] = actual_count
                update_updates.append("photo_count = :c")
                update_values[':c'] = actual_count

            # Check if thumbnail_url is missing but we have photos
            if not gallery.get('thumbnail_url') and gallery_photos:
                 # Find first photo with thumbnail
                 for p in gallery_photos:
                     if p.get('thumbnail_url'):
                         print(f"Fixing thumbnail_url for gallery {gallery_id}")
                         gallery['thumbnail_url'] = p['thumbnail_url'] # Update local object
                         update_updates.append("thumbnail_url = :t")
                         update_values[':t'] = p['thumbnail_url']
                         break
            
            # Check if cover_photo_url is missing but we have photos
            if not gallery.get('cover_photo_url') and gallery_photos:
                 # Find first photo with medium_url or large_url
                 for p in gallery_photos:
                     cover = p.get('large_url') or p.get('medium_url') or p.get('url')
                     if cover:
                         print(f"Fixing cover_photo_url for gallery {gallery_id}")
                         gallery['cover_photo_url'] = cover
                         update_updates.append("cover_photo_url = :c")
                         update_values[':c'] = cover
                         break
            
            if update_updates:
                galleries_table.update_item(
                    Key={'user_id': user['id'], 'id': gallery_id},
                    UpdateExpression="SET " + ", ".join(update_updates),
                    ExpressionAttributeValues=update_values
                )
        except Exception as e:
            print(f"Failed to verify photo count: {e}")
            # Fallback: if photo_count is missing, use len of fetched photos (better than nothing)
            if 'photo_count' not in gallery:
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
        
        return create_response(200, response_data)
    except Exception as e:
        print(f"Error getting gallery: {str(e)}")
        return create_response(404, {'error': 'Gallery not found'})

@require_role('photographer')
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
        if 'allow_edits' in body or 'allowEdits' in body:
            val = body.get('allow_edits') or body.get('allowEdits')
            # Check plan permission for edit requests
            if val:  # Only check if trying to enable
                from handlers.subscription_handler import get_user_features
                features, _, _ = get_user_features(user)
                if not features.get('edit_requests'):
                    return create_response(403, {
                        'error': 'Edit requests are available on Starter, Plus, Pro, and Ultimate plans.',
                        'upgrade_required': True,
                        'required_feature': 'edit_requests'
                    })
            gallery['allow_edits'] = val
        if 'tags' in body:
            # Support tags array for gallery organization
            tags = body.get('tags', [])
            if isinstance(tags, list):
                gallery['tags'] = tags
            else:
                gallery['tags'] = []
        
        # SEO Settings (Pro Feature)
        if 'seo' in body:
            seo_data = body.get('seo', {})
            # Only check permissions if user is actually trying to update SEO data
            # (not just passing empty seo object)
            has_seo_content = (
                seo_data.get('title') or 
                seo_data.get('description') or 
                seo_data.get('slug')
            )
            
            if has_seo_content:
                from handlers.subscription_handler import get_user_features
                features, _, _ = get_user_features(user)
                
                if not features.get('seo_tools'):
                     return create_response(403, {
                         'error': 'SEO tools are available on Pro and Ultimate plans.',
                         'upgrade_required': True
                     })
            
            # Update SEO fields if provided
            if seo_data.get('title') is not None:
                gallery['seo_title'] = str(seo_data.get('title', '')).strip()
            if seo_data.get('description') is not None:
                gallery['seo_description'] = str(seo_data.get('description', '')).strip()
            
            # Slug handling
            new_slug = str(seo_data.get('slug', '')).strip().lower()
            if new_slug and new_slug != gallery.get('slug'):
                import re
                if not re.match(r'^[a-z0-9-]+$', new_slug):
                     return create_response(400, {'error': 'Slug must contain only lowercase letters, numbers, and hyphens'})
                
                # Check uniqueness (scan is expensive but slugs are rare/Pro only feature)
                # Ideally use a separate GSI or table for slugs
                scan_resp = galleries_table.scan(
                    FilterExpression='slug = :s',
                    ExpressionAttributeValues={':s': new_slug}
                )
                if scan_resp.get('Count', 0) > 0:
                    # Check if it's the same gallery
                    if scan_resp['Items'][0]['id'] != gallery_id:
                        return create_response(409, {'error': 'This URL slug is already taken.'})
                
                gallery['slug'] = new_slug
        
        if 'tags' in body:
            # Ensure tags is a list
            tags = body.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            gallery['tags'] = tags
        
        # Layout configuration
        if 'layout_id' in body:
            from utils.gallery_layouts import get_layout
            layout_id = body.get('layout_id')
            layout = get_layout(layout_id)
            if not layout:
                return create_response(400, {'error': f'Invalid layout_id: {layout_id}'})
            gallery['layout_id'] = layout_id
        
        if 'layout_config' in body:
            gallery['layout_config'] = body.get('layout_config', {})
        
        gallery['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Save back to DynamoDB
        galleries_table.put_item(Item=gallery)
        
        return create_response(200, gallery)
    except Exception as e:
        print(f"Error updating gallery: {str(e)}")
        return create_response(500, {'error': 'Failed to update gallery'})

@require_role('photographer')
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
        current_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Get new name from body or use default
        new_name = body.get('name', '').strip() or f"{original_gallery.get('name', 'Gallery')} (Copy)"
        
        frontend_url = os.environ.get('FRONTEND_URL')
        
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
            'share_token_created_at': current_time,
            'share_url': f"{frontend_url}/client-gallery?token={new_share_token}",
            'privacy': original_gallery.get('privacy', 'private'),
            'password': original_gallery.get('password', ''),
            'allow_downloads': original_gallery.get('allow_downloads', True),  # Standardized to plural
            'allow_comments': original_gallery.get('allow_comments', True),
            'allow_edits': original_gallery.get('allow_edits', True),
            'photo_count': 0,
            'view_count': 0,
            'storage_used': 0,
            'tags': original_gallery.get('tags', []),  # Copy tags from original
            'created_at': current_time,
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
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
                            'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
                            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                        }
                        photos_table.put_item(Item=new_photo)
                        copied_photos += 1
                    except Exception as e:
                        print(f" Error copying photo: {str(e)}")
                
                # Update photo count
                new_gallery['photo_count'] = copied_photos
                galleries_table.put_item(Item=new_gallery)
            except Exception as e:
                print(f" Error copying photos: {str(e)}")
        
        print(f"Gallery duplicated: {gallery_id} -> {new_gallery_id}")
        return create_response(201, new_gallery)
    except Exception as e:
        print(f"Error duplicating gallery: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to duplicate gallery'})

@require_role('photographer')
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
        gallery['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Save updated gallery
        galleries_table.put_item(Item=gallery)
        
        action = 'archived' if archive else 'unarchived'
        print(f"Gallery {action}: {gallery_id}")
        return create_response(200, {
            'message': f'Gallery {action} successfully',
            'archived': archive
        })
    except Exception as e:
        print(f"Error archiving gallery: {str(e)}")
        return create_response(500, {'error': f'Failed to {"archive" if archive else "unarchive"} gallery'})

@require_role('photographer')
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
        
        
        return create_response(200, {'message': 'Gallery deleted successfully'})
    except Exception as e:
        print(f"Error deleting gallery: {str(e)}")
        return create_response(500, {'error': 'Failed to delete gallery'})

@require_plan(feature='raw_vault')
@require_role('photographer')
def handle_archive_originals(gallery_id, user):
    """
    Move original files (RAWs) to Glacier Vault
    Ultimate Plan Feature
    """
    try:
        # Plan check handled by @require_plan decorator
        
        # Get Gallery Photos
        photos_response = photos_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        
        items = photos_response.get('Items', [])
        archived_count = 0
        
        for photo in items:
            original_key = photo.get('original_s3_key')
            # Only archive explicit originals (likely RAWs), not the main display/converted JPEG if it's the same
            if original_key and original_key != photo.get('s3_key'):
                try:
                    # Move to Glacier Instant Retrieval
                    # We use copy_object to change storage class in place
                    s3_client.copy_object(
                        Bucket=S3_BUCKET,
                        CopySource={'Bucket': S3_BUCKET, 'Key': original_key},
                        Key=original_key,
                        StorageClass='GLACIER_IR',
                        MetadataDirective='COPY',
                        TaggingDirective='COPY'
                    )
                    archived_count += 1
                except Exception as s3_e:
                    print(f"Failed to archive {original_key}: {s3_e}")
        
        return create_response(200, {
            'message': f'Successfully moved {archived_count} files to RAW Vault (Glacier).',
            'archived_count': archived_count
        })
        
    except Exception as e:
        print(f"Error archiving originals: {str(e)}")
        return create_response(500, {'error': 'Failed to archive files'})


def handle_list_layouts(query_params=None):
    """
    List all available gallery layouts
    Can be filtered by category
    """
    try:
        category = query_params.get('category') if query_params else None
        
        if category:
            layouts = get_layouts_by_category(category)
        else:
            layouts = get_all_layouts()
        
        # Convert to list format for API response
        layouts_list = []
        for layout_id, layout_data in layouts.items():
            layouts_list.append({
                'id': layout_id,
                'name': layout_data['name'],
                'description': layout_data['description'],
                'category': layout_data['category'],
                'total_slots': layout_data['total_slots'],
                'slots': layout_data['slots'],  # Include slots for preview rendering
                'preview_image': layout_data.get('preview_image'),
                'scroll_mode': layout_data.get('scroll_mode'),
                'positioning': layout_data.get('positioning', 'grid')
            })
        
        return create_response(200, {
            'layouts': layouts_list,
            'categories': get_layout_categories(),
            'total': len(layouts_list)
        })
    except Exception as e:
        print(f"Error listing layouts: {str(e)}")
        return create_response(500, {'error': 'Failed to list layouts'})


def handle_get_layout(layout_id):
    """Get detailed layout information including slot configuration"""
    try:
        layout = get_layout(layout_id)
        
        if not layout:
            return create_response(404, {'error': f'Layout not found: {layout_id}'})
        
        return create_response(200, {
            'id': layout_id,
            **layout
        })
    except Exception as e:
        print(f"Error getting layout: {str(e)}")
        return create_response(500, {'error': 'Failed to get layout'})
