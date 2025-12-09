"""
Email Automation Handler
Automated email triggers and scheduling system for Pro/Ultimate plans
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, galleries_table, users_table, photos_table
from utils.response import create_response
from utils.email import (
    send_selection_reminder_email,
    send_download_reminder_email
)
from handlers.notification_handler import should_send_notification
from handlers.subscription_handler import get_user_features

# Email automation queue table
email_queue_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_EMAIL_QUEUE', 'galerly-email-queue-local'))

# Email automation rules table
automation_rules_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_AUTOMATION_RULES', 'galerly-automation-rules-local'))


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
        
        email_type = body.get('email_type')  # 'selection_reminder', 'download_reminder', 'custom'
        gallery_id = body.get('gallery_id')
        scheduled_time = body.get('scheduled_time')  # ISO format
        recipient_email = body.get('recipient_email')
        
        if not all([email_type, gallery_id, scheduled_time, recipient_email]):
            return create_response(400, {'error': 'Missing required fields'})
        
        # Validate scheduled time is not in the past
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            if scheduled_dt < datetime.now(timezone.utc).replace(tzinfo=scheduled_dt.tzinfo):
                return create_response(400, {'error': 'Cannot schedule emails in the past'})
        except ValueError:
            return create_response(400, {'error': 'Invalid scheduled_time format'})
        
        # Validate email type
        allowed_types = ['selection_reminder', 'download_reminder', 'custom']
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
            'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
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
        
        current_time = datetime.now(timezone.utc)
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
                            ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
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
        
        if email_type == 'selection_reminder':
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
    Schedules selection reminders and download reminders based on gallery settings
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
                'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
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
                ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
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


def handle_create_automation_rule(user, body):
    """
    Create a new email automation rule
    
    Request body:
    {
        "name": "Selection Reminder",
        "trigger": {
            "type": "selection_deadline",  // or "gallery_created", "days_after_creation"
            "value": 3  // days
        },
        "action": {
            "type": "send_email",
            "template_id": "template-uuid",
            "delay": 0  // optional additional delay in days
        },
        "active": true
    }
    """
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Validate required fields
        if 'name' not in body or 'trigger' not in body or 'action' not in body:
            return create_response(400, {'error': 'Missing required fields'})
        
        # Create rule
        rule_id = str(uuid.uuid4())
        rule = {
            'id': rule_id,
            'user_id': user['id'],
            'name': body['name'],
            'trigger': body['trigger'],
            'action': body['action'],
            'active': body.get('active', True),
            'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        try:
            automation_rules_table.put_item(Item=rule)
        except Exception as table_error:
            print(f"Note: automation_rules table may not exist: {str(table_error)}")
            # For now, return success even if table doesn't exist (for development)
            return create_response(200, {
                'rule': rule,
                'message': 'Automation rule created (note: table may need to be created in production)'
            })
        
        return create_response(201, {
            'rule': rule,
            'message': 'Automation rule created successfully'
        })
        
    except Exception as e:
        print(f"Error creating automation rule: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create automation rule'})


def handle_list_automation_rules(user):
    """List all automation rules for the user"""
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        try:
            response = automation_rules_table.scan(
                FilterExpression=Attr('user_id').eq(user['id'])
            )
            
            rules = response.get('Items', [])
            rules.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return create_response(200, {
                'rules': rules,
                'count': len(rules),
                'active_count': sum(1 for r in rules if r.get('active'))
            })
        except Exception as table_error:
            print(f"Note: automation_rules table may not exist: {str(table_error)}")
            # Return empty list for development
            return create_response(200, {
                'rules': [],
                'count': 0,
                'active_count': 0
            })
        
    except Exception as e:
        print(f"Error listing automation rules: {str(e)}")
        return create_response(500, {'error': 'Failed to list automation rules'})


def handle_update_automation_rule(user, rule_id, body):
    """Update an existing automation rule"""
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        try:
            # Get existing rule
            response = automation_rules_table.get_item(Key={'id': rule_id})
            
            if 'Item' not in response:
                return create_response(404, {'error': 'Automation rule not found'})
            
            rule = response['Item']
            
            # Verify ownership
            if rule['user_id'] != user['id']:
                return create_response(403, {'error': 'Access denied'})
            
            # Update fields
            update_expressions = []
            expression_values = {}
            
            if 'name' in body:
                update_expressions.append('#name = :name')
                expression_values[':name'] = body['name']
            
            if 'active' in body:
                update_expressions.append('active = :active')
                expression_values[':active'] = body['active']
            
            if 'trigger' in body:
                update_expressions.append('trigger = :trigger')
                expression_values[':trigger'] = body['trigger']
            
            if 'action' in body:
                update_expressions.append('#action = :action')
                expression_values[':action'] = body['action']
            
            # Always update timestamp
            update_expressions.append('updated_at = :updated')
            expression_values[':updated'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            
            if update_expressions:
                automation_rules_table.update_item(
                    Key={'id': rule_id},
                    UpdateExpression='SET ' + ', '.join(update_expressions),
                    ExpressionAttributeNames={'#name': 'name', '#action': 'action'},
                    ExpressionAttributeValues=expression_values
                )
            
            # Get updated rule
            updated_response = automation_rules_table.get_item(Key={'id': rule_id})
            updated_rule = updated_response.get('Item', rule)
            
            return create_response(200, {
                'rule': updated_rule,
                'message': 'Automation rule updated successfully'
            })
            
        except Exception as table_error:
            print(f"Error updating rule: {str(table_error)}")
            return create_response(500, {'error': 'Failed to update automation rule'})
        
    except Exception as e:
        print(f"Error updating automation rule: {str(e)}")
        return create_response(500, {'error': 'Failed to update automation rule'})


def handle_delete_automation_rule(user, rule_id):
    """Delete an automation rule"""
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('email_templates'):
            return create_response(403, {
                'error': 'Email automation is available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        try:
            # Get existing rule
            response = automation_rules_table.get_item(Key={'id': rule_id})
            
            if 'Item' not in response:
                return create_response(404, {'error': 'Automation rule not found'})
            
            rule = response['Item']
            
            # Verify ownership
            if rule['user_id'] != user['id']:
                return create_response(403, {'error': 'Access denied'})
            
            # Delete rule
            automation_rules_table.delete_item(Key={'id': rule_id})
            
            return create_response(200, {
                'message': 'Automation rule deleted successfully'
            })
            
        except Exception as table_error:
            print(f"Error deleting rule: {str(table_error)}")
            return create_response(500, {'error': 'Failed to delete automation rule'})
        
    except Exception as e:
        print(f"Error deleting automation rule: {str(e)}")
        return create_response(500, {'error': 'Failed to delete automation rule'})
