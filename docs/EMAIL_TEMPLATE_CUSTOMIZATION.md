# Email Template Editing - Pro Feature

## Overview

Email template editing is a **Pro-only feature** that allows photographers to customize the email templates sent to their clients. This feature provides complete control over branding and messaging while maintaining all dynamic content.

## Features

### ✅ Customizable Templates

10 client-facing email templates can be customized:
- `gallery_shared` - When a gallery is shared
- `gallery_shared_with_account` - Gallery shared with registered clients
- `gallery_shared_no_account` - Gallery shared with unregistered clients
- `new_photos_added` - New photos added notification
- `gallery_ready` - Gallery ready for viewing
- `selection_reminder` - Photo selection reminder
- `custom_message` - Custom photographer message
- `gallery_expiring_soon` - Gallery expiration warning
- `client_selected_photos` - Client photo selection notification
- `client_feedback_received` - Client feedback notification

### ✅ Template Components

Each template has three customizable parts:
1. **Subject Line** - Email subject with dynamic variables
2. **HTML Body** - Formatted email content (full HTML)
3. **Text Body** - Plain text fallback

### ✅ Template Variables

Dynamic variables available for each template:

| Template | Variables |
|----------|-----------|
| `gallery_shared` | `{client_name}`, `{photographer_name}`, `{gallery_name}`, `{gallery_url}`, `{description}` |
| `new_photos_added` | `{client_name}`, `{photographer_name}`, `{gallery_name}`, `{gallery_url}`, `{photo_count}` |
| `gallery_ready` | `{client_name}`, `{photographer_name}`, `{gallery_name}`, `{gallery_url}`, `{message}` |
| `selection_reminder` | `{client_name}`, `{photographer_name}`, `{gallery_name}`, `{gallery_url}`, `{message}` |
| `gallery_expiring_soon` | `{client_name}`, `{photographer_name}`, `{gallery_name}`, `{gallery_url}`, `{days_remaining}` |

## Pro Plan Enforcement

### Backend Protection

All email template endpoints require Pro plan:

```python
def check_pro_plan(user):
    """Check if user has Pro plan"""
    user_plan = user.get('plan', 'free').lower()
    return user_plan in ['pro', 'professional']
```

Non-Pro users receive `403 Forbidden` with upgrade prompt:

```json
{
  "error": "Email template editing is a Pro feature",
  "upgrade_required": true,
  "current_plan": "plus"
}
```

### Frontend Protection

The UI automatically detects plan level and shows upgrade banner for non-Pro users.

## API Endpoints

### List Templates
```http
GET /v1/email-templates
Authorization: Bearer {token}
```

**Response:**
```json
{
  "templates": [
    {
      "type": "gallery_shared",
      "customized": true,
      "variables": ["client_name", "photographer_name", "gallery_name", "gallery_url", "description"],
      "last_updated": "2024-11-24T10:30:00Z"
    }
  ],
  "custom_count": 3,
  "total_available": 10
}
```

### Get Template
```http
GET /v1/email-templates/{template_type}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "template": {
    "user_id": "user_123",
    "template_type": "gallery_shared",
    "subject": "New Gallery: {gallery_name}",
    "html_body": "<html>...</html>",
    "text_body": "Plain text...",
    "updated_at": "2024-11-24T10:30:00Z"
  },
  "is_custom": true,
  "variables": ["client_name", "photographer_name", "gallery_name", "gallery_url"]
}
```

### Save Template
```http
PUT /v1/email-templates/{template_type}
Authorization: Bearer {token}
Content-Type: application/json

{
  "subject": "New Gallery: {gallery_name}",
  "html_body": "<html><body>Hi {client_name}...</body></html>",
  "text_body": "Hi {client_name}..."
}
```

### Delete Template (Reset to Default)
```http
DELETE /v1/email-templates/{template_type}
Authorization: Bearer {token}
```

### Preview Template
```http
POST /v1/email-templates/{template_type}/preview
Authorization: Bearer {token}
Content-Type: application/json

{
  "subject": "Test Subject",
  "html_body": "<html>...</html>",
  "text_body": "..."
}
```

**Response:**
```json
{
  "preview": {
    "subject": "New Gallery: Sample Wedding Gallery",
    "html": "<html>...with sample data...</html>",
    "text": "Plain text with sample data"
  },
  "sample_data": {
    "client_name": "John Smith",
    "photographer_name": "Photographer Name",
    "gallery_name": "Sample Wedding Gallery",
    "gallery_url": "https://galerly.com/gallery/sample123"
  }
}
```

## Database Schema

### DynamoDB Table: `email_templates`

**Partition Key:** `user_id` (String)  
**Sort Key:** `template_type` (String)

**Attributes:**
- `user_id` - Photographer's user ID
- `template_type` - Template identifier
- `subject` - Email subject line
- `html_body` - HTML email content
- `text_body` - Plain text content
- `created_at` - ISO 8601 timestamp
- `updated_at` - ISO 8601 timestamp

## Email Sending Integration

### Custom Template Usage

When sending emails, pass `user_id` to use custom templates:

```python
from utils.email import send_gallery_shared_email

send_gallery_shared_email(
    client_email='client@example.com',
    client_name='John Smith',
    photographer_name='Jane Photographer',
    gallery_name='Wedding Photos',
    gallery_url='https://galerly.com/gallery/123',
    description='Your beautiful wedding photos',
    user_id='user_123'  # Enables custom templates for Pro users
)
```

