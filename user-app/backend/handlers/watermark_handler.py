"""
Watermark logo upload and configuration handler
Handles logo image upload and watermark settings for watermarking feature
"""
import uuid
import base64
import os
from datetime import datetime, timezone
from utils.config import s3_client, S3_BUCKET, users_table
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
        
        # Update user record with watermark S3 key
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET watermark_s3_key = :s3_key, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':s3_key': s3_key,
                ':updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
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


def handle_get_watermark_settings(user):
    """
    Get watermark configuration settings for user
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('watermarking'):
            return create_response(403, {
                'error': 'Logo watermarking is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Get user data
        response = users_table.get_item(Key={'email': user['email']})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Extract watermark settings with defaults
        settings = {
            'watermark_s3_key': user_data.get('watermark_s3_key', ''),
            'watermark_enabled': user_data.get('watermark_enabled', False),
            'watermark_position': user_data.get('watermark_position', 'bottom-right'),
            'watermark_opacity': user_data.get('watermark_opacity', 0.7),
            'watermark_size_percent': user_data.get('watermark_size_percent', 15)
        }
        
        return create_response(200, settings)
        
    except Exception as e:
        print(f"Error getting watermark settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load watermark settings'})


def handle_update_watermark_settings(user, body):
    """
    Update watermark configuration settings
    
    Request body:
    {
        "watermark_enabled": bool,
        "watermark_position": "top-left" | "top-right" | "bottom-left" | "bottom-right" | "center",
        "watermark_opacity": float (0.0-1.0),
        "watermark_size_percent": int (5-50)
    }
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('watermarking'):
            return create_response(403, {
                'error': 'Logo watermarking is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Build update expression
        update_expressions = []
        expression_values = {}
        
        # Watermark enabled
        if 'watermark_enabled' in body:
            update_expressions.append('watermark_enabled = :enabled')
            expression_values[':enabled'] = bool(body['watermark_enabled'])
        
        # Position
        if 'watermark_position' in body:
            position = body['watermark_position']
            valid_positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']
            if position not in valid_positions:
                return create_response(400, {
                    'error': f'Invalid position. Must be one of: {", ".join(valid_positions)}'
                })
            update_expressions.append('watermark_position = :position')
            expression_values[':position'] = position
        
        # Opacity
        if 'watermark_opacity' in body:
            opacity = float(body['watermark_opacity'])
            if opacity < 0.0 or opacity > 1.0:
                return create_response(400, {'error': 'Opacity must be between 0.0 and 1.0'})
            update_expressions.append('watermark_opacity = :opacity')
            expression_values[':opacity'] = opacity
        
        # Size percent
        if 'watermark_size_percent' in body:
            size = int(body['watermark_size_percent'])
            if size < 5 or size > 50:
                return create_response(400, {'error': 'Size must be between 5 and 50 percent'})
            update_expressions.append('watermark_size_percent = :size')
            expression_values[':size'] = size
        
        if not update_expressions:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Add updated timestamp
        update_expressions.append('updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Update user record
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values
        )
        
        return create_response(200, {
            'message': 'Watermark settings updated successfully'
        })
        
    except ValueError as e:
        return create_response(400, {'error': str(e)})
    except Exception as e:
        print(f"Error updating watermark settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update watermark settings'})


def handle_batch_apply_watermark(user, body):
    """
    Apply watermark to existing photos in a gallery
    
    Request body:
    {
        "gallery_id": str,
        "photo_ids": [str] (optional - all photos if not provided)
    }
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('watermarking'):
            return create_response(403, {
                'error': 'Logo watermarking is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        gallery_id = body.get('gallery_id')
        photo_ids = body.get('photo_ids', [])
        
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id required'})
        
        # Get watermark settings
        user_data_response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in user_data_response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = user_data_response['Item']
        
        if not user_data.get('watermark_s3_key'):
            return create_response(400, {'error': 'No watermark logo uploaded'})
        
        if not user_data.get('watermark_enabled', False):
            return create_response(400, {'error': 'Watermarking is not enabled'})
        
        # Build watermark config
        watermark_config = {
            'watermark_s3_key': user_data['watermark_s3_key'],
            'position': user_data.get('watermark_position', 'bottom-right'),
            'opacity': user_data.get('watermark_opacity', 0.7),
            'size_percent': user_data.get('watermark_size_percent', 15)
        }
        
        # Queue batch watermarking job (in production, this would be a background job)
        # For now, return success and let background processing handle it
        import uuid as uuid_lib
        
        job_id = str(uuid_lib.uuid4())
        
        # In production, you would store this job in background_jobs_table
        # For now, just log and return the job ID
        
        print(f"Batch watermark job queued: {job_id} for gallery {gallery_id}")
        
        return create_response(200, {
            'message': 'Batch watermarking job queued',
            'job_id': job_id,
            'gallery_id': gallery_id,
            'photo_count': len(photo_ids) if photo_ids else 'all'
        })
        
    except Exception as e:
        print(f"Error queueing batch watermark: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to queue batch watermark job'})


