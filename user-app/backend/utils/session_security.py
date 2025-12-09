"""
Session Security Utilities
Handles session rotation and security operations
"""
import secrets
from datetime import datetime, timezone
from utils.config import sessions_table, users_table
from utils.auth import get_token_from_event

def rotate_session(old_session_token, user):
    """
    Rotate session token after sensitive operations
    Creates new token and invalidates old one
    
    Returns: (new_token, cookie_value)
    """
    # Generate new session token
    new_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
    
    # Create new session
    sessions_table.put_item(Item={
        'token': new_token,
        'user': user,
        'created_at': now,
        'rotated_from': old_session_token,
        'rotation_reason': 'sensitive_operation'
    })
    
    # Delete old session
    try:
        sessions_table.delete_item(Key={'token': old_session_token})
    except Exception as e:
        print(f"Warning: Failed to delete old session: {str(e)}")
    
    # Create new cookie
    cookie_value = f"galerly_session={new_token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=604800"
    
    return new_token, cookie_value

def rotate_session_after_operation(event, user, operation_name):
    """
    Wrapper to rotate session after sensitive operations
    
    Args:
        event: Lambda event
        user: User object
        operation_name: Name of the operation (for logging)
    
    Returns: cookie_value for Set-Cookie header
    """
    old_token = get_token_from_event(event)
    
    if not old_token:
        # No session to rotate
        return None
    
    new_token, cookie_value = rotate_session(old_token, user)
    
    print(f"✅ Session rotated after {operation_name}: {old_token[:8]}... → {new_token[:8]}...")
    
    # Log rotation for security audit
    try:
        from utils.config import dynamodb
        import os
        audit_table = dynamodb.Table(os.environ.get('AUDIT_LOG_TABLE', 'galerly-audit-log-dev'))
        
        audit_table.put_item(Item={
            'id': secrets.token_urlsafe(16),
            'user_id': user.get('id'),
            'action': 'session_rotated',
            'operation': operation_name,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'old_token_prefix': old_token[:8],
            'new_token_prefix': new_token[:8]
        })
    except Exception as e:
        print(f"Warning: Failed to log session rotation: {str(e)}")
    
    return cookie_value

def invalidate_all_user_sessions(user_id, user_email, reason='security'):
    """
    Invalidate all sessions for a user
    Used when:
    - Password changed
    - Account compromised
    - User requests logout from all devices
    
    Returns: count of sessions invalidated
    """
    try:
        # Query all sessions for this user
        # Note: This requires a GSI on user_id or email
        from utils.config import dynamodb
        import os
        
        # For now, we'll scan (inefficient but works)
        # In production, add GSI for user lookups
        response = sessions_table.scan()
        
        sessions_to_delete = []
        for session in response.get('Items', []):
            session_user = session.get('user', {})
            if session_user.get('id') == user_id or session_user.get('email') == user_email:
                sessions_to_delete.append(session['token'])
        
        # Delete all user sessions
        for token in sessions_to_delete:
            sessions_table.delete_item(Key={'token': token})
        
        print(f"🔒 Invalidated {len(sessions_to_delete)} sessions for user {user_id} (reason: {reason})")
        
        # Log for audit
        try:
            audit_table = dynamodb.Table(os.environ.get('AUDIT_LOG_TABLE', 'galerly-audit-log-dev'))
            audit_table.put_item(Item={
                'id': secrets.token_urlsafe(16),
                'user_id': user_id,
                'action': 'all_sessions_invalidated',
                'reason': reason,
                'session_count': len(sessions_to_delete),
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            })
        except Exception as e:
            print(f"Warning: Failed to log session invalidation: {str(e)}")
        
        return len(sessions_to_delete)
        
    except Exception as e:
        print(f"Error invalidating sessions: {str(e)}")
        return 0

# Sensitive operations that trigger session rotation
SENSITIVE_OPERATIONS = [
    'password_change',
    'email_change',
    'api_key_generated',
    'payment_method_added',
    'two_factor_enabled',
    'security_settings_changed'
]

def requires_session_rotation(operation_name):
    """Check if operation requires session rotation"""
    return operation_name in SENSITIVE_OPERATIONS

