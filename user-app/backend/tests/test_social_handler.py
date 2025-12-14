"""
Unit tests for social sharing handler
Tests gallery and photo share URL generation and embed code
"""
import pytest
from unittest.mock import Mock, patch
from handlers.social_handler import (
    handle_get_gallery_share_info,
    handle_get_photo_share_info
)


class TestGalleryShareInfo:
    """Test gallery share information generation"""
    
    @patch('handlers.social_handler.galleries_table')
    def test_get_gallery_share_info_success(self, mock_galleries):
        """Test successful gallery share info retrieval"""
        gallery_id = 'gallery123'
        user = {'id': 'photo123', 'role': 'photographer'}
        
        # Mock gallery exists
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'photo123',
                'name': 'Wedding Gallery',
                'share_token': 'abc123xyz',
                'privacy': 'public'
            }
        }
        
        result = handle_get_gallery_share_info(gallery_id, user)
        assert result['statusCode'] == 200
        
        import json
        body = json.loads(result['body'])
        assert 'share_url' in body
        assert 'embed_code' in body
        assert body['is_public'] is True
    
    def test_get_gallery_share_info_invalid_id(self):
        """Test validation rejects invalid gallery ID"""
        gallery_id = 'gallery/123'  # Contains invalid character
        
        result = handle_get_gallery_share_info(gallery_id)
        assert result['statusCode'] == 400
    
    def test_get_gallery_share_info_too_long(self):
        """Test validation rejects overly long gallery ID"""
        gallery_id = 'a' * 150  # Exceeds 128 char limit
        
        result = handle_get_gallery_share_info(gallery_id)
        assert result['statusCode'] == 400
    
    @patch('handlers.social_handler.galleries_table')
    def test_get_gallery_share_info_not_found(self, mock_galleries):
        """Test error when gallery not found"""
        gallery_id = 'nonexistent'
        user = {'id': 'photo123', 'role': 'photographer'}
        
        # Mock gallery not found
        mock_galleries.get_item.return_value = {}
        
        result = handle_get_gallery_share_info(gallery_id, user)
        assert result['statusCode'] == 404


class TestPhotoShareInfo:
    """Test photo share information generation"""
    
    @patch('handlers.social_handler.galleries_table')
    @patch('handlers.social_handler.photos_table')
    def test_get_photo_share_info_success(self, mock_photos, mock_galleries):
        """Test successful photo share info retrieval"""
        photo_id = 'photo123'
        
        # Mock photo exists
        mock_photos.get_item.return_value = {
            'Item': {
                'id': 'photo123',
                'gallery_id': 'gallery123',
                'filename': 'wedding.jpg',
                's3_key': 'gallery123/photo123.jpg',
                'url': 'https://cdn.galerly.com/photo123.jpg'
            }
        }
        
        # Mock gallery exists and is public
        mock_galleries.scan.return_value = {
            'Items': [{
                'id': 'gallery123',
                'user_id': 'photo123',
                'name': 'Wedding Gallery',
                'privacy': 'public'
            }]
        }
        
        with patch('handlers.social_handler.os.environ.get', return_value='http://localhost:5173'):
            result = handle_get_photo_share_info(photo_id)
            assert result['statusCode'] == 200
    
    def test_get_photo_share_info_invalid_id(self):
        """Test validation rejects invalid photo ID"""
        photo_id = 'photo/../123'  # Path traversal attempt
        
        result = handle_get_photo_share_info(photo_id)
        assert result['statusCode'] == 400
    
    @patch('handlers.social_handler.photos_table')
    def test_get_photo_share_info_not_found(self, mock_photos):
        """Test error when photo not found"""
        photo_id = 'nonexistent'
        
        # Mock photo not found
        mock_photos.get_item.return_value = {}
        
        result = handle_get_photo_share_info(photo_id)
        assert result['statusCode'] == 404


class TestEmbedCodeGeneration:
    """Test embed code generation with configurable dimensions"""
    
    @patch('handlers.social_handler.os.environ.get')
    @patch('handlers.social_handler.galleries_table')
    def test_embed_code_uses_env_config(self, mock_galleries, mock_env):
        """Test embed iframe uses environment configuration"""
        gallery_id = 'gallery123'
        
        # Mock gallery with proper structure
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'user123',
                'name': 'Test Gallery',
                'share_token': 'token123',
                'privacy': 'public'
            }
        }
        
        # Mock environment variables
        mock_env.return_value = 'https://galerly.com'
        
        result = handle_get_gallery_share_info(gallery_id)
        
        import json
        body = json.loads(result['body'])
        embed_code = body['embed_code']
        
        # Verify iframe structure (default height is 600 from env)
        assert 'width="100%"' in embed_code
        assert 'height="600"' in embed_code
        assert 'frameborder="0"' in embed_code


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
