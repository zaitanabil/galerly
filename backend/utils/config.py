"""
Configuration and AWS clients with LocalStack support
Automatically detects LocalStack endpoint and configures boto3 accordingly
"""
import os
import boto3
from botocore.config import Config

def get_required_env(key):
    """Get required environment variable or raise error"""
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

# AWS Region - REQUIRED
AWS_REGION = get_required_env('AWS_REGION')

# LocalStack endpoint detection
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
IS_LOCAL = get_required_env('ENVIRONMENT') == 'local'

# Configure boto3 client settings
def get_boto3_config():
    """
    Return boto3 configuration based on environment
    LocalStack requires specific configuration
    """
    config = Config(
        region_name=AWS_REGION,
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
    return config

# Create AWS clients with LocalStack support
def create_s3_client():
    """
    Create S3 client with LocalStack endpoint if configured
    """
    client_args = {
        'service_name': 's3',
        'region_name': AWS_REGION,
        'config': get_boto3_config()
    }
    
    # LocalStack requires custom endpoint and credentials
    if AWS_ENDPOINT_URL:
        client_args['endpoint_url'] = AWS_ENDPOINT_URL
        client_args['aws_access_key_id'] = get_required_env('AWS_ACCESS_KEY_ID')
        client_args['aws_secret_access_key'] = get_required_env('AWS_SECRET_ACCESS_KEY')
    
    return boto3.client(**client_args)

def create_dynamodb_resource():
    """
    Create DynamoDB resource with LocalStack endpoint if configured
    """
    resource_args = {
        'service_name': 'dynamodb',
        'region_name': AWS_REGION
    }
    
    # LocalStack requires custom endpoint and credentials
    if AWS_ENDPOINT_URL:
        resource_args['endpoint_url'] = AWS_ENDPOINT_URL
        resource_args['aws_access_key_id'] = get_required_env('AWS_ACCESS_KEY_ID')
        resource_args['aws_secret_access_key'] = get_required_env('AWS_SECRET_ACCESS_KEY')
    
    return boto3.resource(**resource_args)

def create_lambda_client():
    """
    Create Lambda client with LocalStack endpoint if configured
    """
    client_args = {
        'service_name': 'lambda',
        'region_name': AWS_REGION
    }
    
    if AWS_ENDPOINT_URL:
        client_args['endpoint_url'] = AWS_ENDPOINT_URL
        client_args['aws_access_key_id'] = get_required_env('AWS_ACCESS_KEY_ID')
        client_args['aws_secret_access_key'] = get_required_env('AWS_SECRET_ACCESS_KEY')
    
    return boto3.client(**client_args)

def create_ses_client():
    """
    Create SES client with LocalStack endpoint if configured
    """
    client_args = {
        'service_name': 'ses',
        'region_name': AWS_REGION
    }
    
    if AWS_ENDPOINT_URL:
        client_args['endpoint_url'] = AWS_ENDPOINT_URL
        client_args['aws_access_key_id'] = get_required_env('AWS_ACCESS_KEY_ID')
        client_args['aws_secret_access_key'] = get_required_env('AWS_SECRET_ACCESS_KEY')
    
    return boto3.client(**client_args)

# Initialize AWS clients
s3_client = create_s3_client()
dynamodb = create_dynamodb_resource()
lambda_client = create_lambda_client()
ses_client = create_ses_client()

# Configuration - ALL REQUIRED
S3_BUCKET = get_required_env('S3_PHOTOS_BUCKET')
S3_FRONTEND_BUCKET = get_required_env('S3_BUCKET')
S3_RENDITIONS_BUCKET = get_required_env('S3_RENDITIONS_BUCKET')

# DynamoDB Tables from environment variables - ALL REQUIRED
users_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_USERS'))
galleries_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_GALLERIES'))
photos_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_PHOTOS'))
sessions_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_SESSIONS'))
billing_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_BILLING'))
subscriptions_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_SUBSCRIPTIONS'))
analytics_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_ANALYTICS'))
client_favorites_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_CLIENT_FAVORITES'))
client_feedback_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_CLIENT_FEEDBACK'))
email_templates_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_EMAIL_TEMPLATES'))

# Debug logging for LocalStack
if IS_LOCAL and AWS_ENDPOINT_URL:
    print(f"🔧 LocalStack Mode Enabled")
    print(f"   Endpoint: {AWS_ENDPOINT_URL}")
    print(f"   Region: {AWS_REGION}")
    print(f"   S3 Bucket: {S3_BUCKET}")
    print(f"   DynamoDB Tables: {get_required_env('DYNAMODB_TABLE_USERS')}")
