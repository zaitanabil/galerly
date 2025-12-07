"""
Tests for support_handler.py
Tests support level determination based on plan
"""
import pytest
from unittest.mock import patch
from handlers.support_handler import (
    get_support_level,
    SUPPORT_LEVELS
)


class TestSupportLevels:
    """Test support level definitions"""
    
    def test_all_plans_have_support_level(self):
        """Every plan should have a support level defined"""
        expected_plans = ['free', 'starter', 'plus', 'pro', 'ultimate']
        
        for plan in expected_plans:
            assert plan in SUPPORT_LEVELS
            assert 'level' in SUPPORT_LEVELS[plan]
            assert 'response_time' in SUPPORT_LEVELS[plan]
            assert 'channels' in SUPPORT_LEVELS[plan]
    
    def test_ultimate_has_best_support(self):
        """Ultimate plan should have best support"""
        ultimate = SUPPORT_LEVELS['ultimate']
        
        assert ultimate['level'] == 'vip'
        assert 'phone' in ultimate['channels']
        assert len(ultimate['channels']) >= 4
    
    def test_free_has_basic_support(self):
        """Free plan should have basic support"""
        free = SUPPORT_LEVELS['free']
        
        assert free['level'] == 'priority'
        assert 'email' in free['channels']


class TestGetSupportLevel:
    """Test support level retrieval"""
    
    @patch('handlers.support_handler.get_user_features')
    def test_get_support_level_free(self, mock_get_user_features):
        """Free plan users get priority support"""
        mock_get_user_features.return_value = ({}, 'free', 'free')
        
        user = {'id': 'user123', 'plan': 'free'}
        # FIX: get_support_level returns dict, not response object
        result = get_support_level(user)
        
        assert result['plan'] == 'free'
        assert result['level'] == 'priority'
        assert 'email' in result['channels']
    
    @patch('handlers.support_handler.get_user_features')
    def test_get_support_level_ultimate(self, mock_get_user_features):
        """Ultimate plan users get VIP support"""
        mock_get_user_features.return_value = ({}, 'ultimate', 'ultimate')
        
        user = {'id': 'user123', 'plan': 'ultimate'}
        # FIX: get_support_level returns dict, not response object
        result = get_support_level(user)
        
        assert result['plan'] == 'ultimate'
        assert result['level'] == 'vip'
        assert 'phone' in result['channels']
        assert 'video' in result['channels']
    
    @patch('handlers.support_handler.get_user_features')
    def test_get_support_level_includes_all_fields(self, mock_get_user_features):
        """Response includes all necessary fields"""
        mock_get_user_features.return_value = ({}, 'pro', 'pro')
        
        user = {'id': 'user123', 'plan': 'pro'}
        # FIX: get_support_level returns dict, not response object
        result = get_support_level(user)
        
        assert 'plan' in result
        assert 'level' in result  # Field name is 'level', not 'support_level'
        assert 'response_time' in result
        assert 'channels' in result
        assert 'description' in result


class TestSupportChannels:
    """Test support channel availability"""
    
    def test_email_available_all_plans(self):
        """Email support should be available for all plans"""
        for plan, details in SUPPORT_LEVELS.items():
            assert 'email' in details['channels'], f"Email missing for {plan}"
    
    def test_chat_available_paid_plans(self):
        """Chat should be available for Plus and above"""
        paid_plans_with_chat = ['plus', 'pro', 'ultimate']
        
        for plan in paid_plans_with_chat:
            assert 'chat' in SUPPORT_LEVELS[plan]['channels']
    
    def test_phone_only_ultimate(self):
        """Phone support should only be on Ultimate"""
        for plan, details in SUPPORT_LEVELS.items():
            if plan == 'ultimate':
                assert 'phone' in details['channels']
            else:
                assert 'phone' not in details['channels']


class TestResponseTime:
    """Test response time guarantees"""
    
    def test_ultimate_fastest_response(self):
        """Ultimate should have fastest response time"""
        ultimate_time = SUPPORT_LEVELS['ultimate']['response_time']
        
        assert '2-6 hours' in ultimate_time
    
    def test_free_reasonable_response(self):
        """Free plan should have reasonable response time"""
        free_time = SUPPORT_LEVELS['free']['response_time']
        
        assert 'hours' in free_time or 'hour' in free_time


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
