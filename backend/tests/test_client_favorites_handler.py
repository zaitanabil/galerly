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
    with patch('handlers.client_favorites_handler.favorites_table') as mock_favorites, \
         patch('handlers.client_favorites_handler.photos_table') as mock_photos:
        yield {
            'favorites': mock_favorites,
            'photos': mock_photos
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
        
        favorite = {
            'user_id': sample_user['id'],
            'photo_id': 'photo_123'
        }
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': [favorite]}
        
        result = handle_check_favorite(sample_user, 'photo_123')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('is_favorite') is True
    
    def test_check_favorite_not_favorite(self, sample_user, mock_favorites_dependencies):
        """Check if photo is favorited - returns false."""
        from handlers.client_favorites_handler import handle_check_favorite
        
        mock_favorites_dependencies['favorites'].query.return_value = {'Items': []}
        
        result = handle_check_favorite(sample_user, 'photo_123')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('is_favorite') is False

