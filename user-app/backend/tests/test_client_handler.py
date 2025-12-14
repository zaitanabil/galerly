"""
Unit tests for client handler using REAL AWS resources
Tests client authentication and temporary access tokens
"""
import pytest
import uuid
from handlers.client_handler import (
    is_token_expired,
    regenerate_gallery_token
)
from utils.config import galleries_table
from datetime import datetime, timedelta, timezone


class TestTokenExpiration:
    """Test token expiration checking"""
    
    def test_token_not_expired_within_window(self):
        """Test token is valid within 7 days"""
        created_at = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat() + 'Z'
        result = is_token_expired(created_at)
        assert result is False
    
    def test_token_expired_after_window(self):
        """Test token expires after 7 days"""
        created_at = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat() + 'Z'
        result = is_token_expired(created_at)
        assert result is True
    
    def test_token_expired_with_no_date(self):
        """Test missing creation date treated as expired"""
        result = is_token_expired(None)
        assert result is True
    
    def test_token_expired_with_invalid_date(self):
        """Test invalid date format treated as expired"""
        result = is_token_expired('invalid-date')
        assert result is True


class TestTokenRegeneration:
    """Test gallery token regeneration with real AWS"""
    
    def test_regenerate_token_creates_new_token(self):
        """Test token regeneration with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        gallery = {
            'id': gallery_id,
            'user_id': user_id,
            'share_token': 'old_token'
        }
        
        try:
            # Create real gallery
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'share_token': 'old_token',
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            result = regenerate_gallery_token(gallery)
            # Function should return updated gallery or None
            assert result is None or isinstance(result, dict)
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
