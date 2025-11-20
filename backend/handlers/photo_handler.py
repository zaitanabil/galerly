"""
Photo management handlers
"""
import uuid
import base64
import json
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, photos_table, s3_client, S3_BUCKET, users_table
from utils.response import create_response
from utils.email import send_new_photos_added_email
from utils.duplicate_detector import (
    check_for_duplicates_in_gallery,
    calculate_file_hash,
    get_file_size
)
from utils.image_security import (
    validate_image_data,
    sanitize_image,
    generate_thumbnail,
    ImageSecurityError
)
from utils.cdn_urls import get_photo_urls  # CloudFront CDN URL helper

def handle_check_duplicates(gallery_id, user, event):
    """
    Check if uploaded photo is a duplicate based on METADATA ONLY
    Duplicate = same filename AND same file size
    NO base64 image data needed!
    """
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse body - expect JSON with filename and file_size
        body_str = event.get('body', '')
        if not body_str:
            return create_response(400, {'error': 'No file data provided'})
        
        try:
            body = json.loads(body_str)
            filename = body.get('filename', '')
            file_size = body.get('file_size', 0)
            
            if not filename or not file_size:
                return create_response(400, {'error': 'filename and file_size required'})
            
        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON'})
        
        # Get existing photos in this gallery
        try:
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            existing_photos = photos_response.get('Items', [])
        except Exception as e:
            print(f"Warning: Could not query photos: {str(e)}")
            existing_photos = []
        
        # Check for duplicates: same filename AND same size
        duplicates = []
        for photo in existing_photos:
            if (photo.get('filename', '').lower() == filename.lower() and 
                photo.get('file_size', 0) == file_size):
                duplicates.append({
                    'id': photo.get('id'),
                    'filename': photo.get('filename'),
                    'file_size': photo.get('file_size'),
                    'url': photo.get('url'),
                    'created_at': photo.get('created_at')
                })
        
        # Return duplicate info
        response_data = {
            'filename': filename,
            'file_size': file_size,
            'has_duplicates': len(duplicates) > 0,
            'duplicate_count': len(duplicates),
            'duplicates': duplicates
        }
        
        print(f"✅ Duplicate check for {filename} ({file_size} bytes): {len(duplicates)} duplicates found")
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"❌ Error checking duplicates: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Duplicate check failed: {str(e)}'})

