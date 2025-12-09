"""
Tests for invoice_handler.py with payment link functionality
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
from handlers.invoice_handler import (
    handle_list_invoices,
    handle_create_invoice,
    handle_get_invoice,
    handle_update_invoice,
    handle_delete_invoice,
    handle_send_invoice,
    handle_mark_invoice_paid
)


@pytest.fixture
def mock_user():
    return {
        'id': 'test-user-123',
        'email': 'photographer@test.com',
        'name': 'Test Photographer',
        'plan': 'pro'
    }


@pytest.fixture
def mock_invoice():
    return {
        'id': 'invoice-123',
        'user_id': 'test-user-123',
        'client_name': 'John Doe',
        'client_email': 'client@test.com',
        'status': 'draft',
        'due_date': '2024-12-31',
        'currency': 'USD',
        'items': [
            {
                'description': 'Wedding Photography',
                'quantity': Decimal('1'),
                'price': Decimal('2000.00')
            }
        ],
        'total_amount': Decimal('2000.00'),
        'notes': 'Thank you for your business',
        'created_at': '2024-12-01T10:00:00Z',
        'updated_at': '2024-12-01T10:00:00Z'
    }


class TestCreateInvoice:
    """Test invoice creation"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.invoice_handler.invoices_table')
    def test_create_invoice_success(self, mock_table, mock_features, mock_user):
        """Test successful invoice creation"""
        mock_features.return_value = ({'client_invoicing': True}, None, None)
        
        body = {
            'client_email': 'client@test.com',
            'client_name': 'John Doe',
            'items': [
                {
                    'description': 'Photography Session',
                    'quantity': 1,
                    'price': 500.00
                }
            ],
            'due_date': '2024-12-31',
            'currency': 'USD',
            'notes': 'Payment due upon receipt'
        }
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 201
        body_data = json.loads(response['body'])
        assert 'id' in body_data
        assert body_data['status'] == 'draft'
        assert float(body_data['total_amount']) == 500.00
        mock_table.put_item.assert_called_once()
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_invoice_requires_pro_plan(self, mock_features, mock_user):
        """Test that invoicing requires Pro/Ultimate plan"""
        mock_features.return_value = ({'client_invoicing': False}, None, None)
        
        body = {
            'client_email': 'client@test.com',
            'items': [{'description': 'Test', 'price': 100, 'quantity': 1}]
        }
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'upgrade_required' in body_data
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_invoice_validates_required_fields(self, mock_features, mock_user):
        """Test validation of required fields"""
        mock_features.return_value = ({'client_invoicing': True}, None, None)
        
        body = {'client_email': 'client@test.com'}  # Missing items
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 400
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.invoice_handler.invoices_table')
    def test_create_invoice_calculates_total(self, mock_table, mock_features, mock_user):
        """Test total amount calculation"""
        mock_features.return_value = ({'client_invoicing': True}, None, None)
        
        body = {
            'client_email': 'client@test.com',
            'items': [
                {'description': 'Item 1', 'price': 100, 'quantity': 2},
                {'description': 'Item 2', 'price': 50, 'quantity': 3}
            ]
        }
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 201
        body_data = json.loads(response['body'])
        assert float(body_data['total_amount']) == 350.00  # (100*2) + (50*3)


