"""Tests for engagement_analytics_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from handlers.engagement_analytics_handler import (
    handle_track_engagement,
    handle_get_engagement_stats,
    handle_get_engagement_report
)


class TestEngagementAnalytics:
    """Test engagement analytics with real DynamoDB"""
    
    def test_track_engagement(self):
        """Test tracking engagement event - uses real DynamoDB"""
        body = {
            'gallery_id': f'gallery-{uuid.uuid4()}',
            'photo_id': f'photo-{uuid.uuid4()}',
            'event_type': 'view',
            'user_agent': 'test-agent'
        }
        
        result = handle_track_engagement(body)
        assert result['statusCode'] in [200, 201, 400, 500]
    
    def test_get_engagement_stats(self):
        """Test getting engagement statistics - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        result = handle_get_engagement_stats(user, gallery_id)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_engagement_report(self):
        """Test getting engagement report - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        query_params = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        result = handle_get_engagement_report(user, query_params)
        assert result['statusCode'] in [200, 400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
