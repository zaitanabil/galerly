"""
Resource naming conventions for Galerly
Uses convention over configuration to reduce environment variables
All AWS resources follow the pattern: galerly-{resource-name}
"""
import os


# Base configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
PROJECT_PREFIX = 'galerly'
AWS_REGION = os.environ.get('AWS_REGION', 'eu-central-1')


def get_table_name(resource: str) -> str:
    """
    Get DynamoDB table name using naming convention
    
    Args:
        resource: The resource identifier (e.g., 'users', 'galleries')
    
    Returns:
        Full table name (e.g., 'galerly-users')
    """
    return f"{PROJECT_PREFIX}-{resource}"


def get_bucket_name(resource: str) -> str:
    """
    Get S3 bucket name using naming convention
    
    Args:
        resource: The bucket identifier (e.g., 'images-storage', 'renditions')
    
    Returns:
        Full bucket name (e.g., 'galerly-images-storage')
    """
    return f"{PROJECT_PREFIX}-{resource}"


# DynamoDB Tables - constructed from convention
USERS_TABLE = get_table_name('users')
GALLERIES_TABLE = get_table_name('galleries')
PHOTOS_TABLE = get_table_name('photos')
SESSIONS_TABLE = get_table_name('sessions')
SUBSCRIPTIONS_TABLE = get_table_name('subscriptions')
BILLING_TABLE = get_table_name('billing')
REFUNDS_TABLE = get_table_name('refunds')
ANALYTICS_TABLE = get_table_name('analytics')
AUDIT_LOG_TABLE = get_table_name('audit-log')
RATE_LIMITS_TABLE = get_table_name('rate-limits')
PLAN_VIOLATIONS_TABLE = get_table_name('plan-violations')

# Additional tables
CLIENT_FAVORITES_TABLE = get_table_name('client-favorites')
CLIENT_FEEDBACK_TABLE = get_table_name('client-feedback')
EMAIL_TEMPLATES_TABLE = get_table_name('email-templates')
FEATURES_TABLE = get_table_name('features')
USER_FEATURES_TABLE = get_table_name('user-features')
INVOICES_TABLE = get_table_name('invoices')
APPOINTMENTS_TABLE = get_table_name('appointments')
BACKGROUND_JOBS_TABLE = get_table_name('background-jobs')
CITIES_TABLE = get_table_name('cities')
CONTACT_TABLE = get_table_name('contact')
CONTRACTS_TABLE = get_table_name('contracts')
CUSTOM_DOMAINS_TABLE = get_table_name('custom-domains')
DOWNLOADS_TABLE = get_table_name('downloads')
FEATURE_REQUESTS_TABLE = get_table_name('feature-requests')
FOLLOWUP_SEQUENCES_TABLE = get_table_name('followup-sequences')
LEADS_TABLE = get_table_name('leads')
NEWSLETTERS_TABLE = get_table_name('newsletters')
NOTIFICATION_PREFERENCES_TABLE = get_table_name('notification-preferences')
ONBOARDING_WORKFLOWS_TABLE = get_table_name('onboarding-workflows')
PACKAGES_TABLE = get_table_name('packages')
PAYMENT_REMINDERS_TABLE = get_table_name('payment-reminders')
RAW_VAULT_TABLE = get_table_name('raw-vault')
SALES_TABLE = get_table_name('sales')
SEO_SETTINGS_TABLE = get_table_name('seo-settings')
SERVICES_TABLE = get_table_name('services')
TESTIMONIALS_TABLE = get_table_name('testimonials')
VIDEO_ANALYTICS_TABLE = get_table_name('video-analytics')
VISITOR_TRACKING_TABLE = get_table_name('visitor-tracking')

# S3 Buckets - constructed from convention
S3_FRONTEND_BUCKET = get_bucket_name('frontend')
S3_PHOTOS_BUCKET = get_bucket_name('images-storage')
S3_RENDITIONS_BUCKET = get_bucket_name('renditions')

# Critical environment variables (secrets and URLs - cannot be derived)
# These are the ONLY ones that need to be in environment variables
def get_required_env(key: str) -> str:
    """Get required environment variable or raise error"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


# URLs and secrets that cannot be derived from convention
FRONTEND_URL = get_required_env('FRONTEND_URL')
API_BASE_URL = os.environ.get('API_BASE_URL', '')
CDN_DOMAIN = os.environ.get('CDN_DOMAIN', '')
JWT_SECRET = get_required_env('JWT_SECRET')

# Stripe configuration
STRIPE_SECRET_KEY = get_required_env('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Email configuration
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@galerly.com')
FROM_NAME = os.environ.get('FROM_NAME', 'Galerly')

# Application settings with defaults
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
DEFAULT_INVOICE_CURRENCY = os.environ.get('DEFAULT_INVOICE_CURRENCY', 'USD')
DEFAULT_INVOICE_DUE_DATE = os.environ.get('DEFAULT_INVOICE_DUE_DATE', 'Upon_Receipt')
DEFAULT_INVOICE_PAYMENT_METHOD = os.environ.get('DEFAULT_INVOICE_PAYMENT_METHOD', 'manual')
DEFAULT_ITEM_PRICE = float(os.environ.get('DEFAULT_ITEM_PRICE', '0'))
DEFAULT_ITEM_QUANTITY = int(os.environ.get('DEFAULT_ITEM_QUANTITY', '1'))
PRESIGNED_URL_EXPIRY = int(os.environ.get('PRESIGNED_URL_EXPIRY', '3600'))
