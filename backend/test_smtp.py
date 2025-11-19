"""
Test SMTP connection and authentication
Run this to verify your Namecheap Private Email credentials
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_HOST = os.environ.get('SMTP_HOST', 'mail.privateemail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', 'support@galerly.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@galerly.com')
FROM_NAME = os.environ.get('FROM_NAME', 'Galerly')

print("=" * 80)
print("SMTP CONNECTION TEST")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Host: {SMTP_HOST}")
print(f"  Port: {SMTP_PORT}")
print(f"  User: {SMTP_USER}")
print(f"  From: {FROM_EMAIL}")
print(f"  Password Length: {len(SMTP_PASSWORD)} characters")
print(f"  Password Starts With: {SMTP_PASSWORD[:3]}...")
print(f"  Password Ends With: ...{SMTP_PASSWORD[-3:]}")

if not SMTP_PASSWORD:
    print("\n❌ ERROR: SMTP_PASSWORD is empty!")
    exit(1)

print("\n" + "─" * 80)
print("Step 1: Connecting to SMTP server...")
print("─" * 80)

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    print(f"✅ Connected to {SMTP_HOST}:{SMTP_PORT}")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    exit(1)

print("\n" + "─" * 80)
print("Step 2: Starting TLS encryption...")
print("─" * 80)

try:
    server.starttls()
    print("✅ TLS encryption started")
except Exception as e:
    print(f"❌ TLS failed: {str(e)}")
    server.quit()
    exit(1)

print("\n" + "─" * 80)
print("Step 3: Authenticating with SMTP server...")
print("─" * 80)

try:
    server.login(SMTP_USER, SMTP_PASSWORD)
    print(f"✅ Authentication successful for {SMTP_USER}")
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {str(e)}")
    print("\nPossible issues:")
    print("  1. Wrong username or password")
    print("  2. Account locked/suspended")
    print("  3. Special characters in password need escaping")
    print("  4. Two-factor authentication enabled")
    print("  5. SMTP access disabled in email settings")
    server.quit()
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    server.quit()
    exit(1)

print("\n" + "─" * 80)
print("Step 4: Sending test email...")
print("─" * 80)

# Ask for test recipient
test_email = input("\nEnter test email address (press Enter to skip): ").strip()

if test_email:
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Galerly SMTP Test'
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = test_email
        
        text_body = "This is a test email from Galerly to verify SMTP configuration."
        html_body = "<p>This is a test email from Galerly to verify SMTP configuration.</p>"
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        server.send_message(msg)
        print(f"✅ Test email sent to {test_email}")
        print("\nCheck the inbox (and spam folder) for the test email.")
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
else:
    print("⏭️  Skipped test email")

print("\n" + "─" * 80)
print("Step 5: Closing connection...")
print("─" * 80)

try:
    server.quit()
    print("✅ Connection closed")
except:
    pass

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nSummary:")
print("  ✅ SMTP connection works")
print("  ✅ Authentication successful")
print("  ✅ Ready to send emails")
print("\nIf authentication failed, check:")
print("  1. Verify credentials in Namecheap")
print("  2. Check if account is locked")
print("  3. Ensure SMTP is enabled")
print("  4. Try resetting password")
print("=" * 80 + "\n")

