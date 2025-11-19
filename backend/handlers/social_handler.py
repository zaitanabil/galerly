"""
Social sharing handlers
"""
import os
import re
import html
from utils.config import galleries_table, photos_table
from utils.response import create_response
from boto3.dynamodb.conditions import Key

def handle_get_gallery_share_info(gallery_id, user=None):
    """Get gallery share information including share URL and embed code"""
    try:
        # Validate and sanitize gallery_id
        if not gallery_id or not isinstance(gallery_id, str):
            return create_response(400, {'error': 'Invalid gallery ID'})
        
        # Sanitize: only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', gallery_id):
            return create_response(400, {'error': 'Invalid gallery ID format'})
        
        # Limit length to prevent abuse
        if len(gallery_id) > 128:
            return create_response(400, {'error': 'Gallery ID too long'})
        
        # Get gallery - check ownership if user provided
        if user:
            response = galleries_table.get_item(Key={
                'user_id': user['id'],
                'id': gallery_id
            })
        else:
            # Public access - find by share token or ID
            response = galleries_table.scan(
                FilterExpression='id = :gid',
                ExpressionAttributeValues={':gid': gallery_id}
            )
            if response.get('Items'):
                response = {'Item': response['Items'][0]}
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = response['Item']
        
        # Check if gallery is public or user owns it
        if user and gallery.get('user_id') != user['id']:
            if gallery.get('privacy', 'private') != 'public':
                return create_response(403, {'error': 'Access denied'})
        
        # Generate share URL from environment variable (no fallback)
        frontend_url = os.environ.get('FRONTEND_URL')
        if not frontend_url:
            return create_response(500, {'error': 'FRONTEND_URL environment variable not configured'})
        
        # Use client-gallery page with token parameter
        share_token = gallery.get('share_token')
        if share_token:
            share_url = f"{frontend_url}/client-gallery?token={share_token}"
        else:
            # Fallback: use gallery ID directly
            share_url = f"{frontend_url}/client-gallery?id={gallery_id}"
        
        # Generate embed code with sanitized URL
        # Escape HTML to prevent XSS
        safe_share_url = html.escape(share_url)
        embed_code = f'''<iframe 
    src="{safe_share_url}" 
    width="100%" 
    height="600" 
    frameborder="0" 
    allowfullscreen>
</iframe>'''
        
        return create_response(200, {
            'gallery_id': gallery_id,
            'gallery_name': gallery.get('name', 'Gallery'),
            'share_url': share_url,
            'embed_code': embed_code,
            'is_public': gallery.get('privacy', 'private') == 'public'
        })
    except Exception as e:
        print(f"Error getting gallery share info: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get share information'})

def handle_get_photo_share_info(photo_id, user=None):
    """Get photo share information including direct URL"""
    try:
        # Validate and sanitize photo_id
        if not photo_id or not isinstance(photo_id, str):
            return create_response(400, {'error': 'Invalid photo ID'})
        
        # Sanitize: only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', photo_id):
            return create_response(400, {'error': 'Invalid photo ID format'})
        
        # Limit length to prevent abuse
        if len(photo_id) > 128:
            return create_response(400, {'error': 'Photo ID too long'})
        
        # Get photo
        response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = response['Item']
        gallery_id = photo.get('gallery_id')
        
        if not gallery_id:
            return create_response(400, {'error': 'Photo has no associated gallery'})
        
        # Get gallery to check access
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        
        # Check if user owns gallery or gallery is public
        if user and gallery.get('user_id') != user['id']:
            if gallery.get('privacy', 'private') != 'public':
                return create_response(403, {'error': 'Access denied'})
        
        photo_url = photo.get('url', '')
        
        # Generate gallery share URL from environment variable (no fallback)
        frontend_url = os.environ.get('FRONTEND_URL')
        if not frontend_url:
            return create_response(500, {'error': 'FRONTEND_URL environment variable not configured'})
        
        # Use client-gallery page with token parameter
        share_token = gallery.get('share_token')
        if share_token:
            gallery_share_url = f"{frontend_url}/client-gallery?token={share_token}"
        else:
            # Fallback: use gallery ID directly
            gallery_share_url = f"{frontend_url}/client-gallery?id={gallery_id}"
        
        # Create share URL that opens photo in gallery
        photo_share_url = f"{gallery_share_url}&photo={photo_id}"
        
        return create_response(200, {
            'photo_id': photo_id,
            'photo_url': photo_url,
            'gallery_id': gallery_id,
            'gallery_name': gallery.get('name', 'Gallery'),
            'share_url': photo_share_url,
            'direct_image_url': photo_url,
            'is_public': gallery.get('privacy', 'private') == 'public'
        })
    except Exception as e:
        print(f"Error getting photo share info: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get share information'})

