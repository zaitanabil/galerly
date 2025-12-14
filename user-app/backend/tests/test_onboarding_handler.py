"""Tests for Onboarding Handler"""
import pytest
import json
from unittest.mock import patch, MagicMock
from handlers.onboarding_handler import handle_create_onboarding_workflow, handle_list_workflows

class TestOnboardingHandler:
    @patch('handlers.onboarding_handler.onboarding_workflows_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_workflow(self, mock_features, mock_table):
        user = {'user_id': 'photo1', 'id': 'photo1', 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        # Mock Pro plan with client_onboarding feature
        mock_features.return_value = ({'client_onboarding': True}, 'pro', 'Pro Plan')
        
        # Include proper trigger type and steps as required by handler
        body = {
            'name': 'Welcome Flow', 
            'trigger': 'lead_converted',  # Must be valid trigger type
            'steps': [{'type': 'email', 'delay_hours': 0, 'template': 'welcome', 'subject': 'Welcome', 'content': 'Welcome message'}]
        }
        response = handle_create_onboarding_workflow(user, body)
        assert response['statusCode'] == 201
        assert mock_table.put_item.called
    
    @patch('handlers.onboarding_handler.onboarding_workflows_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_list_workflows(self, mock_features, mock_table):
        user = {'user_id': 'photo1', 'id': 'photo1', 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        # Mock Pro plan with client_onboarding feature
        mock_features.return_value = ({'client_onboarding': True}, 'pro', 'Pro Plan')
        
        mock_table.query.return_value = {'Items': [{'id': 'wf1', 'name': 'Welcome'}]}
        response = handle_list_workflows(user)
        assert response['statusCode'] == 200
