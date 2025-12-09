"""
CloudFront Distribution Manager
Automates CloudFront distribution creation and management for custom domains
"""
import os
import boto3
import uuid
from datetime import datetime

# Initialize CloudFront client
cloudfront_client = boto3.client(
    'cloudfront',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    endpoint_url=os.environ.get('AWS_ENDPOINT_URL') if os.environ.get('AWS_ENDPOINT_URL') else None,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID') if os.environ.get('AWS_ENDPOINT_URL') else None,
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY') if os.environ.get('AWS_ENDPOINT_URL') else None
)

def create_custom_domain_distribution(user_id, custom_domain, acm_certificate_arn=None):
    """
    Create a CloudFront distribution for a custom domain
    
    Args:
        user_id: User ID
        custom_domain: Custom domain name (e.g., gallery.studio.com)
        acm_certificate_arn: Optional ACM certificate ARN for SSL
    
    Returns:
        dict: {
            'success': bool,
            'distribution_id': str,
            'distribution_domain': str,  # CloudFront domain
            'error': str (if failed)
        }
    """
    try:
        # Get origin from environment
        origin_domain = os.environ.get('CLOUDFRONT_ORIGIN_DOMAIN', 'galerly.com')
        s3_bucket = os.environ.get('S3_BUCKET', 'galerly-photos-local')
        
        # Caller reference for idempotency
        caller_reference = f"galerly-{user_id}-{custom_domain}-{int(datetime.utcnow().timestamp())}"
        
        # Build distribution config
        distribution_config = {
            'CallerReference': caller_reference,
            'Comment': f'Galerly custom domain for {custom_domain}',
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'galerly-origin-{user_id}',
                        'DomainName': origin_domain,
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'https-only',
                            'OriginSslProtocols': {
                                'Quantity': 3,
                                'Items': ['TLSv1', 'TLSv1.1', 'TLSv1.2']
                            }
                        },
                        'OriginPath': f'/portfolio/{user_id}'  # Path to user's portfolio
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'galerly-origin-{user_id}',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': {
                    'Quantity': 7,
                    'Items': ['HEAD', 'GET', 'OPTIONS', 'PUT', 'POST', 'PATCH', 'DELETE'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['HEAD', 'GET']
                    }
                },
                'ForwardedValues': {
                    'QueryString': True,
                    'Cookies': {'Forward': 'all'},
                    'Headers': {
                        'Quantity': 3,
                        'Items': ['Host', 'Origin', 'Referer']
                    }
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,  # 1 day
                'MaxTTL': 31536000,  # 1 year
                'Compress': True,
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'CacheBehaviors': {
                'Quantity': 0
            },
            'CustomErrorResponses': {
                'Quantity': 2,
                'Items': [
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/404.html',
                        'ResponseCode': '404',
                        'ErrorCachingMinTTL': 300
                    },
                    {
                        'ErrorCode': 403,
                        'ResponsePagePath': '/404.html',
                        'ResponseCode': '404',
                        'ErrorCachingMinTTL': 300
                    }
                ]
            },
            'PriceClass': 'PriceClass_100',  # US, Europe, Israel
            'ViewerCertificate': {}
        }
        
        # Add custom domain and SSL certificate if provided
        if acm_certificate_arn:
            distribution_config['Aliases'] = {
                'Quantity': 1,
                'Items': [custom_domain]
            }
            distribution_config['ViewerCertificate'] = {
                'ACMCertificateArn': acm_certificate_arn,
                'SSLSupportMethod': 'sni-only',
                'MinimumProtocolVersion': 'TLSv1.2_2021',
                'Certificate': acm_certificate_arn,
                'CertificateSource': 'acm'
            }
        else:
            # Use default CloudFront certificate until custom cert is ready
            distribution_config['ViewerCertificate'] = {
                'CloudFrontDefaultCertificate': True,
                'MinimumProtocolVersion': 'TLSv1'
            }
        
        print(f"Creating CloudFront distribution for {custom_domain}...")
        
        # Create distribution
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution_id = response['Distribution']['Id']
        distribution_domain = response['Distribution']['DomainName']
        
        print(f"✓ CloudFront distribution created: {distribution_id}")
        print(f"  Domain: {distribution_domain}")
        
        return {
            'success': True,
            'distribution_id': distribution_id,
            'distribution_domain': distribution_domain,
            'status': response['Distribution']['Status']
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
    Get status of a CloudFront distribution
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        dict: {
            'success': bool,
            'status': str,  # InProgress, Deployed
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
            'aliases': distribution['DistributionConfig'].get('Aliases', {}).get('Items', []),
            'last_modified': distribution['LastModifiedTime'].isoformat()
        }
        
    except Exception as e:
        print(f"Error getting distribution status: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def update_distribution_certificate(distribution_id, acm_certificate_arn):
    """
    Update CloudFront distribution with SSL certificate after validation
    
    Args:
        distribution_id: CloudFront distribution ID
        acm_certificate_arn: ACM certificate ARN
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'error': str (if failed)
        }
    """
    try:
        # Get current distribution config
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Update viewer certificate configuration
        config['ViewerCertificate'] = {
            'ACMCertificateArn': acm_certificate_arn,
            'SSLSupportMethod': 'sni-only',
            'MinimumProtocolVersion': 'TLSv1.2_2021',
            'Certificate': acm_certificate_arn,
            'CertificateSource': 'acm'
        }
        
        # Update distribution
        cloudfront_client.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        print(f"✓ Updated distribution {distribution_id} with certificate {acm_certificate_arn}")
        
        return {
            'success': True,
            'message': 'Distribution updated with SSL certificate'
        }
        
    except Exception as e:
        print(f"Error updating distribution certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def invalidate_distribution_cache(distribution_id, paths=None):
    """
    Invalidate CloudFront cache for specific paths
    
    Args:
        distribution_id: CloudFront distribution ID
        paths: List of paths to invalidate (default: ['/*'] for all)
    
    Returns:
        dict: {
            'success': bool,
            'invalidation_id': str,
            'error': str (if failed)
        }
    """
    try:
        if paths is None:
            paths = ['/*']
        
        caller_reference = f"invalidation-{int(datetime.utcnow().timestamp())}"
        
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
        
        invalidation_id = response['Invalidation']['Id']
        
        print(f"✓ Cache invalidation created: {invalidation_id}")
        
        return {
            'success': True,
            'invalidation_id': invalidation_id,
            'status': response['Invalidation']['Status']
        }
        
    except Exception as e:
        print(f"Error creating cache invalidation: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def delete_distribution(distribution_id):
    """
    Delete a CloudFront distribution
    Must be disabled first, then wait for deployment before deletion
    
    Args:
        distribution_id: CloudFront distribution ID
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'error': str (if failed)
        }
    """
    try:
        # Get current config
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Check if already disabled
        if config['Enabled']:
            # Disable distribution first
            config['Enabled'] = False
            cloudfront_client.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            return {
                'success': True,
                'message': 'Distribution disabled. Wait for deployment before deletion.',
                'action': 'disabled'
            }
        
        # Check if deployed
        dist_response = cloudfront_client.get_distribution(Id=distribution_id)
        status = dist_response['Distribution']['Status']
        
        if status != 'Deployed':
            return {
                'success': False,
                'error': f'Distribution must be deployed before deletion. Current status: {status}'
            }
        
        # Delete distribution
        cloudfront_client.delete_distribution(
            Id=distribution_id,
            IfMatch=etag
        )
        
        print(f"✓ Distribution deleted: {distribution_id}")
        
        return {
            'success': True,
            'message': 'Distribution deleted successfully',
            'action': 'deleted'
        }
        
    except Exception as e:
        print(f"Error deleting distribution: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
