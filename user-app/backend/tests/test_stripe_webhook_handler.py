"""
Tests for Stripe Webhook Handler
Tests webhook event processing including invoice.paid events
"""
import json
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from handlers.stripe_webhook_handler import handle_invoice_event
from utils.config import dynamodb

# Test table names
TEST_USERS_TABLE = 'galerly-users-test'
TEST_SUBSCRIPTIONS_TABLE = 'galerly-subscriptions-test'
TEST_BILLING_TABLE = 'galerly-billing-test'


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables for testing"""
    # Setup mock tables
    users_table = MagicMock()
    subscriptions_table = MagicMock()
    billing_table = MagicMock()
    mock_resource = MagicMock()
    
    def get_table(name):
        if 'users' in name.lower():
            return users_table
        elif 'subscriptions' in name.lower():
            return subscriptions_table
        elif 'billing' in name.lower():
            return billing_table
        return MagicMock()
    
    mock_resource.Table.side_effect = get_table
    
    # Patch the dynamodb resource inside utils.config
    with patch('utils.config.dynamodb', mock_resource):
        yield {
            'users': users_table,
            'subscriptions': subscriptions_table,
            'billing': billing_table
        }


def test_invoice_paid_event_creates_billing_record_with_correct_plan(mock_dynamodb_tables):
    """
    Test that invoice.paid event creates billing record with correct plan from subscription
    This addresses the bug where billing records were created with plan='free' 
    even for paid subscriptions
    """
    # Mock user lookup
    mock_dynamodb_tables['users'].scan.return_value = {
        'Items': [{
            'id': 'test-user-123',
            'email': 'test@example.com',
            'stripe_customer_id': 'cus_test123'
        }]
    }
    
    # Mock subscription lookup - return ultimate plan subscription
    mock_dynamodb_tables['subscriptions'].scan.return_value = {
        'Items': [{
            'id': 'sub-123',
            'user_id': 'test-user-123',
            'stripe_subscription_id': 'sub_test123',
            'plan': 'ultimate',
            'status': 'active'
        }]
    }
    
    # Mock invoice data
    invoice = {
        'id': 'in_test123',
        'customer': 'cus_test123',
        'subscription': 'sub_test123',
        'amount_paid': 118800,  # $1188 in cents
        'status': 'paid',
        'currency': 'usd',
        'invoice_pdf': 'https://stripe.com/invoice.pdf',
        'number': 'INV-001'
    }
    
    # Call the handler
    response = handle_invoice_event('invoice.paid', invoice)
    
    # Verify billing record was created
    assert mock_dynamodb_tables['billing'].put_item.called
    billing_item = mock_dynamodb_tables['billing'].put_item.call_args[1]['Item']
    
    # Verify correct plan was set
    assert billing_item['plan'] == 'ultimate', \
        "Billing record should have 'ultimate' plan from subscription, not 'free'"
    
    # Verify other fields
    assert billing_item['user_id'] == 'test-user-123'
    assert billing_item['stripe_invoice_id'] == 'in_test123'
    assert billing_item['amount'] == 1188.0
    assert billing_item['status'] == 'paid'


def test_invoice_paid_event_defaults_to_free_when_no_subscription(mock_dynamodb_tables):
    """
    Test that invoice.paid event defaults to free plan when no subscription found
    This is expected behavior for non-subscription invoices
    """
    # Mock user lookup
    mock_dynamodb_tables['users'].scan.return_value = {
        'Items': [{
            'id': 'test-user-456',
            'email': 'test2@example.com',
            'stripe_customer_id': 'cus_test456'
        }]
    }
    
    # Mock subscription lookup - return empty
    mock_dynamodb_tables['subscriptions'].scan.return_value = {
        'Items': []
    }
    
    # Mock invoice data without subscription
    invoice = {
        'id': 'in_test456',
        'customer': 'cus_test456',
        'subscription': None,
        'amount_paid': 5000,  # $50 in cents
        'status': 'paid',
        'currency': 'usd',
        'invoice_pdf': 'https://stripe.com/invoice.pdf',
        'number': 'INV-002'
    }
    
    # Call the handler
    response = handle_invoice_event('invoice.paid', invoice)
    
    # Verify billing record was created with free plan
    assert mock_dynamodb_tables['billing'].put_item.called
    billing_item = mock_dynamodb_tables['billing'].put_item.call_args[1]['Item']
    assert billing_item['plan'] == 'free'


def test_invoice_paid_event_handles_different_plan_types(mock_dynamodb_tables):
    """
    Test that invoice.paid event correctly handles different subscription plans
    """
    plans = ['starter', 'plus', 'pro', 'ultimate']
    
    for plan in plans:
        # Reset mocks
        mock_dynamodb_tables['billing'].reset_mock()
        
        # Mock user lookup
        mock_dynamodb_tables['users'].scan.return_value = {
            'Items': [{
                'id': f'user-{plan}',
                'email': f'{plan}@example.com',
                'stripe_customer_id': f'cus_{plan}'
            }]
        }
        
        # Mock subscription lookup with specific plan
        mock_dynamodb_tables['subscriptions'].scan.return_value = {
            'Items': [{
                'id': f'sub-{plan}',
                'user_id': f'user-{plan}',
                'stripe_subscription_id': f'sub_{plan}',
                'plan': plan,
                'status': 'active'
            }]
        }
        
        # Mock invoice
        invoice = {
            'id': f'in_{plan}',
            'customer': f'cus_{plan}',
            'subscription': f'sub_{plan}',
            'amount_paid': 10000,
            'status': 'paid',
            'currency': 'usd'
        }
        
        # Call handler
        handle_invoice_event('invoice.paid', invoice)
        
        # Verify correct plan
        billing_item = mock_dynamodb_tables['billing'].put_item.call_args[1]['Item']
        assert billing_item['plan'] == plan, \
            f"Billing record should have '{plan}' plan from subscription"


def test_invoice_paid_event_uses_attr_condition_for_scan(mock_dynamodb_tables):
    """
    Test that the subscription lookup uses Attr condition (not string-based KeyConditionExpression)
    This ensures compatibility with boto3 DynamoDB API
    """
    from boto3.dynamodb.conditions import Attr
    
    # Mock user
    mock_dynamodb_tables['users'].scan.return_value = {
        'Items': [{'id': 'user-1', 'stripe_customer_id': 'cus_1'}]
    }
    
    # Mock subscription
    mock_dynamodb_tables['subscriptions'].scan.return_value = {
        'Items': [{'plan': 'pro', 'stripe_subscription_id': 'sub_1'}]
    }
    
    # Invoice
    invoice = {
        'id': 'in_1',
        'customer': 'cus_1',
        'subscription': 'sub_1',
        'amount_paid': 1000,
        'status': 'paid',
        'currency': 'usd'
    }
    
    # Call handler
    handle_invoice_event('invoice.paid', invoice)
    
    # Verify scan was called with FilterExpression (Attr condition)
    assert mock_dynamodb_tables['subscriptions'].scan.called
    call_kwargs = mock_dynamodb_tables['subscriptions'].scan.call_args[1]
    assert 'FilterExpression' in call_kwargs, \
        "Should use FilterExpression with Attr condition for subscription lookup"
