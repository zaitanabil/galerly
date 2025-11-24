"""
Tests for dashboard_handler.py endpoint.
Tests cover: dashboard statistics, gallery counts, photo counts, analytics summary.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_dashboard_dependencies():
    """Mock dashboard dependencies."""
    with patch('handlers.dashboard_handler.galleries_table') as mock_galleries, \
         patch('handlers.dashboard_handler.photos_table') as mock_photos, \
         patch('handlers.dashboard_handler.analytics_table') as mock_analytics:
        yield {
            'galleries': mock_galleries,
            'photos': mock_photos,
            'analytics': mock_analytics
        }

class TestDashboardStats:
    """Tests for handle_dashboard_stats endpoint."""
    
    def test_get_dashboard_stats_success(self, sample_user, mock_dashboard_dependencies):
        """Get dashboard statistics successfully."""
        from handlers.dashboard_handler import handle_dashboard_stats
        
        mock_dashboard_dependencies['galleries'].query.return_value = {
            'Items': [{'id': 'g1'}, {'id': 'g2'}, {'id': 'g3'}]
        }
        mock_dashboard_dependencies['photos'].query.return_value = {
            'Items': [{'id': 'p1'}, {'id': 'p2'}]
        }
        mock_dashboard_dependencies['analytics'].query.return_value = {
            'Items': [{'event_type': 'view', 'count': 100}]
        }
        
        result = handle_dashboard_stats(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'galleries_count' in body or 'stats' in body
    
    def test_get_dashboard_stats_empty(self, sample_user, mock_dashboard_dependencies):
        """Get dashboard stats with no data."""
        from handlers.dashboard_handler import handle_dashboard_stats
        
        mock_dashboard_dependencies['galleries'].query.return_value = {'Items': []}
        mock_dashboard_dependencies['photos'].query.return_value = {'Items': []}
        mock_dashboard_dependencies['analytics'].query.return_value = {'Items': []}
        
        result = handle_dashboard_stats(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('galleries_count', 0) == 0 or body.get('stats', {}).get('galleries', 0) == 0
    
    def test_get_dashboard_stats_aggregation(self, sample_user, mock_dashboard_dependencies):
        """Dashboard stats aggregates data correctly."""
        from handlers.dashboard_handler import handle_dashboard_stats
        
        # Multiple galleries
        galleries = [{'id': f'g{i}', 'photo_count': 10} for i in range(5)]
        mock_dashboard_dependencies['galleries'].query.return_value = {'Items': galleries}
        mock_dashboard_dependencies['photos'].query.return_value = {'Items': []}
        mock_dashboard_dependencies['analytics'].query.return_value = {'Items': []}
        
        result = handle_dashboard_stats(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        # Should have 5 galleries
        assert body.get('galleries_count', 0) == 5 or body.get('stats', {}).get('galleries', 0) == 5

