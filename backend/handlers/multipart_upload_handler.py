"""
Multipart Upload Handler - Steps 1-5 of Professional Workflow
Handles large file uploads with resume capability
"""
import uuid
import json
from datetime import datetime
from utils.config import s3_client, S3_BUCKET, galleries_table, photos_table
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
        file_extension = os.path.splitext(filename)[1] or '.jpg'
        s3_key = f"{gallery_id}/{photo_id}{file_extension}"
        
        # Calculate number of parts (10MB chunks)
        chunk_size = 10 * 1024 * 1024  # 10MB
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
            
            upload_parts.append({
                'part_number': part_number,
                'url': part_url
            })
        
        print(f"✅ Initialized multipart upload: {filename} ({num_parts} parts)")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'upload_type': 'multipart',
            'multipart_upload_id': upload_id,
            'upload_parts': upload_parts,
            'chunk_size': chunk_size
        })
        
    except Exception as e:
        print(f"❌ Error initializing multipart upload: {str(e)}")
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
        
        # Get S3 key from photo_id
        # Note: In production, store this in a temporary session table
        # For now, reconstruct from gallery_id/photo_id
        s3_key = f"{gallery_id}/{photo_id}"
        
        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=S3_BUCKET,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        print(f"✅ Completed multipart upload: {s3_key}")
        
        return create_response(200, {
            'photo_id': photo_id,
            's3_key': s3_key,
            'status': 'completed'
        })
        
    except Exception as e:
        print(f"❌ Error completing multipart upload: {str(e)}")
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
        
        print(f"✅ Aborted multipart upload: {s3_key}")
        
        return create_response(200, {'status': 'aborted'})
        
    except Exception as e:
        print(f"❌ Error aborting multipart upload: {str(e)}")
        return create_response(500, {'error': f'Failed to abort upload: {str(e)}'})

