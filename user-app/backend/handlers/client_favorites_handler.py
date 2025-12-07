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
        
        # Get client email from user session or body
        client_email = ''
        if user:
            client_email = user.get('email', '').lower()
        if not client_email:
            client_email = body.get('client_email', '').lower()
        
        print(f"Adding favorite: photo_id={photo_id}, gallery_id={gallery_id}, client_email={client_email}")
        
        if not photo_id or not gallery_id:
            return create_response(400, {'error': 'photo_id and gallery_id are required'})
        
        if not client_email:
            return create_response(400, {'error': 'User email not found'})
        
        # Verify photo exists and get gallery info
        try:
            photo_response = photos_table.get_item(Key={'id': photo_id})
            if 'Item' not in photo_response:
                print(f"Photo not found: {photo_id}")
                return create_response(404, {'error': 'Photo not found'})
            
            photo = photo_response['Item']
            if photo.get('gallery_id') != gallery_id:
                print(f"Photo gallery mismatch: photo.gallery_id={photo.get('gallery_id')}, requested={gallery_id}")
                return create_response(400, {'error': 'Photo does not belong to this gallery'})
            
            # Get user_id from photo or gallery
            user_id = photo.get('user_id')
            
            if not user_id:
                print(f"Photo missing user_id, fetching from gallery: {photo_id}")
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
            
            # Check if the user trying to favorite is the photographer (owner)
            from utils.config import users_table
            photographer_check = users_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('id').eq(user_id)
            )
            if photographer_check.get('Items'):
                photographer = photographer_check['Items'][0]
                photographer_email = photographer.get('email', '').lower()
                if client_email == photographer_email:
                    return create_response(403, {
                        'error': 'Photographers cannot favorite their own photos',
                        'message': 'Only clients can mark photos as favorites'
                    })
            
            # Check if photographer plan allows favorites
            from handlers.subscription_handler import get_user_features
            photographer_user = {'id': user_id} 
            features, _, _ = get_user_features(photographer_user)
            
            if not features.get('client_favorites'):
                 return create_response(403, {
                     'error': 'Client favorites are not available for this gallery',
                     'upgrade_required': True
                 })

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
            
            # Update photo favorites_count
            try:
                photos_table.update_item(
                    Key={'id': photo_id},
                    UpdateExpression='SET favorites_count = if_not_exists(favorites_count, :zero) + :inc',
                    ExpressionAttributeValues={
                        ':inc': 1,
                        ':zero': 0
                    }
                )
            except Exception as e:
                print(f"Failed to update favorites_count for photo {photo_id}: {e}")

            # Notification is now handled by explicit 'Submit Selection' action
            # to prevent spamming the photographer with one email per photo.
            
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
        
        # Get client email from user session or body
        client_email = ''
        if user:
            client_email = user.get('email', '').lower()
        if not client_email:
            client_email = body.get('client_email', '').lower()
            
        print(f"Removing favorite: photo_id={photo_id}, client_email={client_email}")
        
        if not photo_id:
            return create_response(400, {'error': 'photo_id is required'})
            
        if not client_email:
            return create_response(400, {'error': 'User email not found. Please provide client_email.'})
        
        # Remove from favorites
        favorite_key = {
            'client_email': client_email,
            'photo_id': photo_id
        }
        
        client_favorites_table.delete_item(Key=favorite_key)
        
        # Update photo favorites_count - Only decrement if > 0
        try:
            photos_table.update_item(
                Key={'id': photo_id},
                UpdateExpression='SET favorites_count = favorites_count - :dec',
                ConditionExpression='favorites_count > :zero',
                ExpressionAttributeValues={
                    ':dec': 1,
                    ':zero': 0
                }
            )
        except Exception as e:
            # ConditionalCheckFailedException is expected if count is already 0
            if 'ConditionalCheckFailedException' not in str(e):
                print(f"Failed to update favorites_count for photo {photo_id}: {e}")
        
        return create_response(200, {
            'message': 'Photo removed from favorites',
            'favorited': False
        })
        
    except Exception as e:
        print(f"Error removing favorite: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to remove favorite: {str(e)}'})


def handle_get_favorites(user, query_params=None):
    """Get all favorited photos for a client"""
    try:
        client_email = ''
        if user:
            client_email = user.get('email', '').lower()
        
        if not client_email and query_params:
            client_email = query_params.get('client_email', '').lower()
            
        if not client_email:
             return create_response(400, {'error': 'User email not found'})
        
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


def handle_check_favorite(user, photo_id, query_params=None):
    """Check if a photo is favorited by the client"""
    try:
        client_email = ''
        if user:
            client_email = user.get('email', '').lower()
            
        if not client_email and query_params:
            client_email = query_params.get('client_email', '').lower()
            
        if not client_email:
            # If no email, can't check, assume false
            return create_response(200, {'is_favorite': False})
        
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

def handle_submit_favorites(user, body):
    """
    Submit selected favorites to the photographer.
    This finalizes the selection and triggers a notification.
    """
    try:
        gallery_id = body.get('gallery_id')
        
        # Get client email
        client_email = ''
        if user:
            client_email = user.get('email', '').lower()
        if not client_email:
            client_email = body.get('client_email', '').lower()
            
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id is required'})
            
        if not client_email:
            return create_response(400, {'error': 'Client email is required'})
            
        print(f"Submitting favorites for gallery: {gallery_id}, client: {client_email}")

        # 1. Get all favorites for this client and gallery
        # Using scan or query on client_email then filtering by gallery_id (since we only have PK on client_email)
        response = client_favorites_table.query(
            KeyConditionExpression=Key('client_email').eq(client_email)
        )
        all_favorites = response.get('Items', [])
        
        # Filter for this gallery
        gallery_favorites = [f for f in all_favorites if f.get('gallery_id') == gallery_id]
        
        # Verify these photos actually exist (filter out favorites for deleted photos)
        # Fetch all photo IDs for this gallery to ensure we only count existing photos
        valid_photo_ids = set()
        query_params = {
            'IndexName': 'GalleryIdIndex',
            'KeyConditionExpression': Key('gallery_id').eq(gallery_id),
            'ProjectionExpression': 'id'
        }
        
        while True:
            photos_response = photos_table.query(**query_params)
            valid_photo_ids.update(p['id'] for p in photos_response.get('Items', []))
            if 'LastEvaluatedKey' not in photos_response:
                break
            query_params['ExclusiveStartKey'] = photos_response['LastEvaluatedKey']
            
        # Filter favorites to only include valid photos
        valid_favorites = [f for f in gallery_favorites if f.get('photo_id') in valid_photo_ids]
        selection_count = len(valid_favorites)
        
        if selection_count == 0:
            return create_response(400, {'error': 'No favorites selected for this gallery'})

        # 2. Get Gallery and Photographer details
        # Need to find the photographer_id first. We can get it from one of the favorites or query the gallery.
        photographer_id = valid_favorites[0].get('photographer_id')
        
        if not photographer_id:
            # Fallback: Query gallery (inefficient if we don't have user_id, but we need it)
            # Try to query gallery by ID using GSI if needed, but we need to find user_id
            from utils.config import galleries_table
            gallery_query = galleries_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('id').eq(gallery_id),
                Limit=1
            )
            if gallery_query.get('Items'):
                gallery_item = gallery_query['Items'][0]
                photographer_id = gallery_item.get('user_id')
            else:
                return create_response(404, {'error': 'Gallery not found'})

        # Now get full gallery details with photographer_id
        from utils.config import users_table, galleries_table
        
        gallery_response = galleries_table.get_item(Key={'user_id': photographer_id, 'id': gallery_id})
        if 'Item' not in gallery_response:
             return create_response(404, {'error': 'Gallery details not found'})
             
        gallery = gallery_response['Item']
        client_name = gallery.get('client_name', 'Client') # Or use name associated with email if we tracked it
        gallery_name = gallery.get('name', 'Gallery')

        # Get Photographer email
        # User table uses 'email' as PK, so we need to query by 'id' using GSI
        photographer_response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('id').eq(photographer_id)
        )
        if not photographer_response.get('Items'):
             return create_response(404, {'error': 'Photographer not found'})
             
        photographer = photographer_response['Items'][0]
        photographer_email = photographer.get('email')
        photographer_name = photographer.get('name') or photographer.get('username', 'Photographer')

        # 3. Send Notification
        from handlers.notification_handler import notify_client_selected_photos
        import os
        frontend_url = os.environ.get('FRONTEND_URL')
        gallery_url = f"{frontend_url}/gallery/{gallery_id}" # Link for photographer to view

        success = notify_client_selected_photos(
            photographer_id=photographer_id,
            photographer_email=photographer_email,
            photographer_name=photographer_name,
            client_name=client_name,
            gallery_name=gallery_name,
            gallery_url=gallery_url,
            selection_count=selection_count
        )
        
        if success:
            print(f"Notification sent to {photographer_email}")
            return create_response(200, {
                'success': True, 
                'message': 'Selection submitted successfully',
                'count': selection_count
            })
        else:
            print(f"Notification failed for {photographer_email}")
            # Still return success to client, as the selection is saved
            return create_response(200, {
                'success': True, 
                'message': 'Selection saved, but notification failed',
                'count': selection_count
            })

    except Exception as e:
        print(f"Error submitting favorites: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to submit selection: {str(e)}'})
