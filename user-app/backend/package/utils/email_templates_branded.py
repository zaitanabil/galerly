"""
Updated Galerly Email Templates with Brand Styling
All templates use SF Pro fonts, brand colors, and consistent design
"""

# Galerly Brand Email Styles
GALERLY_EMAIL_STYLES = '''
<style>
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Segoe UI', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: #F5F5F7;
  }}
  
  .email-container {{
    max-width: 600px;
    margin: 0 auto;
    background: #FFFFFF;
  }}
  
  .email-header {{
    background: #F5F5F7;
    padding: 48px 32px 32px;
    text-align: center;
    border-bottom: 1px solid #E5E5EA;
  }}
  
  .email-logo {{
    font-family: 'SF Pro Display', -apple-system, sans-serif;
    font-size: 32px;
    font-weight: 600;
    color: #1D1D1F;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
  }}
  
  .email-tagline {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 400;
    color: #86868B;
    margin: 0;
    letter-spacing: 0.02em;
  }}
  
  .email-body {{
    padding: 48px 32px;
    background: #FFFFFF;
  }}
  
  .email-title {{
    font-family: 'SF Pro Display', -apple-system, sans-serif;
    font-size: 32px;
    font-weight: 300;
    color: #1D1D1F;
    margin: 0 0 24px 0;
    line-height: 1.1;
    letter-spacing: -0.5px;
  }}
  
  .email-text {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 18px;
    font-weight: 400;
    color: #1D1D1F;
    line-height: 1.6;
    margin: 0 0 16px 0;
  }}
  
  .email-text strong {{
    font-weight: 600;
  }}
  
  .email-button {{
    display: inline-block;
    padding: 16px 32px;
    background: #0066CC;
    color: #FFFFFF !important;
    text-decoration: none;
    border-radius: 28px;
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 18px;
    font-weight: 500;
    margin: 32px 0;
    transition: background 0.2s ease;
  }}
  
  .email-button:hover {{
    background: #3A89E6;
  }}
  
  .email-button-success {{
    display: inline-block;
    padding: 16px 32px;
    background: #98FF98;
    color: #1D1D1F !important;
    text-decoration: none;
    border-radius: 28px;
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 18px;
    font-weight: 500;
    margin: 32px 0;
  }}
  
  .email-button-alert {{
    display: inline-block;
    padding: 16px 32px;
    background: #FF6F61;
    color: #FFFFFF !important;
    text-decoration: none;
    border-radius: 28px;
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 18px;
    font-weight: 500;
    margin: 32px 0;
  }}
  
  .email-code-box {{
    background: #F5F5F7;
    border: 1px solid #E5E5EA;
    border-radius: 20px;
    padding: 32px 24px;
    text-align: center;
    margin: 32px 0;
  }}
  
  .email-code {{
    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
    font-size: 42px;
    font-weight: 600;
    color: #0066CC;
    letter-spacing: 12px;
    display: block;
    margin: 0;
  }}
  
  .email-info-box {{
    background: #F5F5F7;
    border-radius: 20px;
    padding: 24px;
    margin: 24px 0;
  }}
  
  .email-info-item {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 16px;
    color: #1D1D1F;
    margin: 0 0 12px 0;
    line-height: 1.6;
  }}
  
  .email-info-item:last-child {{
    margin-bottom: 0;
  }}
  
  .email-info-label {{
    font-weight: 600;
    color: #1D1D1F;
  }}
  
  .email-alert-box {{
    background: #FFF7F4;
    border: 2px solid #FF6F61;
    border-radius: 20px;
    padding: 24px;
    margin: 32px 0;
  }}
  
  .email-alert-text {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 16px;
    font-weight: 500;
    color: #FF6F61;
    margin: 0;
    line-height: 1.6;
  }}
  
  .email-footer {{
    padding: 32px;
    background: #F5F5F7;
    text-align: center;
    border-top: 1px solid #E5E5EA;
  }}
  
  .email-footer-text {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 400;
    color: #86868B;
    line-height: 1.6;
    margin: 0 0 8px 0;
  }}
  
  .email-footer-link {{
    color: #0066CC;
    text-decoration: none;
    font-weight: 500;
  }}
  
  .email-divider {{
    height: 1px;
    background: #E5E5EA;
    margin: 32px 0;
    border: none;
  }}
  
  .email-features-list {{
    margin: 24px 0;
    padding: 0;
    list-style: none;
  }}
  
  .email-features-list li {{
    font-family: 'SF Pro Text', -apple-system, sans-serif;
    font-size: 16px;
    color: #1D1D1F;
    line-height: 1.8;
    padding-left: 28px;
    margin-bottom: 12px;
    position: relative;
  }}
  
  .email-features-list li:before {{
    content: "✓";
    position: absolute;
    left: 0;
    color: #0066CC;
    font-weight: 600;
    font-size: 18px;
  }}
  
  @media only screen and (max-width: 600px) {{
    .email-header {{
      padding: 32px 24px 24px;
    }}
    
    .email-body {{
      padding: 32px 24px;
    }}
    
    .email-title {{
      font-size: 28px;
    }}
    
    .email-text {{
      font-size: 16px;
    }}
    
    .email-button,
    .email-button-alert,
    .email-button-success {{
      display: block;
      text-align: center;
      padding: 14px 24px;
      font-size: 16px;
    }}
    
    .email-code {{
      font-size: 32px;
      letter-spacing: 8px;
    }}
    
    .email-footer {{
      padding: 24px;
    }}
  }}
</style>
'''

