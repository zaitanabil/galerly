"""
Unit tests for engagement analytics handler
Tests photo/video engagement tracking and analytics generation
"""
import pytest
from unittest.mock import Mock, patch
from handlers.engagement_analytics_handler import (
    handle_track_visit,
    handle_get_overall_engagement
)


class TestVisitTracking:
    """Test gallery visit tracking"""
    
    @patch('handlers.engagement_analytics_handler.analytics_table')
    def test_track_visit_success(self, mock_analytics):
        """Test successful visit tracking"""
        body = {
            'gallery_id': 'gallery123',
            'event_time': '2025-01-01T12:00:00Z',
            'metadata': {
                'user_agent': 'Mozilla/5.0',
                'ip_address': '1.2.3.4',
                'referrer': 'https://google.com'
            }
        }
        
        mock_analytics.put_item.return_value = {}
        
        result = handle_track_visit(body)
        assert result['statusCode'] == 200
        assert mock_analytics.put_item.called
    
    def test_track_visit_missing_gallery_id(self):
        """Test validation requires gallery_id"""
        body = {'event_time': '2025-01-01T12:00:00Z'}
        
        result = handle_track_visit(body)
        assert result['statusCode'] == 400


class TestEngagementAnalytics:
    """Test engagement analytics retrieval"""
    
    @patch('handlers.engagement_analytics_handler.analytics_table')
    @patch('handlers.engagement_analytics_handler.galleries_table')
    @patch('handlers.engagement_analytics_handler.photos_table')
    def test_get_overall_engagement_success(self, mock_photos, mock_galleries, mock_analytics):
        """Test overall engagement analytics retrieval"""
        user = {'id': 'photo123', 'role': 'photographer'}
        
        # Mock galleries
        mock_galleries.query.return_value = {
            'Items': [
                {'id': 'g1', 'user_id': 'photo123', 'name': 'Gallery 1'},
                {'id': 'g2', 'user_id': 'photo123', 'name': 'Gallery 2'}
            ]
        }
        
        # Mock analytics events
        mock_analytics.query.return_value = {
            'Items': [
                {'id': 'e1', 'gallery_id': 'g1', 'event_type': 'view', 'timestamp': '2025-01-01T12:00:00Z'},
                {'id': 'e2', 'gallery_id': 'g1', 'event_type': 'download', 'timestamp': '2025-01-02T12:00:00Z'},
                {'id': 'e3', 'gallery_id': 'g2', 'event_type': 'view', 'timestamp': '2025-01-03T12:00:00Z'}
            ]
        }
        
        # Mock photos
        mock_photos.query.return_value = {'Items': []}
        
        result = handle_get_overall_engagement(user)
        assert result['statusCode'] == 200
        
        import json
        body = json.loads(result['body'])
        assert 'total_views' in body
        assert 'total_downloads' in body
        assert 'daily_stats' in body


class TestAnalyticsConfiguration:
    """Test analytics uses environment configuration"""
    
    @patch('handlers.engagement_analytics_handler.ANALYTICS_DEFAULT_DAYS', 7)
    @patch('handlers.engagement_analytics_handler.analytics_table')
    @patch('handlers.engagement_analytics_handler.galleries_table')
    @patch('handlers.engagement_analytics_handler.photos_table')
    def test_analytics_respects_configured_days(self, mock_photos, mock_galleries, mock_analytics):
        """Test analytics uses configured time range"""
        user = {'id': 'photo123', 'role': 'photographer'}
        
        # Mock galleries
        mock_galleries.query.return_value = {'Items': [{'id': 'g1', 'user_id': 'photo123'}]}
        
        # Mock analytics
        mock_analytics.query.return_value = {'Items': []}
        
        # Mock photos
        mock_photos.query.return_value = {'Items': []}
        
        result = handle_get_overall_engagement(user)
        assert result['statusCode'] == 200
        
        import json
        body = json.loads(result['body'])
        daily_stats = body.get('daily_stats', [])
        
        # Should have 7+1 days of data when ANALYTICS_DEFAULT_DAYS=7
        assert len(daily_stats) <= 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
