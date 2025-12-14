"""
Tests for username generation and uniqueness
"""
import pytest
import json  # FIX: Add json import for parsing response bodies
from handlers.auth_handler import (
    generate_username_from_name,
    check_username_exists,
    generate_unique_username,
    handle_register
)


def test_generate_username_from_name_basic():
    """Test basic username generation from full names"""
    assert generate_username_from_name("John Doe") == "johndoe"
    assert generate_username_from_name("Mary Jane") == "maryjane"
    assert generate_username_from_name("Bob") == "bob"


def test_generate_username_from_name_with_special_chars():
    """Test username generation with special characters"""
    # FIX: Function generates full cleaned names (up to 20 chars), not truncated arbitrarily
    assert generate_username_from_name("Mary-Jane Smith") == "maryjanesmith"  # 13 chars
    assert generate_username_from_name("O'Connor") == "oconnor"
    assert generate_username_from_name("Jean-Pierre") == "jeanpierre"


def test_generate_username_from_name_with_accents():
    """Test username generation with accented characters"""
    # FIX: Function correctly removes accents
    assert generate_username_from_name("José García") == "josegarcia"
    assert generate_username_from_name("François Müller") == "francoismuller"
    assert generate_username_from_name("Søren Ørsted") == "sorenorsted"


def test_generate_username_from_name_truncation():
    """Test username truncation to 20 characters"""
    long_name = "Christopher Alexander Montgomery"
    username = generate_username_from_name(long_name)
    assert len(username) <= 20
    # FIX: Function truncates at 20 chars: "christopheralexandermontgomery" -> "christopheralexander"
    assert username == "christopheralexander"


def test_generate_username_from_name_empty():
    """Test username generation with empty/invalid input"""
    assert generate_username_from_name("") == ""
    assert generate_username_from_name("   ") == ""
    assert generate_username_from_name("!!!") == ""


def test_check_username_exists_not_exists():
    """Test checking for non-existent username"""
    from tests.conftest import global_mock_table
    
    # Configure mock to return no users
    global_mock_table.scan.return_value = {'Items': []}
    
    exists = check_username_exists("nonexistentuser123")
    assert exists is False


def test_check_username_exists_does_exist():
    """Test checking for existing username"""
    from tests.conftest import global_mock_table
    
    # Configure mock to return matching user
    global_mock_table.scan.return_value = {
        'Items': [{'username': 'johndoe'}]
    }
    
    exists = check_username_exists("johndoe")
    assert exists is True


def test_generate_unique_username_available():
    """Test generating username when first choice is available"""
    from tests.conftest import global_mock_table
    from unittest.mock import patch
    
    # Mock: no existing users with this username
    with patch('handlers.auth_handler.check_username_exists', return_value=False):
        username = generate_unique_username("Jane Smith", "jane@example.com")
        assert username == "janesmith"


def test_generate_unique_username_collision():
    """Test generating username with collision - should append number"""
    from unittest.mock import patch
    
    # Simulate collision: first check returns True (exists), second returns False (available)
    with patch('handlers.auth_handler.check_username_exists', side_effect=[True, False]):
        username = generate_unique_username("John Doe", "johndoe2@example.com")
        
        # Should get johndoe1
        assert username.startswith("johndoe")
        assert username != "johndoe"  # Must be different
        assert len(username) <= 50  # Within limit


def test_generate_unique_username_multiple_collisions():
    """Test generating username with multiple collisions"""
    from unittest.mock import patch
    
    # Simulate multiple collisions: johndoe, johndoe1, johndoe2 exist, johndoe3 available
    with patch('handlers.auth_handler.check_username_exists', side_effect=[True, True, True, False]):
        username = generate_unique_username("John Doe", "john3@example.com")
        
        # Should get johndoe3
        assert username == "johndoe3"


def test_generate_unique_username_fallback_to_email():
    """Test fallback to email when name is invalid"""
    from unittest.mock import patch
    
    # Mock: username from email is available
    with patch('handlers.auth_handler.check_username_exists', return_value=False):
        username = generate_unique_username("!!!", "testuser@example.com")
        assert username == "testuser"


def test_generate_unique_username_very_short_name():
    """Test handling of very short names"""
    from unittest.mock import patch
    
    # Mock: generated username is available
    with patch('handlers.auth_handler.check_username_exists', return_value=False):
        username = generate_unique_username("A B", "ab@example.com")
        assert len(username) >= 3  # Must meet minimum length


def test_handle_register_auto_generates_username():
    """Test that registration auto-generates username from name"""
    from tests.conftest import global_mock_table
    from unittest.mock import patch, MagicMock
    import secrets
    
    # Create verification token
    token = secrets.token_urlsafe(32)
    
    # Mock get_item to handle both sessions and users lookups
    def mock_get_item(Key):
        if 'token' in Key:
            # Sessions table lookup
            return {
                'Item': {
        'token': token,
        'type': 'email_verification',
        'email': 'newuser@example.com',
        'code': '123456',
        'created_at': '2024-01-01T00:00:00Z',
                    'expires_at': 9999999999,
        'verified': True
                }
            }
        elif 'email' in Key:
            # Users table lookup - no existing user
            return {}
        return {}
    
    # Configure global mock
    global_mock_table.get_item.side_effect = mock_get_item
    global_mock_table.scan.return_value = {'Items': []}  # No existing users for username check
    global_mock_table.put_item.return_value = {}  # Success
    global_mock_table.delete_item.return_value = {}  # Success
    
    # Register with full name (no username provided)
    body = {
        'email': 'newuser@example.com',
        'password': 'SecurePass123',
        'name': 'Alice Johnson',
        'role': 'photographer',
        'verification_token': token
    }
    
    response = handle_register(body)
    
    assert response['statusCode'] == 201
    body_data = json.loads(response['body'])
    assert body_data['username'] == 'alicejohnson'
    assert body_data['name'] == 'Alice Johnson'


