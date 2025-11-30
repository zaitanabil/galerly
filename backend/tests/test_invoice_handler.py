import pytest
from unittest.mock import Mock, patch
import json
from decimal import Decimal

@pytest.fixture
def mock_invoice_dependencies():
    with patch('handlers.invoice_handler.invoices_table') as mock_table, \
         patch('handlers.invoice_handler.send_email') as mock_email:
        yield {
            'table': mock_table,
            'email': mock_email
        }

class TestInvoiceHandler:
    def test_create_invoice_success(self, sample_user, mock_invoice_dependencies):
        from handlers.invoice_handler import handle_create_invoice
        
        body = {
            'client_email': 'client@example.com',
            'items': [{'description': 'Photoshoot', 'price': 100, 'quantity': 1}]
        }
        
        result = handle_create_invoice(sample_user, body)
        
        assert result['statusCode'] == 201
        response = json.loads(result['body'])
        assert response['client_email'] == 'client@example.com'
        assert response['total_amount'] == '100'
        mock_invoice_dependencies['table'].put_item.assert_called_once()

    def test_list_invoices(self, sample_user, mock_invoice_dependencies):
        from handlers.invoice_handler import handle_list_invoices
        
        mock_invoice_dependencies['table'].query.return_value = {
            'Items': [{'id': 'inv1', 'user_id': sample_user['id'], 'total_amount': 100}]
        }
        
        result = handle_list_invoices(sample_user)
        
        assert result['statusCode'] == 200
        response = json.loads(result['body'])
        assert len(response['invoices']) == 1

    def test_send_invoice(self, sample_user, mock_invoice_dependencies):
        from handlers.invoice_handler import handle_send_invoice
        
        invoice = {
            'id': 'inv1', 
            'user_id': sample_user['id'], 
            'client_email': 'client@example.com',
            'status': 'draft',
            'total_amount': Decimal('100.00'),
            'currency': 'USD'
        }
        mock_invoice_dependencies['table'].get_item.return_value = {'Item': invoice}
        
        result = handle_send_invoice('inv1', sample_user)
        
        assert result['statusCode'] == 200
        mock_invoice_dependencies['email'].assert_called_once()
        # Verify status update
        mock_invoice_dependencies['table'].put_item.assert_called()

