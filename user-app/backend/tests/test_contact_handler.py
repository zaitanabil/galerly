"""
Tests for contact_handler.py endpoint.
Tests cover: contact form submission, email sending, validation, spam detection.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_contact_dependencies():
    """Mock contact dependencies."""
    with patch('handlers.contact_handler.contact_table') as mock_table, \
         patch('utils.email.send_email') as mock_email:
        yield {
            'table': mock_table,
            'email': mock_email
        }

class TestContactHandler:
    """Tests for handle_contact_submit endpoint."""
    
    def test_contact_submit_success(self, mock_contact_dependencies):
        """Submit contact form successfully."""
        from handlers.contact_handler import handle_contact_submit
        
        body = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'issueType': 'account',
            'message': 'I would like to know more about your services and how they work.'
        }
        result = handle_contact_submit(body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'thank you' in response_body.get('message', '').lower() or 'success' in str(response_body).lower()
        
        # Verify table was called
        assert mock_contact_dependencies['table'].put_item.called
    
    def test_contact_submit_missing_name(self, mock_contact_dependencies):
        """Contact form fails without name."""
        from handlers.contact_handler import handle_contact_submit
        
        body = {
            'email': 'john@example.com',
            'message': 'Test message'
        }
        result = handle_contact_submit(body)
        
        assert result['statusCode'] == 400
    
    def test_contact_submit_missing_email(self, mock_contact_dependencies):
        """Contact form fails without email."""
        from handlers.contact_handler import handle_contact_submit
        
        body = {
            'name': 'John Doe',
            'message': 'Test message'
        }
        result = handle_contact_submit(body)
        
        assert result['statusCode'] == 400
    
    def test_contact_submit_missing_message(self, mock_contact_dependencies):
        """Contact form fails without message."""
        from handlers.contact_handler import handle_contact_submit
        
        body = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        result = handle_contact_submit(body)
        
        assert result['statusCode'] == 400
    
    def test_contact_submit_invalid_email(self, mock_contact_dependencies):
        """Contact form validates email format."""
        from handlers.contact_handler import handle_contact_submit
        
        body = {
            'name': 'John Doe',
            'email': 'invalid-email',
            'message': 'Test message'
        }
        result = handle_contact_submit(body)
        
        assert result['statusCode'] == 400
    
    def test_contact_submit_spam_detection(self, mock_contact_dependencies):
        """Contact form detects potential spam."""
        from handlers.contact_handler import handle_contact_submit
        
        # Spam-like content
        body = {
            'name': 'Spam Bot',
            'email': 'spam@spam.com',
            'message': 'CLICK HERE NOW!!! BUY VIAGRA!!!'
        }
        result = handle_contact_submit(body)
        
        # Should either reject or mark as spam
        assert result['statusCode'] in [400, 429]

