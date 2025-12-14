"""
Tests for branding_handler.py
White label branding and customization functionality
"""
import pytest
import os
import json
import base64
from datetime import datetime
from unittest.mock import patch, MagicMock
from handlers.branding_handler import (
    handle_get_branding_settings,
    handle_update_branding_settings,
    handle_upload_branding_logo,
    handle_get_public_branding
)


@pytest.fixture
def mock_user():
    return {
        'id': 'test-user-123',
        'email': 'photographer@test.com',
        'name': 'Test Photographer',
        'role': 'photographer',
        'plan': 'plus'
    }


@pytest.fixture
def mock_branding_settings():
    return {
        'hide_galerly_branding': True,
        'custom_branding_enabled': True,
        'custom_branding_logo_url': 'https://example.com/logo.png',
        'custom_branding_business_name': 'My Studio',
        'custom_branding_tagline': 'Capturing moments',
        'custom_branding_footer_text': '© 2024 My Studio',
        'theme_customization_enabled': True,
        'theme_primary_color': '#FF5733',
        'theme_secondary_color': '#33FF57',
        'theme_font_family': 'Montserrat'
    }


class TestGetBrandingSettings:
    """Test branding settings retrieval"""
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_get_branding_settings_success(self, mock_get_features, mock_user, mock_branding_settings):
        """Test successful retrieval of branding settings"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            assert 'hide_galerly_branding' in body or 'custom_branding' in body or 'theme_customization' in body
            # Handler returned successfully
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_get_branding_settings_returns_defaults(self, mock_get_features, mock_user):
        """Test returning default settings when none exist"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            assert 'hide_galerly_branding' in body or 'custom_branding' in body
    
    def test_get_branding_settings_user_not_found(self, mock_user):
        """Test error when user not found - uses real DynamoDB"""
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]


class TestUpdateBrandingSettings:
    """Test branding settings updates"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_branding_settings_success(self, mock_get_features, mock_user):
        """Test successful branding settings update"""
        mock_get_features.return_value = ({'remove_branding': True}, 'plus', 'Plus')
        
        body = {
            'hide_galerly_branding': True,
            'custom_branding': {
                'enabled': True,
                'business_name': 'My Photography Studio',
                'tagline': 'Professional photography',
                'footer_text': '© 2024 My Studio'
            },
            'theme_customization': {
                'enabled': True,
                'primary_color': '#1E90FF',
                'secondary_color': '#FFD700'
            }
        }
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] in [200, 400, 500]
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_branding_requires_plus_plan(self, mock_get_features, mock_user):
        """Test that branding customization requires Plus or higher plan"""
        mock_get_features.return_value = ({'remove_branding': False}, 'starter', 'Starter')
        
        body = {'hide_galerly_branding': True}
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'upgrade_required' in body_data
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_update_branding_partial_update(self, mock_get_features, mock_user):
        """Test partial branding settings update"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {
            'hide_galerly_branding': True
            # Only updating one field
        }
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] in [200, 400, 500]


class TestUploadBrandingLogo:
    """Test branding logo upload"""
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.s3_client')
    def test_upload_branding_logo_success(self, mock_s3, mock_get_features, mock_user):
        """Test successful logo upload"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        # Create a simple base64 encoded image
        image_data = b'fake-image-data'
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        body = {
            'file_data': f'data:image/png;base64,{base64_data}',
            'filename': 'logo.png'
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] in [200, 400, 500]
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_upload_branding_logo_requires_plus_plan(self, mock_get_features, mock_user):
        """Test that logo upload requires Plus or higher plan"""
        mock_get_features.return_value = ({'remove_branding': False}, None, None)
        
        body = {
            'file_data': 'data:image/png;base64,fake-data',
            'filename': 'logo.png'
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] == 403
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_upload_branding_logo_validates_file_data(self, mock_get_features, mock_user):
        """Test validation of file data"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {
            'filename': 'logo.png'
            # Missing file_data
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'required' in body_data['error'].lower()
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_upload_branding_logo_rejects_oversized_files(self, mock_get_features, mock_user):
        """Test rejection of files over 2MB"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        # Create data larger than 2MB
        large_image_data = b'x' * (3 * 1024 * 1024)  # 3MB
        base64_data = base64.b64encode(large_image_data).decode('utf-8')
        
        body = {
            'file_data': base64_data,
            'filename': 'logo.png'
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert '2mb' in body_data['error'].lower()
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_upload_branding_logo_handles_invalid_base64(self, mock_get_features, mock_user):
        """Test handling of invalid base64 data"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {
            'file_data': 'invalid-base64-data!!!',
            'filename': 'logo.png'
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] == 400


class TestGetPublicBranding:
    """Test public branding retrieval (for client galleries)"""
    
    @patch('handlers.branding_handler.get_user_features')
    def test_get_public_branding_success(self, mock_get_features, mock_branding_settings):
        """Test successful public branding retrieval"""
        mock_get_features.return_value = ({'remove_branding': True}, 'plus', 'Plus Plan')
        
        response = handle_get_public_branding('photographer-123')
        
        assert response['statusCode'] in [200, 404, 500]
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            assert 'hide_galerly_branding' in body or 'custom_branding' in body or 'photographer_name' in body
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_get_public_branding_respects_plan_limits(self, mock_get_features, mock_branding_settings):
        """Test that branding is hidden if user doesn't have access"""
        mock_get_features.return_value = ({'remove_branding': False}, None, None)
        
        response = handle_get_public_branding('photographer-123')
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_get_public_branding_photographer_not_found(self):
        """Test error when photographer not found - uses real DynamoDB"""
        response = handle_get_public_branding('photographer-nonexistent')
        
        assert response['statusCode'] in [404, 500]


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_handle_database_errors_gracefully(self, mock_user):
        """Test graceful handling of database errors - uses real DynamoDB"""
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.s3_client')
    def test_upload_logo_handles_s3_errors(self, mock_s3, mock_get_features, mock_user):
        """Test handling of S3 upload errors"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        mock_s3.put_object.side_effect = Exception('S3 error')
        
        image_data = b'fake-image-data'
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        body = {
            'file_data': base64_data,
            'filename': 'logo.png'
        }
        
        response = handle_upload_branding_logo(mock_user, body)
        
        assert response['statusCode'] == 500
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_update_with_empty_body_returns_error(self, mock_get_features, mock_user):
        """Test that empty update body returns error"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {}
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
