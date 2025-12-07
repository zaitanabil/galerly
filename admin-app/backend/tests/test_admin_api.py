"""
Tests for Admin API
Tests admin dashboard endpoints and data health checks
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from admin-app.backend import api


@pytest.fixture
def client():
    """Create test client for Flask app"""
    api.app.config['TESTING'] = True
    with api.app.test_client() as client:
        yield client


@pytest.fixture
def mock_tables():
    """Mock DynamoDB tables"""
    with patch('api.users_table') as users, \
         patch('api.subscriptions_table') as subs, \
         patch('api.billing_table') as billing:
        yield {
            'users': users,
            'subscriptions': subs,
            'billing': billing
        }


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'galerly-admin-api'


def test_data_health_detects_orphaned_subscriptions(client, mock_tables):
    """Test data health endpoint detects orphaned subscriptions"""
    # Mock subscriptions with one orphaned
    mock_tables['subscriptions'].scan.return_value = {
        'Items': [
            {
                'id': 'sub-1',
                'user_id': 'user-1',
                'user_email': 'test@example.com',
                'plan': 'ultimate',
                'status': 'active',
                'stripe_subscription_id': 'sub_test1',
                'created_at': '2025-01-01T00:00:00Z'
            }
        ]
    }
    
    # Mock users table - no user found
    mock_tables['users'].scan.return_value = {'Items': []}
    
    # Mock billing table
    mock_tables['billing'].scan.return_value = {'Items': []}
    
    response = client.get('/api/data-health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['health_score'] < 100  # Should be less than perfect
    assert data['summary']['orphaned_subscriptions'] == 1
    assert len(data['issues']) > 0
    
    # Find orphaned subscription issue
    orphaned_issue = next((i for i in data['issues'] if i['type'] == 'orphaned_subscriptions'), None)
    assert orphaned_issue is not None
    assert orphaned_issue['severity'] == 'high'
    assert orphaned_issue['count'] == 1


def test_subscriptions_endpoint_enriches_data(client, mock_tables):
    """Test subscriptions endpoint enriches data with user validation"""
    # Mock subscriptions
    mock_tables['subscriptions'].scan.return_value = {
        'Items': [
            {
                'id': 'sub-1',
                'user_id': 'user-1',
                'user_email': 'existing@example.com',
                'plan': 'ultimate',
                'status': 'active',
                'stripe_subscription_id': 'sub_test1'
            },
            {
                'id': 'sub-2',
                'user_id': 'user-orphan',
                'user_email': 'orphan@example.com',
                'plan': 'pro',
                'status': 'active',
                'stripe_subscription_id': 'sub_test2'
            }
        ]
    }
    
    # Mock users - first user exists, second doesn't
    def mock_user_scan(FilterExpression=None):
        if 'user-1' in str(FilterExpression):
            return {'Items': [{'id': 'user-1', 'name': 'Test User'}]}
        return {'Items': []}
    
    mock_tables['users'].scan.side_effect = mock_user_scan
    
    response = client.get('/api/subscriptions')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['count'] == 2
    assert data['orphaned_count'] == 1
    
    # Check enriched data
    subs = data['subscriptions']
    existing_sub = next(s for s in subs if s['user_id'] == 'user-1')
    orphaned_sub = next(s for s in subs if s['user_id'] == 'user-orphan')
    
    assert existing_sub['user_exists'] is True
    assert existing_sub['is_orphaned'] is False
    
    assert orphaned_sub['user_exists'] is False
    assert orphaned_sub['is_orphaned'] is True


def test_revenue_endpoint_includes_health_issues(client, mock_tables):
    """Test revenue endpoint includes health issues for orphaned records"""
    # Mock billing records - one orphaned
    mock_tables['billing'].scan.return_value = {
        'Items': [
            {
                'id': 'bill-1',
                'user_id': 'user-1',
                'amount': 100.0,
                'plan': 'ultimate',
                'created_at': '2025-01-01T00:00:00Z'
            },
            {
                'id': 'bill-2',
                'user_id': 'user-orphan',
                'amount': 50.0,
                'plan': 'pro',
                'created_at': '2025-01-02T00:00:00Z'
            }
        ]
    }
    
    # Mock users - first exists, second doesn't
    def mock_user_scan(FilterExpression=None, Limit=None):
        if 'user-1' in str(FilterExpression):
            return {'Items': [{'id': 'user-1'}]}
        return {'Items': []}
    
    mock_tables['users'].scan.side_effect = mock_user_scan
    
    response = client.get('/api/revenue')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['total_revenue'] == 150.0
    assert data['total_transactions'] == 2
    assert data['health_issues']['orphaned_revenue'] == 50.0
    assert data['health_issues']['orphaned_transactions'] == 1


def test_subscriptions_detects_duplicate_emails(client, mock_tables):
    """Test subscriptions endpoint detects duplicate email addresses"""
    # Mock subscriptions with duplicate email
    mock_tables['subscriptions'].scan.return_value = {
        'Items': [
            {
                'id': 'sub-1',
                'user_id': 'user-1',
                'user_email': 'duplicate@example.com',
                'plan': 'ultimate',
                'status': 'canceled',
                'stripe_subscription_id': 'sub_test1'
            },
            {
                'id': 'sub-2',
                'user_id': 'user-2',
                'user_email': 'duplicate@example.com',
                'plan': 'ultimate',
                'status': 'active',
                'stripe_subscription_id': 'sub_test2'
            }
        ]
    }
    
    # Mock users
    mock_tables['users'].scan.return_value = {'Items': []}
    
    response = client.get('/api/subscriptions')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['duplicate_emails']) == 1
    assert 'duplicate@example.com' in data['duplicate_emails']
    assert len(data['duplicate_emails']['duplicate@example.com']) == 2
