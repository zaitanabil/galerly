"""
Email Template Handler - Pro Feature Only
Allows Pro users to customize email templates sent to clients
"""
import json
import boto3
from datetime import datetime, timezone
from utils.response import create_response
from utils.config import dynamodb, users_table, email_templates_table

# Default template types that can be customized
# Note: gallery_shared_with_account and gallery_shared_no_account are used in send_gallery_shared_email()
# based on client account status. The generic 'gallery_shared' is not used.
CUSTOMIZABLE_TEMPLATES = [
    'gallery_shared_with_account',
    'gallery_shared_no_account',
    'new_photos_added',
    'gallery_ready',
    'selection_reminder',
    'custom_message',
    'client_selected_photos',
    'client_feedback_received'
]

# Template variables available for each type
TEMPLATE_VARIABLES = {
    'gallery_shared_with_account': ['client_name', 'photographer_name', 'gallery_name', 'gallery_url', 'description'],
    'gallery_shared_no_account': ['client_name', 'photographer_name', 'gallery_name', 'gallery_url', 'description', 'signup_url'],
    'new_photos_added': ['client_name', 'photographer_name', 'gallery_name', 'gallery_url', 'photo_count'],
    'gallery_ready': ['client_name', 'photographer_name', 'gallery_name', 'gallery_url', 'message'],
    'selection_reminder': ['client_name', 'photographer_name', 'gallery_name', 'gallery_url', 'message'],
    'custom_message': ['client_name', 'photographer_name', 'subject', 'title', 'message', 'button_html'],
    'client_selected_photos': ['photographer_name', 'client_name', 'gallery_name', 'gallery_url', 'selection_count'],
    'client_feedback_received': ['photographer_name', 'client_name', 'gallery_name', 'gallery_url', 'rating', 'feedback']
}


def check_pro_plan(user):
    """Check if user has Pro/Ultimate plan feature"""
    from handlers.subscription_handler import get_user_features
    features, _, _ = get_user_features(user)
    return features.get('email_templates', False)


def handle_list_templates(user):
    """List all email templates for user"""
    try:
        user_id = user['id']
        
        # Check Pro plan
        if not check_pro_plan(user):
            return create_response(403, {
                'error': 'Email template editing is a Pro feature',
                'upgrade_required': True,
                'current_plan': user.get('plan')
            })
        
        # Get user's custom templates
        response = email_templates_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        
        custom_templates = response.get('Items', [])
        
        # Return list of available templates with customization status
        templates_list = []
        for template_type in CUSTOMIZABLE_TEMPLATES:
            custom = next((t for t in custom_templates if t['template_type'] == template_type), None)
            templates_list.append({
                'type': template_type,
                'customized': custom is not None,
                'variables': TEMPLATE_VARIABLES.get(template_type, []),
                'last_updated': custom.get('updated_at') if custom else None
            })
        
        return create_response(200, {
            'templates': templates_list,
            'custom_count': len(custom_templates),
            'total_available': len(CUSTOMIZABLE_TEMPLATES)
        })
        
    except Exception as e:
        print(f"Error listing templates: {str(e)}")
        return create_response(500, {'error': 'Failed to list templates'})


def handle_get_template(user, template_type):
    """Get specific template (custom or default)"""
    try:
        user_id = user['id']
        
        # Check Pro plan
        if not check_pro_plan(user):
            return create_response(403, {
                'error': 'Email template editing is a Pro feature',
                'upgrade_required': True
            })
        
        # Check if template type is valid
        if template_type not in CUSTOMIZABLE_TEMPLATES:
            return create_response(400, {'error': 'Invalid template type'})
        
        # Try to get custom template
        response = email_templates_table.get_item(
            Key={
                'user_id': user_id,
                'template_type': template_type
            }
        )
        
        if 'Item' in response:
            return create_response(200, {
                'template': response['Item'],
                'is_custom': True,
                'variables': TEMPLATE_VARIABLES.get(template_type, [])
            })
        
        # Return default template info
        from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES
        default_template = BRANDED_EMAIL_TEMPLATES.get(template_type, {})
        
        return create_response(200, {
            'template': {
                'user_id': user_id,
                'template_type': template_type,
                'subject': default_template.get('subject', ''),
                'html_body': default_template.get('html', ''),
                'text_body': default_template.get('text', ''),
                'is_default': True
            },
            'is_custom': False,
            'variables': TEMPLATE_VARIABLES.get(template_type, [])
        })
        
    except Exception as e:
        print(f"Error getting template: {str(e)}")
        return create_response(500, {'error': 'Failed to get template'})


