"""
Authentication handlers
"""
import uuid
import secrets
import re
import random
from datetime import datetime
from utils.config import users_table, sessions_table
from utils.response import create_response, get_required_env
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
        print(f"⚠️  Error sending verification email: {str(e)}")
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
    
    # Generate default username from email (before @) if not provided
    default_username = ''
    if email and '@' in email:
        default_username = email.split('@')[0]
    username = body.get('username', default_username).strip()
    role = body.get('role', 'photographer')
    
    if not email or not password:
        return create_response(400, {'error': 'Email and password required'})
    
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
    
    # Validate username
    if username and len(username) < 3:
        return create_response(400, {'error': 'Username must be at least 3 characters long'})
    if username and len(username) > 50:
        return create_response(400, {'error': 'Username must be less than 50 characters'})
    
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
            existing_user = response['Item']
            account_status = existing_user.get('account_status', 'ACTIVE')
            
            # If account is pending deletion, offer restoration
            if account_status == 'PENDING_DELETION':
                return create_response(409, {
                    'error': 'Account pending deletion',
                    'message': 'An account with this email is scheduled for deletion. Contact support to restore your account.',
                    'support_email': 'support@galerly.com',
                    'can_restore': True,
                    'deletion_date': existing_user.get('permanent_deletion_date')
                })
            
            # Active account already exists
            return create_response(409, {'error': 'User already exists'})
    except:
        pass
    
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'email': email,
        'username': username,
        'role': role,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'subscription': 'free',
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
        'user_id': user['id'],  # Store user_id for session invalidation
        'user': user,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    })
    
    # Set HttpOnly cookie for security
    # 7 days expiration (Swiss law compliance)
    max_age = 60 * 60 * 24 * 7  # 7 days in seconds
    # Use Lax for development (works in Safari), Strict for production
    # Remove Secure flag for localhost (HTTP)
    import os
    is_local = 'localhost' in os.environ.get('FRONTEND_URL', '')
    secure_flag = '' if is_local else 'Secure; '
    samesite = 'Lax' if is_local else 'Strict'
    cookie_value = f'galerly_session={token}; HttpOnly; {secure_flag}SameSite={samesite}; Path=/; Max-Age={max_age}'
    
    return {
        'statusCode': 201,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': get_required_env('FRONTEND_URL'),
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,Cookie',
            'Access-Control-Allow-Credentials': 'true',
            'Set-Cookie': cookie_value
        },
        'body': __import__('json').dumps({
            'id': user_id,
            'email': email,
            'username': username,
            'role': role,
            'subscription': 'free'
            # No token in response - it's in HttpOnly cookie!
        })
    }

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
        
        # Check if account is deleted or pending deletion
        account_status = user.get('account_status', 'ACTIVE')
        if account_status == 'PENDING_DELETION':
            return create_response(403, {
                'error': 'Account deleted',
                'message': 'Your account has been scheduled for deletion. Contact support to restore your account.',
                'support_email': 'support@galerly.com',
                'can_restore': True,
                'deletion_date': user.get('permanent_deletion_date')
            })
        
        if user['password_hash'] != hash_password(password):
            return create_response(401, {'error': 'Invalid credentials'})
    except:
        return create_response(401, {'error': 'Invalid credentials'})
    
    # Create session token
    token = secrets.token_urlsafe(32)
    sessions_table.put_item(Item={
        'token': token,
        'user_id': user['id'],  # Store user_id for session invalidation
        'user': user,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    })
    
    # Set HttpOnly cookie for security
    # 7 days expiration (Swiss law compliance)
    max_age = 60 * 60 * 24 * 7  # 7 days in seconds
    # Use Lax for development (works in Safari), Strict for production
    # Remove Secure flag for localhost (HTTP)
    import os
    is_local = 'localhost' in os.environ.get('FRONTEND_URL', '')
    secure_flag = '' if is_local else 'Secure; '
    samesite = 'Lax' if is_local else 'Strict'
    cookie_value = f'galerly_session={token}; HttpOnly; {secure_flag}SameSite={samesite}; Path=/; Max-Age={max_age}'
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': get_required_env('FRONTEND_URL'),
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,Cookie',
            'Access-Control-Allow-Credentials': 'true',
            'Set-Cookie': cookie_value
        },
        'body': __import__('json').dumps({
            'id': user['id'],
            'email': user['email'],
            'username': user.get('username', email.split('@')[0] if '@' in email else email),
            'role': user.get('role', 'photographer'),
            'subscription': user.get('subscription', 'free')
            # No token in response - it's in HttpOnly cookie!
        })
    }

def handle_get_me(user):
    """Get current user info"""
    return create_response(200, {
        'id': user['id'],
        'email': user['email'],
        'username': user.get('username', user['email'].split('@')[0] if '@' in user['email'] else user['email']),
        'name': user.get('name'),
        'bio': user.get('bio'),
        'city': user.get('city'),
        'role': user.get('role', 'photographer'),
        'subscription': user.get('subscription', 'free')
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
    import os
    is_local = 'localhost' in os.environ.get('FRONTEND_URL', '')
    secure_flag = '' if is_local else 'Secure; '
    samesite = 'Lax' if is_local else 'Strict'
    cookie_value = f'galerly_session=; HttpOnly; {secure_flag}SameSite={samesite}; Path=/; Max-Age=0'
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': get_required_env('FRONTEND_URL'),
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,Cookie',
            'Access-Control-Allow-Credentials': 'true',
            'Set-Cookie': cookie_value
        },
        'body': __import__('json').dumps({
            'message': 'Logged out successfully'
        })
    }


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
            print(f"⚠️  Error sending password reset email: {str(e)}")
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


