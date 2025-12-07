"""
Tests for analytics_handler.py endpoints.
Tests cover: track views, downloads, shares, get analytics.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_analytics_dependencies():
    """Mock analytics dependencies."""
    with patch('handlers.analytics_handler.analytics_table') as mock_analytics, \
         patch('handlers.analytics_handler.galleries_table') as mock_galleries:
        yield {
            'analytics': mock_analytics,
            'galleries': mock_galleries
        }

class TestTrackGalleryView:
    """Tests for gallery view tracking."""
    
    def test_track_view_success(self, sample_gallery, mock_analytics_dependencies):
        """Track gallery view successfully."""
        from handlers.analytics_handler import handle_track_gallery_view
        
        mock_analytics_dependencies['galleries'].get_item.return_value = {
            'Item': sample_gallery
        }
        
        result = handle_track_gallery_view('gallery_123', None, {})
        
        assert result['statusCode'] == 200
        mock_analytics_dependencies['analytics'].put_item.assert_called_once()
    
    def test_track_view_skip_owner(self, sample_user, sample_gallery, mock_analytics_dependencies):
        """Don't track view when owner views their own gallery."""
        from handlers.analytics_handler import handle_track_gallery_view
        
        # Handler uses scan to find gallery owner
        mock_analytics_dependencies['galleries'].scan.return_value = {
            'Items': [sample_gallery]
        }
        
        result = handle_track_gallery_view('gallery_123', sample_user['id'], {})
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['status'] == 'skipped'
        assert body['reason'] == 'owner_view'

class TestTrackPhotoView:
    """Tests for photo view tracking."""
    
    def test_track_photo_view(self, mock_analytics_dependencies):
        """Track photo view successfully."""
        from handlers.analytics_handler import handle_track_photo_view
        
        result = handle_track_photo_view('photo_123', 'gallery_123', None, {})
        
        assert result['statusCode'] == 200

class TestTrackDownload:
    """Tests for download tracking."""
    
    def test_track_download(self, mock_analytics_dependencies):
        """Track photo download successfully."""
        from handlers.analytics_handler import handle_track_photo_download
        
        result = handle_track_photo_download('photo_123', 'gallery_123', None, {})
        
        assert result['statusCode'] == 200

class TestGetAnalytics:
    """Tests for retrieving analytics data."""
    
    def test_get_gallery_analytics(self, sample_user, sample_gallery, mock_analytics_dependencies):
        """Get analytics for specific gallery."""
        from handlers.analytics_handler import handle_get_gallery_analytics
        
        mock_analytics_dependencies['galleries'].get_item.return_value = {
            'Item': sample_gallery
        }
        mock_analytics_dependencies['analytics'].query.return_value = {
            'Items': [{'event_type': 'view', 'timestamp': '2024-01-01'}]
        }
        
        result = handle_get_gallery_analytics(sample_user, 'gallery_123')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'metrics' in body
        assert 'period' in body
        assert 'gallery_id' in body

