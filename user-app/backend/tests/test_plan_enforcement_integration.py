"""
Integration tests for plan enforcement decorators
Tests that decorators properly gate access to premium features
"""
import pytest
import json
from unittest.mock import Mock, patch
from utils.plan_enforcement import require_plan, require_role, check_plan_feature


class TestPlanEnforcementDecorators:
    """Test plan enforcement decorator functionality"""
    
    def test_require_plan_allows_access_with_correct_plan(self):
        """Test that @require_plan allows access when user has the feature"""
        # Mock user with Pro plan having client_invoicing feature
        user = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        # Mock function that requires client_invoicing
        @require_plan(feature='client_invoicing')
        def protected_function(user):
            return {'success': True, 'data': 'access granted'}
        
        # Mock get_user_features to return that user has the feature
        with patch('utils.plan_enforcement.get_user_features') as mock_features:
            mock_features.return_value = (
                {'client_invoicing': True},  # features
                {},  # limits
                'pro'  # plan
            )
            
            result = protected_function(user)
            assert result['success'] is True
            assert result['data'] == 'access granted'
    
    def test_require_plan_blocks_access_without_feature(self):
        """Test that @require_plan blocks access when user lacks the feature"""
        user = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'free'
        }
        
        @require_plan(feature='client_invoicing')
        def protected_function(user):
            return {'success': True}
        
        with patch('utils.plan_enforcement.get_user_features') as mock_features:
            mock_features.return_value = (
                {'client_invoicing': False},  # features
                {},  # limits
                'free'  # plan
            )
            
            result = protected_function(user)
            assert result['statusCode'] == 403
            body = json.loads(result['body'])
            assert 'upgrade_required' in body
    
    def test_require_role_allows_correct_role(self):
        """Test that @require_role allows access for correct role"""
        user = {
            'id': 'user123',
            'role': 'photographer'
        }
        
        @require_role('photographer')
        def photographer_only_function(user):
            return {'success': True, 'message': 'photographer access'}
        
        result = photographer_only_function(user)
        assert result['success'] is True
        assert result['message'] == 'photographer access'
    
    def test_require_role_blocks_wrong_role(self):
        """Test that @require_role blocks access for wrong role"""
        user = {
            'id': 'user123',
            'role': 'client'
        }
        
        @require_role('photographer')
        def photographer_only_function(user):
            return {'success': True}
        
        result = photographer_only_function(user)
        assert result['statusCode'] == 403
        body = json.loads(result['body'])
        assert 'Photographers only' in body['error']
    
    def test_require_role_allows_multiple_roles(self):
        """Test that @require_role allows any of multiple specified roles"""
        photographer_user = {'id': 'user1', 'role': 'photographer'}
        client_user = {'id': 'user2', 'role': 'client'}
        admin_user = {'id': 'user3', 'role': 'admin'}
        
        @require_role('photographer', 'client')
        def multi_role_function(user):
            return {'success': True, 'role': user['role']}
        
        # Photographer should pass
        result1 = multi_role_function(photographer_user)
        assert result1['success'] is True
        
        # Client should pass
        result2 = multi_role_function(client_user)
        assert result2['success'] is True
        
        # Admin should be blocked
        result3 = multi_role_function(admin_user)
        assert result3['statusCode'] == 403
    
    def test_stacked_decorators_both_checks(self):
        """Test that stacked decorators apply both plan and role checks"""
        user = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        @require_plan(feature='client_invoicing')
        @require_role('photographer')
        def protected_function(user):
            return {'success': True}
        
        with patch('utils.plan_enforcement.get_user_features') as mock_features:
            # Test with correct role but wrong plan
            mock_features.return_value = (
                {'client_invoicing': False},
                {},
                'free'
            )
            
            result = protected_function(user)
            assert result['statusCode'] == 403
            
            # Test with correct plan and role
            mock_features.return_value = (
                {'client_invoicing': True},
                {},
                'pro'
            )
            
            result = protected_function(user)
            assert result['success'] is True


