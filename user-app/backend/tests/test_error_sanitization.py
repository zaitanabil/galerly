"""
Security Tests - Error Message Sanitization
Tests for sanitizing error messages to prevent information disclosure
"""
import pytest
from utils.error_sanitizer import (
    sanitize_error_message,
    safe_error_response,
    GENERIC_ERRORS
)

def test_sanitize_removes_file_paths():
    """Test that file paths are removed from error messages"""
    error = "File \"/home/user/app/handlers/auth.py\", line 42, in handle_login"
    sanitized = sanitize_error_message(error)
    
    assert '/home/user' not in sanitized
    assert '/app/handlers' not in sanitized

def test_sanitize_removes_api_keys():
    """Test that API keys are sanitized"""
    error = "Stripe API key: sk_live_abc123xyz789"
    sanitized = sanitize_error_message(error)
    
    assert 'sk_live_' not in sanitized
    assert 'abc123xyz789' not in sanitized
    assert sanitized == GENERIC_ERRORS['internal']

def test_sanitize_removes_passwords():
    """Test that password references are sanitized"""
    error = "Password validation failed: password=MySecret123"
    sanitized = sanitize_error_message(error)
    
    assert 'MySecret123' not in sanitized
    assert sanitized == GENERIC_ERRORS['internal']

def test_sanitize_removes_aws_keys():
    """Test that AWS access keys are sanitized"""
    error = "AWS Error: AKIAIOSFODNN7EXAMPLE"
    sanitized = sanitize_error_message(error)
    
    assert 'AKIA' not in sanitized
    assert sanitized == GENERIC_ERRORS['internal']

def test_sanitize_database_errors():
    """Test that database errors get generic message"""
    error = "DynamoDB operation failed: table galerly-users-prod not found"
    sanitized = sanitize_error_message(error)
    
    assert sanitized == GENERIC_ERRORS['database']
    assert 'galerly-users-prod' not in sanitized

def test_sanitize_auth_errors():
    """Test that authentication errors get generic message"""
    error = "Authentication failed: invalid credentials for user@example.com"
    sanitized = sanitize_error_message(error)
    
    assert sanitized == GENERIC_ERRORS['authentication']

def test_sanitize_payment_errors():
    """Test that payment errors get generic message"""
    error = "Stripe charge failed: card_error - insufficient funds"
    sanitized = sanitize_error_message(error)
    
    assert sanitized == GENERIC_ERRORS['payment']

def test_sanitize_validation_errors():
    """Test that validation errors get generic message"""
    error = "Validation error: invalid email format"
    sanitized = sanitize_error_message(error)
    
    assert sanitized == GENERIC_ERRORS['validation']

def test_sanitize_storage_errors():
    """Test that S3/storage errors get generic message"""
    error = "S3 upload failed: bucket galerly-photos-prod access denied"
    sanitized = sanitize_error_message(error)
    
    assert sanitized == GENERIC_ERRORS['storage']
    assert 'galerly-photos-prod' not in sanitized

def test_sanitize_truncates_long_messages():
    """Test that very long messages are truncated"""
    error = "Error: " + "x" * 200
    sanitized = sanitize_error_message(error)
    
    assert len(sanitized) <= 100

def test_sanitize_empty_message():
    """Test handling of empty error messages"""
    sanitized = sanitize_error_message("")
    
    assert sanitized == GENERIC_ERRORS['internal']

def test_sanitize_none_message():
    """Test handling of None error messages"""
    sanitized = sanitize_error_message(None)
    
    assert sanitized == GENERIC_ERRORS['internal']

def test_safe_error_response_structure():
    """Test that safe_error_response returns correct structure"""
    response = safe_error_response(500, Exception("Database connection failed"))
    
    assert response['statusCode'] == 500
    assert 'error' in response['body']
    
    import json
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == GENERIC_ERRORS['database']

def test_safe_error_response_different_status_codes():
    """Test safe_error_response with various status codes"""
    # 400 - Bad Request
    response_400 = safe_error_response(400, ValueError("Invalid input"))
    assert response_400['statusCode'] == 400
    
    # 401 - Unauthorized
    response_401 = safe_error_response(401, Exception("Auth failed"))
    assert response_401['statusCode'] == 401
    
    # 500 - Internal Server Error
    response_500 = safe_error_response(500, Exception("Server error"))
    assert response_500['statusCode'] == 500

def test_sanitize_windows_paths():
    """Test that Windows file paths are removed"""
    error = "Error in C:\\Users\\Admin\\app\\handler.py"
    sanitized = sanitize_error_message(error)
    
    assert 'C:\\' not in sanitized
    assert 'Users\\Admin' not in sanitized

def test_sanitize_multiple_sensitive_patterns():
    """Test that multiple sensitive patterns are all removed"""
    error = "Auth failed with password=secret123 for user at /home/app/auth.py using key sk_live_xyz"
    sanitized = sanitize_error_message(error)
    
    assert 'secret123' not in sanitized
    assert '/home/app' not in sanitized
    assert 'sk_live_xyz' not in sanitized
    assert sanitized == GENERIC_ERRORS['internal']

@pytest.mark.integration
def test_error_sanitization_in_production():
    """Test that errors are properly sanitized in production mode"""
    import os
    
    # Simulate production environment
    with pytest.MonkeyPatch().context() as m:
        m.setenv('ENVIRONMENT', 'production')
        
        response = safe_error_response(
            500,
            Exception("Database error: connection to galerly-prod-db failed"),
            include_details=False
        )
        
        import json
        body = json.loads(response['body'])
        
        # Should not include details in production
        assert 'details' not in body
        assert 'galerly-prod-db' not in str(body)

