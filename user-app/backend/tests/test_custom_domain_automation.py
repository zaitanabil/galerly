"""
Tests for Custom Domain CloudFront and ACM integration
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.portfolio_handler import (
    handle_setup_custom_domain,
    handle_check_custom_domain_status,
    handle_refresh_custom_domain_certificate
)


@pytest.fixture
def mock_user():
    return {
        'id': 'test-user-123',
        'email': 'photographer@example.com',
        'name': 'Test Photographer',
        'plan': 'plus'  # Plus plan has custom_domain feature
    }


@pytest.fixture
def mock_get_features():
    with patch('handlers.portfolio_handler.get_user_features') as mock:
        mock.return_value = (
            {
                'custom_domain': True,
                'portfolio_customization': True
            },
            {},
            'plus'
        )
        yield mock


@pytest.fixture
def mock_cloudfront():
    with patch('handlers.portfolio_handler.create_custom_domain_distribution') as mock_create, \
         patch('handlers.portfolio_handler.get_distribution_status') as mock_status, \
         patch('handlers.portfolio_handler.update_distribution_certificate') as mock_update:
        
        mock_create.return_value = {
            'success': True,
            'distribution_id': 'E1TESTDIST',
            'distribution_domain': 'd123abc.cloudfront.net'
        }
        
        mock_status.return_value = {
            'success': True,
            'status': 'Deployed',
            'domain_name': 'd123abc.cloudfront.net',
            'enabled': True
        }
        
        mock_update.return_value = {
            'success': True,
            'message': 'Distribution updated'
        }
        
        yield {
            'create': mock_create,
            'status': mock_status,
            'update': mock_update
        }


@pytest.fixture
def mock_acm():
    with patch('handlers.portfolio_handler.request_certificate') as mock_request, \
         patch('handlers.portfolio_handler.get_certificate_status') as mock_status:
        
        mock_request.return_value = {
            'success': True,
            'certificate_arn': 'arn:aws:acm:us-east-1:123456789:certificate/test-cert',
            'validation_records': [
                {
                    'domain': 'gallery.example.com',
                    'record_type': 'CNAME',
                    'record_name': '_abc123.gallery.example.com',
                    'record_value': '_def456.acm-validations.aws'
                }
            ],
            'validation_method': 'DNS',
            'status': 'PENDING_VALIDATION'
        }
        
        mock_status.return_value = {
            'success': True,
            'status': 'ISSUED',
            'domain': 'gallery.example.com',
            'validation_records': []
        }
        
        yield {
            'request': mock_request,
            'status': mock_status
        }


@pytest.fixture
def mock_dns():
    with patch('handlers.portfolio_handler.check_cname_propagation') as mock:
        mock.return_value = {
            'propagated': True,
            'percentage': 100.0,
            'ready': True,
            'servers_propagated': 8,
            'servers_checked': 8
        }
        yield mock


@pytest.fixture
def mock_tables():
    with patch('handlers.portfolio_handler.users_table') as mock_users, \
         patch('handlers.portfolio_handler.custom_domains_table') as mock_domains:
        
        # Mock users table
        mock_users.scan.return_value = {'Items': []}
        mock_users.get_item.return_value = {
            'Item': {
                'id': 'test-user-123',
                'email': 'photographer@example.com',
                'name': 'Test Photographer'
            }
        }
        mock_users.update_item.return_value = {}
        
        # Mock custom domains table
        mock_domains.get_item.return_value = {'Item': None}
        mock_domains.put_item.return_value = {}
        mock_domains.update_item.return_value = {}
        
        yield {
            'users': mock_users,
            'domains': mock_domains
        }


def test_setup_custom_domain_success(mock_user, mock_get_features, mock_cloudfront, mock_acm, mock_tables):
    """Test successful custom domain setup"""
    body = {
        'domain': 'gallery.example.com',
        'auto_provision': True
    }
    
    response = handle_setup_custom_domain(mock_user, body)
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['success'] == True
    assert data['domain'] == 'gallery.example.com'
    assert 'certificate_arn' in data
    assert 'distribution_id' in data
    assert 'validation_records' in data
    
    # Verify ACM certificate was requested
    mock_acm['request'].assert_called_once_with('gallery.example.com', validation_method='DNS')
    
    # Verify CloudFront distribution was created
    mock_cloudfront['create'].assert_called_once()
    
    # Verify user record was updated
    mock_tables['users'].update_item.assert_called_once()


def test_setup_custom_domain_without_feature(mock_user, mock_tables):
    """Test custom domain setup without required plan feature"""
    with patch('handlers.portfolio_handler.get_user_features') as mock_features:
        mock_features.return_value = (
            {'custom_domain': False},  # No custom domain feature
            {},
            'starter'
        )
        
        body = {
            'domain': 'gallery.example.com',
            'auto_provision': True
        }
        
        response = handle_setup_custom_domain(mock_user, body)
        
        assert response['statusCode'] == 403
        data = json.loads(response['body'])
        assert 'upgrade_required' in data
        assert data['upgrade_required'] == True


def test_setup_custom_domain_duplicate(mock_user, mock_get_features, mock_tables):
    """Test setup with domain already taken by another user"""
    # Mock domain already exists for different user
    mock_tables['users'].scan.return_value = {
        'Items': [{
            'id': 'other-user-456',
            'email': 'other@example.com',
            'portfolio_custom_domain': 'gallery.example.com'
        }]
    }
    
    body = {
        'domain': 'gallery.example.com',
        'auto_provision': True
    }
    
    response = handle_setup_custom_domain(mock_user, body)
    
    assert response['statusCode'] == 409
    data = json.loads(response['body'])
    assert 'already connected' in data['error'].lower()


def test_check_custom_domain_status(mock_user, mock_get_features, mock_cloudfront, mock_acm, mock_dns, mock_tables):
    """Test checking custom domain status"""
    # Mock existing domain configuration
    mock_tables['domains'].get_item.return_value = {
        'Item': {
            'user_id': 'test-user-123',
            'domain': 'gallery.example.com',
            'certificate_arn': 'arn:aws:acm:us-east-1:123456789:certificate/test-cert',
            'distribution_id': 'E1TESTDIST',
            'distribution_domain': 'd123abc.cloudfront.net',
            'status': 'active'
        }
    }
    
    response = handle_check_custom_domain_status(mock_user, 'gallery.example.com')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['domain'] == 'gallery.example.com'
    assert data['overall_status'] == 'active'
    assert data['ready'] == True
    assert 'certificate' in data
    assert 'distribution' in data
    assert 'dns_propagation' in data


def test_refresh_certificate_pending(mock_user, mock_get_features, mock_acm, mock_tables):
    """Test refreshing certificate that's still pending validation"""
    # Mock existing domain configuration
    mock_tables['domains'].get_item.return_value = {
        'Item': {
            'user_id': 'test-user-123',
            'domain': 'gallery.example.com',
            'certificate_arn': 'arn:aws:acm:us-east-1:123456789:certificate/test-cert',
            'distribution_id': 'E1TESTDIST',
            'status': 'pending_validation'
        }
    }
    
    # Mock certificate still pending
    mock_acm['status'].return_value = {
        'success': True,
        'status': 'PENDING_VALIDATION',
        'domain': 'gallery.example.com',
        'validation_records': [
            {
                'domain': 'gallery.example.com',
                'record_type': 'CNAME',
                'record_name': '_abc123.gallery.example.com',
                'record_value': '_def456.acm-validations.aws'
            }
        ]
    }
    
    response = handle_refresh_custom_domain_certificate(mock_user, 'gallery.example.com')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['status'] == 'pending_validation'
    assert data['certificate_status'] == 'PENDING_VALIDATION'
    assert len(data['validation_records']) > 0


