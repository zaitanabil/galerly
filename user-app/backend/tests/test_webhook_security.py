"""
Security Tests - Webhook Signature Verification
Tests for Stripe webhook signature enforcement
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from handlers.stripe_webhook_handler import handle_stripe_webhook
from handlers.billing_handler import handle_stripe_webhook as handle_billing_webhook

@pytest.fixture
def valid_webhook_event():
    """Create a valid webhook event"""
    return {
        'body': json.dumps({
            'id': 'evt_test_123',
            'type': 'invoice.paid',
            'data': {
                'object': {
                    'id': 'in_test_123',
                    'customer': 'cus_test_123',
                    'amount_paid': 2900,
                    'status': 'paid'
                }
            }
        }),
        'headers': {
            'stripe-signature': 't=1234567890,v1=valid_signature_here'
        }
    }

@pytest.fixture
def mock_stripe(monkeypatch):
    """Mock Stripe module"""
    mock = MagicMock()
    monkeypatch.setattr('handlers.stripe_webhook_handler.stripe', mock)
    monkeypatch.setattr('handlers.billing_handler.stripe', mock)
    return mock

def test_webhook_requires_signature(valid_webhook_event, mock_stripe):
    """Test that webhook without signature is rejected"""
    # Remove signature
    event_without_sig = valid_webhook_event.copy()
    event_without_sig['headers'] = {}
    
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_stripe_webhook(event_without_sig, {})
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'signature' in body['error'].lower()

def test_webhook_requires_secret_configured(valid_webhook_event, mock_stripe):
    """Test that webhook requires STRIPE_WEBHOOK_SECRET to be configured"""
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', None):
        response = handle_stripe_webhook(valid_webhook_event, {})
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'secret' in body['error'].lower()

def test_webhook_invalid_signature_rejected(valid_webhook_event, mock_stripe):
    """Test that invalid signature is rejected"""
    # Mock signature verification failure
    mock_stripe.error.SignatureVerificationError = Exception
    mock_stripe.Webhook.construct_event.side_effect = Exception("Invalid signature")
    
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_stripe_webhook(valid_webhook_event, {})
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'signature' in body['error'].lower()

def test_webhook_valid_signature_accepted(valid_webhook_event, mock_stripe):
    """Test that valid signature is accepted"""
    # Mock successful signature verification
    mock_event = {
        'id': 'evt_test_123',
        'type': 'customer.subscription.created',
        'data': {'object': {'id': 'sub_test', 'status': 'active'}}
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event
    
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_stripe_webhook(valid_webhook_event, {})
    
    # Should not be 400 or 401
    assert response['statusCode'] != 400
    assert response['statusCode'] != 401

def test_webhook_invalid_payload_rejected(valid_webhook_event, mock_stripe):
    """Test that invalid JSON payload is rejected"""
    # Mock payload parsing failure
    mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid JSON")
    
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_stripe_webhook(valid_webhook_event, {})
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'payload' in body['error'].lower()

def test_billing_webhook_signature_required():
    """Test that billing webhook handler enforces signature"""
    event_data = {'type': 'invoice.paid', 'data': {'object': {}}}
    
    # No signature provided
    with patch('handlers.billing_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_billing_webhook(event_data, stripe_signature='', raw_body='')
    
    assert response['statusCode'] == 400

def test_billing_webhook_secret_required():
    """Test that billing webhook requires secret configured"""
    event_data = {'type': 'invoice.paid', 'data': {'object': {}}}
    
    with patch('handlers.billing_handler.STRIPE_WEBHOOK_SECRET', None):
        response = handle_billing_webhook(
            event_data,
            stripe_signature='sig',
            raw_body='body'
        )
    
    assert response['statusCode'] == 500

@pytest.mark.integration
def test_webhook_signature_case_insensitive(valid_webhook_event, mock_stripe):
    """Test that signature header is case-insensitive"""
    # Try with capital S
    event_capital = valid_webhook_event.copy()
    event_capital['headers'] = {
        'Stripe-Signature': 't=1234567890,v1=valid_signature'
    }
    
    mock_stripe.Webhook.construct_event.return_value = {
        'id': 'evt_test',
        'type': 'customer.subscription.created',
        'data': {'object': {}}
    }
    
    with patch('handlers.stripe_webhook_handler.STRIPE_WEBHOOK_SECRET', 'whsec_test'):
        response = handle_stripe_webhook(event_capital, {})
    
    # Should work with capital S
    assert response['statusCode'] != 400

