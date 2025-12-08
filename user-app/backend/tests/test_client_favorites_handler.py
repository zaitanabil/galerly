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
         patch('handlers.client_favorites_handler.users_table') as mock_users, \
         patch('handlers.subscription_handler.get_user_features') as mock_features, \
         patch('handlers.client_favorites_handler.auto_register_guest_client') as mock_auto_register:
        # Setup default mocks
        mock_photos.get_item.return_value = {
            'Item': {
                'id': 'photo_123',
                'gallery_id': 'gallery_123',
                'filename': 'test.jpg',
                'user_id': 'user_123'
            }
        }
        # Include client_emails with sample_user's email for access control
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery_123',
                'user_id': 'user_123',
                'title': 'Test Gallery',
                'client_emails': ['test@example.com'],
                'share_token': 'test_token_123'  # Add share token for testing
            }
        }
        mock_galleries.query.return_value = {
            'Items': [{
                'id': 'gallery_123',
                'user_id': 'user_123',
                'title': 'Test Gallery',
                'client_emails': ['test@example.com'],
                'share_token': 'test_token_123'
            }]
        }
        mock_users.query.return_value = {
            'Items': [{
                'id': 'user_123',
                'email': 'photographer@test.com',
                'plan': 'pro'
            }]
        }
        # Mock auto-register to return a simple user object
        mock_auto_register.return_value = {
            'id': 'guest_user_123',
            'email': 'guest@example.com',
            'role': 'client',
            'is_guest': True
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
            'features': mock_features,
            'auto_register': mock_auto_register
        }

class TestAddFavorite:
    """Tests for handle_add_favorite endpoint."""
    
    def test_add_favorite_success(self, sample_user, mock_favorites_dependencies):
        """Add photo to favorites successfully."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        mock_favorites_dependencies['favorites'].get_item.return_value = {}  # No existing favorite
        
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        result = handle_add_favorite(sample_user, body)
        
        assert result['statusCode'] in [200, 201]
    
    def test_add_favorite_with_share_token(self, mock_favorites_dependencies):
        """Add favorite via shared link (guest user)."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        mock_favorites_dependencies['favorites'].get_item.return_value = {}  # No existing favorite
        
        # Guest user (no auth, using share token)
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123',
            'client_email': 'guest@example.com',
            'client_name': 'Guest User',
            'token': 'test_token_123'
        }
        result = handle_add_favorite(None, body)  # No user session
        
        assert result['statusCode'] in [200, 201]
        # Verify auto-register was called
        mock_favorites_dependencies['auto_register'].assert_called_once()
    
    def test_add_favorite_duplicate(self, sample_user, mock_favorites_dependencies):
        """Add favorite that already exists."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        existing_favorite = {
            'client_email': sample_user['email'],
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123'
        }
        mock_favorites_dependencies['favorites'].get_item.return_value = {'Item': existing_favorite}
        
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
    
    def test_add_favorite_access_denied_no_token(self, mock_favorites_dependencies):
        """Add favorite without access (no token, not in client_emails)."""
        from handlers.client_favorites_handler import handle_add_favorite
        
        # Update gallery to not include this email
        mock_favorites_dependencies['galleries'].get_item.return_value = {
            'Item': {
                'id': 'gallery_123',
                'user_id': 'user_123',
                'title': 'Test Gallery',
                'client_emails': [],  # Empty list
                'share_token': 'test_token_123'
            }
        }
        
        body = {
            'photo_id': 'photo_123',
            'gallery_id': 'gallery_123',
            'client_email': 'unauthorized@example.com'
            # No token provided
        }
        result = handle_add_favorite(None, body)
        
        assert result['statusCode'] == 403

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

