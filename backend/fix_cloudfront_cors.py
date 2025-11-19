#!/usr/bin/env python3
"""
Fix CloudFront CORS configuration for API
Ensures CloudFront properly forwards Origin headers and CORS responses
"""
import boto3
import json
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-east-1'
API_DOMAIN = 'api.galerly.com'

# Initialize clients
cloudfront = boto3.client('cloudfront', region_name=REGION)

def find_distribution_by_domain(domain):
    """Find CloudFront distribution ID by domain name"""
    try:
        print(f"🔍 Searching for CloudFront distribution with domain: {domain}")
        
        paginator = cloudfront.get_paginator('list_distributions')
        for page in paginator.paginate():
            if 'Items' not in page['DistributionList']:
                continue
                
            for dist in page['DistributionList']['Items']:
                aliases = dist.get('Aliases', {}).get('Items', [])
                if domain in aliases:
                    dist_id = dist['Id']
                    print(f"✅ Found distribution: {dist_id}")
                    return dist_id
        
        print(f"❌ No distribution found with domain: {domain}")
        return None
        
    except ClientError as e:
        print(f"❌ Error: {str(e)}")
        return None

def get_distribution_config(dist_id):
    """Get current distribution configuration"""
    try:
        response = cloudfront.get_distribution_config(Id=dist_id)
        return response['DistributionConfig'], response['ETag']
    except ClientError as e:
        print(f"❌ Error getting distribution config: {str(e)}")
        return None, None

def update_distribution_cors(dist_id):
    """Update CloudFront distribution to properly handle CORS"""
    print(f"\n🔧 Updating CloudFront distribution: {dist_id}")
    
    # Get current config
    config, etag = get_distribution_config(dist_id)
    if not config:
        return False
    
    print("\n📋 Current configuration:")
    print(f"   Enabled: {config.get('Enabled')}")
    print(f"   Origins: {len(config.get('Origins', {}).get('Items', []))}")
    
    # Update cache behavior to forward Origin header
    default_cache = config.get('DefaultCacheBehavior', {})
    
    print("\n🔄 Updating cache behavior...")
    
    # Update ForwardedValues to include Origin header
    if 'ForwardedValues' not in default_cache:
        default_cache['ForwardedValues'] = {}
    
    if 'Headers' not in default_cache['ForwardedValues']:
        default_cache['ForwardedValues']['Headers'] = {'Quantity': 0, 'Items': []}
    
    # Ensure Origin header is forwarded
    headers = default_cache['ForwardedValues']['Headers']
    cors_headers = [
        'Origin',
        'Access-Control-Request-Method',
        'Access-Control-Request-Headers'
    ]
    
    current_headers = headers.get('Items', [])
    for header in cors_headers:
        if header not in current_headers:
            current_headers.append(header)
            print(f"   ✅ Added header: {header}")
        else:
            print(f"   ℹ️  Header already forwarded: {header}")
    
    headers['Items'] = current_headers
    headers['Quantity'] = len(current_headers)
    
    # Update AllowedMethods to include OPTIONS
    if 'AllowedMethods' not in default_cache:
        default_cache['AllowedMethods'] = {
            'Quantity': 7,
            'Items': ['HEAD', 'DELETE', 'POST', 'GET', 'OPTIONS', 'PUT', 'PATCH'],
            'CachedMethods': {'Quantity': 2, 'Items': ['HEAD', 'GET']}
        }
        print("   ✅ Added OPTIONS to allowed methods")
    
    # Disable caching for OPTIONS requests (CORS preflight)
    default_cache['MinTTL'] = 0
    default_cache['DefaultTTL'] = 0
    default_cache['MaxTTL'] = 86400  # 24 hours max
    
    print("   ✅ Updated cache TTL for CORS")
    
    # Apply changes
    print("\n📤 Applying changes to CloudFront...")
    try:
        response = cloudfront.update_distribution(
            Id=dist_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        print("✅ Distribution updated successfully!")
        print(f"   Status: {response['Distribution']['Status']}")
        print(f"   Domain: {response['Distribution']['DomainName']}")
        
        # Create invalidation to clear cache
        print("\n🔄 Creating cache invalidation...")
        invalidation = cloudfront.create_invalidation(
            DistributionId=dist_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': f'cors-fix-{int(__import__("time").time())}'
            }
        )
        
        print(f"✅ Cache invalidation created: {invalidation['Invalidation']['Id']}")
        print("   Wait ~5-10 minutes for invalidation to complete")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating distribution: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 70)
    print("🔧 CLOUDFRONT CORS FIX")
    print("=" * 70)
    print("")
    
    # Find distribution
    dist_id = find_distribution_by_domain(API_DOMAIN)
    
    if not dist_id:
        print("\n❌ Could not find CloudFront distribution")
        print("Please manually provide the distribution ID:")
        print(f"  python {__file__} <distribution-id>")
        return
    
    # Update distribution
    success = update_distribution_cors(dist_id)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ CloudFront CORS configuration updated!")
        print("\n📋 Next steps:")
        print("   1. Wait 5-10 minutes for cache invalidation")
        print("   2. Hard refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)")
        print("   3. Try logging in again")
    else:
        print("⚠️  Configuration update failed")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()

