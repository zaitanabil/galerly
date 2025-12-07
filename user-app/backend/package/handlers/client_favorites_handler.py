"""
Client Favorites Handler
Allows clients to favorite photos for easy access
"""
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import photos_table, galleries_table, client_favorites_table
from utils.response import create_response


def handle_add_favorite(user, body):
    """Add a photo to client favorites"""
    try:
        photo_id = body.get('photo_id')
        gallery_id = body.get('gallery_id')
        client_email = user.get('email', '').lower()
        
        print(f"Adding favorite: photo_id={photo_id}, gallery_id={gallery_id}, client_email={client_email}")
        
        if not photo_id or not gallery_id:
            return create_response(400, {'error': 'photo_id and gallery_id are required'})
        
        if not client_email:
            return create_response(400, {'error': 'User email not found'})
        
        # Verify photo exists and client has access to gallery
        try:
            photo_response = photos_table.get_item(Key={'id': photo_id})
            if 'Item' not in photo_response:
                print(f"Photo not found: {photo_id}")
                return create_response(404, {'error': 'Photo not found'})
            
            photo = photo_response['Item']
            if photo.get('gallery_id') != gallery_id:
                print(f"Photo gallery mismatch: photo.gallery_id={photo.get('gallery_id')}, requested={gallery_id}")
                return create_response(400, {'error': 'Photo does not belong to this gallery'})
            
            # Get user_id from photo or gallery - required for gallery lookup
            user_id = photo.get('user_id')
            
            # If photo doesn't have user_id (legacy data), get it from gallery
            if not user_id:
                print(f"Photo missing user_id, fetching from gallery: {photo_id}")
                # Try to get gallery using GalleryIdIndex (GSI)
                gallery_query = galleries_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('id').eq(gallery_id),
                    Limit=1
                )
                if gallery_query.get('Items'):
                    user_id = gallery_query['Items'][0].get('user_id')
                    print(f"Found user_id from gallery: {user_id}")
                else:
                    print(f"Gallery not found via GSI: {gallery_id}")
                    return create_response(404, {'error': 'Gallery not found'})
            
            if not user_id:
                print(f"Could not determine user_id for photo: {photo_id}")
                return create_response(400, {'error': 'Photo data is invalid - missing user_id'})
            
            # Verify gallery access (client_email must match)
            gallery_response = galleries_table.get_item(
                Key={'user_id': user_id, 'id': gallery_id}
            )
            if 'Item' not in gallery_response:
                print(f"Gallery not found: gallery_id={gallery_id}, user_id={user_id}")
                return create_response(404, {'error': 'Gallery not found'})
            
            gallery = gallery_response['Item']
            
            # Check if user email is in client_emails array (or legacy client_email)
            client_emails = gallery.get('client_emails', [])
            legacy_email = gallery.get('client_email', '').lower()
            
            # Add legacy email to array for unified checking
            if legacy_email and legacy_email not in client_emails:
                client_emails = client_emails + [legacy_email]
            
            print(f"Gallery client_emails: {client_emails}, user email: {client_email}")
            
            # Check if user has access
            if client_email not in [email.lower() for email in client_emails]:
                print(f"Access denied: user email={client_email} not in client_emails={client_emails}")
                return create_response(403, {'error': 'Access denied - you do not have access to this gallery'})
        except Exception as e:
            print(f"Error verifying photo/gallery access: {str(e)}")
            import traceback
            traceback.print_exc()
            return create_response(500, {'error': f'Failed to verify access: {str(e)}'})
        
        # Check if already favorited
        favorite_key = {
            'client_email': client_email,
            'photo_id': photo_id
        }
        
        try:
            existing = client_favorites_table.get_item(Key=favorite_key)
            if 'Item' in existing:
                print(f"Photo already favorited: {photo_id}")
                return create_response(200, {
                    'message': 'Photo already in favorites',
                    'favorited': True
                })
        except Exception as e:
            print(f"Error checking existing favorite: {str(e)}")
            # If table doesn't exist, this will fail - but we'll try to create it anyway
            import traceback
            traceback.print_exc()
        
        # Add to favorites
        # Use user_id from photo or gallery (for legacy photos)
        photographer_id = photo.get('user_id') or user_id
        
        favorite = {
            'client_email': client_email,
            'photo_id': photo_id,
            'gallery_id': gallery_id,
            'photographer_id': photographer_id,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        try:
            client_favorites_table.put_item(Item=favorite)
            print(f"Successfully added favorite: {photo_id} for {client_email}")
            
            # ✅ SEND NOTIFICATION TO PHOTOGRAPHER - Client Selected Photos
            try:
                from handlers.notification_handler import notify_client_selected_photos
                from utils.config import users_table
                
                # Get photographer details
                photographer_response = users_table.get_item(Key={'id': photographer_id})
                if 'Item' in photographer_response:
                    photographer = photographer_response['Item']
                    photographer_email = photographer.get('email')
                    photographer_name = photographer.get('name') or photographer.get('username', 'Photographer')
                    
                    # Get client name from gallery
                    client_name = gallery.get('client_name', 'Client')
                    gallery_name = gallery.get('name', 'Your gallery')
                    
                    # Build gallery URL
                    import os
                    frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
                    gallery_url = f"{frontend_url}/gallery?id={gallery_id}"
                    
                    # Send notification (function checks preferences internally)
                    notify_client_selected_photos(
                        photographer_id=photographer_id,
                        photographer_email=photographer_email,
                        photographer_name=photographer_name,
                        client_name=client_name,
                        gallery_name=gallery_name,
                        gallery_url=gallery_url,
                        selection_count=1
                    )
                    print(f"✅ Sent 'Client Selected Photos' notification to photographer {photographer_email}")
            except Exception as notif_error:
                print(f"⚠️  Failed to send notification: {str(notif_error)}")
                # Don't fail the favorite action if notification fails
        except Exception as e:
            print(f"Error writing to favorites table: {str(e)}")
            import traceback
            traceback.print_exc()
            # Check if it's a table not found error
            if 'ResourceNotFoundException' in str(e) or 'does not exist' in str(e).lower():
                return create_response(500, {
                    'error': 'Favorites table not found',
                    'message': 'The favorites feature is not yet configured. Please contact support.',
                    'details': str(e)
                })
            raise
        
        return create_response(200, {
            'message': 'Photo added to favorites',
            'favorited': True
        })
        
    except Exception as e:
        print(f"Error adding favorite: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to add favorite',
            'message': str(e),
            'type': type(e).__name__
        })


