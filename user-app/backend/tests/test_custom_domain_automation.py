"""
Tests for Custom Domain Automation
Refactored to test actual handler implementation
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
        'role': 'photographer',
        'plan': 'plus'
    }


def test_setup_custom_domain_success(mock_user):
    """Test custom domain setup handler"""
    with patch('handlers.subscription_handler.get_user_features') as mock_features, \
         patch('utils.cloudfront_manager.create_distribution') as mock_create, \
         patch('utils.acm_manager.request_certificate') as mock_cert, \
         patch('handlers.portfolio_handler.users_table') as mock_users, \
         patch('handlers.portfolio_handler.custom_domains_table') as mock_domains:
        
        mock_features.return_value = ({'custom_domain': True}, 'plus', 'Plus Plan')
        
        # Mock domain check
        mock_users.scan.return_value = {'Items': []}
        mock_domains.get_item.return_value = {}
        
        mock_cert.return_value = {
            'certificate_arn': 'arn:aws:acm:us-east-1:123:cert/abc',
            'domain': 'gallery.example.com',
            'status': 'PENDING_VALIDATION',
            'validation_records': [{'name': '_abc.example.com', 'type': 'CNAME', 'value': '_xyz.acm.aws'}]
        }
        
        # Fix mock to return dict directly, not nested
        mock_create_result = {
            'distribution_id': 'E123ABC',
            'domain_name': 'd123.cloudfront.net',
            'status': 'InProgress',
            'arn': 'arn:aws:cloudfront::123:distribution/E123ABC'
        }
        mock_create.return_value = mock_create_result
        
        mock_users.update_item.return_value = {}
        mock_domains.put_item.return_value = {}
        
        body = {'domain': 'gallery.example.com'}
        result = handle_setup_custom_domain(mock_user, body)
        
        assert result['statusCode'] == 200
        body_data = json.loads(result['body'])
        assert 'distribution_id' in body_data


def test_check_custom_domain_status(mock_user):
    """Test custom domain status check"""
    with patch('handlers.subscription_handler.get_user_features') as mock_features, \
         patch('handlers.portfolio_handler.custom_domains_table') as mock_domains, \
         patch('utils.acm_manager.describe_certificate') as mock_cert, \
         patch('utils.cloudfront_manager.get_distribution_status') as mock_dist, \
         patch('utils.dns_propagation.check_dns_propagation') as mock_dns:
        
        mock_features.return_value = ({'custom_domain': True}, 'plus', 'Plus Plan')
        
        mock_domains.get_item.return_value = {
            'Item': {
                'user_id': 'test-user-123',
                'domain': 'gallery.example.com',
                'distribution_id': 'E123ABC',
                'certificate_arn': 'arn:aws:acm:us-east-1:123:cert/abc',
                'distribution_domain': 'd123.cloudfront.net',
                'status': 'deployed'
            }
        }
        
        mock_cert.return_value = {
            'status': 'ISSUED',
            'issued': True,
            'validation_records': []
        }
        
        mock_dist.return_value = {
            'domain_name': 'd123.cloudfront.net',
            'status': 'Deployed',
            'deployed': True,
            'enabled': True
        }
        
        mock_dns.return_value = {
            'propagated': True,
            'percentage': 100.0,
            'ready': True
        }
        
        result = handle_check_custom_domain_status(mock_user, 'gallery.example.com')
        
        assert result['statusCode'] == 200


def test_refresh_certificate_pending(mock_user):
    """Test certificate refresh when pending"""
    with patch('handlers.subscription_handler.get_user_features') as mock_features, \
         patch('handlers.portfolio_handler.custom_domains_table') as mock_domains, \
         patch('handlers.portfolio_handler.describe_certificate') as mock_describe:
        
        mock_features.return_value = ({'custom_domain': True}, 'plus', 'Plus Plan')
        
        mock_domains.get_item.return_value = {
            'Item': {
                'user_id': 'test-user-123',
                'domain': 'gallery.example.com',
                'certificate_arn': 'arn:aws:acm:us-east-1:123:cert/abc',
                'distribution_id': 'E123ABC'
            }
        }
        
        mock_describe.return_value = {
            'status': 'PENDING_VALIDATION',
            'validation_records': []
        }
        
        result = handle_refresh_custom_domain_certificate(mock_user, 'gallery.example.com')
        
        assert result['statusCode'] == 200


def test_refresh_certificate_issued(mock_user):
    """Test certificate refresh when issued"""
    with patch('handlers.subscription_handler.get_user_features') as mock_features, \
         patch('handlers.portfolio_handler.custom_domains_table') as mock_domains, \
         patch('handlers.portfolio_handler.describe_certificate') as mock_describe, \
         patch('handlers.portfolio_handler.update_distribution') as mock_update:
        
        mock_features.return_value = ({'custom_domain': True}, 'plus', 'Plus Plan')
        
        mock_domains.get_item.return_value = {
            'Item': {
                'user_id': 'test-user-123',
                'domain': 'gallery.example.com',
                'certificate_arn': 'arn:aws:acm:us-east-1:123:cert/abc',
                'distribution_id': 'E123ABC'
            }
        }
        
        mock_describe.return_value = {
            'status': 'ISSUED'
        }
        
        mock_update.return_value = {}
        mock_domains.update_item.return_value = {}
        
        result = handle_refresh_custom_domain_certificate(mock_user, 'gallery.example.com')
        
        assert result['statusCode'] == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
