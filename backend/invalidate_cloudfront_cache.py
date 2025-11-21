#!/usr/bin/env python3
"""
CloudFront Cache Invalidation Script
Clears CloudFront cache for specific paths
"""

import boto3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize CloudFront client
cloudfront = boto3.client(
    'cloudfront',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# CloudFront Distribution IDs
# Frontend distribution (galerly.com, www.galerly.com)
FRONTEND_DISTRIBUTION_ID = 'EEUAF5M39R2Z5'
# Image CDN distribution (cdn.galerly.com) - used for image transformations
IMAGE_CDN_DISTRIBUTION_ID = 'E3P0EU1X4VGR58'

# Use frontend distribution for cache invalidation
DISTRIBUTION_ID = FRONTEND_DISTRIBUTION_ID

def invalidate_cache(paths):
    """
    Invalidate CloudFront cache for specific paths
    
    Args:
        paths: List of paths to invalidate (e.g., ['/client-gallery*', '/*.html'])
    """
    try:
        print("\n" + "="*60)
        print("   ☁️  CLOUDFRONT CACHE INVALIDATION")
        print("="*60)
        print(f"\n📍 Distribution ID: {DISTRIBUTION_ID}")
        print(f"🗑️  Paths to invalidate:")
        for path in paths:
            print(f"   - {path}")
        print()
        
        # Create invalidation
        response = cloudfront.create_invalidation(
            DistributionId=DISTRIBUTION_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f'invalidation-{datetime.utcnow().timestamp()}'
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        status = response['Invalidation']['Status']
        
        print(f"✅ Invalidation created successfully!")
        print(f"🔖 Invalidation ID: {invalidation_id}")
        print(f"📊 Status: {status}")
        print(f"\n⏳ Cache invalidation typically takes 1-5 minutes to complete.")
        print(f"   The cache will be cleared for the specified paths.\n")
        
        print("="*60)
        print("   ✅ CACHE INVALIDATION IN PROGRESS")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Cache invalidation failed: {str(e)}")
        return False


if __name__ == '__main__':
    # Default paths to invalidate
    default_paths = [
        '/client-gallery*',  # Client gallery pages with query params
        '/*.html',           # All HTML pages
        '/404.html'          # 404 page
    ]
    
    # Use command line arguments if provided, otherwise use defaults
    paths_to_invalidate = sys.argv[1:] if len(sys.argv) > 1 else default_paths
    
    print("\n🚀 Starting CloudFront cache invalidation...")
    print(f"Usage: python3 {sys.argv[0]} [path1] [path2] ...")
    print(f"Example: python3 {sys.argv[0]} '/client-gallery*' '/*.html'\n")
    
    if paths_to_invalidate:
        success = invalidate_cache(paths_to_invalidate)
        sys.exit(0 if success else 1)
    else:
        print("❌ No paths specified for invalidation")
        sys.exit(1)

