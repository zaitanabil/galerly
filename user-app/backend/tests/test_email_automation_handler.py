"""
Tests for email_automation_handler.py
Automated email scheduling and queue processing
"""
import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from handlers.email_automation_handler import (
    handle_schedule_automated_email,
    handle_process_email_queue,
    handle_setup_gallery_automation,
    handle_cancel_scheduled_email,
    handle_list_scheduled_emails
)


@pytest.fixture
def mock_user():
    return {
        'id': 'test-user-123',
        'email': 'photographer@test.com',
        'name': 'Test Photographer',
        'plan': 'pro'
    }


@pytest.fixture
def mock_scheduled_email():
    return {
        'id': 'email-123',
        'user_id': 'test-user-123',
        'recipient_email': 'client@test.com',
        'subject': 'Test Subject',
        'body_html': '<p>Test email</p>',
        'body_text': 'Test email',
        'scheduled_time': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z',
        'status': 'scheduled',
        'email_type': 'custom',
        'retry_count': 0,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }


class TestScheduleAutomatedEmail:
    """Test email scheduling functionality"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_schedule_email_success(self, mock_table, mock_features, mock_user):
        """Test successful email scheduling"""
        mock_features.return_value = ({'email_automation': True}, None, None)
        
        body = {
            'recipient_email': 'client@test.com',
            'gallery_id': 'gallery-123',
            'email_type': 'custom',
            'subject': 'Gallery Ready',
            'body': '<p>Your gallery is ready</p>',
            'scheduled_time': (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'email_id' in body_data
        mock_table.put_item.assert_called_once()
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_schedule_email_requires_pro_plan(self, mock_features, mock_user):
        """Test that email automation requires Pro/Ultimate plan"""
        mock_features.return_value = ({'email_automation': False}, None, None)
        
        body = {
            'recipient_email': 'client@test.com',
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'body_text': 'Test',
            'scheduled_time': (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'upgrade_required' in body_data
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_schedule_email_validates_required_fields(self, mock_features, mock_user):
        """Test validation of required fields"""
        mock_features.return_value = ({'email_automation': True}, None, None)
        
        body = {
            'recipient_email': 'client@test.com'
            # Missing required fields
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'required' in body_data['error'].lower()
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_schedule_email_prevents_past_scheduling(self, mock_features, mock_user):
        """Test that emails cannot be scheduled in the past"""
        mock_features.return_value = ({'email_automation': True}, None, None)
        
        body = {
            'recipient_email': 'client@test.com',
            'gallery_id': 'gallery-123',
            'email_type': 'custom',
            'subject': 'Test',
            'body': '<p>Test</p>',
            'scheduled_time': (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'past' in body_data['error'].lower()


class TestSetupGalleryAutomation:
    """Test gallery automation setup"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('utils.config.galleries_table')
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_setup_gallery_automation_success(self, mock_queue, mock_galleries, mock_features, mock_user):
        """Test successful gallery automation setup"""
        mock_features.return_value = ({'email_automation': True}, None, None)
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery-123',
                'user_id': mock_user['id'],
                'title': 'Wedding Photos',
                'expiration_date': (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
                'client_emails': ['client@test.com']
            }
        }
        
        body = {
            'gallery_id': 'gallery-123',
            'reminders': {
                'expiration_7days': True,
                'expiration_1day': True
            }
        }
        
        response = handle_setup_gallery_automation(mock_user, body)
        
        assert response['statusCode'] == 201
        body_data = json.loads(response['body'])
        assert 'scheduled_emails' in body_data
        assert len(body_data['scheduled_emails']) > 0
    
    @patch('handlers.email_automation_handler.get_user_features')
    @patch('handlers.email_automation_handler.galleries_table')
    def test_setup_gallery_automation_validates_ownership(self, mock_galleries, mock_features, mock_user):
        """Test that users can only setup automation for their galleries"""
        mock_features.return_value = ({'email_automation': True}, None, None)
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery-123',
                'user_id': 'different-user',
                'title': 'Wedding Photos'
            }
        }
        
        body = {
            'gallery_id': 'gallery-123',
            'reminders': {'expiration_7days': True}
        }
        
        response = handle_setup_gallery_automation(mock_user, body)
        
        assert response['statusCode'] == 403


