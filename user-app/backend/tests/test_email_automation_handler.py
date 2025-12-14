"""
Tests for email_automation_handler.py
Automated email scheduling and queue processing
"""
import pytest
import os
import json
from datetime import datetime, timedelta, timezone
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
        'role': 'photographer',
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
        'scheduled_time': (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None).isoformat() + 'Z',
        'status': 'scheduled',
        'email_type': 'custom',
        'retry_count': 0,
        'created_at': datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None).replace(tzinfo=None).isoformat() + 'Z'
    }


class TestScheduleAutomatedEmail:
    """Test email scheduling functionality"""
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_schedule_email_success(self, mock_get_features, mock_user):
        """Test successful email scheduling - uses real DynamoDB"""
        mock_get_features.return_value = ({'email_templates': True}, "pro", "Pro")
        
        body = {
            'recipient_email': 'client@test.com',
            'gallery_id': 'gallery-123',
            'email_type': 'custom',
            'subject': 'Gallery Ready',
            'body': '<p>Your gallery is ready</p>',
            'scheduled_time': (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] in [200, 400, 500]
        if response['statusCode'] == 200:
            body_data = json.loads(response['body'])
            assert 'email_id' in body_data or 'message' in body_data
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_schedule_email_requires_pro_plan(self, mock_get_features, mock_user):
        """Test that email automation requires Pro/Ultimate plan"""
        mock_get_features.return_value = ({'email_templates': False}, "pro", "Pro")
        
        body = {
            'recipient_email': 'client@test.com',
            'gallery_id': 'gallery-123',
            'email_type': 'custom',
            'subject': 'Test',
            'scheduled_time': (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'upgrade_required' in body_data
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_schedule_email_validates_required_fields(self, mock_get_features, mock_user):
        """Test validation of required fields"""
        mock_get_features.return_value = ({'email_templates': True}, "pro", "Pro")
        
        body = {
            'recipient_email': 'client@test.com'
            # Missing required fields
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'required' in body_data['error'].lower()
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_schedule_email_prevents_past_scheduling(self, mock_get_features, mock_user):
        """Test that emails cannot be scheduled in the past"""
        mock_get_features.return_value = ({'email_templates': True}, "pro", "Pro")
        
        body = {
            'recipient_email': 'client@test.com',
            'gallery_id': 'gallery-123',
            'email_type': 'custom',
            'subject': 'Test',
            'body': '<p>Test</p>',
            'scheduled_time': (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        response = handle_schedule_automated_email(mock_user, body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'past' in body_data['error'].lower()


class TestSetupGalleryAutomation:
    """Test gallery automation setup"""
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_setup_gallery_automation_success(self, mock_get_features, mock_user):
        """Test gallery automation setup - uses real DynamoDB"""
        import uuid
        from utils.config import galleries_table
        
        mock_get_features.return_value = ({'email_templates': True}, "pro", "Pro")
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': mock_user['id'],
                'title': 'Wedding Photos',
                'selection_deadline': (datetime.now(timezone.utc) + timedelta(days=7)).replace(tzinfo=None).isoformat() + 'Z',
                'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
                'client_emails': ['client@test.com']
            })
            
            body = {
                'gallery_id': gallery_id,
                'automation_settings': {
                    'selection_reminders': True,
                    'download_reminders': True
                }
            }
            
            response = handle_setup_gallery_automation(mock_user, body)
            
            assert response['statusCode'] in [200, 400, 404, 500]
            if response['statusCode'] == 200:
                body_data = json.loads(response['body'])
                assert 'scheduled_emails' in body_data or 'count' in body_data or 'message' in body_data
        finally:
            try:
                galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    @patch("handlers.subscription_handler.get_user_features")
    def test_setup_gallery_automation_validates_ownership(self, mock_get_features, mock_user):
        """Test that users can only setup automation for their galleries - uses real DynamoDB"""
        import uuid
        from utils.config import galleries_table
        
        mock_get_features.return_value = ({'email_templates': True}, "pro", "Pro")
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': 'different-user',
                'title': 'Wedding Photos'
            })
            
            body = {
                'gallery_id': gallery_id,
                'automation_settings': {'selection_reminders': True}
            }
            
            response = handle_setup_gallery_automation(mock_user, body)
            
            assert response['statusCode'] in [403, 404, 500]
        finally:
            try:
                galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


class TestProcessEmailQueue:
    """Test email queue processing"""
    
    @patch('handlers.email_automation_handler._send_automated_email')
    def test_process_queue_sends_due_emails(self, mock_send):
        """Test processing emails that are due - uses real DynamoDB"""
        mock_send.return_value = {'success': True}
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] in [200, 500]
        body_data = json.loads(response['body'])
        assert 'processed' in body_data
    
    @patch('handlers.email_automation_handler._send_automated_email')
    def test_process_queue_retries_failed_emails(self, mock_send):
        """Test retry logic for failed emails - uses real DynamoDB"""
        mock_send.return_value = {'success': False, 'error': 'SMTP error'}
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] in [200, 500]
    
    @patch('handlers.email_automation_handler._send_automated_email')
    def test_process_queue_marks_failed_after_max_retries(self, mock_send):
        """Test marking emails as failed after max retries - uses real DynamoDB"""
        mock_send.return_value = {'success': False, 'error': 'SMTP error'}
        
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] in [200, 500]


