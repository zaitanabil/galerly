#!/usr/bin/env python3
"""
LocalStack AWS Setup Script
Creates all AWS resources in LocalStack for local development
Replaces production setup_aws.py with LocalStack-compatible version
"""
import boto3
import json
import sys
import os
import time
from botocore.exceptions import ClientError

# LocalStack Configuration - All from environment variables
LOCALSTACK_ENDPOINT = os.environ.get('AWS_ENDPOINT_URL')
if not LOCALSTACK_ENDPOINT:
    print("❌ AWS_ENDPOINT_URL not set in environment")
    print("   Please set in .env.local or export it")
    sys.exit(1)

REGION = os.environ.get('AWS_REGION')
if not REGION:
    print("❌ AWS_REGION not set in environment")
    sys.exit(1)

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("❌ AWS credentials not set in environment")
    sys.exit(1)

# Application Configuration - All from environment variables
FRONTEND_URL = os.environ.get('FRONTEND_URL')
if not FRONTEND_URL:
    print("❌ FRONTEND_URL not set in environment")
    sys.exit(1)

S3_PHOTOS_BUCKET = os.environ.get('S3_PHOTOS_BUCKET')
S3_FRONTEND_BUCKET = os.environ.get('S3_BUCKET')
S3_RENDITIONS_BUCKET = os.environ.get('S3_RENDITIONS_BUCKET')

if not all([S3_PHOTOS_BUCKET, S3_FRONTEND_BUCKET, S3_RENDITIONS_BUCKET]):
    print("❌ S3 bucket names not set in environment")
    print("   Required: S3_PHOTOS_BUCKET, S3_BUCKET, S3_RENDITIONS_BUCKET")
    sys.exit(1)

# Initialize LocalStack clients
s3 = boto3.client(
    's3',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

dynamodb = boto3.client(
    'dynamodb',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

lambda_client = boto3.client(
    'lambda',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

apigateway = boto3.client(
    'apigateway',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

def create_s3_buckets():
    """Create S3 buckets in LocalStack"""
    print("🪣 Creating S3 buckets in LocalStack...")
    
    buckets = [S3_PHOTOS_BUCKET, S3_FRONTEND_BUCKET, S3_RENDITIONS_BUCKET]
    
    for bucket_name in buckets:
        try:
            # Check if bucket exists
            try:
                s3.head_bucket(Bucket=bucket_name)
                print(f"  ✅ {bucket_name} already exists")
                continue
            except ClientError:
                pass
            
            # Create bucket
            s3.create_bucket(Bucket=bucket_name)
            print(f"  ✅ Created bucket: {bucket_name}")
            
            # Enable CORS
            cors_config = {
                'CORSRules': [
                    {
                        'AllowedOrigins': ['*'],  # LocalStack allows wildcard
                        'AllowedMethods': ['GET', 'HEAD', 'POST', 'PUT', 'DELETE'],
                        'AllowedHeaders': ['*'],
                        'ExposeHeaders': ['ETag', 'Content-Length', 'Content-Type'],
                        'MaxAgeSeconds': 3600
                    }
                ]
            }
            
            s3.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_config
            )
            print(f"  ✅ CORS configured for {bucket_name}")
            
        except Exception as e:
            print(f"  ❌ Error with bucket {bucket_name}: {str(e)}")
    
    print("")

def verify_buckets():
    """Verify S3 buckets"""
    print("🔍 Verifying S3 buckets...")
    
    try:
        response = s3.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        
        for bucket_name in [S3_PHOTOS_BUCKET, S3_FRONTEND_BUCKET, S3_RENDITIONS_BUCKET]:
            if bucket_name in buckets:
                print(f"  ✅ {bucket_name}")
            else:
                print(f"  ❌ {bucket_name} not found")
        
        print("")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        print("")
        return False

def create_dynamodb_tables():
    """Create DynamoDB tables in LocalStack"""
    print("🗄️  Creating DynamoDB tables in LocalStack...")
    print("   This will use the setup_dynamodb.py script with LocalStack endpoint")
    print("")
    
    # The setup_dynamodb.py script will automatically use LocalStack
    # if AWS_ENDPOINT_URL is set in environment
    import subprocess
    result = subprocess.run(
        ['python3', 'setup_dynamodb.py', 'create'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=False
    )
    
    if result.returncode == 0:
        print("  ✅ DynamoDB tables created")
        return True
    else:
        print("  ❌ Error creating DynamoDB tables")
        return False

def create_lambda_function():
    """Create Lambda function in LocalStack (optional, for testing)"""
    print("⚡ Creating Lambda function in LocalStack...")
    print("   Note: LocalStack Lambda requires Docker and may be resource-intensive")
    print("   For local development, running Flask directly is recommended")
    print("")
    
    # Skip Lambda creation in favor of direct Flask execution
    print("  ⏭️  Skipping Lambda creation (use Flask directly)")
    print("")
    return True

def wait_for_localstack():
    """Wait for LocalStack to be ready"""
    print("⏳ Waiting for LocalStack to be ready...")
    
    max_retries = int(os.environ.get('LOCALSTACK_MAX_RETRIES', '30'))
    retry_delay = int(os.environ.get('LOCALSTACK_RETRY_DELAY', '2'))
    
    for i in range(max_retries):
        try:
            # Try to list buckets as health check
            s3.list_buckets()
            print("  ✅ LocalStack is ready")
            print("")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"  ⏳ Attempt {i+1}/{max_retries}: LocalStack not ready yet...")
                time.sleep(retry_delay)
            else:
                print(f"  ❌ LocalStack failed to start after {max_retries} attempts")
                print(f"     Error: {str(e)}")
                print("")
                return False

def main():
    """Main setup function"""
    print("=" * 70)
    print("🚀 GALERLY - LocalStack Setup")
    print("=" * 70)
    print("")
    print(f"LocalStack Endpoint: {LOCALSTACK_ENDPOINT}")
    print(f"Region: {REGION}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print("")
    
    # Wait for LocalStack to be ready
    if not wait_for_localstack():
        print("❌ LocalStack is not available")
        print("   Start LocalStack with: docker-compose -f docker-compose.localstack.yml up -d")
        sys.exit(1)
    
    # Create S3 buckets
    create_s3_buckets()
    
    # Verify buckets
    verify_buckets()
    
    # Create DynamoDB tables
    create_dynamodb_tables()
    
    # Create Lambda function (optional)
    create_lambda_function()
    
    print("=" * 70)
    print("✅ LocalStack setup complete!")
    print("=" * 70)
    print("")
    print("Next steps:")
    print("  1. Start the backend: cd backend && python api.py")
    print("  2. Start the frontend: cd frontend && python -m http.server 8000")
    print("  3. Open browser: http://localhost:8000")
    print("")
    print("LocalStack endpoints:")
    print(f"  • S3: {LOCALSTACK_ENDPOINT}")
    print(f"  • DynamoDB: {LOCALSTACK_ENDPOINT}")
    print(f"  • API Gateway: {LOCALSTACK_ENDPOINT}")
    print("")
    print("LocalStack Web UI:")
    print(f"  • Dashboard: http://localhost:8080")
    print("")

if __name__ == '__main__':
    main()

