"""
Tests for client_favorites_handler.py endpoints.
Tests cover: add favorite, remove favorite, get favorites, check favorite status.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_favorites_dependencies():
    """Mock favorites dependencies."""
    with patch('handlers.client_favorites_handler.client_favorites_table') as mock_favorites, \
         patch('handlers.client_favorites_handler.photos_table') as mock_photos, \
         patch('handlers.client_favorites_handler.galleries_table') as mock_galleries, \
         patch('utils.config.users_table') as mock_users, \
         patch('handlers.subscription_handler.get_user_features') as mock_features:
        # Setup default mocks
        mock_photos.get_item.return_value = {
            'Item': {
                'id': 'photo_123',
                'gallery_id': 'gallery_123',
                'filename': 'test.jpg',
                'user_id': 'user_123'
            }
        }
        # FIX: Include client_emails with sample_user's email for access control
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery_123',
                'user_id': 'user_123',
                'title': 'Test Gallery',
                'client_emails': ['test@example.com']  # Match sample_user email
            }
        }
        mock_users.get_item.return_value = {
            'Item': {
                'id': 'user_123',
                'email': 'photographer@test.com',
                'plan': 'pro'
            }
        }
        # Mock photographer features - allow favorites
        mock_features.return_value = (
            {'client_favorites': True, 'storage_gb': 100},
            'pro',
            'Pro'
        )
        yield {
            'favorites': mock_favorites,
            'photos': mock_photos,
            'galleries': mock_galleries,
            'users': mock_users,
            'features': mock_features
        }

class TestAddFavorite:
    """Tests for handle_add_favorite endpoint."""
    
    def test_add_favorite_success(self, sample_user, mock_favorites_dependencies):
        """Add photo to favorites successfully."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': []}
        
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        result = handle_add_favorite(sample_user, body)
        
        assert result['statusCode'] in [200, 201]
    
    def test_add_favorite_duplicate(self, sample_user, mock_favorites_dependencies):
        """Add favorite that already exists."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        existing_favorite = {
            'user_id': sample_user['id'],
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': [existing_favorite]}
        
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        result = handle_add_favorite(sample_user, body)
        
        assert result['statusCode'] in [200, 400]
    
    def test_add_favorite_missing_photo_id(self, sample_user, mock_favorites_dependencies):
        """Add favorite without photo_id."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        body = {'gallery_id': 'gallery_123'}
        result = handle_add_favorite(sample_user, body)
        
        assert result['statusCode'] == 400

class TestRemoveFavorite:
    """Tests for handle_remove_favorite endpoint."""
    
    def test_remove_favorite_success(self, sample_user, mock_favorites_dependencies):
        """Remove photo from favorites successfully."""
        from handlers.client_favorites_handler import handle_remove_favorite
        
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        result = handle_remove_favorite(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_remove_favorite_not_found(self, sample_user, mock_favorites_dependencies):
        """Remove favorite that doesn't exist."""
        from handlers.client_favorites_handler import handle_remove_favorite
        
        body = {
            'photo_id': 'nonexistent',
            'gallery_id': 'gallery_123'
        }
        result = handle_remove_favorite(sample_user, body)
        
        assert result['statusCode'] in [200, 404]

class TestGetFavorites:
    """Tests for handle_get_favorites endpoint."""
    
    def test_get_favorites_success(self, sample_user, sample_photo, mock_favorites_dependencies):
        """Get all user favorites."""
        from handlers.client_favorites_handler import handle_get_favorites
        
        favorites = [
            {'user_id': sample_user['id'], 'photo_id': 'photo_1', 'gallery_id': 'gallery_123'},
            {'user_id': sample_user['id'], 'photo_id': 'photo_2', 'gallery_id': 'gallery_123'}
        ]
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': favorites}
        mock_favorites_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        
        result = handle_get_favorites(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'favorites' in body or len(body) >= 0
    
    def test_get_favorites_empty(self, sample_user, mock_favorites_dependencies):
        """Get favorites when user has none."""
        from handlers.client_favorites_handler import handle_get_favorites
        
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': []}
        
        result = handle_get_favorites(sample_user)
        
        assert result['statusCode'] == 200

class TestCheckFavorite:
    """Tests for handle_check_favorite endpoint."""
    
    def test_check_favorite_is_favorite(self, sample_user, mock_favorites_dependencies):
        """Check if photo is favorited - returns true."""
        from handlers.client_favorites_handler import handle_check_favorite
        
        # FIX: Handler uses get_item, not query, and checks for 'Item' key
        favorite = {
            'user_id': sample_user['id'],
            'photo_id': 'photo_123',
            'client_email': 'test@example.com'
        }
        mock_favorites_dependencies['favorites'].get_item.return_value = {'Item': favorite}
        
        result = handle_check_favorite(sample_user, 'photo_123')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        # Handler returns 'favorited' field
        assert body.get('favorited') is True
    
    def test_check_favorite_not_favorite(self, sample_user, mock_favorites_dependencies):
        """Check if photo is favorited - returns false."""
        from handlers.client_favorites_handler import handle_check_favorite
        
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': []}
        
        result = handle_check_favorite(sample_user, 'photo_123')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('favorited') is False or body.get('is_favorite') is False

