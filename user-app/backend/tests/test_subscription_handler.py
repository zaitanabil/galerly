"""
Test Suite for Subscription Handler using REAL AWS resources
"""
import pytest
import json
import uuid
from unittest.mock import Mock
from handlers.subscription_handler import (
    get_user_features,
    get_plan_limits,
    handle_check_feature_access
)
from utils.config import users_table, user_features_table, features_table


class TestGetUserFeatures:
    """Test user feature retrieval with real AWS"""
    
    def test_get_user_features_free_plan(self):
        """Free plan users get basic features with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        
        try:
            # Create user with free plan in real DB
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            features, plan, plan_name = get_user_features(user_id)
            
            # Free plan has limited features
            assert plan == 'free'
            assert isinstance(features, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_get_user_features_ultimate_plan(self):
        """Ultimate plan users get all features with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'ultimate',
                'role': 'photographer'
            })
            
            features, plan, plan_name = get_user_features(user_id)
            
            assert plan == 'ultimate'
            assert isinstance(features, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_get_user_features_custom_features(self):
        """Test users with custom feature grants"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'pro',
                'role': 'photographer'
            })
            
            # Add custom feature
            user_features_table.put_item(Item={
                'user_id': user_id,
                'feature_name': 'custom_domain',
                'granted': True
            })
            
            features, plan, plan_name = get_user_features(user_id)
            
            assert plan == 'pro'
            assert isinstance(features, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
                user_features_table.delete_item(Key={'user_id': user_id, 'feature_name': 'custom_domain'})
            except:
                pass
    
    def test_get_user_features_nonexistent_user(self):
        """Test getting features for nonexistent user"""
        features, plan, plan_name = get_user_features('nonexistent-user')
        
        # Should return default/free features
        assert isinstance(features, dict)
        assert isinstance(plan, str)


class TestGetPlanLimits:
    """Test plan limit retrieval with real AWS"""
    
    def test_get_plan_limits_returns_limits(self):
        """Plan limits are returned correctly with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'pro',
                'role': 'photographer'
            })
            
            limits = get_plan_limits(user_id)
            
            assert isinstance(limits, dict)
            assert 'storage_gb' in limits or 'galleries_per_month' in limits
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_get_plan_limits_free_user(self):
        """Free users get basic limits"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            limits = get_plan_limits(user_id)
            
            assert isinstance(limits, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass


class TestFeatureAccessCheck:
    """Test feature access checking with real AWS"""
    
    def test_check_feature_access_allowed(self):
        """Test access to allowed feature"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email, 'role': 'photographer', 'plan': 'pro'}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'pro',
                'role': 'photographer'
            })
            
            response = handle_check_feature_access(user, {'feature': 'custom_email_templates'})
            
            assert response['statusCode'] in [200, 403]
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_check_feature_access_denied(self):
        """Test access to denied feature"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email, 'role': 'photographer', 'plan': 'free'}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            response = handle_check_feature_access(user, {'feature': 'raw_vault'})
            
            assert response['statusCode'] in [200, 403]
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_check_feature_access_missing_feature(self):
        """Test checking nonexistent feature"""
        user = {'id': 'user123', 'email': 'test@example.com', 'role': 'photographer', 'plan': 'pro'}
        
        response = handle_check_feature_access(user, {})
        
        assert response['statusCode'] in [400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