def handle_delete_account(user):
    """
    Soft delete user account - marks for deletion with 30-day archival period
    Similar to gallery deletion: archived for 30 days before permanent removal
    """
    try:
        user_email = user.get('email')
        user_id = user.get('id')
        
        if not user_email or not user_id:
            return create_response(400, {'error': 'Invalid user session'})
        
        # Get current timestamp
        now = datetime.utcnow()
        deletion_scheduled_at = now.isoformat() + 'Z'
        
        # Calculate permanent deletion date (30 days from now)
        from datetime import timedelta
        deletion_date = now + timedelta(days=30)
        deletion_date_str = deletion_date.isoformat() + 'Z'
        
        print(f"🗑️ Soft deleting account: {user_email}")
        print(f"   User ID: {user_id}")
        print(f"   Scheduled for permanent deletion: {deletion_date_str}")
        
        # Update user account with deletion markers
        # Mark account as deleted and set deletion date
        users_table.update_item(
            Key={'email': user_email},
            UpdateExpression='''
                SET deleted_at = :deleted_at,
                    deletion_scheduled_at = :scheduled_at,
                    permanent_deletion_date = :deletion_date,
                    account_status = :status,
                    updated_at = :now
            ''',
            ExpressionAttributeValues={
                ':deleted_at': deletion_scheduled_at,
                ':scheduled_at': deletion_scheduled_at,
                ':deletion_date': deletion_date_str,
                ':status': 'PENDING_DELETION',
                ':now': deletion_scheduled_at
            }
        )
        
        # Import galleries table for marking user's galleries
        from utils.config import galleries_table, photos_table
        
        # Mark all user's galleries for deletion
        try:
            galleries_response = galleries_table.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            user_galleries = galleries_response.get('Items', [])
            print(f"   Found {len(user_galleries)} galleries to mark for deletion")
            
            for gallery in user_galleries:
                gallery_id = gallery.get('id')
                if gallery_id:
                    galleries_table.update_item(
                        Key={
                            'user_id': user_id,
                            'id': gallery_id
                        },
                        UpdateExpression='''
                            SET deleted_at = :deleted_at,
                                deletion_scheduled_at = :scheduled_at,
                                permanent_deletion_date = :deletion_date,
                                updated_at = :now
                        ''',
                        ExpressionAttributeValues={
                            ':deleted_at': deletion_scheduled_at,
                            ':scheduled_at': deletion_scheduled_at,
                            ':deletion_date': deletion_date_str,
                            ':now': deletion_scheduled_at
                        }
                    )
                    print(f"   ✓ Marked gallery {gallery_id} for deletion")
        except Exception as gallery_error:
            print(f"⚠️  Error marking galleries for deletion: {gallery_error}")
            # Continue with account deletion even if gallery marking fails
        
        # Invalidate all user sessions (logout from all devices)
        try:
            sessions_response = sessions_table.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            for session in sessions_response.get('Items', []):
                token = session.get('token')
                if token:
                    sessions_table.delete_item(Key={'token': token})
            
            print(f"   ✓ Invalidated all user sessions")
        except Exception as session_error:
            print(f"⚠️  Error invalidating sessions: {session_error}")
        
        # Send account deletion notification email
        try:
            from utils.email import send_email
            import os
            
            support_email = os.environ.get('SUPPORT_EMAIL', 'support@galerly.com')
            
            send_email(
                to_email=user_email,
                template_name='account_deletion_scheduled',
                template_vars={
                    'user_name': user.get('name', user_email.split('@')[0]),
                    'deletion_date': deletion_date.strftime('%B %d, %Y'),
                    'days_remaining': '30',
                    'support_email': support_email
                }
            )
            print(f"   ✓ Sent deletion notification email to {user_email}")
        except Exception as email_error:
            print(f"⚠️  Error sending deletion email: {email_error}")
            import traceback
            traceback.print_exc()
            # Continue even if email fails
        
        print(f"✅ Account soft deleted successfully")
        print(f"   Account will be permanently deleted on: {deletion_date_str}")
        
        # Check if local development to set appropriate cookie flags
        import os
        is_local = 'localhost' in os.environ.get('FRONTEND_URL', '')
        secure_flag = '' if is_local else 'Secure; '
        samesite = 'Lax' if is_local else 'Strict'
        cookie_value = f'galerly_session=; HttpOnly; {secure_flag}SameSite={samesite}; Path=/; Max-Age=0'
        
        response = create_response(200, {
            'message': 'Account scheduled for deletion. Your data will be permanently removed in 30 days.',
            'deletion_date': deletion_date_str,
            'days_remaining': 30
        })
        
        # Add Set-Cookie header to clear session
        response['headers']['Set-Cookie'] = cookie_value
        
        return response
        
    except Exception as e:
        print(f"❌ Error deleting account: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to delete account. Please contact support.'})

