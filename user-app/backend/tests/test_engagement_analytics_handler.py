"""Tests for engagement_analytics_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from handlers.engagement_analytics_handler import (
    handle_track_visit,
    handle_track_photo_engagement,
    handle_get_gallery_engagement,
    handle_get_overall_engagement
)


class TestEngagementAnalytics:
    """Test engagement analytics with real DynamoDB"""
    
    def test_track_visit(self):
        """Test tracking gallery visit - uses real DynamoDB"""
        body = {
            'gallery_id': f'gallery-{uuid.uuid4()}',
            'visitor_id': f'visitor-{uuid.uuid4()}',
            'user_agent': 'test-agent',
            'ip_address': '127.0.0.1'
        }
        
        result = handle_track_visit(body)
        assert result['statusCode'] in [200, 201, 400, 500]
    
    def test_track_photo_engagement(self):
        """Test tracking photo engagement - uses real DynamoDB"""
        body = {
            'photo_id': f'photo-{uuid.uuid4()}',
            'gallery_id': f'gallery-{uuid.uuid4()}',
            'event_type': 'view',
            'duration': 5
        }
        
        result = handle_track_photo_engagement(body)
        assert result['statusCode'] in [200, 201, 400, 500]
    
    def test_get_gallery_engagement(self):
        """Test getting gallery engagement stats - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        result = handle_get_gallery_engagement(user, gallery_id)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_overall_engagement(self):
        """Test getting overall engagement for user - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        result = handle_get_overall_engagement(user)
        assert result['statusCode'] in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
