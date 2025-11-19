"""
Bulk Download Handler - Server-Side ZIP Generation
Provides fast ZIP downloads by streaming directly from S3
"""
import io
import zipfile
from boto3.dynamodb.conditions import Key
from utils.config import s3_client, S3_BUCKET, photos_table, galleries_table
from utils.response import create_response


def handle_bulk_download(gallery_id, user, event):
    """
    Generate and stream ZIP file of selected photos
    Much faster than client-side ZIP generation
    """
    import json
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        photo_ids = body.get('photo_ids', [])
        
        if not photo_ids or not isinstance(photo_ids, list):
            return create_response(400, {'error': 'photo_ids must be a non-empty array'})
        
        print(f"📦 Bulk download requested: {len(photo_ids)} photos from gallery {gallery_id}")
        
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
        
        # Get photos from DynamoDB
        photos = []
        for photo_id in photo_ids:
            try:
                photo_response = photos_table.get_item(Key={'id': photo_id})
                if 'Item' in photo_response:
                    photo = photo_response['Item']
                    # Verify photo belongs to this gallery
                    if photo.get('gallery_id') == gallery_id:
                        photos.append(photo)
            except Exception as e:
                print(f"⚠️  Error fetching photo {photo_id}: {str(e)}")
                continue
        
        if not photos:
            return create_response(404, {'error': 'No valid photos found'})
        
        print(f"✅ Found {len(photos)} valid photos")
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            used_filenames = {}  # Track duplicates
            
            for photo in photos:
                try:
                    s3_key = photo.get('s3_key')
                    filename = photo.get('filename', f"photo-{photo['id']}.jpg")
                    
                    # Handle duplicate filenames
                    if filename in used_filenames:
                        # Extract extension
                        name_parts = filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            base_name, ext = name_parts
                            filename = f"{base_name}_{used_filenames[filename]}.{ext}"
                        else:
                            filename = f"{filename}_{used_filenames[filename]}"
                        used_filenames[filename] = used_filenames.get(filename, 0) + 1
                    else:
                        used_filenames[filename] = 1
                    
                    # Download from S3 and add to ZIP
                    print(f"  📥 Downloading {s3_key}...")
                    s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
                    image_data = s3_object['Body'].read()
                    
                    # Add to ZIP
                    zip_file.writestr(filename, image_data)
                    print(f"  ✅ Added {filename} ({len(image_data):,} bytes)")
                    
                except Exception as photo_error:
                    print(f"  ❌ Error processing photo {photo.get('id')}: {str(photo_error)}")
                    continue
        
        # Get ZIP data
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_size_mb = len(zip_data) / (1024 * 1024)
        
        print(f"✅ ZIP created: {len(photos)} photos, {zip_size_mb:.2f} MB")
        
        # Return ZIP as base64-encoded data for API Gateway
        import base64
        zip_base64 = base64.b64encode(zip_data).decode('utf-8')
        
        gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
        filename = f"{gallery_name}-{len(photos)}-photos.zip"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/zip',
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': zip_base64,
            'isBase64Encoded': True
        }
        
    except Exception as e:
        print(f"❌ Error creating bulk download: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Bulk download failed: {str(e)}'})


def handle_bulk_download_by_token(event):
    """
    Generate ZIP for clients accessing via share token
    No authentication required - token-based access
    """
    import json
    from utils.token import verify_gallery_token
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        token = body.get('token')
        photo_ids = body.get('photo_ids', [])
        
        if not token:
            return create_response(400, {'error': 'Token required'})
        
        if not photo_ids or not isinstance(photo_ids, list):
            return create_response(400, {'error': 'photo_ids must be a non-empty array'})
        
        # Verify token and get gallery_id
        token_data = verify_gallery_token(token)
        if not token_data:
            return create_response(403, {'error': 'Invalid or expired token'})
        
        gallery_id = token_data.get('gallery_id')
        
        print(f"📦 Token-based bulk download: {len(photo_ids)} photos from gallery {gallery_id}")
        
        # Get gallery
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        
        # Get photos from DynamoDB
        photos = []
        for photo_id in photo_ids:
            try:
                photo_response = photos_table.get_item(Key={'id': photo_id})
                if 'Item' in photo_response:
                    photo = photo_response['Item']
                    # Verify photo belongs to this gallery
                    if photo.get('gallery_id') == gallery_id:
                        photos.append(photo)
            except Exception as e:
                print(f"⚠️  Error fetching photo {photo_id}: {str(e)}")
                continue
        
        if not photos:
            return create_response(404, {'error': 'No valid photos found'})
        
        print(f"✅ Found {len(photos)} valid photos")
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            used_filenames = {}  # Track duplicates
            
            for photo in photos:
                try:
                    s3_key = photo.get('s3_key')
                    filename = photo.get('filename', f"photo-{photo['id']}.jpg")
                    
                    # Handle duplicate filenames
                    if filename in used_filenames:
                        # Extract extension
                        name_parts = filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            base_name, ext = name_parts
                            filename = f"{base_name}_{used_filenames[filename]}.{ext}"
                        else:
                            filename = f"{filename}_{used_filenames[filename]}"
                        used_filenames[filename] = used_filenames.get(filename, 0) + 1
                    else:
                        used_filenames[filename] = 1
                    
                    # Download from S3 and add to ZIP
                    print(f"  📥 Downloading {s3_key}...")
                    s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
                    image_data = s3_object['Body'].read()
                    
                    # Add to ZIP
                    zip_file.writestr(filename, image_data)
                    print(f"  ✅ Added {filename} ({len(image_data):,} bytes)")
                    
                except Exception as photo_error:
                    print(f"  ❌ Error processing photo {photo.get('id')}: {str(photo_error)}")
                    continue
        
        # Get ZIP data
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_size_mb = len(zip_data) / (1024 * 1024)
        
        print(f"✅ ZIP created: {len(photos)} photos, {zip_size_mb:.2f} MB")
        
        # Return ZIP as base64-encoded data for API Gateway
        import base64
        zip_base64 = base64.b64encode(zip_data).decode('utf-8')
        
        gallery_name = gallery.get('name', 'gallery').replace(' ', '-').lower()
        filename = f"{gallery_name}-{len(photos)}-photos.zip"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/zip',
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': zip_base64,
            'isBase64Encoded': True
        }
        
    except Exception as e:
        print(f"❌ Error creating token-based bulk download: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Bulk download failed: {str(e)}'})

