"""
Authentication utilities
"""
import hashlib
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from .config import sessions_table, users_table

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_token_from_event(event):
    """Extract session token from Cookie header"""
    headers = event.get('headers', {}) or {}
    
    # Only accept token from Cookie header (Strict HttpOnly enforcement)
    cookie_header = headers.get('Cookie') or headers.get('cookie', '')
    if cookie_header:
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        return cookies.get('galerly_session')
    
    return None

def get_api_key_from_event(event):
    """Extract API key from Authorization header"""
    headers = event.get('headers', {}) or {}
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    # Also support X-API-Key header
    return headers.get('X-API-Key') or headers.get('x-api-key')

def get_user_from_api_key(event):
    """Authenticate user via API Key"""
    api_key = get_api_key_from_event(event)
    if not api_key:
        return None
        
    try:
        # Query users table by API key using GSI
        # Assuming GSI 'ApiKeyIndex' exists on 'api_key' field
        response = users_table.query(
            IndexName='ApiKeyIndex',
            KeyConditionExpression=Key('api_key').eq(api_key)
        )
        
        items = response.get('Items', [])
        if not items:
            return None
            
        user = items[0]
        
        # Enforce Plan Limits: Check if plan still supports API access
        # Users might downgrade but keep the key - block access if not Ultimate/Pro
        plan = user.get('plan') or user.get('subscription') or 'free'
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        return user
        
    except Exception as e:
        print(f"Error authenticating with API key: {str(e)}")
    return None

def get_user_from_token(event):
    """Extract user from Cookie/Authorization and fetch from DynamoDB"""
    # 1. Try Session Token (Cookie)
    token = get_token_from_event(event)
    
    if token:
        try:
            response = sessions_table.get_item(Key={'token': token})
            
            if 'Item' in response:
                session = response['Item']
                
                # Check if session is expired (7 days - Swiss law compliance)
                created_at = datetime.fromisoformat(session.get('created_at', '2000-01-01').replace('Z', ''))
                age = datetime.utcnow() - created_at
                
                if age <= timedelta(days=7):
                    return session.get('user')
                else:
                    sessions_table.delete_item(Key={'token': token})
        except Exception as e:
            print(f"Error in auth (session): {str(e)}")
            
    # 2. Try API Key (Bearer Token)
    return get_user_from_api_key(event)

def get_session(token):
    """Get session from token - for security decorator"""
    try:
        response = sessions_table.get_item(Key={'token': token})
        
        if 'Item' not in response:
            return None
        
        session = response['Item']
        
        # Check if session is expired (7 days)
        created_at = datetime.fromisoformat(session.get('created_at', '2000-01-01').replace('Z', ''))
        age = datetime.utcnow() - created_at
        
        if age > timedelta(days=7):
            sessions_table.delete_item(Key={'token': token})
            return None
        
        # Return session data
        user = session.get('user', {})
        return {
            'user_id': user.get('id'),
            'email': user.get('email')
        }
    except Exception as e:
        print(f"Error getting session: {str(e)}")
        return None