# Email Header Component
def get_email_header():
    return '''
    <div class="email-header">
      <div class="email-logo">Galerly</div>
      <div class="email-tagline">Share art, not files</div>
    </div>
    '''

# Email Footer Component  
def get_email_footer():
    return '''
    <div class="email-footer">
      <div class="email-footer-text">
        This email was sent by Galerly<br>
        Professional photo gallery platform for photographers
      </div>
      <div class="email-footer-text" style="margin-top: 16px;">
        <a href="https://galerly.com" class="email-footer-link">galerly.com</a>
      </div>
      <div class="email-footer-text" style="margin-top: 12px;">
        <a href="https://galerly.com/privacy" class="email-footer-link">Privacy Policy</a>
        &nbsp;•&nbsp;
        <a href="https://galerly.com/legal-notice" class="email-footer-link">Legal Notice</a>
      </div>
    </div>
    '''

# All email templates with brand styling
BRANDED_EMAIL_TEMPLATES = {
    'verification_code': {
        'subject': 'Verify Your Email - Galerly',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Verify Your Email</h1>
<p class="email-text">Thank you for signing up for Galerly!</p>
<p class="email-text">To complete your registration, please enter this verification code:</p>
<div class="email-code-box"><span class="email-code">{code}</span></div>
<p class="email-text" style="color: #86868B; font-size: 15px;">This code will expire in 10 minutes.</p>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">If you didn't request this code, you can safely ignore this email.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Your Galerly verification code is: {code}. This code will expire in 10 minutes.'
    },
    
    'welcome': {
        'subject': 'Welcome to Galerly!',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Welcome to Galerly!</h1>
<p class="email-text">Hi <strong>{name}</strong>,</p>
<p class="email-text">Thank you for joining Galerly! We're excited to help you share your photography with the world.</p>
<p class="email-text">Get started by creating your first gallery and sharing it with clients.</p>
<a href="{dashboard_url}" class="email-button">Go to Dashboard</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">If you have any questions, feel free to contact our support team.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Welcome to Galerly! Thank you for joining. Get started by creating your first gallery.'
    },
    
    'gallery_shared': {
        'subject': 'New Gallery Shared: {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">New Gallery Shared</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">{photographer_name} has shared a new gallery with you: <strong>{gallery_name}</strong></p>
<p class="email-text">{description}</p>
<a href="{gallery_url}" class="email-button">View Gallery</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">This gallery was shared by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'A new gallery "{gallery_name}" has been shared with you by {photographer_name}. View it at: {gallery_url}'
    },
    
    'gallery_shared_with_account': {
        'subject': 'New Gallery Shared: {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">New Gallery Shared</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">{photographer_name} has shared a new gallery with you: <strong>{gallery_name}</strong></p>
<p class="email-text">{description}</p>
<a href="{gallery_url}" class="email-button">View Gallery</a>
<hr class="email-divider">
<p class="email-text" style="color: #1D1D1F; font-size: 16px; margin-top: 24px;"><strong>💡 Sign in to interact with your photographer</strong></p>
<p class="email-text" style="font-size: 15px;">You have a Galerly account! Sign in to approve photos, leave comments, and download your favorites.</p>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">This gallery was shared by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'A new gallery "{gallery_name}" has been shared with you by {photographer_name}. Sign in to your Galerly account to approve photos, comment, and download. View at: {gallery_url}'
    },
    
    'gallery_shared_no_account': {
        'subject': 'New Gallery Shared: {gallery_name} - Create Account to Interact',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">New Gallery Shared</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">{photographer_name} has shared a new gallery with you: <strong>{gallery_name}</strong></p>
<p class="email-text">{description}</p>
<a href="{gallery_url}" class="email-button">View Gallery (View Only)</a>
<hr class="email-divider">
<p class="email-text" style="color: #1D1D1F; font-size: 16px; margin-top: 24px;"><strong>🎯 Create an account to unlock full features</strong></p>
<p class="email-text" style="font-size: 15px; margin-bottom: 16px;">Right now, you can view the gallery with the link above. To unlock full interaction:</p>
<ul class="email-features-list">
<li><strong>Approve photos</strong> - Mark your favorites</li>
<li><strong>Leave comments</strong> - Communicate with your photographer</li>
<li><strong>Download photos</strong> - Save your images</li>
<li><strong>Receive updates</strong> - Get notified when new photos are added</li>
</ul>
<a href="{signup_url}" class="email-button-success">Create Free Account</a>
<p class="email-text" style="font-size: 14px; color: #86868B; margin-top: 16px;">Creating an account is free and takes less than a minute.</p>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">This gallery was shared by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'A new gallery "{gallery_name}" has been shared with you by {photographer_name}. You can view it at: {gallery_url}\n\nCreate a free Galerly account to approve photos, leave comments, and download images: {signup_url}\n\nWithout an account, you can only view the gallery.'
    },
    
    'password_reset': {
        'subject': 'Reset Your Galerly Password',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Password Reset Request</h1>
<p class="email-text">Hi <strong>{name}</strong>,</p>
<p class="email-text">We received a request to reset your password. Click the button below to reset it:</p>
<a href="{reset_url}" class="email-button">Reset Password</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
<p class="email-text" style="color: #86868B; font-size: 14px;">This link will expire in 1 hour.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Reset your password by visiting: {reset_url}'
    },
    
    'new_photos_added': {
        'subject': 'New Photos Added to {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">New Photos Added</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">{photographer_name} has added new photos to your gallery: <strong>{gallery_name}</strong></p>
<p class="email-text">{photo_count} new photo(s) have been added. Check them out!</p>
<a href="{gallery_url}" class="email-button">View Gallery</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Gallery by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'New photos have been added to your gallery "{gallery_name}" by {photographer_name}. View them at: {gallery_url}'
    },
    
    'gallery_ready': {
        'subject': 'Your Gallery is Ready - {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Your Gallery is Ready!</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">{photographer_name} has finished uploading your photos to: <strong>{gallery_name}</strong></p>
<p class="email-text">{message}</p>
<a href="{gallery_url}" class="email-button">View Your Photos</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Gallery by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Your gallery "{gallery_name}" is ready! View it at: {gallery_url}'
    },
    
    'selection_reminder': {
        'subject': 'Reminder: Select Your Favorite Photos - {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Reminder: Select Your Photos</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">This is a friendly reminder to select your favorite photos from the gallery: <strong>{gallery_name}</strong></p>
<p class="email-text">{message}</p>
<a href="{gallery_url}" class="email-button">Select Photos</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Gallery by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Reminder: Please select your favorite photos from "{gallery_name}". View at: {gallery_url}'
    },
    
    'custom_message': {
        'subject': '{subject}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">{title}</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<div class="email-text" style="white-space: pre-wrap;">{message}</div>
{button_html}
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Message from {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': '{message}\n\nFrom: {photographer_name} via Galerly'
    },
    
    'gallery_expiring_soon': {
        'subject': 'Gallery Expiring Soon - {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<div class="email-alert-box">
<p class="email-alert-text">⚠️ Your gallery will expire soon!</p>
</div>
<h1 class="email-title">Gallery Expiring Soon</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">This is a reminder that your gallery <strong>{gallery_name}</strong> will expire in <strong>{days_remaining} day(s)</strong>.</p>
<p class="email-text">Make sure to download your photos before they're no longer available.</p>
<a href="{gallery_url}" class="email-button-alert">Download Photos</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Gallery by {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Your gallery "{gallery_name}" will expire in {days_remaining} day(s). Download your photos at: {gallery_url}'
    },
    
    'gallery_expiration_reminder': {
        'subject': 'Gallery Expiring Soon - Action Required',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<div class="email-alert-box">
<p class="email-alert-text">⏰ Gallery Expiration Reminder</p>
</div>
<h1 class="email-title">Gallery Expiring Soon</h1>
<p class="email-text">Hi <strong>{photographer_name}</strong>,</p>
<p class="email-text">This is a reminder that your gallery <strong>{gallery_name}</strong> will expire on <strong>{expiration_date}</strong>.</p>
<p class="email-text">If you'd like to extend the expiration date, you can update the gallery settings.</p>
<a href="{gallery_url}" class="email-button-alert">Manage Gallery</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">To extend the expiration date, open gallery settings and select a new expiry duration.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Your gallery "{gallery_name}" will expire on {expiration_date}. Manage it at: {gallery_url}'
    },
    
    'client_selected_photos': {
        'subject': 'Client Selected Photos - {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Client Photo Selection</h1>
<p class="email-text">Hi <strong>{photographer_name}</strong>,</p>
<p class="email-text">{client_name} has selected <strong>{selection_count} photo(s)</strong> from the gallery: <strong>{gallery_name}</strong></p>
<a href="{gallery_url}" class="email-button">View Selections</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Notification from Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': '{client_name} has selected {selection_count} photo(s) from "{gallery_name}". View at: {gallery_url}'
    },
    
    'client_feedback_received': {
        'subject': 'New Client Feedback - {gallery_name}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">New Client Feedback</h1>
<p class="email-text">Hi <strong>{photographer_name}</strong>,</p>
<p class="email-text">{client_name} left feedback on the gallery: <strong>{gallery_name}</strong></p>
<div class="email-info-box">
<p class="email-info-item"><span class="email-info-label">Rating:</span> {rating}/5 stars</p>
<p class="email-info-item"><span class="email-info-label">Comment:</span> {feedback}</p>
</div>
<a href="{gallery_url}" class="email-button">View Gallery</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Notification from Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'New feedback from {client_name} on "{gallery_name}": {rating}/5 stars - {feedback}'
    },
    
    'payment_received': {
        'subject': 'Payment Received - Thank You!',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Payment Received</h1>
<p class="email-text">Hi <strong>{client_name}</strong>,</p>
<p class="email-text">Thank you for your payment of <strong>{amount}</strong> for gallery: <strong>{gallery_name}</strong></p>
<p class="email-text">{message}</p>
<div class="email-info-box">
<p class="email-info-item"><span class="email-info-label">Amount:</span> {amount}</p>
<p class="email-info-item"><span class="email-info-label">Gallery:</span> {gallery_name}</p>
<p class="email-info-item"><span class="email-info-label">Date:</span> {payment_date}</p>
</div>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Receipt from {photographer_name} via Galerly.</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Payment of {amount} received for "{gallery_name}". Thank you! - {photographer_name}'
    },
    
    'refund_request_confirmation': {
        'subject': 'Refund Request Received - Galerly',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Refund Request Received</h1>
<p class="email-text">Hi <strong>{user_name}</strong>,</p>
<p class="email-text">We've received your refund request and our team will review it within 2-3 business days.</p>
<div class="email-info-box">
<p class="email-info-item"><span class="email-info-label">Refund ID:</span> {refund_id}</p>
<p class="email-info-item"><span class="email-info-label">Status:</span> Pending Review</p>
</div>
<p class="email-text">Our support team will contact you via email once your refund request has been processed.</p>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">If you have any questions, please contact us at <strong>{support_email}</strong></p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Your refund request (ID: {refund_id}) has been received and will be reviewed within 2-3 business days. Contact: {support_email}'
    },
    
    'admin_refund_notification': {
        'subject': 'NEW REFUND REQUEST - {user_email} - {plan}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<div class="email-alert-box">
<p class="email-alert-text">🚨 NEW REFUND REQUEST</p>
</div>
<h1 class="email-title">Refund Request</h1>
<div class="email-info-box">
<p class="email-info-item"><span class="email-info-label">Refund ID:</span> {refund_id}</p>
<p class="email-info-item"><span class="email-info-label">User:</span> {user_name} ({user_email})</p>
<p class="email-info-item"><span class="email-info-label">Plan:</span> {plan}</p>
</div>
<p class="email-text"><strong>User's Reason:</strong></p>
<div class="email-info-box">
<p class="email-info-item" style="white-space: pre-wrap;">{reason}</p>
</div>
<p class="email-text"><strong>Eligibility Details:</strong></p>
<div class="email-info-box">
<p class="email-info-item" style="white-space: pre-wrap;">{details}</p>
</div>
<a href="{admin_url}" class="email-button-alert">Review Refund Request</a>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">Admin notification from Galerly</p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'NEW REFUND REQUEST\nRefund ID: {refund_id}\nUser: {user_name} ({user_email})\nPlan: {plan}\nReason: {reason}\nDetails: {details}'
    },
    
    'refund_status_update': {
        'subject': 'Refund Request Update - Status: {status}',
        'html': '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">''' + GALERLY_EMAIL_STYLES + '''</head><body>
<div class="email-container">''' + get_email_header() + '''
<div class="email-body">
<h1 class="email-title">Refund Request Update</h1>
<p class="email-text">Hi <strong>{user_name}</strong>,</p>
<p class="email-text">Your refund request status has been updated:</p>
<div class="email-info-box">
<p class="email-info-item"><span class="email-info-label">Refund ID:</span> {refund_id}</p>
<p class="email-info-item"><span class="email-info-label">Status:</span> {status}</p>
</div>
<p class="email-text"><strong>Admin Notes:</strong></p>
<div class="email-info-box">
<p class="email-info-item" style="white-space: pre-wrap;">{admin_notes}</p>
</div>
<hr class="email-divider">
<p class="email-text" style="color: #86868B; font-size: 14px;">If you have any questions, please contact us at <strong>{support_email}</strong></p>
</div>''' + get_email_footer() + '''</div></body></html>''',
        'text': 'Refund request update (ID: {refund_id}). Status: {status}. Admin notes: {admin_notes}. Contact: {support_email}'
    }
}

