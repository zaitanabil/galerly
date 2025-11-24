"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock
from decimal import Decimal

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
        'plan': 'pro',
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
    return {
        'user_id': 'user_123',
        'subscription_id': 'sub_test123',
        'stripe_subscription_id': 'sub_stripe123',
        'plan': 'pro',
        'status': 'active',
        'current_period_start': '2024-01-01T00:00:00Z',
        'current_period_end': '2024-02-01T00:00:00Z',
        'cancel_at_period_end': False,
        'created_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def mock_stripe():
    """Mock Stripe client."""
    stripe = Mock()
    stripe.Subscription = Mock()
    stripe.Subscription.retrieve = Mock()
    stripe.Subscription.modify = Mock()
    stripe.Subscription.delete = Mock()
    stripe.checkout = Mock()
    stripe.checkout.Session = Mock()
    stripe.checkout.Session.create = Mock()
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

