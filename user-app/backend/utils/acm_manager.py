"""
AWS Certificate Manager (ACM) Integration
Handles SSL certificate request, validation, and management for custom domains
"""
import os
import time
import boto3
from botocore.exceptions import ClientError

# Initialize ACM client (must use us-east-1 for CloudFront)
acm_client = boto3.client(
    'acm',
    region_name='us-east-1',  # CloudFront requires certificates in us-east-1
    endpoint_url=os.environ.get('ACM_ENDPOINT_URL')  # For LocalStack
)


def request_certificate(domain, validation_method='DNS'):
    """
    Request an SSL certificate from ACM for a custom domain
    
    Args:
        domain: Domain name (e.g., gallery.yourstudio.com)
        validation_method: 'DNS' or 'EMAIL' (default: DNS)
    
    Returns:
        dict: {
            'success': bool,
            'certificate_arn': str,
            'validation_records': list of DNS records needed for validation,
            'status': str,
            'error': str (if failed)
        }
    """
    try:
        print(f"Requesting ACM certificate for {domain}...")
        
        # Request certificate
        response = acm_client.request_certificate(
            DomainName=domain,
            ValidationMethod=validation_method,
            SubjectAlternativeNames=[domain],  # Include domain as SAN
            Tags=[
                {
                    'Key': 'Service',
                    'Value': 'Galerly'
                },
                {
                    'Key': 'Domain',
                    'Value': domain
                }
            ],
            Options={
                'CertificateTransparencyLoggingPreference': 'ENABLED'
            }
        )
        
        certificate_arn = response['CertificateArn']
        print(f"✓ Certificate requested: {certificate_arn}")
        
        # Get validation details
        time.sleep(2)  # Wait for ACM to prepare validation details
        validation_records = get_certificate_validation_records(certificate_arn)
        
        return {
            'success': True,
            'certificate_arn': certificate_arn,
            'validation_records': validation_records,
            'status': 'PENDING_VALIDATION',
            'validation_method': validation_method
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ACM error ({error_code}): {error_message}")
        
        return {
            'success': False,
            'error': f'{error_code}: {error_message}'
        }
    except Exception as e:
        print(f"Error requesting certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_certificate_validation_records(certificate_arn):
    """
    Get DNS validation records for a certificate
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        list: [
            {
                'name': str,  # DNS record name
                'type': str,  # DNS record type (CNAME)
                'value': str,  # DNS record value
                'status': str  # Validation status
            }
        ]
    """
    try:
        response = acm_client.describe_certificate(CertificateArn=certificate_arn)
        certificate = response['Certificate']
        
        validation_records = []
        
        for validation in certificate.get('DomainValidationOptions', []):
            if 'ResourceRecord' in validation:
                record = validation['ResourceRecord']
                validation_records.append({
                    'name': record.get('Name', ''),
                    'type': record.get('Type', 'CNAME'),
                    'value': record.get('Value', ''),
                    'status': validation.get('ValidationStatus', 'PENDING_VALIDATION'),
                    'domain': validation.get('DomainName', '')
                })
        
        return validation_records
        
    except Exception as e:
        print(f"Error getting validation records: {str(e)}")
        return []


def get_certificate_status(certificate_arn):
    """
    Get current status of an ACM certificate
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        dict: {
            'success': bool,
            'status': str,  # PENDING_VALIDATION, ISSUED, INACTIVE, EXPIRED, etc.
            'domain': str,
            'issued_at': str,
            'not_after': str,
            'validation_records': list,
            'in_use': bool,
            'error': str (if failed)
        }
    """
    try:
        response = acm_client.describe_certificate(CertificateArn=certificate_arn)
        certificate = response['Certificate']
        
        return {
            'success': True,
            'status': certificate.get('Status'),
            'domain': certificate.get('DomainName'),
            'issued_at': certificate.get('IssuedAt').isoformat() if certificate.get('IssuedAt') else None,
            'not_after': certificate.get('NotAfter').isoformat() if certificate.get('NotAfter') else None,
            'validation_records': get_certificate_validation_records(certificate_arn),
            'in_use': len(certificate.get('InUseBy', [])) > 0,
            'type': certificate.get('Type'),
            'key_algorithm': certificate.get('KeyAlgorithm')
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def check_certificate_validation(certificate_arn, max_attempts=60, delay=10):
    """
    Poll certificate validation status until validated or timeout
    
    Args:
        certificate_arn: ARN of the certificate
        max_attempts: Maximum number of polling attempts (default: 60)
        delay: Delay between attempts in seconds (default: 10)
    
    Returns:
        dict: {
            'success': bool,
            'validated': bool,
            'status': str,
            'attempts': int,
            'error': str (if failed)
        }
    """
    try:
        for attempt in range(max_attempts):
            status_result = get_certificate_status(certificate_arn)
            
            if not status_result['success']:
                return {
                    'success': False,
                    'validated': False,
                    'error': status_result.get('error')
                }
            
            status = status_result['status']
            
            if status == 'ISSUED':
                print(f"✓ Certificate validated and issued after {attempt + 1} attempts")
                return {
                    'success': True,
                    'validated': True,
                    'status': status,
                    'attempts': attempt + 1
                }
            elif status in ['EXPIRED', 'REVOKED', 'FAILED', 'VALIDATION_TIMED_OUT']:
                return {
                    'success': False,
                    'validated': False,
                    'status': status,
                    'error': f'Certificate validation failed with status: {status}',
                    'attempts': attempt + 1
                }
            
            # Still pending, wait and retry
            if attempt < max_attempts - 1:
                time.sleep(delay)
        
        # Timeout
        return {
            'success': False,
            'validated': False,
            'status': 'TIMEOUT',
            'error': f'Certificate validation timed out after {max_attempts * delay} seconds',
            'attempts': max_attempts
        }
        
    except Exception as e:
        print(f"Error checking certificate validation: {str(e)}")
        return {
            'success': False,
            'validated': False,
            'error': str(e)
        }


def delete_certificate(certificate_arn):
    """
    Delete an ACM certificate
    Note: Cannot delete certificates that are in use by CloudFront
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        dict: {'success': bool, 'error': str}
    """
    try:
        # Check if certificate is in use
        status_result = get_certificate_status(certificate_arn)
        if status_result.get('in_use'):
            return {
                'success': False,
                'error': 'Certificate is in use and cannot be deleted. Remove it from CloudFront first.'
            }
        
        # Delete certificate
        acm_client.delete_certificate(CertificateArn=certificate_arn)
        
        print(f"✓ Certificate deleted: {certificate_arn}")
        
        return {'success': True}
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"Error deleting certificate: {error_message}")
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        print(f"Error deleting certificate: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def list_certificates(statuses=None):
    """
    List ACM certificates with optional status filter
    
    Args:
        statuses: List of statuses to filter by (e.g., ['ISSUED', 'PENDING_VALIDATION'])
    
    Returns:
        dict: {
            'success': bool,
            'certificates': list,
            'count': int,
            'error': str (if failed)
        }
    """
    try:
        params = {}
        if statuses:
            params['CertificateStatuses'] = statuses
        
        response = acm_client.list_certificates(**params)
        certificates = response.get('CertificateSummaryList', [])
        
        return {
            'success': True,
            'certificates': certificates,
            'count': len(certificates)
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def renew_certificate(certificate_arn):
    """
    Renew an ACM certificate (AWS handles auto-renewal for DNS-validated certs)
    This function checks if renewal is needed and forces renewal if necessary
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        dict: {
            'success': bool,
            'renewal_needed': bool,
            'status': str,
            'error': str (if failed)
        }
    """
    try:
        # Get certificate details
        response = acm_client.describe_certificate(CertificateArn=certificate_arn)
        certificate = response['Certificate']
        
        renewal_summary = certificate.get('RenewalSummary', {})
        renewal_status = renewal_summary.get('RenewalStatus', 'NOT_APPLICABLE')
        
        # ACM auto-renews DNS-validated certificates
        # Manual renewal is not typically needed
        
        return {
            'success': True,
            'renewal_needed': renewal_status == 'PENDING_AUTO_RENEWAL',
            'renewal_status': renewal_status,
            'status': certificate.get('Status'),
            'not_after': certificate.get('NotAfter').isoformat() if certificate.get('NotAfter') else None
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
