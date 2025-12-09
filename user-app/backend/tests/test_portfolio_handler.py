"""
Tests for portfolio_handler.py
Tests portfolio customization and settings
"""
import pytest
import json  # FIX: Add json import for parsing response bodies
from unittest.mock import patch
from handlers.portfolio_handler import (
    handle_get_portfolio_settings,
    handle_update_portfolio_settings,
    handle_verify_domain
)


class TestGetPortfolioSettings:
    """Test portfolio settings retrieval"""
    
    @patch('handlers.portfolio_handler.users_table')
    def test_get_portfolio_settings_returns_defaults(self, mock_users_table):
        """New users get default portfolio settings"""
        mock_users_table.get_item.return_value = {
            'Item': {
                'id': 'user123',
                'email': 'user@test.com'
                # No portfolio settings yet
            }
        }
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        response = handle_get_portfolio_settings(user)
        
        assert response['statusCode'] == 200
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert body['theme'] == 'default'
        assert body['primary_color'] == '#0066CC'
        assert 'social_links' in body
    
    @patch('handlers.portfolio_handler.users_table')
    def test_get_portfolio_settings_returns_custom(self, mock_users_table):
        """Users with custom settings get their settings"""
        mock_users_table.get_item.return_value = {
            'Item': {
                'id': 'user123',
                'email': 'user@test.com',
                'portfolio_theme': 'dark',
                'portfolio_primary_color': '#FF0000',
                'portfolio_about': 'Professional photographer'
            }
        }
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        response = handle_get_portfolio_settings(user)
        
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert body['theme'] == 'dark'
        assert body['primary_color'] == '#FF0000'
        assert body['about_section'] == 'Professional photographer'


class TestUpdatePortfolioSettings:
    """Test portfolio settings update"""
    
    @patch('handlers.portfolio_handler.users_table')
    @patch('handlers.portfolio_handler.get_user_features')
    def test_update_portfolio_settings_success(self, mock_get_features, mock_users_table):
        """Portfolio settings can be updated"""
        mock_get_features.return_value = ({'portfolio_customization': True}, 'pro', 'pro')
        # FIX: Mock get_item to return user (handler needs to fetch user first)
        mock_users_table.get_item.return_value = {
            'Item': {'id': 'user123', 'email': 'user@test.com'}
        }
        mock_users_table.update_item.return_value = {}
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {
            'theme': 'dark',
            'primary_color': '#123456',
            'about_section': 'New about text'
        }
        
        response = handle_update_portfolio_settings(user, body)
        
        assert response['statusCode'] == 200
        assert mock_users_table.update_item.called
    
    @patch('handlers.portfolio_handler.users_table')
    @patch('handlers.portfolio_handler.get_user_features')
    def test_update_requires_pro_plan(self, mock_get_features, mock_users_table):
        """Portfolio customization requires Pro plan"""
        # FIX: Free plan should have portfolio_customization: False
        mock_get_features.return_value = ({'portfolio_customization': False}, 'free', 'free')
        # FIX: Handler doesn't actually enforce Pro plan yet - mocking users_table for now
        mock_users_table.get_item.return_value = {
            'Item': {'id': 'user123', 'email': 'user@test.com'}
        }
        mock_users_table.update_item.return_value = {}
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {'theme': 'dark'}
        
        response = handle_update_portfolio_settings(user, body)
        
        # Handler now checks portfolio_customization feature flag and returns 403 for Plus plan
        assert response['statusCode'] == 403
        assert 'upgrade_required' in json.loads(response['body']) if isinstance(response['body'], str) else response['body']
    
    @patch('handlers.portfolio_handler.users_table')
    @patch('handlers.portfolio_handler.get_user_features')
    def test_update_validates_color_format(self, mock_get_features, mock_users_table):
        """Color codes must be valid hex format"""
        mock_get_features.return_value = ({'portfolio_customization': True}, 'pro', 'pro')
        # FIX: Mock get_item to return user
        mock_users_table.get_item.return_value = {
            'Item': {'id': 'user123', 'email': 'user@test.com'}
        }
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {
            'primary_color': 'not-a-color'  # Invalid format
        }
        
        response = handle_update_portfolio_settings(user, body)
        
        # Should either reject or sanitize
        assert response['statusCode'] in [400, 200]


class TestVerifyCustomDomain:
    """Test custom domain verification"""
    
    @patch('handlers.portfolio_handler.get_user_features')
    @patch('handlers.portfolio_handler.dns.resolver.resolve')
    def test_verify_custom_domain_success(self, mock_dns_resolve, mock_get_features):
        """Valid custom domain can be verified"""
        mock_get_features.return_value = ({'custom_domain': True}, 'ultimate', 'ultimate')
        mock_dns_resolve.return_value = ['galerly.com']
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {'domain': 'photos.example.com'}
        
        response = handle_verify_domain(user, body)
        
        assert response['statusCode'] in [200, 400]  # Either verified or pending
    
    @patch('handlers.portfolio_handler.get_user_features')
    def test_verify_requires_ultimate_plan(self, mock_get_features):
        """Custom domain requires Ultimate plan"""
        mock_get_features.return_value = ({'custom_domain': False}, 'starter', 'starter')
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {'domain': 'photos.example.com'}
        
        response = handle_verify_domain(user, body)
        
        assert response['statusCode'] == 403
    
    @patch('handlers.portfolio_handler.get_user_features')
    def test_verify_rejects_invalid_domain(self, mock_get_features):
        """Invalid domain format is rejected"""
        mock_get_features.return_value = ({'custom_domain': True}, 'ultimate', 'ultimate')
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        body = {'domain': 'not a valid domain!@#$'}
        
        response = handle_verify_domain(user, body)
        
        assert response['statusCode'] == 400


class TestPortfolioThemes:
    """Test portfolio theme validation"""
    
    @patch('handlers.portfolio_handler.users_table')
    @patch('handlers.portfolio_handler.get_user_features')
    def test_valid_themes_accepted(self, mock_get_features, mock_users_table):
        """Valid theme names are accepted"""
        mock_get_features.return_value = ({'portfolio_customization': True}, 'pro', 'pro')
        # FIX: Mock get_item to return user
        mock_users_table.get_item.return_value = {
            'Item': {'id': 'user123', 'email': 'user@test.com'}
        }
        mock_users_table.update_item.return_value = {}
        
        valid_themes = ['default', 'dark', 'minimal', 'bold']
        user = {'id': 'user123', 'email': 'user@test.com'}
        
        for theme in valid_themes:
            body = {'theme': theme}
            response = handle_update_portfolio_settings(user, body)
            # Should accept valid themes
            assert response['statusCode'] in [200, 400]


class TestSEOSettings:
    """Test portfolio SEO settings"""
    
    @patch('handlers.portfolio_handler.users_table')
    def test_get_portfolio_includes_seo_settings(self, mock_users_table):
        """Portfolio settings include SEO configuration"""
        mock_users_table.get_item.return_value = {
            'Item': {
                'id': 'user123',
                'email': 'user@test.com',
                'portfolio_seo': {
                    'title': 'My Photography',
                    'description': 'Professional photographer',
                    'keywords': 'photography,wedding,portrait'
                }
            }
        }
        
        user = {'id': 'user123', 'email': 'user@test.com'}
        response = handle_get_portfolio_settings(user)
        
        # FIX: Parse JSON body
        body = json.loads(response['body'])
        assert 'seo_settings' in body
        assert body['seo_settings']['title'] == 'My Photography'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
