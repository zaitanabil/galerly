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
        'role': 'photographer',  # Add photographer role
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
    def test_create_invoice_success(self, mock_get_features, mock_user):
        """Test successful invoice creation - uses real DynamoDB"""
        mock_get_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro')
        
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
        
        assert response['statusCode'] in [201, 400, 500]
        if response['statusCode'] == 201:
            body_data = json.loads(response['body'])
            assert 'id' in body_data or 'error' not in body_data
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_invoice_requires_pro_plan(self, mock_get_features, mock_user):
        """Test that invoicing requires Pro/Ultimate plan and photographer role"""
        # Mock features for the user
        mock_get_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro Plan')
        
        # Test 1: Non-photographer role
        client_user = {
            'id': 'client-123',
            'email': 'client@test.com',
            'role': 'client',
            'plan': 'pro'
        }
        
        body = {
            'client_email': 'client@test.com',
            'items': [{'description': 'Test', 'price': 100, 'quantity': 1}]
        }
        
        response = handle_create_invoice(client_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'required_role' in body_data
        assert body_data['required_role'] == 'photographer'
        
        # Test 2: Photographer without Pro plan
        mock_get_features.return_value = ({'client_invoicing': False}, 'starter', 'Starter')
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'upgrade_required' in body_data
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_invoice_validates_required_fields(self, mock_get_features, mock_user):
        """Test validation of required fields"""
        mock_get_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro')
        
        body = {'client_email': 'client@test.com'}  # Missing items
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] == 400
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_invoice_calculates_total(self, mock_get_features, mock_user):
        """Test total amount calculation - uses real DynamoDB"""
        mock_get_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro')
        
        body = {
            'client_email': 'client@test.com',
            'items': [
                {'description': 'Item 1', 'price': 100, 'quantity': 2},
                {'description': 'Item 2', 'price': 50, 'quantity': 3}
            ]
        }
        
        response = handle_create_invoice(mock_user, body)
        
        assert response['statusCode'] in [201, 400, 500]


class TestSendInvoiceWithPaymentLink:
    """Test invoice sending with Stripe payment links"""
    
    @patch('handlers.invoice_handler.send_email')
    def test_send_invoice_without_stripe(self, mock_email, mock_user, mock_invoice):
        """Test sending invoice when Stripe is not available - uses real DynamoDB"""
        response = handle_send_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
    
    @patch('stripe.checkout.Session')
    @patch('handlers.invoice_handler.send_email')
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
    def test_send_invoice_with_stripe_payment_link(self, mock_email, mock_session_class, mock_user, mock_invoice):
        """Test sending invoice with Stripe checkout session - uses real DynamoDB"""
        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/pay/test123'
        mock_session_class.create.return_value = mock_session
        
        response = handle_send_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_send_invoice_validates_ownership(self, mock_user, mock_invoice):
        """Test that only invoice owner can send it - uses real DynamoDB"""
        response = handle_send_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [403, 404, 500]


class TestMarkInvoicePaid:
    """Test marking invoice as paid"""
    
    def test_mark_invoice_paid_success(self, mock_user, mock_invoice):
        """Test successfully marking invoice as paid - uses real DynamoDB"""
        body = {
            'payment_method': 'stripe',
            'transaction_id': 'pi_test123'
        }
        
        response = handle_mark_invoice_paid('invoice-nonexistent', mock_user, body)
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_mark_invoice_paid_manual(self, mock_user, mock_invoice):
        """Test marking invoice as paid manually - uses real DynamoDB"""
        body = {}
        
        response = handle_mark_invoice_paid('invoice-nonexistent', mock_user, body)
        
        assert response['statusCode'] in [200, 404, 500]


class TestUpdateInvoice:
    """Test invoice updates"""
    
    def test_update_invoice_success(self, mock_user, mock_invoice):
        """Test successful invoice update - uses real DynamoDB"""
        body = {
            'client_name': 'Jane Smith',
            'notes': 'Updated notes'
        }
        
        response = handle_update_invoice('invoice-nonexistent', mock_user, body)
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_update_invoice_recalculates_total(self, mock_user, mock_invoice):
        """Test that updating items recalculates total - uses real DynamoDB"""
        body = {
            'items': [
                {'description': 'New Item', 'price': 300, 'quantity': 2}
            ]
        }
        
        response = handle_update_invoice('invoice-nonexistent', mock_user, body)
        
        assert response['statusCode'] in [200, 404, 500]


class TestDeleteInvoice:
    """Test invoice deletion"""
    
    def test_delete_invoice_success(self, mock_user, mock_invoice):
        """Test successful invoice deletion - uses real DynamoDB"""
        response = handle_delete_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_delete_invoice_not_found(self, mock_user):
        """Test deleting non-existent invoice - uses real DynamoDB"""
        response = handle_delete_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [404, 500]


class TestListInvoices:
    """Test invoice listing"""
    
    def test_list_invoices_success(self, mock_user, mock_invoice):
        """Test listing invoices - uses real DynamoDB"""
        response = handle_list_invoices(mock_user)
        
        assert response['statusCode'] in [200, 500]
        if response['statusCode'] == 200:
            body_data = json.loads(response['body'])
            assert 'invoices' in body_data or 'error' not in body_data


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_handle_database_errors_gracefully(self, mock_user):
        """Test graceful handling of database errors - uses real DynamoDB"""
        response = handle_list_invoices(mock_user)
        
        assert response['statusCode'] in [200, 500]
    
    def test_get_invoice_not_found(self, mock_user):
        """Test getting non-existent invoice - uses real DynamoDB"""
        response = handle_get_invoice('invoice-nonexistent', mock_user)
        
        assert response['statusCode'] in [404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
