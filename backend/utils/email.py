"""
Email notification system using SMTP (Namecheap Private Email)
No AWS SES required - sends directly through your email provider
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def get_required_env(key):
    """Get required environment variable or raise error"""
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

# SMTP Configuration - ALL REQUIRED
SMTP_HOST = get_required_env('SMTP_HOST')
SMTP_PORT = int(get_required_env('SMTP_PORT'))
SMTP_USER = get_required_env('SMTP_USER')
SMTP_PASSWORD = get_required_env('SMTP_PASSWORD')
FROM_EMAIL = get_required_env('FROM_EMAIL')
FROM_NAME = get_required_env('FROM_NAME')

# Import branded email templates
from .email_templates_branded import BRANDED_EMAIL_TEMPLATES

# Use branded templates
EMAIL_TEMPLATES = BRANDED_EMAIL_TEMPLATES


def send_email(to_email, template_name, template_vars=None, user_id=None):
    """
    Send email using SMTP (Namecheap Private Email)
    
    Args:
        to_email: Recipient email address
        template_name: Template type to use
        template_vars: Variables to substitute in template
        user_id: If provided, uses custom Pro user templates
    """
    if template_vars is None:
        template_vars = {}
    
    # Get template (custom if user_id provided and they're Pro)
    if user_id:
        from handlers.email_template_handler import get_user_template
        try:
            template = get_user_template(user_id, template_name)
            if not template:
                print(f"⚠️  Custom template '{template_name}' not found for user {user_id}, using default")
                if template_name not in EMAIL_TEMPLATES:
                    print(f"❌ Default email template '{template_name}' not found")
                    return False
                template = EMAIL_TEMPLATES[template_name]
        except Exception as e:
            print(f"❌ Error loading custom template '{template_name}' for user {user_id}: {str(e)}")
            if template_name not in EMAIL_TEMPLATES:
                print(f"❌ Default email template '{template_name}' not found")
                return False
            template = EMAIL_TEMPLATES[template_name]
    else:
        if template_name not in EMAIL_TEMPLATES:
            print(f"❌ Email template '{template_name}' not found")
            return False
        template = EMAIL_TEMPLATES[template_name]
    
    # Validate template structure (both custom and default must have required keys)
    required_keys = ['subject', 'html', 'text']
    missing_keys = [key for key in required_keys if key not in template]
    if missing_keys:
        print(f"⚠️  Email template '{template_name}' missing required keys: {missing_keys}")
        return False
    
    # Check if SMTP password is configured
    if not SMTP_PASSWORD:
        print(f"❌ SMTP_PASSWORD not configured. Cannot send email.")
        return False
    
    # Format template with variables (wrapped in try-except for missing variables)
    try:
        subject = template['subject'].format(**template_vars)
        html_body = template['html'].format(**template_vars)
        text_body = template['text'].format(**template_vars)
    except KeyError as e:
        print(f"❌ Template variable error: Missing variable {e} in template '{template_name}'")
        print(f"   Available variables: {list(template_vars.keys())}")
        return False
    except Exception as e:
        print(f"❌ Error formatting template '{template_name}': {str(e)}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        
        # Attach both text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Connect to SMTP server and send
        print(f"🔌 Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            print(f"🔐 Starting TLS...")
            server.starttls()  # Upgrade to encrypted connection
            print(f"👤 Authenticating as {SMTP_USER}...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print(f"📤 Sending message...")
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email} via SMTP")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {str(e)}")
        print(f"   SMTP_USER used: {SMTP_USER}")
        print(f"   Check SMTP_USER and SMTP_PASSWORD in environment variables")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error sending email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_welcome_email(user_email, user_name):
    """Send welcome email to new user"""
    return send_email(
        user_email,
        'welcome',
        {
            'name': user_name or 'there',
            'dashboard_url': get_required_env('FRONTEND_URL') + '/dashboard'
        }
    )


def send_gallery_shared_email(client_email, client_name, photographer_name, gallery_name, gallery_url, description='', user_id=None):
    """
    Send notification when gallery is shared with client
    
    Checks if client has an account:
    - If YES: Sends email encouraging them to sign in to interact (approve, comment)
    - If NO: Sends email encouraging them to create account for full interaction, otherwise view-only
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    from utils.config import users_table
    
    # Check if client has an account
    has_account = False
    try:
        response = users_table.get_item(Key={'email': client_email.lower()})
        has_account = 'Item' in response
    except Exception as e:
        print(f"Error checking if client {client_email} has account: {str(e)}")
        # Default to no account if error
        has_account = False
    
    # Choose template based on account status
    if has_account:
        template_name = 'gallery_shared_with_account'
    else:
        template_name = 'gallery_shared_no_account'
    
    signup_url = f"{get_required_env('FRONTEND_URL')}/auth?email={client_email}&redirect=client-gallery"
    
    return send_email(
        client_email,
        template_name,
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'description': description or 'Check out your photos!',
            'signup_url': signup_url,
            'has_account': has_account
        },
        user_id=user_id  # Pass user_id for custom templates
    )


def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset email"""
    reset_url = f"{get_required_env('FRONTEND_URL')}/reset-password?token={reset_token}"
    return send_email(
        user_email,
        'password_reset',
        {
            'name': user_name or 'there',
            'reset_url': reset_url
        }
    )


def send_new_photos_added_email(client_email, client_name, photographer_name, gallery_name, gallery_url, photo_count, user_id=None):
    """
    Send notification when new photos are added to gallery
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        client_email,
        'new_photos_added',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'photo_count': photo_count
        },
        user_id=user_id
    )


