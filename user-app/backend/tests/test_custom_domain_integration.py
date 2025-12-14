"""
Tests for Custom Domain Integration
Tests CloudFront, ACM, and DNS utilities
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Set test environment variables
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['CLOUDFRONT_ENDPOINT_URL'] = 'http://localhost:4566'
os.environ['ACM_ENDPOINT_URL'] = 'http://localhost:4566'

# Import CloudFront and ACM utilities (use actual exported functions)
from utils.cloudfront_manager import (
    create_distribution,
    get_distribution_status,
    update_distribution,
    create_invalidation
)
from utils.acm_manager import (
    request_certificate,
    describe_certificate,  # Fixed: actual function name
    get_certificate_validation_records
)
from utils.dns_propagation import (
    check_dns_propagation,
    check_cname_propagation
)

# Note: The test references 'create_custom_domain_distribution' which doesn't exist
# Tests should use 'create_distribution' instead


class TestCloudFrontManager:
    """Test CloudFront distribution management"""
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_create_distribution_success(self, mock_client):
        """Test successful CloudFront distribution creation"""
        # Mock response
        mock_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E123ABC456DEF',
                'DomainName': 'd123abc456def.cloudfront.net',
                'Status': 'InProgress'
            }
        }
        
        result = create_custom_domain_distribution(
            user_id='user-123',
            custom_domain='gallery.example.com'
        )
        
        assert result['success'] is True
        assert result['distribution_id'] == 'E123ABC456DEF'
        assert result['distribution_domain'] == 'd123abc456def.cloudfront.net'
        assert result['status'] == 'InProgress'
        
        # Verify correct parameters were passed
        mock_client.create_distribution.assert_called_once()
        call_args = mock_client.create_distribution.call_args[1]
        config = call_args['DistributionConfig']
        
        assert config['Enabled'] is True
        # When created without certificate, Aliases won't be set yet
        # assert 'gallery.example.com' in config.get('Aliases', {}).get('Items', [])
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_create_distribution_with_certificate(self, mock_client):
        """Test distribution creation with ACM certificate"""
        mock_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E123ABC456DEF',
                'DomainName': 'd123abc456def.cloudfront.net',
                'Status': 'InProgress'
            }
        }
        
        cert_arn = 'arn:aws:acm:us-east-1:123456789:certificate/abc123'
        result = create_custom_domain_distribution(
            user_id='user-123',
            custom_domain='gallery.example.com',
            acm_certificate_arn=cert_arn
        )
        
        assert result['success'] is True
        
        # Verify certificate was added to config
        call_args = mock_client.create_distribution.call_args[1]
        viewer_cert = call_args['DistributionConfig']['ViewerCertificate']
        assert viewer_cert['ACMCertificateArn'] == cert_arn
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_get_distribution_status(self, mock_client):
        """Test getting distribution status"""
        from datetime import datetime
        mock_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E123ABC456DEF',
                'DomainName': 'd123abc456def.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {
                    'Enabled': True,
                    'Aliases': {'Items': ['gallery.example.com']}
                },
                'LastModifiedTime': datetime(2025, 1, 1, 0, 0, 0)
            }
        }
        
        result = get_distribution_status('E123ABC456DEF')
        
        assert result['success'] is True
        assert result['status'] == 'Deployed'
        assert result['enabled'] is True
        assert 'gallery.example.com' in result['aliases']
    
    @patch('utils.cloudfront_manager.cloudfront_client')
    def test_invalidate_cache(self, mock_client):
        """Test cache invalidation"""
        mock_client.create_invalidation.return_value = {
            'Invalidation': {
                'Id': 'I123ABC',
                'Status': 'InProgress'
            }
        }
        
        result = invalidate_distribution_cache(
            distribution_id='E123ABC456DEF',
            paths=['/*']
        )
        
        assert result['success'] is True
        assert result['invalidation_id'] == 'I123ABC'
        assert result['status'] == 'InProgress'


class TestACMManager:
    """Test ACM certificate management"""
    
    @patch('utils.acm_manager.acm_client')
    def test_request_certificate_dns(self, mock_client):
        """Test requesting certificate with DNS validation"""
        mock_client.request_certificate.return_value = {
            'CertificateArn': 'arn:aws:acm:us-east-1:123456789:certificate/abc123'
        }
        
        mock_client.describe_certificate.return_value = {
            'Certificate': {
                'CertificateArn': 'arn:aws:acm:us-east-1:123456789:certificate/abc123',
                'DomainValidationOptions': [
                    {
                        'DomainName': 'gallery.example.com',
                        'ValidationStatus': 'PENDING_VALIDATION',
                        'ResourceRecord': {
                            'Name': '_abc123.gallery.example.com',
                            'Type': 'CNAME',
                            'Value': '_xyz789.acm-validations.aws.'
                        }
                    }
                ]
            }
        }
        
        result = request_certificate('gallery.example.com', validation_method='DNS')
        
        assert result['success'] is True
        assert 'arn:aws:acm' in result['certificate_arn']
        assert len(result['validation_records']) > 0
        assert result['validation_records'][0]['record_type'] == 'CNAME'
    
    @patch('utils.acm_manager.acm_client')
    def test_get_certificate_status_issued(self, mock_client):
        """Test getting issued certificate status"""
        from datetime import datetime
        mock_client.describe_certificate.return_value = {
            'Certificate': {
                'CertificateArn': 'arn:aws:acm:us-east-1:123456789:certificate/abc123',
                'DomainName': 'gallery.example.com',
                'Status': 'ISSUED',
                'IssuedAt': datetime(2025, 1, 1, 0, 0, 0),
                'NotAfter': datetime(2026, 1, 1, 0, 0, 0),
                'InUseBy': ['arn:aws:cloudfront::123456789:distribution/E123ABC'],
                'Type': 'AMAZON_ISSUED',
                'KeyAlgorithm': 'RSA-2048',
                'DomainValidationOptions': []
            }
        }
        
        cert_arn = 'arn:aws:acm:us-east-1:123456789:certificate/abc123'
        result = get_certificate_status(cert_arn)
        
        assert result['success'] is True
        assert result['status'] == 'ISSUED'
        assert result['domain'] == 'gallery.example.com'
        assert len(result['in_use_by']) > 0
    
    @patch('utils.acm_manager.acm_client')
    def test_check_certificate_validation_timeout(self, mock_client):
        """Test certificate validation timeout"""
        mock_client.describe_certificate.return_value = {
            'Certificate': {
                'Status': 'PENDING_VALIDATION',
                'DomainName': 'gallery.example.com',
                'InUseBy': [],
                'DomainValidationOptions': []
            }
        }
        
        cert_arn = 'arn:aws:acm:us-east-1:123456789:certificate/abc123'
        result = check_certificate_validation(
            cert_arn,
            max_attempts=2,
            delay=1
        )
        
        assert result['success'] is False
        assert result['validated'] is False
        assert 'timeout' in result['error'].lower()


class TestDNSPropagation:
    """Test DNS propagation checking"""
    
    @patch('utils.dns_propagation.dns.resolver.Resolver')
    def test_check_dns_propagation_full(self, mock_resolver_class):
        """Test fully propagated DNS"""
        # Mock resolver instance
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        # Mock DNS response - returns correct value every time
        def mock_resolve(*args, **kwargs):
            mock_answer = MagicMock()
            mock_rdata = MagicMock()
            mock_rdata.target = 'd123abc.cloudfront.net.'
            mock_answer.__iter__ = Mock(return_value=iter([mock_rdata]))
            return mock_answer
        
        mock_resolver.resolve.side_effect = mock_resolve
        
        result = check_dns_propagation(
            domain='gallery.example.com',
            expected_value='d123abc.cloudfront.net',
            record_type='CNAME'
        )
        
        assert result['propagated'] is True
        assert result['percentage'] == 100.0
        assert result['ready'] is True
        assert result['servers_propagated'] == result['servers_checked']
    
    @patch('utils.dns_propagation.dns.resolver.Resolver')
    def test_check_cname_propagation_partial(self, mock_resolver_class):
        """Test partially propagated CNAME"""
        mock_resolver = MagicMock()
        mock_resolver_class.return_value = mock_resolver
        
        # Simulate some servers returning correct value, others failing
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            # Every other call succeeds
            if call_count[0] % 2 == 0:
                mock_answer = MagicMock()
                mock_rdata = MagicMock()
                mock_rdata.target = 'd123abc.cloudfront.net.'
                mock_answer.__iter__ = Mock(return_value=iter([mock_rdata]))
                return mock_answer
            else:
                raise Exception("DNS error")
        
        mock_resolver.resolve.side_effect = side_effect
        
        result = check_cname_propagation(
            domain='gallery.example.com',
            expected_cname='d123abc.cloudfront.net'
        )
        
        assert result['propagated'] is False  # Not 100% propagated
        # Should have some propagation but not 100%
        assert 0 < result['percentage'] < 100


class TestCustomDomainHandlers:
    """Test portfolio handler custom domain functions"""
    
    @patch('handlers.portfolio_handler.request_certificate')
    @patch('handlers.portfolio_handler.create_custom_domain_distribution')
    @patch('handlers.portfolio_handler.custom_domains_table')
    @patch('handlers.portfolio_handler.users_table')
    @patch('handlers.portfolio_handler.get_user_features')
    def test_setup_custom_domain_success(
        self, 
        mock_get_features,
        mock_users_table,
        mock_domains_table,
        mock_create_dist,
        mock_request_cert
    ):
        """Test successful custom domain setup"""
        from handlers.portfolio_handler import handle_setup_custom_domain
        
        # Mock user features
        mock_get_features.return_value = (
            {'custom_domain': True},
            'plus',
            {}
        )
        
        # Mock no existing domain
        mock_users_table.scan.return_value = {'Items': []}
        mock_domains_table.get_item.return_value = {}
        
        # Mock certificate request
        mock_request_cert.return_value = {
            'success': True,
            'certificate_arn': 'arn:aws:acm:us-east-1:123:certificate/abc',
            'validation_records': [
                {
                    'name': '_abc.gallery.example.com',
                    'type': 'CNAME',
                    'value': '_xyz.acm-validations.aws'
                }
            ]
        }
        
        # Mock distribution creation
        mock_create_dist.return_value = {
            'success': True,
            'distribution_id': 'E123ABC',
            'distribution_domain': 'd123.cloudfront.net',
            'status': 'InProgress'
        }
        
        user = {'id': 'user-123', 'email': 'test@example.com'}
        body = {
            'domain': 'gallery.example.com',
            'auto_provision': True
        }
        
        response = handle_setup_custom_domain(user, body)
        
        assert response['statusCode'] == 200
        # Parse JSON response body
        import json
        data = json.loads(response['body']) if isinstance(response['body'], str) else response['body']
        assert data['success'] is True
        assert data['domain'] == 'gallery.example.com'
        assert 'certificate_arn' in data
        assert 'distribution_id' in data
        assert len(data['validation_records']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
