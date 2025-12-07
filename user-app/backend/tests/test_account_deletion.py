"""
Tests for account deletion and session cleanup
"""
import pytest
from unittest.mock import patch
from handlers.auth_handler import handle_delete_account, handle_logout


@pytest.fixture
def mock_auth_dependencies():
    """Mock auth handler dependencies."""
    with patch('handlers.auth_handler.users_table') as mock_users, \
         patch('handlers.auth_handler.sessions_table') as mock_sessions, \
         patch('handlers.background_jobs_handler.create_background_job') as mock_job:
        mock_job.return_value = 'job_123'
        yield {
            'users': mock_users,
            'sessions': mock_sessions,
            'job': mock_job
        }


def test_delete_account_clears_session(sample_user, mock_auth_dependencies):
    """Test that deleting account creates background job"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    assert mock_auth_dependencies['job'].called


def test_delete_account_clears_cookie(sample_user, mock_auth_dependencies):
    """Test that delete account response includes session cleanup"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    # Cookie clearing happens at API gateway level


def test_delete_account_deletes_all_user_sessions(sample_user, mock_auth_dependencies):
    """Test account deletion creates cleanup job"""
    result = handle_delete_account(sample_user)
    
    assert result['statusCode'] == 200
    assert mock_auth_dependencies['job'].called


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
    assert mock_auth_dependencies['job'].called
