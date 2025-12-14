"""
Tests for scheduled handler using REAL AWS resources
"""
import pytest
import uuid
import json
from handlers.scheduled_handler import (
    handle_gallery_expiration_reminders,
    handle_expire_galleries
)


class TestGalleryExpirationReminders:
    """Test gallery expiration reminder scheduling"""
    
    def test_expiration_reminders_disabled(self):
        """Expiration reminders are disabled - galleries never expire"""
        event = {}
        context = {}
        result = handle_gallery_expiration_reminders(event, context)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['message'] == 'Gallery expiration feature is disabled'


class TestCleanupExpiredGalleries:
    """Test expired gallery cleanup"""
    
    def test_expire_galleries_disabled(self):
        """Gallery expiration is disabled - galleries never expire"""
        event = {}
        context = {}
        result = handle_expire_galleries(event, context)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['message'] == 'Gallery expiration feature is disabled'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