class TestProcessEmailQueue:
    """Test email queue processing"""
    
    @patch('utils.email.send_email')
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_process_queue_sends_due_emails(self, mock_table, mock_send):
        """Test processing emails that are due"""
        now = datetime.utcnow()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'email-1',
                    'user_id': 'user-123',
                    'recipient_email': 'client@test.com',
                    'subject': 'Test',
                    'body_html': '<p>Test</p>',
                    'body_text': 'Test',
                    'scheduled_time': (now - timedelta(minutes=1)).isoformat() + 'Z',
                    'status': 'scheduled',
                    'retry_count': 0
                }
            ]
        }
        mock_send.return_value = None  # Success
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['processed'] >= 1
        mock_send.assert_called()
        mock_table.put_item.assert_called()  # Status update
    
    @patch('utils.email.send_email')
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_process_queue_retries_failed_emails(self, mock_table, mock_send):
        """Test retry logic for failed emails"""
        now = datetime.utcnow()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'email-1',
                    'user_id': 'user-123',
                    'recipient_email': 'client@test.com',
                    'subject': 'Test',
                    'body_html': '<p>Test</p>',
                    'body_text': 'Test',
                    'scheduled_time': (now - timedelta(minutes=1)).isoformat() + 'Z',
                    'status': 'scheduled',
                    'retry_count': 0
                }
            ]
        }
        mock_send.side_effect = Exception('SMTP error')
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] == 200
        # Should update status to retry
        calls = mock_table.put_item.call_args_list
        assert any('retry_count' in str(call) for call in calls)
    
    @patch('utils.email.send_email')
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_process_queue_marks_failed_after_max_retries(self, mock_table, mock_send):
        """Test marking emails as failed after max retries"""
        now = datetime.utcnow()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'email-1',
                    'user_id': 'user-123',
                    'recipient_email': 'client@test.com',
                    'subject': 'Test',
                    'body_html': '<p>Test</p>',
                    'body_text': 'Test',
                    'scheduled_time': (now - timedelta(minutes=1)).isoformat() + 'Z',
                    'status': 'scheduled',
                    'retry_count': 3  # Max retries
                }
            ]
        }
        mock_send.side_effect = Exception('SMTP error')
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] == 200
        # Should mark as failed
        calls = mock_table.put_item.call_args_list
        assert len(calls) > 0


class TestCancelScheduledEmail:
    """Test email cancellation"""
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_cancel_email_success(self, mock_table, mock_user, mock_scheduled_email):
        """Test successful email cancellation"""
        mock_scheduled_email['user_id'] = mock_user['id']  # Ensure ownership
        mock_table.get_item.return_value = {'Item': mock_scheduled_email}
        
        response = handle_cancel_scheduled_email(mock_user, 'email-123')
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'cancelled' in body_data['message'].lower()
        mock_table.put_item.assert_called_once()
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_cancel_email_validates_ownership(self, mock_table, mock_user):
        """Test that users can only cancel their own emails"""
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'email-123',
                'user_id': 'different-user',
                'status': 'scheduled'
            }
        }
        
        response = handle_cancel_scheduled_email(mock_user, 'email-123')
        
        assert response['statusCode'] == 403
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_cancel_email_not_found(self, mock_table, mock_user):
        """Test cancelling non-existent email"""
        mock_table.get_item.return_value = {}
        
        response = handle_cancel_scheduled_email(mock_user, 'email-123')
        
        assert response['statusCode'] == 404
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_cancel_already_sent_email_fails(self, mock_table, mock_user, mock_scheduled_email):
        """Test that already sent emails cannot be cancelled"""
        mock_scheduled_email['status'] = 'sent'
        mock_scheduled_email['user_id'] = mock_user['id']
        mock_table.get_item.return_value = {'Item': mock_scheduled_email}
        
        response = handle_cancel_scheduled_email(mock_user, 'email-123')
        
        assert response['statusCode'] == 400


class TestListScheduledEmails:
    """Test listing scheduled emails"""
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_list_all_scheduled_emails(self, mock_table, mock_user, mock_scheduled_email):
        """Test listing all scheduled emails for user"""
        email1 = mock_scheduled_email.copy()
        email1['user_id'] = mock_user['id']
        email2 = mock_scheduled_email.copy()
        email2['user_id'] = mock_user['id']
        email2['id'] = 'email-456'
        mock_table.query.return_value = {
            'Items': [email1, email2]
        }
        
        response = handle_list_scheduled_emails(mock_user, None)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert 'scheduled_emails' in body_data
        assert body_data['count'] == 2
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_list_scheduled_emails_filtered_by_gallery(self, mock_table, mock_user, mock_scheduled_email):
        """Test filtering scheduled emails by gallery"""
        mock_scheduled_email['gallery_id'] = 'gallery-123'
        mock_scheduled_email['user_id'] = mock_user['id']
        mock_table.query.return_value = {'Items': [mock_scheduled_email]}
        
        response = handle_list_scheduled_emails(mock_user, 'gallery-123')
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['count'] == 1
        assert body_data['scheduled_emails'][0]['gallery_id'] == 'gallery-123'


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_handle_database_errors_gracefully(self, mock_table, mock_user):
        """Test graceful handling of database errors"""
        mock_table.query.side_effect = Exception('Database error')
        
        response = handle_list_scheduled_emails(mock_user, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('handlers.email_automation_handler.email_queue_table')
    def test_process_queue_handles_empty_queue(self, mock_table):
        """Test processing an empty queue"""
        mock_table.scan.return_value = {'Items': []}
        
        response = handle_process_email_queue()
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['processed'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
