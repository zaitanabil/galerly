"""
Email Automation Handler
Automated email triggers and scheduling system for Pro/Ultimate plans
"""
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, galleries_table, users_table, photos_table
from utils.response import create_response
from utils.email import (
    send_gallery_expiration_reminder_email,
    send_selection_reminder_email,
    send_download_reminder_email
)
from handlers.notification_handler import should_send_notification
from handlers.subscription_handler import get_user_features

# Email automation queue table
email_queue_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_EMAIL_QUEUE', 'galerly-email-queue-local'))


def handle_schedule_automated_email(user, body):
    """
    Schedule an automated email to be sent at a specific time
    Pro/Ultimate plan feature
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        email_type = body.get('email_type')  # 'expiration_reminder', 'selection_reminder', 'download_reminder'
        gallery_id = body.get('gallery_id')
        scheduled_time = body.get('scheduled_time')  # ISO format
        recipient_email = body.get('recipient_email')
        
        if not all([email_type, gallery_id, scheduled_time, recipient_email]):
            return create_response(400, {'error': 'Missing required fields'})
        
        # Validate scheduled time is not in the past
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            if scheduled_dt < datetime.utcnow().replace(tzinfo=scheduled_dt.tzinfo):
                return create_response(400, {'error': 'Cannot schedule emails in the past'})
        except ValueError:
            return create_response(400, {'error': 'Invalid scheduled_time format'})
        
        # Validate email type
        allowed_types = ['expiration_reminder', 'selection_reminder', 'download_reminder', 'custom']
        if email_type not in allowed_types:
            return create_response(400, {'error': f'Invalid email type. Allowed: {", ".join(allowed_types)}'})
        
        # Create scheduled email
        email_id = str(uuid.uuid4())
        scheduled_email = {
            'id': email_id,
            'user_id': user['id'],
            'gallery_id': gallery_id,
            'email_type': email_type,
            'recipient_email': recipient_email,
            'scheduled_time': scheduled_time,
            'status': 'scheduled',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'attempts': 0
        }
        
        # Add custom data if provided
        if 'subject' in body:
            scheduled_email['custom_subject'] = body['subject']
        if 'body' in body:
            scheduled_email['custom_body'] = body['body']
        
        email_queue_table.put_item(Item=scheduled_email)
        
        return create_response(200, {
            'email_id': email_id,
            'scheduled_time': scheduled_time,
            'message': 'Email scheduled successfully'
        })
        
    except Exception as e:
        print(f"Error scheduling email: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to schedule email'})


def handle_process_email_queue(event, context):
    """
    Scheduled Lambda function to process pending emails in the queue
    Runs every hour via EventBridge
    """
    try:
        print("🔄 Processing email queue...")
        
        current_time = datetime.utcnow()
        current_time_str = current_time.isoformat() + 'Z'
        
        # Scan for emails that are ready to send
        response = email_queue_table.scan(
            FilterExpression=Attr('status').eq('scheduled') & Attr('scheduled_time').lte(current_time_str)
        )
        
        pending_emails = response.get('Items', [])
        print(f"Found {len(pending_emails)} emails ready to send")
        
        sent_count = 0
        failed_count = 0
        
        for email in pending_emails:
            try:
                result = _send_automated_email(email)
                
                if result['success']:
                    # Update status to sent
                    email_queue_table.update_item(
                        Key={'id': email['id']},
                        UpdateExpression='SET #status = :sent, sent_at = :now, attempts = :attempts',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':sent': 'sent',
                            ':now': datetime.utcnow().isoformat() + 'Z',
                            ':attempts': email.get('attempts', 0) + 1
                        }
                    )
                    sent_count += 1
                    print(f"✓ Sent email {email['id']}")
                else:
                    # Update attempt count and schedule retry
                    attempts = email.get('attempts', 0) + 1
                    
                    if attempts >= 3:
                        # Max attempts reached, mark as failed
                        email_queue_table.update_item(
                            Key={'id': email['id']},
                            UpdateExpression='SET #status = :failed, attempts = :attempts, error = :error',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={
                                ':failed': 'failed',
                                ':attempts': attempts,
                                ':error': result.get('error', 'Unknown error')
                            }
                        )
                    else:
                        # Schedule retry in 1 hour
                        retry_time = current_time + timedelta(hours=1)
                        email_queue_table.update_item(
                            Key={'id': email['id']},
                            UpdateExpression='SET attempts = :attempts, scheduled_time = :retry_time',
                            ExpressionAttributeValues={
                                ':attempts': attempts,
                                ':retry_time': retry_time.isoformat() + 'Z'
                            }
                        )
                    
                    failed_count += 1
                    print(f"✗ Failed to send email {email['id']}: {result.get('error')}")
                    
            except Exception as e:
                failed_count += 1
                print(f"Error processing email {email.get('id')}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        result = {
            'processed': len(pending_emails),
            'sent': sent_count,
            'failed': failed_count
        }
        
        print(f"Email queue processing completed: {sent_count} sent, {failed_count} failed")
        return create_response(200, result)
        
    except Exception as e:
        print(f"Error processing email queue: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': str(e)})


def _send_automated_email(email):
    """Send a single automated email"""
    try:
        email_type = email.get('email_type')
        gallery_id = email.get('gallery_id')
        recipient_email = email.get('recipient_email')
        user_id = email.get('user_id')
        
        # Get gallery details
        gallery_response = galleries_table.scan(
            FilterExpression=Attr('id').eq(gallery_id)
        )
        galleries = gallery_response.get('Items', [])
        if not galleries:
            return {'success': False, 'error': 'Gallery not found'}
        
        gallery = galleries[0]
        
        # Get user details
        user_response = users_table.scan(
            FilterExpression=Attr('id').eq(user_id)
        )
        users = user_response.get('Items', [])
        if not users:
            return {'success': False, 'error': 'User not found'}
        
        user = users[0]
        
        # Check notification preferences
        if not should_send_notification(user_id, email_type.replace('_reminder', '')):
            print(f"Notifications disabled for {email_type}")
            return {'success': True, 'skipped': True}
        
        # Send appropriate email based on type
        frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
        gallery_url = f"{frontend_url}/client-gallery/{gallery_id}"
        
        success = False
        
        if email_type == 'expiration_reminder':
            expiration_date = gallery.get('expiration_date', 'soon')
            success = send_gallery_expiration_reminder_email(
                recipient_email,
                user.get('name', 'Photographer'),
                gallery.get('name', 'Your gallery'),
                gallery_url,
                expiration_date
            )
        
        elif email_type == 'selection_reminder':
            success = send_selection_reminder_email(
                recipient_email,
                gallery.get('client_name', 'Client'),
                gallery.get('name', 'Your gallery'),
                gallery_url,
                user.get('name', 'Photographer')
            )
        
        elif email_type == 'download_reminder':
            success = send_download_reminder_email(
                recipient_email,
                gallery.get('client_name', 'Client'),
                gallery.get('name', 'Your gallery'),
                gallery_url
            )
        
        elif email_type == 'custom':
            # Send custom email with user-defined content
            from utils.email import send_custom_email
            subject = email.get('custom_subject', 'Message from your photographer')
            body = email.get('custom_body', '')
            success = send_custom_email(recipient_email, subject, body)
        
        return {'success': success}
        
    except Exception as e:
        print(f"Error sending automated email: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def handle_setup_gallery_automation(user, body):
    """
    Setup automated emails for a gallery
    Schedules expiration reminders, selection reminders based on gallery settings
    """
    try:
        # Check plan
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        gallery_id = body.get('gallery_id')
        automation_settings = body.get('automation_settings', {})
        
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id required'})
        
        # Get gallery
        from utils.config import galleries_table
        gallery_response = galleries_table.get_item(Key={'id': gallery_id})
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Item']
        
        # Verify ownership
        if gallery.get('user_id') != user['id']:
            return create_response(403, {'error': 'Unauthorized'})
        scheduled_emails = []
        
        # Get current time with timezone info for comparison
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        
        # Schedule expiration reminder (7 days before, 1 day before)
        if automation_settings.get('expiration_reminders', True) and gallery.get('expiration_date'):
            expiration_date = datetime.fromisoformat(gallery['expiration_date'].replace('Z', '+00:00'))
            
            # 7 days before
            reminder_7d = expiration_date - timedelta(days=7)
            if reminder_7d > now_utc:
                scheduled_emails.append({
                    'email_type': 'expiration_reminder',
                    'scheduled_time': reminder_7d.isoformat().replace('+00:00', 'Z'),
                    'recipient_email': gallery.get('client_email'),
                    'gallery_id': gallery_id
                })
            
            # 1 day before
            reminder_1d = expiration_date - timedelta(days=1)
            if reminder_1d > now_utc:
                scheduled_emails.append({
                    'email_type': 'expiration_reminder',
                    'scheduled_time': reminder_1d.isoformat().replace('+00:00', 'Z'),
                    'recipient_email': gallery.get('client_email'),
                    'gallery_id': gallery_id
                })
        
        # Schedule selection reminder (if selection_deadline is set)
        if automation_settings.get('selection_reminders', True) and gallery.get('selection_deadline'):
            deadline = datetime.fromisoformat(gallery['selection_deadline'].replace('Z', '+00:00'))
            
            # 3 days before deadline
            reminder_3d = deadline - timedelta(days=3)
            if reminder_3d > now_utc:
                scheduled_emails.append({
                    'email_type': 'selection_reminder',
                    'scheduled_time': reminder_3d.isoformat().replace('+00:00', 'Z'),
                    'recipient_email': gallery.get('client_email'),
                    'gallery_id': gallery_id
                })
        
        # Schedule download reminder (X days after gallery creation)
        if automation_settings.get('download_reminders', True):
            reminder_days = automation_settings.get('download_reminder_days', 14)
            created_at = datetime.fromisoformat(gallery['created_at'].replace('Z', '+00:00'))
            reminder_time = created_at + timedelta(days=reminder_days)
            
            if reminder_time > now_utc:
                scheduled_emails.append({
                    'email_type': 'download_reminder',
                    'scheduled_time': reminder_time.isoformat().replace('+00:00', 'Z'),
                    'recipient_email': gallery.get('client_email'),
                    'gallery_id': gallery_id
                })
        
        # Save all scheduled emails
        for email_data in scheduled_emails:
            email_data.update({
                'id': str(uuid.uuid4()),
                'user_id': user['id'],
                'status': 'scheduled',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'attempts': 0
            })
            email_queue_table.put_item(Item=email_data)
        
        return create_response(200, {
            'scheduled_emails': len(scheduled_emails),
            'emails': scheduled_emails,
            'message': f'Scheduled {len(scheduled_emails)} automated emails'
        })
        
    except Exception as e:
        print(f"Error setting up gallery automation: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to setup automation'})


def handle_cancel_scheduled_email(user, email_id):
    """Cancel a scheduled email"""
    try:
        # Get email
        response = email_queue_table.get_item(Key={'id': email_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Scheduled email not found'})
        
        email = response['Item']
        
        # Verify ownership
        if email.get('user_id') != user['id']:
            return create_response(403, {'error': 'Unauthorized'})
        
        # Only cancel if not yet sent
        if email.get('status') != 'scheduled':
            return create_response(400, {'error': f'Cannot cancel email with status: {email.get("status")}'})
        
        # Update status to cancelled
        email_queue_table.update_item(
            Key={'id': email_id},
            UpdateExpression='SET #status = :cancelled, cancelled_at = :now',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':cancelled': 'cancelled',
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        return create_response(200, {'message': 'Email cancelled successfully'})
        
    except Exception as e:
        print(f"Error cancelling email: {str(e)}")
        return create_response(500, {'error': 'Failed to cancel email'})


def handle_list_scheduled_emails(user, gallery_id=None):
    """List scheduled emails for user or specific gallery"""
    try:
        if gallery_id:
            # Get emails for specific gallery
            response = email_queue_table.scan(
                FilterExpression=Attr('user_id').eq(user['id']) & Attr('gallery_id').eq(gallery_id)
            )
        else:
            # Get all emails for user
            response = email_queue_table.scan(
                FilterExpression=Attr('user_id').eq(user['id'])
            )
        
        emails = response.get('Items', [])
        
        # Sort by scheduled time
        emails.sort(key=lambda x: x.get('scheduled_time', ''), reverse=True)
        
        return create_response(200, {
            'scheduled_emails': emails,
            'count': len(emails)
        })
        
    except Exception as e:
        print(f"Error listing scheduled emails: {str(e)}")
        return create_response(500, {'error': 'Failed to list emails'})
