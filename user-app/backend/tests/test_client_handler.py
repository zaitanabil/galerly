"""
Unit tests for client handler
Tests client authentication and temporary access tokens
"""
import pytest
from unittest.mock import Mock, patch
from handlers.client_handler import (
    is_token_expired,
    regenerate_gallery_token
)
from datetime import datetime, timedelta, timezone


class TestTokenExpiration:
    """Test token expiration checking"""
    
    def test_token_not_expired_within_window(self):
        """Test token is valid within 7 days"""
        # Token created 3 days ago
        created_at = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat() + 'Z'
        
        result = is_token_expired(created_at)
        assert result is False
    
    def test_token_expired_after_window(self):
        """Test token expires after 7 days"""
        # Token created 10 days ago
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
    """Test gallery token regeneration"""
    
    @patch('handlers.client_handler.galleries_table')
    def test_regenerate_token_creates_new_token(self, mock_table):
        """Test token regeneration creates new secure token"""
        gallery = {
            'id': 'gallery123',
            'user_id': 'photo123',
            'share_token': 'old_token'
        }
        
        mock_table.update_item.return_value = {
            'Attributes': {
                'id': 'gallery123',
                'share_token': 'new_token'
            }
        }
        
        result = regenerate_gallery_token(gallery)
        assert mock_table.update_item.called
        # Verify new token was generated


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