def handle_remove_favorite(user, body):
    """Remove a photo from client favorites"""
    try:
        photo_id = body.get('photo_id')
        
        if not photo_id:
            return create_response(400, {'error': 'photo_id is required'})
        
        client_email = user.get('email', '').lower()
        
        # Remove from favorites
        favorite_key = {
            'client_email': client_email,
            'photo_id': photo_id
        }
        
        client_favorites_table.delete_item(Key=favorite_key)
        
        return create_response(200, {
            'message': 'Photo removed from favorites',
            'favorited': False
        })
        
    except Exception as e:
        print(f"Error removing favorite: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to remove favorite: {str(e)}'})


def handle_get_favorites(user):
    """Get all favorited photos for a client"""
    try:
        client_email = user.get('email', '').lower()
        
        # Query favorites by client_email
        response = client_favorites_table.query(
            KeyConditionExpression=Key('client_email').eq(client_email)
        )
        
        favorites = response.get('Items', [])
        
        # Get full photo details
        favorite_photos = []
        for fav in favorites:
            photo_response = photos_table.get_item(Key={'id': fav['photo_id']})
            if 'Item' in photo_response:
                photo = photo_response['Item']
                favorite_photos.append({
                    'photo_id': photo['id'],
                    'gallery_id': fav['gallery_id'],
                    'photographer_id': fav.get('photographer_id'),
                    'url': photo.get('url'),
                    'thumbnail_url': photo.get('thumbnail_url'),
                    'title': photo.get('title'),
                    'description': photo.get('description'),
                    'favorited_at': fav.get('created_at')
                })
        
        return create_response(200, {
            'favorites': favorite_photos,
            'count': len(favorite_photos)
        })
        
    except Exception as e:
        print(f"Error getting favorites: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to get favorites: {str(e)}'})


def handle_check_favorite(user, photo_id):
    """Check if a photo is favorited by the client"""
    try:
        client_email = user.get('email', '').lower()
        
        favorite_key = {
            'client_email': client_email,
            'photo_id': photo_id
        }
        
        response = client_favorites_table.get_item(Key=favorite_key)
        
        return create_response(200, {
            'favorited': 'Item' in response
        })
        
    except Exception as e:
        print(f"Error checking favorite: {str(e)}")
        return create_response(500, {'error': f'Failed to check favorite: {str(e)}'})

