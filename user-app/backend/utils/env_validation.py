"""
Environment Variable Validation
Ensures all required environment variables are set and valid
"""
import os
import sys
from typing import Dict, List, Tuple

# Required environment variables by category
REQUIRED_ENV_VARS = {
    'aws': [
        'AWS_REGION',
        'DYNAMODB_TABLE_USERS',
        'DYNAMODB_TABLE_GALLERIES',
        'DYNAMODB_TABLE_PHOTOS',
        'DYNAMODB_TABLE_SESSIONS',
        'DYNAMODB_TABLE_SUBSCRIPTIONS',
        'DYNAMODB_TABLE_BILLING',
        'S3_BUCKET_PHOTOS',
        'S3_BUCKET_EXPORTS',
    ],
    'stripe': [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'STRIPE_PUBLISHABLE_KEY',
    ],
    'security': [
        'CSRF_SECRET',
        'SESSION_SECRET',
        'ENCRYPTION_KEY',
    ],
    'email': [
        'SES_FROM_EMAIL',
        'SES_REGION',
    ],
    'app': [
        'ENVIRONMENT',
        'API_BASE_URL',
        'FRONTEND_URL',
    ]
}

# Optional but recommended
OPTIONAL_ENV_VARS = [
    'RATE_LIMIT_STORAGE_URI',
    'ADMIN_CORS_ORIGINS',
    'LOG_LEVEL',
    'SENTRY_DSN',
]

def validate_env_var_format(var_name: str, var_value: str) -> Tuple[bool, str]:
    """
    Validate format of specific environment variables
    Returns: (is_valid, error_message)
    """
    if not var_value:
        return False, f"{var_name} is empty"
    
    # Stripe keys
    if var_name == 'STRIPE_SECRET_KEY':
        if not var_value.startswith('sk_'):
            return False, "STRIPE_SECRET_KEY must start with 'sk_'"
        if len(var_value) < 32:
            return False, "STRIPE_SECRET_KEY appears to be invalid (too short)"
    
    if var_name == 'STRIPE_PUBLISHABLE_KEY':
        if not var_value.startswith('pk_'):
            return False, "STRIPE_PUBLISHABLE_KEY must start with 'pk_'"
    
    if var_name == 'STRIPE_WEBHOOK_SECRET':
        if not var_value.startswith('whsec_'):
            return False, "STRIPE_WEBHOOK_SECRET must start with 'whsec_'"
    
    # AWS Region
    if var_name == 'AWS_REGION':
        valid_regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1']
        if var_value not in valid_regions:
            return False, f"AWS_REGION '{var_value}' may be invalid"
    
    # Environment
    if var_name == 'ENVIRONMENT':
        if var_value not in ['development', 'staging', 'production']:
            return False, f"ENVIRONMENT must be 'development', 'staging', or 'production', got '{var_value}'"
    
    # URLs
    if var_name in ['API_BASE_URL', 'FRONTEND_URL']:
        if not var_value.startswith(('http://', 'https://')):
            return False, f"{var_name} must start with http:// or https://"
    
    # Email
    if var_name == 'SES_FROM_EMAIL':
        if '@' not in var_value:
            return False, "SES_FROM_EMAIL must be a valid email address"
    
    # Secrets (minimum length)
    if var_name in ['CSRF_SECRET', 'SESSION_SECRET', 'ENCRYPTION_KEY']:
        if len(var_value) < 32:
            return False, f"{var_name} should be at least 32 characters for security"
    
    return True, ""

def validate_environment() -> Tuple[bool, List[str], List[str]]:
    """
    Validate all environment variables
    Returns: (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Check required variables
    for category, var_names in REQUIRED_ENV_VARS.items():
        for var_name in var_names:
            var_value = os.environ.get(var_name)
            
            if not var_value:
                errors.append(f"❌ Missing required environment variable: {var_name} ({category})")
            else:
                # Validate format
                is_valid, error_msg = validate_env_var_format(var_name, var_value)
                if not is_valid:
                    errors.append(f"❌ Invalid {var_name}: {error_msg}")
    
    # Check optional but recommended
    for var_name in OPTIONAL_ENV_VARS:
        var_value = os.environ.get(var_name)
        if not var_value:
            warnings.append(f"⚠️  Optional environment variable not set: {var_name}")
    
    # Security checks
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # Production-specific checks
        if os.environ.get('STRIPE_SECRET_KEY', '').startswith('sk_test_'):
            errors.append("❌ Using Stripe TEST key in PRODUCTION environment")
        
        frontend_url = os.environ.get('FRONTEND_URL', '')
        if frontend_url.startswith('http://'):
            errors.append("❌ FRONTEND_URL should use HTTPS in production")
        
        if not os.environ.get('SENTRY_DSN'):
            warnings.append("⚠️  SENTRY_DSN not set - error monitoring disabled")
    
    is_valid = len(errors) == 0
    
    return is_valid, errors, warnings

def print_validation_results(errors: List[str], warnings: List[str]):
    """Print validation results to console"""
    print("\n" + "="*60)
    print("ENVIRONMENT VARIABLE VALIDATION")
    print("="*60 + "\n")
    
    if errors:
        print(f"Found {len(errors)} error(s):\n")
        for error in errors:
            print(f"  {error}")
        print()
    
    if warnings:
        print(f"Found {len(warnings)} warning(s):\n")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ All environment variables are valid!\n")
    elif not errors:
        print("✅ All required environment variables are valid (warnings can be ignored)\n")
    else:
        print(f"❌ Environment validation failed with {len(errors)} error(s)\n")
    
    print("="*60 + "\n")

def validate_on_startup():
    """
    Validate environment on application startup
    Exits if validation fails in production
    """
    is_valid, errors, warnings = validate_environment()
    
    print_validation_results(errors, warnings)
    
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if not is_valid and environment == 'production':
        print("❌ CRITICAL: Environment validation failed in production. Exiting.")
        sys.exit(1)
    
    return is_valid

def get_env_or_fail(var_name: str) -> str:
    """
    Get environment variable or raise error if not set
    Use for critical variables that must be present
    """
    value = os.environ.get(var_name)
    if not value:
        raise EnvironmentError(f"Required environment variable not set: {var_name}")
    return value

def get_env_with_default(var_name: str, default: str) -> str:
    """Get environment variable with default fallback"""
    return os.environ.get(var_name, default)

# Auto-validate on module import (can be disabled)
if os.environ.get('SKIP_ENV_VALIDATION') != 'true':
    try:
        validate_on_startup()
    except Exception as e:
        print(f"Warning: Environment validation failed: {str(e)}")

