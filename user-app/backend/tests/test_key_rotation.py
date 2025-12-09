"""
Security Tests - Key Rotation System
Tests for weekly key rotation functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from utils.key_rotation import (
    get_current_key,
    check_key_rotation_needed,
    rotate_key,
    ROTATION_POLICIES
)

@pytest.fixture
def mock_key_rotation_table(monkeypatch):
    """Mock DynamoDB key rotation table"""
    mock_table = MagicMock()
    monkeypatch.setattr('utils.key_rotation.key_rotation_table', mock_table)
    return mock_table

def test_rotation_policies_exist():
    """Test that rotation policies are defined for all key types"""
    required_key_types = [
        'password_salt',
        'session_secret',
        'api_key_salt',
        'encryption_key'
    ]
    
    for key_type in required_key_types:
        assert key_type in ROTATION_POLICIES
        policy = ROTATION_POLICIES[key_type]
        assert 'rotation_interval_days' in policy
        assert 'requires_user_action' in policy
        assert 'grace_period_days' in policy

def test_rotation_interval_is_weekly():
    """Test that all keys rotate weekly (7 days)"""
    for key_type, policy in ROTATION_POLICIES.items():
        assert policy['rotation_interval_days'] == 7, f"{key_type} should rotate weekly"

def test_get_current_key_returns_active_key(mock_key_rotation_table):
    """Test that get_current_key returns the active key"""
    mock_key = {
        'key_id': 'key_123',
        'key_value': 'secret_value_xyz',
        'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
        'status': 'active'
    }
    
    mock_key_rotation_table.query.return_value = {'Items': [mock_key]}
    
    key_id, key_value, created_at = get_current_key('password_salt')
    
    assert key_id == 'key_123'
    assert key_value == 'secret_value_xyz'
    assert isinstance(created_at, str)

def test_get_current_key_generates_if_none_exists(mock_key_rotation_table):
    """Test that get_current_key generates new key if none exists"""
    # Return empty result (no active keys)
    mock_key_rotation_table.query.return_value = {'Items': []}
    mock_key_rotation_table.put_item.return_value = {}
    
    key_id, key_value, created_at = get_current_key('password_salt')
    
    # Should generate new key
    assert key_id is not None
    assert key_value is not None
    assert created_at is not None
    
    # Should have called put_item to store it
    assert mock_key_rotation_table.put_item.called

def test_check_key_rotation_needed_old_key(mock_key_rotation_table):
    """Test that rotation is needed for old keys"""
    # Key created 10 days ago (older than 7 day policy)
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).replace(tzinfo=None).isoformat() + 'Z'
    
    mock_key_rotation_table.query.return_value = {
        'Items': [{
            'key_id': 'old_key',
            'key_value': 'value',
            'created_at': old_date,
            'status': 'active'
        }]
    }
    
    needs_rotation, age_days = check_key_rotation_needed('password_salt')
    
    assert needs_rotation is True
    assert age_days >= 7

def test_check_key_rotation_not_needed_recent_key(mock_key_rotation_table):
    """Test that rotation is not needed for recent keys"""
    # Key created 2 days ago (newer than 7 day policy)
    recent_date = (datetime.now(timezone.utc) - timedelta(days=2)).replace(tzinfo=None).isoformat() + 'Z'
    
    mock_key_rotation_table.query.return_value = {
        'Items': [{
            'key_id': 'new_key',
            'key_value': 'value',
            'created_at': recent_date,
            'status': 'active'
        }]
    }
    
    needs_rotation, age_days = check_key_rotation_needed('password_salt')
    
    assert needs_rotation is False
    assert age_days <= 2  # Should be 2 or less days old

def test_rotate_key_marks_old_key_as_rotated(mock_key_rotation_table):
    """Test that rotate_key marks old key as rotated"""
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).replace(tzinfo=None).isoformat() + 'Z'
    
    mock_key_rotation_table.query.return_value = {
        'Items': [{
            'key_id': 'old_key',
            'key_value': 'old_value',
            'created_at': old_date,
            'status': 'active'
        }]
    }
    mock_key_rotation_table.update_item.return_value = {}
    mock_key_rotation_table.put_item.return_value = {}
    
    new_key_id, new_key_value, old_key_id = rotate_key('password_salt')
    
    # Should have updated old key status
    assert mock_key_rotation_table.update_item.called
    update_call = mock_key_rotation_table.update_item.call_args
    assert update_call[1]['Key']['key_id'] == 'old_key'
    
    # Should have created new key
    assert new_key_id != old_key_id
    assert new_key_value != 'old_value'

def test_rotate_key_creates_new_key(mock_key_rotation_table):
    """Test that rotate_key creates a new active key"""
    mock_key_rotation_table.query.return_value = {
        'Items': [{
            'key_id': 'old_key',
            'key_value': 'old_value',
            'created_at': (datetime.now(timezone.utc) - timedelta(days=10)).replace(tzinfo=None).isoformat() + 'Z',
            'status': 'active'
        }]
    }
    mock_key_rotation_table.update_item.return_value = {}
    mock_key_rotation_table.put_item.return_value = {}
    
    new_key_id, new_key_value, old_key_id = rotate_key('password_salt')
    
    # Should have created new key
    assert mock_key_rotation_table.put_item.called
    new_key_call = mock_key_rotation_table.put_item.call_args
    new_key_item = new_key_call[1]['Item']
    
    assert new_key_item['status'] == 'active'
    assert new_key_item['key_id'] == new_key_id
    assert 'expires_at' in new_key_item

@pytest.mark.integration
def test_user_action_required_for_password_rotation():
    """Test that password rotation requires user action"""
    policy = ROTATION_POLICIES['password_salt']
    
    assert policy['requires_user_action'] is True
    assert policy['grace_period_days'] == 14  # 2 weeks to update

@pytest.mark.integration
def test_automatic_rotation_for_session_secret():
    """Test that session secret rotates automatically"""
    policy = ROTATION_POLICIES['session_secret']
    
    assert policy['requires_user_action'] is False
    assert policy['grace_period_days'] == 1  # Sessions expire quickly

@pytest.mark.integration
def test_rotation_interval_enforcement():
    """Test that rotation interval is enforced"""
    # All keys should rotate weekly
    for key_type, policy in ROTATION_POLICIES.items():
        rotation_days = policy['rotation_interval_days']
        assert rotation_days == 7, f"{key_type} must rotate weekly for security compliance"

