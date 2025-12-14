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
    @patch('handlers.branding_handler.users_table')
    def test_get_branding_settings_success(self, mock_table, mock_get_features, mock_user, mock_branding_settings):
        """Test successful retrieval of branding settings"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        user_data = {'email': mock_user['email']}
        user_data.update(mock_branding_settings)
        mock_table.get_item.return_value = {'Item': user_data}
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['hide_galerly_branding'] is True
        assert body['custom_branding']['enabled'] is True
        assert body['custom_branding']['business_name'] == 'My Studio'
        assert body['theme_customization']['primary_color'] == '#FF5733'
        assert body['has_access'] is True
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.users_table')
    def test_get_branding_settings_returns_defaults(self, mock_table, mock_get_features, mock_user):
        """Test returning default settings when none exist"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        mock_table.get_item.return_value = {'Item': {'email': mock_user['email']}}
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['hide_galerly_branding'] is False
        assert body['custom_branding']['enabled'] is False
        assert body['theme_customization']['primary_color'] == '#0066CC'
    
    @patch('handlers.branding_handler.users_table')
    def test_get_branding_settings_user_not_found(self, mock_table, mock_user):
        """Test error when user not found"""
        mock_table.get_item.return_value = {}
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] == 404


class TestUpdateBrandingSettings:
    """Test branding settings updates"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.branding_handler.users_table')
    def test_update_branding_settings_success(self, mock_table, mock_get_features, mock_user):
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
        
        assert response['statusCode'] == 200
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert 'hide_galerly_branding' in str(call_args)
    
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
    @patch('handlers.branding_handler.users_table')
    def test_update_branding_partial_update(self, mock_table, mock_get_features, mock_user):
        """Test partial branding settings update"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {
            'hide_galerly_branding': True
            # Only updating one field
        }
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] == 200
        mock_table.update_item.assert_called_once()


class TestUploadBrandingLogo:
    """Test branding logo upload"""
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.users_table')
    @patch('handlers.branding_handler.s3_client')
    def test_upload_branding_logo_success(self, mock_s3, mock_table, mock_get_features, mock_user):
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
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'url' in body_data
        assert 's3_key' in body_data
        assert 'branding-logos' in body_data['s3_key']
        mock_s3.put_object.assert_called_once()
        mock_table.update_item.assert_called_once()
    
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
    @patch('handlers.branding_handler.users_table')
    def test_get_public_branding_success(self, mock_table, mock_get_features, mock_branding_settings):
        """Test successful public branding retrieval"""
        mock_get_features.return_value = ({'remove_branding': True}, 'plus', 'Plus Plan')
        photographer_data = {
            'id': 'photographer-123',
            'name': 'Test Photographer',
            'email': 'photo@test.com',
            'role': 'photographer',
            'plan': 'plus'
        }
        photographer_data.update(mock_branding_settings)
        mock_table.query.return_value = {'Items': [photographer_data]}
        
        response = handle_get_public_branding('photographer-123')
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['hide_galerly_branding'] is True
        assert body['custom_branding']['enabled'] is True
        assert body['photographer_name'] == 'Test Photographer'
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.users_table')
    def test_get_public_branding_respects_plan_limits(self, mock_table, mock_get_features, mock_branding_settings):
        """Test that branding is hidden if user doesn't have access"""
        mock_get_features.return_value = ({'remove_branding': False}, None, None)
        photographer_data = {'id': 'photographer-123', 'name': 'Test Photographer'}
        photographer_data.update(mock_branding_settings)
        mock_table.query.return_value = {'Items': [photographer_data]}
        
        response = handle_get_public_branding('photographer-123')
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Even though settings say hide_galerly_branding is True,
        # it should be False because user doesn't have the feature
        assert body['hide_galerly_branding'] is False
        assert body['custom_branding']['enabled'] is False
    
    @patch('handlers.branding_handler.users_table')
    def test_get_public_branding_photographer_not_found(self, mock_table):
        """Test error when photographer not found"""
        mock_table.query.return_value = {'Items': []}
        
        response = handle_get_public_branding('photographer-123')
        
        assert response['statusCode'] == 404


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.branding_handler.users_table')
    def test_handle_database_errors_gracefully(self, mock_table, mock_user):
        """Test graceful handling of database errors"""
        mock_table.get_item.side_effect = Exception('Database error')
        
        response = handle_get_branding_settings(mock_user)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch("handlers.subscription_handler.get_user_features")
    @patch('handlers.branding_handler.users_table')
    @patch('handlers.branding_handler.s3_client')
    def test_upload_logo_handles_s3_errors(self, mock_s3, mock_table, mock_get_features, mock_user):
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
    @patch('handlers.branding_handler.users_table')
    def test_update_with_empty_body_returns_error(self, mock_table, mock_get_features, mock_user):
        """Test that empty update body returns error"""
        mock_get_features.return_value = ({'remove_branding': True}, None, None)
        
        body = {}
        
        response = handle_update_branding_settings(mock_user, body)
        
        assert response['statusCode'] == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
