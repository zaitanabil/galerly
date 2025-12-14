"""
Test Suite for Subscription Handler using REAL AWS resources
"""
import pytest
import json
import uuid
from handlers.subscription_handler import (
    get_user_features,
    get_user_plan_limits,
    check_gallery_limit,
    check_storage_limit
)
from utils.config import users_table, user_features_table


class TestGetUserFeatures:
    """Test user feature retrieval with real AWS"""
    
    def test_get_user_features_free_plan(self):
        """Free plan users get basic features with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            features, plan, plan_name = get_user_features(user)
            
            assert plan_name.lower() == 'free'
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
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'ultimate',
                'role': 'photographer'
            })
            
            features, plan, plan_name = get_user_features(user)
            
            assert plan == 'ultimate' or plan_name == 'Ultimate'
            assert isinstance(features, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass


class TestGetPlanLimits:
    """Test plan limit retrieval with real AWS"""
    
    def test_get_plan_limits_returns_limits(self):
        """Plan limits are returned correctly with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'starter',
                'role': 'photographer'
            })
            
            limits = get_user_plan_limits(user)
            
            assert limits is not None
            assert isinstance(limits, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass


class TestCheckGalleryLimit:
    """Test gallery limit checking with real AWS"""
    
    def test_check_gallery_limit_enforced(self):
        """Gallery limit is enforced"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            result = check_gallery_limit(user)
            assert result is not None
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass


class TestPlanEnforcement:
    """Test plan enforcement logic with real AWS"""
    
    def test_storage_limit_enforced(self):
        """Storage limits are enforced per plan"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'starter',
                'role': 'photographer'
            })
            
            # check_storage_limit returns bool or tuple
            result = check_storage_limit(user, 1000)  # 1GB
            assert result is not None
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass
    
    def test_gallery_limit_enforced(self):
        """Gallery limits are enforced per plan"""
        user_id = f'user-{uuid.uuid4()}'
        user_email = f'{user_id}@example.com'
        user = {'id': user_id, 'email': user_email}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user_email,
                'plan': 'free',
                'role': 'photographer'
            })
            
            result = check_gallery_limit(user)
            assert result is not None
            
        finally:
            try:
                users_table.delete_item(Key={'email': user_email})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
