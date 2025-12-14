"""
CloudFront Distribution Manager
Handles automatic CloudFront distribution creation and management for custom domains
"""
import os
import boto3
import json
import time
from typing import Dict, Any, Optional, List

# Get AWS configuration from environment
AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# CloudFront client
cloudfront_client = boto3.client(
    'cloudfront',
    region_name=AWS_REGION,
    endpoint_url=os.environ.get('CLOUDFRONT_ENDPOINT_URL') or AWS_ENDPOINT_URL
)

# Origin domain for custom domain distributions
ORIGIN_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', 'cdn.galerly.com')


def create_distribution(
    domain: str,
    certificate_arn: str,
    user_id: str,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a CloudFront distribution for a custom domain
    
    Args:
        domain: Custom domain name
        certificate_arn: ACM certificate ARN for SSL
        user_id: User ID for tagging
        comment: Optional comment for the distribution
    
    Returns:
        Dict containing distribution_id, domain_name, and status
    """
    
    # Generate caller reference (unique identifier)
    caller_reference = f"galerly-{domain}-{int(time.time())}"
    
    # Distribution configuration
    distribution_config = {
        'CallerReference': caller_reference,
        'Comment': comment or f"Galerly custom domain for {domain}",
        'Enabled': True,
        
        # Aliases (custom domain names)
        'Aliases': {
            'Quantity': 1,
            'Items': [domain]
        },
        
        # Origins - point to main Galerly CloudFront
        'Origins': {
            'Quantity': 1,
            'Items': [{
                'Id': 'galerly-origin',
                'DomainName': ORIGIN_DOMAIN,
                'CustomOriginConfig': {
                    'HTTPPort': 80,
                    'HTTPSPort': 443,
                    'OriginProtocolPolicy': 'https-only',
                    'OriginSslProtocols': {
                        'Quantity': 3,
                        'Items': ['TLSv1.2', 'TLSv1.3', 'TLSv1.1']
                    }
                }
            }]
        },
        
        # Default cache behavior
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
            'ForwardedValues': {
                'QueryString': True,
                'Cookies': {
                    'Forward': 'all'
                },
                'Headers': {
                    'Quantity': 4,
                    'Items': ['Authorization', 'Origin', 'Accept', 'Host']
                }
            },
            'MinTTL': 0,
            'DefaultTTL': 86400,
            'MaxTTL': 31536000,
            'Compress': True
        },
        
        # SSL/TLS configuration
        'ViewerCertificate': {
            'ACMCertificateArn': certificate_arn,
            'SSLSupportMethod': 'sni-only',
            'MinimumProtocolVersion': 'TLSv1.2_2021',
            'Certificate': certificate_arn,
            'CertificateSource': 'acm'
        },
        
        # Price class (use all edge locations)
        'PriceClass': 'PriceClass_All',
        
        # HTTP version
        'HttpVersion': 'http2and3',
        
        # IPv6
        'IsIPV6Enabled': True
    }
    
    try:
        # Create the distribution
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution = response['Distribution']
        
        return {
            'distribution_id': distribution['Id'],
            'domain_name': distribution['DomainName'],
            'status': distribution['Status'],
            'arn': distribution['ARN']
        }
    
    except Exception as e:
        print(f"Error creating CloudFront distribution: {str(e)}")
        raise


def get_distribution_status(distribution_id: str) -> Dict[str, Any]:
    """
    Get the current status of a CloudFront distribution
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        Dict containing status, domain_name, and deployed flag
    """
    
    try:
        response = cloudfront_client.get_distribution(Id=distribution_id)
        distribution = response['Distribution']
        
        return {
            'distribution_id': distribution['Id'],
            'domain_name': distribution['DomainName'],
            'status': distribution['Status'],
            'deployed': distribution['Status'] == 'Deployed',
            'enabled': distribution['DistributionConfig']['Enabled'],
            'aliases': distribution['DistributionConfig']['Aliases'].get('Items', [])
        }
    
    except cloudfront_client.exceptions.NoSuchDistribution:
        return {
            'error': 'Distribution not found',
            'exists': False
        }
    
    except Exception as e:
        print(f"Error getting distribution status: {str(e)}")
        raise


def update_distribution(
    distribution_id: str,
    certificate_arn: Optional[str] = None,
    enabled: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing CloudFront distribution
    
    Args:
        distribution_id: CloudFront distribution ID
        certificate_arn: New ACM certificate ARN (optional)
        enabled: Enable or disable the distribution (optional)
    
    Returns:
        Dict containing updated distribution info
    """
    
    try:
        # Get current configuration
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Update certificate if provided
        if certificate_arn:
            config['ViewerCertificate']['ACMCertificateArn'] = certificate_arn
            config['ViewerCertificate']['Certificate'] = certificate_arn
        
        # Update enabled state if provided
        if enabled is not None:
            config['Enabled'] = enabled
        
        # Apply updates
        update_response = cloudfront_client.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        distribution = update_response['Distribution']
        
        return {
            'distribution_id': distribution['Id'],
            'status': distribution['Status'],
            'updated': True
        }
    
    except Exception as e:
        print(f"Error updating distribution: {str(e)}")
        raise


def delete_distribution(distribution_id: str) -> Dict[str, Any]:
    """
    Delete a CloudFront distribution
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        Dict containing deletion status
    """
    
    try:
        # First disable the distribution
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        if config['Enabled']:
            config['Enabled'] = False
            cloudfront_client.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            # Wait for distribution to be disabled
            # In production, this should be done asynchronously
            print(f"Distribution {distribution_id} disabled. Waiting for deployment...")
            time.sleep(5)
        
        # Get new ETag after disabling
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        etag = response['ETag']
        
        # Delete the distribution
        cloudfront_client.delete_distribution(
            Id=distribution_id,
            IfMatch=etag
        )
        
        return {
            'distribution_id': distribution_id,
            'deleted': True
        }
    
    except Exception as e:
        print(f"Error deleting distribution: {str(e)}")
        raise


def create_invalidation(distribution_id: str, paths: List[str]) -> Dict[str, Any]:
    """
    Create a cache invalidation for specific paths
    
    Args:
        distribution_id: CloudFront distribution ID
        paths: List of paths to invalidate (e.g., ['/*'] for all)
    
    Returns:
        Dict containing invalidation ID and status
    """
    
    try:
        response = cloudfront_client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f"invalidation-{int(time.time())}"
            }
        )
        
        invalidation = response['Invalidation']
        
        return {
            'invalidation_id': invalidation['Id'],
            'status': invalidation['Status'],
            'create_time': invalidation['CreateTime'].isoformat()
        }
    
    except Exception as e:
        print(f"Error creating invalidation: {str(e)}")
        raise


def wait_for_deployment(distribution_id: str, max_wait_seconds: int = 1800) -> bool:
    """
    Wait for a distribution to be fully deployed
    
    Args:
        distribution_id: CloudFront distribution ID
        max_wait_seconds: Maximum time to wait (default 30 minutes)
    
    Returns:
        True if deployed, False if timeout
    """
    
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait_seconds:
        status = get_distribution_status(distribution_id)
        
        if status.get('deployed'):
            return True
        
        # Check every 30 seconds
        time.sleep(30)
    
    return False
