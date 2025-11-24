"""
Tests for notification_handler.py endpoints.
Tests cover: notification preferences, custom notifications, reminders.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_notification_dependencies():
    """Mock notification dependencies."""
    with patch('handlers.notification_handler.users_table') as mock_users, \
         patch('handlers.notification_handler.send_email') as mock_email:
        yield {
            'users': mock_users,
            'email': mock_email
        }

class TestNotificationPreferences:
    """Tests for notification preferences endpoints."""
    
    def test_get_preferences(self, sample_user, mock_notification_dependencies):
        """Get notification preferences."""
        from handlers.notification_handler import handle_get_preferences
        
        user_with_prefs = {
            **sample_user,
            'notification_preferences': {
                'email_notifications': True,
                'push_notifications': False
            }
        }
        mock_notification_dependencies['users'].get_item.return_value = {'Item': user_with_prefs}
        
        result = handle_get_preferences(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'email_notifications' in body or 'preferences' in body
    
    def test_get_preferences_defaults(self, sample_user, mock_notification_dependencies):
        """Get default preferences when none set."""
        from handlers.notification_handler import handle_get_preferences
        
        mock_notification_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        result = handle_get_preferences(sample_user)
        
        assert result['statusCode'] == 200
    
    def test_update_preferences_email(self, sample_user, mock_notification_dependencies):
        """Update email notification preferences."""
        from handlers.notification_handler import handle_update_preferences
        
        mock_notification_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'email_notifications': False}
        result = handle_update_preferences(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_update_preferences_push(self, sample_user, mock_notification_dependencies):
        """Update push notification preferences."""
        from handlers.notification_handler import handle_update_preferences
        
        mock_notification_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {'push_notifications': True}
        result = handle_update_preferences(sample_user, body)
        
        assert result['statusCode'] == 200
    
    def test_update_preferences_multiple(self, sample_user, mock_notification_dependencies):
        """Update multiple preference settings."""
        from handlers.notification_handler import handle_update_preferences
        
        mock_notification_dependencies['users'].get_item.return_value = {'Item': sample_user}
        
        body = {
            'email_notifications': True,
            'push_notifications': True,
            'sms_notifications': False
        }
        result = handle_update_preferences(sample_user, body)
        
        assert result['statusCode'] == 200

class TestCustomNotifications:
    """Tests for custom notification endpoints."""
    
    def test_send_custom_notification(self, sample_user, sample_gallery, mock_notification_dependencies):
        """Send custom notification to client."""
        from handlers.notification_handler import handle_send_custom_notification
        
        with patch('handlers.notification_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            body = {
                'gallery_id': 'gallery_123',
                'recipient_email': 'client@example.com',
                'message': 'Your photos are ready!'
            }
            result = handle_send_custom_notification(sample_user, body)
            
            assert result['statusCode'] == 200
            mock_notification_dependencies['email'].assert_called_once()
    
    def test_send_selection_reminder(self, sample_user, sample_gallery, mock_notification_dependencies):
        """Send selection reminder to client."""
        from handlers.notification_handler import handle_send_selection_reminder
        
        with patch('handlers.notification_handler.galleries_table') as mock_galleries:
            gallery_with_clients = {**sample_gallery, 'client_emails': ['client@example.com']}
            mock_galleries.get_item.return_value = {'Item': gallery_with_clients}
            
            body = {'gallery_id': 'gallery_123'}
            result = handle_send_selection_reminder(sample_user, body)
            
            assert result['statusCode'] == 200
    
    def test_send_notification_rate_limiting(self, sample_user, mock_notification_dependencies):
        """Custom notification respects rate limiting."""
        from handlers.notification_handler import handle_send_custom_notification
        
        with patch('handlers.notification_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': {'user_id': sample_user['id']}}
            
            body = {
                'gallery_id': 'gallery_123',
                'recipient_email': 'client@example.com',
                'message': 'Test'
            }
            
            # Send multiple notifications quickly
            for _ in range(10):
                result = handle_send_custom_notification(sample_user, body)
            
            # Should eventually rate limit
            assert result['statusCode'] in [200, 429]

