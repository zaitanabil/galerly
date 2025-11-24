"""
Comprehensive tests for auth_handler.py endpoints.
Tests cover: register, login, logout, password reset, email verification, account deletion.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

@pytest.fixture
def mock_auth_dependencies():
    """Mock all auth handler dependencies."""
    with patch('handlers.auth_handler.users_table') as mock_users, \
         patch('handlers.auth_handler.verification_codes_table') as mock_codes, \
         patch('handlers.auth_handler.sessions_table') as mock_sessions, \
         patch('handlers.auth_handler.send_email') as mock_email:
        yield {
            'users': mock_users,
            'codes': mock_codes,
            'sessions': mock_sessions,
            'email': mock_email
        }

# Test: handle_register
class TestHandleRegister:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, mock_auth_dependencies):
        """Register new user successfully."""
        from handlers.auth_handler import handle_register
        
        # No existing user
        mock_auth_dependencies['users'].query.return_value = {'Items': []}
        
        body = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'name': 'New User',
            'verification_code': '123456'
        }
        
        # Mock verification code validation
        with patch('handlers.auth_handler.validate_verification_code', return_value=True):
            result = handle_register(body)
            
            assert result['statusCode'] == 201
            response_body = json.loads(result['body'])
            assert 'token' in response_body
            assert response_body['user']['email'] == 'newuser@example.com'
    
    def test_register_missing_email(self, mock_auth_dependencies):
        """Register fails without email."""
        from handlers.auth_handler import handle_register
        
        body = {'password': 'password123', 'name': 'User'}
        result = handle_register(body)
        
        assert result['statusCode'] == 400
        body_data = json.loads(result['body'])
        assert 'email' in body_data['error'].lower()
    
    def test_register_missing_password(self, mock_auth_dependencies):
        """Register fails without password."""
        from handlers.auth_handler import handle_register
        
        body = {'email': 'test@example.com', 'name': 'User'}
        result = handle_register(body)
        
        assert result['statusCode'] == 400
    
    def test_register_duplicate_email(self, mock_auth_dependencies):
        """Register fails with existing email."""
        from handlers.auth_handler import handle_register
        
        # Existing user found
        mock_auth_dependencies['users'].query.return_value = {
            'Items': [{'email': 'existing@example.com'}]
        }
        
        body = {
            'email': 'existing@example.com',
            'password': 'password123',
            'name': 'User',
            'verification_code': '123456'
        }
        
        with patch('handlers.auth_handler.validate_verification_code', return_value=True):
            result = handle_register(body)
            
            assert result['statusCode'] == 400
            body_data = json.loads(result['body'])
            assert 'already exists' in body_data['error'].lower()
    
    def test_register_invalid_verification_code(self, mock_auth_dependencies):
        """Register fails with invalid verification code."""
        from handlers.auth_handler import handle_register
        
        mock_auth_dependencies['users'].query.return_value = {'Items': []}
        
        body = {
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'User',
            'verification_code': 'wrong_code'
        }
        
        with patch('handlers.auth_handler.validate_verification_code', return_value=False):
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
        
        # Mock password hash validation
        user_with_password = {**sample_user, 'password_hash': 'hashed_password'}
        mock_auth_dependencies['users'].query.return_value = {'Items': [user_with_password]}
        
        body = {'email': 'test@example.com', 'password': 'correctpassword'}
        
        with patch('handlers.auth_handler.check_password', return_value=True):
            result = handle_login(body)
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'token' in response_body
            assert response_body['user']['email'] == sample_user['email']
    
    def test_login_invalid_credentials(self, sample_user, mock_auth_dependencies):
        """Login fails with wrong password."""
        from handlers.auth_handler import handle_login
        
        user_with_password = {**sample_user, 'password_hash': 'hashed_password'}
        mock_auth_dependencies['users'].query.return_value = {'Items': [user_with_password]}
        
        body = {'email': 'test@example.com', 'password': 'wrongpassword'}
        
        with patch('handlers.auth_handler.check_password', return_value=False):
            result = handle_login(body)
            
            assert result['statusCode'] == 401
            body_data = json.loads(result['body'])
            assert 'invalid' in body_data['error'].lower()
    
    def test_login_user_not_found(self, mock_auth_dependencies):
        """Login fails when user doesn't exist."""
        from handlers.auth_handler import handle_login
        
        mock_auth_dependencies['users'].query.return_value = {'Items': []}
        
        body = {'email': 'nonexistent@example.com', 'password': 'password'}
        result = handle_login(body)
        
        assert result['statusCode'] == 401
    
    def test_login_missing_email(self, mock_auth_dependencies):
        """Login fails without email."""
        from handlers.auth_handler import handle_login
        
        body = {'password': 'password'}
        result = handle_login(body)
        
        assert result['statusCode'] == 400
    
    def test_login_missing_password(self, mock_auth_dependencies):
        """Login fails without password."""
        from handlers.auth_handler import handle_login
        
        body = {'email': 'test@example.com'}
        result = handle_login(body)
        
        assert result['statusCode'] == 400

