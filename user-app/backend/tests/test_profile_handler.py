"""
Tests for profile_handler.py endpoint.
Tests cover: profile updates, user settings, bio, profile photo.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_profile_dependencies():
    """Mock profile dependencies."""
    with patch('handlers.profile_handler.users_table') as mock_users:
        yield {'users': mock_users}

class TestProfileHandler:
    """Tests for handle_update_profile endpoint."""
    
    def test_update_profile_name(self, sample_user, mock_profile_dependencies):
        """Update user profile name."""
        from handlers.profile_handler import handle_update_profile
        
        mock_profile_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'name': 'Updated Name'}
        result = handle_update_profile(sample_user, body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body.get('name') == 'Updated Name' or 'success' in response_body.get('message', '').lower()
    
    def test_update_profile_bio(self, sample_user, mock_profile_dependencies):
        """Update user bio."""
        from handlers.profile_handler import handle_update_profile
        
        mock_profile_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'bio': 'Professional photographer specializing in weddings'}
        result = handle_update_profile(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_update_profile_city(self, sample_user, mock_profile_dependencies):
        """Update user city."""
        from handlers.profile_handler import handle_update_profile
        
        mock_profile_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'city': 'New York', 'country': 'USA'}
        result = handle_update_profile(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_update_profile_portfolio_url(self, sample_user, mock_profile_dependencies):
        """Update portfolio URL."""
        from handlers.profile_handler import handle_update_profile
        
        mock_profile_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'portfolio_url': 'https://photos.example.com'}
        result = handle_update_profile(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_update_profile_multiple_fields(self, sample_user, mock_profile_dependencies):
        """Update multiple profile fields at once."""
        from handlers.profile_handler import handle_update_profile
        
        mock_profile_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {
            'name': 'New Name',
            'bio': 'New bio',
            'city': 'San Francisco',
            'phone': '+1234567890'
        }
        result = handle_update_profile(sample_user, body)
        
        assert result['statusCode'] == 200

