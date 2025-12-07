"""
Bulk Download Handler - Server-Side ZIP Generation
Provides fast ZIP downloads by streaming directly from S3
"""
from boto3.dynamodb.conditions import Key
from utils.config import s3_client, S3_RENDITIONS_BUCKET, photos_table, galleries_table
from utils.response import create_response


def handle_bulk_download(gallery_id, user, event):
    """
    Return pre-generated ZIP file URL for all gallery photos
    ZIP is pre-generated and stored in S3, so download is instant
    """
    import json
    
    try:
        # Verify gallery access
        # Check if user owns the gallery OR has access via token
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        gallery_owner_id = gallery.get('user_id')
        
        # Check access: either owner or client
        is_owner = user and user.get('id') == gallery_owner_id
        user_email = user.get('email', '').lower() if user else ''
        client_emails = [email.lower() for email in gallery.get('client_emails', [])]
        is_client = user_email in client_emails
        
        # For public access via token, we'll handle in a separate endpoint
        # For now, require authentication
        if not (is_owner or is_client):
            return create_response(403, {'error': 'Access denied'})
        
        # Get pre-generated ZIP URL from S3 renditions bucket
        zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
        
        # Check if ZIP exists in S3
        try:
            s3_client.head_object(Bucket=S3_RENDITIONS_BUCKET, Key=zip_s3_key)
            # ZIP exists - generate URL
            from utils.cdn_urls import get_zip_url
            zip_url = get_zip_url(gallery_id)
            
            gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
            photo_count = gallery.get('photo_count', 0)
            filename = f"{gallery_name}-{photo_count}-photos.zip"
            
            print(f"Returning pre-generated ZIP URL: {zip_url}")
            
            return create_response(200, {
                'zip_url': zip_url,
                'filename': filename,
                'photo_count': photo_count
            })
        except:
            # ZIP doesn't exist yet - generate it now
            print(f" ZIP not found, generating now...")
            from utils.zip_generator import generate_gallery_zip
            result = generate_gallery_zip(gallery_id)
            
            if result.get('success'):
                gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
                filename = f"{gallery_name}-{result.get('photo_count', 0)}-photos.zip"
                
                return create_response(200, {
                    'zip_url': result.get('zip_url'),
                    'filename': filename,
                    'photo_count': result.get('photo_count', 0)
                })
            else:
                return create_response(500, {'error': 'Failed to generate ZIP file'})
        
    except Exception as e:
        print(f"Error getting bulk download: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Bulk download failed: {str(e)}'})


def handle_bulk_download_by_token(event):
    """
    Return pre-generated ZIP file URL for clients accessing via share token
    No authentication required - token-based access
    ZIP is pre-generated and stored in S3, so download is instant
    """
    import json
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        token = body.get('token')
        
        if not token:
            return create_response(400, {'error': 'Token required'})
        
        # Verify token by looking up gallery with matching share_token
        gallery_response = galleries_table.scan(
            FilterExpression='share_token = :token',
            ExpressionAttributeValues={':token': token}
        )
        
        galleries = gallery_response.get('Items', [])
        if not galleries:
            return create_response(403, {'error': 'Invalid or expired token'})
        
        gallery = galleries[0]
        gallery_id = gallery.get('id')
        
        # Check if gallery owner's account is deleted
        photographer_id = gallery.get('user_id')
        if photographer_id:
            try:
                from utils.config import users_table
                photographer_response = users_table.scan(
                    FilterExpression='id = :id',
                    ExpressionAttributeValues={':id': photographer_id}
                )
                
                if photographer_response.get('Items'):
                    photographer = photographer_response['Items'][0]
                    account_status = photographer.get('account_status', 'ACTIVE')
                    
                    if account_status == 'PENDING_DELETION':
                        return create_response(410, {
                            'error': 'Download unavailable',
                            'message': 'This gallery is no longer available. The photographer\'s account has been deactivated.'
                        })
            except Exception as e:
                print(f" Error checking photographer status: {e}")
                # Continue if check fails - don't block download
        
        print(f"Token-based bulk download for gallery {gallery_id}")
        
        # Get pre-generated ZIP URL from S3 renditions bucket
        zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
        
        # Check if ZIP exists in S3
        try:
            s3_client.head_object(Bucket=S3_RENDITIONS_BUCKET, Key=zip_s3_key)
            # ZIP exists - generate URL
            from utils.cdn_urls import get_zip_url
            zip_url = get_zip_url(gallery_id)
            
            gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
            photo_count = gallery.get('photo_count', 0)
            filename = f"{gallery_name}-{photo_count}-photos.zip"
            
            print(f"Returning pre-generated ZIP URL: {zip_url}")
            
            return create_response(200, {
                'zip_url': zip_url,
                'filename': filename,
                'photo_count': photo_count
            })
        except:
            # ZIP doesn't exist yet - generate it now
            print(f" ZIP not found, generating now...")
            from utils.zip_generator import generate_gallery_zip
            result = generate_gallery_zip(gallery_id)
            
            if result.get('success'):
                gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
                filename = f"{gallery_name}-{result.get('photo_count', 0)}-photos.zip"
                
                return create_response(200, {
                    'zip_url': result.get('zip_url'),
                    'filename': filename,
                    'photo_count': result.get('photo_count', 0)
                })
            else:
                return create_response(500, {'error': 'Failed to generate ZIP file'})
        
    except Exception as e:
        print(f"Error getting token-based bulk download: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Bulk download failed: {str(e)}'})

