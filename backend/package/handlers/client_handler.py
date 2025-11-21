"""
Client gallery access handlers
"""
import secrets
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, photos_table, users_table, client_favorites_table
from utils.response import create_response

# Token expiration: 7 days (Swiss law compliance)
TOKEN_EXPIRATION_DAYS = 7

def is_token_expired(token_created_at):
    """Check if a share token is expired (older than 7 days)"""
    if not token_created_at:
        return True  # No creation date = expired
    
    try:
        created_date = datetime.fromisoformat(token_created_at.replace('Z', ''))
        age = datetime.utcnow() - created_date
        return age > timedelta(days=TOKEN_EXPIRATION_DAYS)
    except Exception as e:
        print(f"Error checking token expiration: {str(e)}")
        return True  # If error, consider expired for security

def regenerate_gallery_token(gallery):
    """Regenerate expired share token for a gallery"""
    try:
        new_token = secrets.token_urlsafe(16)
        current_time = datetime.utcnow().isoformat() + 'Z'
        frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
        new_share_url = f"{frontend_url}/client-gallery?token={new_token}"
        
        # Update gallery with new token
        galleries_table.update_item(
            Key={
                'user_id': gallery['user_id'],
                'id': gallery['id']
            },
            UpdateExpression='SET share_token = :token, share_token_created_at = :created, share_url = :url, updated_at = :updated',
            ExpressionAttributeValues={
                ':token': new_token,
                ':created': current_time,
                ':url': new_share_url,
                ':updated': current_time
            }
        )
        
        print(f"✅ Regenerated token for gallery: {gallery.get('name')} (ID: {gallery['id']})")
        
        # Update the gallery object with new values
        gallery['share_token'] = new_token
        gallery['share_token_created_at'] = current_time
        gallery['share_url'] = new_share_url
        
        return gallery
    except Exception as e:
        print(f"❌ Error regenerating token: {str(e)}")
        raise