### Template Resolution Logic

1. If `user_id` provided:
   - Query `email_templates` table for custom template
   - If found, use custom template
   - If not found, fall back to default
2. If no `user_id`, use default template

```python
def get_user_template(user_id, template_type):
    """Get user's custom template or default"""
    try:
        response = email_templates_table.get_item(
            Key={'user_id': user_id, 'template_type': template_type}
        )
        
        if 'Item' in response:
            # Custom template exists
            return {
                'subject': response['Item']['subject'],
                'html': response['Item']['html_body'],
                'text': response['Item']['text_body']
            }
        
        # Fall back to default
        from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES
        return BRANDED_EMAIL_TEMPLATES.get(template_type, {})
        
    except Exception as e:
        # Always fall back to default on error
        from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES
        return BRANDED_EMAIL_TEMPLATES.get(template_type, {})
```

## Frontend Usage

### Access Email Templates Page

```
https://galerly.com/email-templates.html
```

### User Interface

1. **Template Grid** - Shows all customizable templates
2. **Status Indicators** - "Using Default" or "✓ Customized"
3. **Edit Modal** - Full WYSIWYG editor with:
   - Subject line editor
   - HTML body editor
   - Plain text editor
   - Variable hints
   - Preview function
   - Save/Reset buttons

### Key Features

- **Real-time Preview** - Test templates with sample data
- **Variable Hints** - Shows available variables for each template
- **Reset to Default** - One-click revert to default template
- **Auto-save Indicator** - Shows last saved timestamp

## Testing

### Test Suite: `test_email_template_handler.py`

**Coverage:**
- ✅ List templates (Pro vs Free)
- ✅ Get template (custom vs default)
- ✅ Save template (validation)
- ✅ Delete template (revert to default)
- ✅ Preview template (with sample data)
- ✅ Pro plan enforcement
- ✅ Invalid template types
- ✅ Missing required fields
- ✅ Template variable validation

**Run Tests:**
```bash
cd backend
pytest tests/test_email_template_handler.py -v
```

## Security & Validation

### Input Validation

1. **Template Type** - Must be in `CUSTOMIZABLE_TEMPLATES` list
2. **Subject** - Required, non-empty string
3. **Body** - At least one of `html_body` or `text_body` required
4. **Variables** - Warns if required variables missing

### Access Control

- **Authentication** - Requires valid JWT token
- **Plan Check** - Enforces Pro plan on every request
- **User Isolation** - Users can only access their own templates

### SQL Injection Protection

No risk - DynamoDB uses parameterized queries via Boto3.

### XSS Protection

Frontend displays HTML in sandboxed iframe during preview.

## Best Practices

### Template Design

1. **Keep Variables** - Always include required variables
2. **Test Preview** - Preview before saving
3. **Plain Text** - Always provide text fallback
4. **Responsive HTML** - Use email-safe HTML/CSS
5. **Brand Consistency** - Match your portfolio branding

### Variable Usage

```html
<!-- Good: All required variables included -->
<h1>Hi {client_name}!</h1>
<p>View your gallery: {gallery_name}</p>
<a href="{gallery_url}">View Photos</a>

<!-- Bad: Missing required variables -->
<h1>Hi there!</h1>
<p>View your photos</p>
```

### HTML Email Tips

- Use inline CSS
- Use tables for layout
- Test in multiple email clients
- Keep width under 600px
- Use web-safe fonts

## Limitations

### Not Customizable

These templates are NOT customizable (system use only):
- `verification_code` - Email verification
- `welcome` - New user welcome
- `password_reset` - Password reset
- `refund_request_confirmation` - Refund confirmation
- `admin_refund_notification` - Admin notifications
- `account_deletion_scheduled` - Account deletion

### Technical Limits

- **Template Size** - Max 100KB per template
- **Variable Count** - Max 20 variables per template
- **Revisions** - No version history (single current version)

## Troubleshooting

### Template Not Applying

**Check:**
1. User has Pro plan
2. Template was saved successfully
3. Email function passes `user_id` parameter
4. Template type matches exactly

### Variables Not Replacing

**Check:**
1. Variable names match exactly (case-sensitive)
2. Variables wrapped in `{braces}`
3. All required variables provided in template
4. Preview shows correct substitution

### Preview Shows Errors

**Common Issues:**
- Missing required variables
- Invalid HTML syntax
- Unclosed tags
- Special characters not escaped

## Future Enhancements

Possible improvements:
- Template versioning/history
- A/B testing support
- Template marketplace
- Visual drag-and-drop editor
- Email analytics (open rates, click rates)
- Template inheritance
- Conditional content blocks

## Summary

Email template editing provides Pro users with complete control over client communications while maintaining system reliability through:

✅ **Pro-only Access** - Enforced at all levels  
✅ **Default Fallbacks** - Never breaks email sending  
✅ **Full Customization** - Subject, HTML, and text  
✅ **Variable System** - Dynamic content injection  
✅ **Preview Function** - Test before sending  
✅ **Comprehensive Tests** - 20+ test cases  
✅ **User-Friendly UI** - Clean, intuitive interface  

The feature adds significant value for Pro users while maintaining system security and reliability.

