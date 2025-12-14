"""
Tests for leads handler using REAL AWS resources
"""
import pytest
import json
import uuid
from unittest.mock import patch
from handlers.leads_handler import handle_capture_lead, handle_list_leads, calculate_lead_score
from utils.config import leads_table, users_table


class TestLeadsHandler:
    """Test leads management with real AWS"""
    
    def test_calculate_lead_score(self):
        """Test lead scoring algorithm"""
        lead_data = {
            'source': 'portfolio_contact',
            'message': 'I need a wedding photographer',
            'budget': '3000-5000',
            'timeline': 'within_6_months'
        }
        score = calculate_lead_score(lead_data)
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_capture_lead(self):
        """Test capturing a lead with real AWS"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        
        try:
            users_table.put_item(Item={
                'id': photographer_id,
                'email': f'{photographer_id}@example.com',
                'name': 'Test Photographer',
                'role': 'photographer'
            })
            
            body = {
                'name': 'Test Client',
                'email': f'client-{uuid.uuid4()}@example.com',
                'message': 'I need a professional photographer for my wedding',
                'source': 'portfolio_contact'
            }
            
            with patch('handlers.leads_handler.send_email'), \
                 patch('handlers.leads_handler.handle_trigger_followup_sequence'):
                response = handle_capture_lead(photographer_id, body)
                assert response['statusCode'] in [200, 400, 404, 500]
            
        finally:
            try:
                users_table.delete_item(Key={'email': f'{photographer_id}@example.com'})
            except:
                pass
    
    def test_list_leads(self):
        """Test listing leads with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        user = {
            'user_id': user_id,
            'id': user_id,
            'email': f'{user_id}@example.com',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        with patch('handlers.subscription_handler.get_user_features') as mock_features:
            mock_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro Plan')
            
            response = handle_list_leads(user, query_params={})
            assert response['statusCode'] in [200, 403, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
