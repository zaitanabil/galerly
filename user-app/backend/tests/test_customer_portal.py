import pytest
import json  # FIX: Add json import for parsing response bodies
from unittest.mock import MagicMock, patch
from handlers.billing_handler import handle_create_customer_portal_session


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        'id': 'user123',
        'email': 'test@example.com',
        'role': 'photographer',
        'plan': 'plus'
    }


@pytest.fixture
def mock_tables():
    """Mock DynamoDB tables"""
    with patch('handlers.billing_handler.users_table') as mock_users:
        yield {'users': mock_users}


@pytest.fixture
def mock_stripe():
    """Mock Stripe"""
    with patch('handlers.billing_handler.stripe') as mock_stripe_module:
        yield mock_stripe_module


def test_create_customer_portal_success(mock_user, mock_tables, mock_stripe):
    """Test creating a Stripe Customer Portal session"""
    # Mock user with stripe_customer_id
    mock_tables['users'].get_item.return_value = {
        'Item': {
            'email': 'test@example.com',
            'stripe_customer_id': 'cus_test123'
        }
    }
    
    # Mock Stripe session creation - return object with url attribute, not dict
    mock_session = MagicMock()
    mock_session.url = 'https://billing.stripe.com/session/test123'
    mock_stripe.billing_portal.Session.create.return_value = mock_session
    
    body = {'return_url': 'http://localhost:5173/billing'}
    response = handle_create_customer_portal_session(mock_user, body)
    
    assert response['statusCode'] == 200
    # FIX: Parse JSON body before accessing
    body = json.loads(response['body'])
    assert 'url' in body
    assert 'stripe.com' in body['url'] or 'portal=mock' in body['url']


def test_create_customer_portal_no_customer_id(mock_user, mock_tables, mock_stripe):
    """Test creating portal session when user has no Stripe customer ID"""
    # Mock user without stripe_customer_id
    mock_tables['users'].get_item.return_value = {
        'Item': {
            'email': 'test@example.com'
            # No stripe_customer_id
        }
    }
    
    body = {'return_url': 'http://localhost:5173/billing'}
    response = handle_create_customer_portal_session(mock_user, body)
    
    assert response['statusCode'] == 400
    # FIX: Parse JSON body before accessing
    body = json.loads(response['body'])
    assert 'No payment method' in body['error']


def test_create_customer_portal_user_not_found(mock_user, mock_tables, mock_stripe):
    """Test creating portal session when user not found"""
    mock_tables['users'].get_item.return_value = {}  # No Item
    
    body = {'return_url': 'http://localhost:5173/billing'}
    response = handle_create_customer_portal_session(mock_user, body)
    
    assert response['statusCode'] == 404
    # FIX: Parse JSON body before accessing
    body = json.loads(response['body'])
    assert 'User not found' in body['error']


@patch.dict('os.environ', {'ENVIRONMENT': 'local'})
def test_create_customer_portal_local_environment(mock_user, mock_tables, mock_stripe):
    """Test creating portal session in local environment (returns mock URL)"""
    mock_tables['users'].get_item.return_value = {
        'Item': {
            'email': 'test@example.com',
            'stripe_customer_id': 'cus_test123'
        }
    }
    
    body = {'return_url': 'http://localhost:5173/billing'}
    response = handle_create_customer_portal_session(mock_user, body)
    
    assert response['statusCode'] == 200
    # FIX: Parse JSON body before accessing
    body = json.loads(response['body'])
    assert 'url' in body
    assert 'portal=mock' in body['url']
    # Should NOT call Stripe in local mode
    mock_stripe.billing_portal.Session.create.assert_not_called()

