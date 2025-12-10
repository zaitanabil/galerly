"""
Pytest configuration and shared fixtures for backend tests.
FIX: boto3 MUST be patched BEFORE any handler/utils imports.
Import order is CRITICAL for test mocking to work.
"""
import pytest
import os
import sys

# ============================================================================
# CRITICAL: Set environment variables FIRST, before ANY imports
# ============================================================================
os.environ.setdefault('SMTP_HOST', 'mail.privateemail.com')
os.environ.setdefault('SMTP_PORT', '587')
os.environ.setdefault('SMTP_USER', 'support@galerly.com')
os.environ.setdefault('SMTP_PASSWORD', 'f#@ho]7J69iqf8,kCK:.uoKA:FGKD~')
os.environ.setdefault('FROM_EMAIL', 'noreply@galerly.com')
os.environ.setdefault('FROM_NAME', 'Galerly')
os.environ.setdefault('DEFAULT_PAGE_SIZE', '50')
os.environ.setdefault('MAX_USERNAME_BASE_LENGTH', '47')
os.environ.setdefault('SESSION_MAX_AGE', '604800')
os.environ.setdefault('MULTIPART_CHUNK_SIZE', '10485760')
os.environ.setdefault('REFUND_LIST_LIMIT', '5')
os.environ.setdefault('PRESIGNED_URL_EXPIRY', '604800')
os.environ.setdefault('CNAME_TARGET', 'cname.galerly.com')
os.environ.setdefault('SUPPORT_EMAIL', 'support@galerly.com')
os.environ.setdefault('WEBSITE_URL', 'https://galerly.com')
os.environ.setdefault('FRONTEND_URL_FALLBACK', 'http://localhost:5173')
os.environ.setdefault('DYNAMODB_TABLE_CITIES', 'galerly-cities-local')
os.environ.setdefault('DYNAMODB_TABLE_NOTIFICATION_PREFERENCES', 'galerly-notification-preferences-local')
os.environ.setdefault('DYNAMODB_TABLE_NEWSLETTERS', 'galerly-newsletters-local')
os.environ.setdefault('DYNAMODB_TABLE_CONTACT', 'galerly-contact-local')
os.environ.setdefault('DYNAMODB_TABLE_VIDEO_ANALYTICS', 'galerly-video-analytics-local')
os.environ.setdefault('DYNAMODB_TABLE_VISITOR_TRACKING', 'galerly-visitor-tracking-local')
os.environ.setdefault('DYNAMODB_TABLE_BACKGROUND_JOBS', 'galerly-background-jobs')

# Add backend directory to path BEFORE any imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ============================================================================
# CRITICAL: Mock boto3 BEFORE any utils/handlers imports
# ============================================================================
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from dotenv import load_dotenv

# Create persistent mocks
_mock_dynamodb = MagicMock()
_mock_table = MagicMock()
_mock_s3 = MagicMock()
_mock_ses = MagicMock()

# Configure mock responses
_mock_table.put_item.return_value = {}
_mock_table.get_item.return_value = {'Item': {}}
_mock_table.query.return_value = {'Items': []}
_mock_table.scan.return_value = {'Items': []}
_mock_table.delete_item.return_value = {}
_mock_table.update_item.return_value = {'Attributes': {}}
_mock_table.batch_write_item.return_value = {}

_mock_dynamodb.Table.return_value = _mock_table

_mock_s3.generate_presigned_url.return_value = 'https://fake-s3.com/test'
_mock_s3.put_object.return_value = {}
_mock_s3.delete_object.return_value = {}
_mock_s3.list_objects_v2.return_value = {'Contents': []}
_mock_s3.head_object.return_value = {'ContentLength': 1024}

_mock_ses.send_email.return_value = {'MessageId': 'test-msg-id'}

def _mock_boto3_client(service_name, **kwargs):
    """Factory for boto3.client() calls"""
    if service_name == 's3':
        return _mock_s3
    elif service_name == 'ses':
        return _mock_ses
    return MagicMock()

def _mock_boto3_resource(service_name, **kwargs):
    """Factory for boto3.resource() calls"""
    if service_name == 'dynamodb':
        return _mock_dynamodb
    return MagicMock()

# Set required SMTP environment variables BEFORE any imports
# This prevents ValueError when utils.email module loads
# Values from .env.development (actual production SMTP credentials for testing)
# Note: Tests mock smtplib.SMTP below, so no real emails are sent
os.environ.setdefault('SMTP_HOST', 'mail.privateemail.com')
os.environ.setdefault('SMTP_PORT', '587')
os.environ.setdefault('SMTP_USER', 'support@galerly.com')
os.environ.setdefault('SMTP_PASSWORD', 'f#@ho]7J69iqf8,kCK:.uoKA:FGKD~')
os.environ.setdefault('FROM_EMAIL', 'noreply@galerly.com')
os.environ.setdefault('FROM_NAME', 'Galerly')

