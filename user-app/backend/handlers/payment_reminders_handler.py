"""
Payment Reminder Automation
Automated reminders for unpaid invoices and pending payments
Pro+ feature - requires Pro or Ultimate plan
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, users_table
from utils.response import create_response
from utils.email import send_email
from handlers.subscription_handler import get_user_features
import os

# Initialize DynamoDB tables
invoices_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_INVOICES'))
payment_reminders_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PAYMENT_REMINDERS'))


def handle_create_reminder_schedule(user, invoice_id, body):
    """
    Create automated payment reminder schedule - Pro+ feature
    
    POST /api/v1/invoices/{invoice_id}/reminders
    Body: {
        "reminder_days": [7, 3, 1],  // Days before due date
        "overdue_days": [1, 7, 14],  // Days after due date
        "custom_message": "Optional custom message"
    }
    """
    try:
        # Check plan permission - Pro+ feature
        features, _, _ = get_user_features(user)
        if not features.get('client_invoicing'):
            return create_response(403, {
                'error': 'Payment reminders require Pro plan',
                'upgrade_required': True,
                'required_feature': 'client_invoicing'
            })
        
        # Get invoice
        invoice_response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in invoice_response:
            return create_response(404, {'error': 'Invoice not found'})
        
        invoice = invoice_response['Item']
        
        # Verify ownership
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Check if invoice is already paid
        if invoice.get('status') == 'paid':
            return create_response(400, {'error': 'Invoice is already paid'})
        
        reminder_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Calculate reminder dates
        due_date = datetime.fromisoformat(invoice.get('due_date', timestamp).replace('Z', '+00:00'))
        
        reminders = []
        
        # Before due date reminders
        for days in body.get('reminder_days', [7, 3, 1]):
            reminder_date = due_date - timedelta(days=days)
            # Compare timezone-aware datetimes
            if reminder_date > datetime.now(timezone.utc).replace(tzinfo=reminder_date.tzinfo):
                reminders.append({
                    'type': 'before_due',
                    'days': days,
                    'send_at': reminder_date.isoformat().replace('+00:00', 'Z'),
                    'sent': False
                })
        
        # Overdue reminders
        for days in body.get('overdue_days', [1, 7, 14]):
            reminder_date = due_date + timedelta(days=days)
            reminders.append({
                'type': 'overdue',
                'days': days,
                'send_at': reminder_date.isoformat().replace('+00:00', 'Z'),
                'sent': False
            })
        
        reminder_schedule = {
            'id': reminder_id,
            'invoice_id': invoice_id,
            'photographer_id': user['id'],
            'client_email': invoice['client_email'],
            'reminders': reminders,
            'custom_message': body.get('custom_message', ''),
            'status': 'active',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        payment_reminders_table.put_item(Item=reminder_schedule)
        
        return create_response(201, reminder_schedule)
        
    except Exception as e:
        print(f"Error creating reminder schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create reminder schedule'})


def handle_process_payment_reminders(event, context):
    """
    Process pending payment reminders (scheduled Lambda - runs daily)
    Checks for reminders that need to be sent
    """
    try:
        # Scan for active reminder schedules
        response = payment_reminders_table.scan(
            FilterExpression=Attr('status').eq('active')
        )
        
        schedules = response.get('Items', [])
        sent_count = 0
        
        for schedule in schedules:
            try:
                # Check each reminder in the schedule
                reminders = schedule.get('reminders', [])
                invoice_id = schedule['invoice_id']
                
                # Get invoice to check if still unpaid
                invoice_response = invoices_table.get_item(Key={'id': invoice_id})
                if 'Item' not in invoice_response:
                    continue
                
                invoice = invoice_response['Item']
                
                # Skip if invoice is paid
                if invoice.get('status') == 'paid':
                    # Mark schedule as completed
                    payment_reminders_table.update_item(
                        Key={'id': schedule['id']},
                        UpdateExpression='SET #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': 'completed'}
                    )
                    continue
                
                # Check each reminder
                updated_reminders = []
                for reminder in reminders:
                    if not reminder.get('sent'):
                        send_at = datetime.fromisoformat(reminder['send_at'].replace('Z', '+00:00'))
                        
                        # Send if time has passed
                        if datetime.now(timezone.utc).replace(tzinfo=None) >= send_at:
                            # Get photographer details
                            photographer_response = users_table.get_item(
                                Key={'id': schedule['photographer_id']}
                            )
                            photographer = photographer_response['Item']
                            
                            # Send reminder email
                            subject = f"Payment Reminder: Invoice #{invoice.get('invoice_number', invoice_id[:8])}"
                            
                            if reminder['type'] == 'before_due':
                                body_html = f"""
                                <h2>Payment Reminder</h2>
                                <p>Hi {invoice.get('client_name', 'there')},</p>
                                <p>This is a friendly reminder that your invoice is due in {reminder['days']} day(s).</p>
                                <p><strong>Invoice #{invoice.get('invoice_number', invoice_id[:8])}</strong></p>
                                <p><strong>Amount Due:</strong> ${invoice.get('total_amount', 0)}</p>
                                <p><strong>Due Date:</strong> {invoice.get('due_date', '')[:10]}</p>
                                {f"<p>{schedule.get('custom_message', '')}</p>" if schedule.get('custom_message') else ''}
                                <p><a href="{os.environ.get('FRONTEND_URL')}/invoices/view/{invoice_id}">View Invoice</a></p>
                                <p>Thank you!<br>{photographer.get('name', 'Your photographer')}</p>
                                """
                            else:  # overdue
                                body_html = f"""
                                <h2>Overdue Payment Notice</h2>
                                <p>Hi {invoice.get('client_name', 'there')},</p>
                                <p>Your invoice is now {reminder['days']} day(s) overdue.</p>
                                <p><strong>Invoice #{invoice.get('invoice_number', invoice_id[:8])}</strong></p>
                                <p><strong>Amount Due:</strong> ${invoice.get('total_amount', 0)}</p>
                                <p><strong>Original Due Date:</strong> {invoice.get('due_date', '')[:10]}</p>
                                {f"<p>{schedule.get('custom_message', '')}</p>" if schedule.get('custom_message') else ''}
                                <p>Please submit payment as soon as possible to avoid any service interruptions.</p>
                                <p><a href="{os.environ.get('FRONTEND_URL')}/invoices/view/{invoice_id}">View & Pay Invoice</a></p>
                                <p>Thank you!<br>{photographer.get('name', 'Your photographer')}</p>
                                """
                            
                            send_email(
                                to_addresses=[schedule['client_email']],
                                subject=subject,
                                body_html=body_html,
                                body_text=f"Payment reminder for invoice #{invoice.get('invoice_number', invoice_id[:8])}. Amount due: ${invoice.get('total_amount', 0)}"
                            )
                            
                            reminder['sent'] = True
                            reminder['sent_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                            sent_count += 1
                    
                    updated_reminders.append(reminder)
                
                # Update reminder schedule
                payment_reminders_table.update_item(
                    Key={'id': schedule['id']},
                    UpdateExpression='SET reminders = :reminders, updated_at = :updated_at',
                    ExpressionAttributeValues={
                        ':reminders': updated_reminders,
                        ':updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                    }
                )
                
                # Check if all reminders sent
                if all(r.get('sent') for r in updated_reminders):
                    payment_reminders_table.update_item(
                        Key={'id': schedule['id']},
                        UpdateExpression='SET #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': 'completed'}
                    )
                
            except Exception as reminder_error:
                print(f"Error processing reminder {schedule.get('id')}: {str(reminder_error)}")
                continue
        
        print(f"Processed payment reminders: {sent_count} sent")
        
        return {
            'statusCode': 200,
            'body': f'Processed {sent_count} reminders'
        }
        
    except Exception as e:
        print(f"Error processing payment reminders: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': 'Error processing reminders'
        }


def handle_cancel_reminder_schedule(user, invoice_id):
    """Cancel payment reminder schedule - Pro+ feature"""
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('client_invoicing'):
            return create_response(403, {
                'error': 'Payment reminders require Pro plan',
                'upgrade_required': True
            })
        
        # Find schedule for this invoice
        response = payment_reminders_table.scan(
            FilterExpression=Attr('invoice_id').eq(invoice_id) & Attr('photographer_id').eq(user['id']) & Attr('status').eq('active')
        )
        
        schedules = response.get('Items', [])
        
        for schedule in schedules:
            payment_reminders_table.update_item(
                Key={'id': schedule['id']},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'cancelled',
                    ':updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                }
            )
        
        return create_response(200, {'message': 'Payment reminder schedule cancelled'})
        
    except Exception as e:
        print(f"Error cancelling reminder schedule: {str(e)}")
        return create_response(500, {'error': 'Failed to cancel reminder schedule'})
