"""
Security utilities for user data isolation
"""
from .response import create_response

def require_auth(handler):
    """
    Decorator to require authentication for an endpoint.
    Extracts user_id from session and passes it to the handler.
    Supports both HttpOnly cookies and Authorization header (fallback).
    """
    def wrapper(event, context):
        # Get session token from Cookie or Authorization header
        from .auth import get_token_from_event, get_session
        
        token = get_token_from_event(event)
        
        if not token:
            return create_response(401, {'error': 'Authentication required'})
        
        # Get user_id from session
        session = get_session(token)
        
        if not session:
            return create_response(401, {'error': 'Invalid or expired session'})
        
        # Pass user_id to the handler
        event['user_id'] = session.get('user_id')
        event['user_email'] = session.get('email')
        
        return handler(event, context)
    
    return wrapper

def check_gallery_ownership(user_id, gallery_id):
    """
    Check if a user owns a gallery.
    Returns True if authorized, False otherwise.
    """
    import boto3
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    galleries_table = dynamodb.Table('galerly-galleries')
    
    try:
        response = galleries_table.get_item(
            Key={
                'user_id': user_id,
                'id': gallery_id
            }
        )
        
        return 'Item' in response
    except Exception as e:
        print(f"❌ Error checking gallery ownership: {str(e)}")
        return False

def check_photo_ownership(user_id, photo_id):
    """
    Check if a user owns a photo.
    Returns True if authorized, False otherwise.
    """
    import boto3
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    photos_table = dynamodb.Table('galerly-photos')
    
    try:
        # Get photo to check user_id
        response = photos_table.get_item(Key={'id': photo_id})
        
        if 'Item' not in response:
            return False
        
        photo = response['Item']
        
        # Check if photo's user_id matches
        return photo.get('user_id') == user_id
    except Exception as e:
        print(f"❌ Error checking photo ownership: {str(e)}")
        return False

def filter_user_data(items, user_id, user_field='user_id'):
    """
    Filter a list of items to only include those belonging to the user.
    
    Args:
        items: List of items from DynamoDB
        user_id: The authenticated user's ID
        user_field: The field name that contains the user ID (default: 'user_id')
    
    Returns:
        Filtered list containing only the user's items
    """
    return [item for item in items if item.get(user_field) == user_id]

def ensure_user_field(item, user_id):
    """
    Ensure an item has the user_id field set correctly before saving.
    This prevents users from creating items for other users.
    
    Args:
        item: The item dict to be saved
        user_id: The authenticated user's ID
    
    Returns:
        Item dict with user_id set
    """
    item['user_id'] = user_id
    return item

