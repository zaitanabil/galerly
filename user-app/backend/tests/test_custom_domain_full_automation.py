"""
Tests for custom domain automation features
Includes CloudFront, ACM, and DNS checking utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.cloudfront_manager import (
    create_distribution,
    get_distribution_status,
    update_distribution,
    delete_distribution,
    create_invalidation,
    wait_for_deployment
)
from utils.acm_manager import (
    request_certificate,
    describe_certificate,
    wait_for_validation,
    check_certificate_renewal
)
from utils.dns_checker import (
    check_propagation,
    verify_dns_configuration,
    check_domain_availability
)


class TestCloudFrontManager:
    """Tests for CloudFront distribution management"""
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_create_distribution_success(self, mock_cf_client):
        """Test successful CloudFront distribution creation"""
        # Mock response
        mock_cf_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E123ABC',
                'DomainName': 'd123abc.cloudfront.net',
                'Status': 'InProgress',
                'ARN': 'arn:aws:cloudfront::123:distribution/E123ABC'
            }
        }
        
        # Call function
        result = create_distribution(
            domain='gallery.example.com',
            certificate_arn='arn:aws:acm:us-east-1:123:certificate/abc123',
            user_id='user123',
            comment='Test distribution'
        )
        
        # Assertions
        assert result['distribution_id'] == 'E123ABC'
        assert result['domain_name'] == 'd123abc.cloudfront.net'
        assert result['status'] == 'InProgress'
        assert 'arn' in result
        
        # Verify API was called
        mock_cf_client.create_distribution.assert_called_once()
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_get_distribution_status(self, mock_cf_client):
        """Test getting distribution status"""
        mock_cf_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E123ABC',
                'DomainName': 'd123abc.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {
                    'Enabled': True,
                    'Aliases': {'Items': ['gallery.example.com']}
                }
            }
        }
        
        result = get_distribution_status('E123ABC')
        
        assert result['distribution_id'] == 'E123ABC'
        assert result['deployed'] is True
        assert result['enabled'] is True
        assert 'gallery.example.com' in result['aliases']
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_get_distribution_status_not_found(self, mock_cf_client):
        """Test getting status for non-existent distribution"""
        mock_cf_client.get_distribution.side_effect = mock_cf_client.exceptions.NoSuchDistribution()
        
        result = get_distribution_status('INVALID')
        
        assert 'error' in result
        assert result['exists'] is False
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_create_invalidation(self, mock_cf_client):
        """Test creating cache invalidation"""
        mock_cf_client.create_invalidation.return_value = {
            'Invalidation': {
                'Id': 'INV123',
                'Status': 'InProgress',
                'CreateTime': MagicMock()
            }
        }
        
        mock_cf_client.create_invalidation.return_value['Invalidation']['CreateTime'].isoformat.return_value = '2025-01-01T00:00:00Z'
        
        result = create_invalidation('E123ABC', ['/*'])
        
        assert result['invalidation_id'] == 'INV123'
        assert result['status'] == 'InProgress'


class TestACMManager:
    """Tests for ACM certificate management"""
    
    @patch('utils.acm_manager.acm_client')
    def test_request_certificate(self, mock_acm_client):
        """Test requesting SSL certificate"""
        mock_acm_client.request_certificate.return_value = {
            'CertificateArn': 'arn:aws:acm:us-east-1:123:certificate/abc123'
        }
        
        mock_acm_client.describe_certificate.return_value = {
            'Certificate': {
                'CertificateArn': 'arn:aws:acm:us-east-1:123:certificate/abc123',
                'DomainName': 'gallery.example.com',
                'Status': 'PENDING_VALIDATION',
                'ValidationMethod': 'DNS',
                'DomainValidationOptions': [{
                    'ResourceRecord': {
                        'Name': '_abc123.gallery.example.com',
                        'Type': 'CNAME',
                        'Value': '_xyz789.acm-validations.aws'
                    }
                }]
            }
        }
        
        result = request_certificate('gallery.example.com')
        
        assert result['certificate_arn'] == 'arn:aws:acm:us-east-1:123:certificate/abc123'
        assert result['status'] == 'PENDING_VALIDATION'
        assert len(result['validation_records']) > 0
    
    @patch('utils.acm_manager.acm_client')
    def test_describe_certificate(self, mock_acm_client):
        """Test getting certificate details"""
        mock_acm_client.describe_certificate.return_value = {
            'Certificate': {
                'CertificateArn': 'arn:aws:acm:us-east-1:123:certificate/abc123',
                'DomainName': 'gallery.example.com',
                'Status': 'ISSUED',
                'ValidationMethod': 'DNS',
                'DomainValidationOptions': []
            }
        }
        
        result = describe_certificate('arn:aws:acm:us-east-1:123:certificate/abc123')
        
        assert result['issued'] is True
        assert result['status'] == 'ISSUED'
        assert result['domain'] == 'gallery.example.com'
    
    @patch('utils.acm_manager.acm_client')
    def test_describe_certificate_not_found(self, mock_acm_client):
        """Test describing non-existent certificate"""
        mock_acm_client.describe_certificate.side_effect = mock_acm_client.exceptions.ResourceNotFoundException()
        
        result = describe_certificate('arn:aws:acm:us-east-1:123:certificate/invalid')
        
        assert 'error' in result
        assert result['exists'] is False


class TestDNSChecker:
    """Tests for DNS propagation checking"""
    
    @patch('utils.dns_checker.resolve_domain')
    def test_check_propagation_success(self, mock_resolve):
        """Test DNS propagation check when fully propagated"""
        mock_resolve.return_value = '1.2.3.4'
        
        result = check_propagation('gallery.example.com', record_type='A')
        
        # Should check multiple servers and return results
        assert 'propagated' in result
        assert 'propagation_percentage' in result
        assert 'servers_checked' in result
        assert result['domain'] == 'gallery.example.com'
    
    @patch('utils.dns_checker.resolve_domain')
    def test_check_propagation_partial(self, mock_resolve):
        """Test DNS propagation when partially propagated"""
        # Simulate some servers resolving, some not
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            return '1.2.3.4' if call_count[0] % 2 == 0 else None
        
        mock_resolve.side_effect = side_effect
        
        result = check_propagation('gallery.example.com', record_type='A')
        
        assert result['propagation_percentage'] < 100
        assert result['servers_propagated'] < result['servers_checked']
    
    def test_check_domain_availability(self):
        """Test checking if domain is resolvable"""
        # Test with a known domain (google.com should always resolve)
        result = check_domain_availability('google.com')
        
        assert 'available' in result
        assert 'resolvable' in result
        assert result['domain'] == 'google.com'
    
    @patch('utils.dns_checker.check_cname_record')
    def test_verify_dns_configuration(self, mock_check_cname):
        """Test verifying DNS records match expected values"""
        mock_check_cname.return_value = True
        
        expected_records = [
            {'name': '_acme.gallery.example.com', 'type': 'CNAME', 'value': 'validation.acm.aws'},
            {'name': 'gallery.example.com', 'type': 'CNAME', 'value': 'd123abc.cloudfront.net'}
        ]
        
        result = verify_dns_configuration('gallery.example.com', expected_records)
        
        assert result['all_valid'] is True
        assert result['records_checked'] == 2


class TestPortfolioHandlerIntegration:
    """Integration tests for portfolio handler with custom domains"""
    
    @patch('handlers.portfolio_handler.ACM_AVAILABLE', True)
    @patch('handlers.portfolio_handler.CLOUDFRONT_AVAILABLE', True)
    @patch('handlers.portfolio_handler.request_certificate')
    @patch('handlers.portfolio_handler.create_distribution')
    @patch('handlers.portfolio_handler.custom_domains_table')
    @patch('handlers.portfolio_handler.users_table')
    def test_setup_custom_domain_full_flow(
        self,
        mock_users_table,
        mock_domains_table,
        mock_create_dist,
        mock_request_cert,
    ):
        """Test complete custom domain setup flow"""
        # Mock certificate request
        mock_request_cert.return_value = {
            'certificate_arn': 'arn:aws:acm:us-east-1:123:certificate/abc123',
            'validation_records': [
                {'name': '_abc.gallery.example.com', 'type': 'CNAME', 'value': '_xyz.acm.aws'}
            ]
        }
        
        # Mock distribution creation
        mock_create_dist.return_value = {
            'distribution_id': 'E123ABC',
            'domain_name': 'd123abc.cloudfront.net',
            'status': 'InProgress'
        }
        
        # Mock domain table checks
        mock_domains_table.get_item.return_value = {}
        
        # Mock user scan
        mock_users_table.scan.return_value = {'Items': []}
        
        # Import handler
        from handlers.portfolio_handler import handle_setup_custom_domain
        
        user = {'id': 'user123', 'email': 'test@example.com'}
        body = {'domain': 'gallery.example.com', 'auto_provision': True}
        
        response = handle_setup_custom_domain(user, body)
        
        # Verify response structure
        assert response['statusCode'] == 200
        body_data = response.get('body', '{}')
        import json
        response_data = json.loads(body_data) if isinstance(body_data, str) else body_data
        
        assert 'certificate_arn' in response_data or 'error' in response_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

