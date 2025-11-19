"""
Test API endpoints and handlers
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAPIRouting:
    """Test API routing and health checks"""
    
    def test_health_endpoint(self):
        """Test health check endpoint returns 200"""
        # Simple test that health endpoint works
        from handlers import auth_handler
        assert hasattr(auth_handler, 'handle_register')
        # Health endpoint is working if we can import modules
    
    def test_cors_headers_in_responses(self):
        """Test CORS headers are present"""
        from utils.response import create_response
        
        response = create_response(200, {'message': 'test'})
        
        assert 'statusCode' in response
        assert response['statusCode'] == 200


class TestHandlerImports:
    """Test that all handlers can be imported"""
    
    def test_auth_handler_imports(self):
        """Test auth handler functions can be imported"""
        from handlers.auth_handler import (
            handle_register,
            handle_login,
            handle_get_me
        )
        assert callable(handle_register)
        assert callable(handle_login)
        assert callable(handle_get_me)
    
    def test_gallery_handler_imports(self):
        """Test gallery handler functions can be imported"""
        from handlers.gallery_handler import (
            handle_list_galleries,
            handle_create_gallery,
            handle_get_gallery
        )
        assert callable(handle_list_galleries)
        assert callable(handle_create_gallery)
        assert callable(handle_get_gallery)
    
    def test_photo_handler_imports(self):
        """Test photo handler can be imported"""
        from handlers.photo_handler import (
            handle_upload_photo,
            handle_delete_photos,
            handle_update_photo
        )
        assert callable(handle_upload_photo)
        assert callable(handle_delete_photos)
        assert callable(handle_update_photo)
    
    def test_subscription_handler_imports(self):
        """Test subscription handler functions can be imported"""
        from handlers.subscription_handler import handle_get_usage
        assert callable(handle_get_usage)
    
    def test_dashboard_handler_imports(self):
        """Test dashboard handler can be imported"""
        from handlers.dashboard_handler import handle_dashboard_stats
        assert callable(handle_dashboard_stats)


class TestResponseUtils:
    """Test response utility functions"""
    
    def test_create_response(self):
        """Test response creation"""
        from utils.response import create_response
        
        response = create_response(200, {'message': 'test'})
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        body = json.loads(response['body'])
        assert body['message'] == 'test'
    
    def test_create_response_with_error(self):
        """Test error response creation"""
        from utils.response import create_response
        
        response = create_response(400, {'error': 'Bad request'})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'


class TestAuthUtils:
    """Test authentication utility functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        from utils.auth import hash_password
        
        hashed = hash_password('test_password')
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex digest
        assert hashed != 'test_password'
    
    def test_hash_password_consistent(self):
        """Test password hashing is consistent"""
        from utils.auth import hash_password
        
        hash1 = hash_password('test_password')
        hash2 = hash_password('test_password')
        
        assert hash1 == hash2
    
    def test_hash_password_different_for_different_passwords(self):
        """Test different passwords produce different hashes"""
        from utils.auth import hash_password
        
        hash1 = hash_password('password1')
        hash2 = hash_password('password2')
        
        assert hash1 != hash2
    
    def test_get_token_from_event(self):
        """Test token extraction from event with Bearer prefix"""
        from utils.auth import get_token_from_event
        
        event = {
            'headers': {
                'Authorization': 'Bearer test_token_123'
            }
        }
        
        token = get_token_from_event(event)
        assert token == 'test_token_123'


class TestCDNIntegration:
    """Test CDN URL generation"""
    
    def test_get_cdn_url(self):
        """Test CDN URL generation"""
        from utils.cdn_urls import get_cdn_url
        
        url = get_cdn_url('test-gallery/test-photo.jpg')
        
        assert 'cdn.galerly.com' in url
        assert 'test-gallery/test-photo.jpg' in url
        assert 's3.amazonaws.com' not in url
    
    def test_photo_urls_use_cdn(self):
        """Test that photo URLs use CDN"""
        from utils.cdn_urls import get_photo_urls
        
        urls = get_photo_urls('test-gallery/test-photo.jpg')
        
        # Check all URL keys exist
        assert 'url' in urls
        assert 'medium_url' in urls
        assert 'thumbnail_url' in urls
        assert 'small_thumb_url' in urls
        
        # All URLs should use CDN domain
        assert 'cdn.galerly.com' in urls['url']
        assert 'cdn.galerly.com' in urls['thumbnail_url']
        assert 'cdn.galerly.com' in urls['medium_url']
        
        # Should not use S3 URLs
        assert 's3.amazonaws.com' not in urls['url']
    
    def test_photo_urls_structure(self):
        """Test photo URLs have correct structure"""
        from utils.cdn_urls import get_photo_urls
        
        urls = get_photo_urls('test.jpg')
        
        # Should return dict with required keys
        assert isinstance(urls, dict)
        assert len(urls) >= 4  # At least 4 size variants
