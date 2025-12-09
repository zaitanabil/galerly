"""
Error Sanitizer - Prevents sensitive information leakage
Sanitizes error messages before sending to clients
"""
import re
import traceback
from utils.response import create_response

# Patterns that indicate sensitive information
SENSITIVE_PATTERNS = [
    r'password[_\s]*[:=].*',
    r'api[_\s]*key[_\s]*[:=].*',
    r'secret[_\s]*[:=].*',
    r'token[_\s]*[:=].*',
    r'aws[_\s]*access[_\s]*key.*',
    r'stripe[_\s]*key.*',
    r'\/home\/.*',
    r'\/usr\/.*',
    r'\/var\/.*',
    r'C:\\.*',
    r'[a-zA-Z]:\\.*',
    r'File\s+".*",\s+line\s+\d+',  # File paths in tracebacks
    r'sk_live_[a-zA-Z0-9]+',  # Stripe live keys
    r'sk_test_[a-zA-Z0-9]+',  # Stripe test keys
    r'pk_live_[a-zA-Z0-9]+',
    r'pk_test_[a-zA-Z0-9]+',
    r'AKIA[0-9A-Z]{16}',  # AWS access keys
    r'[0-9a-zA-Z/+=]{40}',  # AWS secret keys pattern
]

# Generic error messages by category
GENERIC_ERRORS = {
    'database': 'Database operation failed',
    'authentication': 'Authentication failed',
    'authorization': 'Access denied',
    'validation': 'Invalid input',
    'payment': 'Payment processing failed',
    'storage': 'File operation failed',
    'network': 'Network request failed',
    'internal': 'Internal server error',
}

def sanitize_error_message(error_msg):
    """
    Sanitize error message to remove sensitive information
    Returns a safe error message for client consumption
    """
    if not error_msg:
        return GENERIC_ERRORS['internal']
    
    error_str = str(error_msg).lower()
    
    # Check for sensitive patterns
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, error_str, re.IGNORECASE):
            return GENERIC_ERRORS['internal']
    
    # Remove file paths and line numbers
    sanitized = re.sub(r'File\s+"[^"]+",\s+line\s+\d+', '', str(error_msg))
    sanitized = re.sub(r'/[^\s]+/', '', sanitized)
    sanitized = re.sub(r'[a-zA-Z]:\\[^\s]+', '', sanitized)
    
    # Categorize and return appropriate generic message
    if any(keyword in error_str for keyword in ['dynamodb', 'database', 'table', 'query', 'scan']):
        return GENERIC_ERRORS['database']
    elif any(keyword in error_str for keyword in ['auth', 'login', 'credential', 'password']):
        return GENERIC_ERRORS['authentication']
    elif any(keyword in error_str for keyword in ['permission', 'forbidden', 'unauthorized']):
        return GENERIC_ERRORS['authorization']
    elif any(keyword in error_str for keyword in ['validation', 'invalid', 'required', 'format']):
        return GENERIC_ERRORS['validation']
    elif any(keyword in error_str for keyword in ['stripe', 'payment', 'charge', 'invoice']):
        return GENERIC_ERRORS['payment']
    elif any(keyword in error_str for keyword in ['s3', 'bucket', 'upload', 'download', 'file']):
        return GENERIC_ERRORS['storage']
    elif any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'request']):
        return GENERIC_ERRORS['network']
    
    # If no specific category, return sanitized message (first 100 chars)
    if len(sanitized) > 100:
        return sanitized[:97] + '...'
    
    return sanitized or GENERIC_ERRORS['internal']

def safe_error_response(status_code, error, include_details=False):
    """
    Create a safe error response with sanitized message
    
    Args:
        status_code: HTTP status code
        error: Exception or error message
        include_details: Whether to include sanitized details (for debugging)
    
    Returns:
        Response dict
    """
    # Log the full error for debugging
    print(f"❌ Error: {str(error)}")
    
    # Sanitize error message for client
    safe_message = sanitize_error_message(str(error))
    
    response_data = {
        'error': safe_message
    }
    
    # In development, include more details (but still sanitized)
    if include_details:
        import os
        if os.environ.get('ENVIRONMENT') == 'development':
            response_data['details'] = sanitize_error_message(str(error))
    
    return create_response(status_code, response_data)

def log_error_safely(error, context=''):
    """
    Log error with full details server-side, but safely
    
    Args:
        error: Exception object
        context: Context string describing where error occurred
    """
    print(f"{'='*60}")
    print(f"ERROR in {context}")
    print(f"Type: {type(error).__name__}")
    print(f"Message: {str(error)}")
    print(f"{'='*60}")
    
    # Only log traceback in development
    import os
    if os.environ.get('ENVIRONMENT') == 'development':
        print("Traceback:")
        traceback.print_exc()

def is_user_error(status_code):
    """Check if error is client error (4xx) vs server error (5xx)"""
    return 400 <= status_code < 500

def create_user_friendly_error(status_code, error_type, user_message):
    """
    Create a user-friendly error response
    
    Args:
        status_code: HTTP status code
        error_type: Type of error (validation, authentication, etc.)
        user_message: User-friendly message (already sanitized)
    
    Returns:
        Response dict
    """
    return create_response(status_code, {
        'error': user_message,
        'error_type': error_type
    })

