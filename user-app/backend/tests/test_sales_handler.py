"""Tests for Sales Handler"""
import pytest
import json
from unittest.mock import patch, MagicMock
from handlers.sales_handler import handle_create_payment_intent, handle_list_sales

class TestSalesHandler:
    @patch('handlers.sales_handler.sales_table')
    @patch('handlers.sales_handler.users_table')
    @patch('handlers.sales_handler.packages_table')
    @patch('handlers.sales_handler.stripe.PaymentIntent')
    def test_create_payment_intent(self, mock_stripe, mock_packages_table, mock_users_table, mock_sales_table):
        mock_stripe.create.return_value = MagicMock(id='pi_123', client_secret='secret_123')
        # Mock photographer exists
        mock_users_table.get_item.return_value = {'Item': {'id': 'photo1', 'email': 'photo@example.com', 'name': 'Photographer'}}
        # Mock package lookup for package type
        mock_packages_table.get_item.return_value = {
            'Item': {
                'id': 'pkg1', 
                'photographer_id': 'photo1', 
                'price': 500, 
                'name': 'Wedding Package'
            }
        }
        body = {
            'type': 'package', 
            'package_id': 'pkg1', 
            'photographer_id': 'photo1', 
            'customer_email': 'client@example.com', 
            'customer_name': 'Test Client'
        }
        response = handle_create_payment_intent(body)
        assert response['statusCode'] == 200
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.sales_handler.sales_table')
    def test_list_sales(self, mock_sales_table, mock_get_features):
        # Mock Pro plan features
        mock_get_features.return_value = ({'client_invoicing': True}, None, None)
        user = {'user_id': 'photo1', 'id': 'photo1', 'role': 'photographer'}
        mock_sales_table.query.return_value = {'Items': [{'id': 'sale1', 'amount': 5000, 'status': 'completed'}]}
        response = handle_list_sales(user, query_params={})
        assert response['statusCode'] == 200
