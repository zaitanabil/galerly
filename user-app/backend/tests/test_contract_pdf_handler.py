"""
Tests for Contract PDF Handler
"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.contract_pdf_handler import handle_generate_contract_pdf, handle_download_contract_pdf


class TestContractPDFHandler:
    """Test contract PDF generation"""
    
    @patch('handlers.contract_pdf_handler.get_user_from_token')
    @patch('handlers.contract_pdf_handler.dynamodb')
    @patch('handlers.contract_pdf_handler.generate_contract_pdf')
    def test_generate_contract_pdf(self, mock_generate, mock_dynamodb, mock_get_user):
        """Test generating contract PDF"""
        mock_get_user.return_value = {'user_id': 'photo1'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'contract1', 'photographer_id': 'photo1', 'client_name': 'Test Client'}
        }
        mock_generate.return_value = 's3://bucket/contract.pdf'
        
        event = {'pathParameters': {'contract_id': 'contract1'}}
        response = handle_generate_contract_pdf(event)
        
        assert response['statusCode'] == 200
    
    @patch('handlers.contract_pdf_handler.get_user_from_token')
    @patch('handlers.contract_pdf_handler.dynamodb')
    @patch('handlers.contract_pdf_handler.SecureURLGenerator')
    def test_download_contract_pdf(self, mock_url_gen_class, mock_dynamodb, mock_get_user):
        """Test downloading contract PDF"""
        mock_get_user.return_value = {'user_id': 'photo1'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'contract1', 'photographer_id': 'photo1', 'pdf_url': 's3://bucket/contracts/contract1.pdf'}
        }
        
        # Mock URL generator instance
        mock_url_gen = MagicMock()
        mock_url_gen.generate_download_url.return_value = 'https://presigned-url.com'
        mock_url_gen_class.return_value = mock_url_gen
        
        event = {'pathParameters': {'contract_id': 'contract1'}}
        response = handle_download_contract_pdf(event)
        
        assert response['statusCode'] == 200
