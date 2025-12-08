"""
Tests for engagement analytics handler
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from handlers.engagement_analytics_handler import (
    handle_track_visit,
    handle_track_event,
    handle_track_photo_engagement,
    handle_track_video_engagement,
    handle_get_gallery_engagement,
    handle_get_client_preferences
)


def test_track_visit():
    """Test tracking a gallery visit"""
    with patch('handlers.engagement_analytics_handler.analytics_table') as mock_table:
        mock_table.put_item = MagicMock()
        
        body = {
            'gallery_id': 'test-gallery',
            'path': '/client/gallery/test',
            'referrer': 'https://instagram.com',
            'screen_width': 1920,
            'screen_height': 1080
        }
        
        response = handle_track_visit(body)
        
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['success'] is True
        mock_table.put_item.assert_called_once()


def test_track_photo_engagement():
    """Test tracking photo engagement"""
    with patch('handlers.engagement_analytics_handler.analytics_table') as mock_table:
        mock_table.put_item = MagicMock()
        
        body = {
            'gallery_id': 'test-gallery',
            'photo_id': 'test-photo',
            'event_type': 'view',
            'duration': 5.5
        }
        
        response = handle_track_photo_engagement(body)
        
        assert response['statusCode'] == 200
        mock_table.put_item.assert_called_once()
        
        # Verify duration was converted to Decimal
        call_args = mock_table.put_item.call_args
        saved_event = call_args[1]['Item']
        assert isinstance(saved_event['duration'], Decimal)


def test_track_video_engagement():
    """Test tracking video engagement"""
    with patch('handlers.engagement_analytics_handler.analytics_table') as mock_table:
        mock_table.put_item = MagicMock()
        
        body = {
            'gallery_id': 'test-gallery',
            'photo_id': 'test-video',
            'event_type': 'play',
            'video_timestamp': 10.5,
            'session_duration': 15.3
        }
        
        response = handle_track_video_engagement(body)
        
        assert response['statusCode'] == 200
        mock_table.put_item.assert_called_once()


def test_get_gallery_engagement():
    """Test retrieving gallery engagement summary"""
    user = {'id': 'user123'}
    gallery_id = 'gallery123'
    
    with patch('handlers.engagement_analytics_handler.galleries_table') as mock_galleries, \
         patch('handlers.engagement_analytics_handler.photos_table') as mock_photos, \
         patch('handlers.engagement_analytics_handler.analytics_table') as mock_analytics:
        
        # Mock gallery exists
        mock_galleries.get_item.return_value = {
            'Item': {'id': gallery_id, 'user_id': 'user123', 'name': 'Test Gallery'}
        }
        
        # Mock photos in gallery
        mock_photos.query.return_value = {
            'Items': [
                {'id': 'photo1', 'filename': 'IMG_001.jpg', 'type': 'image', 'thumbnail_url': 'url1'},
                {'id': 'photo2', 'filename': 'VID_001.mov', 'type': 'video', 'thumbnail_url': 'url2'}
            ]
        }
        
        # Mock analytics events
        mock_analytics.query.return_value = {
            'Items': [
                {'id': '1', 'photo_id': 'photo1', 'event_type': 'photo_view', 'duration': Decimal('5')},
                {'id': '2', 'photo_id': 'photo1', 'event_type': 'photo_favorite', 'duration': Decimal('0')},
                {'id': '3', 'photo_id': 'photo2', 'event_type': 'video_play', 'duration': Decimal('10')}
            ]
        }
        
        response = handle_get_gallery_engagement(user, gallery_id)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert isinstance(data, list)
        assert len(data) == 2  # Two photos


def test_get_client_preferences():
    """Test analyzing client preferences"""
    user = {'id': 'user123'}
    gallery_id = 'gallery123'
    
    with patch('handlers.engagement_analytics_handler.galleries_table') as mock_galleries, \
         patch('handlers.engagement_analytics_handler.analytics_table') as mock_analytics, \
         patch('handlers.engagement_analytics_handler.photos_table') as mock_photos:
        
        # Mock gallery exists
        mock_galleries.get_item.return_value = {
            'Item': {'id': gallery_id, 'user_id': 'user123'}
        }
        
        # Mock analytics events
        mock_analytics.query.return_value = {
            'Items': [
                {'photo_id': 'photo1', 'event_type': 'photo_view', 'duration': Decimal('5')},
                {'photo_id': 'photo2', 'event_type': 'photo_view', 'duration': Decimal('15')},
                {'photo_id': 'photo1', 'event_type': 'photo_favorite', 'duration': Decimal('0')}
            ]
        }
        
        # Mock photo lookup for favorites
        mock_photos.get_item.return_value = {
            'Item': {'id': 'photo1', 'type': 'image'}
        }
        
        response = handle_get_client_preferences(user, gallery_id)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'engagement_pattern' in data
        assert 'decision_speed' in data
        assert 'avg_time_per_photo' in data
