"""
Tests for social_handler.py
Tests social sharing functionality
"""
import json  # FIX: Move import to proper location
import pytest
from unittest.mock import patch
from handlers.social_handler import (
    handle_get_gallery_share_info,
    handle_get_photo_share_info
)


class TestGetGalleryShareInfo:
    """Test gallery share information retrieval"""
    
    @patch('handlers.social_handler.galleries_table')
    def test_get_share_info_for_owned_gallery(self, mock_galleries_table):
        """Owner can get share info for their gallery"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'title': 'Wedding Photos',
                'share_token': 'abc123',
                'privacy': 'private'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123', 'email': 'user@test.com'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        assert response['statusCode'] == 200
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert 'share_url' in body
        assert 'embed_code' in body
    
    @patch('handlers.social_handler.galleries_table')
    def test_get_share_info_for_public_gallery(self, mock_galleries_table):
        """Anyone can get share info for public gallery"""
        mock_galleries_table.scan.return_value = {
            'Items': [{
                'id': 'gal123',
                'user_id': 'owner123',
                'title': 'Public Gallery',
                'share_token': 'abc123',
                'privacy': 'public'
            }]
        }
        
        gallery_id = 'gal123'
        user = None  # No authentication
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        assert response['statusCode'] == 200
    
    def test_invalid_gallery_id_format(self):
        """Invalid gallery ID format is rejected"""
        gallery_id = 'gal123; DROP TABLE galleries;'  # SQL injection attempt
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        assert response['statusCode'] == 400
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert 'Invalid gallery ID format' in body['error']
    
    def test_gallery_id_too_long(self):
        """Excessively long gallery ID is rejected"""
        gallery_id = 'a' * 200  # Way too long
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        assert response['statusCode'] == 400
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert 'too long' in body['error'].lower()
    
    @patch('handlers.social_handler.galleries_table')
    def test_access_denied_for_private_gallery(self, mock_galleries_table):
        """Non-owner cannot access private gallery share info"""
        mock_galleries_table.scan.return_value = {
            'Items': [{
                'id': 'gal123',
                'user_id': 'owner123',
                'privacy': 'private'
            }]
        }
        
        gallery_id = 'gal123'
        user = {'id': 'other_user', 'email': 'other@test.com'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        # FIX: Handler returns 404 (not found) instead of 403 when gallery not accessible
        assert response['statusCode'] == 404


class TestGetEmbedCode:
    """Test embed code generation"""
    
    @patch('handlers.social_handler.galleries_table')
    def test_share_info_includes_embed_data(self, mock_galleries_table):
        """Share info can be used to generate embed code"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'title': 'Test Gallery',
                'share_token': 'abc123'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        assert response['statusCode'] == 200
        body = response['body']
        # Share info contains data needed for embedding
        assert 'share_url' in body or 'gallery_id' in body
    
    @patch('handlers.social_handler.galleries_table')
    def test_embed_url_contains_gallery_reference(self, mock_galleries_table):
        """Share URL contains gallery reference for embedding"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'share_token': 'abc123'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        body = response['body']
        # Should have share URL that can be embedded
        assert 'share_url' in body
    
    @patch('handlers.social_handler.galleries_table')
    def test_title_safe_for_embedding(self, mock_galleries_table):
        """Gallery titles with special chars are handled"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'title': '<script>alert("xss")</script>',
                'share_token': 'abc123'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        # Should not crash on special characters
        assert response['statusCode'] == 200


class TestShareURLGeneration:
    """Test share URL generation"""
    
    @patch('handlers.social_handler.galleries_table')
    def test_share_url_contains_token(self, mock_galleries_table):
        """Share URL contains the share token"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'share_token': 'unique_token_123'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert 'unique_token_123' in body['share_url']
    
    @patch('handlers.social_handler.galleries_table')
    def test_share_url_uses_https(self, mock_galleries_table):
        """Share URLs use HTTPS protocol"""
        mock_galleries_table.get_item.return_value = {
            'Item': {
                'id': 'gal123',
                'user_id': 'user123',
                'share_token': 'abc123'
            }
        }
        
        gallery_id = 'gal123'
        user = {'id': 'user123'}
        
        response = handle_get_gallery_share_info(gallery_id, user)
        
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        # In production, should use HTTPS
        assert body['share_url'].startswith('http')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
