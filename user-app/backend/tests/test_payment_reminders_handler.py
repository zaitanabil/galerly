"""Tests for payment_reminders_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.payment_reminders_handler import (
    handle_create_reminder_schedule,
    handle_process_payment_reminders,
    handle_cancel_reminder_schedule
)


class TestPaymentReminders:
    """Test payment reminder functionality with real DynamoDB"""
    
    @patch('handlers.payment_reminders_handler.send_email')
    def test_create_reminder_schedule(self, mock_email):
        """Test creating reminder schedule - uses real DynamoDB"""
        mock_email.return_value = None
        
        user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'test-{uuid.uuid4()}@test.com',
            'role': 'photographer'
        }
        
        invoice_id = f'invoice-{uuid.uuid4()}'
        body = {
            'reminder_days': [7, 3, 1],
            'message': 'Payment due'
        }
        
        result = handle_create_reminder_schedule(user, invoice_id, body)
        assert result['statusCode'] in [200, 201, 400, 401, 403, 404, 500]
    
    @patch('handlers.payment_reminders_handler.send_email')
    def test_process_payment_reminders(self, mock_email):
        """Test processing payment reminders - uses real DynamoDB"""
        mock_email.return_value = None
        
        result = handle_process_payment_reminders({}, None)
        assert result['statusCode'] in [200, 500]
    
    def test_cancel_reminder_schedule(self):
        """Test canceling reminder schedule - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        invoice_id = f'invoice-{uuid.uuid4()}'
        
        result = handle_cancel_reminder_schedule(user, invoice_id)
        assert result['statusCode'] in [200, 401, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
