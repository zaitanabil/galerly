"""
Authentication handlers
"""
import uuid
import secrets
import re
import random
import os
from datetime import datetime
from utils.config import users_table, sessions_table
from utils.response import create_response
from utils.auth import hash_password
from utils.email import send_welcome_email, send_password_reset_email, send_verification_code_email

def validate_email_format(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if len(password) > 128:
        return False, 'Password must be less than 128 characters'
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    if not has_letter:
        return False, 'Password must contain at least one letter'
    if not has_number:
        return False, 'Password must contain at least one number'
    return True, None


def generate_username_from_name(full_name):
    """
    Generate a clean username from full name
    Examples:
      - "John Doe" -> "johndoe"
      - "Mary-Jane Smith" -> "maryjanesmit"
      - "José García" -> "josegarcia"
    """
    if not full_name:
        return ""
    
    # Remove accents and special characters using NFD normalization + transliteration
    import unicodedata
    
    # First, normalize to NFD (decomposed form)
    normalized = unicodedata.normalize('NFD', full_name)
    
    # Remove combining characters (accents)
    ascii_name = ''.join(c for c in normalized if not unicodedata.combining(c))
    
    # Manual transliteration for common non-ASCII letters that don't decompose
    transliterations = {
        'ø': 'o', 'Ø': 'O',
        'æ': 'ae', 'Æ': 'AE',
        'å': 'a', 'Å': 'A',
        'ß': 'ss',
        'þ': 'th', 'Þ': 'TH',
        'ð': 'd', 'Ð': 'D',
    }
    for char, replacement in transliterations.items():
        ascii_name = ascii_name.replace(char, replacement)
    
    # Convert to lowercase and remove non-alphanumeric characters
    clean_name = ''.join(c.lower() for c in ascii_name if c.isalnum() or c.isspace())
    
    # Remove spaces and truncate to 20 characters
    username = clean_name.replace(' ', '')[:20]
    
    return username if username else ""


def check_username_exists(username):
    """Check if username already exists in database"""
    try:
        # Scan for username (note: in production, use a GSI on username for better performance)
        response = users_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username},
            Limit=1
        )
        return len(response.get('Items', [])) > 0
    except Exception as e:
        print(f"Error checking username: {str(e)}")
        return False


def generate_unique_username(full_name, email):
    """
    Generate a unique username from full name
    If username exists, append numbers until unique
    """
    # Start with name-based username
    base_username = generate_username_from_name(full_name)
    
    # Fallback to email if name is empty/invalid
    if not base_username or len(base_username) < 3:
        if email and '@' in email:
            base_username = email.split('@')[0].lower()
            base_username = ''.join(c for c in base_username if c.isalnum())[:20]
    
    # Ensure minimum length
    if not base_username or len(base_username) < 3:
        base_username = 'user' + str(random.randint(1000, 9999))
    
    # Check if base username is available
    username = base_username
    if not check_username_exists(username):
        return username
    
    # If taken, try with numbers (1-999)
    for i in range(1, 1000):
        # Truncate to make room for number
        max_base_length = int(os.environ.get('MAX_USERNAME_BASE_LENGTH'))
        truncated_base = base_username[:max_base_length]
        username = f"{truncated_base}{i}"
        
        if not check_username_exists(username):
            return username
    
    # Fallback: use random UUID suffix
    import uuid
    return f"{base_username[:40]}{uuid.uuid4().hex[:8]}"

def handle_request_verification_code(body):
    """Send verification code to email for account creation"""
    email = body.get('email', '').lower().strip()
    
    if not email:
        return create_response(400, {'error': 'Email is required'})
    
    # Validate email format
    if not validate_email_format(email):
        return create_response(400, {'error': 'Invalid email format'})
    
    if len(email) > 255:
        return create_response(400, {'error': 'Email address is too long'})
    
    try:
        # Check if user already exists
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            return create_response(409, {'error': 'An account with this email already exists'})
    except:
        pass
    
    # Generate 6-digit verification code
    verification_code = str(random.randint(100000, 999999))
    
    # Store verification code in sessions table with expiration (10 minutes)
    expires_at = int(datetime.utcnow().timestamp() + 600)  # 10 minutes from now
    token = secrets.token_urlsafe(32)  # Unique token to retrieve the code
    
    sessions_table.put_item(Item={
        'token': token,
        'type': 'email_verification',
        'email': email,
        'code': verification_code,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'expires_at': expires_at,
        'verified': False
    })
    
    # Send verification email
    try:
        send_verification_code_email(email, verification_code)
    except Exception as e:
        print(f" Error sending verification email: {str(e)}")
        return create_response(500, {'error': 'Failed to send verification email. Please try again.'})
    
    return create_response(200, {
        'message': 'Verification code sent to your email',
        'verification_token': token
    })

