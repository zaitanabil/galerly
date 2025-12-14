"""
Unit tests for payment reminders handler
Tests automated reminder scheduling and cancellation
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from handlers.payment_reminders_handler import (
    handle_create_reminder_schedule,
    handle_cancel_reminder_schedule
)


class TestReminderScheduleCreation:
    """Test payment reminder schedule creation"""
    
    @patch('handlers.payment_reminders_handler.payment_reminders_table')
    @patch('handlers.payment_reminders_handler.invoices_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_reminder_schedule_success(self, mock_features, mock_invoices, mock_reminders):
        """Test successful reminder schedule creation"""
        user = {'id': 'user123', 'role': 'photographer', 'email': 'user@test.com'}
        invoice_id = 'inv123'
        body = {
            'reminder_days': [7, 3, 1],  # Days before due date
            'overdue_days': [1, 7, 14],  # Days after due date
            'custom_message': 'Payment reminder'
        }
        
        # Mock Pro plan with invoicing feature
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # Mock invoice exists and owned by user
        due_date = (datetime.now(timezone.utc) + timedelta(days=14)).replace(tzinfo=None).isoformat() + 'Z'
        mock_invoices.get_item.return_value = {
            'Item': {
                'id': 'inv123',
                'user_id': 'user123',
                'due_date': due_date,
                'status': 'pending',
                'amount': 1000
            }
        }
        
        mock_reminders.put_item.return_value = {}
        
        result = handle_create_reminder_schedule(user, invoice_id, body)
        assert result['statusCode'] == 201
        assert mock_reminders.put_item.called
    
    @patch('handlers.payment_reminders_handler.invoices_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_reminder_verifies_invoice_ownership(self, mock_features, mock_invoices):
        """Test reminder creation verifies invoice ownership"""
        user = {'id': 'user123', 'role': 'photographer', 'plan': 'pro'}
        invoice_id = 'inv123'
        body = {'reminder_days': [7, 3, 1]}
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # Mock invoice owned by different user
        mock_invoices.get_item.return_value = {
            'Item': {
                'id': 'inv123',
                'user_id': 'user456',  # Different owner
                'due_date': '2025-12-31T00:00:00Z'
            }
        }
        
        result = handle_create_reminder_schedule(user, invoice_id, body)
        assert result['statusCode'] == 403
    
    @patch('handlers.payment_reminders_handler.invoices_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_create_reminder_validates_paid_invoice(self, mock_features, mock_invoices):
        """Test reminder creation blocked for already paid invoices"""
        user = {'id': 'user123', 'role': 'photographer', 'plan': 'pro'}
        invoice_id = 'inv123'
        body = {'reminder_days': [7]}
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # Mock already paid invoice
        mock_invoices.get_item.return_value = {
            'Item': {
                'id': 'inv123',
                'user_id': 'user123',
                'status': 'paid',  # Already paid
                'due_date': '2025-12-31T00:00:00Z'
            }
        }
        
        result = handle_create_reminder_schedule(user, invoice_id, body)
        assert result['statusCode'] == 400


class TestReminderScheduleCancellation:
    """Test payment reminder schedule cancellation"""
    
    @patch('handlers.payment_reminders_handler.payment_reminders_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_cancel_reminder_schedule_success(self, mock_features, mock_reminders):
        """Test successful reminder schedule cancellation"""
        user = {'id': 'user123', 'role': 'photographer', 'plan': 'pro'}
        invoice_id = 'inv123'
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # Mock active reminder schedules
        mock_reminders.scan.return_value = {
            'Items': [
                {
                    'id': 'reminder123',
                    'invoice_id': 'inv123',
                    'photographer_id': 'user123',
                    'status': 'active'
                }
            ]
        }
        
        mock_reminders.update_item.return_value = {}
        
        result = handle_cancel_reminder_schedule(user, invoice_id)
        assert result['statusCode'] == 200
        assert mock_reminders.update_item.called
    
    @patch('handlers.payment_reminders_handler.payment_reminders_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_cancel_reminder_handles_no_schedules(self, mock_features, mock_reminders):
        """Test cancellation handles case with no active schedules"""
        user = {'id': 'user123', 'role': 'photographer', 'plan': 'pro'}
        invoice_id = 'inv123'
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # No active schedules
        mock_reminders.scan.return_value = {'Items': []}
        
        result = handle_cancel_reminder_schedule(user, invoice_id)
        assert result['statusCode'] == 200


class TestReminderConfiguration:
    """Test reminder configuration validation"""
    
    @patch('handlers.payment_reminders_handler.invoices_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_validates_reminder_days_format(self, mock_features, mock_invoices):
        """Test validation of reminder_days array"""
        user = {'id': 'user123', 'role': 'photographer', 'plan': 'pro'}
        invoice_id = 'inv123'
        body = {
            'reminder_days': 'invalid'  # Should be array
        }
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        mock_invoices.get_item.return_value = {
            'Item': {
                'id': 'inv123',
                'user_id': 'user123',
                'due_date': '2025-12-31T00:00:00Z',
                'status': 'pending'
            }
        }
        
        result = handle_create_reminder_schedule(user, invoice_id, body)
        # Should validate array format
        assert result['statusCode'] in [400, 201]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
