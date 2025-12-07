"""
Watermark logo upload handler
Handles logo image upload for watermarking feature
"""
import uuid
import base64
import os
from datetime import datetime
from utils.config import s3_client, S3_BUCKET
from utils.response import create_response
from handlers.subscription_handler import get_user_features


def handle_upload_watermark_logo(user, body):
    """
    Upload watermark logo image
    Plus, Pro, Ultimate plans only
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('watermarking'):
            return create_response(403, {
                'error': 'Logo watermarking is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Get file data
        file_data_b64 = body.get('file_data', '')
        filename = body.get('filename', 'logo.png')
        
        if not file_data_b64:
            return create_response(400, {'error': 'file_data required'})
        
        # Remove data URL prefix if present
        if 'base64,' in file_data_b64:
            file_data_b64 = file_data_b64.split('base64,')[1]
        
        # Decode
        try:
            file_data = base64.b64decode(file_data_b64)
        except Exception as e:
            return create_response(400, {'error': f'Invalid base64 data: {str(e)}'})
        
        # Validate file size (max 2MB)
        if len(file_data) > 2 * 1024 * 1024:
            return create_response(400, {'error': 'Logo file must be less than 2MB'})
        
        # Validate image
        from utils.image_security import validate_image_data
        try:
            validation_result = validate_image_data(file_data, filename)
        except Exception as e:
            return create_response(400, {'error': f'Invalid image file: {str(e)}'})
        
        # Generate S3 key
        file_ext = os.path.splitext(filename)[1] or '.png'
        logo_id = str(uuid.uuid4())
        s3_key = f"watermarks/{user['id']}/{logo_id}{file_ext}"
        
        # Upload to S3
        content_type = 'image/png'
        if file_ext == '.jpg' or file_ext == '.jpeg':
            content_type = 'image/jpeg'
        elif file_ext == '.webp':
            content_type = 'image/webp'
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type
        )
        
        print(f"Uploaded watermark logo: {s3_key}")
        
        # Return S3 key for saving to profile
        return create_response(200, {
            's3_key': s3_key,
            'message': 'Logo uploaded successfully'
        })
        
    except Exception as e:
        print(f"Error uploading watermark logo: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to upload logo'})

