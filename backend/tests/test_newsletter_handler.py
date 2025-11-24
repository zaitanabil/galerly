"""
Tests for newsletter_handler.py endpoints.
Tests cover: subscribe, unsubscribe, email validation.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_newsletter_dependencies():
    """Mock newsletter dependencies."""
    with patch('handlers.newsletter_handler.newsletter_table') as mock_newsletter:
        yield {'newsletter': mock_newsletter}

class TestNewsletterSubscribe:
    """Tests for handle_newsletter_subscribe endpoint."""
    
    def test_subscribe_success(self, mock_newsletter_dependencies):
        """Subscribe to newsletter successfully."""
        from handlers.newsletter_handler import handle_newsletter_subscribe
        
        mock_newsletter_dependencies['newsletter'].query.return_value = {'Items': []}
        
        body = {'email': 'subscriber@example.com'}
        result = handle_newsletter_subscribe(body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'subscribed' in response_body.get('message', '').lower() or 'success' in response_body.get('message', '').lower()
    
    def test_subscribe_duplicate_email(self, mock_newsletter_dependencies):
        """Subscribe with already subscribed email."""
        from handlers.newsletter_handler import handle_newsletter_subscribe
        
        mock_newsletter_dependencies['newsletter'].query.return_value = {
            'Items': [{'email': 'subscriber@example.com', 'subscribed': True}]
        }
        
        body = {'email': 'subscriber@example.com'}
        result = handle_newsletter_subscribe(body)
        
        assert result['statusCode'] in [200, 400]
        response_body = json.loads(result['body'])
        assert 'already' in response_body.get('message', '').lower() or 'success' in response_body.get('message', '').lower()
    
    def test_subscribe_invalid_email(self, mock_newsletter_dependencies):
        """Subscribe with invalid email format."""
        from handlers.newsletter_handler import handle_newsletter_subscribe
        
        body = {'email': 'invalid-email'}
        result = handle_newsletter_subscribe(body)
        
        assert result['statusCode'] == 400
    
    def test_subscribe_missing_email(self, mock_newsletter_dependencies):
        """Subscribe without email."""
        from handlers.newsletter_handler import handle_newsletter_subscribe
        
        body = {}
        result = handle_newsletter_subscribe(body)
        
        assert result['statusCode'] == 400

class TestNewsletterUnsubscribe:
    """Tests for handle_newsletter_unsubscribe endpoint."""
    
    def test_unsubscribe_success(self, mock_newsletter_dependencies):
        """Unsubscribe from newsletter successfully."""
        from handlers.newsletter_handler import handle_newsletter_unsubscribe
        
        mock_newsletter_dependencies['newsletter'].query.return_value = {
            'Items': [{'email': 'subscriber@example.com', 'subscribed': True}]
        }
        
        body = {'email': 'subscriber@example.com'}
        result = handle_newsletter_unsubscribe(body)
        
        assert result['statusCode'] == 200
    
    def test_unsubscribe_not_found(self, mock_newsletter_dependencies):
        """Unsubscribe email that doesn't exist."""
        from handlers.newsletter_handler import handle_newsletter_unsubscribe
        
        mock_newsletter_dependencies['newsletter'].query.return_value = {'Items': []}
        
        body = {'email': 'nonexistent@example.com'}
        result = handle_newsletter_unsubscribe(body)
        
        assert result['statusCode'] in [200, 404]
    
    def test_unsubscribe_missing_email(self, mock_newsletter_dependencies):
        """Unsubscribe without email."""
        from handlers.newsletter_handler import handle_newsletter_unsubscribe
        
        body = {}
        result = handle_newsletter_unsubscribe(body)
        
        assert result['statusCode'] == 400

