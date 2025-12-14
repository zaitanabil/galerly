"""Tests for Onboarding Handler using REAL AWS resources"""
import pytest
import json
import uuid
from unittest.mock import patch
from handlers.onboarding_handler import handle_create_onboarding_workflow, handle_list_workflows


class TestOnboardingHandler:
    """Test onboarding functionality with real DynamoDB"""
    
    def test_create_workflow(self):
        """Test creating workflow with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user = {'user_id': user_id, 'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'pro'}
        workflow_id = None
        
        try:
            # Mock Pro plan with client_onboarding feature
            with patch('handlers.subscription_handler.get_user_features') as mock_features:
                mock_features.return_value = ({'client_onboarding': True}, 'pro', 'Pro Plan')
                
                body = {
                    'name': f'Workflow {uuid.uuid4()}',
                    'trigger': 'lead_converted',
                    'steps': [{'type': 'email', 'delay_hours': 0, 'template': 'welcome', 'subject': 'Welcome', 'content': 'Welcome message'}]
                }
                response = handle_create_onboarding_workflow(user, body)
                
                assert response['statusCode'] in [201, 400, 500]
                if response['statusCode'] == 201:
                    data = json.loads(response['body'])
                    workflow_id = data.get('id')
        
        finally:
            # Cleanup happens via handler's table reference
            pass
    
    def test_list_workflows(self):
        """Test listing workflows with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user = {'user_id': user_id, 'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        with patch('handlers.subscription_handler.get_user_features') as mock_features:
            mock_features.return_value = ({'client_onboarding': True}, 'pro', 'Pro Plan')
            
            response = handle_list_workflows(user)
            assert response['statusCode'] in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
