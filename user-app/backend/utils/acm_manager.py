"""
AWS Certificate Manager (ACM) Utility
Handles SSL certificate request and validation for custom domains
"""
import os
import boto3
import time
from typing import Dict, Any, List, Optional

# Get AWS configuration from environment
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# ACM client (must be in us-east-1 for CloudFront)
acm_client = boto3.client(
    'acm',
    region_name='us-east-1',
    endpoint_url=os.environ.get('ACM_ENDPOINT_URL') or AWS_ENDPOINT_URL
)


def request_certificate(domain: str, validation_method: str = 'DNS') -> Dict[str, Any]:
    """
    Request an SSL certificate from ACM
    
    Args:
        domain: Domain name for the certificate
        validation_method: DNS or EMAIL (DNS recommended)
    
    Returns:
        Dict containing certificate_arn and validation_records
    """
    
    try:
        # Request certificate
        response = acm_client.request_certificate(
            DomainName=domain,
            ValidationMethod=validation_method,
            Options={
                'CertificateTransparencyLoggingPreference': 'ENABLED'
            },
            Tags=[
                {
                    'Key': 'Service',
                    'Value': 'Galerly'
                },
                {
                    'Key': 'Domain',
                    'Value': domain
                }
            ]
        )
        
        certificate_arn = response['CertificateArn']
        
        # Wait a moment for validation options to be populated
        time.sleep(2)
        
        # Get certificate details including validation records
        cert_details = describe_certificate(certificate_arn)
        
        return {
            'certificate_arn': certificate_arn,
            'domain': domain,
            'status': cert_details.get('status', 'PENDING_VALIDATION'),
            'validation_method': validation_method,
            'validation_records': cert_details.get('validation_records', [])
        }
    
    except Exception as e:
        print(f"Error requesting certificate: {str(e)}")
        raise


def describe_certificate(certificate_arn: str) -> Dict[str, Any]:
    """
    Get details about a certificate
    
    Args:
        certificate_arn: ACM certificate ARN
    
    Returns:
        Dict containing certificate details
    """
    
    try:
        response = acm_client.describe_certificate(
            CertificateArn=certificate_arn
        )
        
        certificate = response['Certificate']
        
        # Extract validation records
        validation_records = []
        if 'DomainValidationOptions' in certificate:
            for option in certificate['DomainValidationOptions']:
                if 'ResourceRecord' in option:
                    record = option['ResourceRecord']
                    validation_records.append({
                        'name': record['Name'],
                        'type': record['Type'],
                        'value': record['Value']
                    })
        
        return {
            'certificate_arn': certificate['CertificateArn'],
            'domain': certificate['DomainName'],
            'status': certificate['Status'],
            'issued': certificate['Status'] == 'ISSUED',
            'validation_method': certificate.get('ValidationMethod'),
            'validation_records': validation_records,
            'created_at': certificate.get('CreatedAt').isoformat() if certificate.get('CreatedAt') else None,
            'issued_at': certificate.get('IssuedAt').isoformat() if certificate.get('IssuedAt') else None,
            'not_before': certificate.get('NotBefore').isoformat() if certificate.get('NotBefore') else None,
            'not_after': certificate.get('NotAfter').isoformat() if certificate.get('NotAfter') else None
        }
    
    except acm_client.exceptions.ResourceNotFoundException:
        return {
            'error': 'Certificate not found',
            'exists': False
        }
    
    except Exception as e:
        print(f"Error describing certificate: {str(e)}")
        raise


def list_certificates(
    statuses: Optional[List[str]] = None,
    domain_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List ACM certificates
    
    Args:
        statuses: Filter by status (PENDING_VALIDATION, ISSUED, INACTIVE, etc.)
        domain_filter: Filter by domain name
    
    Returns:
        List of certificate summaries
    """
    
    try:
        params = {}
        if statuses:
            params['CertificateStatuses'] = statuses
        
        response = acm_client.list_certificates(**params)
        
        certificates = []
        for cert in response.get('CertificateSummaryList', []):
            # Apply domain filter if specified
            if domain_filter and domain_filter not in cert['DomainName']:
                continue
            
            certificates.append({
                'certificate_arn': cert['CertificateArn'],
                'domain': cert['DomainName'],
                'status': cert.get('Status'),
                'type': cert.get('Type')
            })
        
        return certificates
    
    except Exception as e:
        print(f"Error listing certificates: {str(e)}")
        raise


def delete_certificate(certificate_arn: str) -> Dict[str, Any]:
    """
    Delete an ACM certificate
    
    Args:
        certificate_arn: ACM certificate ARN
    
    Returns:
        Dict containing deletion status
    """
    
    try:
        acm_client.delete_certificate(
            CertificateArn=certificate_arn
        )
        
        return {
            'certificate_arn': certificate_arn,
            'deleted': True
        }
    
    except acm_client.exceptions.ResourceInUseException:
        return {
            'certificate_arn': certificate_arn,
            'deleted': False,
            'error': 'Certificate is in use by CloudFront distribution'
        }
    
    except Exception as e:
        print(f"Error deleting certificate: {str(e)}")
        raise


def wait_for_validation(
    certificate_arn: str,
    max_wait_seconds: int = 1800
) -> bool:
    """
    Wait for a certificate to be validated and issued
    
    Args:
        certificate_arn: ACM certificate ARN
        max_wait_seconds: Maximum time to wait (default 30 minutes)
    
    Returns:
        True if issued, False if timeout or failure
    """
    
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait_seconds:
        cert_details = describe_certificate(certificate_arn)
        
        status = cert_details.get('status')
        
        if status == 'ISSUED':
            return True
        
        if status in ['FAILED', 'VALIDATION_TIMED_OUT', 'REVOKED']:
            return False
        
        # Check every 30 seconds
        time.sleep(30)
    
    return False


def check_certificate_renewal(certificate_arn: str) -> Dict[str, Any]:
    """
    Check if a certificate is due for renewal
    
    Args:
        certificate_arn: ACM certificate ARN
    
    Returns:
        Dict containing renewal status and days until expiration
    """
    
    try:
        cert_details = describe_certificate(certificate_arn)
        
        if not cert_details.get('not_after'):
            return {
                'needs_renewal': False,
                'error': 'Certificate expiration date not available'
            }
        
        from datetime import datetime
        
        not_after = datetime.fromisoformat(cert_details['not_after'].replace('Z', '+00:00'))
        now = datetime.now(not_after.tzinfo)
        days_until_expiry = (not_after - now).days
        
        # ACM auto-renews DNS-validated certificates
        # Flag if less than 30 days remaining
        needs_renewal = days_until_expiry < 30
        
        return {
            'certificate_arn': certificate_arn,
            'days_until_expiry': days_until_expiry,
            'needs_renewal': needs_renewal,
            'expiry_date': cert_details['not_after'],
            'auto_renewal_enabled': cert_details.get('validation_method') == 'DNS'
        }
    
    except Exception as e:
        print(f"Error checking certificate renewal: {str(e)}")
        raise


def get_certificate_validation_records(certificate_arn: str) -> List[Dict[str, str]]:
    """
    Get DNS validation records for a certificate
    
    Args:
        certificate_arn: ACM certificate ARN
    
    Returns:
        List of DNS records needed for validation
    """
    
    cert_details = describe_certificate(certificate_arn)
    return cert_details.get('validation_records', [])
