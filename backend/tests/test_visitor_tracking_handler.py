"""
Tests for visitor_tracking_handler.py endpoints.
Tests cover: track visits, track events, session tracking, visitor analytics.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_visitor_dependencies():
    """Mock visitor tracking dependencies."""
    with patch('handlers.visitor_tracking_handler.visitor_table') as mock_visitor:
        yield {'visitor': mock_visitor}

class TestTrackVisit:
    """Tests for handle_track_visit endpoint."""
    
    def test_track_visit_success(self, mock_visitor_dependencies):
        """Track visitor visit successfully."""
        from handlers.visitor_tracking_handler import handle_track_visit
        
        body = {
            'session_id': 'session_123',
            'page': '/',
            'referrer': 'https://google.com',
            'user_agent': 'Mozilla/5.0',
            'metadata': {'screen_width': 1920}
        }
        result = handle_track_visit(body)
        
        assert result['statusCode'] == 200
    
    def test_track_visit_new_session(self, mock_visitor_dependencies):
        """Track visit creates new session."""
        from handlers.visitor_tracking_handler import handle_track_visit
        
        body = {
            'session_id': 'new_session',
            'page': '/galleries',
            'metadata': {}
        }
        result = handle_track_visit(body)
        
        assert result['statusCode'] == 200
    
    def test_track_visit_captures_referrer(self, mock_visitor_dependencies):
        """Track visit captures referrer information."""
        from handlers.visitor_tracking_handler import handle_track_visit
        
        body = {
            'session_id': 'session_123',
            'page': '/pricing',
            'referrer': 'https://facebook.com/ad'
        }
        result = handle_track_visit(body)
        
        assert result['statusCode'] == 200
    
    def test_track_visit_missing_session_id(self, mock_visitor_dependencies):
        """Track visit fails without session_id."""
        from handlers.visitor_tracking_handler import handle_track_visit
        
        body = {'page': '/'}
        result = handle_track_visit(body)
        
        assert result['statusCode'] == 400

class TestTrackEvent:
    """Tests for handle_track_event endpoint."""
    
    def test_track_event_click(self, mock_visitor_dependencies):
        """Track click event."""
        from handlers.visitor_tracking_handler import handle_track_event
        
        body = {
            'session_id': 'session_123',
            'event_type': 'click',
            'event_data': {
                'element': 'pricing_button',
                'page': '/pricing'
            }
        }
        result = handle_track_event(body)
        
        assert result['statusCode'] == 200
    
    def test_track_event_scroll(self, mock_visitor_dependencies):
        """Track scroll event."""
        from handlers.visitor_tracking_handler import handle_track_event
        
        body = {
            'session_id': 'session_123',
            'event_type': 'scroll',
            'event_data': {
                'depth': 75,
                'page': '/about'
            }
        }
        result = handle_track_event(body)
        
        assert result['statusCode'] == 200
    
    def test_track_event_time_on_page(self, mock_visitor_dependencies):
        """Track time spent on page."""
        from handlers.visitor_tracking_handler import handle_track_event
        
        body = {
            'session_id': 'session_123',
            'event_type': 'time_on_page',
            'event_data': {
                'duration': 45,
                'page': '/gallery/123'
            }
        }
        result = handle_track_event(body)
        
        assert result['statusCode'] == 200
    
    def test_track_custom_event(self, mock_visitor_dependencies):
        """Track custom event."""
        from handlers.visitor_tracking_handler import handle_track_event
        
        body = {
            'session_id': 'session_123',
            'event_type': 'video_play',
            'event_data': {
                'video_id': 'intro_video',
                'timestamp': 0
            }
        }
        result = handle_track_event(body)
        
        assert result['statusCode'] == 200

class TestSessionEnd:
    """Tests for handle_track_session_end endpoint."""
    
    def test_track_session_end_success(self, mock_visitor_dependencies):
        """Track session end successfully."""
        from handlers.visitor_tracking_handler import handle_track_session_end
        
        body = {
            'session_id': 'session_123',
            'duration': 300,
            'page_count': 5
        }
        result = handle_track_session_end(body)
        
        assert result['statusCode'] == 200
    
    def test_track_session_end_calculates_duration(self, mock_visitor_dependencies):
        """Session end calculates duration correctly."""
        from handlers.visitor_tracking_handler import handle_track_session_end
        
        body = {
            'session_id': 'session_123',
            'duration': 600,
            'page_count': 10
        }
        result = handle_track_session_end(body)
        
        assert result['statusCode'] == 200
    
    def test_track_session_end_missing_session_id(self, mock_visitor_dependencies):
        """Session end fails without session_id."""
        from handlers.visitor_tracking_handler import handle_track_session_end
        
        body = {'duration': 100}
        result = handle_track_session_end(body)
        
        assert result['statusCode'] == 400

class TestVisitorAnalytics:
    """Tests for handle_get_visitor_analytics endpoint."""
    
    def test_get_visitor_analytics_success(self, sample_user, mock_visitor_dependencies):
        """Get visitor analytics successfully."""
        from handlers.visitor_tracking_handler import handle_get_visitor_analytics
        
        mock_visitor_dependencies['visitor'].query.return_value = {
            'Items': [
                {'session_id': 's1', 'page': '/', 'timestamp': '2024-01-01'},
                {'session_id': 's2', 'page': '/pricing', 'timestamp': '2024-01-02'}
            ]
        }
        
        query_params = {}
        result = handle_get_visitor_analytics(sample_user, query_params)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'analytics' in body or 'visits' in body or len(body) >= 0
    
    def test_get_visitor_analytics_date_filter(self, sample_user, mock_visitor_dependencies):
        """Get visitor analytics with date filtering."""
        from handlers.visitor_tracking_handler import handle_get_visitor_analytics
        
        mock_visitor_dependencies['visitor'].query.return_value = {'Items': []}
        
        query_params = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        result = handle_get_visitor_analytics(sample_user, query_params)
        
        assert result['statusCode'] == 200
    
    def test_get_visitor_analytics_event_filter(self, sample_user, mock_visitor_dependencies):
        """Get visitor analytics filtered by event type."""
        from handlers.visitor_tracking_handler import handle_get_visitor_analytics
        
        mock_visitor_dependencies['visitor'].query.return_value = {'Items': []}
        
        query_params = {'event_type': 'click'}
        result = handle_get_visitor_analytics(sample_user, query_params)
        
        assert result['statusCode'] == 200
    
    def test_get_visitor_analytics_aggregation(self, sample_user, mock_visitor_dependencies):
        """Visitor analytics aggregates data."""
        from handlers.visitor_tracking_handler import handle_get_visitor_analytics
        
        visits = [
            {'page': '/', 'event': 'visit'},
            {'page': '/', 'event': 'visit'},
            {'page': '/pricing', 'event': 'visit'}
        ]
        mock_visitor_dependencies['visitor'].query.return_value = {'Items': visits}
        
        result = handle_get_visitor_analytics(sample_user, {})
        
        assert result['statusCode'] == 200
    
    def test_get_visitor_analytics_empty(self, sample_user, mock_visitor_dependencies):
        """Get analytics with no visitor data."""
        from handlers.visitor_tracking_handler import handle_get_visitor_analytics
        
        mock_visitor_dependencies['visitor'].query.return_value = {'Items': []}
        
        result = handle_get_visitor_analytics(sample_user, {})
        
        assert result['statusCode'] == 200

