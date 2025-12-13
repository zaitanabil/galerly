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
from utils.plan_enforcement import require_plan, require_role


@require_plan(feature='watermarking')
@require_role('photographer')
def handle_upload_watermark_logo(user, body):
    """
    Upload watermark logo image
    Plus, Pro, Ultimate plans only
    """
    try:
        # Plan enforcement handled by decorators
        
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


@require_plan(feature='watermarking')
def handle_get_watermark_settings(user):
    """
    Get watermark configuration settings for user
    """
    try:
        # Plan enforcement handled by decorator
        
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


@require_plan(feature='watermarking')
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
        # Plan enforcement handled by decorator
        
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


@require_plan(feature='watermarking')
@require_role('photographer')
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
        # Plan enforcement handled by decorators
        
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
        
        # Get photos from gallery
        from utils.config import photos_table
        from boto3.dynamodb.conditions import Key
        
        if photo_ids:
            # Process specific photos
            photos_to_process = []
            for photo_id in photo_ids:
                response = photos_table.get_item(
                    Key={'id': photo_id, 'gallery_id': gallery_id}
                )
                if 'Item' in response:
                    photos_to_process.append(response['Item'])
        else:
            # Process all photos in gallery
            response = photos_table.query(
                IndexName='gallery_id-created_at-index',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            photos_to_process = response.get('Items', [])
        
        if not photos_to_process:
            return create_response(404, {'error': 'No photos found to watermark'})
        
        # Apply watermark to each photo
        from utils.image_processor import generate_renditions_with_watermark
        
        processed_count = 0
        failed_count = 0
        
        for photo in photos_to_process:
            try:
                s3_key = photo.get('s3_key')
                if not s3_key:
                    continue
                
                # Regenerate renditions with watermark
                result = generate_renditions_with_watermark(
                    s3_key=s3_key,
                    watermark_config=watermark_config
                )
                
                if result.get('success'):
                    processed_count += 1
                    print(f"✓ Watermarked: {s3_key}")
                    
                    # Update photo record with watermarked flag
                    photos_table.update_item(
                        Key={'id': photo['id'], 'gallery_id': gallery_id},
                        UpdateExpression='SET watermarked = :true, updated_at = :now',
                        ExpressionAttributeValues={
                            ':true': True,
                            ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                        }
                    )
                else:
                    failed_count += 1
                    print(f"✗ Failed to watermark: {s3_key}")
            
            except Exception as photo_error:
                failed_count += 1
                print(f"Error watermarking photo {photo.get('id')}: {str(photo_error)}")
        
        return create_response(200, {
            'message': 'Batch watermarking completed',
            'processed': processed_count,
            'failed': failed_count,
            'total': len(photos_to_process)
        })
        
    except Exception as e:
        print(f"Error in batch watermark: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to apply batch watermark'})

