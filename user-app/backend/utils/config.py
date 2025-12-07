"""
Configuration and AWS clients with LocalStack support
Automatically detects LocalStack endpoint and configures boto3 accordingly
"""
import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Check if running in pytest - skip LocalStack printing for faster tests
IS_TEST_MODE = 'PYTEST_CURRENT_TEST' in os.environ

# Determine which .env file to load based on environment
# Load from project root (../../ from this file's location)
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent.parent
env_file = project_root / '.env.development'  # Default to development

# Check if ENVIRONMENT is already set (e.g., by Docker or shell)
if os.environ.get('ENVIRONMENT') == 'production':
    env_file = project_root / '.env.production'

# Load the appropriate .env file
# override=False ensures Docker environment variables are NOT overwritten
load_dotenv(env_file, override=False)

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
# Accept 'development' or 'local' as local environment
ENVIRONMENT = get_required_env('ENVIRONMENT')
IS_LOCAL = ENVIRONMENT in ['development', 'local']

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
# FIX: Use lazy initialization to allow test mocking
# These will be set on first access or can be overridden by tests
_s3_client = None
_dynamodb = None
_lambda_client = None
_ses_client = None

def get_s3_client():
    """Get S3 client (lazy-loaded, mockable)"""
    global _s3_client
    if _s3_client is None:
        _s3_client = create_s3_client()
    return _s3_client

def get_dynamodb():
    """Get DynamoDB resource (lazy-loaded, mockable)"""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = create_dynamodb_resource()
    return _dynamodb

def get_lambda_client():
    """Get Lambda client (lazy-loaded, mockable)"""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = create_lambda_client()
    return _lambda_client

def get_ses_client():
    """Get SES client (lazy-loaded, mockable)"""
    global _ses_client
    if _ses_client is None:
        _ses_client = create_ses_client()
    return _ses_client

# Backwards compatibility: expose as module-level attributes
# These call the getter functions on access
class LazyClient:
    """Proxy that lazy-loads boto3 clients on attribute access"""
    def __init__(self, getter):
        self._getter = getter
        self._client = None
    
    def __getattr__(self, name):
        if self._client is None:
            self._client = self._getter()
        return getattr(self._client, name)

s3_client = LazyClient(get_s3_client)
dynamodb = LazyClient(get_dynamodb)
lambda_client = LazyClient(get_lambda_client)
ses_client = LazyClient(get_ses_client)

# Configuration - ALL REQUIRED
S3_BUCKET = get_required_env('S3_PHOTOS_BUCKET')
S3_FRONTEND_BUCKET = get_required_env('S3_BUCKET')
S3_RENDITIONS_BUCKET = get_required_env('S3_RENDITIONS_BUCKET')

# DynamoDB Tables - lazy-loaded to allow test mocking
# FIX: In test mode, return the conftest global mock instead of real tables
_tables_cache = {}

def get_table(table_name_env):
    """Get DynamoDB table by environment variable name (lazy-loaded, mockable)"""
    # FIX: In test mode, return the global mock table from conftest
    if IS_TEST_MODE:
        try:
            from tests.conftest import global_mock_table
            return global_mock_table
        except ImportError:
            pass  # Not in test environment
    
    if table_name_env not in _tables_cache:
        _tables_cache[table_name_env] = get_dynamodb().Table(get_required_env(table_name_env))
    return _tables_cache[table_name_env]

# Backwards compatibility: Create lazy-loading properties
class LazyTable:
    """Proxy that lazy-loads DynamoDB tables on attribute access"""
    def __init__(self, env_var):
        self._env_var = env_var
        self._table = None
    
    def __getattr__(self, name):
        # FIX: Don't cache in test mode, always get fresh table
        # This allows tests to reconfigure global_mock_table between tests
        if IS_TEST_MODE:
            table = get_table(self._env_var)
            return getattr(table, name)
        
        if self._table is None:
            self._table = get_table(self._env_var)
        return getattr(self._table, name)

users_table = LazyTable('DYNAMODB_TABLE_USERS')
galleries_table = LazyTable('DYNAMODB_TABLE_GALLERIES')
photos_table = LazyTable('DYNAMODB_TABLE_PHOTOS')
sessions_table = LazyTable('DYNAMODB_TABLE_SESSIONS')
billing_table = LazyTable('DYNAMODB_TABLE_BILLING')
subscriptions_table = LazyTable('DYNAMODB_TABLE_SUBSCRIPTIONS')
analytics_table = LazyTable('DYNAMODB_TABLE_ANALYTICS')
client_favorites_table = LazyTable('DYNAMODB_TABLE_CLIENT_FAVORITES')
client_feedback_table = LazyTable('DYNAMODB_TABLE_CLIENT_FEEDBACK')
email_templates_table = LazyTable('DYNAMODB_TABLE_EMAIL_TEMPLATES')
features_table = LazyTable('DYNAMODB_TABLE_FEATURES')
user_features_table = LazyTable('DYNAMODB_TABLE_USER_FEATURES')
invoices_table = LazyTable('DYNAMODB_TABLE_INVOICES')
appointments_table = LazyTable('DYNAMODB_TABLE_APPOINTMENTS')
contracts_table = LazyTable('DYNAMODB_TABLE_CONTRACTS')
raw_vault_table = LazyTable('DYNAMODB_TABLE_RAW_VAULT')
seo_settings_table = LazyTable('DYNAMODB_TABLE_SEO_SETTINGS')
background_jobs_table = LazyTable('DYNAMODB_TABLE_BACKGROUND_JOBS')
visitor_tracking_table = LazyTable('DYNAMODB_TABLE_VISITOR_TRACKING')
video_analytics_table = LazyTable('DYNAMODB_TABLE_VIDEO_ANALYTICS')

# Debug logging for LocalStack (skip in test mode for speed)
if IS_LOCAL and AWS_ENDPOINT_URL and not IS_TEST_MODE:
    print(f"LocalStack Mode Enabled")
    print(f"   Endpoint: {AWS_ENDPOINT_URL}")
    print(f"   Region: {AWS_REGION}")
    print(f"   S3 Bucket: {S3_BUCKET}")
    print(f"   DynamoDB Tables: {get_required_env('DYNAMODB_TABLE_USERS')}")
