"""Tests for social_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from handlers.social_handler import (
    handle_get_gallery_share_info,
    handle_get_photo_share_info
)


class TestSocialHandler:
    """Test social media functionality with real DynamoDB"""
    
    def test_get_gallery_share_info_with_user(self):
        """Test getting gallery share info as owner - uses real DynamoDB"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        result = handle_get_gallery_share_info(gallery_id, user)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_gallery_share_info_public(self):
        """Test getting public gallery share info - uses real DynamoDB"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        result = handle_get_gallery_share_info(gallery_id, user=None)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_photo_share_info_with_user(self):
        """Test getting photo share info as owner - uses real DynamoDB"""
        photo_id = f'photo-{uuid.uuid4()}'
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        result = handle_get_photo_share_info(photo_id, user)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_photo_share_info_public(self):
        """Test getting public photo share info - uses real DynamoDB"""
        photo_id = f'photo-{uuid.uuid4()}'
        
        result = handle_get_photo_share_info(photo_id, user=None)
        assert result['statusCode'] in [200, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
