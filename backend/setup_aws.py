#!/usr/bin/env python3
"""
Galerly - AWS Configuration Script
Unified script for configuring AWS services (API Gateway CORS, S3 CORS)
Replaces: enable-cors.sh, configure-s3-cors.sh
"""
import boto3
import json
import sys
import os
from botocore.exceptions import ClientError

# AWS Configuration - Use environment variables with fallbacks
REGION = os.environ.get('AWS_REGION', 'us-east-1')
API_GATEWAY_ID = os.environ.get('API_GATEWAY_ID', '')  # Must be provided via environment
S3_BUCKET_NAME = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://galerly.com')

# Initialize AWS clients
apigateway = boto3.client('apigateway', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API GATEWAY CORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_api_resources():
    """Get all resources for the API"""
    try:
        response = apigateway.get_resources(restApiId=API_GATEWAY_ID)
        return response.get('items', [])
    except ClientError as e:
        print(f"❌ Error getting API resources: {str(e)}")
        return []


def enable_cors_on_resource(resource_id: str, resource_path: str):
    """Enable CORS on a specific API Gateway resource"""
    try:
        print(f"  📝 Enabling CORS on {resource_path}...")
        
        # 1. Add OPTIONS method
        try:
            apigateway.put_method(
                restApiId=API_GATEWAY_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            print(f"     ✅ OPTIONS method added")
        except ClientError as e:
            if 'ConflictException' in str(e):
                print(f"     ℹ️  OPTIONS method already exists")
            else:
                raise
        
        # 2. Set up OPTIONS integration (MOCK)
        try:
            apigateway.put_integration(
                restApiId=API_GATEWAY_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            print(f"     ✅ MOCK integration configured")
        except ClientError as e:
            if 'ConflictException' in str(e):
                print(f"     ℹ️  Integration already exists")
        
        # 3. Delete existing method response to update it
        try:
            apigateway.delete_method_response(
                restApiId=API_GATEWAY_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200'
            )
            print(f"     🔄 Deleted old method response")
        except:
            pass  # It's okay if it doesn't exist
        
        # 4. Add method response (with credentials support)
        apigateway.put_method_response(
            restApiId=API_GATEWAY_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Credentials': True
            }
        )
        print(f"     ✅ Method response configured")
        
        # 5. Delete existing integration response to update it
        try:
            apigateway.delete_integration_response(
                restApiId=API_GATEWAY_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200'
            )
            print(f"     🔄 Deleted old integration response")
        except:
            pass  # It's okay if it doesn't exist
        
        # 6. Add integration response (with specific origin and credentials)
        apigateway.put_integration_response(
            restApiId=API_GATEWAY_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,Cookie'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': f"'{FRONTEND_URL}'",
                'method.response.header.Access-Control-Allow-Credentials': "'true'"
            }
        )
        print(f"     ✅ Integration response configured with {FRONTEND_URL}")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {str(e)}")
        return False


def enable_api_gateway_cors():
    """Enable CORS on API Gateway"""
    print("🔧 Configuring API Gateway CORS...")
    print(f"API ID: {API_GATEWAY_ID}")
    print("")
    
    resources = get_api_resources()
    if not resources:
        print("❌ No resources found")
        return False
    
    # Enable CORS on all resources
    success_count = 0
    for resource in resources:
        resource_id = resource['id']
        resource_path = resource.get('path', '/')
        
        if enable_cors_on_resource(resource_id, resource_path):
            success_count += 1
    
    # Deploy API
    print("\n📤 Deploying API changes...")
    try:
        apigateway.create_deployment(
            restApiId=API_GATEWAY_ID,
            stageName='prod',
            description='CORS configuration update'
        )
        print("  ✅ API deployed to prod stage")
    except Exception as e:
        print(f"  ❌ Deployment error: {str(e)}")
        return False
    
    print(f"\n✅ CORS enabled on {success_count} resources")
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S3 CORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enable_s3_cors():
    """Enable CORS on S3 bucket"""
    print("🔧 Configuring S3 CORS...")
    print(f"Bucket: {S3_BUCKET_NAME}")
    print("")
    
    # CORS configuration
    cors_config = {
        'CORSRules': [
            {
                'AllowedOrigins': [FRONTEND_URL, 'http://localhost:3000'],
                'AllowedMethods': ['GET', 'HEAD', 'POST', 'PUT'],  # Added POST for presigned URL uploads!
                'AllowedHeaders': ['*'],
                'ExposeHeaders': ['ETag', 'Content-Length', 'Content-Type'],
                'MaxAgeSeconds': 3600
            }
        ]
    }
    
    print("📄 CORS Configuration:")
    print(json.dumps(cors_config, indent=2))
    print("")
    
    try:
        s3.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_config
        )
        
        print("✅ CORS configured successfully!")
        print("")
        print("📋 Configuration details:")
        print(f"   • Allowed Origins: {FRONTEND_URL}, localhost")
        print("   • Allowed Methods: GET, HEAD, POST, PUT (includes uploads!)")
        print("   • Allowed Headers: * (all headers)")
        print("   • Expose Headers: ETag, Content-Length, Content-Type")
        print("   • Max Age: 3600 seconds (1 hour)")
        print("")
        print("🎯 This allows:")
        print("   ✅ Fetching images as blobs")
        print("   ✅ Downloading images from frontend")
        print("   ✅ Direct S3 uploads via presigned URLs")
        print("   ✅ Cross-origin requests")
        
        # Verify configuration
        print("\n🧪 Verifying configuration...")
        response = s3.get_bucket_cors(Bucket=S3_BUCKET_NAME)
        print("  ✅ CORS configuration verified")
        
        return True
        
    except ClientError as e:
        print(f"❌ Failed to configure CORS: {str(e)}")
        print("Please check:")
        print("   • AWS credentials are valid")
        print("   • Bucket name is correct")
        print("   • You have s3:PutBucketCORS permission")
        return False