def test_handle_register_requires_name():
    """Test that registration requires full name"""
    from tests.conftest import global_mock_table
    import secrets
    
    token = secrets.token_urlsafe(32)
    
    # Mock get_item to handle sessions lookup
    def mock_get_item(Key):
        if 'token' in Key:
            return {
                'Item': {
        'token': token,
        'type': 'email_verification',
        'email': 'test@example.com',
        'code': '123456',
        'created_at': '2024-01-01T00:00:00Z',
        'expires_at': 9999999999,
        'verified': True
                }
            }
        return {}
    
    global_mock_table.get_item.side_effect = mock_get_item
    
    # Try to register without name
    body = {
        'email': 'test@example.com',
        'password': 'SecurePass123',
        'role': 'photographer',
        'verification_token': token
    }
    
    response = handle_register(body)
    
    assert response['statusCode'] == 400
    body_data = json.loads(response['body'])
    assert 'name' in body_data['error'].lower()


def test_profile_update_username_uniqueness():
    """Test that profile update checks username uniqueness"""
    from tests.conftest import global_mock_table
    from handlers.profile_handler import handle_update_profile
    
    user2_data = {
        'email': 'user2@example.com',
        'username': 'user2',
        'name': 'User Two',
        'password_hash': 'hash',
        'role': 'photographer',
        'created_at': '2024-01-01T00:00:00Z',
        'plan': 'free'
    }
    
    # Mock get_item to handle user lookup, scan to find conflicting username
    def mock_get_item(Key):
        if Key.get('email') == 'user2@example.com':
            return {'Item': user2_data}
        return {}
    
    global_mock_table.get_item.side_effect = mock_get_item
    global_mock_table.scan.return_value = {'Items': [{'username': 'user1', 'email': 'other@example.com'}]}
    
    # User 2 tries to change username to user1 (already taken)
    user = {'id': 'user2', 'email': 'user2@example.com', 'role': 'photographer', 'plan': 'pro'}
    body = {'username': 'user1'}
    
    response = handle_update_profile(user, body)
    
    assert response['statusCode'] == 400
    body_data = json.loads(response['body'])
    assert 'already taken' in body_data['error'].lower() or 'exists' in body_data['error'].lower()


def test_profile_update_username_own_username():
    """Test that user can keep their own username"""
    from tests.conftest import global_mock_table
    from handlers.profile_handler import handle_update_profile
    
    user_data = {
        'id': 'user123',
        'email': 'user@example.com',
        'username': 'myusername',
        'name': 'My Name',
        'password_hash': 'hash',
        'role': 'photographer',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'plan': 'free'
    }
    
    # Mock get_item to return user data, scan to return no conflicts, update_item to succeed
    def mock_get_item(Key):
        if Key.get('email') == 'user@example.com':
            return {'Item': user_data}
        return {}
    
    global_mock_table.get_item.side_effect = mock_get_item
    global_mock_table.scan.return_value = {'Items': []}  # No conflicts (own username excluded by filter)
    global_mock_table.update_item.return_value = {'Attributes': user_data}
    
    # User updates profile with same username (should work)
    user = {'id': 'user123', 'email': 'user@example.com', 'role': 'photographer', 'plan': 'pro'}
    body = {'username': 'myusername', 'bio': 'New bio'}
    
    response = handle_update_profile(user, body)
    
    # Should succeed (not conflict with own username)
    assert response['statusCode'] == 200


def test_profile_update_username_new_unique():
    """Test that user can change to a new unique username"""
    from tests.conftest import global_mock_table
    from handlers.profile_handler import handle_update_profile
    
    old_user_data = {
        'id': 'user456',
        'email': 'user@example.com',
        'username': 'oldusername',
        'name': 'My Name',
        'password_hash': 'hash',
        'role': 'photographer',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'plan': 'free'
    }
    
    updated_user_data = old_user_data.copy()
    updated_user_data['username'] = 'newunique'
    
    # Mock get_item for user lookup, scan for username conflict check, update_item for save
    def mock_get_item(Key):
        if Key.get('email') == 'user@example.com':
            return {'Item': old_user_data}
        return {}
    
    global_mock_table.get_item.side_effect = mock_get_item
    global_mock_table.scan.return_value = {'Items': []}  # No conflicts
    global_mock_table.update_item.return_value = {'Attributes': updated_user_data}
    
    # Change to new unique username
    user = {'id': 'user123', 'email': 'user@example.com', 'role': 'photographer', 'plan': 'pro'}
    body = {'username': 'newunique'}
    
    response = handle_update_profile(user, body)
    
    assert response['statusCode'] == 200
    body_data = json.loads(response['body'])
    assert body_data['username'] == 'newunique'