# Test: handle_logout
class TestHandleLogout:
    """Tests for user logout endpoint."""
    
    def test_logout_success(self, mock_auth_dependencies):
        """Logout successfully."""
        from handlers.auth_handler import handle_logout
        
        event = {'headers': {'Authorization': 'Bearer valid_token'}}
        
        with patch('handlers.auth_handler.invalidate_session', return_value=True):
            result = handle_logout(event)
            
            assert result['statusCode'] == 200
            body_data = json.loads(result['body'])
            assert 'logged out' in body_data['message'].lower()

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
        assert 'sent' in body_data['message'].lower()
        
        # Verify email was sent
        mock_auth_dependencies['email'].assert_called_once()
    
    def test_request_code_missing_email(self, mock_auth_dependencies):
        """Request verification code fails without email."""
        from handlers.auth_handler import handle_request_verification_code
        
        body = {}
        result = handle_request_verification_code(body)
        
        assert result['statusCode'] == 400

# Test: handle_verify_code
class TestHandleVerifyCode:
    """Tests for email verification code validation."""
    
    def test_verify_code_success(self, mock_auth_dependencies):
        """Verify code successfully."""
        from handlers.auth_handler import handle_verify_code
        
        body = {'email': 'test@example.com', 'code': '123456'}
        
        with patch('handlers.auth_handler.validate_verification_code', return_value=True):
            result = handle_verify_code(body)
            
            assert result['statusCode'] == 200
            body_data = json.loads(result['body'])
            assert body_data['valid'] is True
    
    def test_verify_code_invalid(self, mock_auth_dependencies):
        """Verify code fails with invalid code."""
        from handlers.auth_handler import handle_verify_code
        
        body = {'email': 'test@example.com', 'code': 'wrong'}
        
        with patch('handlers.auth_handler.validate_verification_code', return_value=False):
            result = handle_verify_code(body)
            
            assert result['statusCode'] == 400
            body_data = json.loads(result['body'])
            assert body_data['valid'] is False

