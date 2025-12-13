"""
Notification Preferences Handler
Manages email notification settings for photographers and their clients
"""
import boto3
import json
from datetime import datetime, timezone
from utils.response import create_response
from utils.email import (
    send_gallery_ready_email,
    send_selection_reminder_email,
    send_custom_email,
    send_client_selected_photos_email,
    send_client_feedback_email,
    send_payment_received_email,
    send_new_photos_added_email
)
from utils.plan_enforcement import require_role

# DynamoDB setup
from utils.config import dynamodb, users_table, galleries_table
import os
preferences_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NOTIFICATION_PREFERENCES'))

# Default notification preferences for new users
DEFAULT_PREFERENCES = {
    'client_notifications': {
        'gallery_shared': True,
        'new_photos_added': True,
        'gallery_ready': True,
        'selection_reminder': True,
        'payment_received': True,
        'custom_messages': True
    },
    'photographer_notifications': {
        'client_selected_photos': True,
        'client_feedback_received': True,
        'gallery_viewed': True
    }
}


def get_notification_preferences(user_id):
    """
    Get notification preferences for a user
    Creates default preferences if none exist
    """
    try:
        response = preferences_table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            return response['Item']
        else:
            # Create default preferences
            preferences = {
                'user_id': user_id,
                **DEFAULT_PREFERENCES,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            preferences_table.put_item(Item=preferences)
            return preferences
            
    except Exception as e:
        print(f"Error getting notification preferences: {str(e)}")
        return {
            'user_id': user_id,
            **DEFAULT_PREFERENCES
        }


def update_notification_preferences(user_id, preferences_update):
    """Update notification preferences for a user"""
    try:
        # Get current preferences
        current_prefs = get_notification_preferences(user_id)
        
        # Update preferences
        if 'client_notifications' in preferences_update:
            current_prefs['client_notifications'].update(preferences_update['client_notifications'])
        
        if 'photographer_notifications' in preferences_update:
            current_prefs['photographer_notifications'].update(preferences_update['photographer_notifications'])
        
        current_prefs['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save to DynamoDB
        preferences_table.put_item(Item=current_prefs)
        
        return current_prefs
        
    except Exception as e:
        print(f"Error updating notification preferences: {str(e)}")
        raise


def should_send_notification(user_id, notification_type, notification_category='client_notifications'):
    """Check if a notification should be sent based on user preferences"""
    try:
        prefs = get_notification_preferences(user_id)
        category_prefs = prefs.get(notification_category, {})
        return category_prefs.get(notification_type, True)
    except Exception as e:
        print(f"Error checking notification preference: {str(e)}")
        return True  # Default to sending if error


def notify_gallery_shared(gallery_id, client_email, client_name, photographer_name, gallery_url, description='', user_id=None):
    """Send notification when gallery is shared with client"""
    try:
        # Check if client wants this notification (if they have an account)
        # For now, send to all clients as they may not have preferences yet
        from utils.email import send_gallery_shared_email
        return send_gallery_shared_email(
            client_email, client_name, photographer_name,
            gallery_id, gallery_url, description, user_id=user_id
        )
    except Exception as e:
        print(f"Error sending gallery shared notification: {str(e)}")
        return False


def notify_new_photos_added(user_id, gallery_id, client_email, client_name, photographer_name, gallery_url, photo_count):
    """Send notification when new photos are added to gallery"""
    try:
        if should_send_notification(user_id, 'new_photos_added'):
            return send_new_photos_added_email(
                client_email, client_name, photographer_name,
                gallery_id, gallery_url, photo_count, user_id=user_id
            )
        return False
    except Exception as e:
        print(f"Error sending new photos notification: {str(e)}")
        return False


def notify_gallery_ready(user_id, gallery_id, client_email, client_name, photographer_name, gallery_url, message=''):
    """Send notification when gallery is ready for viewing"""
    try:
        if should_send_notification(user_id, 'gallery_ready'):
            return send_gallery_ready_email(
                client_email, client_name, photographer_name,
                gallery_id, gallery_url, message, user_id=user_id
            )
        return False
    except Exception as e:
        print(f"Error sending gallery ready notification: {str(e)}")
        return False


def notify_selection_reminder(user_id, gallery_id, client_email, client_name, photographer_name, gallery_url, message=''):
    """Send reminder to client to select photos"""
    try:
        if should_send_notification(user_id, 'selection_reminder'):
            return send_selection_reminder_email(
                client_email, client_name, photographer_name,
                gallery_id, gallery_url, message, user_id=user_id
            )
        return False
    except Exception as e:
        print(f"Error sending selection reminder: {str(e)}")
        return False


def notify_custom_message(user_id, client_email, client_name, photographer_name, subject, title, message, button_text='', button_url=''):
    """Send custom message from photographer to client"""
    try:
        if should_send_notification(user_id, 'custom_messages'):
            return send_custom_email(
                client_email, client_name, photographer_name,
                subject, title, message, button_text, button_url, user_id=user_id
            )
        return False
    except Exception as e:
        print(f"Error sending custom message: {str(e)}")
        return False


def notify_client_selected_photos(photographer_id, photographer_email, photographer_name, client_name, gallery_name, gallery_url, selection_count):
    """Notify photographer when client selects photos"""
    try:
        if should_send_notification(photographer_id, 'client_selected_photos', 'photographer_notifications'):
            return send_client_selected_photos_email(
                photographer_email, photographer_name, client_name,
                gallery_name, gallery_url, selection_count
            )
        return False
    except Exception as e:
        print(f"Error sending client selected photos notification: {str(e)}")
        return False


def notify_client_feedback(photographer_id, photographer_email, photographer_name, client_name, gallery_name, gallery_url, rating, feedback):
    """Notify photographer when client leaves feedback"""
    try:
        if should_send_notification(photographer_id, 'client_feedback_received', 'photographer_notifications'):
            return send_client_feedback_email(
                photographer_email, photographer_name, client_name,
                gallery_name, gallery_url, rating, feedback
            )
        return False
    except Exception as e:
        print(f"Error sending client feedback notification: {str(e)}")
        return False


def notify_payment_received(user_id, client_email, client_name, photographer_name, gallery_name, amount, payment_date, message=''):
    """Send payment confirmation to client"""
    try:
        if should_send_notification(user_id, 'payment_received'):
            return send_payment_received_email(
                client_email, client_name, photographer_name,
                gallery_name, amount, payment_date, message, user_id=user_id
            )
        return False
    except Exception as e:
        print(f"Error sending payment received notification: {str(e)}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API REQUEST HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@require_role('photographer')
def handle_get_preferences(user):
    """Get notification preferences for logged-in user"""
    try:
        user_id = user.get('id')
        preferences = get_notification_preferences(user_id)
        
        return create_response(200, {
            'success': True,
            'preferences': preferences
        })
        
    except Exception as e:
        print(f"Error in handle_get_preferences: {str(e)}")
        return create_response(500, {'error': 'Failed to get notification preferences'})


@require_role('photographer')
def handle_update_preferences(user, body):
    """Update notification preferences for logged-in user"""
    try:
        user_id = user.get('id')
        
        # Validate input
        if not isinstance(body, dict):
            return create_response(400, {'error': 'Invalid request body'})
        
        # Update preferences
        updated_prefs = update_notification_preferences(user_id, body)
        
        return create_response(200, {
            'success': True,
            'message': 'Notification preferences updated',
            'preferences': updated_prefs
        })
        
    except Exception as e:
        print(f"Error in handle_update_preferences: {str(e)}")
        return create_response(500, {'error': 'Failed to update notification preferences'})


@require_role('photographer')
def handle_send_custom_notification(user, body):
    """Send custom notification from photographer to client(s)"""
    try:
        user_id = user.get('id')
        photographer_name = user.get('full_name', 'Your photographer')
        
        # Validate required fields
        required_fields = ['gallery_id', 'subject', 'title', 'message']
        for field in required_fields:
            if field not in body:
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        gallery_id = body['gallery_id']
        subject = body['subject']
        title = body['title']
        message = body['message']
        button_text = body.get('button_text', '')
        button_url = body.get('button_url', '')
        
        # Get gallery to find client email
        gallery_response = galleries_table.get_item(
            Key={'user_id': user_id, 'id': gallery_id}
        )
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Item']
        client_email = gallery.get('client_email')
        client_name = gallery.get('client_name', 'Client')
        
        if not client_email:
            return create_response(400, {'error': 'Gallery has no client email'})
        
        # Send notification
        success = notify_custom_message(
            user_id, client_email, client_name, photographer_name,
            subject, title, message, button_text, button_url
        )
        
        if success:
            return create_response(200, {
                'success': True,
                'message': f'Notification sent to {client_email}'
            })
        else:
            return create_response(500, {'error': 'Failed to send notification'})
        
    except Exception as e:
        print(f"Error in handle_send_custom_notification: {str(e)}")
        return create_response(500, {'error': 'Failed to send notification'})


@require_role('photographer')
def handle_send_selection_reminder(user, body):
    """Send selection reminder to gallery clients"""
    try:
        user_id = user.get('id')
        photographer_name = user.get('full_name') or user.get('name') or user.get('username', 'Your photographer')
        
        # Validate required fields
        if 'gallery_id' not in body:
            return create_response(400, {'error': 'Missing required field: gallery_id'})
        
        gallery_id = body['gallery_id']
        custom_message = body.get('message', '')
        
        # Get gallery to find client emails
        gallery_response = galleries_table.get_item(
            Key={'user_id': user_id, 'id': gallery_id}
        )
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Item']
        client_emails = gallery.get('client_emails', [])
        client_name = gallery.get('client_name', 'Client')
        gallery_name = gallery.get('name', 'Your gallery')
        
        print(f"SELECTION REMINDER: gallery_id={gallery_id}")
        print(f"   Client emails: {client_emails}")
        
        # Validate client emails
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_emails = []
        invalid_emails = []
        
        for email in client_emails:
            email_str = str(email).strip().lower()
            if email_str and re.match(email_pattern, email_str):
                valid_emails.append(email_str)
            else:
                invalid_emails.append(email_str)
                print(f" Invalid email address: '{email_str}'")
        
        if not valid_emails:
            return create_response(400, {
                'error': 'No valid client email addresses found',
                'invalid_emails': invalid_emails,
                'hint': 'Please add valid email addresses in gallery settings'
            })
        
        # Build gallery URL
        import os
        frontend_url = os.environ.get('FRONTEND_URL')
        share_token = gallery.get('share_token', '')
        gallery_url = f"{frontend_url}/client-gallery?token={share_token}"
        
        # Send reminder to all clients
        success_count = 0
        failed_emails = []
        
        for client_email in valid_emails:
            try:
                print(f"  📤 Sending reminder to: {client_email}")
                success = notify_selection_reminder(
                    user_id, gallery_name, client_email, client_name,
                    photographer_name, gallery_url, custom_message
                )
                
                if success:
                    success_count += 1
                    print(f"  Reminder sent to {client_email}")
                else:
                    failed_emails.append(client_email)
                    print(f"  Failed to send reminder to {client_email}")
            except Exception as email_error:
                print(f"  Exception sending reminder to {client_email}: {str(email_error)}")
                failed_emails.append(client_email)
        
        response_data = {
            'success': True,
            'reminders_sent': success_count,
            'reminders_failed': len(failed_emails),
            'total_clients': len(valid_emails),
            'message': f'Selection reminder sent to {success_count} client(s)'
        }
        
        if failed_emails:
            response_data['failed_emails'] = failed_emails
            response_data['warning'] = f'Failed to send to {len(failed_emails)} email(s)'
        
        if invalid_emails:
            response_data['invalid_emails'] = invalid_emails
        
        print(f"Selection reminders complete: sent={success_count}, failed={len(failed_emails)}, invalid={len(invalid_emails)}")
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"Error in handle_send_selection_reminder: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to send reminder'})

