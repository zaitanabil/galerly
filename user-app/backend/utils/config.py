"""
Configuration and AWS clients with LocalStack support
Automatically detects LocalStack endpoint and configures boto3 accordingly
Uses resource naming conventions to reduce environment variables
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

# Import resource names (uses convention over configuration)
from utils.resource_names import (
    # Environment
    ENVIRONMENT,
    AWS_REGION,
    DEBUG,
    # DynamoDB Tables
    USERS_TABLE,
    GALLERIES_TABLE,
    PHOTOS_TABLE,
    SESSIONS_TABLE,
    SUBSCRIPTIONS_TABLE,
    BILLING_TABLE,
    ANALYTICS_TABLE,
    AUDIT_LOG_TABLE,
    RATE_LIMITS_TABLE,
    PLAN_VIOLATIONS_TABLE,
    CLIENT_FAVORITES_TABLE,
    CLIENT_FEEDBACK_TABLE,
    EMAIL_TEMPLATES_TABLE,
    FEATURES_TABLE,
    USER_FEATURES_TABLE,
    INVOICES_TABLE,
    APPOINTMENTS_TABLE,
    CONTRACTS_TABLE,
    RAW_VAULT_TABLE,
    SEO_SETTINGS_TABLE,
    BACKGROUND_JOBS_TABLE,
    VISITOR_TRACKING_TABLE,
    VIDEO_ANALYTICS_TABLE,
    # S3 Buckets
    S3_FRONTEND_BUCKET,
    S3_PHOTOS_BUCKET,
    S3_RENDITIONS_BUCKET,
    # Secrets and URLs
    FRONTEND_URL,
    API_BASE_URL,
    CDN_DOMAIN,
    JWT_SECRET,
    STRIPE_SECRET_KEY,
    STRIPE_PUBLISHABLE_KEY,
    STRIPE_WEBHOOK_SECRET,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    FROM_EMAIL,
    FROM_NAME,
    # Defaults
    DEFAULT_INVOICE_CURRENCY,
    DEFAULT_INVOICE_DUE_DATE,
    DEFAULT_INVOICE_PAYMENT_METHOD,
    DEFAULT_ITEM_PRICE,
    DEFAULT_ITEM_QUANTITY,
    PRESIGNED_URL_EXPIRY,
)

# LocalStack endpoint detection
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
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

# Configuration - using naming conventions (no env vars needed for bucket names)
# S3_BUCKET is an alias for backwards compatibility
S3_BUCKET = S3_PHOTOS_BUCKET

# DynamoDB Tables - lazy-loaded to allow test mocking
_tables_cache = {}

def get_table(table_name):
    """Get DynamoDB table by name (lazy-loaded, mockable)"""
    # In test mode, return the global mock table from conftest
    if IS_TEST_MODE:
        try:
            from tests.conftest import global_mock_table
            return global_mock_table
        except ImportError:
            pass  # Not in test environment
    
    if table_name not in _tables_cache:
        _tables_cache[table_name] = get_dynamodb().Table(table_name)
    return _tables_cache[table_name]

# Backwards compatibility: Create lazy-loading properties
class LazyTable:
    """Proxy that lazy-loads DynamoDB tables on attribute access"""
    def __init__(self, table_name):
        self._table_name = table_name
        self._table = None
    
    def __getattr__(self, name):
        # Don't cache in test mode, always get fresh table
        # This allows tests to reconfigure global_mock_table between tests
        if IS_TEST_MODE:
            table = get_table(self._table_name)
            return getattr(table, name)
        
        if self._table is None:
            self._table = get_table(self._table_name)
        return getattr(self._table, name)

# Table references using naming conventions (not env vars)
users_table = LazyTable(USERS_TABLE)
galleries_table = LazyTable(GALLERIES_TABLE)
photos_table = LazyTable(PHOTOS_TABLE)
sessions_table = LazyTable(SESSIONS_TABLE)
billing_table = LazyTable(BILLING_TABLE)
subscriptions_table = LazyTable(SUBSCRIPTIONS_TABLE)
analytics_table = LazyTable(ANALYTICS_TABLE)
client_favorites_table = LazyTable(CLIENT_FAVORITES_TABLE)
client_feedback_table = LazyTable(CLIENT_FEEDBACK_TABLE)
email_templates_table = LazyTable(EMAIL_TEMPLATES_TABLE)
features_table = LazyTable(FEATURES_TABLE)
user_features_table = LazyTable(USER_FEATURES_TABLE)
invoices_table = LazyTable(INVOICES_TABLE)
appointments_table = LazyTable(APPOINTMENTS_TABLE)
contracts_table = LazyTable(CONTRACTS_TABLE)
raw_vault_table = LazyTable(RAW_VAULT_TABLE)
seo_settings_table = LazyTable(SEO_SETTINGS_TABLE)
background_jobs_table = LazyTable(BACKGROUND_JOBS_TABLE)
visitor_tracking_table = LazyTable(VISITOR_TRACKING_TABLE)
video_analytics_table = LazyTable(VIDEO_ANALYTICS_TABLE)
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
client_selections_table = LazyTable('DYNAMODB_CLIENT_SELECTIONS_TABLE')

# Debug logging for LocalStack (skip in test mode for speed)
if IS_LOCAL and AWS_ENDPOINT_URL and not IS_TEST_MODE:
    print(f"LocalStack Mode Enabled")
    print(f"   Endpoint: {AWS_ENDPOINT_URL}")
    print(f"   Region: {AWS_REGION}")
    print(f"   S3 Bucket: {S3_BUCKET}")
    print(f"   DynamoDB Tables: {get_required_env('DYNAMODB_TABLE_USERS')}")
