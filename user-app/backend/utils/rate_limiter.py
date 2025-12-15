"""
Rate Limiting Middleware for Expensive Operations
Prevents abuse of analytics, uploads, and API endpoints
"""
import time
import hashlib
from functools import wraps
from utils.response import create_response
from utils.config import get_dynamodb
from utils.resource_names import RATE_LIMITS_TABLE

# Initialize rate limit tracking table using naming convention
dynamodb = get_dynamodb()
rate_limits_table = dynamodb.Table(RATE_LIMITS_TABLE)

# Rate limit configurations by endpoint type
RATE_LIMITS = {
    # Analytics endpoints - prevent scraping
    'analytics_view': {
        'requests': 60,
        'window_seconds': 60,
        'message': 'Analytics rate limit exceeded. Please wait before requesting more data.'
    },
    'analytics_export': {
        'requests': 10,
        'window_seconds': 3600,  # 10 exports per hour
        'message': 'Export limit exceeded. Please wait before generating more exports.'
    },
    
    # Upload endpoints - prevent abuse
    'photo_upload': {
        'requests': 100,
        'window_seconds': 300,  # 100 uploads per 5 min
        'message': 'Upload rate limit exceeded. Please slow down.'
    },
    'bulk_download': {
        'requests': 5,
        'window_seconds': 300,  # 5 bulk downloads per 5 min
        'message': 'Bulk download limit exceeded. Please wait before downloading again.'
    },
    
    # Gallery viewing - prevent bot scraping
    'gallery_view': {
        'requests': 100,
        'window_seconds': 60,
        'message': 'Too many requests. Please slow down.'
    },
    
    # API calls - general protection
    'api_general': {
        'requests': 300,
        'window_seconds': 60,
        'message': 'API rate limit exceeded. Please wait before making more requests.'
    },
    
    # Authentication - prevent brute force
    'auth_login': {
        'requests': 5,
        'window_seconds': 300,  # 5 attempts per 5 min
        'message': 'Too many login attempts. Please wait 5 minutes.'
    },
    'auth_register': {
        'requests': 3,
        'window_seconds': 3600,  # 3 registrations per hour per IP
        'message': 'Registration limit exceeded. Please try again later.'
    }
}


def get_rate_limit_key(limit_type, identifier):
    """Generate unique key for rate limit tracking"""
    # Hash identifier for privacy
    hashed = hashlib.sha256(identifier.encode()).hexdigest()
    return f"{limit_type}:{hashed}"


def check_rate_limit(limit_type, identifier):
    """
    Check if request is within rate limit
    
    Args:
        limit_type: Type of rate limit (e.g., 'photo_upload')
        identifier: Unique identifier (user_id, IP, etc.)
    
    Returns:
        (allowed: bool, retry_after: int)
    """
    try:
        if limit_type not in RATE_LIMITS:
            # No rate limit configured, allow
            return True, 0
        
        config = RATE_LIMITS[limit_type]
        key = get_rate_limit_key(limit_type, identifier)
        current_time = int(time.time())
        window_start = current_time - config['window_seconds']
        
        # Get or create rate limit record
        try:
            response = rate_limits_table.get_item(Key={'limit_key': key})
            
            if 'Item' in response:
                item = response['Item']
                requests = item.get('requests', [])
                
                # Filter out requests outside window
                requests = [r for r in requests if r > window_start]
                
                # Check if limit exceeded
                if len(requests) >= config['requests']:
                    oldest_request = min(requests)
                    retry_after = oldest_request + config['window_seconds'] - current_time
                    return False, max(retry_after, 0)
                
                # Add current request
                requests.append(current_time)
            else:
                # First request
                requests = [current_time]
            
            # Update record
            rate_limits_table.put_item(Item={
                'limit_key': key,
                'requests': requests,
                'updated_at': current_time,
                'ttl': current_time + config['window_seconds'] + 3600  # Expire 1 hour after window
            })
            
            return True, 0
            
        except Exception as db_error:
            print(f"Rate limit DB error: {str(db_error)}")
            # On error, allow request (fail open)
            return True, 0
            
    except Exception as e:
        print(f"Rate limit check error: {str(e)}")
        # On error, allow request
        return True, 0