def send_verification_code_email(user_email, code):
    """Send email verification code"""
    return send_email(
        user_email,
        'verification_code',
        {
            'code': code
        }
    )


def send_gallery_ready_email(client_email, client_name, photographer_name, gallery_name, gallery_url, message='', user_id=None):
    """
    Send notification when gallery is ready for viewing
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        client_email,
        'gallery_ready',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'message': message or 'Your photos are ready! Click below to view and select your favorites.'
        },
        user_id=user_id
    )


def send_selection_reminder_email(client_email, client_name, photographer_name, gallery_name, gallery_url, message='', user_id=None):
    """
    Send reminder to client to select photos
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        client_email,
        'selection_reminder',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'message': message or 'Please take a moment to select your favorite photos from the gallery.'
        },
        user_id=user_id
    )


def send_custom_email(client_email, client_name, photographer_name, subject, title, message, button_text='', button_url='', user_id=None):
    """
    Send custom message from photographer to client
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    button_html = ''
    if button_text and button_url:
        button_html = f'<a href="{button_url}" class="email-button">{button_text}</a>'
    
    return send_email(
        client_email,
        'custom_message',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'subject': subject,
            'title': title,
            'message': message,
            'button_html': button_html
        },
        user_id=user_id
    )


def send_gallery_expiring_email(client_email, client_name, photographer_name, gallery_name, gallery_url, days_remaining, user_id=None):
    """
    Send notification when gallery is about to expire - TO CLIENT
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        client_email,
        'gallery_expiring_soon',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'days_remaining': days_remaining
        },
        user_id=user_id
    )


def send_gallery_expiration_reminder_email(photographer_email, photographer_name, gallery_name, gallery_url, expiration_date):
    """Send expiration reminder to photographer - 7 days before expiration"""
    return send_email(
        photographer_email,
        'gallery_expiration_reminder',
        {
            'photographer_name': photographer_name or 'there',
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'expiration_date': expiration_date
        }
    )


def send_client_selected_photos_email(photographer_email, photographer_name, client_name, gallery_name, gallery_url, selection_count, user_id=None):
    """
    Notify photographer when client selects photos
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        photographer_email,
        'client_selected_photos',
        {
            'photographer_name': photographer_name or 'there',
            'client_name': client_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'selection_count': selection_count
        },
        user_id=user_id
    )


def send_client_feedback_email(photographer_email, photographer_name, client_name, gallery_name, gallery_url, rating, feedback, user_id=None):
    """
    Notify photographer when client leaves feedback
    
    Args:
        user_id: If provided, uses custom Pro user templates
    """
    return send_email(
        photographer_email,
        'client_feedback_received',
        {
            'photographer_name': photographer_name or 'there',
            'client_name': client_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'rating': rating,
            'feedback': feedback
        },
        user_id=user_id
    )


def send_payment_received_email(client_email, client_name, photographer_name, gallery_name, amount, payment_date, message=''):
    """Send payment confirmation to client"""
    return send_email(
        client_email,
        'payment_received',
        {
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'amount': amount,
            'payment_date': payment_date,
            'message': message or 'Your payment has been received. Thank you for your business!'
        }
    )


def send_refund_request_confirmation_email(user_email, user_name, refund_id):
    """Send confirmation to user when refund request is submitted"""
    return send_email(
        user_email,
        'refund_request_confirmation',
        {
            'user_name': user_name or 'there',
            'refund_id': refund_id,
            'support_email': 'support@galerly.com'
        }
    )


def send_admin_refund_request_notification(refund_id, user_email, user_name, plan, reason, eligibility_details):
    """Send notification to admin when a refund is requested"""
    # Use SMTP_USER (support@galerly.com) as admin email
    admin_email = get_required_env('SMTP_USER')
    
    # Format eligibility details
    details_str = '\n'.join([f"{k}: {v}" for k, v in eligibility_details.items()])
    
    return send_email(
        admin_email,
        'admin_refund_notification',
        {
            'refund_id': refund_id,
            'user_email': user_email,
            'user_name': user_name or 'Unknown',
            'plan': plan,
            'reason': reason,
            'details': details_str,
            'admin_url': f"{get_required_env('FRONTEND_URL')}/admin/refunds/{refund_id}"
        }
    )


def send_refund_status_update_email(user_email, user_name, refund_id, status, admin_notes=''):
    """Send notification to user when refund status changes"""
    return send_email(
        user_email,
        'refund_status_update',
        {
            'user_name': user_name or 'there',
            'refund_id': refund_id,
            'status': status,
            'admin_notes': admin_notes or 'No additional notes.',
            'support_email': 'support@galerly.com'
        }
    )


def send_gallery_expiration_notice(photographer_email, gallery_name, gallery_id):
    """Send notification to photographer when their gallery has expired and been archived"""
    frontend_url = get_required_env('FRONTEND_URL')
    support_email = get_required_env('SMTP_USER')  # Support email
    return send_email(
        photographer_email,
        'gallery_expired',
        {
            'gallery_name': gallery_name,
            'gallery_id': gallery_id,
            'gallery_url': f"{frontend_url}/gallery?id={gallery_id}",
            'support_email': support_email,
            'frontend_url': frontend_url
        }
    )


def send_gallery_deletion_notice(photographer_email, gallery_name, archived_days):
    """Send notification to photographer when their archived gallery is permanently deleted"""
    support_email = get_required_env('SMTP_USER')  # Support email
    return send_email(
        photographer_email,
        'gallery_deleted',
        {
            'gallery_name': gallery_name,
            'archived_days': archived_days,
            'support_email': support_email
        }
    )


