"""
CloudFront Distribution Manager
Handles creation, configuration, and management of CloudFront distributions for custom domains
"""
import os
import time
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize CloudFront client
cloudfront_client = boto3.client(
    'cloudfront',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    endpoint_url=os.environ.get('CLOUDFRONT_ENDPOINT_URL')  # For LocalStack
)


def create_custom_domain_distribution(user_id, custom_domain, acm_certificate_arn=None):
    """
    Create a CloudFront distribution for a custom domain
    
    Args:
        user_id: User ID for tagging
        custom_domain: Custom domain name (e.g., gallery.yourstudio.com)
        acm_certificate_arn: ARN of ACM certificate (optional, created if not provided)
    
    Returns:
        dict: {
            'success': bool,
            'distribution_id': str,
            'distribution_domain': str,
            'status': str,
            'error': str (if failed)
        }
    """
    try:
        # Get origin domain from environment (main CloudFront or S3)
        origin_domain = os.environ.get('CLOUDFRONT_DOMAIN', 'cdn.galerly.com')
        
        # Create distribution config
        caller_reference = f"galerly-{user_id}-{int(time.time())}"
        
        distribution_config = {
            'CallerReference': caller_reference,
            'Comment': f'Galerly custom domain for {custom_domain}',
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 'galerly-origin',
                        'DomainName': origin_domain,
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'https-only',
                            'OriginSslProtocols': {
                                'Quantity': 3,
                                'Items': ['TLSv1.2', 'TLSv1.1', 'TLSv1']
                            },
                            'OriginReadTimeout': 30,
                            'OriginKeepaliveTimeout': 5
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'galerly-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': {
                    'Quantity': 7,
                    'Items': ['GET', 'HEAD', 'OPTIONS', 'PUT', 'POST', 'PATCH', 'DELETE'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD']
                    }
                },
                'Compress': True,
                'ForwardedValues': {
                    'QueryString': True,
                    'Cookies': {'Forward': 'all'},
                    'Headers': {
                        'Quantity': 3,
                        'Items': ['Host', 'Origin', 'Authorization']
                    }
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,  # 24 hours
                'MaxTTL': 31536000,  # 1 year
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'Aliases': {
                'Quantity': 1,
                'Items': [custom_domain]
            },
            'DefaultRootObject': 'index.html',
            'CustomErrorResponses': {
                'Quantity': 2,
                'Items': [
                    {
                        'ErrorCode': 403,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 300
                    },
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 300
                    }
                ]
            },
            'PriceClass': 'PriceClass_100',  # Use only North America and Europe
            'ViewerCertificate': {
                'MinimumProtocolVersion': 'TLSv1.2_2021',
                'SSLSupportMethod': 'sni-only'
            }
        }
        
        # Add ACM certificate if provided
        if acm_certificate_arn:
            distribution_config['ViewerCertificate']['ACMCertificateArn'] = acm_certificate_arn
            distribution_config['ViewerCertificate']['Certificate'] = acm_certificate_arn
            distribution_config['ViewerCertificate']['CertificateSource'] = 'acm'
        else:
            # Use CloudFront default certificate (will show warning)
            distribution_config['ViewerCertificate']['CloudFrontDefaultCertificate'] = True
        
        # Create distribution
        print(f"Creating CloudFront distribution for {custom_domain}...")
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution = response['Distribution']
        distribution_id = distribution['Id']
        distribution_domain = distribution['DomainName']
        status = distribution['Status']
        
        print(f"✓ Distribution created: {distribution_id} ({status})")
        
        return {
            'success': True,
            'distribution_id': distribution_id,
            'distribution_domain': distribution_domain,
            'status': status,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"CloudFront error ({error_code}): {error_message}")
        
        return {
            'success': False,
            'error': f'{error_code}: {error_message}'
        }
    except Exception as e:
        print(f"Error creating CloudFront distribution: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_distribution_status(distribution_id):
    """
    Get current status of a CloudFront distribution
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        dict: {
            'success': bool,
            'status': str,  # 'InProgress' or 'Deployed'
            'domain_name': str,
            'enabled': bool,
            'aliases': list,
            'error': str (if failed)
        }
    """
    try:
        response = cloudfront_client.get_distribution(Id=distribution_id)
        distribution = response['Distribution']
        
        return {
            'success': True,
            'status': distribution['Status'],
            'domain_name': distribution['DomainName'],
            'enabled': distribution['DistributionConfig']['Enabled'],
            'aliases': distribution['DistributionConfig']['Aliases'].get('Items', []),
            'last_modified': distribution['LastModifiedTime'].isoformat()
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


def update_distribution_certificate(distribution_id, acm_certificate_arn):
    """
    Update CloudFront distribution with ACM certificate
    
    Args:
        distribution_id: CloudFront distribution ID
        acm_certificate_arn: ARN of ACM certificate
    
    Returns:
        dict: {
            'success': bool,
            'status': str,
            'error': str (if failed)
        }
    """
    try:
        # Get current distribution config
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Update certificate
        config['ViewerCertificate'] = {
            'ACMCertificateArn': acm_certificate_arn,
            'Certificate': acm_certificate_arn,
            'CertificateSource': 'acm',
            'MinimumProtocolVersion': 'TLSv1.2_2021',
            'SSLSupportMethod': 'sni-only'
        }
        
        # Update distribution
        response = cloudfront_client.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        print(f"✓ Distribution {distribution_id} updated with certificate")
        
        return {
            'success': True,
            'status': response['Distribution']['Status']
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"Error updating distribution: {error_message}")
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        print(f"Error updating distribution certificate: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def delete_distribution(distribution_id):
    """
    Delete a CloudFront distribution (must be disabled first)
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        dict: {'success': bool, 'error': str}
    """
    try:
        # Get current config
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Disable distribution first if enabled
        if config['Enabled']:
            print(f"Disabling distribution {distribution_id}...")
            config['Enabled'] = False
            
            response = cloudfront_client.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            # Wait for distribution to be disabled
            print("Waiting for distribution to be disabled...")
            waiter = cloudfront_client.get_waiter('distribution_deployed')
            waiter.wait(Id=distribution_id, WaiterConfig={'Delay': 30, 'MaxAttempts': 40})
            
            # Get new ETag after update
            response = cloudfront_client.get_distribution_config(Id=distribution_id)
            etag = response['ETag']
        
        # Delete distribution
        print(f"Deleting distribution {distribution_id}...")
        cloudfront_client.delete_distribution(
            Id=distribution_id,
            IfMatch=etag
        )
        
        print(f"✓ Distribution {distribution_id} deleted")
        
        return {'success': True}
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"Error deleting distribution: {error_message}")
        return {
            'success': False,
            'error': error_message
        }
    except Exception as e:
        print(f"Error deleting distribution: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def invalidate_distribution_cache(distribution_id, paths=None):
    """
    Create invalidation to clear CloudFront cache
    
    Args:
        distribution_id: CloudFront distribution ID
        paths: List of paths to invalidate (default: ['/*'])
    
    Returns:
        dict: {
            'success': bool,
            'invalidation_id': str,
            'status': str,
            'error': str (if failed)
        }
    """
    if paths is None:
        paths = ['/*']
    
    try:
        caller_reference = f"invalidation-{int(time.time())}"
        
        response = cloudfront_client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': caller_reference
            }
        )
        
        invalidation = response['Invalidation']
        
        print(f"✓ Cache invalidation created: {invalidation['Id']}")
        
        return {
            'success': True,
            'invalidation_id': invalidation['Id'],
            'status': invalidation['Status']
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
