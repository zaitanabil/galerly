"""
Tests for Invoice PDF Handler
"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.invoice_pdf_handler import handle_generate_invoice_pdf, handle_download_invoice_pdf


class TestInvoicePDFHandler:
    """Test invoice PDF generation"""
    
    @patch('handlers.invoice_pdf_handler.get_user_from_token')
    @patch('handlers.invoice_pdf_handler.dynamodb')
    @patch('handlers.invoice_pdf_handler.generate_invoice_pdf')
    def test_generate_invoice_pdf(self, mock_generate, mock_dynamodb, mock_get_user):
        """Test generating invoice PDF"""
        mock_get_user.return_value = {'user_id': 'photo1'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'invoice1', 'photographer_id': 'photo1', 'client_name': 'Test Client', 'line_items': []}
        }
        mock_generate.return_value = 's3://bucket/invoice.pdf'
        
        event = {'pathParameters': {'invoice_id': 'invoice1'}}
        response = handle_generate_invoice_pdf(event)
        
        assert response['statusCode'] == 200
    
    @patch('handlers.invoice_pdf_handler.get_user_from_token')
    @patch('handlers.invoice_pdf_handler.dynamodb')
    @patch('handlers.invoice_pdf_handler.SecureURLGenerator')
    def test_download_invoice_pdf(self, mock_url_gen_class, mock_dynamodb, mock_get_user):
        """Test downloading invoice PDF"""
        mock_get_user.return_value = {'user_id': 'photo1'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'invoice1', 'photographer_id': 'photo1', 'pdf_url': 's3://bucket/invoices/invoice1.pdf'}
        }
        
        # Mock URL generator instance
        mock_url_gen = MagicMock()
        mock_url_gen.generate_download_url.return_value = 'https://presigned-url.com'
        mock_url_gen_class.return_value = mock_url_gen
        
        event = {'pathParameters': {'invoice_id': 'invoice1'}}
        response = handle_download_invoice_pdf(event)
        
        assert response['statusCode'] == 200