def enrich_photos_with_favorites(photos, client_email, gallery_id):
    """Add is_favorite field to each photo based on client_favorites_table"""
    if not client_email or not photos:
        return photos
    
    try:
        # Get all favorites for this client and gallery
        favorites_response = client_favorites_table.query(
            KeyConditionExpression=Key('client_email').eq(client_email.lower()),
            FilterExpression='gallery_id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        favorited_photo_ids = {fav['photo_id'] for fav in favorites_response.get('Items', [])}
        
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

def handle_client_galleries(user):
    """Get all galleries where client has access (client in client_emails array)"""
    try:
        # Scan all galleries and filter where user email is in client_emails
        response = galleries_table.scan()
        all_galleries = response.get('Items', [])
        
        # Filter galleries where user email is in client_emails array (or legacy client_email)
        client_galleries = []
        user_email = user['email'].lower()
        
        for gallery in all_galleries:
            # Check both client_emails array (new) and client_email (legacy)
            client_emails = gallery.get('client_emails', [])
            legacy_email = gallery.get('client_email', '').lower()
            
            # Add legacy email to array for unified checking
            if legacy_email and legacy_email not in client_emails:
                client_emails = client_emails + [legacy_email]
            
            # Check if user email is in the list
            if user_email in [email.lower() for email in client_emails]:
                # Get photographer info
                try:
                    photographer_id = gallery.get('user_id')
                    photographer_response = users_table.scan(
                        FilterExpression='id = :id',
                        ExpressionAttributeValues={':id': photographer_id}
                    )
                    photographers = photographer_response.get('Items', [])
                    if photographers:
                        photographer = photographers[0]
                        gallery['photographer_name'] = photographer.get('name') or photographer.get('username') or 'Unknown'
                        gallery['photographer_id'] = photographer['id']
                    else:
                        gallery['photographer_name'] = 'Unknown Photographer'
                        gallery['photographer_id'] = photographer_id
                except Exception as e:
                    print(f"Error looking up photographer: {str(e)}")
                    gallery['photographer_name'] = 'Unknown Photographer'
                    gallery['photographer_id'] = gallery.get('user_id')
                
                # Get photos for gallery
                try:
                    photos_response = photos_table.query(
                        IndexName='GalleryIdIndex',
                        KeyConditionExpression=Key('gallery_id').eq(gallery['id'])
                    )
                    gallery_photos = photos_response.get('Items', [])
                    
                    # Enrich photos with is_favorite field for this client
                    gallery_photos = enrich_photos_with_favorites(gallery_photos, user['email'], gallery['id'])
                    
                    # Show ALL photos (pending + approved) - clients need to approve them
                    gallery['photos'] = gallery_photos
                    gallery['photo_count'] = len(gallery_photos)
                    
                    # Set cover image
                    if gallery_photos:
                        # Prefer approved photo as cover, fallback to first photo
                        approved_photos = [p for p in gallery_photos if p.get('status') == 'approved']
                        if approved_photos:
                            gallery['cover_image'] = approved_photos[0].get('url')
                        else:
                            gallery['cover_image'] = gallery_photos[0].get('url')
                except:
                    gallery['photos'] = []
                    gallery['photo_count'] = 0
                
                client_galleries.append(gallery)
        
        # Sort by created date (newest first)
        client_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return create_response(200, {
            'galleries': client_galleries,
            'total': len(client_galleries)
        })
    except Exception as e:
        print(f"❌ Error getting client galleries: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load galleries'})

def handle_get_client_gallery(gallery_id, user):
    """Get single gallery for client - CHECK CLIENT EMAIL ACCESS"""
    try:
        # Scan for the gallery (since we don't know the user_id/photographer)
        response = galleries_table.scan(
            FilterExpression='id = :gallery_id',
            ExpressionAttributeValues={':gallery_id': gallery_id}
        )
        
        galleries = response.get('Items', [])
        if not galleries:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = galleries[0]
        user_email = user['email'].lower()
        
        # Check if client has access (user email in client_emails array or legacy client_email)
        client_emails = gallery.get('client_emails', [])
        legacy_email = gallery.get('client_email', '').lower()
        
        # Add legacy email to array for unified checking
        if legacy_email and legacy_email not in client_emails:
            client_emails = client_emails + [legacy_email]
        
        # Check access
        if user_email not in [email.lower() for email in client_emails]:
            return create_response(403, {'error': 'Access denied. This gallery is not shared with you.'})
        
        # Get photographer info
        try:
            photographer_id = gallery.get('user_id')
            photographer_response = users_table.scan(
                FilterExpression='id = :id',
                ExpressionAttributeValues={':id': photographer_id}
            )
            photographers = photographer_response.get('Items', [])
            if photographers:
                photographer = photographers[0]
                gallery['photographer_name'] = photographer.get('name') or photographer.get('username')
                gallery['photographer_id'] = photographer['id']
            else:
                gallery['photographer_name'] = 'Unknown Photographer'
                gallery['photographer_id'] = photographer_id
        except:
            gallery['photographer_name'] = 'Unknown Photographer'
            gallery['photographer_id'] = gallery.get('user_id')
        
        # Get ALL photos (pending + approved)
        try:
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            gallery_photos = photos_response.get('Items', [])
            gallery_photos.sort(key=lambda x: x.get('created_at', ''))
            
            # Enrich photos with is_favorite field for this client
            gallery_photos = enrich_photos_with_favorites(gallery_photos, user['email'], gallery_id)
            
            gallery['photos'] = gallery_photos
            gallery['photo_count'] = len(gallery_photos)
        except Exception as e:
            print(f"Error loading photos: {str(e)}")
            gallery['photos'] = []
            gallery['photo_count'] = 0
        
        return create_response(200, gallery)
    except Exception as e:
        print(f"Error getting client gallery: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load gallery'})

def handle_get_client_gallery_by_token(share_token):
    """Get gallery by share token - PUBLIC ACCESS (no auth required)"""
    try:
        # Scan for gallery with matching share_token
        response = galleries_table.scan(
            FilterExpression='share_token = :token',
            ExpressionAttributeValues={':token': share_token}
        )
        
        galleries = response.get('Items', [])
        if not galleries:
            return create_response(404, {'error': 'Gallery not found or link is invalid'})
        
        gallery = galleries[0]
        gallery_id = gallery['id']
        
        # Check if token is expired
        token_created_at = gallery.get('share_token_created_at')
        if is_token_expired(token_created_at):
            # Token expired - regenerate it
            try:
                gallery = regenerate_gallery_token(gallery)
                
                # Return error with new URL so photographer can share updated link
                # But still show the gallery to avoid breaking existing experience
                print(f"⚠️ Token expired for gallery {gallery_id}, regenerated new token")
                
                # Note: We still serve the gallery but mark token as expired
                # The photographer will need to share the new URL
                gallery['token_expired'] = True
                gallery['message'] = 'This share link has expired. A new link has been generated.'
            except Exception as e:
                print(f"Error regenerating token: {str(e)}")
                # If regeneration fails, still return 404
                return create_response(404, {
                    'error': 'This share link has expired. Please request a new link from the photographer.'
                })
        
        # Get photographer info
        try:
            photographer_id = gallery.get('user_id')
            photographer_response = users_table.scan(
                FilterExpression='id = :id',
                ExpressionAttributeValues={':id': photographer_id}
            )
            photographers = photographer_response.get('Items', [])
            if photographers:
                photographer = photographers[0]
                gallery['photographer_name'] = photographer.get('name') or photographer.get('username') or 'Unknown'
                gallery['photographer_id'] = photographer['id']
            else:
                gallery['photographer_name'] = 'Unknown Photographer'
                gallery['photographer_id'] = photographer_id
        except Exception as e:
            print(f"Error looking up photographer: {str(e)}")
            gallery['photographer_name'] = 'Unknown Photographer'
            gallery['photographer_id'] = gallery.get('user_id')
        
        # Get ALL photos (pending + approved)
        try:
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            gallery_photos = photos_response.get('Items', [])
            gallery_photos.sort(key=lambda x: x.get('created_at', ''))
            gallery['photos'] = gallery_photos
            gallery['photo_count'] = len(gallery_photos)
        except Exception as e:
            print(f"Error loading photos: {str(e)}")
            gallery['photos'] = []
            gallery['photo_count'] = 0
        
        return create_response(200, gallery)
    except Exception as e:
        print(f"Error getting gallery by token: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load gallery'})

