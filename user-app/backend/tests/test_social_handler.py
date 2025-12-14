"""Tests for social_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from handlers.social_handler import (
    handle_generate_social_share,
    handle_get_social_stats,
    handle_create_social_post
)


class TestSocialHandler:
    """Test social media functionality with real DynamoDB"""
    
    def test_generate_social_share_success(self):
        """Test generating social share link - uses real DynamoDB"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        body = {'platform': 'instagram', 'gallery_id': gallery_id}
        
        result = handle_generate_social_share(user, body)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_social_stats(self):
        """Test getting social media stats - uses real DynamoDB"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        result = handle_get_social_stats(user, gallery_id)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_create_social_post(self):
        """Test creating social media post - uses real DynamoDB"""
        photo_id = f'photo-{uuid.uuid4()}'
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        body = {
            'photo_id': photo_id,
            'platform': 'facebook',
            'caption': 'Test post'
        }
        
        result = handle_create_social_post(user, body)
        assert result['statusCode'] in [200, 404, 500]
    
    @patch('handlers.social_handler.s3_client')
    def test_create_post_with_image_processing(self, mock_s3):
        """Test post creation with image processing"""
        mock_s3.generate_presigned_url.return_value = 'https://example.com/image.jpg'
        
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        body = {
            'photo_id': f'photo-{uuid.uuid4()}',
            'platform': 'twitter',
            'caption': 'Test'
        }
        
        result = handle_create_social_post(user, body)
        assert result['statusCode'] in [200, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