class TestHandlerIntegration:
    """Integration tests for specific handlers with decorators"""
    
    def test_invoice_handler_requires_pro_plan(self):
        """Test that invoice operations require Pro+ plan"""
        from handlers.invoice_handler import handle_create_invoice
        
        user_free = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'free'
        }
        
        body = {
            'client_name': 'Test Client',
            'amount': 1000,
            'items': [{'description': 'Service', 'quantity': 1, 'price': 1000}]
        }
        
        with patch('handlers.invoice_handler.get_user_features') as mock_features:
            mock_features.return_value = (
                {'client_invoicing': False},
                {},
                'free'
            )
            
            result = handle_create_invoice(user_free, body)
            assert result['statusCode'] == 403
    
    def test_raw_vault_requires_ultimate_plan(self):
        """Test that RAW vault operations require Ultimate plan"""
        from handlers.raw_vault_handler import handle_archive_raw_file
        
        user_pro = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        body = {
            'photo_id': 'photo123',
            'filename': 'photo.raw'
        }
        
        with patch('handlers.raw_vault_handler.get_user_features') as mock_features:
            mock_features.return_value = (
                {'raw_vault': False},  # Pro plan doesn't have raw_vault
                {},
                'pro'
            )
            
            result = handle_archive_raw_file(user_pro, body)
            assert result['statusCode'] == 403
    
    def test_email_templates_requires_pro_plan(self):
        """Test that custom email templates require Pro+ plan"""
        from handlers.email_template_handler import handle_create_template
        
        user_starter = {
            'id': 'user123',
            'role': 'photographer',
            'plan': 'starter'
        }
        
        body = {
            'name': 'Welcome Email',
            'subject': 'Welcome!',
            'body': 'Hi {client_name}'
        }
        
        with patch('handlers.email_template_handler.get_user_features') as mock_features:
            mock_features.return_value = (
                {'custom_email_templates': False},
                {},
                'starter'
            )
            
            result = handle_create_template(user_starter, body)
            assert result['statusCode'] == 403
    
    def test_photographer_role_required_for_gallery_create(self):
        """Test that only photographers can create galleries"""
        from handlers.gallery_handler import handle_create_gallery
        
        client_user = {
            'id': 'user123',
            'role': 'client'  # Clients should not create galleries
        }
        
        body = {
            'name': 'Test Gallery',
            'client_name': 'Client Name'
        }
        
        result = handle_create_gallery(client_user, body)
        assert result['statusCode'] == 403
        body_data = json.loads(result['body'])
        assert 'Photographers only' in body_data['error']


class TestFeatureGating:
    """Test that features are properly gated by plan level"""
    
    def test_free_plan_feature_access(self):
        """Test that free plan has access to basic features only"""
        from utils.plan_enforcement import get_required_plan_for_feature
        
        # Free plan features (should return None or 'free')
        free_features = ['basic_galleries', 'photo_upload', 'client_sharing']
        
        for feature in free_features:
            required_plan = get_required_plan_for_feature(feature)
            assert required_plan in [None, 'free'], f"{feature} should be free"
    
    def test_pro_plan_features_blocked_on_free(self):
        """Test that Pro features are blocked on free plan"""
        pro_features = [
            'client_invoicing',
            'custom_email_templates',
            'advanced_seo'
        ]
        
        for feature in pro_features:
            # Mock a free plan user
            user_features = {'client_invoicing': False}
            
            has_feature = check_plan_feature(user_features, feature)
            assert not has_feature, f"{feature} should be blocked on free plan"
    
    def test_ultimate_plan_has_all_features(self):
        """Test that Ultimate plan has access to all features"""
        ultimate_features = {
            'client_invoicing': True,
            'custom_email_templates': True,
            'advanced_seo': True,
            'raw_vault': True,
            'scheduler': True,
            'custom_domain': True,
            'remove_branding': True,
            'priority_support': True
        }
        
        for feature, expected in ultimate_features.items():
            has_feature = check_plan_feature(ultimate_features, feature)
            assert has_feature == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
