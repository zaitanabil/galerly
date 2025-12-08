"""
LocalStack S3 Bucket Setup with CORS
Creates S3 buckets and configures CORS for LocalStack development
"""
import boto3
import json
import os

def setup_s3_buckets():
    """
    Create S3 buckets and configure CORS for LocalStack
    """
    # Get LocalStack endpoint
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
    
    # Only run for LocalStack
    if 'localstack' not in endpoint_url.lower():
        print("⏭️  Not LocalStack - skipping S3 bucket setup")
        return
    
    print(f"🔧 Setting up S3 buckets for LocalStack: {endpoint_url}")
    
    s3_client = boto3.client('s3', 
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test'),
        region_name=os.environ.get('AWS_REGION', 'us-east-1')
    )
    
    # CORS configuration for browser uploads
    cors_config = {
        'CORSRules': [
            {
                'AllowedOrigins': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedHeaders': ['*'],
                'ExposeHeaders': ['ETag', 'x-amz-version-id'],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    
    # Get bucket names from environment
    buckets = [
        os.environ.get('S3_BUCKET', 'galerly-images-storage-local'),
        os.environ.get('S3_RENDITIONS_BUCKET', 'galerly-renditions-local')
    ]
    
    for bucket in buckets:
        # Create bucket
        try:
            s3_client.create_bucket(Bucket=bucket)
            print(f'  ✅ Created bucket: {bucket}')
        except Exception as e:
            if 'BucketAlreadyOwnedByYou' in str(e) or 'BucketAlreadyExists' in str(e):
                print(f'  ℹ️  Bucket already exists: {bucket}')
            else:
                print(f'  ❌ Failed to create {bucket}: {str(e)}')
                continue
        
        # Configure CORS
        try:
            s3_client.put_bucket_cors(
                Bucket=bucket,
                CORSConfiguration=cors_config
            )
            print(f'  ✅ CORS configured: {bucket}')
        except Exception as e:
            print(f'  ❌ Failed to configure CORS for {bucket}: {str(e)}')
    
    print("✅ S3 bucket setup complete")


if __name__ == '__main__':
    setup_s3_buckets()