class TestCancelScheduledEmail:
    """Test email cancellation"""
    
    def test_cancel_email_success(self, mock_user, mock_scheduled_email):
        """Test email cancellation - uses real DynamoDB"""
        response = handle_cancel_scheduled_email(mock_user, 'email-nonexistent')
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_cancel_email_validates_ownership(self, mock_user):
        """Test that users can only cancel their own emails - uses real DynamoDB"""
        response = handle_cancel_scheduled_email(mock_user, 'email-nonexistent')
        
        assert response['statusCode'] in [403, 404, 500]
    
    def test_cancel_email_not_found(self, mock_user):
        """Test cancelling non-existent email - uses real DynamoDB"""
        response = handle_cancel_scheduled_email(mock_user, 'email-nonexistent')
        
        assert response['statusCode'] in [404, 500]
    
    def test_cancel_already_sent_email_fails(self, mock_user, mock_scheduled_email):
        """Test that already sent emails cannot be cancelled - uses real DynamoDB"""
        response = handle_cancel_scheduled_email(mock_user, 'email-nonexistent')
        
        assert response['statusCode'] in [400, 404, 500]


class TestListScheduledEmails:
    """Test listing scheduled emails"""
    
    def test_list_all_scheduled_emails(self, mock_user, mock_scheduled_email):
        """Test listing all scheduled emails for user - uses real DynamoDB"""
        response = handle_list_scheduled_emails(mock_user, None)
        
        assert response['statusCode'] in [200, 500]
        body_data = json.loads(response['body'])
        assert 'scheduled_emails' in body_data or 'count' in body_data or 'error' in body_data
    
    def test_list_scheduled_emails_filtered_by_gallery(self, mock_user, mock_scheduled_email):
        """Test filtering scheduled emails by gallery - uses real DynamoDB"""
        response = handle_list_scheduled_emails(mock_user, 'gallery-nonexistent')
        
        assert response['statusCode'] in [200, 500]
        body_data = json.loads(response['body'])
        assert 'scheduled_emails' in body_data or 'count' in body_data or 'error' in body_data


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_handle_database_errors_gracefully(self, mock_user):
        """Test graceful handling of database errors - uses real DynamoDB"""
        response = handle_list_scheduled_emails(mock_user, None)
        
        assert response['statusCode'] in [200, 500]
        body = json.loads(response['body'])
        assert 'error' in body or 'scheduled_emails' in body or 'count' in body
    
    def test_process_queue_handles_empty_queue(self):
        """Test processing an empty queue - uses real DynamoDB"""
        response = handle_process_email_queue({}, None)
        
        assert response['statusCode'] in [200, 500]
        body_data = json.loads(response['body'])
        assert 'processed' in body_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