# Test: handle_request_password_reset
class TestHandleRequestPasswordReset:
    """Tests for password reset request."""
    
    def test_request_reset_success(self, sample_user, mock_auth_dependencies):
        """Request password reset successfully."""
        from handlers.auth_handler import handle_request_password_reset
        
        mock_auth_dependencies['users'].query.return_value = {'Items': [sample_user]}
        
        body = {'email': 'test@example.com'}
        result = handle_request_password_reset(body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'sent' in body_data['message'].lower()
    
    def test_request_reset_user_not_found(self, mock_auth_dependencies):
        """Request password reset for nonexistent user still returns success (security)."""
        from handlers.auth_handler import handle_request_password_reset
        
        mock_auth_dependencies['users'].query.return_value = {'Items': []}
        
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
        
        mock_auth_dependencies['users'].query.return_value = {'Items': [sample_user]}
        
        body = {
            'email': 'test@example.com',
            'reset_token': 'valid_token',
            'new_password': 'NewSecurePass123!'
        }
        
        with patch('handlers.auth_handler.validate_reset_token', return_value=True):
            result = handle_reset_password(body)
            
            assert result['statusCode'] == 200
            body_data = json.loads(result['body'])
            assert 'reset' in body_data['message'].lower()
    
    def test_reset_password_invalid_token(self, sample_user, mock_auth_dependencies):
        """Reset password fails with invalid token."""
        from handlers.auth_handler import handle_reset_password
        
        body = {
            'email': 'test@example.com',
            'reset_token': 'invalid_token',
            'new_password': 'NewPassword123!'
        }
        
        with patch('handlers.auth_handler.validate_reset_token', return_value=False):
            result = handle_reset_password(body)
            
            assert result['statusCode'] == 400

# Test: handle_delete_account
class TestHandleDeleteAccount:
    """Tests for account deletion."""
    
    def test_delete_account_success(self, sample_user, mock_auth_dependencies):
        """Delete user account successfully."""
        from handlers.auth_handler import handle_delete_account
        
        result = handle_delete_account(sample_user)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'deleted' in body_data['message'].lower()
        
        # Verify user was deleted from database
        mock_auth_dependencies['users'].delete_item.assert_called_once()
    
    def test_delete_account_cascading_deletions(self, sample_user, sample_gallery, mock_auth_dependencies):
        """Delete account removes all user data."""
        from handlers.auth_handler import handle_delete_account
        
        with patch('handlers.auth_handler.galleries_table') as mock_galleries, \
             patch('handlers.auth_handler.photos_table') as mock_photos:
            
            # User has galleries
            mock_galleries.query.return_value = {'Items': [sample_gallery]}
            mock_photos.query.return_value = {'Items': []}
            
            result = handle_delete_account(sample_user)
            
            assert result['statusCode'] == 200
            
            # Verify galleries were deleted
            assert mock_galleries.delete_item.called

# Test: handle_get_me
class TestHandleGetMe:
    """Tests for getting current user info."""
    
    def test_get_me_success(self, sample_user):
        """Get current user info successfully."""
        from handlers.auth_handler import handle_get_me
        
        result = handle_get_me(sample_user)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert body_data['id'] == sample_user['id']
        assert body_data['email'] == sample_user['email']
        assert 'password_hash' not in body_data  # Sensitive data excluded

# Test: Session management
class TestSessionManagement:
    """Tests for session creation and validation."""
    
    def test_create_session(self):
        """Create new session generates token."""
        from handlers.auth_handler import create_session
        
        with patch('handlers.auth_handler.sessions_table') as mock_sessions:
            user_id = 'user123'
            token = create_session(user_id)
            
            assert token is not None
            assert len(token) > 20
            mock_sessions.put_item.assert_called_once()
    
    def test_validate_session_valid(self):
        """Validate active session."""
        from handlers.auth_handler import validate_session
        
        with patch('handlers.auth_handler.sessions_table') as mock_sessions:
            # Mock valid session
            mock_sessions.get_item.return_value = {
                'Item': {
                    'token': 'valid_token',
                    'user_id': 'user123',
                    'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
                }
            }
            
            user_id = validate_session('valid_token')
            
            assert user_id == 'user123'
    
    def test_validate_session_expired(self):
        """Validate expired session returns None."""
        from handlers.auth_handler import validate_session
        
        with patch('handlers.auth_handler.sessions_table') as mock_sessions:
            # Mock expired session
            mock_sessions.get_item.return_value = {
                'Item': {
                    'token': 'expired_token',
                    'user_id': 'user123',
                    'expires_at': (datetime.utcnow() - timedelta(days=1)).isoformat()
                }
            }
            
            user_id = validate_session('expired_token')
            
            assert user_id is None