def handle_verify_code(body):
    """Verify the email verification code"""
    verification_token = body.get('verification_token', '')
    code = body.get('code', '').strip()
    
    if not verification_token or not code:
        return create_response(400, {'error': 'Verification token and code are required'})
    
    try:
        # Get verification record from sessions table
        response = sessions_table.get_item(Key={'token': verification_token})
        if 'Item' not in response:
            return create_response(400, {'error': 'Invalid or expired verification token'})
        
        verification_record = response['Item']
        
        # Check if it's an email verification token
        if verification_record.get('type') != 'email_verification':
            return create_response(400, {'error': 'Invalid verification token'})
        
        # Check if token has expired
        expires_at = verification_record.get('expires_at', 0)
        if int(datetime.utcnow().timestamp()) > expires_at:
            # Delete expired token
            sessions_table.delete_item(Key={'token': verification_token})
            return create_response(400, {'error': 'Verification code has expired. Please request a new one.'})
        
        # Check if code matches
        stored_code = verification_record.get('code', '')
        if code != stored_code:
            return create_response(400, {'error': 'Invalid verification code. Please try again.'})
        
        # Mark as verified
        sessions_table.update_item(
            Key={'token': verification_token},
            UpdateExpression='SET verified = :verified',
            ExpressionAttributeValues={
                ':verified': True
            }
        )
        
        return create_response(200, {
            'message': 'Email verified successfully',
            'email': verification_record.get('email')
        })
    except Exception as e:
        print(f"Error verifying code: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to verify code'})

def handle_register(body):
    """Register new user - requires verified email"""
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    verification_token = body.get('verification_token', '')
    name = body.get('name', '').strip()  # Full name
    role = body.get('role', 'photographer')
    
    if not email or not password:
        return create_response(400, {'error': 'Email and password required'})
    
    if not name:
        return create_response(400, {'error': 'Full name is required'})
    
    if len(name) > 100:
        return create_response(400, {'error': 'Name must be less than 100 characters'})
    
    if not verification_token:
        return create_response(400, {'error': 'Email verification required. Please verify your email first.'})
    
    # Validate email format
    if not validate_email_format(email):
        return create_response(400, {'error': 'Invalid email format'})
    
    if len(email) > 255:
        return create_response(400, {'error': 'Email address is too long'})
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        return create_response(400, {'error': error_message})
    
        try:
            # Verify that email was verified
            response = sessions_table.get_item(Key={'token': verification_token})
            if 'Item' not in response:
                return create_response(400, {'error': 'Invalid verification token. Please verify your email again.'})
            
            verification_record = response['Item']
            
            # Check if it's an email verification token
            if verification_record.get('type') != 'email_verification':
                return create_response(400, {'error': 'Invalid verification token'})
            
            # Check if verified
            if not verification_record.get('verified', False):
                return create_response(400, {'error': 'Email not verified. Please enter the verification code sent to your email.'})
            
            # Check if token has expired
            expires_at = verification_record.get('expires_at', 0)
            if int(datetime.utcnow().timestamp()) > expires_at:
                sessions_table.delete_item(Key={'token': verification_token})
                return create_response(400, {'error': 'Verification token has expired. Please request a new verification code.'})
            
            # Check if email matches
            if verification_record.get('email') != email:
                return create_response(400, {'error': 'Email mismatch. Please use the email you verified.'})
        except Exception as e:
            print(f"Error checking verification: {str(e)}")
            return create_response(500, {'error': 'Failed to verify email verification status'})
    
    # Check if user exists
    try:
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            return create_response(409, {'error': 'User already exists'})
    except:
        pass
    
    # Generate unique username from full name
    username = generate_unique_username(name, email)
    print(f"Generated username '{username}' from name '{name}'")
    
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'email': email,
        'name': name,  # Store full name
        'username': username,  # Auto-generated unique username
        'role': role,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'subscription': 'free',
        'plan': 'free', # Initialize plan
        'email_verified': True  # Email was verified during registration
    }
    
    # Store user in DynamoDB
    users_table.put_item(Item=user)
    
    # Delete verification token (one-time use)
    try:
        sessions_table.delete_item(Key={'token': verification_token})
    except:
        pass
    
    # Send welcome email (async - don't wait for it)
    try:
        send_welcome_email(email, username)
    except:
        pass  # Don't fail registration if email fails
    
    # Create session token
    token = secrets.token_urlsafe(32)
    sessions_table.put_item(Item={
        'token': token,
        'user': user,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    })
    
    # Set HttpOnly cookie for security
    # 7 days expiration (Swiss law compliance)
    max_age = int(os.environ.get('SESSION_MAX_AGE'))
    
    # Check environment for Secure flag
    is_local = os.environ.get('ENVIRONMENT') == 'local'
    secure_flag = '; Secure' if not is_local else ''
    
    cookie_value = f'galerly_session={token}; HttpOnly{secure_flag}; SameSite=Strict; Path=/; Max-Age={max_age}'
    
    return create_response(201, {
        'id': user_id,
        'email': email,
        'name': name,
        'username': username,
        'role': role,
        'subscription': 'free',
        'plan': 'free'
    }, headers={'Set-Cookie': cookie_value})

