"""Tests for Leads Handler (CRM)"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.leads_handler import handle_capture_lead, handle_list_leads, calculate_lead_score

class TestLeadsHandler:
    def test_calculate_lead_score(self):
        lead_data = {'source': 'portfolio_contact', 'message': 'I need a wedding photographer', 'budget': '3000-5000', 'timeline': 'within_6_months'}
        score = calculate_lead_score(lead_data)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    @patch('handlers.leads_handler.send_email')
    @patch('handlers.leads_handler.handle_trigger_followup_sequence')
    @patch('handlers.leads_handler.leads_table')
    @patch('handlers.leads_handler.users_table')
    def test_capture_lead(self, mock_users_table, mock_leads_table, mock_trigger, mock_send_email):
        # Mock photographer exists
        mock_users_table.get_item.return_value = {'Item': {'id': 'photo1', 'email': 'photo@example.com', 'name': 'Photographer'}}
        photographer_id = 'photo1'
        body = {'name': 'Test Client', 'email': 'client@example.com', 'message': 'I need a professional photographer for my wedding next year', 'source': 'portfolio_contact'}
        response = handle_capture_lead(photographer_id, body)
        assert response['statusCode'] == 200
        assert mock_leads_table.put_item.called
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.leads_handler.leads_table')
    def test_list_leads(self, mock_leads_table, mock_get_features):
        # Mock Pro plan features
        mock_get_features.return_value = ({'client_invoicing': True}, None, None)
        user = {'user_id': 'photo1', 'id': 'photo1', 'role': 'photographer'}
        mock_leads_table.query.return_value = {'Items': [{'id': 'lead1', 'name': 'Client 1', 'score': 85}]}
        response = handle_list_leads(user, query_params={})
        assert response['statusCode'] == 200
