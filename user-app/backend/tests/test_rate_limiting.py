"""
Security Tests - Rate Limiting
Tests for API rate limiting functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from utils.rate_limiter import (
    get_client_identifier,
    check_rate_limit,
    RATE_LIMITS
)

@pytest.fixture
def mock_event():
    """Create a mock AWS Lambda event"""
    return {
        'headers': {
            'X-Forwarded-For': '203.0.113.1'
        },
        'requestContext': {
            'identity': {
                'sourceIp': '203.0.113.1'
            }
        }
    }

@pytest.fixture
def mock_dynamodb_table(monkeypatch):
    """Mock DynamoDB table for rate limiting"""
    mock_table = MagicMock()
    
    # Mock empty rate limit (first request)
    mock_table.get_item.return_value = {}
    mock_table.put_item.return_value = {}
    
    # Patch the rate_limit_table
    with patch('utils.rate_limiter.rate_limit_table', mock_table):
        yield mock_table

def test_get_client_identifier_by_ip(mock_event):
    """Test that client identifier is extracted from IP address"""
    with patch('utils.auth.get_user_from_token', return_value=None):
        identifier = get_client_identifier(mock_event)
    
    assert identifier == 'ip:203.0.113.1'

def test_get_client_identifier_by_user():
    """Test that authenticated users are identified by user ID"""
    mock_event = {
        'headers': {'X-Forwarded-For': '203.0.113.1'}
    }
    mock_user = {'id': 'user-123', 'email': 'test@example.com'}
    
    with patch('utils.auth.get_user_from_token', return_value=mock_user):
        identifier = get_client_identifier(mock_event)
    
    assert identifier == 'user:user-123'

def test_check_rate_limit_first_request(mock_event, mock_dynamodb_table):
    """Test that first request is allowed"""
    is_allowed, remaining, reset_at = check_rate_limit(mock_event, 'auth_login')
    
    assert is_allowed is True
    assert remaining == RATE_LIMITS['auth_login']['limit'] - 1
    assert isinstance(reset_at, str)

def test_check_rate_limit_within_limit(mock_event, mock_dynamodb_table):
    """Test that requests within limit are allowed"""
    # Mock 2 previous requests with timezone-aware datetime
    now = datetime.now(timezone.utc)
    mock_dynamodb_table.get_item.return_value = {
        'Item': {
            'identifier': 'ip:203.0.113.1:auth_login',
            'requests': [
                (now - timedelta(seconds=10)).isoformat().replace('+00:00', 'Z'),
                (now - timedelta(seconds=5)).isoformat().replace('+00:00', 'Z')
            ]
        }
    }
    
    is_allowed, remaining, reset_at = check_rate_limit(mock_event, 'auth_login')
    
    assert is_allowed is True
    # Should have 2 previous + 1 new = 3 total, limit is 5, so remaining should be 2
    assert remaining == 2

def test_check_rate_limit_exceeded(mock_event, mock_dynamodb_table):
    """Test that rate limit is enforced when exceeded"""
    # Mock limit number of requests within window
    now = datetime.now(timezone.utc)
    limit = RATE_LIMITS['auth_login']['limit']
    
    # Create limit number of recent requests
    requests = [
        (now - timedelta(seconds=i*10)).isoformat().replace('+00:00', 'Z')
        for i in range(limit)
    ]
    
    mock_dynamodb_table.get_item.return_value = {
        'Item': {
            'identifier': 'ip:203.0.113.1:auth_login',
            'requests': requests
        }
    }
    
    is_allowed, remaining, reset_at = check_rate_limit(mock_event, 'auth_login')
    
    assert is_allowed is False
    assert remaining == 0

def test_check_rate_limit_old_requests_ignored(mock_event, mock_dynamodb_table):
    """Test that old requests outside window are not counted"""
    now = datetime.now(timezone.utc)
    window = RATE_LIMITS['auth_login']['window']
    
    # Create requests outside the window
    old_requests = [
        (now - timedelta(seconds=window + 100)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(seconds=window + 200)).isoformat().replace('+00:00', 'Z')
    ]
    
    mock_dynamodb_table.get_item.return_value = {
        'Item': {
            'identifier': 'ip:203.0.113.1:auth_login',
            'requests': old_requests
        }
    }
    
    is_allowed, remaining, reset_at = check_rate_limit(mock_event, 'auth_login')
    
    # Old requests should be cleaned up, so this should be like first request
    assert is_allowed is True
    assert remaining == RATE_LIMITS['auth_login']['limit'] - 1

def test_rate_limit_different_endpoints():
    """Test that different endpoints have different rate limits"""
    # Auth login: 5 per 5 minutes
    assert RATE_LIMITS['auth_login']['limit'] == 5
    assert RATE_LIMITS['auth_login']['window'] == 300
    
    # Auth register: 3 per hour
    assert RATE_LIMITS['auth_register']['limit'] == 3
    assert RATE_LIMITS['auth_register']['window'] == 3600
    
    # Password reset: 3 per hour
    assert RATE_LIMITS['auth_password_reset']['limit'] == 3
    assert RATE_LIMITS['auth_password_reset']['window'] == 3600

def test_rate_limit_fail_open_on_error(mock_event, mock_dynamodb_table):
    """Test that rate limiter fails open (allows requests) on errors"""
    # Mock DynamoDB error
    mock_dynamodb_table.get_item.side_effect = Exception("DynamoDB error")
    
    is_allowed, remaining, reset_at = check_rate_limit(mock_event, 'auth_login')
    
    # Should allow request despite error (fail open for availability)
    assert is_allowed is True

@pytest.mark.integration
def test_rate_limit_multiple_users():
    """Test that rate limits are per-user/IP, not global"""
    mock_event1 = {
        'headers': {'X-Forwarded-For': '203.0.113.1'},
        'requestContext': {'identity': {'sourceIp': '203.0.113.1'}}
    }
    mock_event2 = {
        'headers': {'X-Forwarded-For': '203.0.113.2'},
        'requestContext': {'identity': {'sourceIp': '203.0.113.2'}}
    }
    
    with patch('utils.auth.get_user_from_token', return_value=None):
        id1 = get_client_identifier(mock_event1)
        id2 = get_client_identifier(mock_event2)
    
    # Different IPs should have different identifiers
    assert id1 != id2
    assert id1 == 'ip:203.0.113.1'
    assert id2 == 'ip:203.0.113.2'

