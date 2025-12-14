"""
Unit tests for realtime viewers handler
Tests live viewer tracking and location data
"""
import pytest
from unittest.mock import Mock, patch
from handlers.realtime_viewers_handler import (
    handle_track_viewer_heartbeat,  # Fixed: correct function name
    handle_get_active_viewers
)


class TestViewerTracking:
    """Test real-time viewer tracking"""
    
    @patch('handlers.realtime_viewers_handler.get_location_from_ip')
    @patch('handlers.realtime_viewers_handler.get_ip_from_request')
    @patch('handlers.realtime_viewers_handler.galleries_table')
    def test_track_viewer_creates_entry(self, mock_galleries, mock_get_ip, mock_get_location):
        """Test viewer tracking creates entry with location"""
        gallery_id = 'gallery123'
        event = {'headers': {'X-Forwarded-For': '1.2.3.4'}}
        
        # Mock gallery exists
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'photo123',
                'name': 'Test Gallery'
            }
        }
        
        # Mock IP and location
        mock_get_ip.return_value = '1.2.3.4'
        mock_get_location.return_value = {
            'city': 'San Francisco',
            'country': 'United States',
            'lat': 37.7749,
            'lng': -122.4194
        }
        
        result = handle_track_viewer(gallery_id, event)
        assert result['statusCode'] == 200
    
    @patch('handlers.realtime_viewers_handler.galleries_table')
    def test_track_viewer_validates_gallery(self, mock_galleries):
        """Test tracking validates gallery exists"""
        gallery_id = 'nonexistent'
        event = {'headers': {}}
        
        # Mock gallery not found
        mock_galleries.get_item.return_value = {}
        
        result = handle_track_viewer(gallery_id, event)
        assert result['statusCode'] == 404


class TestActiveViewersRetrieval:
    """Test active viewers retrieval"""
    
    @patch('handlers.realtime_viewers_handler.active_viewers')
    @patch('handlers.realtime_viewers_handler.get_user_features')
    @patch('handlers.realtime_viewers_handler.galleries_table')
    def test_get_active_viewers_photographer_access(self, mock_galleries, mock_features, mock_active):
        """Test photographer can see active viewers on their gallery"""
        gallery_id = 'gallery123'
        user = {'id': 'photo123', 'role': 'photographer'}
        
        # Mock Plus plan with realtime viewers feature
        mock_features.return_value = ({'realtime_viewers': True}, {}, 'plus')
        
        # Mock gallery ownership
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'photo123'
            }
        }
        
        # Mock active viewers
        mock_active.__iter__.return_value = iter({})
        
        result = handle_get_active_viewers(gallery_id, user)
        assert result['statusCode'] == 200
    
    @patch('handlers.realtime_viewers_handler.galleries_table')
    def test_get_active_viewers_blocks_non_owner(self, mock_galleries):
        """Test non-owner cannot see active viewers"""
        gallery_id = 'gallery123'
        user = {'id': 'photo456', 'role': 'photographer'}
        
        # Mock gallery owned by different photographer
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'photo123'  # Different owner
            }
        }
        
        with patch('handlers.realtime_viewers_handler.get_user_features') as mock_features:
            mock_features.return_value = ({'realtime_viewers': True}, {}, 'plus')
            result = handle_get_active_viewers(gallery_id, user)
            assert result['statusCode'] == 403


class TestViewerCleanup:
    """Test inactive viewer cleanup"""
    
    @patch('handlers.realtime_viewers_handler.time')
    @patch('handlers.realtime_viewers_handler.active_viewers')
    def test_cleanup_removes_inactive_viewers(self, mock_active, mock_time):
        """Test cleanup removes viewers past timeout"""
        current_time = 1000
        mock_time.time.return_value = current_time
        
        # Mock viewers with different last_seen times
        mock_active.__iter__.return_value = iter(['viewer1', 'viewer2'])
        mock_active.items.return_value = [
            ('viewer1', {'last_seen': current_time - 30}),  # Active (within 60s)
            ('viewer2', {'last_seen': current_time - 90})   # Inactive (> 60s)
        ]
        mock_active.__delitem__ = Mock()
        
        cleanup_inactive_viewers()
        # Viewer2 should be removed
        mock_active.__delitem__.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