def handle_upload_photo(gallery_id, user, event):
    """Upload photo - VERIFY GALLERY OWNERSHIP"""
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        gallery = response['Item']
        
        # Parse body - expect JSON with base64 data
        body_str = event.get('body', '')
        if not body_str:
            return create_response(400, {'error': 'No file data provided'})
        
        try:
            body = json.loads(body_str)
            filename_from_client = body.get('filename', 'photo.jpg')
            base64_data = body.get('data', '')
            skip_duplicate_check = body.get('skip_duplicate_check', False)  # Allow forcing upload
            
            if not base64_data:
                return create_response(400, {'error': 'No image data in request'})
            
            # Decode base64
            image_data = base64.b64decode(base64_data)
            
            # ==========================================
            # SECURITY: VALIDATE & SANITIZE IMAGE
            # ==========================================
            try:
                # 1. Validate image (check magic bytes, format, dimensions, etc.)
                validation_result = validate_image_data(image_data, filename_from_client)
                print(f"✅ Image validation passed: {validation_result}")
                
                # 2. SANITIZATION DISABLED - Preserve original quality
                # Original sanitization was compressing JPEG files (quality=98)
                # This caused ~50% size reduction (1GB → 505MB)
                # Photographers need TRUE original files without re-encoding
                print(f"ℹ️  Sanitization disabled - preserving original file quality")
                
                # Skip sanitization - use original image data
                # sanitized_data = sanitize_image(image_data, output_format='JPEG', quality=98)
                # image_data = sanitized_data
                
            except ImageSecurityError as security_error:
                print(f"🚨 SECURITY: Image rejected: {str(security_error)}")
                return create_response(400, {
                    'error': 'Image security validation failed',
                    'detail': str(security_error)
                })
            # ==========================================
            
            # Note: No size limit - photographers need full quality
            # Storage limits are enforced at the subscription level
            
        except json.JSONDecodeError:
            return create_response(400, {'error': 'Invalid JSON'})
        except Exception as e:
            return create_response(400, {'error': f'Invalid image data: {str(e)}'})
        
        # Calculate hashes and size for duplicate detection
        file_hash = calculate_file_hash(image_data)
        file_size = get_file_size(image_data)
        size_mb = file_size / (1024 * 1024)  # Convert bytes to MB
        
        # Extract file extension from original filename to preserve format
        import os
        file_extension = os.path.splitext(filename_from_client)[1] or '.jpg'  # Default to .jpg if no extension
        
        photo_id = str(uuid.uuid4())
        s3_key_full = f"{gallery_id}/{photo_id}{file_extension}"
        
        # ⚡ PERFORMANCE FIX: Skip thumbnail generation for faster uploads
        # Thumbnails will be generated on-demand by CloudFront + Lambda@Edge
        print(f"⚡ FAST UPLOAD: Skipping thumbnail generation (CloudFront will generate on-demand)")
        
        # Get proper MIME type from file extension
        from utils.mime_types import get_mime_type
        content_type = get_mime_type(filename_from_client)
        
        # Upload FULL-RES to S3 (original quality for download)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key_full,
            Body=image_data,
            ContentType=content_type
        )
        print(f"✅ Full-res uploaded: {s3_key_full} ({len(image_data):,} bytes, {content_type})")
        
        # Generate CloudFront CDN URLs with automatic resizing
        # URL format: https://cdn.galerly.com/resize/{width}x{height}/{s3_key}
        photo_urls = get_photo_urls(s3_key_full)
        
        # Create photo record with hashes for future duplicate detection
        photo = {
            'id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user['id'],  # Add user_id for security checks
            'filename': filename_from_client,
            's3_key': s3_key_full,
            'url': photo_urls['url'],  # CloudFront URL for original
            'medium_url': photo_urls['medium_url'],  # CloudFront URL for medium (2000x2000)
            'thumbnail_url': photo_urls['thumbnail_url'],  # CloudFront URL for thumbnail (800x600)
            'title': body.get('title', ''),
            'description': body.get('description', ''),
            'tags': body.get('tags', []),  # Photo tags for search
            'status': 'pending',  # Photos start as pending, need approval
            'views': 0,
            'comments': [],  # Empty comments array
            'file_hash': file_hash,  # Store for exact duplicate detection
            'file_size': file_size,  # Store for filename+size duplicate detection (bytes)
            'size_mb': Decimal(str(round(size_mb, 2))),  # Store size in MB for display and storage tracking (use Decimal for DynamoDB)
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        photos_table.put_item(Item=photo)
        
        # Update gallery photo count and storage
        new_photo_count = gallery.get('photo_count', 0) + 1
        current_storage_mb = float(gallery.get('storage_used', 0))
        new_storage_mb = current_storage_mb + size_mb
        
        gallery['photo_count'] = new_photo_count
        gallery['storage_used'] = Decimal(str(round(new_storage_mb, 2)))  # Use Decimal for DynamoDB
        gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        galleries_table.put_item(Item=gallery)
        
        # Regenerate gallery ZIP file (async - don't block upload)
        try:
            from utils.zip_generator import generate_gallery_zip
            # Run in background - Lambda will wait for non-daemon threads
            import threading
            thread = threading.Thread(target=generate_gallery_zip, args=(gallery_id,))
            thread.start()
            print(f"🔄 Started ZIP regeneration for gallery {gallery_id}")
        except Exception as zip_error:
            print(f"⚠️  Failed to regenerate ZIP: {str(zip_error)}")
            # Don't fail upload if ZIP generation fails
        
        # EMAIL NOTIFICATIONS DISABLED FOR AUTO-SEND
        # Photographer must manually send batch notification via "Send Email Notification" button
        # This prevents clients from receiving 100 emails when 100 photos are uploaded
        # Instead, photographer can send ONE email after all uploads are complete
        
        print(f"✅ Photo uploaded: {s3_key_full} ({len(image_data):,} bytes)")
        return create_response(201, photo)
    except Exception as e:
        print(f"❌ Error uploading photo: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Upload failed: {str(e)}'})

def handle_update_photo(photo_id, body, user=None):
    """Update photo status or metadata - ONLY CLIENTS CAN APPROVE"""
    try:
        response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = response['Item']
        gallery_id = photo.get('gallery_id')
        
        if not gallery_id:
            return create_response(400, {'error': 'Photo has no associated gallery'})
        
        # Get gallery to check client_email
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        
        # If updating status to 'approved', ONLY the client can do this
        if 'status' in body and body['status'] == 'approved':
            if not user:
                return create_response(401, {'error': 'Authentication required to approve photos'})
            
            # Check if user is a client (not the photographer)
            user_email = user.get('email', '').lower()
            photographer_user_id = gallery.get('user_id')
            
            # Deny if user is the photographer (owner)
            if user['id'] == photographer_user_id:
                return create_response(403, {'error': 'Only the client can approve photos. Photographers cannot approve their own photos.'})
            
            # Check if user is in client_emails array
            client_emails = gallery.get('client_emails', [])
            
            # Allow if user is one of the clients
            if user_email in [email.lower() for email in client_emails]:
                photo['status'] = 'approved'
                photo['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                photos_table.put_item(Item=photo)
                print(f"✅ Photo {photo_id} approved by client {user_email}")
                return create_response(200, photo)
            else:
                return create_response(403, {'error': 'Only clients assigned to this gallery can approve photos'})
        
        # For other updates (non-status or non-approval), allow photographer to update
        # SECURITY: Verify user owns this photo (if user is provided)
        if user and photo.get('user_id') != user['id']:
            return create_response(403, {'error': 'Access denied: You do not own this photo'})
        
        # Update other fields if provided
        if 'title' in body:
            photo['title'] = body['title']
        if 'description' in body:
            photo['description'] = body['description']
        if 'tags' in body:
            # Ensure tags is a list
            tags = body.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            photo['tags'] = tags
        if 'status' in body:
            photo['status'] = body['status']
        
            photo['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            photos_table.put_item(Item=photo)
        
        if 'status' in body:
            print(f"✅ Photo {photo_id} status updated to {body['status']}")
        
        return create_response(200, photo)
    except Exception as e:
        print(f"❌ Error updating photo: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update photo'})

def handle_add_comment(photo_id, user, body):
    """Add comment to photo - Enhanced with threading, reactions, mentions"""
    try:
        # Get photo
        response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = response['Item']
        
        # Get comment text
        comment_text = body.get('text', '').strip()
        if not comment_text:
            return create_response(400, {'error': 'Comment text required'})
        
        # Parse @mentions from comment text
        import re
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment_text)
        
        # Create comment with enhanced structure
        comment_id = str(uuid.uuid4())
        comment = {
            'id': comment_id,
            'text': comment_text,
            'author': user.get('username', user.get('email', 'Anonymous')),
            'user_id': user['id'],
            'user_email': user.get('email', ''),
            'parent_id': body.get('parent_id'),  # For threaded comments (replies)
            'mentions': mentions,  # List of mentioned usernames
            'reactions': {},  # Format: {'like': [user_ids], 'heart': [user_ids]}
            'is_edited': False,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add to photo's comments list
        if 'comments' not in photo or not isinstance(photo['comments'], list):
            photo['comments'] = []
        
        photo['comments'].append(comment)
        
        # Update photo in DynamoDB
        photos_table.put_item(Item=photo)
        
        # ================================================================
        # NOTIFICATION LOGIC - Two scenarios:
        # ================================================================
        
        # Get gallery to determine photographer and clients
        gallery_id = photo.get('gallery_id')
        if gallery_id:
            try:
                gallery_response = galleries_table.scan(
                    FilterExpression='id = :gid',
                    ExpressionAttributeValues={':gid': gallery_id}
                )
                
                if gallery_response.get('Items'):
                    gallery = gallery_response['Items'][0]
                    photographer_id = gallery.get('user_id')
                    user_email_lower = user.get('email', '').lower()
                    client_emails = [email.lower() for email in gallery.get('client_emails', [])]
                    
                    # SCENARIO 1: CLIENT comments → Notify PHOTOGRAPHER (Client Feedback)
                    if photographer_id and user['id'] != photographer_id and user_email_lower in client_emails:
                        try:
                            from handlers.notification_handler import notify_client_feedback
                            
                            # Get photographer details
                            photographer_response = users_table.get_item(Key={'id': photographer_id})
                            if 'Item' in photographer_response:
                                photographer = photographer_response['Item']
                                photographer_email = photographer.get('email')
                                photographer_name = photographer.get('name') or photographer.get('username', 'Photographer')
                                
                                # Get client name from gallery
                                client_name = gallery.get('client_name', 'Client')
                                gallery_name = gallery.get('name', 'Your gallery')
                                
                                # Build photo URL
                                import os
                                frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
                                photo_url = f"{frontend_url}/gallery?id={gallery_id}&photo={photo_id}"
                                
                                # Send notification (function checks preferences internally)
                                notify_client_feedback(
                                    photographer_id=photographer_id,
                                    photographer_email=photographer_email,
                                    photographer_name=photographer_name,
                                    client_name=client_name,
                                    gallery_name=gallery_name,
                                    gallery_url=photo_url,
                                    rating=None,  # No rating system yet
                                    feedback=comment_text
                                )
                                print(f"✅ Sent 'Client Feedback' notification to photographer {photographer_email}")
                        except Exception as notif_error:
                            print(f"⚠️  Failed to send client feedback notification: {str(notif_error)}")
                    
                    # SCENARIO 2: PHOTOGRAPHER comments → Notify ALL CLIENTS (Custom Message)
                    elif photographer_id and user['id'] == photographer_id:
                        try:
                            from handlers.notification_handler import notify_custom_message
                            
                            # Get photographer details
                            photographer_name = user.get('name') or user.get('username', 'Your photographer')
                            client_name = gallery.get('client_name', 'Client')
                            gallery_name = gallery.get('name', 'Your gallery')
                            
                            # Build photo URL
                            import os
                            frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
                            photo_url = f"{frontend_url}/gallery?id={gallery_id}&photo={photo_id}"
                            
                            # Send to ALL clients
                            for client_email in gallery.get('client_emails', []):
                                try:
                                    notify_custom_message(
                                        user_id=photographer_id,
                                        client_email=client_email,
                                        client_name=client_name,
                                        photographer_name=photographer_name,
                                        subject=f"New message from {photographer_name}",
                                        title=f"Message about {gallery_name}",
                                        message=comment_text,
                                        button_text="View Photo",
                                        button_url=photo_url
                                    )
                                    print(f"✅ Sent 'Custom Message' notification to {client_email}")
                                except Exception as email_error:
                                    print(f"⚠️  Failed to send custom message to {client_email}: {str(email_error)}")
                        except Exception as notif_error:
                            print(f"⚠️  Failed to send custom message notifications: {str(notif_error)}")
            
            except Exception as gallery_error:
                print(f"⚠️  Failed to process notifications: {str(gallery_error)}")
        
        print(f"✅ Comment added to photo {photo_id} by {user.get('email')} (parent: {comment.get('parent_id')})")
        return create_response(201, comment)
        
    except Exception as e:
        print(f"❌ Error adding comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to add comment: {str(e)}'})

def handle_update_comment(photo_id, comment_id, user, body):
    """Update comment (edit text or add/remove reactions)"""
    try:
        # Get photo
        response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = response['Item']
        
        if 'comments' not in photo or not isinstance(photo['comments'], list):
            return create_response(404, {'error': 'Comment not found'})
        
        # Find comment
        comment_index = None
        for idx, comment in enumerate(photo['comments']):
            if comment.get('id') == comment_id:
                comment_index = idx
                break
        
        if comment_index is None:
            return create_response(404, {'error': 'Comment not found'})
        
        comment = photo['comments'][comment_index]
        
        # Get gallery info for permission checks
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': photo.get('gallery_id')}
        )
        gallery = gallery_response.get('Items', [{}])[0] if gallery_response.get('Items') else {}
        is_gallery_owner = gallery.get('user_id') == user['id']
        is_comment_author = comment.get('user_id') == user['id']
        
        # Handle reaction updates (ANYONE can react, no permission check needed)
        if 'reaction' in body:
            reaction_type = body.get('reaction')  # 'like', 'heart', etc.
            action = body.get('action', 'toggle')  # 'add' or 'remove' or 'toggle'
            
            if 'reactions' not in comment:
                comment['reactions'] = {}
            if reaction_type not in comment['reactions']:
                comment['reactions'][reaction_type] = []
            
            user_id = user['id']
            reactions_list = comment['reactions'][reaction_type]
            
            if action == 'toggle':
                # Toggle reaction
                if user_id in reactions_list:
                    reactions_list.remove(user_id)
                else:
                    reactions_list.append(user_id)
            elif action == 'add' and user_id not in reactions_list:
                reactions_list.append(user_id)
            elif action == 'remove' and user_id in reactions_list:
                reactions_list.remove(user_id)
            
            comment['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Handle text update (edit) - ONLY comment author can edit text
        elif 'text' in body:
            if not is_comment_author:
                return create_response(403, {'error': 'Only the comment author can edit the text'})
            
            new_text = body.get('text', '').strip()
            if not new_text:
                return create_response(400, {'error': 'Comment text cannot be empty'})
            
            # Parse @mentions from new text
            import re
            mention_pattern = r'@(\w+)'
            mentions = re.findall(mention_pattern, new_text)
            
            comment['text'] = new_text
            comment['mentions'] = mentions
            comment['is_edited'] = True
            comment['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update photo in DynamoDB
        photos_table.put_item(Item=photo)
        
        print(f"✅ Comment {comment_id} updated by {user.get('email')}")
        return create_response(200, comment)
        
    except Exception as e:
        print(f"❌ Error updating comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to update comment: {str(e)}'})

def handle_delete_comment(photo_id, comment_id, user):
    """Delete comment - Only comment author or gallery owner can delete"""
    try:
        # Get photo
        response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = response['Item']
        
        if 'comments' not in photo or not isinstance(photo['comments'], list):
            return create_response(404, {'error': 'Comment not found'})
        
        # Find comment
        comment_index = None
        comment = None
        for idx, c in enumerate(photo['comments']):
            if c.get('id') == comment_id:
                comment_index = idx
                comment = c
                break
        
        if comment_index is None:
            return create_response(404, {'error': 'Comment not found'})
        
        # Check permissions: only comment author or gallery owner can delete
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': photo.get('gallery_id')}
        )
        gallery = gallery_response.get('Items', [{}])[0] if gallery_response.get('Items') else {}
        is_gallery_owner = gallery.get('user_id') == user['id']
        is_comment_author = comment.get('user_id') == user['id']
        
        if not (is_comment_author or is_gallery_owner):
            return create_response(403, {'error': 'Permission denied: You can only delete your own comments'})
        
        # Remove comment (and all its replies if threaded)
        def remove_comment_and_replies(comments, target_id):
            """Recursively remove comment and all its replies"""
            result = []
            for c in comments:
                if c.get('id') == target_id:
                    continue  # Skip this comment
                if c.get('parent_id') == target_id:
                    # This is a reply to the deleted comment, remove it too
                    continue
                # Recursively clean replies
                result.append(c)
            return result
        
        photo['comments'] = remove_comment_and_replies(photo['comments'], comment_id)
        
        # Update photo in DynamoDB
        photos_table.put_item(Item=photo)
        
        print(f"✅ Comment {comment_id} deleted by {user.get('email')}")
        return create_response(200, {'message': 'Comment deleted successfully'})
        
    except Exception as e:
        print(f"❌ Error deleting comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to delete comment: {str(e)}'})

def handle_search_photos(user, query_params):
    """Search photos by tags, title, description - USER'S PHOTOS ONLY"""
    try:
        # Get user's galleries first
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        user_galleries = galleries_response.get('Items', [])
        gallery_ids = [g['id'] for g in user_galleries]
        
        if not gallery_ids:
            return create_response(200, {'photos': [], 'total': 0})
        
        # Parse search parameters
        search_query = query_params.get('q', '').strip().lower()
        tags_filter = query_params.get('tags', '').strip()
        gallery_id_filter = query_params.get('gallery_id')
        status_filter = query_params.get('status')
        
        # Search photos in user's galleries
        all_photos = []
        for gallery_id in gallery_ids:
            try:
                photos_response = photos_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery_id)
                )
                all_photos.extend(photos_response.get('Items', []))
            except:
                pass
        
        # Apply filters
        filtered_photos = all_photos
        
        # Filter by gallery_id if provided
        if gallery_id_filter:
            filtered_photos = [p for p in filtered_photos if p.get('gallery_id') == gallery_id_filter]
        
        # Filter by status if provided
        if status_filter:
            filtered_photos = [p for p in filtered_photos if p.get('status') == status_filter]
        
        # Filter by search query (title, description)
        if search_query:
            filtered_photos = [
                p for p in filtered_photos
                if search_query in (p.get('title', '') or '').lower() or
                   search_query in (p.get('description', '') or '').lower() or
                   search_query in (p.get('filename', '') or '').lower()
            ]
        
        # Filter by tags if provided
        if tags_filter:
            filter_tags = [t.strip().lower() for t in tags_filter.split(',')]
            filtered_photos = [
                p for p in filtered_photos
                if any(tag in [t.lower() for t in p.get('tags', [])] for tag in filter_tags)
            ]
        
        # Sort by created date (newest first)
        filtered_photos.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return create_response(200, {
            'photos': filtered_photos,
            'total': len(filtered_photos)
        })
    except Exception as e:
        print(f"Error searching photos: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to search photos'})

def handle_delete_photos(gallery_id, user, event):
    """Delete photos (single or batch) - ONLY PHOTOGRAPHER can delete"""
    print(f"🔥 DELETE PHOTOS HANDLER CALLED: gallery_id={gallery_id}, user_id={user.get('id')}")
    
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            print(f"❌ Gallery not found: gallery_id={gallery_id}, user_id={user['id']}")
            return create_response(403, {'error': 'Gallery not found or you do not own this gallery'})
        
        gallery = response['Item']
        print(f"✅ Gallery found: {gallery.get('name')}, photo_count={gallery.get('photo_count')}")
        
        # Parse body - expect JSON with photo_ids array
        body_str = event.get('body', '')
        if not body_str:
            print("❌ No body in request")
            return create_response(400, {'error': 'No photo IDs provided'})
        
        try:
            body = json.loads(body_str)
            photo_ids = body.get('photo_ids', [])
            
            if not photo_ids or not isinstance(photo_ids, list):
                print(f"❌ Invalid photo_ids: {photo_ids}")
                return create_response(400, {'error': 'photo_ids must be a non-empty array'})
            
            print(f"📸 Deleting {len(photo_ids)} photos: {photo_ids}")
            
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in body: {body_str[:100]}")
            return create_response(400, {'error': 'Invalid JSON'})
        
        deleted_count = 0
        failed_count = 0
        failed_photos = []
        total_size_mb_deleted = 0.0  # Track total storage freed
        
        for photo_id in photo_ids:
            try:
                print(f"  Processing photo: {photo_id}")
                
                # Get photo to verify ownership and get S3 key
                photo_response = photos_table.get_item(Key={'id': photo_id})
                
                if 'Item' not in photo_response:
                    print(f"    ❌ Photo not found in DB: {photo_id}")
                    failed_count += 1
                    failed_photos.append({'id': photo_id, 'error': 'Photo not found'})
                    continue
                
                photo = photo_response['Item']
                photo_size_mb = float(photo.get('size_mb', 0))
                print(f"    ✅ Photo found: {photo.get('filename')}, size={photo_size_mb}MB, s3_key={photo.get('s3_key')}")
                
                # Check gallery_id match (always required)
                if photo.get('gallery_id') != gallery_id:
                    print(f"    ❌ Gallery ID mismatch: photo_gallery={photo.get('gallery_id')}, expected={gallery_id}")
                    failed_count += 1
                    failed_photos.append({'id': photo_id, 'error': 'Photo does not belong to this gallery'})
                    continue
                
                # Check user_id if it exists on the photo (for newer photos)
                # For older photos without user_id, gallery ownership check above is sufficient
                photo_user_id = photo.get('user_id')
                if photo_user_id and photo_user_id != user['id']:
                    print(f"    ❌ User ID mismatch: photo_user={photo_user_id}, expected={user['id']}")
                    failed_count += 1
                    failed_photos.append({'id': photo_id, 'error': 'Access denied'})
                    continue
                
                # Delete from S3
                s3_key = photo.get('s3_key')
                if s3_key:
                    try:
                        print(f"    🗑️  Deleting from S3: {s3_key}")
                        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                        print(f"    ✅ S3 deletion successful: {s3_key}")
                    except Exception as s3_error:
                        print(f"    ⚠️  S3 deletion failed for {s3_key}: {str(s3_error)}")
                        # Continue to delete from DB even if S3 fails
                
                # Delete from DynamoDB
                print(f"    🗑️  Deleting from DynamoDB: {photo_id}")
                photos_table.delete_item(Key={'id': photo_id})
                print(f"    ✅ DynamoDB deletion successful: {photo_id}")
                deleted_count += 1
                total_size_mb_deleted += photo_size_mb
                
            except Exception as photo_error:
                print(f"    ❌ Error deleting photo {photo_id}: {str(photo_error)}")
                failed_count += 1
                failed_photos.append({'id': photo_id, 'error': str(photo_error)})
        
        # Update gallery photo count and storage
        if deleted_count > 0:
            new_photo_count = max(0, gallery.get('photo_count', 0) - deleted_count)
            current_storage_mb = float(gallery.get('storage_used', 0))
            new_storage_mb = max(0, current_storage_mb - total_size_mb_deleted)
            
            gallery['photo_count'] = new_photo_count
            gallery['storage_used'] = Decimal(str(round(new_storage_mb, 2)))  # Use Decimal for DynamoDB
            gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            galleries_table.put_item(Item=gallery)
            print(f"✅ Updated gallery: photo_count={new_photo_count}, storage={new_storage_mb}MB (freed {total_size_mb_deleted}MB)")
            
            # Regenerate gallery ZIP file (async - don't block deletion)
            try:
                from utils.zip_generator import generate_gallery_zip
                # Run in background - Lambda will wait for non-daemon threads
                import threading
                thread = threading.Thread(target=generate_gallery_zip, args=(gallery_id,))
                thread.start()
                print(f"🔄 Started ZIP regeneration for gallery {gallery_id}")
            except Exception as zip_error:
                print(f"⚠️  Failed to regenerate ZIP: {str(zip_error)}")
                # Don't fail deletion if ZIP generation fails
        
        response_data = {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'total': len(photo_ids),
            'message': f'Successfully deleted {deleted_count} photo(s)'
        }
        
        if failed_photos:
            response_data['failed_photos'] = failed_photos
        
        print(f"✅ Delete operation complete: deleted={deleted_count}, failed={failed_count}")
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"❌ Error in batch delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Batch delete failed: {str(e)}'})


def handle_send_batch_notification(gallery_id, user):
    """
    Send ONE batch email notification to all clients about new photos
    Called manually by photographer after uploading multiple photos
    """
    print(f"📧 BATCH EMAIL NOTIFICATION: gallery_id={gallery_id}, user_id={user.get('id')}")
    
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            print(f"❌ Gallery not found or access denied")
            return create_response(403, {'error': 'Gallery not found or access denied'})
        
        gallery = response['Item']
        photo_count = gallery.get('photo_count', 0)
        
        if photo_count == 0:
            return create_response(400, {'error': 'Cannot send notification for empty gallery'})
        
        # Get client emails and validate them
        client_emails = gallery.get('client_emails', [])
        print(f"📬 Raw client_emails from gallery: {client_emails}")
        
        # Filter out empty strings and validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_emails = []
        invalid_emails = []
        
        for email in client_emails:
            email_str = str(email).strip().lower()
            if email_str and re.match(email_pattern, email_str):
                valid_emails.append(email_str)
            else:
                invalid_emails.append(email_str)
                print(f"⚠️  Invalid email address: '{email_str}'")
        
        if invalid_emails:
            print(f"❌ Found {len(invalid_emails)} invalid email(s): {invalid_emails}")
        
        if not valid_emails:
            return create_response(400, {
                'error': 'No valid client email addresses found',
                'invalid_emails': invalid_emails,
                'hint': 'Please add valid email addresses in gallery settings'
            })
        
        print(f"✅ Found {len(valid_emails)} valid email address(es): {valid_emails}")
        
        # Check if photographer has notifications enabled
        from handlers.notification_handler import should_send_notification
        
        if not should_send_notification(user['id'], 'new_photos_added'):
            print(f"ℹ️  Email notification disabled by photographer")
            return create_response(400, {
                'error': 'Email notifications are disabled in your settings',
                'hint': 'Enable notifications in your profile settings'
            })
        
        # Get photographer name
        photographer_name = user.get('name') or user.get('username', 'Your photographer')
        gallery_name = gallery.get('name', 'Gallery')
        gallery_url = gallery.get('share_url', '')
        client_name = gallery.get('client_name', '')
        
        print(f"📧 Sending emails:")
        print(f"   From: {photographer_name}")
        print(f"   Gallery: {gallery_name}")
        print(f"   URL: {gallery_url}")
        print(f"   Photos: {photo_count}")
        
        # Send ONE email to each client
        success_count = 0
        failed_emails = []
        
        for client_email in valid_emails:
            try:
                print(f"  📤 Sending to: {client_email}")
                email_sent = send_new_photos_added_email(
                    client_email,
                    client_name,
                    photographer_name,
                    gallery_name,
                    gallery_url,
                    photo_count
                )
                
                if email_sent:
                    success_count += 1
                    print(f"  ✅ Email sent to {client_email}")
                else:
                    failed_emails.append(client_email)
                    print(f"  ❌ Email failed to send to {client_email} (send_email returned False)")
                    
            except Exception as email_error:
                print(f"  ❌ Exception sending email to {client_email}: {str(email_error)}")
                import traceback
                traceback.print_exc()
                failed_emails.append(client_email)
        
        response_data = {
            'success': True,
            'emails_sent': success_count,
            'emails_failed': len(failed_emails),
            'total_clients': len(valid_emails),
            'message': f'Notification sent to {success_count} client(s)'
        }
        
        if failed_emails:
            response_data['failed_emails'] = failed_emails
            response_data['warning'] = f'Failed to send to {len(failed_emails)} email(s)'
        
        if invalid_emails:
            response_data['invalid_emails'] = invalid_emails
            response_data['warning'] = f'{len(invalid_emails)} invalid email address(es) in gallery settings'
        
        print(f"✅ Batch notification complete: sent={success_count}, failed={len(failed_emails)}, invalid={len(invalid_emails)}")
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"❌ Error sending batch notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to send notification: {str(e)}'})