def handle_login(body):
    """Login user"""
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    
    if not email or not password:
        return create_response(400, {'error': 'Email and password required'})
    
    # Validate email format
    if not validate_email_format(email):
        return create_response(400, {'error': 'Invalid email format'})
    
    try:
        response = users_table.get_item(Key={'email': email})
        if 'Item' not in response:
            return create_response(401, {'error': 'Invalid credentials'})
        
        user = response['Item']
        if user['password_hash'] != hash_password(password):
            return create_response(401, {'error': 'Invalid credentials'})
    except:
        return create_response(401, {'error': 'Invalid credentials'})
    
    # Create session token
    token = secrets.token_urlsafe(32)
    sessions_table.put_item(Item={
        'token': token,
        'user': user,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    })
    
    # Set HttpOnly cookie for security
    # 7 days expiration (Swiss law compliance)
    max_age = int(os.environ.get('SESSION_MAX_AGE'))
    
    # Check environment for Secure flag
    is_local = os.environ.get('ENVIRONMENT') == 'local'
    secure_flag = '; Secure' if not is_local else ''
    
    cookie_value = f'galerly_session={token}; HttpOnly{secure_flag}; SameSite=Strict; Path=/; Max-Age={max_age}'
    
    return create_response(200, {
        'id': user['id'],
        'email': user['email'],
        'username': user.get('username', email.split('@')[0] if '@' in email else email),
        'role': user.get('role', 'photographer'),
        'subscription': user.get('subscription', 'free'),
        'plan': user.get('plan') or user.get('subscription', 'free')
    }, headers={'Set-Cookie': cookie_value})

def handle_get_me(user):
    """Get current user info"""
    # Fetch fresh user data from DB to get latest settings
    try:
        response = users_table.get_item(Key={'email': user['email']})
        db_user = response.get('Item', user)
    except:
        db_user = user

    return create_response(200, {
        'id': db_user['id'],
        'email': db_user['email'],
        'username': db_user.get('username', db_user['email'].split('@')[0] if '@' in db_user['email'] else db_user['email']),
        'name': db_user.get('name'),
        'bio': db_user.get('bio'),
        'city': db_user.get('city'),
        'role': db_user.get('role', 'photographer'),
        'subscription': db_user.get('subscription', 'free'),
        'plan': db_user.get('plan') or db_user.get('subscription', 'free'),
        # Watermark Settings
        'watermark_enabled': db_user.get('watermark_enabled', False),
        'watermark_text': db_user.get('watermark_text', ''),
        'watermark_position': db_user.get('watermark_position', 'bottom-right'),
        'watermark_opacity': db_user.get('watermark_opacity', 0.5)
    })

