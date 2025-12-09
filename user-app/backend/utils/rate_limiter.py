"""
Rate Limiter for AWS Lambda
Uses DynamoDB to track request rates per IP/user
"""
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from utils.config import dynamodb
from utils.response import create_response

# Initialize rate limit table
rate_limit_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_RATE_LIMITS', 'galerly-rate-limits-dev'))

# Rate limit configurations (requests per window)
RATE_LIMITS = {
    'auth_login': {'limit': 5, 'window': 300},  # 5 attempts per 5 minutes
    'auth_register': {'limit': 3, 'window': 3600},  # 3 registrations per hour
    'auth_password_reset': {'limit': 3, 'window': 3600},  # 3 resets per hour
    'auth_verification': {'limit': 5, 'window': 3600},  # 5 verifications per hour
    'api_default': {'limit': 100, 'window': 60},  # 100 requests per minute
}

def get_client_identifier(event):
    """
    Get unique identifier for rate limiting (IP address or user ID)
    Prioritizes user ID if authenticated, falls back to IP
    """
    # Try to get IP address from various headers
    headers = event.get('headers', {}) or {}
    ip_address = (
        headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        headers.get('X-Real-IP', '') or
        event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
    )
    
    # If user is authenticated, use user ID for more accurate rate limiting
    from utils.auth import get_user_from_token
    user = get_user_from_token(event)
    if user and user.get('id'):
        return f"user:{user['id']}"
    
    return f"ip:{ip_address}"

def check_rate_limit(event, limit_type='api_default'):
    """
    Check if request is within rate limit
    Returns: (is_allowed: bool, remaining: int, reset_at: str)
    """
    try:
        config = RATE_LIMITS.get(limit_type, RATE_LIMITS['api_default'])
        limit = config['limit']
        window_seconds = config['window']
        
        identifier = get_client_identifier(event)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        
        # Create unique key for this rate limit
        rate_key = f"{identifier}:{limit_type}"
        
        # Get current count from DynamoDB
        try:
            response = rate_limit_table.get_item(Key={'identifier': rate_key})
            item = response.get('Item', {})
            
            # Clean up old requests outside the window
            requests = item.get('requests', [])
            requests = [
                req for req in requests 
                if datetime.fromisoformat(req.replace('Z', '')).replace(tzinfo=timezone.utc) > window_start
            ]
            
            # Check if limit exceeded
            if len(requests) >= limit:
                reset_at = min(requests) if requests else now.replace(tzinfo=None).isoformat() + 'Z'
                return False, 0, reset_at
            
            # Add current request
            requests.append(now.replace(tzinfo=None).isoformat() + 'Z')
            remaining = limit - len(requests)
            
            # Update DynamoDB
            rate_limit_table.put_item(
                Item={
                    'identifier': rate_key,
                    'requests': requests,
                    'updated_at': now.replace(tzinfo=None).isoformat() + 'Z',
                    'ttl': int((now + timedelta(seconds=window_seconds * 2)).timestamp())  # Auto-cleanup
                }
            )
            
            reset_at = (now + timedelta(seconds=window_seconds)).replace(tzinfo=None).isoformat() + 'Z'
            return True, remaining, reset_at
            
        except Exception as e:
            print(f"Rate limit check error: {str(e)}")
            # On error, allow request (fail open for availability)
            return True, limit, now.replace(tzinfo=None).isoformat() + 'Z'
            
    except Exception as e:
        print(f"Rate limiter error: {str(e)}")
        # Fail open - allow request if rate limiter fails
        return True, 0, datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'

def rate_limit_decorator(limit_type='api_default'):
    """
    Decorator to apply rate limiting to endpoints
    Usage: @rate_limit_decorator('auth_login')
    """
    def decorator(handler_func):
        def wrapper(event, *args, **kwargs):
            is_allowed, remaining, reset_at = check_rate_limit(event, limit_type)
            
            if not is_allowed:
                return create_response(429, {
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': reset_at
                }, headers={
                    'X-RateLimit-Limit': str(RATE_LIMITS[limit_type]['limit']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': reset_at,
                    'Retry-After': str(RATE_LIMITS[limit_type]['window'])
                })
            
            # Execute handler
            response = handler_func(event, *args, **kwargs)
            
            # Add rate limit headers to response
            if isinstance(response, dict) and 'headers' in response:
                response['headers']['X-RateLimit-Limit'] = str(RATE_LIMITS[limit_type]['limit'])
                response['headers']['X-RateLimit-Remaining'] = str(remaining)
                response['headers']['X-RateLimit-Reset'] = reset_at
            
            return response
        return wrapper
    return decorator