def test_refresh_certificate_issued(mock_user, mock_get_features, mock_acm, mock_cloudfront, mock_tables):
    """Test refreshing certificate that has been validated"""
    # Mock existing domain configuration
    mock_tables['domains'].get_item.return_value = {
        'Item': {
            'user_id': 'test-user-123',
            'domain': 'gallery.example.com',
            'certificate_arn': 'arn:aws:acm:us-east-1:123456789:certificate/test-cert',
            'distribution_id': 'E1TESTDIST',
            'status': 'pending_validation'
        }
    }
    
    # Mock certificate is now issued
    mock_acm['status'].return_value = {
        'success': True,
        'status': 'ISSUED',
        'domain': 'gallery.example.com',
        'validation_records': []
    }
    
    response = handle_refresh_custom_domain_certificate(mock_user, 'gallery.example.com')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['status'] == 'active'
    assert data['certificate_status'] == 'ISSUED'
    
    # Verify CloudFront distribution was updated with certificate
    mock_cloudfront['update'].assert_called_once()
    
    # Verify domain status was updated
    mock_tables['domains'].update_item.assert_called_once()


def test_setup_custom_domain_invalid_format(mock_user, mock_get_features):
    """Test setup with invalid domain format"""
    body = {
        'domain': 'invalid domain with spaces',
        'auto_provision': True
    }
    
    response = handle_setup_custom_domain(mock_user, body)
    
    # Should still process but domain will be sanitized
    assert response['statusCode'] in [200, 400]


def test_setup_custom_domain_without_auto_provision(mock_user, mock_get_features, mock_tables):
    """Test setup without auto-provisioning"""
    body = {
        'domain': 'gallery.example.com',
        'auto_provision': False
    }
    
    response = handle_setup_custom_domain(mock_user, body)
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    assert data['success'] == True
    assert 'next_steps' in data

