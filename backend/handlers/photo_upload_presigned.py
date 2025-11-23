"""
Photo Upload Handler - Presigned S3 URLs
Handles large file uploads by providing presigned URLs for direct S3 upload
INCLUDES POST-UPLOAD SECURITY VALIDATION
"""
import uuid
import os
from datetime import datetime
from decimal import Decimal
from utils.config import s3_client, S3_BUCKET
from utils.response import create_response
from utils.cdn_urls import get_photo_urls  # CloudFront CDN URL helper

def handle_get_upload_url(gallery_id, user, event):
    """
    Generate presigned S3 URL for direct upload
    Step 1 of 3-step upload process
    
    For LocalStack: Returns a special flag to use direct backend upload
    For Production: Returns presigned POST URL
    """
    try:
        from utils.config import galleries_table, AWS_ENDPOINT_URL
        
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse request body
        import json
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', 'photo.jpg')
        content_type = body.get('content_type', 'image/jpeg')
        file_size = body.get('file_size', 0)
        use_multipart = body.get('use_multipart', False)
        
        # Extract file extension from original filename to preserve format
        import os
        file_extension = os.path.splitext(filename)[1] or '.jpg'  # Default to .jpg if no extension
        
        # Generate unique photo ID and S3 key with original extension
        photo_id = str(uuid.uuid4())
        s3_key = f"{gallery_id}/{photo_id}{file_extension}"
        
        # LocalStack workaround: Presigned POST doesn't work reliably
        # Use direct backend upload instead
        if AWS_ENDPOINT_URL and 'localstack' in AWS_ENDPOINT_URL.lower():
            print(f"🔧 LocalStack detected - using direct backend upload for {filename}")
            return create_response(200, {
                'photo_id': photo_id,
                's3_key': s3_key,
                'upload_url': f'galleries/{gallery_id}/photos/direct-upload',  # Backend endpoint (no /v1 prefix - added by frontend)
                'use_direct_upload': True,  # Flag for frontend
                'filename': filename,
                'file_size': file_size
            })
        
        # For large files (> 10MB), use multipart upload
        if use_multipart or file_size > 10 * 1024 * 1024:
            from handlers.multipart_upload_handler import handle_initialize_multipart_upload
            return handle_initialize_multipart_upload(gallery_id, user, event)
        
        # Generate presigned POST URL (for small files < 10MB)
        presigned_data = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Fields={
                'Content-Type': content_type
            },
            Conditions=[
                {'Content-Type': content_type},
                ['content-length-range', 1, 5368709120]  # Max 5GB
            ],
            ExpiresIn=3600  # 1 hour to complete upload
        )
        
        # LocalStack fix: Replace internal Docker hostname with localhost for browser access
        upload_url = presigned_data['url']
        if 'localstack' in upload_url:
            upload_url = upload_url.replace('http://localstack:', 'http://localhost:')
            print(f"🔧 Fixed LocalStack URL for browser: {upload_url}")
        
        print(f"✅ Generated presigned URL for {filename}: {s3_key}")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'upload_url': upload_url,
            'upload_fields': presigned_data['fields'],
            'filename': filename,
            'file_size': file_size
        })
        
    except Exception as e:
        print(f"❌ Error generating upload URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to generate upload URL: {str(e)}'})


def handle_direct_upload(gallery_id, user, event):
    """
    Direct backend upload for LocalStack
    Accepts both original file (e.g., HEIC) and converted file (JPEG)
    Stores both for download + serving respectively
    """
    try:
        from utils.config import galleries_table
        import base64
        
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse JSON upload data
        import json
        body = event.get('body', '')
        
        try:
            data = json.loads(body)
            photo_id = data.get('photo_id')
            s3_key = data.get('s3_key')
            filename = data.get('filename')
            file_data_b64 = data.get('file_data')  # Base64 encoded converted file (JPEG)
            
            # Optional: Original file (HEIC, RAW, etc) if different from converted
            original_filename = data.get('original_filename')
            original_file_data_b64 = data.get('original_file_data')
            
            if not all([photo_id, s3_key, filename, file_data_b64]):
                return create_response(400, {'error': 'Missing required fields: photo_id, s3_key, filename, file_data'})
            
            # Decode converted file (always required - this is what we serve)
            file_data = base64.b64decode(file_data_b64)
            
        except (json.JSONDecodeError, KeyError) as parse_error:
            print(f"❌ JSON parse error: {str(parse_error)}")
            return create_response(400, {'error': 'Invalid JSON format'})
        
        # Upload converted file to S3 (for serving via CDN)
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file_data,
                ContentType='image/jpeg'
            )
            print(f"✅ Converted file uploaded: {s3_key} ({len(file_data):,} bytes)")
            
        except Exception as upload_error:
            print(f"❌ S3 upload failed: {str(upload_error)}")
            import traceback
            traceback.print_exc()
            return create_response(500, {'error': f'Upload failed: {str(upload_error)}'})
        
        # Upload original file if provided (for downloads)
        original_s3_key = None
        if original_file_data_b64 and original_filename:
            try:
                original_file_data = base64.b64decode(original_file_data_b64)
                
                # Store originals in /originals/ subfolder
                # Format: originals/gallery_id/photo_id.heic
                original_s3_key = f"originals/{gallery_id}/{photo_id}.{original_filename.split('.')[-1]}"
                
                # Detect content type from extension
                ext = original_filename.lower().split('.')[-1]
                content_type_map = {
                    'heic': 'image/heic',
                    'heif': 'image/heif',
                    'cr2': 'image/x-canon-cr2',
                    'nef': 'image/x-nikon-nef',
                    'arw': 'image/x-sony-arw',
                    'dng': 'image/dng',
                    'raw': 'image/x-raw'
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
                
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=original_s3_key,
                    Body=original_file_data,
                    ContentType=content_type,
                    Metadata={
                        'original-filename': original_filename,
                        'converted-s3-key': s3_key
                    }
                )
                print(f"✅ Original file uploaded: {original_s3_key} ({len(original_file_data):,} bytes)")
                
            except Exception as original_error:
                print(f"⚠️  Original file upload failed (non-critical): {str(original_error)}")
                # Don't fail the whole upload if original fails
                original_s3_key = None
        
        return create_response(200, {
            'success': True,
            'photo_id': photo_id,
            's3_key': s3_key,
            'original_s3_key': original_s3_key,
            'original_filename': original_filename if original_s3_key else None,
            'message': 'Upload successful'
        })
        
    except Exception as e:
        print(f"❌ Error in direct upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Direct upload failed: {str(e)}'})


def handle_confirm_upload(gallery_id, user, event):
    """
    Confirm S3 upload and create photo record
    Step 3 of 3-step upload process
    """
    try:
        from utils.config import galleries_table, photos_table
        import json
        
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        gallery = response['Item']
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        photo_id = body.get('photo_id')
        s3_key = body.get('s3_key')
        filename = body.get('filename', 'photo.jpg')
        file_size = body.get('file_size', 0)
        file_hash = body.get('file_hash', '')
        
        if not photo_id or not s3_key:
            return create_response(400, {'error': 'Missing photo_id or s3_key'})
        
        # Verify file exists in S3
        try:
            s3_response = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except:
            return create_response(404, {'error': 'File not found in S3'})
        
        # ==========================================
        # SECURITY & METADATA: Steps 6-8
        # ==========================================
        # Step 6: File validation and metadata extraction
        # Step 7: Comprehensive metadata recording
        # Step 8: Database record creation with linkage
        try:
            # Download file from S3 for validation and metadata extraction
            s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
            image_data = s3_object['Body'].read()
            file_size = len(image_data)
            
            # Step 7: Extract comprehensive metadata
            from utils.metadata_extractor import extract_image_metadata
            metadata = extract_image_metadata(image_data, filename)
            
            print(f"📋 Extracted metadata: format={metadata.get('format')}, "
                  f"dimensions={metadata.get('dimensions')}, "
                  f"camera={metadata.get('camera', {}).get('model', 'unknown')}")
            
            # ==========================================
            # STORAGE STRATEGY: Single source of truth
            # ==========================================
            # Store ONLY the original file (RAW, HEIC, JPEG, etc.)
            # Renditions generated asynchronously by processing Lambda
            # Original preserved for download (no quality loss)
            # 
            # Benefits:
            # - No duplicate storage (original stored once)
            # - Processing queue handles rendition generation
            # - Download gets original file (lossless)
            # - Renditions optimized for web delivery
            # ==========================================
            
        except Exception as e:
            print(f"❌ Error processing upload: {str(e)}")
            
            # DELETE the file from S3 if there was an error
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                print(f"🗑️  Deleted problematic file from S3: {s3_key}")
            except Exception as delete_error:
                print(f"⚠️  Failed to delete problematic file: {str(delete_error)}")
            
            # Return error to frontend
            return create_response(400, {
                'error': 'Error processing uploaded file',
                'detail': str(e),
                'action': 'File has been rejected and deleted'
            })
        # ==========================================
        
        # Calculate size in MB - Use Decimal for DynamoDB
        size_mb = Decimal(str(round(file_size / (1024 * 1024), 2)))
        
        # Convert any float values in metadata to Decimal or string
        def convert_floats_to_decimal(obj):
            """Recursively convert float to Decimal for DynamoDB"""
            if isinstance(obj, float):
                return Decimal(str(round(obj, 6)))
            elif isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(item) for item in obj]
            return obj
        
        # Clean metadata to ensure DynamoDB compatibility
        clean_metadata = convert_floats_to_decimal(metadata)
        
        # Step 8: Create photo record with comprehensive metadata
        # Links stored original to gallery and photographer
        
        # Get original file info if provided (from direct upload response)
        original_s3_key = body.get('original_s3_key')
        original_filename = body.get('original_filename')
        
        # Generate CDN URLs for renditions (will be populated after processing)
        photo_urls = get_photo_urls(s3_key)
        
        # Generate download URL for original file (if different from converted)
        if original_s3_key:
            from utils.cdn_urls import IS_LOCALSTACK_S3, AWS_ENDPOINT_URL, S3_PHOTOS_BUCKET
            if IS_LOCALSTACK_S3 and AWS_ENDPOINT_URL:
                endpoint = AWS_ENDPOINT_URL.replace('http://localstack:', 'http://localhost:')
                original_download_url = f"{endpoint}/{S3_PHOTOS_BUCKET}/{original_s3_key}"
            else:
                from utils.cdn_urls import CDN_DOMAIN
                original_download_url = f"https://{CDN_DOMAIN}/{original_s3_key}"
        else:
            original_download_url = photo_urls['url']  # Same as converted if no original
        
        photo = {
            'id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user['id'],
            'filename': filename,
            's3_key': s3_key,
            
            # Original file (if converted from HEIC/RAW)
            'original_s3_key': original_s3_key if original_s3_key else None,
            'original_filename': original_filename if original_filename else filename,
            
            # URLs (CloudFront CDN)
            'url': photo_urls['url'],  # Converted file for viewing
            'original_download_url': original_download_url,  # Original for download
            'medium_url': photo_urls['medium_url'],  # 2000x2000
            'thumbnail_url': photo_urls['thumbnail_url'],  # 800x600
            'small_thumb_url': photo_urls.get('small_url'),  # 400x400 (key is 'small_url' in get_photo_urls)
            'large_url': photo_urls.get('large_url'),  # 4000x4000
            
            # User-provided metadata
            'title': body.get('title', ''),
            'description': body.get('description', ''),
            'tags': body.get('tags', []),
            
            # File metadata from extraction (cleaned for DynamoDB)
            'file_size': file_size,
            'size_mb': size_mb,
            'format': clean_metadata.get('format'),
            'dimensions': clean_metadata.get('dimensions'),
            
            # Camera and EXIF metadata (cleaned for DynamoDB)
            'camera': clean_metadata.get('camera', {}),
            'exif': clean_metadata.get('exif', {}),
            'gps': clean_metadata.get('gps', {}),
            'color': clean_metadata.get('color', {}),
            'timestamps': clean_metadata.get('timestamps', {}),
            
            # Processing status (Step 9: queued for async processing)
            'status': 'processing',  # Will be updated to 'active' after renditions generated
            'processing_started_at': datetime.utcnow().isoformat() + 'Z',
            
            # Engagement metrics
            'views': 0,
            'downloads': 0,
            'comments': [],
            
            # Timestamps
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        photos_table.put_item(Item=photo)
        
        # Step 9-15: LocalStack only - Generate renditions synchronously
        # In production, this is handled by Lambda triggered by S3 event
        from utils.config import AWS_ENDPOINT_URL
        if AWS_ENDPOINT_URL and 'localstack' in AWS_ENDPOINT_URL.lower():
            try:
                from utils.image_processor import process_upload_async
                print(f"🔄 Processing image for LocalStack: {s3_key}")
                result = process_upload_async(s3_key, S3_BUCKET)
                if result.get('success'):
                    print(f"✅ Renditions generated successfully")
                    # Update photo status to 'active' since processing is complete
                    photo['status'] = 'active'
                    photos_table.put_item(Item=photo)
                else:
                    print(f"⚠️  Rendition generation failed: {result.get('error')}")
            except Exception as proc_error:
                print(f"⚠️  LocalStack processing error: {str(proc_error)}")
                # Don't fail the upload if processing fails
        
        # Update gallery photo count and storage
        previous_photo_count = gallery.get('photo_count', 0)
        new_photo_count = previous_photo_count + 1
        current_storage_mb = gallery.get('storage_used', 0)
        if isinstance(current_storage_mb, Decimal):
            current_storage_mb = float(current_storage_mb)
        else:
            current_storage_mb = float(current_storage_mb) if current_storage_mb else 0.0
        new_storage_mb = Decimal(str(round(current_storage_mb + float(size_mb), 2)))
        
        gallery['photo_count'] = new_photo_count
        gallery['storage_used'] = new_storage_mb
        gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        galleries_table.put_item(Item=gallery)
        
        # Regenerate gallery ZIP file (synchronous - wait for completion)
        try:
            from utils.zip_generator import generate_gallery_zip
            print(f"🔄 Starting ZIP regeneration for gallery {gallery_id}...")
            result = generate_gallery_zip(gallery_id)
            if result.get('success'):
                print(f"✅ ZIP regeneration completed: {result.get('photo_count')} photos, {result.get('zip_size_mb', 0):.2f}MB")
            else:
                print(f"⚠️  ZIP regeneration failed: {result.get('error', 'unknown')}")
        except Exception as zip_error:
            print(f"⚠️  Failed to regenerate ZIP: {str(zip_error)}")
            # Don't fail upload if ZIP generation fails
        
        # ✅ SEND "GALLERY READY" NOTIFICATION - When FIRST photo is uploaded
        if previous_photo_count == 0 and new_photo_count == 1:
            try:
                from handlers.notification_handler import notify_gallery_ready
                from utils.config import users_table
                
                # Get photographer details
                photographer_response = users_table.get_item(Key={'id': user['id']})
                if 'Item' in photographer_response:
                    photographer = photographer_response['Item']
                    photographer_name = photographer.get('name') or photographer.get('username', 'Your photographer')
                    
                    # Get client emails and details
                    client_emails = gallery.get('client_emails', [])
                    client_name = gallery.get('client_name', 'Client')
                    gallery_url = gallery.get('share_url', '')
                    
                    # Send to ALL clients
                    for client_email in client_emails:
                        try:
                            notify_gallery_ready(
                                user_id=user['id'],
                                gallery_id=gallery_id,
                                client_email=client_email,
                                client_name=client_name,
                                photographer_name=photographer_name,
                                gallery_url=gallery_url,
                                message='Your gallery is now ready for viewing!'
                            )
                            print(f"✅ Sent 'Gallery Ready' notification to {client_email}")
                        except Exception as email_error:
                            print(f"⚠️  Failed to send Gallery Ready email to {client_email}: {str(email_error)}")
            except Exception as notif_error:
                print(f"⚠️  Failed to send Gallery Ready notifications: {str(notif_error)}")
                # Don't fail the upload if notification fails
        
        print(f"✅ Photo confirmed: {filename} ({size_mb:.2f} MB)")
        return create_response(201, photo)
        
    except Exception as e:
        print(f"❌ Error confirming upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to confirm upload: {str(e)}'})