# Set application limits and configuration from .env.development
os.environ.setdefault('DEFAULT_PAGE_SIZE', '50')
os.environ.setdefault('MAX_USERNAME_BASE_LENGTH', '47')
os.environ.setdefault('SESSION_MAX_AGE', '604800')
os.environ.setdefault('MULTIPART_CHUNK_SIZE', '10485760')
os.environ.setdefault('REFUND_LIST_LIMIT', '5')
os.environ.setdefault('PRESIGNED_URL_EXPIRY', '604800')
os.environ.setdefault('CNAME_TARGET', 'cname.galerly.com')
os.environ.setdefault('SUPPORT_EMAIL', 'support@galerly.com')
os.environ.setdefault('WEBSITE_URL', 'https://galerly.com')
os.environ.setdefault('FRONTEND_URL_FALLBACK', 'http://localhost:5173')
os.environ.setdefault('DYNAMODB_TABLE_CITIES', 'galerly-cities-local')
os.environ.setdefault('DYNAMODB_TABLE_NOTIFICATION_PREFERENCES', 'galerly-notification-preferences-local')
os.environ.setdefault('DYNAMODB_TABLE_NEWSLETTERS', 'galerly-newsletters-local')
os.environ.setdefault('DYNAMODB_TABLE_CONTACT', 'galerly-contact-local')
os.environ.setdefault('DYNAMODB_TABLE_VIDEO_ANALYTICS', 'galerly-video-analytics-local')
os.environ.setdefault('DYNAMODB_TABLE_VISITOR_TRACKING', 'galerly-visitor-tracking-local')
os.environ.setdefault('DYNAMODB_TABLE_BACKGROUND_JOBS', 'galerly-background-jobs')

# Start patching boto3 IMMEDIATELY
# FIX: Store patchers globally so tests can stop/restart them if needed
_boto3_client_patcher = patch('boto3.client', side_effect=_mock_boto3_client)
_boto3_resource_patcher = patch('boto3.resource', side_effect=_mock_boto3_resource)
_boto3_client_patcher.start()
_boto3_resource_patcher.start()

# FIX: Mock SMTP connection to prevent actual email sending
_mock_smtp = MagicMock()
_smtp_patcher = patch('smtplib.SMTP', return_value=_mock_smtp)
_smtp_patcher.start()

# Export global mocks for tests that need to check/configure them
global_mock_table = _mock_table
global_mock_s3 = _mock_s3
global_mock_ses = _mock_ses

# Load environment variables from root .env.development for testing
# Navigate from tests/ -> backend/ -> user-app/ -> project root/
env_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env.development')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def reset_global_mocks():
    """
    Auto-reset global mocks between each test to prevent state bleed.
    This fixture runs automatically before each test.
    """
    # Reset all mock method return values and side_effects
    global_mock_table.reset_mock()
    global_mock_s3.reset_mock()
    global_mock_ses.reset_mock()
    
    # Set default return values
    global_mock_table.get_item.return_value = {}
    global_mock_table.scan.return_value = {'Items': []}
    global_mock_table.query.return_value = {'Items': []}
    global_mock_table.put_item.return_value = {}
    global_mock_table.delete_item.return_value = {}
    global_mock_table.update_item.return_value = {'Attributes': {}}
    
    # Clear any side_effect
    global_mock_table.get_item.side_effect = None
    global_mock_table.scan.side_effect = None
    global_mock_table.query.side_effect = None
    
    yield