def handle_save_template(user, template_type, body):
    """Save or update custom email template"""
    try:
        user_id = user['id']
        
        # Check Pro plan
        if not check_pro_plan(user):
            return create_response(403, {
                'error': 'Email template editing is a Pro feature',
                'upgrade_required': True,
                'current_plan': user.get('plan')
            })
        
        # Validate template type
        if template_type not in CUSTOMIZABLE_TEMPLATES:
            return create_response(400, {'error': 'Invalid template type'})
        
        # Validate required fields
        subject = body.get('subject', '').strip()
        html_body = body.get('html_body', '').strip()
        text_body = body.get('text_body', '').strip()
        
        if not subject:
            return create_response(400, {'error': 'Subject is required'})
        
        if not html_body and not text_body:
            return create_response(400, {'error': 'At least one of html_body or text_body is required'})
        
        # Validate template variables
        required_vars = TEMPLATE_VARIABLES.get(template_type, [])
        for var in required_vars:
            placeholder = '{' + var + '}'
            if placeholder not in subject and placeholder not in html_body and placeholder not in text_body:
                print(f"Warning: Template missing variable {var}")
        
        # Save template
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        template_item = {
            'user_id': user_id,
            'template_type': template_type,
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body,
            'updated_at': now,
            'created_at': now
        }
        
        # Check if updating existing template
        existing = email_templates_table.get_item(
            Key={'user_id': user_id, 'template_type': template_type}
        )
        
        if 'Item' in existing:
            template_item['created_at'] = existing['Item'].get('created_at', now)
        
        email_templates_table.put_item(Item=template_item)
        
        return create_response(200, {
            'message': 'Template saved successfully',
            'template': template_item
        })
        
    except Exception as e:
        print(f"Error saving template: {str(e)}")
        return create_response(500, {'error': 'Failed to save template'})


def handle_delete_template(user, template_type):
    """Delete custom template (revert to default)"""
    try:
        user_id = user['id']
        
        # Check Pro plan
        if not check_pro_plan(user):
            return create_response(403, {
                'error': 'Email template editing is a Pro feature',
                'upgrade_required': True
            })
        
        # Validate template type
        if template_type not in CUSTOMIZABLE_TEMPLATES:
            return create_response(400, {'error': 'Invalid template type'})
        
        # Delete custom template
        email_templates_table.delete_item(
            Key={
                'user_id': user_id,
                'template_type': template_type
            }
        )
        
        return create_response(200, {
            'message': 'Custom template deleted, reverted to default'
        })
        
    except Exception as e:
        print(f"Error deleting template: {str(e)}")
        return create_response(500, {'error': 'Failed to delete template'})


def handle_preview_template(user, template_type, body):
    """Preview template with sample data"""
    try:
        # Check Pro plan
        if not check_pro_plan(user):
            return create_response(403, {
                'error': 'Email template editing is a Pro feature',
                'upgrade_required': True
            })
        
        # Validate template type
        if template_type not in CUSTOMIZABLE_TEMPLATES:
            return create_response(400, {'error': 'Invalid template type'})
        
        subject = body.get('subject', '')
        html_body = body.get('html_body', '')
        text_body = body.get('text_body', '')
        
        # Sample data for preview
        sample_data = {
            'client_name': 'John Smith',
            'photographer_name': user.get('name', 'Photographer'),
            'gallery_name': 'Sample Wedding Gallery',
            'gallery_url': 'https://galerly.com/gallery/sample123',
            'description': 'Your beautiful wedding photos are ready!',
            'photo_count': '150',
            'message': 'Please review and select your favorite photos.',
            'days_remaining': '7',
            'selection_count': '25',
            'rating': '5',
            'feedback': 'Amazing work! We love the photos.',
            'subject': 'Sample Subject',
            'title': 'Sample Title',
            'button_html': '<a href="#" class="email-button">View Gallery</a>',
            'signup_url': 'https://galerly.com/auth'
        }
        
        # Apply sample data
        try:
            preview_subject = subject.format(**sample_data)
            preview_html = html_body.format(**sample_data)
            preview_text = text_body.format(**sample_data)
        except KeyError as e:
            return create_response(400, {
                'error': f'Invalid template variable: {str(e)}'
            })
        
        return create_response(200, {
            'preview': {
                'subject': preview_subject,
                'html': preview_html,
                'text': preview_text
            },
            'sample_data': sample_data
        })
        
    except Exception as e:
        print(f"Error previewing template: {str(e)}")
        return create_response(500, {'error': 'Failed to preview template'})


def get_user_template(user_id, template_type):
    """
    Get user's custom template or default template
    Used by email sending functions
    """
    try:
        # Try to get custom template
        response = email_templates_table.get_item(
            Key={
                'user_id': user_id,
                'template_type': template_type
            }
        )
        
        if 'Item' in response:
            item = response['Item']
            return {
                'subject': item['subject'],
                'html': item['html_body'],
                'text': item['text_body']
            }
        
        # Return default template
        from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES
        return BRANDED_EMAIL_TEMPLATES.get(template_type, {})
        
    except Exception as e:
        print(f"Error getting user template: {str(e)}")
        # Fallback to default
        from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES
        return BRANDED_EMAIL_TEMPLATES.get(template_type, {})