def handle_logout(event):
    """Logout user - invalidate session and clear cookie"""
    # Get token from cookie
    headers = event.get('headers', {})
    cookie_header = headers.get('Cookie') or headers.get('cookie', '')
    
    token = None
    if cookie_header:
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        token = cookies.get('galerly_session')
    
    # Delete session from database if token exists
    if token:
        try:
            sessions_table.delete_item(Key={'token': token})
        except Exception as e:
            print(f"Error deleting session: {str(e)}")
    
    # Clear cookie by setting Max-Age=0
    is_local = os.environ.get('ENVIRONMENT') == 'local'
    secure_flag = '; Secure' if not is_local else ''
    
    cookie_value = f'galerly_session=; HttpOnly{secure_flag}; SameSite=Strict; Path=/; Max-Age=0'
    
    return create_response(200, {
        'message': 'Logged out successfully'
    }, headers={'Set-Cookie': cookie_value})


def handle_request_password_reset(body):
    """Request password reset - sends email with reset token"""
    email = body.get('email', '').lower().strip()
    
    if not email:
        return create_response(400, {'error': 'Email is required'})
    
    # Validate email format
    if not validate_email_format(email):
        return create_response(400, {'error': 'Invalid email format'})
    
    try:
        # Check if user exists
        response = users_table.get_item(Key={'email': email})
        if 'Item' not in response:
            # Don't reveal if user exists or not (security best practice)
            return create_response(200, {'message': 'If an account exists with this email, a password reset link has been sent.'})
        
        user = response['Item']
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token in sessions table with expiration (1 hour)
        expires_at = int(datetime.utcnow().timestamp() + 3600)  # 1 hour from now
        sessions_table.put_item(Item={
            'token': reset_token,
            'type': 'password_reset',
            'user_id': user['id'],
            'email': email,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'expires_at': expires_at
        })
        
        # Send password reset email
        try:
            user_name = user.get('username') or user.get('name') or (email.split('@')[0] if '@' in email else email)
            send_password_reset_email(email, user_name, reset_token)
        except Exception as e:
            print(f" Error sending password reset email: {str(e)}")
            # Don't fail the request if email fails
        
        return create_response(200, {'message': 'If an account exists with this email, a password reset link has been sent.'})
    except Exception as e:
        print(f"Error requesting password reset: {str(e)}")
        return create_response(500, {'error': 'Failed to process password reset request'})

