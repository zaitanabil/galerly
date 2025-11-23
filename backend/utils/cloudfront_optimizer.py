"""
CloudFront CDN Optimization Configuration
Implements best practices for global content delivery with AWS CloudFront
"""
import os
import boto3
import json


class CloudFrontOptimizer:
    """
    Manages CloudFront distribution configuration for optimal image delivery
    Implements professional CDN practices for photography platforms
    """
    
    def __init__(self):
        self.cloudfront_client = boto3.client('cloudfront', region_name='us-east-1')
        self.distribution_id = os.environ.get('CLOUDFRONT_DISTRIBUTION_ID')
        self.cdn_domain = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')
    
    
    def get_optimized_cache_behaviors(self):
        """
        Define cache behaviors for different content types
        Optimizes caching strategy for images vs other content
        
        Returns:
            List of cache behavior configurations
        """
        return {
            # Original images - cache for 1 year (immutable)
            'originals': {
                'PathPattern': '*/gallery-id/*',
                'TargetOriginId': 'S3-galerly-images',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': ['GET', 'HEAD', 'OPTIONS'],
                'CachedMethods': ['GET', 'HEAD'],
                'Compress': False,  # Don't compress images
                'MinTTL': 31536000,  # 1 year
                'DefaultTTL': 31536000,
                'MaxTTL': 31536000,
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': ['Origin', 'Access-Control-Request-Headers', 'Access-Control-Request-Method']
                }
            },
            
            # Renditions - cache for 1 year (generated once, immutable)
            'renditions': {
                'PathPattern': 'renditions/*',
                'TargetOriginId': 'S3-galerly-images',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': ['GET', 'HEAD', 'OPTIONS'],
                'CachedMethods': ['GET', 'HEAD'],
                'Compress': False,  # Images already optimized
                'MinTTL': 31536000,  # 1 year
                'DefaultTTL': 31536000,
                'MaxTTL': 31536000,
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': ['Origin']
                }
            },
            
            # ZIP downloads - no cache (generated on demand)
            'zips': {
                'PathPattern': '*/gallery-all-photos.zip',
                'TargetOriginId': 'S3-galerly-images',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': ['GET', 'HEAD'],
                'CachedMethods': ['GET', 'HEAD'],
                'Compress': False,  # Already compressed
                'MinTTL': 0,
                'DefaultTTL': 0,
                'MaxTTL': 0,
                'ForwardedValues': {
                    'QueryString': True,  # For signed URLs
                    'Cookies': {'Forward': 'none'}
                }
            }
        }
    
    
    def configure_response_headers_policy(self):
        """
        Configure response headers policy for CORS and security
        Enables proper image loading across origins
        
        Returns:
            Response headers policy configuration
        """
        return {
            'Name': 'GalerlyImagePolicy',
            'Comment': 'Optimized headers for image delivery',
            'CorsConfig': {
                'AccessControlAllowOrigins': {
                    'Quantity': 2,
                    'Items': [
                        'https://galerly.com',
                        'https://www.galerly.com'
                    ]
                },
                'AccessControlAllowHeaders': {
                    'Quantity': 3,
                    'Items': ['*']
                },
                'AccessControlAllowMethods': {
                    'Quantity': 3,
                    'Items': ['GET', 'HEAD', 'OPTIONS']
                },
                'AccessControlMaxAgeSec': 86400,  # 24 hours
                'AccessControlAllowCredentials': False,
                'OriginOverride': True
            },
            'SecurityHeadersConfig': {
                'StrictTransportSecurity': {
                    'Override': True,
                    'IncludeSubdomains': True,
                    'Preload': True,
                    'AccessControlMaxAgeSec': 31536000  # 1 year
                },
                'ContentTypeOptions': {
                    'Override': True
                },
                'XSSProtection': {
                    'Override': True,
                    'Protection': True,
                    'ModeBlock': True
                }
            },
            'CustomHeadersConfig': {
                'Quantity': 2,
                'Items': [
                    {
                        'Header': 'Cache-Control',
                        'Value': 'public, max-age=31536000, immutable',
                        'Override': False
                    },
                    {
                        'Header': 'X-Content-Type-Options',
                        'Value': 'nosniff',
                        'Override': True
                    }
                ]
            }
        }
    
    
    def get_compression_config(self):
        """
        Configure compression settings
        
        Strategy:
        - Enable Brotli compression for text assets
        - Disable compression for images (already optimized)
        """
        return {
            'Compress': True,  # Enable for supported content types
            'CompressionType': 'brotli'  # Better than gzip
        }
    
    
    def get_origin_config(self):
        """
        Configure S3 origin settings
        Optimizes connection to S3 bucket
        """
        bucket_name = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        
        return {
            'Id': 'S3-galerly-images',
            'DomainName': f'{bucket_name}.s3.{region}.amazonaws.com',
            'OriginPath': '',  # Root of bucket
            'CustomHeaders': {
                'Quantity': 0
            },
            'S3OriginConfig': {
                'OriginAccessIdentity': ''  # Use OAI for security
            },
            'ConnectionAttempts': 3,
            'ConnectionTimeout': 10,
            'OriginShield': {
                'Enabled': True,
                'OriginShieldRegion': region  # Reduce load on origin
            }
        }
    
    
    def invalidate_cache(self, paths):
        """
        Invalidate CloudFront cache for specific paths
        Used when content is updated
        
        Args:
            paths: List of paths to invalidate (e.g., ['/gallery-id/*'])
        
        Returns:
            Invalidation ID or None if failed
        """
        if not self.distribution_id:
            print("⚠️  CloudFront distribution ID not configured")
            return None
        
        try:
            from datetime import datetime
            
            invalidation = self.cloudfront_client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f'galerly-invalidation-{datetime.utcnow().isoformat()}'
                }
            )
            
            invalidation_id = invalidation['Invalidation']['Id']
            print(f"✅ Created CloudFront invalidation: {invalidation_id}")
            return invalidation_id
            
        except Exception as e:
            print(f"❌ Failed to create invalidation: {str(e)}")
            return None
    
    
    def get_distribution_stats(self):
        """
        Get CloudFront distribution statistics
        Useful for monitoring and optimization
        
        Returns:
            Dictionary with distribution metrics
        """
        if not self.distribution_id:
            return None
        
        try:
            # Get distribution config
            response = self.cloudfront_client.get_distribution(
                Id=self.distribution_id
            )
            
            distribution = response['Distribution']
            
            stats = {
                'id': self.distribution_id,
                'domain': distribution['DomainName'],
                'status': distribution['Status'],
                'enabled': distribution['DistributionConfig']['Enabled'],
                'price_class': distribution['DistributionConfig']['PriceClass'],
                'origins': len(distribution['DistributionConfig']['Origins']['Items']),
                'cache_behaviors': len(distribution['DistributionConfig'].get('CacheBehaviors', {}).get('Items', []))
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get distribution stats: {str(e)}")
            return None
    
    
    def enable_http3(self):
        """
        Enable HTTP/3 (QUIC) for faster connections
        HTTP/3 reduces latency and improves performance over poor networks
        """
        if not self.distribution_id:
            return False
        
        try:
            # Get current config
            response = self.cloudfront_client.get_distribution_config(
                Id=self.distribution_id
            )
            
            config = response['DistributionConfig']
            etag = response['ETag']
            
            # Enable HTTP/3
            config['HttpVersion'] = 'http3'
            
            # Update distribution
            self.cloudfront_client.update_distribution(
                Id=self.distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )
            
            print("✅ HTTP/3 enabled for CloudFront distribution")
            return True
            
        except Exception as e:
            print(f"❌ Failed to enable HTTP/3: {str(e)}")
            return False


def configure_cloudfront():
    """
    Main function to configure CloudFront for optimal image delivery
    Can be called from setup scripts
    """
    optimizer = CloudFrontOptimizer()
    
    print("CloudFront CDN Optimization")
    print("=" * 50)
    
    # Get distribution stats
    stats = optimizer.get_distribution_stats()
    if stats:
        print(f"Distribution ID: {stats['id']}")
        print(f"Domain: {stats['domain']}")
        print(f"Status: {stats['status']}")
        print(f"Enabled: {stats['enabled']}")
    
    # Enable HTTP/3
    print("\nEnabling HTTP/3...")
    optimizer.enable_http3()
    
    print("\n✅ CloudFront optimization complete")
    return optimizer


if __name__ == '__main__':
    configure_cloudfront()

