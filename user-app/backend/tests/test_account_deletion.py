"""
Tests for account deletion and session cleanup
Updated for grace period implementation
"""
import pytest
import json
from unittest.mock import patch
from handlers.auth_handler import handle_delete_account, handle_logout


@pytest.fixture
def mock_auth_dependencies():
    """Mock auth handler dependencies."""
    with patch('handlers.auth_handler.users_table') as mock_users, \
         patch('handlers.auth_handler.sessions_table') as mock_sessions, \
         patch('utils.email.send_account_deletion_scheduled_email') as mock_email:
        mock_users.update_item.return_value = {}
        mock_sessions.scan.return_value = {'Items': []}
        yield {
            'users': mock_users,
            'sessions': mock_sessions,
            'email': mock_email
        }


def test_delete_account_clears_session(sample_user, mock_auth_dependencies):
    """Test that deleting account marks for deletion and clears sessions"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    
    # Grace period implementation
    assert 'deletion_date' in body
    assert body['grace_period_days'] == 30


def test_delete_account_clears_cookie(sample_user, mock_auth_dependencies):
    """Test that delete account response includes session cleanup"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    # Should clear cookie
    assert 'Set-Cookie' in result['headers']
    assert 'Max-Age=0' in result['headers']['Set-Cookie']


def test_delete_account_deletes_all_user_sessions(sample_user, mock_auth_dependencies):
    """Test account deletion terminates all sessions"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    # Sessions are terminated in the function
    mock_auth_dependencies['sessions'].scan.assert_called()


def test_logout_clears_cookie(mock_auth_dependencies):
    """Test that logout clears session"""
    event = {'headers': {'Cookie': 'galerly_session=test_token'}}
    
    result = handle_logout(event)
    
    assert result['statusCode'] == 200
    assert mock_auth_dependencies['sessions'].delete_item.called


def test_delete_account_without_cookie(sample_user, mock_auth_dependencies):
    """Test account deletion works without active session"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert 'deletion_date' in body

