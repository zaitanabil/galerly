"""Tests for Services Handler"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.services_handler import handle_list_services, handle_create_service

class TestServicesHandler:
    @patch('handlers.services_handler.dynamodb')
    def test_list_services(self, mock_dynamodb):
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.return_value = {'Items': [{'id': 'svc1', 'name': 'Wedding'}]}
        response = handle_list_services('photo1', is_public=True)
        assert response['statusCode'] == 200
    
    @patch('handlers.services_handler.dynamodb')
    def test_create_service(self, mock_dynamodb):
        user = {'user_id': 'photo1', 'id': 'photo1', 'role': 'photographer'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        body = {'name': 'Wedding Photography', 'price': 2500, 'description': 'Full day'}
        response = handle_create_service(user, body)
        assert response['statusCode'] == 201
