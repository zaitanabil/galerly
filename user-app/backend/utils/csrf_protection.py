"""
CSRF Protection Middleware
Protects against Cross-Site Request Forgery attacks
"""
import secrets
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from utils.response import create_response

# CSRF token expiry (1 hour)
CSRF_TOKEN_EXPIRY = 3600

# Secret key for CSRF token generation (should be in environment)
import os
CSRF_SECRET = os.environ.get('CSRF_SECRET', secrets.token_urlsafe(32))

def generate_csrf_token(session_token):
    """
    Generate a CSRF token tied to the user's session
    Returns: (token, expires_at)
    """
    # Create timestamp
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    
    # Generate token: HMAC(session_token + timestamp, CSRF_SECRET)
    message = f"{session_token}:{timestamp}".encode('utf-8')
    signature = hmac.new(
        CSRF_SECRET.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    
    # Token format: timestamp.signature
    token = f"{timestamp}.{signature}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=CSRF_TOKEN_EXPIRY)
    
    return token, expires_at.replace(tzinfo=None).isoformat() + 'Z'

def verify_csrf_token(csrf_token, session_token):
    """
    Verify CSRF token is valid for the given session
    Returns: (is_valid: bool, error_message: str)
    """
    if not csrf_token or not session_token:
        return False, "Missing CSRF token or session"
    
    try:
        # Parse token
        parts = csrf_token.split('.')
        if len(parts) != 2:
            return False, "Invalid CSRF token format"
        
        timestamp_str, provided_signature = parts
        timestamp = int(timestamp_str)
        
        # Check if token expired
        token_age = datetime.now(timezone.utc).timestamp() - timestamp
        if token_age > CSRF_TOKEN_EXPIRY:
            return False, "CSRF token expired"
        
        if token_age < 0:
            return False, "Invalid CSRF token timestamp"
        
        # Verify signature
        message = f"{session_token}:{timestamp_str}".encode('utf-8')
        expected_signature = hmac.new(
            CSRF_SECRET.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(provided_signature, expected_signature):
            return False, "Invalid CSRF token signature"
        
        return True, ""
        
    except Exception as e:
        print(f"CSRF verification error: {str(e)}")
        return False, "CSRF token verification failed"

def csrf_protect(handler_func):
    """
    Decorator to protect endpoints with CSRF validation
    Apply to state-changing operations (POST, PUT, DELETE)
    
    Usage:
        @csrf_protect
        def handle_update_profile(event, user):
            # handler code
    """
    def wrapper(event, *args, **kwargs):
        # Skip CSRF for GET/HEAD/OPTIONS
        method = event.get('httpMethod', '').upper()
        if method in ['GET', 'HEAD', 'OPTIONS']:
            return handler_func(event, *args, **kwargs)
        
        # Get CSRF token from header
        headers = event.get('headers', {}) or {}
        csrf_token = headers.get('X-CSRF-Token') or headers.get('x-csrf-token')
        
        # Get session token from cookie
        from utils.auth import get_token_from_event
        session_token = get_token_from_event(event)
        
        if not session_token:
            return create_response(401, {'error': 'Authentication required'})
        
        # Verify CSRF token
        is_valid, error_message = verify_csrf_token(csrf_token, session_token)
        
        if not is_valid:
            print(f"❌ CSRF validation failed: {error_message}")
            return create_response(403, {
                'error': 'CSRF validation failed',
                'message': error_message
            })
        
        # CSRF valid - proceed with handler
        return handler_func(event, *args, **kwargs)
    
    return wrapper

def get_csrf_token_for_session(event):
    """
    Get CSRF token for current session
    Endpoint: GET /v1/auth/csrf-token
    """
    from utils.auth import get_token_from_event
    session_token = get_token_from_event(event)
    
    if not session_token:
        return create_response(401, {'error': 'Authentication required'})
    
    csrf_token, expires_at = generate_csrf_token(session_token)
    
    return create_response(200, {
        'csrf_token': csrf_token,
        'expires_at': expires_at
    })

