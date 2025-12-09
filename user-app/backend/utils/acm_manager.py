"""
AWS Certificate Manager (ACM) Integration
Automates SSL/TLS certificate request and validation for custom domains
"""
import os
import boto3
from datetime import datetime

# Initialize ACM client in us-east-1 (required for CloudFront certificates)
acm_client = boto3.client(
    'acm',
    region_name='us-east-1',  # CloudFront requires certificates in us-east-1
    endpoint_url=os.environ.get('AWS_ENDPOINT_URL') if os.environ.get('AWS_ENDPOINT_URL') else None,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID') if os.environ.get('AWS_ENDPOINT_URL') else None,
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY') if os.environ.get('AWS_ENDPOINT_URL') else None
)


def request_certificate(domain, validation_method='DNS', subject_alternative_names=None):
    """
    Request an SSL certificate from AWS Certificate Manager
    
    Args:
        domain: Primary domain name (e.g., gallery.yourstudio.com)
        validation_method: 'DNS' or 'EMAIL'
        subject_alternative_names: Optional list of additional domains (e.g., ['*.yourstudio.com'])
    
    Returns:
        dict: {
            'success': bool,
            'certificate_arn': str,
            'validation_records': list,  # DNS records needed for validation
            'error': str (if failed)
        }
    """
    try:
        # Prepare domain validation options
        domain_validation_options = [{
            'DomainName': domain,
            'ValidationDomain': domain
        }]
        
        # Add SANs if provided
        sans = [domain]
        if subject_alternative_names:
            sans.extend(subject_alternative_names)
            for san in subject_alternative_names:
                domain_validation_options.append({
                    'DomainName': san,
                    'ValidationDomain': san
                })
        
        print(f"Requesting ACM certificate for {domain}...")
        
        # Request certificate
        response = acm_client.request_certificate(
            DomainName=domain,
            ValidationMethod=validation_method,
            SubjectAlternativeNames=sans if len(sans) > 1 else None,
            DomainValidationOptions=domain_validation_options,
            Tags=[
                {'Key': 'Application', 'Value': 'Galerly'},
                {'Key': 'Domain', 'Value': domain},
                {'Key': 'ManagedBy', 'Value': 'Galerly-AutoSSL'}
            ]
        )
        
        certificate_arn = response['CertificateArn']
        
        print(f"✓ Certificate requested: {certificate_arn}")
        
        # Get validation records (DNS records that need to be added)
        validation_records = []
        
        if validation_method == 'DNS':
            # Wait a moment for AWS to populate validation options
            import time
            time.sleep(2)
            
            try:
                cert_details = acm_client.describe_certificate(
                    CertificateArn=certificate_arn
                )
                
                domain_validation_options = cert_details['Certificate'].get('DomainValidationOptions', [])
                
                for option in domain_validation_options:
                    resource_record = option.get('ResourceRecord')
                    if resource_record:
                        validation_records.append({
                            'domain': option['DomainName'],
                            'record_type': resource_record['Type'],
                            'record_name': resource_record['Name'],
                            'record_value': resource_record['Value']
                        })
            except:
                # Validation records might not be immediately available
                print("Validation records not yet available, will be populated shortly")
        
        return {
            'success': True,
            'certificate_arn': certificate_arn,
            'validation_records': validation_records,
            'validation_method': validation_method,
            'status': 'PENDING_VALIDATION'
        }
        
    except Exception as e:
        print(f"Error requesting certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_certificate_status(certificate_arn):
    """
    Get the current status of an ACM certificate
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        dict: {
            'success': bool,
            'status': str,  # PENDING_VALIDATION, ISSUED, INACTIVE, EXPIRED, VALIDATION_TIMED_OUT, REVOKED, FAILED
            'domain': str,
            'subject_alternative_names': list,
            'validation_records': list,
            'not_before': str,
            'not_after': str,
            'error': str (if failed)
        }
    """
    try:
        response = acm_client.describe_certificate(
            CertificateArn=certificate_arn
        )
        
        certificate = response['Certificate']
        
        # Extract validation records
        validation_records = []
        for option in certificate.get('DomainValidationOptions', []):
            resource_record = option.get('ResourceRecord')
            if resource_record:
                validation_records.append({
                    'domain': option['DomainName'],
                    'validation_status': option.get('ValidationStatus'),
                    'record_type': resource_record['Type'],
                    'record_name': resource_record['Name'],
                    'record_value': resource_record['Value']
                })
        
        result = {
            'success': True,
            'status': certificate['Status'],
            'domain': certificate['DomainName'],
            'subject_alternative_names': certificate.get('SubjectAlternativeNames', []),
            'validation_records': validation_records,
            'type': certificate.get('Type'),
            'in_use_by': certificate.get('InUseBy', [])
        }
        
        # Add validity dates if issued
        if certificate['Status'] == 'ISSUED':
            result['not_before'] = certificate.get('NotBefore').isoformat() if certificate.get('NotBefore') else None
            result['not_after'] = certificate.get('NotAfter').isoformat() if certificate.get('NotAfter') else None
        
        return result
        
    except Exception as e:
        print(f"Error getting certificate status: {str(e)}")
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
        dict: {
            'success': bool,
            'validation_records': list,
            'error': str (if failed)
        }
    """
    try:
        response = acm_client.describe_certificate(
            CertificateArn=certificate_arn
        )
        
        certificate = response['Certificate']
        validation_records = []
        
        for option in certificate.get('DomainValidationOptions', []):
            resource_record = option.get('ResourceRecord')
            if resource_record:
                validation_records.append({
                    'domain': option['DomainName'],
                    'validation_status': option.get('ValidationStatus'),
                    'record_type': resource_record['Type'],
                    'record_name': resource_record['Name'],
                    'record_value': resource_record['Value']
                })
        
        return {
            'success': True,
            'validation_records': validation_records
        }
        
    except Exception as e:
        print(f"Error getting validation records: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def delete_certificate(certificate_arn):
    """
    Delete an ACM certificate
    Certificate must not be in use by any AWS resources
    
    Args:
        certificate_arn: ARN of the certificate
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'error': str (if failed)
        }
    """
    try:
        # Check if certificate is in use
        cert_status = get_certificate_status(certificate_arn)
        
        if cert_status['success'] and cert_status.get('in_use_by'):
            return {
                'success': False,
                'error': f"Certificate is in use by: {', '.join(cert_status['in_use_by'])}"
            }
        
        # Delete certificate
        acm_client.delete_certificate(
            CertificateArn=certificate_arn
        )
        
        print(f"✓ Certificate deleted: {certificate_arn}")
        
        return {
            'success': True,
            'message': 'Certificate deleted successfully'
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
        statuses: Optional list of statuses to filter by
                 ['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']
    
    Returns:
        dict: {
            'success': bool,
            'certificates': list,
            'error': str (if failed)
        }
    """
    try:
        params = {}
        if statuses:
            params['CertificateStatuses'] = statuses
        
        response = acm_client.list_certificates(**params)
        
        certificates = []
        for cert_summary in response.get('CertificateSummaryList', []):
            certificates.append({
                'certificate_arn': cert_summary['CertificateArn'],
                'domain_name': cert_summary['DomainName']
            })
        
        return {
            'success': True,
            'certificates': certificates,
            'count': len(certificates)
        }
        
    except Exception as e:
        print(f"Error listing certificates: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def check_certificate_validation(certificate_arn, max_attempts=60, delay=10):
    """
    Poll ACM certificate validation status until validated or timeout
    
    Args:
        certificate_arn: ARN of the certificate to check
        max_attempts: Maximum number of polling attempts (default 60)
        delay: Seconds to wait between attempts (default 10)
    
    Returns:
        dict: {
            'success': bool,
            'validated': bool,
            'status': str,
            'attempts': int,
            'error': str (if failed)
        }
    """
    import time
    
    try:
        for attempt in range(max_attempts):
            status_result = get_certificate_status(certificate_arn)
            
            if not status_result['success']:
                return {
                    'success': False,
                    'validated': False,
                    'error': status_result.get('error', 'Failed to get certificate status')
                }
            
            status = status_result['status']
            
            # Check if certificate is issued (validated)
            if status == 'ISSUED':
                print(f"✓ Certificate validated and issued after {attempt + 1} attempts")
                return {
                    'success': True,
                    'validated': True,
                    'status': status,
                    'attempts': attempt + 1
                }
            
            # Check for failed states
            if status in ['FAILED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'EXPIRED']:
                return {
                    'success': False,
                    'validated': False,
                    'status': status,
                    'attempts': attempt + 1,
                    'error': f'Certificate validation failed with status: {status}'
                }
            
            # Still pending, wait and retry
            if attempt < max_attempts - 1:
                print(f"Certificate status: {status}, attempt {attempt + 1}/{max_attempts}, waiting {delay}s...")
                time.sleep(delay)
        
        # Timeout reached
        return {
            'success': False,
            'validated': False,
            'status': 'PENDING_VALIDATION',
            'attempts': max_attempts,
            'error': f'Validation timeout after {max_attempts} attempts'
        }
        
    except Exception as e:
        print(f"Error checking certificate validation: {str(e)}")
        return {
            'success': False,
            'validated': False,
            'error': str(e)
        }


def resend_validation_emails(certificate_arn, domain=None):
    """
    Resend validation emails for email-validated certificates
    
    Args:
        certificate_arn: ARN of the certificate
        domain: Optional specific domain to resend for (otherwise resends all)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'error': str (if failed)
        }
    """
    try:
        params = {
            'CertificateArn': certificate_arn
        }
        
        if domain:
            params['Domain'] = domain
            params['ValidationDomain'] = domain
        
        acm_client.resend_validation_email(**params)
        
        print(f"✓ Validation email resent for {certificate_arn}")
        
        return {
            'success': True,
            'message': 'Validation email resent successfully'
        }
        
    except Exception as e:
        print(f"Error resending validation email: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