def verify_s3_cors():
    """Verify S3 CORS configuration"""
    print("🧪 Verifying S3 CORS configuration...")
    print(f"Bucket: {S3_BUCKET_NAME}")
    print("")
    
    try:
        response = s3.get_bucket_cors(Bucket=S3_BUCKET_NAME)
        cors_rules = response.get('CORSRules', [])
        
        if not cors_rules:
            print("❌ No CORS rules configured")
            return False
        
        print(f"✅ {len(cors_rules)} CORS rule(s) configured:")
        for i, rule in enumerate(cors_rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Allowed Origins: {', '.join(rule.get('AllowedOrigins', []))}")
            print(f"    Allowed Methods: {', '.join(rule.get('AllowedMethods', []))}")
            print(f"    Allowed Headers: {', '.join(rule.get('AllowedHeaders', []))}")
            print(f"    Max Age: {rule.get('MaxAgeSeconds', 'Not set')}s")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print("❌ No CORS configuration found")
        else:
            print(f"❌ Error: {str(e)}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Main function"""
    print("=" * 70)
    print("🔧 GALERLY - AWS Configuration")
    print("=" * 70)
    print("")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_aws.py api-cors    # Enable CORS on API Gateway")
        print("  python setup_aws.py s3-cors     # Enable CORS on S3 bucket")
        print("  python setup_aws.py all         # Configure all CORS settings")
        print("  python setup_aws.py verify      # Verify configurations")
        print("")
        return
    
    command = sys.argv[1].lower()
    
    success = True
    
    if command == 'api-cors':
        success = enable_api_gateway_cors()
    elif command == 's3-cors':
        success = enable_s3_cors()
    elif command == 'all':
        print("🎯 Configuring all AWS services...\n")
        api_success = enable_api_gateway_cors()
        print("\n" + "━" * 70 + "\n")
        s3_success = enable_s3_cors()
        success = api_success and s3_success
    elif command == 'verify':
        print("🧪 Verifying AWS configurations...\n")
        verify_s3_cors()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: api-cors, s3-cors, all, verify")
        success = False
    
    print("\n" + "=" * 70)
    
    if success:
        print("✅ Configuration completed successfully!")
    else:
        print("⚠️  Configuration completed with warnings/errors")
    
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()

