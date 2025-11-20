"""
Test handler imports
Ensures all handlers can be imported without errors
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestHandlerImports:
    """Test that all handler modules can be imported"""
    
    def test_auth_handler_import(self):
        """Test auth_handler imports successfully"""
        from handlers import auth_handler
        assert hasattr(auth_handler, 'handle_register')
        assert hasattr(auth_handler, 'handle_login')
        assert hasattr(auth_handler, 'handle_logout')
    
    def test_gallery_handler_import(self):
        """Test gallery_handler imports successfully"""
        from handlers import gallery_handler
        assert hasattr(gallery_handler, 'handle_create_gallery')
        assert hasattr(gallery_handler, 'handle_list_galleries')
        assert hasattr(gallery_handler, 'handle_get_gallery')
        assert hasattr(gallery_handler, 'handle_update_gallery')
        assert hasattr(gallery_handler, 'handle_delete_gallery')
    
    def test_photo_handler_import(self):
        """Test photo_handler imports successfully"""
        from handlers import photo_handler
        assert hasattr(photo_handler, 'handle_upload_photo')
        assert hasattr(photo_handler, 'handle_delete_photos')
        assert hasattr(photo_handler, 'handle_send_batch_notification')
    
    def test_billing_handler_import(self):
        """Test billing_handler imports successfully"""
        from handlers import billing_handler
        assert hasattr(billing_handler, 'handle_create_checkout_session')
        assert hasattr(billing_handler, 'handle_stripe_webhook')
        assert hasattr(billing_handler, 'handle_get_subscription')
    
    def test_dashboard_handler_import(self):
        """Test dashboard_handler imports successfully"""
        from handlers import dashboard_handler
        assert hasattr(dashboard_handler, 'handle_dashboard_stats')
    
    def test_notification_handler_import(self):
        """Test notification_handler imports successfully"""
        from handlers import notification_handler
        assert hasattr(notification_handler, 'handle_get_preferences')
        assert hasattr(notification_handler, 'handle_update_preferences')
    
    def test_social_handler_import(self):
        """Test social_handler imports successfully"""
        from handlers import social_handler
        assert hasattr(social_handler, 'handle_get_gallery_share_info')
        assert hasattr(social_handler, 'handle_get_photo_share_info')
    
    def test_visitor_tracking_handler_import(self):
        """Test visitor_tracking_handler imports successfully"""
        from handlers import visitor_tracking_handler
        assert hasattr(visitor_tracking_handler, 'handle_track_visit')
        assert hasattr(visitor_tracking_handler, 'handle_track_event')


class TestUtilImports:
    """Test that all utility modules can be imported"""
    
    def test_auth_util_import(self):
        """Test auth utility imports successfully"""
        from utils import auth
        assert hasattr(auth, 'get_user_from_token')
        assert hasattr(auth, 'get_session')
    
    def test_email_util_import(self):
        """Test email utility imports successfully"""
        from utils import email
        assert hasattr(email, 'send_email')
    
    def test_response_util_import(self):
        """Test response utility imports successfully"""
        from utils import response
        assert hasattr(response, 'create_response')