"""
Email utility functions - Add these to existing email.py
"""

def send_account_deletion_scheduled_email(to_email, user_name, deletion_date):
    """
    Send confirmation email when account deletion is scheduled
    Includes instructions for restoration
    """
    from datetime import datetime
    
    # Parse deletion date
    deletion_dt = datetime.fromisoformat(deletion_date.replace('Z', ''))
    deletion_formatted = deletion_dt.strftime('%B %d, %Y at %I:%M %p UTC')
    
    subject = "Account Deletion Scheduled - You Have 30 Days to Change Your Mind"
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1D1D1F; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: #f5f5f7; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 30px; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ff9500; padding: 20px; margin: 20px 0; }}
            .button {{ display: inline-block; background: #0066CC; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
            .info-box {{ background: #f5f5f7; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #86868b; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #d2d2d7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; color: #ff3b30;">⚠️ Account Deletion Scheduled</h1>
            </div>
            
            <p>Hello {user_name},</p>
            
            <p>Your Galerly account has been scheduled for deletion as requested.</p>
            
            <div class="warning">
                <strong>⏰ You have 30 days to change your mind</strong>
                <p style="margin: 10px 0 0 0;">Your account will be permanently deleted on <strong>{deletion_formatted}</strong></p>
            </div>
            
            <h2>What Happens Next?</h2>
            
            <div class="info-box">
                <p><strong>Immediately:</strong></p>
                <ul>
                    <li>You've been logged out of all devices</li>
                    <li>You cannot access your account</li>
                    <li>Your galleries are not visible to clients</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>After 30 days:</strong></p>
                <ul>
                    <li>Your account will be permanently deleted</li>
                    <li>All photos and galleries will be removed</li>
                    <li>This action cannot be undone</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>Exception:</strong></p>
                <ul>
                    <li>Billing records retained for 7 years (tax law requirement)</li>
                </ul>
            </div>
            
            <h2>Changed Your Mind?</h2>
            
            <p>You can restore your account at any time within the next 30 days by simply logging in again. We'll ask if you want to restore your account.</p>
            
            <div style="text-align: center;">
                <a href="https://app.galerly.com/login" class="button">Restore My Account</a>
            </div>
            
            <p style="margin-top: 30px;">If you didn't request this deletion, please restore your account immediately and change your password.</p>
            
            <div class="footer">
                <p>Galerly - Professional Photography Platform</p>
                <p>Questions? Contact us at support@galerly.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Hello {user_name},

Your Galerly account has been scheduled for deletion as requested.

⚠️ YOU HAVE 30 DAYS TO CHANGE YOUR MIND

Your account will be permanently deleted on {deletion_formatted}

WHAT HAPPENS NEXT?

Immediately:
- You've been logged out of all devices
- You cannot access your account
- Your galleries are not visible to clients

After 30 days:
- Your account will be permanently deleted
- All photos and galleries will be removed
- This action cannot be undone

Exception: Billing records retained for 7 years (tax law requirement)

CHANGED YOUR MIND?

You can restore your account at any time within the next 30 days by simply logging in again.

Visit: https://app.galerly.com/login

If you didn't request this deletion, please restore your account immediately and change your password.

---
Galerly - Professional Photography Platform
Questions? Contact us at support@galerly.com
    """
    
    send_email(to_email, subject, html_body, text_body)


def send_account_restored_email(to_email, user_name):
    """
    Send confirmation email when account is restored
    """
    subject = "Welcome Back! Your Account Has Been Restored"
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1D1D1F; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ background: #d1f2eb; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 30px; }}
            .success {{ background: #d1f2eb; border-left: 4px solid #34c759; padding: 20px; margin: 20px 0; }}
            .button {{ display: inline-block; background: #0066CC; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #86868b; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #d2d2d7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; color: #34c759;">✅ Account Restored Successfully</h1>
            </div>
            
            <p>Hello {user_name},</p>
            
            <p>Great news! Your Galerly account has been restored and is now active.</p>
            
            <div class="success">
                <p><strong>✓ All your data is safe</strong></p>
                <ul>
                    <li>Your galleries are accessible</li>
                    <li>All photos preserved</li>
                    <li>Settings and preferences intact</li>
                </ul>
            </div>
            
            <p>You can now log in and continue using Galerly as before.</p>
            
            <div style="text-align: center;">
                <a href="https://app.galerly.com/dashboard" class="button">Go to Dashboard</a>
            </div>
            
            <h3>Security Tip</h3>
            <p>If you didn't restore this account yourself, please change your password immediately and contact support.</p>
            
            <div class="footer">
                <p>Galerly - Professional Photography Platform</p>
                <p>Questions? Contact us at support@galerly.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Hello {user_name},

Great news! Your Galerly account has been restored and is now active.

✓ ALL YOUR DATA IS SAFE
- Your galleries are accessible
- All photos preserved
- Settings and preferences intact

You can now log in and continue using Galerly as before.

Visit: https://app.galerly.com/dashboard

SECURITY TIP
If you didn't restore this account yourself, please change your password immediately and contact support.

---
Galerly - Professional Photography Platform
Questions? Contact us at support@galerly.com
    """
    
    send_email(to_email, subject, html_body, text_body)


def send_account_deleted_confirmation_email(to_email):
    """
    Send final confirmation email after permanent deletion
    """
    subject = "Your Galerly Account Has Been Permanently Deleted"
    
    html_body = """
    <html>
    <head>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1D1D1F; }
            .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
            .header { background: #f5f5f7; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 30px; }
            .footer { text-align: center; color: #86868b; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #d2d2d7; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; color: #1D1D1F;">Account Permanently Deleted</h1>
            </div>
            
            <p>Your Galerly account has been permanently deleted as requested.</p>
            
            <p><strong>What was deleted:</strong></p>
            <ul>
                <li>Your profile and account information</li>
                <li>All galleries and photos</li>
                <li>Settings and preferences</li>
                <li>Analytics data</li>
            </ul>
            
            <p><strong>What was retained:</strong></p>
            <ul>
                <li>Billing records (anonymized, required for tax law compliance for 7 years)</li>
            </ul>
            
            <p>Thank you for using Galerly. If you ever want to come back, you're always welcome to create a new account.</p>
            
            <div class="footer">
                <p>Galerly - Professional Photography Platform</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = """
Your Galerly account has been permanently deleted as requested.

WHAT WAS DELETED:
- Your profile and account information
- All galleries and photos
- Settings and preferences
- Analytics data

WHAT WAS RETAINED:
- Billing records (anonymized, required for tax law compliance for 7 years)

Thank you for using Galerly. If you ever want to come back, you're always welcome to create a new account.

---
Galerly - Professional Photography Platform
    """
    
    send_email(to_email, subject, html_body, text_body)

