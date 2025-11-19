"""
Test configuration and fixtures
"""
import os
import sys
import pytest
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use production environment variables for testing (safe since no real users yet)
# All environment variables are set via GitHub Secrets in CI/CD pipeline
# No mock/test environment needed - tests run against actual AWS resources

@pytest.fixture
def mock_user():
    """Mock user data for testing"""
    return {
        'id': 'test-user-123',
        'email': 'test@galerly.com',
        'name': 'Test User',
        'role': 'photographer'
    }

@pytest.fixture
def mock_gallery():
    """Mock gallery data for testing"""
    return {
        'id': 'test-gallery-123',
        'user_id': 'test-user-123',
        'name': 'Test Gallery',
        'share_token': 'test-token-123',
        'photo_count': Decimal('10'),
        'storage_used': Decimal('1.5'),
        'privacy': 'private',
        'client_emails': ['client@example.com']
    }

@pytest.fixture
def mock_photo():
    """Mock photo data for testing"""
    return {
        'id': 'test-photo-123',
        'gallery_id': 'test-gallery-123',
        'user_id': 'test-user-123',
        'url': 'https://s3.amazonaws.com/test/photo.jpg',
        'size_mb': Decimal('0.5'),
        'uploaded_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def mock_event():
    """Mock Lambda event for testing"""
    return {
        'httpMethod': 'GET',
        'path': '/v1/test',
        'headers': {
            'Content-Type': 'application/json'
        },
        'queryStringParameters': {},
        'body': None
    }