@pytest.fixture
def mock_dynamodb():
    """
    Mock all DynamoDB tables for integration tests.
    FIX: This fixture now properly stops global boto3 patches
    to allow test-specific table mocking.
    """
    # Temporarily stop global boto3 patches
    _boto3_client_patcher.stop()
    _boto3_resource_patcher.stop()
    
    try:
        with patch('utils.config.users_table') as mock_users, \
             patch('utils.config.sessions_table') as mock_sessions, \
             patch('utils.config.galleries_table') as mock_galleries, \
             patch('utils.config.photos_table') as mock_photos, \
             patch('utils.config.subscriptions_table') as mock_subs, \
             patch('utils.config.billing_table') as mock_billing:
            
            # Setup default behaviors for common operations
            for mock_table in [mock_users, mock_sessions, mock_galleries, mock_photos, mock_subs, mock_billing]:
                mock_table.put_item = Mock(return_value={})
                mock_table.get_item = Mock(return_value={'Item': {}})
                mock_table.query = Mock(return_value={'Items': []})
                mock_table.scan = Mock(return_value={'Items': []})
                mock_table.delete_item = Mock(return_value={})
                mock_table.update_item = Mock(return_value={'Attributes': {}})
            
            yield {
                'users_table': mock_users,
                'sessions_table': mock_sessions,
                'galleries_table': mock_galleries,
                'photos_table': mock_photos,
                'subscriptions_table': mock_subs,
                'billing_table': mock_billing
            }
    finally:
        # Restart global patches
        _boto3_client_patcher.start()
        _boto3_resource_patcher.start()

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table with common methods."""
    table = Mock()
    table.query = Mock()
    table.get_item = Mock()
    table.put_item = Mock()
    table.delete_item = Mock()
    table.update_item = Mock()
    table.scan = Mock()
    return table

@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    client = Mock()
    client.generate_presigned_url = Mock()
    client.delete_object = Mock()
    client.list_objects_v2 = Mock()
    return client

@pytest.fixture
def sample_user():
    """Sample user object for testing."""
    return {
        'id': 'user_123',
        'email': 'test@example.com',
        'name': 'Test User',
        'username': 'testuser',
        'role': 'photographer',
        'plan': 'pro',
        'subscription': 'pro',
        'stripe_customer_id': 'cus_test123',
        'created_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def sample_gallery():
    """Sample gallery object for testing."""
    return {
        'user_id': 'user_123',
        'id': 'gallery_123',
        'name': 'Test Gallery',
        'status': 'active',
        'client_emails': ['client1@example.com', 'client2@example.com'],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'photo_count': 10,
        'archived': False
    }

@pytest.fixture
def sample_photo():
    """Sample photo object for testing."""
    return {
        'id': 'photo_123',
        'gallery_id': 'gallery_123',
        'user_id': 'user_123',
        'status': 'approved',
        'url': 'https://cdn.example.com/photo.jpg',
        'thumbnail_url': 'https://cdn.example.com/thumb.jpg',
        'medium_url': 'https://cdn.example.com/medium.jpg',
        'filename': 'photo.jpg',
        'size': 1024000,
        'width': 1920,
        'height': 1080,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def sample_subscription():
    """Sample subscription object for testing."""
    import time
    # Use numeric timestamps (seconds since epoch)
    current_time = int(time.time())
    period_end = current_time + (30 * 24 * 3600)  # 30 days from now
    
    return {
        'id': 'sub_test123',  # Add missing id field
        'user_id': 'user_123',
        'subscription_id': 'sub_test123',
        'stripe_subscription_id': 'sub_stripe123',
        'plan': 'pro',
        'status': 'active',
        'current_period_start': current_time - (5 * 24 * 3600),  # 5 days ago
        'current_period_end': period_end,  # 30 days from now
        'cancel_at_period_end': False,
        'created_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def mock_stripe():
    """Mock Stripe client."""
    stripe = Mock()
    stripe.Subscription = Mock()
    
    # Make Subscription.retrieve return a dict-like object with nested structure
    def mock_retrieve(sub_id):
        return {
            'id': sub_id,
            'cancel_at_period_end': False,
            'items': {
                'data': [
                    {
                        'price': {
                            'id': 'price_starter'
                        }
                    }
                ]
            }
        }
    
    stripe.Subscription.retrieve = Mock(side_effect=mock_retrieve)
    stripe.Subscription.modify = Mock(return_value={'id': 'sub_modified'})
    stripe.Subscription.delete = Mock()
    stripe.checkout = Mock()
    stripe.checkout.Session = Mock()
    stripe.checkout.Session.create = Mock(return_value={'id': 'cs_test', 'url': 'https://checkout.stripe.com/test'})
    stripe.Customer = Mock()
    stripe.Customer.create = Mock()
    stripe.Customer.retrieve = Mock()
    stripe.PaymentIntent = Mock()
    stripe.Refund = Mock()
    return stripe

@pytest.fixture
def mock_cache():
    """Mock cache instance."""
    cache = Mock()
    cache.retrieve = Mock(return_value=None)
    cache.store = Mock()
    cache.remove = Mock()
    cache.invalidate_pattern = Mock(return_value=0)
    cache.clear = Mock()
    cache.get_statistics = Mock(return_value={'hits': 0, 'misses': 0, 'hit_rate': 0.0})
    return cache

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization in tests."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

