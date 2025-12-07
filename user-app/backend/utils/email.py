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


def send_email(to_email=None, template_name=None, template_vars=None, user_id=None, to_addresses=None, subject=None, body_html=None, body_text=None):
    """
    Send email using SMTP (Namecheap Private Email)
    
    Supports two modes:
    1. Template Mode: provide template_name and template_vars
    2. Raw Mode: provide subject, body_html, and body_text
    
    Args:
        to_email: Single recipient email address (string)
        template_name: Template type to use (string)
        template_vars: Variables to substitute in template (dict)
        user_id: If provided, uses custom Pro user templates
        to_addresses: List of recipient emails (legacy/AWS compatibility)
        subject: Direct subject line (Raw Mode)
        body_html: Direct HTML body (Raw Mode)
        body_text: Direct text body (Raw Mode)
    """
    if template_vars is None:
        template_vars = {}
    
    # Resolve recipient
    recipient = to_email
    if not recipient and to_addresses and isinstance(to_addresses, list) and len(to_addresses) > 0:
        recipient = to_addresses[0]
        
    if not recipient:
        print("Error: No recipient email provided")
        return False

    # Mode 1: Template Mode
    if template_name:
    # Get template (custom if user_id provided and they're Pro)
        template = None
        if user_id:
            from handlers.email_template_handler import get_user_template
            try:
                template = get_user_template(user_id, template_name)
                if not template:
                    print(f" Custom template '{template_name}' not found for user {user_id}, using default")
            except Exception as e:
                print(f"Error loading custom template '{template_name}' for user {user_id}: {str(e)}")
        
        # Fallback to default if no custom template found or requested
        if not template:
            if template_name not in EMAIL_TEMPLATES:
                print(f"Email template '{template_name}' not found")
                return False
            template = EMAIL_TEMPLATES[template_name]
        
        # Validate template structure
        required_keys = ['subject', 'html', 'text']
        missing_keys = [key for key in required_keys if key not in template]
        if missing_keys:
            print(f" Email template '{template_name}' missing required keys: {missing_keys}")
            return False
        
        # Format template with variables
        try:
            subject = template['subject'].format(**template_vars)
            html_body = template['html'].format(**template_vars)
            text_body = template['text'].format(**template_vars)
        except KeyError as e:
            print(f"Template variable error: Missing variable {e} in template '{template_name}'")
            print(f"   Available variables: {list(template_vars.keys())}")
            return False
        except Exception as e:
            print(f"Error formatting template '{template_name}': {str(e)}")
            return False

    # Mode 2: Raw Mode (Direct inputs)
    elif subject and (body_html or body_text):
        # Use provided values
        if not body_text and body_html:
            # Simple strip tags for fallback text
            import re
            body_text = re.sub('<[^<]+?>', '', body_html)
        if not body_html and body_text:
            body_html = f"<p>{body_text}</p>"
    else:
        print("Error: Must provide either template_name OR (subject and body)")
        return False
    
    # Check if SMTP password is configured
    if not SMTP_PASSWORD:
        print(f"SMTP_PASSWORD not configured. Cannot send email.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = recipient
        
        # Attach both text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Connect to SMTP server and send
        print(f"🔌 Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            print(f"Starting TLS...")
            server.starttls()  # Upgrade to encrypted connection
            print(f"Authenticating as {SMTP_USER}...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print(f"📤 Sending message to {recipient}...")
            server.send_message(msg)
        
        print(f"Email sent to {recipient} via SMTP")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication failed: {str(e)}")
        print(f"   SMTP_USER used: {SMTP_USER}")
        print(f"   Check SMTP_USER and SMTP_PASSWORD in environment variables")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error sending email to {recipient}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_welcome_email(user_email, user_name):
    """Send welcome email to new user"""
    return send_email(
        to_email=user_email,
        template_name='welcome',
        template_vars={
            'name': user_name or 'there',
            'dashboard_url': get_required_env('FRONTEND_URL') + '/dashboard'
        }
    )


def send_gallery_shared_email(client_email, client_name, photographer_name, gallery_name, gallery_url, description='', user_id=None):
    """
    Send notification when gallery is shared with client
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
        to_email=client_email,
        template_name=template_name,
        template_vars={
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
        to_email=user_email,
        template_name='password_reset',
        template_vars={
            'name': user_name or 'there',
            'reset_url': reset_url
        }
    )


def send_new_photos_added_email(client_email, client_name, photographer_name, gallery_name, gallery_url, photo_count, user_id=None):
    """
    Send notification when new photos are added to gallery
    """
    return send_email(
        to_email=client_email,
        template_name='new_photos_added',
        template_vars={
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
        to_email=user_email,
        template_name='verification_code',
        template_vars={
            'code': code
        }
    )


def send_gallery_ready_email(client_email, client_name, photographer_name, gallery_name, gallery_url, message='', user_id=None):
    """
    Send notification when gallery is ready for viewing
    """
    return send_email(
        to_email=client_email,
        template_name='gallery_ready',
        template_vars={
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
    """
    return send_email(
        to_email=client_email,
        template_name='selection_reminder',
        template_vars={
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'message': message or 'Please take a moment to select your favorite photos from the gallery.'
        },
        user_id=user_id
    )


def send_download_reminder_email(client_email, client_name, gallery_name, gallery_url, photographer_name='', user_id=None):
    """
    Send reminder to client to download their photos
    """
    return send_email(
        to_email=client_email,
        template_name='download_reminder',
        template_vars={
            'client_name': client_name or 'there',
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'photographer_name': photographer_name,
            'message': 'Your photos are ready to download! Don\'t forget to save your favorites.'
        },
        user_id=user_id
    )


def send_custom_email(client_email, client_name, photographer_name, subject, title, message, button_text='', button_url='', user_id=None):
    """
    Send custom message from photographer to client
    """
    button_html = ''
    if button_text and button_url:
        button_html = f'<a href="{button_url}" class="email-button">{button_text}</a>'
    
    return send_email(
        to_email=client_email,
        template_name='custom_message',
        template_vars={
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
    Send notification when gallery is about to expire
    """
    return send_email(
        to_email=client_email,
        template_name='gallery_expiring_soon',
        template_vars={
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'days_remaining': days_remaining
        },
        user_id=user_id
    )


def send_gallery_expiration_reminder_email(photographer_email, photographer_name, gallery_name, gallery_url, expiration_date):
    """Send expiration reminder to photographer"""
    return send_email(
        to_email=photographer_email,
        template_name='gallery_expiration_reminder',
        template_vars={
            'photographer_name': photographer_name or 'there',
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'expiration_date': expiration_date
        }
    )


def send_client_selected_photos_email(photographer_email, photographer_name, client_name, gallery_name, gallery_url, selection_count, user_id=None):
    """
    Notify photographer when client selects photos
    """
    return send_email(
        to_email=photographer_email,
        template_name='client_selected_photos',
        template_vars={
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
    """
    return send_email(
        to_email=photographer_email,
        template_name='client_feedback_received',
        template_vars={
            'photographer_name': photographer_name or 'there',
            'client_name': client_name,
            'gallery_name': gallery_name,
            'gallery_url': gallery_url,
            'rating': rating,
            'feedback': feedback
        },
        user_id=user_id
    )


def send_payment_received_email(client_email, client_name, photographer_name, gallery_name, amount, payment_date, message='', user_id=None):
    """Send payment confirmation to client"""
    return send_email(
        to_email=client_email,
        template_name='payment_received',
        template_vars={
            'client_name': client_name or 'there',
            'photographer_name': photographer_name,
            'gallery_name': gallery_name,
            'amount': amount,
            'payment_date': payment_date,
            'message': message or 'Your payment has been received. Thank you for your business!'
        },
        user_id=user_id
    )


def send_refund_request_confirmation_email(user_email, user_name, refund_id):
    """Send confirmation to user when refund request is submitted"""
    return send_email(
        to_email=user_email,
        template_name='refund_request_confirmation',
        template_vars={
            'user_name': user_name or 'there',
            'refund_id': refund_id,
            'support_email': os.environ.get('SUPPORT_EMAIL')
        }
    )


def send_admin_refund_request_notification(refund_id, user_email, user_name, plan, reason, eligibility_details):
    """Send notification to admin when a refund is requested"""
    admin_email = get_required_env('SMTP_USER')
    
    # Format eligibility details
    details_str = '\n'.join([f"{k}: {v}" for k, v in eligibility_details.items()])
    
    return send_email(
        to_email=admin_email,
        template_name='admin_refund_notification',
        template_vars={
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
        to_email=user_email,
        template_name='refund_status_update',
        template_vars={
            'user_name': user_name or 'there',
            'refund_id': refund_id,
            'status': status,
            'admin_notes': admin_notes or 'No additional notes.',
            'support_email': os.environ.get('SUPPORT_EMAIL')
        }
    )


def send_gallery_expiration_notice(photographer_email, gallery_name, gallery_id):
    """Send notification to photographer when their gallery has expired and been archived"""
    frontend_url = get_required_env('FRONTEND_URL')
    support_email = get_required_env('SMTP_USER')
    return send_email(
        to_email=photographer_email,
        template_name='gallery_expired',
        template_vars={
            'gallery_name': gallery_name,
            'gallery_id': gallery_id,
            'gallery_url': f"{frontend_url}/gallery?id={gallery_id}",
            'support_email': support_email,
            'frontend_url': frontend_url
        }
    )


def send_gallery_deletion_notice(photographer_email, gallery_name, archived_days):
    """Send notification to photographer when their archived gallery is permanently deleted"""
    support_email = get_required_env('SMTP_USER')
    return send_email(
        to_email=photographer_email,
        template_name='gallery_deleted',
        template_vars={
            'gallery_name': gallery_name,
            'archived_days': archived_days,
            'support_email': support_email
        }
    )


def send_subscription_upgraded_email(user_email, user_name, plan_name, features):
    """Send subscription upgrade confirmation to user"""
    dashboard_url = get_required_env('FRONTEND_URL') + '/dashboard'
    features_html = "<ul>" + "".join([f"<li>{f}</li>" for f in features]) + "</ul>"
    
    return send_email(
        to_email=user_email,
        subject=f"Welcome to Galerly {plan_name}!",
        body_html=f"""
        <h2>Welcome to {plan_name}!</h2>
        <p>Hi {user_name or 'there'},</p>
        <p>Your account has been successfully upgraded to the <strong>{plan_name}</strong> plan.</p>
        <p>You now have access to:</p>
        {features_html}
        <p><a href="{dashboard_url}" class="email-button">Go to Dashboard</a></p>
        """,
        body_text=f"Welcome to {plan_name}! Your account has been upgraded. Visit your dashboard to see new features: {dashboard_url}"
    )


def send_subscription_downgraded_email(user_email, user_name, plan_name, effective_date):
    """Send subscription downgrade confirmation to user"""
    dashboard_url = get_required_env('FRONTEND_URL') + '/billing'
    
    return send_email(
        to_email=user_email,
        subject="Subscription Change Scheduled",
        body_html=f"""
        <h2>Subscription Update</h2>
        <p>Hi {user_name or 'there'},</p>
        <p>Your subscription change has been scheduled.</p>
        <p>Your account will be moved to the <strong>{plan_name}</strong> plan on <strong>{effective_date}</strong>.</p>
        <p>You will retain access to your current plan features until then.</p>
        <p><a href="{dashboard_url}">Manage Subscription</a></p>
        """,
        body_text=f"Subscription Update: Your account will be moved to the {plan_name} plan on {effective_date}. You retain current access until then."
    )


def send_payment_receipt_email(user_email, user_name, amount, currency, plan_name):
    """Send payment receipt to user (Galerly Subscription)"""
    billing_url = get_required_env('FRONTEND_URL') + '/billing'
    
    return send_email(
        to_email=user_email,
        subject="Payment Receipt",
        body_html=f"""
        <h2>Payment Received</h2>
        <p>Hi {user_name or 'there'},</p>
        <p>We received your payment of <strong>{amount} {currency.upper()}</strong> for the <strong>{plan_name}</strong> plan.</p>
        <p>Thank you for choosing Galerly!</p>
        <p><a href="{billing_url}">View Billing History</a></p>
        """,
        body_text=f"Payment Received: We received your payment of {amount} {currency.upper()} for the {plan_name} plan. Thank you!"
    )
