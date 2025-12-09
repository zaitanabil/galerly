"""
Comprehensive tests for auth_handler.py endpoints.
Tests cover: register, login, logout, password reset, email verification, account deletion.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta, timezone

@pytest.fixture(autouse=False)
def mock_auth_dependencies():
    """Mock all auth handler dependencies - patch at handler level where they're used."""
    with patch('handlers.auth_handler.users_table') as mock_users, \
         patch('handlers.auth_handler.sessions_table') as mock_sessions, \
         patch('utils.email.send_welcome_email') as mock_welcome, \
         patch('utils.email.send_verification_code_email') as mock_verify, \
         patch('utils.email.send_password_reset_email') as mock_reset:
        
        # Don't set default return values - let each test set them explicitly
        # This prevents state pollution between tests
        
        yield {
            'users': mock_users,
            'sessions': mock_sessions,
            'email_welcome': mock_welcome,
            'email_verify': mock_verify,
            'email_reset': mock_reset
        }

# Test: handle_register
class TestHandleRegister:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, mock_auth_dependencies):
        """Register new user successfully."""
        from handlers.auth_handler import handle_register
        from utils.auth import hash_password
        
        # Mock verification token validation - sessions_table returns valid verification
        mock_auth_dependencies['sessions'].get_item.return_value = {
            'Item': {
                'token': 'valid_token',
                'type': 'email_verification',
                'verified': True,
                'email': 'newuser@example.com',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
        }
        
        # No existing user
        mock_auth_dependencies['users'].get_item.return_value = {}
        
        body = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'name': 'New User',
            'verification_token': 'valid_token',
            'role': 'photographer'
        }
        
        result = handle_register(body)
        
        assert result['statusCode'] == 201
        response_body = json.loads(result['body'])
        assert 'id' in response_body
        assert response_body['email'] == 'newuser@example.com'
        # Check that user was created
        assert mock_auth_dependencies['users'].put_item.called
    
    def test_register_missing_email(self, mock_auth_dependencies):
        """Register fails without email."""
        from handlers.auth_handler import handle_register
        
        # No mock setup needed - validation fails before DB access
        body = {'password': 'password123', 'name': 'User'}
        result = handle_register(body)
        
        assert result['statusCode'] == 400
        body_data = json.loads(result['body'])
        assert 'email' in body_data['error'].lower()
    
    def test_register_missing_password(self, mock_auth_dependencies):
        """Register fails without password."""
        from handlers.auth_handler import handle_register
        
        # No mock setup needed - validation fails before DB access
        body = {'email': 'test@example.com', 'name': 'User'}
        result = handle_register(body)
        
        assert result['statusCode'] == 400
    
    def test_register_duplicate_email(self, mock_auth_dependencies):
        """Register fails with existing email."""
        from handlers.auth_handler import handle_register
        
        # Mock verification token
        mock_auth_dependencies['sessions'].get_item.return_value = {
            'Item': {
                'token': 'valid_token',
                'type': 'email_verification',
                'verified': True,
                'email': 'existing@example.com',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
        }
        
        # Existing user found - must return Item in get_item response
        mock_auth_dependencies['users'].get_item.return_value = {
            'Item': {'email': 'existing@example.com', 'id': 'user123'}
        }
        
        body = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'name': 'User',
            'verification_token': 'valid_token'
        }
        
        result = handle_register(body)
        
        assert result['statusCode'] == 409
        body_data = json.loads(result['body'])
        assert 'already exists' in body_data['error'].lower()
    
    def test_register_invalid_verification_code(self, mock_auth_dependencies):
        """Register fails without verification token."""
        from handlers.auth_handler import handle_register
        
        # No verification_token provided - fails validation before DB access
        body = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'name': 'User'
            # No verification_token
        }
        
        result = handle_register(body)
        
        assert result['statusCode'] == 400
        body_data = json.loads(result['body'])
        assert 'verification' in body_data['error'].lower()

