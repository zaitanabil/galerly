"""
Tests for Real-time Viewer Tracking
"""
import pytest
from handlers.realtime_viewers_handler import (
    handle_track_viewer_heartbeat,
    handle_get_active_viewers,
    handle_viewer_disconnect,
    active_viewers,
    cleanup_inactive_viewers
)
from utils.geolocation import get_location_from_ip, get_ip_from_request


def test_get_location_from_localhost():
    """Test that localhost returns default location"""
    location = get_location_from_ip('127.0.0.1')
    assert location['city'] == 'Local'
    assert location['country'] == 'Local'
    assert location['latitude'] == 0.0
    assert location['longitude'] == 0.0


def test_get_ip_from_request():
    """Test IP extraction from API Gateway event"""
    event = {
        'headers': {
            'X-Forwarded-For': '203.0.113.0, 198.51.100.0'
        }
    }
    ip = get_ip_from_request(event)
    assert ip == '203.0.113.0'  # Should get first IP from X-Forwarded-For


def test_track_viewer_heartbeat(monkeypatch):
    """Test viewer heartbeat tracking"""
    # Clear active viewers
    active_viewers.clear()
    
    event = {
        'body': {
            'gallery_id': 'test-gallery-123',
            'page_type': 'gallery',
            'gallery_name': 'Test Gallery'
        },
        'headers': {},
        'requestContext': {
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        }
    }
    
    # Mock get_user_from_token to return None (guest viewer)
    def mock_get_user(event):
        return None
    
    # Import api module and patch get_user_from_token there
    import api
    monkeypatch.setattr('api.get_user_from_token', mock_get_user)
    
    response = handle_track_viewer_heartbeat(event)
    assert response['statusCode'] == 200
    
    body = response['body']
    import json
    data = json.loads(body)
    assert data['tracked'] == True
    assert 'viewer_id' in data


def test_cleanup_inactive_viewers():
    """Test inactive viewer cleanup"""
    # Add some viewers
    import time
    active_viewers['old-viewer'] = {
        'viewer_id': 'old-viewer',
        'last_seen': time.time() - 120  # 2 minutes ago (inactive)
    }
    active_viewers['active-viewer'] = {
        'viewer_id': 'active-viewer',
        'last_seen': time.time()  # Just now (active)
    }
    
    removed = cleanup_inactive_viewers()
    assert removed == 1
    assert 'old-viewer' not in active_viewers
    assert 'active-viewer' in active_viewers
    
    # Cleanup
    active_viewers.clear()


def test_get_active_viewers_for_user():
    """Test getting active viewers for authenticated photographer"""
    from unittest.mock import patch
    import time
    
    active_viewers.clear()
    
    user = {'id': 'photographer-123'}
    
    # Add some viewers
    active_viewers['viewer-1'] = {
        'viewer_id': 'viewer-1',
        'gallery_id': 'gallery-1',
        'gallery_name': 'Test Gallery',
        'gallery_owner_id': 'photographer-123',
        'location': {
            'city': 'New York',
            'country': 'USA',
            'country_code': 'US',
            'latitude': 40.7128,
            'longitude': -74.0060
        },
        'first_seen': time.time() - 60,
        'last_seen': time.time()
    }
    
    # Mock user has Plus+ plan with advanced analytics
    with patch('handlers.realtime_viewers_handler.get_user_features') as mock_features:
        mock_features.return_value = ({'analytics_level': 'advanced'}, 'plus', None)
        
        response = handle_get_active_viewers(user)
        assert response['statusCode'] == 200
        
        body = response['body']
        import json
        data = json.loads(body)
        assert data['total_active'] == 1
        assert len(data['viewers']) == 1
        assert data['by_country']['US'] == 1
        
        # Cleanup
        active_viewers.clear()
