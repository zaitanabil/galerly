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
from utils.image_security import validate_image_data, sanitize_image, generate_thumbnail, ImageSecurityError
from utils.cdn_urls import get_photo_urls  # CloudFront CDN URL helper

def handle_get_upload_url(gallery_id, user, event):
    """
    Generate presigned S3 URL for direct upload
    Step 1 of 3-step upload process
    """
    try:
        from utils.config import galleries_table
        
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
        
        # Extract file extension from original filename to preserve format
        import os
        file_extension = os.path.splitext(filename)[1] or '.jpg'  # Default to .jpg if no extension
        
        # Generate unique photo ID and S3 key with original extension
        photo_id = str(uuid.uuid4())
        s3_key = f"{gallery_id}/{photo_id}{file_extension}"
        
        # Generate presigned POST URL (allows uploads up to 5TB!)
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
        
        print(f"✅ Generated presigned URL for {filename}: {s3_key}")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'upload_url': presigned_data['url'],
            'upload_fields': presigned_data['fields'],
            'filename': filename,
            'file_size': file_size
        })
        
    except Exception as e:
        print(f"❌ Error generating upload URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to generate upload URL: {str(e)}'})


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
        # SECURITY: DOWNLOAD, VALIDATE & SANITIZE IMAGE
        # ==========================================
        try:
            print(f"🔒 Security check: Downloading {s3_key} for validation...")
            
            # Download file from S3 for validation
            s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
            image_data = s3_object['Body'].read()
            
            # 1. Validate image (check for code injection, polyglot, malware)
            validation_result = validate_image_data(image_data, filename)
            print(f"✅ Image validation passed: {validation_result}")
            
            # 2. SANITIZATION DISABLED - Preserve original quality
            print(f"ℹ️  Sanitization disabled - preserving original file quality")
            
            # 3-7. THUMBNAIL GENERATION MOVED TO CLOUDFRONT
            # ⚡ PERFORMANCE FIX: Synchronous thumbnail generation was causing 2-3 sec delay PER photo
            # Solution: CloudFront + Lambda@Edge will generate thumbnails on-demand
            print(f"⚡ FAST UPLOAD: CloudFront will generate thumbnails on-demand")
            
            # Use original file size
            file_size = len(image_data)
            
            # ==========================================
            # BIG TECH APPROACH: Store originals, transform via CDN
            # Instagram/Google Photos method:
            # - Accept ALL formats (RAW, HEIC, JPEG, etc.)
            # - Store original in S3
            # - CloudFront transforms for display (via URL params)
            # - Download gives original
            # ==========================================
            
            # Generate CloudFront CDN URLs
            # CloudFront will handle format conversion via URL parameters
            photo_urls = get_photo_urls(s3_key)
            
        except ImageSecurityError as security_error:
            print(f"🚨 SECURITY THREAT DETECTED: {str(security_error)}")
            
            # DELETE the malicious file from S3
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                print(f"🗑️  Deleted malicious file from S3: {s3_key}")
            except Exception as delete_error:
                print(f"⚠️  Failed to delete malicious file: {str(delete_error)}")
            
            # Return error to frontend
            return create_response(400, {
                'error': 'Security threat detected in uploaded file',
                'detail': str(security_error),
                'action': 'File has been rejected and deleted'
            })
        except Exception as validation_error:
            print(f"❌ Validation error: {str(validation_error)}")
            
            # Delete potentially problematic file
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                print(f"🗑️  Deleted problematic file from S3: {s3_key}")
            except:
                pass
            
            return create_response(400, {
                'error': 'Image validation failed',
                'detail': str(validation_error)
            })
        # ==========================================
        
        # Calculate size in MB
        size_mb = file_size / (1024 * 1024)
        
        # Create photo record with CloudFront CDN URLs
        photo = {
            'id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user['id'],
            'filename': filename,
            's3_key': s3_key,
            'url': photo_urls['url'],  # CloudFront URL for original
            'medium_url': photo_urls['medium_url'],  # CloudFront URL for medium (2000x2000)
            'thumbnail_url': photo_urls['thumbnail_url'],  # CloudFront URL for thumbnail (800x600)
            'title': body.get('title', ''),
            'description': body.get('description', ''),
            'tags': body.get('tags', []),
            'status': 'pending',
            'views': 0,
            'comments': [],
            'file_hash': file_hash,
            'file_size': file_size,
            'size_mb': Decimal(str(round(size_mb, 2))),
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        photos_table.put_item(Item=photo)
        
        # Update gallery photo count and storage
        previous_photo_count = gallery.get('photo_count', 0)
        new_photo_count = previous_photo_count + 1
        current_storage_mb = float(gallery.get('storage_used', 0))
        new_storage_mb = current_storage_mb + size_mb
        
        gallery['photo_count'] = new_photo_count
        gallery['storage_used'] = Decimal(str(round(new_storage_mb, 2)))
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

