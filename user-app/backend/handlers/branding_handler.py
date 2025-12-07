"""
Branding / White Label configuration handlers
Allows photographers to remove Galerly branding and use custom branding
"""
import os
import uuid
import base64
from datetime import datetime
from utils.config import users_table, s3_client, S3_BUCKET
from utils.response import create_response
from handlers.subscription_handler import get_user_features


def handle_get_branding_settings(user):
    """Get white label branding settings for user"""
    try:
        # Check plan access
        features, _, _ = get_user_features(user)
        
        # Get user data
        response = users_table.get_item(Key={'email': user['email']})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Extract branding settings
        branding_settings = {
            'hide_galerly_branding': user_data.get('hide_galerly_branding', False),
            'custom_branding': {
                'enabled': user_data.get('custom_branding_enabled', False),
                'logo_url': user_data.get('custom_branding_logo_url', ''),
                'business_name': user_data.get('custom_branding_business_name', ''),
                'tagline': user_data.get('custom_branding_tagline', ''),
                'footer_text': user_data.get('custom_branding_footer_text', '')
            },
            'theme_customization': {
                'enabled': user_data.get('theme_customization_enabled', False),
                'primary_color': user_data.get('theme_primary_color', '#0066CC'),
                'secondary_color': user_data.get('theme_secondary_color', '#FFD700'),
                'font_family': user_data.get('theme_font_family', 'Inter')
            },
            'has_access': features.get('remove_branding', False)
        }
        
        return create_response(200, branding_settings)
        
    except Exception as e:
        print(f"Error getting branding settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load branding settings'})


def handle_update_branding_settings(user, body):
    """Update white label branding settings"""
    try:
        # Check plan access
        features, _, _ = get_user_features(user)
        
        if not features.get('remove_branding'):
            return create_response(403, {
                'error': 'White label branding is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True,
                'required_feature': 'remove_branding'
            })
        
        # Build update expression
        update_expressions = []
        expression_values = {}
        
        # Hide Galerly branding
        if 'hide_galerly_branding' in body:
            update_expressions.append('hide_galerly_branding = :hide_branding')
            expression_values[':hide_branding'] = bool(body['hide_galerly_branding'])
        
        # Custom branding settings
        if 'custom_branding' in body:
            branding = body['custom_branding']
            
            if 'enabled' in branding:
                update_expressions.append('custom_branding_enabled = :cb_enabled')
                expression_values[':cb_enabled'] = bool(branding['enabled'])
            
            if 'logo_url' in branding:
                update_expressions.append('custom_branding_logo_url = :cb_logo')
                expression_values[':cb_logo'] = str(branding['logo_url'])
            
            if 'business_name' in branding:
                update_expressions.append('custom_branding_business_name = :cb_name')
                expression_values[':cb_name'] = str(branding['business_name'])
            
            if 'tagline' in branding:
                update_expressions.append('custom_branding_tagline = :cb_tagline')
                expression_values[':cb_tagline'] = str(branding['tagline'])
            
            if 'footer_text' in branding:
                update_expressions.append('custom_branding_footer_text = :cb_footer')
                expression_values[':cb_footer'] = str(branding['footer_text'])
        
        # Theme customization
        if 'theme_customization' in body:
            theme = body['theme_customization']
            
            if 'enabled' in theme:
                update_expressions.append('theme_customization_enabled = :theme_enabled')
                expression_values[':theme_enabled'] = bool(theme['enabled'])
            
            if 'primary_color' in theme:
                update_expressions.append('theme_primary_color = :theme_primary')
                expression_values[':theme_primary'] = str(theme['primary_color'])
            
            if 'secondary_color' in theme:
                update_expressions.append('theme_secondary_color = :theme_secondary')
                expression_values[':theme_secondary'] = str(theme['secondary_color'])
            
            if 'font_family' in theme:
                update_expressions.append('theme_font_family = :theme_font')
                expression_values[':theme_font'] = str(theme['font_family'])
        
        # Check if any fields to update (before adding updated_at)
        if not update_expressions:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Add updated timestamp
        update_expressions.append('updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update user record
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values
        )
        
        return create_response(200, {
            'message': 'Branding settings updated successfully'
        })
        
    except Exception as e:
        print(f"Error updating branding settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update branding settings'})


def handle_upload_branding_logo(user, body):
    """Upload custom branding logo"""
    try:
        # Check plan access
        features, _, _ = get_user_features(user)
        
        if not features.get('remove_branding'):
            return create_response(403, {
                'error': 'Custom branding is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        file_data = body.get('file_data')
        filename = body.get('filename', 'logo.png')
        
        if not file_data:
            return create_response(400, {'error': 'file_data required'})
        
        # Extract base64 data (remove data:image/...;base64, prefix if present)
        if ',' in file_data:
            file_data = file_data.split(',')[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(file_data)
        except Exception as decode_error:
            print(f"Error decoding base64: {str(decode_error)}")
            return create_response(400, {'error': 'Invalid base64 data'})
        
        # Validate file size (max 2MB)
        if len(image_bytes) > 2 * 1024 * 1024:
            return create_response(400, {'error': 'Logo file must be less than 2MB'})
        
        # Generate unique S3 key
        file_extension = filename.split('.')[-1] if '.' in filename else 'png'
        s3_key = f"branding-logos/{user['id']}/{uuid.uuid4()}.{file_extension}"
        
        # Determine content type
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(file_extension.lower(), 'image/png')
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
            CacheControl='public, max-age=31536000'  # 1 year cache
        )
        
        # Generate URL
        logo_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
        
        # Optionally update user record immediately
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET custom_branding_logo_url = :logo_url, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':logo_url': logo_url,
                ':updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        print(f"✅ Branding logo uploaded: {s3_key}")
        
        return create_response(200, {
            'url': logo_url,
            's3_key': s3_key,
            'message': 'Logo uploaded successfully'
        })
        
    except Exception as e:
        print(f"Error uploading branding logo: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to upload logo'})


def handle_get_public_branding(photographer_id):
    """
    Get public branding settings for a photographer (used by client galleries)
    No authentication required - public endpoint
    """
    try:
        # Get photographer data
        response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='id = :id',
            ExpressionAttributeValues={':id': photographer_id}
        )
        
        if not response.get('Items'):
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = response['Items'][0]
        
        # Check plan and build branding response
        features, _, _ = get_user_features(photographer)
        
        branding = {
            'hide_galerly_branding': photographer.get('hide_galerly_branding', False) and features.get('remove_branding', False),
            'custom_branding': {
                'enabled': photographer.get('custom_branding_enabled', False) and features.get('remove_branding', False),
                'logo_url': photographer.get('custom_branding_logo_url', ''),
                'business_name': photographer.get('custom_branding_business_name', ''),
                'tagline': photographer.get('custom_branding_tagline', ''),
                'footer_text': photographer.get('custom_branding_footer_text', '')
            },
            'theme_customization': {
                'enabled': photographer.get('theme_customization_enabled', False) and features.get('remove_branding', False),
                'primary_color': photographer.get('theme_primary_color', '#0066CC'),
                'secondary_color': photographer.get('theme_secondary_color', '#FFD700'),
                'font_family': photographer.get('theme_font_family', 'Inter')
            },
            'photographer_name': photographer.get('name', photographer.get('username', 'Photographer'))
        }
        
        return create_response(200, branding)
        
    except Exception as e:
        print(f"Error getting public branding: {str(e)}")
        return create_response(500, {'error': 'Failed to load branding'})
