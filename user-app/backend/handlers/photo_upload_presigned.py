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
from handlers.subscription_handler import enforce_storage_limit, get_user_features

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
        
        # Validate filename is provided
        if not filename or not body.get('filename'):
            return create_response(400, {'error': 'Missing filename'})
        
        # Extract file extension and validate
        import os
        file_extension = (os.path.splitext(filename)[1] or '').lower()
        
        # Define allowed file types
        allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif', '.bmp', '.tiff', '.tif', '.svg']
        allowed_video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']
        allowed_raw_extensions = ['.cr2', '.cr3', '.nef', '.arw', '.dng', '.raw', '.raf', '.orf', '.rw2', '.pef', '.srw']
        all_allowed_extensions = allowed_image_extensions + allowed_video_extensions + allowed_raw_extensions
        
        # Validate file extension
        if file_extension not in all_allowed_extensions:
            return create_response(400, {
                'error': f'Invalid file type. Allowed types: images (.jpg, .png, etc.), videos (.mp4, .mov, etc.), RAW (.cr2, .nef, etc.)'
            })
        
        # 1. Enforce Storage Limit
        additional_mb = float(file_size) / (1024 * 1024)
        allowed, error_message = enforce_storage_limit(user, additional_mb)
        if not allowed:
            return create_response(403, {'error': error_message})
        
        # 2. Enforce Feature Limits (Video & RAW)
        features, _, _ = get_user_features(user)
        
        # Video Check
        video_extensions = allowed_video_extensions
        if file_extension in video_extensions:
            if features.get('video_quality') == 'none' or features.get('video_minutes', 0) == 0:
                 return create_response(403, {
                     'error': 'Video uploads are not available on your current plan. Please upgrade to upload videos.'
                 })
            
            # Note: Duration-based enforcement happens after upload when duration is extracted
            # We'll add a metadata field in presigned URL to pass estimated duration if provided
            estimated_duration_minutes = body.get('estimated_duration_minutes', 0)
            if estimated_duration_minutes > 0:
                from utils.video_utils import enforce_video_duration_limit
                allowed, error_msg = enforce_video_duration_limit(user, estimated_duration_minutes, features)
                if not allowed:
                    return create_response(403, {'error': error_msg})
        
        # RAW Check
        raw_extensions = allowed_raw_extensions
        if file_extension in raw_extensions:
            if not features.get('raw_support', False):
                 return create_response(403, {
                     'error': 'RAW photo uploads are only available on Pro and Ultimate plans. Please upgrade to upload RAW files.'
                 })
        
        # Generate unique photo ID and S3 key with original extension
        photo_id = str(uuid.uuid4())
        import os
        base_filename = os.path.splitext(filename)[0]  # Name without extension
        s3_key = f"{gallery_id}/{photo_id}_{base_filename}{file_extension}"
        
        # LocalStack workaround: Presigned POST doesn't work reliably
        # Use direct backend upload instead
        if AWS_ENDPOINT_URL and 'localstack' in AWS_ENDPOINT_URL.lower():
            print(f"LocalStack detected - using direct backend upload for {filename}")
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
            print(f"Fixed LocalStack URL for browser: {upload_url}")
        
        print(f"Generated presigned URL for {filename}: {s3_key}")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'upload_url': upload_url,
            'upload_fields': presigned_data['fields'],
            'filename': filename,
            'file_size': file_size
        })
        
    except Exception as e:
        print(f"Error generating upload URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to generate upload URL: {str(e)}'})


def handle_direct_upload(gallery_id, user, event):
    """
    Direct backend upload for LocalStack
    Accepts both original file (e.g., HEIC) and converted file (JPEG)
    Stores both for download + serving respectively
    
    For RAW/standard formats: Stores original file with correct extension
    For HEIC: Stores converted JPEG + original HEIC (optional)
    """
    try:
        from utils.config import galleries_table
        import base64
        import os
        
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
            file_data_b64 = data.get('file_data')  # Base64 encoded file
            
            if not all([photo_id, s3_key, filename, file_data_b64]):
                return create_response(400, {'error': 'Missing required fields: photo_id, s3_key, filename, file_data'})
            
            # Decode file
            file_data = base64.b64decode(file_data_b64)
            
        except (json.JSONDecodeError, KeyError) as parse_error:
            print(f"JSON parse error: {str(parse_error)}")
            return create_response(400, {'error': 'Invalid JSON format'})
        
        # Detect file type from extension
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Enforce Feature Limits (Video & RAW)
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        # Video Check
        allowed_video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']
        if file_extension in allowed_video_extensions:
            if features.get('video_quality') == 'none' or features.get('video_minutes', 0) == 0:
                return create_response(403, {
                    'error': 'Video uploads are not available on your current plan. Please upgrade to upload videos.'
                })
        
        # RAW Check
        allowed_raw_extensions = ['.cr2', '.cr3', '.nef', '.arw', '.dng', '.raw', '.raf', '.orf', '.rw2', '.pef', '.srw']
        if file_extension in allowed_raw_extensions:
            if not features.get('raw_support', False):
                return create_response(403, {
                    'error': 'RAW photo uploads are only available on Pro and Ultimate plans. Please upgrade to upload RAW files.',
                    'upgrade_required': True,
                    'feature': 'raw_support'
                })
        
        from utils.mime_types import get_mime_type
        content_type = get_mime_type(filename)
        
        # Upload file to S3 with correct content type
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type
            )
            print(f"File uploaded: {s3_key} ({len(file_data):,} bytes, type: {content_type})")
            
        except Exception as upload_error:
            print(f"S3 upload failed: {str(upload_error)}")
            import traceback
            traceback.print_exc()
            return create_response(500, {'error': f'Upload failed: {str(upload_error)}'})
        
        return create_response(200, {
            'success': True,
            'photo_id': photo_id,
            's3_key': s3_key,
            'message': 'Upload successful'
        })
        
    except Exception as e:
        print(f"Error in direct upload: {str(e)}")
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
                  f"type={metadata.get('type')}, "
                  f"dimensions={metadata.get('dimensions')}, "
                  f"camera={metadata.get('camera', {}).get('model', 'unknown')}")
            
            # VIDEO DURATION ENFORCEMENT
            # Check if this is a video and enforce duration limits
            file_extension = os.path.splitext(filename)[1].lower()
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']
            if file_extension in video_extensions:
                duration_seconds = metadata.get('duration_seconds')
                if duration_seconds:
                    duration_minutes = duration_seconds / 60.0
                    
                    # Enforce video duration limit
                    from handlers.subscription_handler import get_user_features
                    from utils.video_utils import enforce_video_duration_limit
                    
                    features, _, _ = get_user_features(user)
                    allowed, error_msg = enforce_video_duration_limit(user, duration_minutes, features)
                    
                    if not allowed:
                        # DELETE the video from S3 - exceeds plan limit
                        try:
                            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                            print(f"🚫 Deleted video {s3_key} - exceeds plan limit")
                        except Exception as delete_error:
                            print(f"Failed to delete video: {str(delete_error)}")
                        
                        return create_response(403, {
                            'error': error_msg,
                            'duration_minutes': round(duration_minutes, 2),
                            'action': 'Video has been rejected and deleted'
                        })
                    
                    print(f"✅ Video duration OK: {duration_minutes:.2f} minutes")
            
            # ==========================================
            # STORAGE STRATEGY: Single source of truth
            # ==========================================
            # Store ONLY the original file (RAW, HEIC, JPEG, video, etc.)
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
            print(f"Error processing upload: {str(e)}")
            
            # DELETE the file from S3 if there was an error
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                print(f" Deleted problematic file from S3: {s3_key}")
            except Exception as delete_error:
                print(f" Failed to delete problematic file: {str(delete_error)}")
            
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
            """Recursively convert float/rational to Decimal for DynamoDB"""
            if isinstance(obj, float):
                return Decimal(str(round(obj, 6)))
            # Handle PIL IFDRational (numerator/denominator)
            elif hasattr(obj, 'numerator') and hasattr(obj, 'denominator'):
                try:
                    return Decimal(str(round(float(obj), 6)))
                except:
                    return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(item) for item in obj]
            elif isinstance(obj, tuple):
                return [convert_floats_to_decimal(item) for item in obj]
            return obj
        
        # Clean metadata to ensure DynamoDB compatibility
        clean_metadata = convert_floats_to_decimal(metadata)
        
        # Step 8: Create photo record with comprehensive metadata
        # Links stored file to gallery and photographer
        
        # Generate CDN URLs for renditions (will be populated after processing)
        photo_urls = get_photo_urls(s3_key)
        
        # Determine if original is web-safe (JPEG, PNG, WebP)
        # If not (e.g. HEIC, RAW), we must use a converted rendition for the main 'url'
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        is_web_safe = ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']
        
        # Main display URL: use original if web-safe, otherwise use large rendition (JPEG)
        display_url = photo_urls['url']
        if not is_web_safe:
            # For HEIC/RAW, the 'url' field must point to a JPEG
            # We use the large rendition (4000px) as the main view
            display_url = photo_urls.get('large_url')
        
        # Download URL: always the original file
        original_download_url = photo_urls['url']
        
        photo = {
            'id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user['id'],
            'filename': filename,
            's3_key': s3_key,
            
            # Filename for display and download (same as uploaded)
            'original_filename': filename,
            
            # URLs (CloudFront CDN)
            'url': display_url,  # WEB-SAFE URL for viewing (JPEG if original was HEIC)
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
            'file_size': file_size,  # Actual file size for duplicate detection
            'size_mb': size_mb,
            'format': clean_metadata.get('format'),
            'dimensions': clean_metadata.get('dimensions'),
            'width': clean_metadata.get('dimensions', {}).get('width') if isinstance(clean_metadata.get('dimensions'), dict) else None,
            'height': clean_metadata.get('dimensions', {}).get('height') if isinstance(clean_metadata.get('dimensions'), dict) else None,
            
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
                # Check if this is a video file
                file_extension = os.path.splitext(filename)[1].lower()
                video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']
                is_video = file_extension in video_extensions
                
                if is_video:
                    # Use video processor for videos
                    from utils.video_processor import process_video_upload_async
                    print(f"🎬 Processing video for LocalStack: {s3_key}")
                    result = process_video_upload_async(s3_key, S3_BUCKET, image_data=image_data)
                else:
                    # Use image processor for images with watermark if enabled
                    from utils.image_processor import process_upload_async
                    from utils.config import users_table
                    
                    # Check if user has watermarking enabled
                    watermark_config = None
                    try:
                        user_response = users_table.get_item(Key={'email': user['email']})
                        if 'Item' in user_response:
                            user_data = user_response['Item']
                            if user_data.get('watermark_enabled', False) and user_data.get('watermark_s3_key'):
                                watermark_config = {
                                    'watermark_s3_key': user_data['watermark_s3_key'],
                                    'position': user_data.get('watermark_position', 'bottom-right'),
                                    'opacity': user_data.get('watermark_opacity', 0.7),
                                    'size_percent': user_data.get('watermark_size_percent', 15)
                                }
                                print(f"🎨 Watermarking enabled: {watermark_config['position']}, opacity: {watermark_config['opacity']}")
                    except Exception as wm_error:
                        print(f"⚠️ Could not load watermark config: {str(wm_error)}")
                    
                    print(f"🔄 Processing image for LocalStack: {s3_key}")
                    result = process_upload_async(s3_key, S3_BUCKET, image_data=image_data, watermark_config=watermark_config)
                
                if result.get('success'):
                    print(f"✅ Processing completed successfully")
                    
                    # Calculate total storage: original + all renditions
                    renditions = result.get('renditions', {})
                    renditions_size_bytes = sum(r['size'] for r in renditions.values())
                    renditions_size_mb = renditions_size_bytes / (1024 * 1024)
                    total_storage_mb = float(size_mb) + renditions_size_mb
                    
                    print(f"Storage breakdown:")
                    print(f"  Original: {float(size_mb):.2f} MB")
                    print(f"  Renditions: {renditions_size_mb:.2f} MB")
                    print(f"  Total: {total_storage_mb:.2f} MB")
                    
                    # Update photo with total storage and status
                    photo['status'] = 'active'
                    photo['size_mb'] = Decimal(str(round(total_storage_mb, 2)))
                    photo['renditions_size_mb'] = Decimal(str(round(renditions_size_mb, 2)))
                    
                    # For videos, add duration info if available
                    if is_video and metadata.get('duration_seconds'):
                        photo['duration_seconds'] = Decimal(str(metadata['duration_seconds']))
                        photo['duration_minutes'] = Decimal(str(metadata['duration_minutes']))
                        photo['type'] = 'video'
                    
                    photos_table.put_item(Item=photo)
                    
                    # Update gallery storage to include renditions
                    additional_storage = Decimal(str(round(renditions_size_mb, 2)))
                    try:
                        galleries_table.update_item(
                            Key={'user_id': user['id'], 'id': gallery_id},
                            UpdateExpression="SET storage_used = storage_used + :additional",
                            ExpressionAttributeValues={
                                ':additional': additional_storage
                            }
                        )
                        print(f"Updated gallery storage: +{renditions_size_mb:.2f} MB for renditions")
                    except Exception as storage_error:
                        print(f"Failed to update gallery storage for renditions: {storage_error}")
                else:
                    print(f"⚠️ Processing failed: {result.get('error')}")
            except Exception as proc_error:
                print(f"⚠️ LocalStack processing error: {str(proc_error)}")
                import traceback
                traceback.print_exc()
                # Don't fail the upload if processing fails
        
        # Update gallery photo count, storage, and thumbnail (for first photo)
        # Use atomic update to avoid race conditions when uploading multiple photos
        previous_photo_count = gallery.get('photo_count', 0)
        new_photo_count = previous_photo_count + 1  # Define new_photo_count before any try/except
        
        try:
            galleries_table.update_item(
                Key={'user_id': user['id'], 'id': gallery_id},
                UpdateExpression="SET photo_count = if_not_exists(photo_count, :zero) + :inc, storage_used = if_not_exists(storage_used, :zero) + :size, updated_at = :time, thumbnail_url = if_not_exists(thumbnail_url, :thumb), cover_photo_url = if_not_exists(cover_photo_url, :thumb)",
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':size': size_mb,
                    ':time': datetime.utcnow().isoformat() + 'Z',
                    ':thumb': photo_urls['thumbnail_url'],
                    ':zero': 0
                }
            )
        except Exception as e:
            print(f"Failed to update gallery stats atomically: {e}")
            # Fallback to non-atomic update
            current_storage_mb = gallery.get('storage_used', 0)
            if isinstance(current_storage_mb, Decimal):
                current_storage_mb = float(current_storage_mb)
            else:
                current_storage_mb = float(current_storage_mb) if current_storage_mb else 0.0
            new_storage_mb = Decimal(str(round(current_storage_mb + float(size_mb), 2)))
            
            gallery['photo_count'] = new_photo_count
            gallery['storage_used'] = new_storage_mb
            gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            if not gallery.get('thumbnail_url'):
                gallery['thumbnail_url'] = photo_urls['thumbnail_url']
            if not gallery.get('cover_photo_url'):
                gallery['cover_photo_url'] = photo_urls['thumbnail_url']
            galleries_table.put_item(Item=gallery)
        
        # Invalidate gallery ZIP file (delete it so it's regenerated on next download)
        # This is much faster than regenerating it synchronously
        try:
            zip_key = f"{gallery_id}/gallery-all-photos.zip"
            print(f" Invalidating gallery ZIP: {zip_key}")
            s3_client.delete_object(Bucket=S3_BUCKET, Key=zip_key)
        except Exception as zip_error:
            print(f" Failed to invalidate ZIP: {str(zip_error)}")
        
        # SEND "GALLERY READY" NOTIFICATION - When FIRST photo is uploaded
        if previous_photo_count == 0 and new_photo_count == 1:
            try:
                from handlers.notification_handler import notify_gallery_ready
                from utils.config import users_table
                
                # Get photographer details
                # Check user ID presence to avoid DynamoDB errors
                user_id = user.get('id')
                if not user_id:
                    print(f" Skipping notification: User ID missing in token")
                else:
                    photographer_response = users_table.get_item(Key={'id': user_id})
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
                                    user_id=user_id,
                                    gallery_id=gallery_id,
                                    client_email=client_email,
                                    client_name=client_name,
                                    photographer_name=photographer_name,
                                    gallery_url=gallery_url,
                                    message='Your gallery is now ready for viewing!'
                                )
                                print(f"Sent 'Gallery Ready' notification to {client_email}")
                            except Exception as email_error:
                                print(f" Failed to send Gallery Ready email to {client_email}: {str(email_error)}")
            except Exception as notif_error:
                print(f" Failed to send Gallery Ready notifications: {str(notif_error)}")
                # Don't fail the upload if notification fails
        
        print(f"Photo confirmed: {filename} ({size_mb:.2f} MB)")
        return create_response(201, photo)
        
    except Exception as e:
        print(f"Error confirming upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to confirm upload: {str(e)}'})

