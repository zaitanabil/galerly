"""
Input Validation Utilities
Comprehensive validation for all user inputs
"""
import re
from typing import Tuple, Any

# Validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
URL_PATTERN = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'  # E.164 format
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9]+$'
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,30}$'

# Dangerous patterns to block
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|;|\/\*|\*\/|xp_|sp_)",
    r"(\bOR\b.*=.*\bOR\b)",
    r"(\bAND\b.*=.*\bAND\b)",
    r"(UNION.*SELECT)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

def sanitize_string(value: str, max_length: int = None) -> str:
    """
    Sanitize string input
    - Strips whitespace
    - Removes null bytes
    - Enforces max length
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Enforce max length
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    Returns: (is_valid, error_message)
    """
    email = sanitize_string(email, 255)
    
    if not email:
        return False, "Email is required"
    
    if len(email) > 255:
        return False, "Email is too long (max 255 characters)"
    
    if not re.match(EMAIL_PATTERN, email, re.IGNORECASE):
        return False, "Invalid email format"
    
    # Check for dangerous patterns
    if contains_injection_pattern(email):
        return False, "Invalid email format"
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    Requirements:
    - Min 8 characters
    - Max 128 characters
    - At least one uppercase
    - At least one lowercase
    - At least one number
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, ""

def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format"""
    url = sanitize_string(url, 2048)
    
    if not url:
        return False, "URL is required"
    
    if not re.match(URL_PATTERN, url, re.IGNORECASE):
        return False, "Invalid URL format"
    
    # Only allow HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    return True, ""

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number (E.164 format)"""
    phone = sanitize_string(phone, 20)
    
    if not phone:
        return True, ""  # Phone is optional
    
    # Remove common formatting
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    if not re.match(PHONE_PATTERN, phone):
        return False, "Invalid phone number format (use international format: +1234567890)"
    
    return True, ""

def validate_text_field(value: str, field_name: str, min_length: int = 0, max_length: int = 1000, required: bool = True) -> Tuple[bool, str]:
    """
    Generic text field validation
    """
    value = sanitize_string(value, max_length)
    
    if required and not value:
        return False, f"{field_name} is required"
    
    if value and len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if value and len(value) > max_length:
        return False, f"{field_name} must be less than {max_length} characters"
    
    # Check for injection patterns
    if value and contains_injection_pattern(value):
        return False, f"{field_name} contains invalid characters"
    
    # Check for XSS patterns
    if value and contains_xss_pattern(value):
        return False, f"{field_name} contains invalid characters"
    
    return True, ""

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format"""
    username = sanitize_string(username, 30)
    
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    if not re.match(USERNAME_PATTERN, username):
        return False, "Username can only contain letters, numbers, hyphens, and underscores"
    
    return True, ""

def validate_uuid(uuid_str: str) -> Tuple[bool, str]:
    """Validate UUID format"""
    if not uuid_str:
        return False, "ID is required"
    
    if not re.match(UUID_PATTERN, uuid_str.lower()):
        return False, "Invalid ID format"
    
    return True, ""

def validate_integer(value: Any, field_name: str, min_val: int = None, max_val: int = None) -> Tuple[bool, str]:
    """Validate integer field"""
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"
    
    if min_val is not None and int_value < min_val:
        return False, f"{field_name} must be at least {min_val}"
    
    if max_val is not None and int_value > max_val:
        return False, f"{field_name} must be at most {max_val}"
    
    return True, ""

def contains_injection_pattern(value: str) -> bool:
    """Check if value contains SQL injection patterns"""
    value_upper = value.upper()
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    
    return False

def contains_xss_pattern(value: str) -> bool:
    """Check if value contains XSS patterns"""
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False

def validate_json_size(json_str: str, max_size_kb: int = 100) -> Tuple[bool, str]:
    """Validate JSON payload size"""
    size_bytes = len(json_str.encode('utf-8'))
    size_kb = size_bytes / 1024
    
    if size_kb > max_size_kb:
        return False, f"Payload too large (max {max_size_kb}KB)"
    
    return True, ""

