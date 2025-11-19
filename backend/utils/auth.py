"""
Authentication utilities
"""
import hashlib
from datetime import datetime, timedelta
from .config import sessions_table

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_token_from_event(event):
    """Extract session token from Cookie header or Authorization header (fallback)"""
    headers = event.get('headers', {})
    
    # First, try to get token from Cookie header (HttpOnly cookie)
    cookie_header = headers.get('Cookie') or headers.get('cookie', '')
    if cookie_header:
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        token = cookies.get('galerly_session')
        if token:
            return token
    
    # Fallback: try Authorization header (for backward compatibility)
    auth_header = headers.get('Authorization', '') or headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '')
    
    return None

def get_user_from_token(event):
    """Extract user from Cookie/Authorization and fetch from DynamoDB"""
    token = get_token_from_event(event)
    
    if not token:
        return None
    
    try:
        response = sessions_table.get_item(Key={'token': token})
        
        if 'Item' not in response:
            return None
        
        session = response['Item']
        
        # Check if session is expired (7 days - Swiss law compliance)
        created_at = datetime.fromisoformat(session.get('created_at', '2000-01-01').replace('Z', ''))
        age = datetime.utcnow() - created_at
        
        if age > timedelta(days=7):
            sessions_table.delete_item(Key={'token': token})
            return None
        
        return session.get('user')
    except Exception as e:
        print(f"Error in auth: {str(e)}")
        return None

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