def rate_limit(limit_type, identifier_key='user_id'):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit_type: Type of rate limit to apply
        identifier_key: Key to extract identifier from (user_id, ip, email)
    
    Usage:
        @rate_limit('photo_upload', 'user_id')
        def handle_upload_photo(user, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier from arguments
            identifier = None
            
            # Check if first arg is user dict
            if args and isinstance(args[0], dict):
                user = args[0]
                if identifier_key == 'user_id':
                    identifier = user.get('id', user.get('email', 'anonymous'))
                elif identifier_key == 'email':
                    identifier = user.get('email', 'anonymous')
                elif identifier_key == 'ip':
                    # Would need to pass event to get IP
                    # For now use user ID
                    identifier = user.get('id', 'anonymous')
            
            # Check for event object to get IP
            for arg in args:
                if isinstance(arg, dict) and 'requestContext' in arg:
                    event = arg
                    if identifier_key == 'ip':
                        identifier = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
                    break
            
            if not identifier:
                identifier = 'anonymous'
            
            # Check rate limit
            allowed, retry_after = check_rate_limit(limit_type, identifier)
            
            if not allowed:
                config = RATE_LIMITS.get(limit_type, {})
                return create_response(429, {
                    'error': config.get('message', 'Rate limit exceeded'),
                    'retry_after': retry_after,
                    'limit_type': limit_type
                }, headers={
                    'Retry-After': str(retry_after)
                })
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_rate_limit_status(limit_type, identifier):
    """
    Get current rate limit status for an identifier
    
    Returns:
        {
            'requests_made': int,
            'requests_allowed': int,
            'remaining': int,
            'reset_at': int (timestamp)
        }
    """
    try:
        if limit_type not in RATE_LIMITS:
            return {
                'requests_made': 0,
                'requests_allowed': -1,
                'remaining': -1,
                'reset_at': 0
            }
        
        config = RATE_LIMITS[limit_type]
        key = get_rate_limit_key(limit_type, identifier)
        current_time = int(time.time())
        window_start = current_time - config['window_seconds']
        
        try:
            response = rate_limits_table.get_item(Key={'limit_key': key})
            
            if 'Item' in response:
                item = response['Item']
                requests = item.get('requests', [])
                
                # Filter out requests outside window
                requests = [r for r in requests if r > window_start]
                
                oldest_request = min(requests) if requests else current_time
                reset_at = oldest_request + config['window_seconds']
                
                return {
                    'requests_made': len(requests),
                    'requests_allowed': config['requests'],
                    'remaining': max(0, config['requests'] - len(requests)),
                    'reset_at': reset_at
                }
            else:
                return {
                    'requests_made': 0,
                    'requests_allowed': config['requests'],
                    'remaining': config['requests'],
                    'reset_at': current_time + config['window_seconds']
                }
                
        except Exception as db_error:
            print(f"Rate limit status DB error: {str(db_error)}")
            return {
                'requests_made': 0,
                'requests_allowed': config['requests'],
                'remaining': config['requests'],
                'reset_at': current_time + config['window_seconds']
            }
            
    except Exception as e:
        print(f"Rate limit status error: {str(e)}")
        return {
            'requests_made': 0,
            'requests_allowed': -1,
            'remaining': -1,
            'reset_at': 0
        }


def reset_rate_limit(limit_type, identifier):
    """
    Reset rate limit for a specific identifier (admin function)
    """
    try:
        key = get_rate_limit_key(limit_type, identifier)
        rate_limits_table.delete_item(Key={'limit_key': key})
        print(f"Rate limit reset: {limit_type} for {identifier}")
        return True
    except Exception as e:
        print(f"Error resetting rate limit: {str(e)}")
        return False
