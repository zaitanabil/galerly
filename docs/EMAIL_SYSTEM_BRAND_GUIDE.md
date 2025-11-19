# Galerly Email System - Brand Style Guide

## 📧 Overview

All Galerly email templates are fully branded to match the exact design system of the platform. Every email uses the same fonts, colors, button styles, and design language as the website.

## 🎨 Brand Design Elements

### Typography

- **Headings (Titles)**: SF Pro Display, 28px, weight 600, letter-spacing -0.5px
- **Body Text**: SF Pro Text, 16px, weight 400, line-height 1.6
- **Verification Codes**: SF Mono, 36px, weight 700, letter-spacing 8px
- **Footer Text**: SF Pro Text, 13px, weight 400

### Color Palette

```css
Primary Blue:    #0071E3  (buttons, links, codes)
Shark (Dark):    #1D1D1F  (headings, primary text)
Gray (Medium):   #86868B  (secondary text)
Light Gray:      #F5F5F7  (backgrounds, boxes)
Border Gray:     #E5E5EA  (dividers, borders)
Alert Orange:    #FF6B35  (urgent actions)
```

### Design Components

#### Buttons
- **Primary Button**: Blue (#0071E3), fully rounded (border-radius: 980px), padding: 14px 32px
- **Alert Button**: Orange (#FF6B35), same style for urgent actions
- All buttons use SF Pro Text, 16px, weight 500

#### Content Boxes
- **Info Box**: #F5F5F7 background, 16px border-radius, 24px padding
- **Code Box**: #F5F5F7 background, 2px solid #E5E5EA border, 16px border-radius
- **Alert Box**: Gradient orange background (#FFF4E6 → #FFE8CC), 2px solid #FF6B35

#### Layout
- **Max Width**: 600px
- **Body Padding**: 40px horizontal, 32px vertical
- **Header Padding**: 48px top, 32px horizontal and bottom
- **Divider**: 1px solid #E5E5EA

## 📨 Email Templates

### 1. **Verification Code**
- **Purpose**: Email verification during signup
- **Key Elements**: Large verification code in SF Mono, blue color
- **Expiry Note**: "This code will expire in 10 minutes"

### 2. **Welcome Email**
- **Purpose**: Onboarding new users
- **CTA**: "Go to Dashboard" (blue button)
- **Personalization**: Uses user's name

### 3. **Gallery Shared**
- **Purpose**: Notify client when photographer shares gallery
- **Key Info**: Photographer name, gallery name, description
- **CTA**: "View Gallery" (blue button)

### 4. **Password Reset**
- **Purpose**: Security - password reset request
- **CTA**: "Reset Password" (blue button)
- **Security Note**: "Link expires in 1 hour"

### 5. **New Photos Added**
- **Purpose**: Alert client when new photos uploaded
- **Key Info**: Photo count, gallery name
- **CTA**: "View Gallery" (blue button)

### 6. **Gallery Ready**
- **Purpose**: Notify client when gallery is complete
- **Custom Message**: Photographer can add personal message
- **CTA**: "View Your Photos" (blue button)

### 7. **Selection Reminder**
- **Purpose**: Remind client to select favorite photos
- **Tone**: Friendly reminder
- **CTA**: "Select Photos" (blue button)

### 8. **Custom Message**
- **Purpose**: Flexible template for photographer messages
- **Features**: Custom title, message, optional button
- **CTA**: Configurable button text and URL

### 9. **Gallery Expiring Soon**
- **Purpose**: URGENT - Gallery about to expire
- **Style**: Alert box with warning emoji (⚠️)
- **CTA**: "Download Photos" (orange button)
- **Key Info**: Days remaining

### 10. **Client Selected Photos**
- **Purpose**: Notify photographer of client selections
- **Key Info**: Selection count, client name
- **CTA**: "View Selections" (blue button)

### 11. **Client Feedback Received**
- **Purpose**: Notify photographer of client feedback
- **Key Info**: Rating (stars), comment text in info box
- **CTA**: "View Gallery" (blue button)

### 12. **Payment Received**
- **Purpose**: Payment confirmation receipt
- **Key Info**: Amount, gallery name, date in info box
- **Style**: Professional receipt format

## 🏗️ Technical Architecture

### File Structure

```
backend/utils/
├── email.py                      # Main email handler (SMTP configuration)
├── email_templates_branded.py    # All 12 branded templates
└── email.py.backup              # Backup of old templates
```

### How It Works

1. **email_templates_branded.py** contains:
   - Complete CSS styles (GALERLY_EMAIL_STYLES)
   - Reusable header component (get_email_header)
   - Reusable footer component (get_email_footer)
   - All 12 email templates (BRANDED_EMAIL_TEMPLATES)

2. **email.py** imports and uses these templates:
   ```python
   from .email_templates_branded import BRANDED_EMAIL_TEMPLATES
   EMAIL_TEMPLATES = BRANDED_EMAIL_TEMPLATES
   ```

3. **Send email using**:
   ```python
   from backend.utils.email import send_welcome_email, send_gallery_shared_email, etc.
   ```

### Helper Functions

Each email type has a dedicated helper function:
- `send_verification_code_email(email, code)`
- `send_welcome_email(email, name)`
- `send_gallery_shared_email(client_email, client_name, photographer_name, gallery_name, url, description)`
- `send_password_reset_email(email, name, reset_token)`
- `send_new_photos_added_email(client_email, client_name, photographer_name, gallery_name, url, photo_count)`
- `send_gallery_ready_email(client_email, client_name, photographer_name, gallery_name, url, message)`
- `send_selection_reminder_email(client_email, client_name, photographer_name, gallery_name, url, message)`
- `send_custom_email(client_email, client_name, photographer_name, subject, title, message, button_text, button_url)`
- `send_gallery_expiring_email(client_email, client_name, photographer_name, gallery_name, url, days_remaining)`
- `send_client_selected_photos_email(photographer_email, photographer_name, client_name, gallery_name, url, selection_count)`
- `send_client_feedback_email(photographer_email, photographer_name, client_name, gallery_name, url, rating, feedback)`
- `send_payment_received_email(client_email, client_name, photographer_name, gallery_name, amount, payment_date, message)`

## 📱 Responsive Design

All emails are mobile-optimized with media queries:

```css
@media only screen and (max-width: 600px) {
  - Reduced padding (32px → 24px)
  - Smaller titles (28px → 24px)
  - Smaller body text (16px → 15px)
  - Full-width buttons
  - Smaller code text (36px → 28px)
  - Adjusted letter-spacing (8px → 6px)
}
```

## ✅ Best Practices

### Do's ✅
- Always use proper personalization (names, specific details)
- Include clear call-to-action buttons
- Keep messages concise and scannable
- Use consistent brand voice (professional, friendly)
- Test emails in multiple clients (Gmail, Outlook, Apple Mail)

### Don'ts ❌
- Don't use generic greetings ("Dear User")
- Don't overload with too much information
- Don't use ALL CAPS (except for emphasis)
- Don't forget fallback fonts for email clients
- Don't use images for critical information

## 🧪 Testing

To test email templates locally:

```python
from backend.utils.email import send_verification_code_email

# Test verification email
send_verification_code_email('test@example.com', '123456')
```

**Note**: Requires SMTP credentials to be configured in environment variables:
- `SMTP_HOST` (default: mail.privateemail.com)
- `SMTP_PORT` (default: 587)
- `SMTP_USER` (default: noreply@galerly.com)
- `SMTP_PASSWORD` (required)

## 🔄 Adding New Templates

To add a new email template:

1. Open `backend/utils/email_templates_branded.py`
2. Add new template to `BRANDED_EMAIL_TEMPLATES` dictionary:

```python
'your_template_name': {
    'subject': 'Your Subject - Galerly',
    'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Your Title</h1>
<p class="email-text">Your content with <strong>{variable}</strong></p>
<a href="{url}" class="email-button">Your CTA</a>
</div>''' + get_email_footer() + '''</div></body></html>''',
    'text': 'Plain text version: {variable}'
}
```

3. Create helper function in `backend/utils/email.py`:

```python
def send_your_template_email(to_email, variable, url):
    return send_email(
        to_email,
        'your_template_name',
        {
            'variable': variable,
            'url': url
        }
    )
```

## 📊 Email Metrics

Track these KPIs for email effectiveness:
- Open Rate (target: >40%)
- Click-Through Rate (target: >20%)
- Conversion Rate (varies by type)
- Bounce Rate (target: <2%)
- Unsubscribe Rate (target: <0.5%)

## 🎯 Future Enhancements

Potential improvements:
- [ ] Dark mode support (@media (prefers-color-scheme: dark))
- [ ] A/B testing framework
- [ ] Email preview API endpoint
- [ ] Inline image support
- [ ] Multi-language support
- [ ] Email scheduling
- [ ] Analytics tracking pixels
- [ ] Unsubscribe management

---

**Last Updated**: November 2025  
**Maintained by**: Galerly Engineering Team

