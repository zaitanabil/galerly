"""
Multipart Upload Handler - Steps 1-5 of Professional Workflow
Handles large file uploads with resume capability
"""
import uuid
import json
from datetime import datetime
from decimal import Decimal
from utils.config import s3_client, S3_BUCKET, galleries_table, photos_table, AWS_ENDPOINT_URL
from utils.response import create_response


def handle_initialize_multipart_upload(gallery_id, user, event):
    """
    Step 1-2: Initialize multipart upload for large files
    Returns upload URLs for each part
    """
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename')
        file_size = body.get('file_size')
        content_type = body.get('content_type', 'application/octet-stream')
        
        if not filename or not file_size:
            return create_response(400, {'error': 'filename and file_size required'})
        
        # Generate unique photo ID and S3 key
        photo_id = str(uuid.uuid4())
        import os
        file_extension = os.path.splitext(filename)[1].lower() or '.jpg'
        
        # Use original filename in S3 key, with UUID prefix for uniqueness
        # Format: gallery_id/photo_id_original_filename.ext
        # This preserves the original name while ensuring uniqueness
        base_filename = os.path.splitext(filename)[0]  # Name without extension
        s3_key = f"{gallery_id}/{photo_id}_{base_filename}{file_extension}"
        
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
        
        # Calculate number of parts
        chunk_size = int(os.environ.get('MULTIPART_CHUNK_SIZE'))
        num_parts = (file_size + chunk_size - 1) // chunk_size
        
        # Initialize S3 multipart upload
        multipart_upload = s3_client.create_multipart_upload(
            Bucket=S3_BUCKET,
            Key=s3_key,
            ContentType=content_type
        )
        
        upload_id = multipart_upload['UploadId']
        
        # Generate presigned URLs for each part
        upload_parts = []
        for part_number in range(1, num_parts + 1):
            part_url = s3_client.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': S3_BUCKET,
                    'Key': s3_key,
                    'UploadId': upload_id,
                    'PartNumber': part_number
                },
                ExpiresIn=3600  # 1 hour per part
            )
            
            # LocalStack fix: Replace internal Docker hostname with localhost for browser access
            if 'localstack' in part_url:
                part_url = part_url.replace('http://localstack:', 'http://localhost:')
            
            upload_parts.append({
                'part_number': part_number,
                'url': part_url
            })
        
        print(f"Initialized multipart upload: {filename} ({num_parts} parts)")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'upload_type': 'multipart',
            'multipart_upload_id': upload_id,
            'upload_parts': upload_parts,
            'chunk_size': chunk_size
        })
        
    except Exception as e:
        print(f"Error initializing multipart upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to initialize upload: {str(e)}'})


def handle_complete_multipart_upload(gallery_id, user, event):
    """
    Step 5: Complete multipart upload after all parts uploaded
    Assembles chunks into complete file
    """
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        photo_id = body.get('photo_id')
        upload_id = body.get('upload_id')
        parts = body.get('parts')  # [{'PartNumber': 1, 'ETag': '...'}]
        
        if not photo_id or not upload_id or not parts:
            return create_response(400, {'error': 'photo_id, upload_id, and parts required'})
        
        # Get S3 key from request (preferred) or reconstruct
        s3_key = body.get('s3_key')
        
        if not s3_key:
            # Fallback: Try to reconstruct (requires filename to be accurate)
            filename = body.get('filename')
            if filename:
                import os
                file_extension = os.path.splitext(filename)[1] or '.jpg'
                s3_key = f"{gallery_id}/{photo_id}{file_extension}"
            else:
                # Last resort fallback (often fails for files with extensions)
                # This was the cause of the NoSuchUpload error
                s3_key = f"{gallery_id}/{photo_id}"
        
        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=S3_BUCKET,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        print(f"Completed multipart upload: {s3_key}")
        
        # Get file info from S3
        head_response = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        file_size = head_response['ContentLength']
        size_mb = round(file_size / (1024 * 1024), 2)
        
        # Get filename from request or extract from s3_key
        filename = body.get('filename', s3_key.split('/')[-1])
        
        # Get file hash if provided
        file_hash = body.get('file_hash', '')
        
        # Create photo record in DynamoDB
        from datetime import datetime
        from decimal import Decimal
        from utils.cdn_urls import get_photo_urls
        
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Generate CDN URLs for all renditions
        photo_urls = get_photo_urls(s3_key)
        
        photo = {
            'id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user['id'],
            'filename': filename,
            'original_filename': filename,  # For multipart, the original IS the uploaded file
            's3_key': s3_key,
            'size': file_size,
            'file_size': file_size,  # For duplicate detection
            'size_mb': Decimal(str(size_mb)),
            'status': 'processing',  # Will be updated to 'active' after renditions generated
            'created_at': current_time,
            'updated_at': current_time,
            'file_hash': file_hash,
            # CDN URLs for responsive display
            'url': photo_urls['url'],  # Original file URL
            'original_download_url': photo_urls['url'],  # Explicit original download URL
            'thumbnail_url': photo_urls['thumbnail_url'],
            'small_url': photo_urls['small_url'],
            'medium_url': photo_urls['medium_url'],
            'large_url': photo_urls['large_url']
        }
        
        photos_table.put_item(Item=photo)
        print(f"Created photo record: {photo_id}")
        
        # Trigger image processing for LocalStack
        # In production, Lambda is triggered by S3 event
        renditions_size_mb = 0
        if AWS_ENDPOINT_URL and 'localstack' in AWS_ENDPOINT_URL.lower():
            try:
                from utils.image_processor import process_upload_async
                print(f"🔄 Processing image for LocalStack: {s3_key}")
                result = process_upload_async(s3_key, S3_BUCKET)
                if result.get('success'):
                    print(f"Renditions generated successfully")
                    
                    # Calculate total storage: original + all renditions
                    renditions = result.get('renditions', {})
                    renditions_size_bytes = sum(r['size'] for r in renditions.values())
                    renditions_size_mb = renditions_size_bytes / (1024 * 1024)
                    total_storage_mb = size_mb + renditions_size_mb
                    
                    print(f"Storage breakdown:")
                    print(f"  Original: {size_mb:.2f} MB")
                    print(f"  Renditions: {renditions_size_mb:.2f} MB")
                    print(f"  Total: {total_storage_mb:.2f} MB")
                    
                    # Update photo with total storage and status
                    photo['status'] = 'active'
                    photo['size_mb'] = Decimal(str(round(total_storage_mb, 2)))
                    photo['renditions_size_mb'] = Decimal(str(round(renditions_size_mb, 2)))
                    photos_table.put_item(Item=photo)
                else:
                    print(f"⚠️ Rendition generation failed: {result.get('error')}")
            except Exception as proc_error:
                print(f"⚠️ LocalStack processing error: {str(proc_error)}")
        
        # Update gallery photo count, storage, and thumbnail (for first photo)
        # Use atomic update to avoid race conditions
        # Include both original and renditions in storage calculation
        total_size_for_gallery = Decimal(str(round(size_mb + renditions_size_mb, 2)))
        try:
            galleries_table.update_item(
                Key={'user_id': user['id'], 'id': gallery_id},
                UpdateExpression="SET photo_count = if_not_exists(photo_count, :zero) + :inc, storage_used = if_not_exists(storage_used, :zero) + :size, updated_at = :time, thumbnail_url = if_not_exists(thumbnail_url, :thumb), cover_photo_url = if_not_exists(cover_photo_url, :thumb)",
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':size': total_size_for_gallery,
                    ':time': current_time,
                    ':thumb': photo_urls['thumbnail_url'],
                    ':zero': 0
                }
            )
            print(f"Updated gallery atomically with thumbnail and total storage ({float(total_size_for_gallery):.2f} MB)")
        except Exception as e:
            print(f"Failed to update gallery stats atomically: {e}")
            # Fallback to non-atomic update
            gallery = response['Item']
            previous_photo_count = gallery.get('photo_count', 0)
            new_photo_count = previous_photo_count + 1
            current_storage_mb = gallery.get('storage_used', 0)
            if isinstance(current_storage_mb, Decimal):
                current_storage_mb = float(current_storage_mb)
            else:
                current_storage_mb = float(current_storage_mb) if current_storage_mb else 0.0
            new_storage_mb = Decimal(str(round(current_storage_mb + size_mb + renditions_size_mb, 2)))
            
            gallery['photo_count'] = new_photo_count
            gallery['storage_used'] = new_storage_mb
            gallery['updated_at'] = current_time
            if not gallery.get('thumbnail_url'):
                gallery['thumbnail_url'] = photo_urls['thumbnail_url']
            if not gallery.get('cover_photo_url'):
                gallery['cover_photo_url'] = photo_urls['thumbnail_url']
            galleries_table.put_item(Item=gallery)
            print(f"Updated gallery: photo_count={new_photo_count}, storage={new_storage_mb}MB")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'status': 'completed',
            'photo': photo
        })
        
    except Exception as e:
        print(f"Error completing multipart upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to complete upload: {str(e)}'})


def handle_abort_multipart_upload(gallery_id, user, event):
    """
    Abort multipart upload (cleanup on failure)
    """
    try:
        # Verify gallery ownership
        response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in response:
            return create_response(403, {'error': 'Access denied'})
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        photo_id = body.get('photo_id')
        upload_id = body.get('upload_id')
        
        if not photo_id or not upload_id:
            return create_response(400, {'error': 'photo_id and upload_id required'})
        
        # Reconstruct S3 key
        s3_key = f"{gallery_id}/{photo_id}"
        
        # Abort multipart upload
        s3_client.abort_multipart_upload(
            Bucket=S3_BUCKET,
            Key=s3_key,
            UploadId=upload_id
        )
        
        print(f"Aborted multipart upload: {s3_key}")
        
        return create_response(200, {'status': 'aborted'})
        
    except Exception as e:
        print(f"Error aborting multipart upload: {str(e)}")
        return create_response(500, {'error': f'Failed to abort upload: {str(e)}'})