def handle_reset_password(body):
    """Reset password using reset token"""
    token = body.get('token', '')
    new_password = body.get('password', '')
    
    if not token or not new_password:
        return create_response(400, {'error': 'Token and password are required'})
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        return create_response(400, {'error': error_message})
    
    try:
        # Get reset token from sessions table
        response = sessions_table.get_item(Key={'token': token})
        if 'Item' not in response:
            return create_response(400, {'error': 'Invalid or expired reset token'})
        
        reset_record = response['Item']
        
        # Check if it's a password reset token
        if reset_record.get('type') != 'password_reset':
            return create_response(400, {'error': 'Invalid reset token'})
        
        # Check if token has expired
        expires_at = reset_record.get('expires_at', 0)
        if int(datetime.utcnow().timestamp()) > expires_at:
            # Delete expired token
            sessions_table.delete_item(Key={'token': token})
            return create_response(400, {'error': 'Reset token has expired. Please request a new one.'})
        
        # Get user email from reset record
        user_email = reset_record.get('email')
        if not user_email:
            return create_response(400, {'error': 'Invalid reset token'})
        
        # Update user password
        users_table.update_item(
            Key={'email': user_email},
            UpdateExpression='SET password_hash = :hash, updated_at = :now',
            ExpressionAttributeValues={
                ':hash': hash_password(new_password),
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Delete reset token (one-time use)
        sessions_table.delete_item(Key={'token': token})
        
        return create_response(200, {'message': 'Password reset successfully. You can now login with your new password.'})
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to reset password'})

def handle_delete_account(user, cookie_header=None):
    """
    Initiate account deletion as a background job
    In LocalStack mode: Process deletion synchronously for immediate testing
    In Production: Queue as background job for asynchronous processing
    """
    try:
        from handlers.background_jobs_handler import create_background_job, process_account_deletion
        from utils.config import AWS_ENDPOINT_URL
        
        # Extract session token from cookie to clear it immediately
        session_token = None
        if cookie_header:
            cookies = cookie_header.split(';')
            for cookie in cookies:
                if 'galerly_session' in cookie:
                    session_token = cookie.split('=')[1].strip()
                    break
        
        # Delete the current session immediately so user is logged out
        if session_token:
            try:
                sessions_table.delete_item(Key={'token': session_token})
            except Exception as e:
                print(f"Error deleting session: {str(e)}")
        
        # Create background job for full account deletion
        job_id = create_background_job(
            job_type='account_deletion',
            user_id=user['id'],
            user_email=user['email'],
            metadata={'initiated_at': datetime.utcnow().isoformat() + 'Z'}
        )
        
        # In LocalStack mode: Process deletion synchronously
        if AWS_ENDPOINT_URL and 'localstack' in AWS_ENDPOINT_URL.lower():
            print(f"Processing account deletion synchronously for user {user['email']}")
            success = process_account_deletion(
                job_id=job_id,
                user_id=user['id'],
                user_email=user['email']
            )
            
            # Clear session cookie
            is_local = os.environ.get('ENVIRONMENT') == 'local'
            secure_flag = '; Secure' if not is_local else ''
            cookie_value = f'galerly_session=; HttpOnly{secure_flag}; SameSite=Strict; Path=/; Max-Age=0'
            
            if success:
                return create_response(200, {
                    'message': 'Account deleted successfully',
                    'job_id': job_id
                }, headers={'Set-Cookie': cookie_value})
            else:
                return create_response(500, {'error': 'Failed to delete account'})
        
        # Production mode: Queue as background job for async processing
        # Clear session cookie
        is_local = os.environ.get('ENVIRONMENT') == 'local'
        secure_flag = '; Secure' if not is_local else ''
        cookie_value = f'galerly_session=; HttpOnly{secure_flag}; SameSite=Strict; Path=/; Max-Age=0'
        
        return create_response(200, {
            'message': 'Account deletion initiated. This process may take a few minutes.',
            'job_id': job_id,
            'status': 'pending'
        }, headers={'Set-Cookie': cookie_value})
        
    except Exception as e:
        print(f"Error initiating account deletion: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to initiate account deletion'})


def handle_generate_api_key(user):
    """Generate a new API key for the user"""
    try:
        # Check if plan supports API access (Pro or Ultimate)
        # Assuming simple check here, robust check is in billing_handler
        plan = user.get('plan', 'free')
        if plan not in ['pro', 'ultimate']:
            return create_response(403, {'error': 'API access requires Pro or Ultimate plan'})
            
        # Generate API key (format: galerly_live_<random>)
        # Not using 'sk_live_' prefix to avoid confusion with Stripe keys
        api_key = f"galerly_live_{secrets.token_urlsafe(24)}"
        
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET api_key = :key, api_key_created_at = :now',
            ExpressionAttributeValues={
                ':key': api_key,
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        return create_response(200, {'api_key': api_key})
    except Exception as e:
        print(f"Error generating API key: {str(e)}")
        return create_response(500, {'error': 'Failed to generate API key'})

def handle_get_api_key(user):
    """Get existing API key (masked)"""
    try:
        # Fetch fresh user data
        response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
            
        fresh_user = response['Item']
        api_key = fresh_user.get('api_key')
        
        if not api_key:
            return create_response(200, {'api_key': None})
            
        return create_response(200, {'api_key': api_key}) # Return full key so they can copy it
    except Exception as e:
        print(f"Error getting API key: {str(e)}")
        return create_response(500, {'error': 'Failed to get API key'})
