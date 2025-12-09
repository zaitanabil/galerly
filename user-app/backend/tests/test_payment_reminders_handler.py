"""Tests for Payment Reminders Handler"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from handlers.payment_reminders_handler import handle_create_reminder_schedule, handle_process_payment_reminders

class TestPaymentRemindersHandler:
    @patch('handlers.payment_reminders_handler.payment_reminders_table')
    @patch('handlers.payment_reminders_handler.invoices_table')
    def test_create_reminder_schedule(self, mock_invoices_table, mock_reminders_table):
        user = {'user_id': 'photo1', 'id': 'photo1', 'role': 'photographer'}
        # Mock invoice exists with proper user_id field and future due date
        future_date = (datetime.now(timezone.utc) + timedelta(days=14)).replace(tzinfo=None).isoformat() + 'Z'
        mock_invoices_table.get_item.return_value = {
            'Item': {
                'id': 'inv1', 
                'user_id': 'photo1',  # Handler checks user_id not photographer_id
                'status': 'pending', 
                'due_date': future_date,  # Use future date to avoid datetime comparison issues
                'client_email': 'client@example.com'
            }
        }
        invoice_id = 'inv1'
        body = {'reminder_days': [7, 3, 1]}
        response = handle_create_reminder_schedule(user, invoice_id, body)
        assert response['statusCode'] == 201
    
    @patch('handlers.payment_reminders_handler.payment_reminders_table')
    def test_process_payment_reminders(self, mock_table):
        mock_table.scan.return_value = {'Items': []}
        event = {}
        context = {}
        response = handle_process_payment_reminders(event, context)
        assert response['statusCode'] == 200
