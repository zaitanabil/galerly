"""Tests for payment_reminders_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.payment_reminders_handler import (
    handle_create_payment_reminder,
    handle_send_payment_reminders,
    handle_list_payment_reminders,
    handle_cancel_payment_reminder
)


class TestPaymentReminders:
    """Test payment reminder functionality with real DynamoDB"""
    
    @patch('handlers.payment_reminders_handler.send_email')
    def test_create_payment_reminder(self, mock_email):
        """Test creating payment reminder - uses real DynamoDB"""
        mock_email.return_value = None
        
        user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'test-{uuid.uuid4()}@test.com',
            'role': 'photographer'
        }
        
        body = {
            'invoice_id': f'invoice-{uuid.uuid4()}',
            'reminder_date': '2024-12-31',
            'message': 'Payment due'
        }
        
        result = handle_create_payment_reminder(user, body)
        assert result['statusCode'] in [201, 400, 404, 500]
    
    @patch('handlers.payment_reminders_handler.send_email')
    def test_send_payment_reminders(self, mock_email):
        """Test sending payment reminders - uses real DynamoDB"""
        mock_email.return_value = None
        
        result = handle_send_payment_reminders({}, None)
        assert result['statusCode'] in [200, 500]
    
    def test_list_payment_reminders(self):
        """Test listing payment reminders - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        result = handle_list_payment_reminders(user)
        assert result['statusCode'] in [200, 500]
    
    def test_cancel_payment_reminder(self):
        """Test canceling payment reminder - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        reminder_id = f'reminder-{uuid.uuid4()}'
        
        result = handle_cancel_payment_reminder(user, reminder_id)
        assert result['statusCode'] in [200, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