class TestSendInvoiceWithPaymentLink:
    """Test invoice sending with Stripe payment links"""
    
    @patch('handlers.invoice_handler.send_email')
    @patch('handlers.invoice_handler.invoices_table')
    def test_send_invoice_without_stripe(self, mock_table, mock_email, mock_user, mock_invoice):
        """Test sending invoice when Stripe is not available"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        response = handle_send_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'Invoice sent' in body_data['message']
        mock_email.assert_called_once()
        
        # Verify status updated
        assert mock_table.put_item.called
        updated_invoice = mock_table.put_item.call_args[1]['Item']
        assert updated_invoice['status'] == 'sent'
        assert 'sent_at' in updated_invoice
    
    @patch('stripe.checkout.Session')
    @patch('handlers.invoice_handler.send_email')
    @patch('handlers.invoice_handler.invoices_table')
    @patch.dict('os.environ', {
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'FRONTEND_URL': 'http://localhost:5173',
        'DEFAULT_INVOICE_CURRENCY': 'USD',
        'DEFAULT_INVOICE_PAYMENT_METHOD': 'manual',
        'DEFAULT_INVOICE_DUE_DATE': 'Upon_Receipt',
        'DEFAULT_SERVICE_NAME': 'Service',
        'DEFAULT_PHOTOGRAPHER_NAME': 'Your_Photographer',
        'DEFAULT_ITEM_PRICE': '0',
        'DEFAULT_ITEM_QUANTITY': '1',
        'DISABLE_STRIPE_INVOICE_INTEGRATION': 'false'
    })
    def test_send_invoice_with_stripe_payment_link(self, mock_table, mock_email, mock_session_class, mock_user, mock_invoice):
        """Test sending invoice with Stripe checkout session"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        # Mock Stripe Checkout Session response
        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/pay/test123'
        mock_session_class.create.return_value = mock_session
        
        response = handle_send_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['payment_link'] == 'https://checkout.stripe.com/pay/test123'
        
        # Verify Checkout Session was created with correct parameters
        mock_session_class.create.assert_called_once()
        create_call_kwargs = mock_session_class.create.call_args[1]
        assert create_call_kwargs['mode'] == 'payment'
        assert len(create_call_kwargs['line_items']) == 1
        assert create_call_kwargs['line_items'][0]['price_data']['product_data']['name'] == 'Wedding Photography'
        assert create_call_kwargs['success_url'] == 'http://localhost:5173/invoice/invoice-123/success'
        assert create_call_kwargs['cancel_url'] == 'http://localhost:5173/invoice/invoice-123'
        
        # Verify email contains payment link
        email_call = mock_email.call_args
        assert 'checkout.stripe.com' in str(email_call)
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_send_invoice_validates_ownership(self, mock_table, mock_user, mock_invoice):
        """Test that only invoice owner can send it"""
        mock_invoice['user_id'] = 'different-user'
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        response = handle_send_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 403


class TestMarkInvoicePaid:
    """Test marking invoice as paid"""
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_mark_invoice_paid_success(self, mock_table, mock_user, mock_invoice):
        """Test successfully marking invoice as paid"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        body = {
            'payment_method': 'stripe',
            'transaction_id': 'pi_test123'
        }
        
        response = handle_mark_invoice_paid('invoice-123', mock_user, body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['invoice']['status'] == 'paid'
        assert 'paid_at' in body_data['invoice']
        assert body_data['invoice']['payment_method'] == 'stripe'
        assert body_data['invoice']['transaction_id'] == 'pi_test123'
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_mark_invoice_paid_manual(self, mock_table, mock_user, mock_invoice):
        """Test marking invoice as paid manually"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        body = {}  # No payment method provided
        
        response = handle_mark_invoice_paid('invoice-123', mock_user, body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['invoice']['payment_method'] == 'manual'


class TestUpdateInvoice:
    """Test invoice updates"""
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_update_invoice_success(self, mock_table, mock_user, mock_invoice):
        """Test successful invoice update"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        body = {
            'client_name': 'Jane Smith',
            'notes': 'Updated notes'
        }
        
        response = handle_update_invoice('invoice-123', mock_user, body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['client_name'] == 'Jane Smith'
        assert body_data['notes'] == 'Updated notes'
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_update_invoice_recalculates_total(self, mock_table, mock_user, mock_invoice):
        """Test that updating items recalculates total"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        body = {
            'items': [
                {'description': 'New Item', 'price': 300, 'quantity': 2}
            ]
        }
        
        response = handle_update_invoice('invoice-123', mock_user, body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert float(body_data['total_amount']) == 600.00


class TestDeleteInvoice:
    """Test invoice deletion"""
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_delete_invoice_success(self, mock_table, mock_user, mock_invoice):
        """Test successful invoice deletion"""
        mock_table.get_item.return_value = {'Item': mock_invoice}
        
        response = handle_delete_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 200
        mock_table.delete_item.assert_called_once_with(Key={'id': 'invoice-123'})
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_delete_invoice_not_found(self, mock_table, mock_user):
        """Test deleting non-existent invoice"""
        mock_table.get_item.return_value = {}
        
        response = handle_delete_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 404


class TestListInvoices:
    """Test invoice listing"""
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_list_invoices_success(self, mock_table, mock_user, mock_invoice):
        """Test listing invoices"""
        mock_table.query.return_value = {
            'Items': [mock_invoice, mock_invoice.copy()]
        }
        
        response = handle_list_invoices(mock_user)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'invoices' in body_data
        assert len(body_data['invoices']) == 2


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_handle_database_errors_gracefully(self, mock_table, mock_user):
        """Test graceful handling of database errors"""
        mock_table.query.side_effect = Exception('Database error')
        
        response = handle_list_invoices(mock_user)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('handlers.invoice_handler.invoices_table')
    def test_get_invoice_not_found(self, mock_table, mock_user):
        """Test getting non-existent invoice"""
        mock_table.get_item.return_value = {}
        
        response = handle_get_invoice('invoice-123', mock_user)
        
        assert response['statusCode'] == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
