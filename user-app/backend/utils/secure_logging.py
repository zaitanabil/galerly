"""
Secure Logging Utilities
Audit and minimize logging of sensitive data
"""
import re
import json
from typing import Any, Dict

# Sensitive field patterns to mask
SENSITIVE_FIELDS = [
    'password',
    'password_hash',
    'secret',
    'token',
    'api_key',
    'access_key',
    'secret_key',
    'private_key',
    'credit_card',
    'card_number',
    'cvv',
    'ssn',
    'social_security',
]

# Patterns to detect in string values
SENSITIVE_PATTERNS = [
    (r'sk_live_[a-zA-Z0-9]+', '[STRIPE_SECRET_KEY]'),
    (r'pk_live_[a-zA-Z0-9]+', '[STRIPE_PUBLIC_KEY]'),
    (r'AKIA[0-9A-Z]{16}', '[AWS_ACCESS_KEY]'),
    (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CREDIT_CARD]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    (r'"password"\s*:\s*"[^"]*"', '"password": "[REDACTED]"'),
]

def mask_sensitive_value(value: Any) -> Any:
    """
    Mask sensitive values for logging
    """
    if isinstance(value, str):
        # Apply pattern replacements
        masked = value
        for pattern, replacement in SENSITIVE_PATTERNS:
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        
        # If value is longer than 100 chars and looks like a token, mask it
        if len(masked) > 100 and any(char in masked for char in ['=', '.', '-']):
            return f"[LONG_TOKEN:{len(masked)} chars]"
        
        return masked
    
    return value

def sanitize_dict_for_logging(data: Dict[str, Any], depth: int = 0, max_depth: int = 10) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary for safe logging
    
    Args:
        data: Dictionary to sanitize
        depth: Current recursion depth
        max_depth: Maximum recursion depth
    
    Returns: Sanitized dictionary
    """
    if depth > max_depth:
        return {'__truncated__': 'max depth reached'}
    
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive field name
        is_sensitive = any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS)
        
        if is_sensitive:
            # Mask sensitive fields
            if isinstance(value, str) and len(value) > 0:
                sanitized[key] = f"[REDACTED:{len(value)} chars]"
            else:
                sanitized[key] = '[REDACTED]'
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_dict_for_logging(value, depth + 1, max_depth)
        elif isinstance(value, list):
            # Sanitize lists
            sanitized[key] = [
                sanitize_dict_for_logging(item, depth + 1, max_depth) if isinstance(item, dict) else mask_sensitive_value(item)
                for item in value[:100]  # Limit list size in logs
            ]
        elif isinstance(value, str):
            # Mask sensitive patterns in strings
            sanitized[key] = mask_sensitive_value(value)
        else:
            # Keep other types as-is
            sanitized[key] = value
    
    return sanitized

def safe_log(message: str, data: Dict[str, Any] = None, level: str = 'INFO'):
    """
    Safely log data with automatic sanitization
    
    Args:
        message: Log message
        data: Data to log (will be sanitized)
        level: Log level (INFO, WARNING, ERROR)
    """
    if data:
        sanitized_data = sanitize_dict_for_logging(data)
        log_entry = {
            'level': level,
            'message': message,
            'data': sanitized_data
        }
        print(json.dumps(log_entry))
    else:
        print(f"{level}: {message}")

def log_api_request(event: Dict[str, Any], redact_body: bool = True):
    """
    Log API request with sensitive data redacted
    
    Args:
        event: Lambda event
        redact_body: Whether to redact request body
    """
    log_data = {
        'method': event.get('httpMethod'),
        'path': event.get('path'),
        'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
    }
    
    # Add query params (sanitized)
    query_params = event.get('queryStringParameters')
    if query_params:
        log_data['query_params'] = sanitize_dict_for_logging(query_params)
    
    # Add body (optionally redacted)
    if redact_body:
        body = event.get('body')
        if body:
            try:
                body_json = json.loads(body) if isinstance(body, str) else body
                log_data['body'] = sanitize_dict_for_logging(body_json)
            except:
                log_data['body'] = '[BODY_PARSE_ERROR]'
    
    safe_log('API Request', log_data)

def log_error_safely(error: Exception, context: str = '', include_traceback: bool = False):
    """
    Log error without exposing sensitive information
    
    Args:
        error: Exception object
        context: Context where error occurred
        include_traceback: Whether to include traceback (only in development)
    """
    import os
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
    }
    
    # Only include traceback in development
    if include_traceback and environment == 'development':
        import traceback
        error_data['traceback'] = traceback.format_exc()
    
    safe_log('Error occurred', error_data, level='ERROR')

# Decorator for automatic request/response logging
def log_handler(handler_func):
    """
    Decorator to automatically log handler requests/responses
    with sensitive data redaction
    """
    def wrapper(event, *args, **kwargs):
        # Log request
        log_api_request(event, redact_body=True)
        
        try:
            # Execute handler
            response = handler_func(event, *args, **kwargs)
            
            # Log response (sanitized)
            safe_log(f'{handler_func.__name__} completed', {
                'status_code': response.get('statusCode'),
                'handler': handler_func.__name__
            })
            
            return response
            
        except Exception as e:
            # Log error safely
            log_error_safely(e, f'{handler_func.__name__}', include_traceback=True)
            raise
    
    return wrapper