# Test: handle_login
class TestHandleLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, sample_user, mock_auth_dependencies):
        """Login with correct credentials."""
        from handlers.auth_handler import handle_login
        from utils.auth import hash_password
        
        # Mock user with correct password hash
        user_with_password = {
            **sample_user,
            'password_hash': hash_password('correctpassword')
        }
        mock_auth_dependencies['users'].get_item.return_value = {'Item': user_with_password}
        
        body = {'email': 'test@example.com', 'password': 'correctpassword'}
        
        result = handle_login(body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['email'] == sample_user['email']
        assert 'Set-Cookie' in result.get('headers', {})
        # Check that session was created
        assert mock_auth_dependencies['sessions'].put_item.called
    
    def test_login_invalid_credentials(self, sample_user, mock_auth_dependencies):
        """Login fails with wrong password."""
        from handlers.auth_handler import handle_login
        from utils.auth import hash_password
        
        user_with_password = {
            **sample_user,
            'password_hash': hash_password('correctpassword')
        }
        mock_auth_dependencies['users'].get_item.return_value = {'Item': user_with_password}
        
        body = {'email': 'test@example.com', 'password': 'wrongpassword'}
        
        result = handle_login(body)
        
        assert result['statusCode'] == 401
        body_data = json.loads(result['body'])
        assert 'invalid' in body_data['error'].lower()
    
    def test_login_user_not_found(self, mock_auth_dependencies):
        """Login fails when user doesn't exist."""
        from handlers.auth_handler import handle_login
        
        # Mock user not found
        mock_auth_dependencies['users'].get_item.return_value = {}
        
        body = {'email': 'nonexistent@example.com', 'password': 'password'}
        result = handle_login(body)
        
        assert result['statusCode'] == 401
    
    def test_login_missing_email(self, mock_auth_dependencies):
        """Login fails without email."""
        from handlers.auth_handler import handle_login
        
        # No mock setup needed - validation fails before DB access
        body = {'password': 'password'}
        result = handle_login(body)
        
        assert result['statusCode'] == 400
    
    def test_login_missing_password(self, mock_auth_dependencies):
        """Login fails without password."""
        from handlers.auth_handler import handle_login
        
        # No mock setup needed - validation fails before DB access
        body = {'email': 'test@example.com'}
        result = handle_login(body)
        
        assert result['statusCode'] == 400

# Test: handle_logout
class TestHandleLogout:
    """Tests for user logout endpoint."""
    
    def test_logout_success(self, mock_auth_dependencies):
        """Logout successfully."""
        from handlers.auth_handler import handle_logout
        
        event = {'headers': {'Cookie': 'galerly_session=valid_token'}}
        
        result = handle_logout(event)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'logged out' in body_data['message'].lower()
        # Check that delete_item was called (token deletion)
        assert mock_auth_dependencies['sessions'].delete_item.called

# Test: handle_request_verification_code
class TestHandleRequestVerificationCode:
    """Tests for email verification code request."""
    
    def test_request_code_success(self, mock_auth_dependencies):
        """Request verification code successfully."""
        from handlers.auth_handler import handle_request_verification_code
        
        body = {'email': 'test@example.com'}
        
        result = handle_request_verification_code(body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'sent' in body_data['message'].lower() or 'verification' in body_data['message'].lower()
        # Check that put_item was called (don't assert_called_once as other tests may have called it)
        assert mock_auth_dependencies['sessions'].put_item.called
    
    def test_request_code_missing_email(self, mock_auth_dependencies):
        """Request verification code fails without email."""
        from handlers.auth_handler import handle_request_verification_code
        
        # No mock setup needed - validation fails before DB access
        body = {}
        result = handle_request_verification_code(body)
        
        assert result['statusCode'] == 400

# Test: handle_verify_code
class TestHandleVerifyCode:
    """Tests for email verification code validation."""
    
    def test_verify_code_success(self, mock_auth_dependencies):
        """Verify code successfully."""
        from handlers.auth_handler import handle_verify_code
        
        # Mock sessions table to return a valid verification record
        mock_auth_dependencies['sessions'].get_item.return_value = {
            'Item': {
                'token': 'verification_token_123',
                'type': 'email_verification',
                'email': 'test@example.com',
                'code': '123456',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                'verified': False
            }
        }
        
        body = {'verification_token': 'verification_token_123', 'code': '123456'}
        
        result = handle_verify_code(body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'verified' in body_data['message'].lower() or 'email' in body_data
    
    def test_verify_code_invalid(self, mock_auth_dependencies):
        """Verify code fails with invalid code."""
        from handlers.auth_handler import handle_verify_code
        
        # Mock sessions table with valid token but different code
        mock_auth_dependencies['sessions'].get_item.return_value = {
            'Item': {
                'token': 'verification_token_123',
                'type': 'email_verification',
                'email': 'test@example.com',
                'code': '123456',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                'verified': False
            }
        }
        
        body = {'verification_token': 'verification_token_123', 'code': 'wrong_code'}
        
        result = handle_verify_code(body)
        
        assert result['statusCode'] == 400

# Test: handle_request_password_reset
class TestHandleRequestPasswordReset:
    """Tests for password reset request."""
    
    def test_request_reset_success(self, sample_user, mock_auth_dependencies):
        """Request password reset successfully."""
        from handlers.auth_handler import handle_request_password_reset
        
        mock_auth_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'email': 'test@example.com'}
        result = handle_request_password_reset(body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'sent' in body_data['message'].lower() or 'email' in body_data['message'].lower()
        # Check that reset token was created
        assert mock_auth_dependencies['sessions'].put_item.called
    
    def test_request_reset_user_not_found(self, mock_auth_dependencies):
        """Request password reset for nonexistent user still returns success (security)."""
        from handlers.auth_handler import handle_request_password_reset
        
        mock_auth_dependencies['users'].get_item.return_value = {}
        
        body = {'email': 'nonexistent@example.com'}
        result = handle_request_password_reset(body)
        
        # Should still return 200 to prevent email enumeration
        assert result['statusCode'] == 200

# Test: handle_reset_password
class TestHandleResetPassword:
    """Tests for password reset with token."""
    
    def test_reset_password_success(self, sample_user, mock_auth_dependencies):
        """Reset password with valid token."""
        from handlers.auth_handler import handle_reset_password
        
        # Mock sessions table with valid reset token
        mock_auth_dependencies['sessions'].get_item.return_value = {
            'Item': {
                'token': 'valid_token',
                'type': 'password_reset',
                'email': 'test@example.com',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
        }
        
        body = {
            'token': 'valid_token',
            'password': 'NewSecurePass123!'
        }
        
        result = handle_reset_password(body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'reset' in body_data['message'].lower() or 'success' in body_data['message'].lower()
        # Check that password was updated
        assert mock_auth_dependencies['users'].update_item.called
    
    def test_reset_password_invalid_token(self, sample_user, mock_auth_dependencies):
        """Reset password fails with invalid token."""
        from handlers.auth_handler import handle_reset_password
        
        # Mock sessions table returns no item
        mock_auth_dependencies['sessions'].get_item.return_value = {}
        
        body = {
            'token': 'invalid_token',
            'password': 'NewPassword123!'
        }
        
        result = handle_reset_password(body)
        
        assert result['statusCode'] == 400

# Test: handle_delete_account
class TestHandleDeleteAccount:
    """Tests for account deletion."""
    
    def test_delete_account_success(self, sample_user, mock_auth_dependencies):
        """Delete user account successfully with grace period."""
        from handlers.auth_handler import handle_delete_account
        
        result = handle_delete_account(sample_user)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        
        # Grace period implementation
        assert 'deletion_date' in body_data
        assert body_data['grace_period_days'] == 30
        assert 'restore_info' in body_data
    
    def test_delete_account_cascading_deletions(self, sample_user, sample_gallery, mock_auth_dependencies):
        """Delete account with grace period - cascading deletions happen after 30 days."""
        from handlers.auth_handler import handle_delete_account
        
        result = handle_delete_account(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        
        # Account deletion is now soft delete with grace period
        assert 'deletion_date' in body
        assert 'grace_period_days' in body

# Test: handle_get_me
class TestHandleGetMe:
    """Tests for getting current user info."""
    
    def test_get_me_success(self, sample_user, mock_auth_dependencies):
        """Get current user info successfully."""
        from handlers.auth_handler import handle_get_me
        
        mock_auth_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        result = handle_get_me(sample_user)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert body_data['id'] == sample_user['id']
        assert body_data['email'] == sample_user['email']
        assert 'password_hash' not in body_data  # Sensitive data excluded

# Test: Session management
# Note: Session functions (create_session, validate_session) are internal helpers
# They are tested indirectly via handle_login, handle_logout, and handle_get_me

