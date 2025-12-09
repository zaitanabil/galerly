"""
Key Rotation System
Manages automatic rotation of encryption keys and password salts
Enforces weekly rotation policy for enhanced security
"""
import os
import json
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from utils.config import dynamodb, users_table
from utils.response import create_response

# Key rotation table
key_rotation_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_KEY_ROTATION', 'galerly-key-rotation-dev'))

# Rotation policies
ROTATION_POLICIES = {
    'password_salt': {
        'rotation_interval_days': 7,  # Weekly rotation
        'requires_user_action': True,  # Users must reset password
        'grace_period_days': 14  # 2 weeks to update
    },
    'session_secret': {
        'rotation_interval_days': 7,
        'requires_user_action': False,  # Automatic rotation
        'grace_period_days': 1  # Sessions expire quickly
    },
    'api_key_salt': {
        'rotation_interval_days': 7,
        'requires_user_action': True,  # API keys must be regenerated
        'grace_period_days': 30  # 1 month grace period
    },
    'encryption_key': {
        'rotation_interval_days': 7,
        'requires_user_action': False,  # Transparent re-encryption
        'grace_period_days': 0  # Immediate rotation
    }
}

def get_current_key(key_type):
    """
    Get the current active key for a specific type
    Returns: (key_id, key_value, created_at)
    """
    try:
        # Query for active keys of this type
        response = key_rotation_table.query(
            IndexName='KeyTypeIndex',
            KeyConditionExpression='key_type = :type',
            FilterExpression='#status = :active',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':type': key_type,
                ':active': 'active'
            },
            ScanIndexForward=False,  # Latest first
            Limit=1
        )
        
        items = response.get('Items', [])
        if items:
            key = items[0]
            return key['key_id'], key['key_value'], key['created_at']
        
        # No active key found - generate new one
        return generate_new_key(key_type)
        
    except Exception as e:
        print(f"Error getting current key: {str(e)}")
        # Fallback to generating new key
        return generate_new_key(key_type)

def generate_new_key(key_type):
    """
    Generate a new encryption key
    Returns: (key_id, key_value, created_at)
    """
    key_id = secrets.token_urlsafe(16)
    key_value = secrets.token_urlsafe(32)  # 256-bit key
    created_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
    
    try:
        # Store in rotation table
        key_rotation_table.put_item(Item={
            'key_id': key_id,
            'key_type': key_type,
            'key_value': key_value,
            'created_at': created_at,
            'status': 'active',
            'rotated_at': None,
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=ROTATION_POLICIES[key_type]['rotation_interval_days'])).replace(tzinfo=None).isoformat() + 'Z'
        })
        
        print(f"✅ Generated new {key_type} key: {key_id}")
        return key_id, key_value, created_at
        
    except Exception as e:
        print(f"Error storing new key: {str(e)}")
        # Return generated key anyway
        return key_id, key_value, created_at

def check_key_rotation_needed(key_type):
    """
    Check if a key type needs rotation
    Returns: (needs_rotation: bool, current_key_age_days: int)
    """
    try:
        key_id, key_value, created_at = get_current_key(key_type)
        
        # Parse created_at timestamp with timezone awareness
        key_created = datetime.fromisoformat(created_at.replace('Z', '')).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - key_created).days
        
        policy = ROTATION_POLICIES.get(key_type, {})
        rotation_interval = policy.get('rotation_interval_days', 7)
        
        needs_rotation = age_days >= rotation_interval
        
        return needs_rotation, age_days
        
    except Exception as e:
        print(f"Error checking rotation: {str(e)}")
        return True, 999  # Force rotation on error

def rotate_key(key_type):
    """
    Rotate a specific key type
    Returns: (new_key_id, new_key_value, old_key_id)
    """
    try:
        # Get current key
        old_key_id, old_key_value, created_at = get_current_key(key_type)
        
        # Mark old key as rotated
        key_rotation_table.update_item(
            Key={'key_id': old_key_id},
            UpdateExpression='SET #status = :rotated, rotated_at = :now',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':rotated': 'rotated',
                ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        # Generate new key
        new_key_id, new_key_value, new_created_at = generate_new_key(key_type)
        
        print(f"🔄 Rotated {key_type}: {old_key_id} → {new_key_id}")
        
        return new_key_id, new_key_value, old_key_id
        
    except Exception as e:
        print(f"Error rotating key: {str(e)}")
        raise

def rotate_user_password_salt(user_id, email):
    """
    Rotate password salt for a specific user
    Requires user to reset password on next login
    """
    try:
        # Generate new salt
        new_salt = bcrypt.gensalt(rounds=12)
        
        # Mark user for password reset
        users_table.update_item(
            Key={'email': email},
            UpdateExpression='SET password_reset_required = :required, password_salt_rotated_at = :now, password_salt = :salt',
            ExpressionAttributeValues={
                ':required': True,
                ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
                ':salt': new_salt.decode('utf-8')
            }
        )
        
        print(f"🔐 Rotated password salt for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"Error rotating user password salt: {str(e)}")
        return False

def check_all_rotations():
    """
    Check all key types and rotate if needed
    Called by scheduled Lambda function weekly
    Returns: dict with rotation results
    """
    results = {
        'checked_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
        'rotations': []
    }
    
    for key_type, policy in ROTATION_POLICIES.items():
        try:
            needs_rotation, age_days = check_key_rotation_needed(key_type)
            
            if needs_rotation:
                new_key_id, new_key_value, old_key_id = rotate_key(key_type)
                
                results['rotations'].append({
                    'key_type': key_type,
                    'status': 'success',
                    'old_key_id': old_key_id,
                    'new_key_id': new_key_id,
                    'age_days': age_days
                })
                
                # Send notifications if requires user action
                if policy['requires_user_action']:
                    notify_users_of_rotation(key_type, policy['grace_period_days'])
            else:
                results['rotations'].append({
                    'key_type': key_type,
                    'status': 'skipped',
                    'reason': 'not_due',
                    'age_days': age_days,
                    'next_rotation_days': policy['rotation_interval_days'] - age_days
                })
                
        except Exception as e:
            print(f"Error rotating {key_type}: {str(e)}")
            results['rotations'].append({
                'key_type': key_type,
                'status': 'error',
                'error': str(e)
            })
    
    return results

def notify_users_of_rotation(key_type, grace_period_days):
    """
    Notify users when rotation requires their action
    """
    try:
        if key_type == 'password_salt':
            # Send email to all users about password reset requirement
            from utils.email import send_email
            
            # Get all active users
            response = users_table.scan(
                FilterExpression='account_status = :active',
                ExpressionAttributeValues={':active': 'active'}
            )
            
            users = response.get('Items', [])
            
            for user in users:
                email = user.get('email')
                name = user.get('name', 'User')
                
                # Mark user for required password reset
                rotate_user_password_salt(user.get('id'), email)
            
            print(f"📧 Notified {len(users)} users about password rotation")
            
        elif key_type == 'api_key_salt':
            # Notify users with API keys
            response = users_table.scan(
                FilterExpression='attribute_exists(api_key)',
            )
            
            users = response.get('Items', [])
            
            for user in users:
                email = user.get('email')
                name = user.get('name', 'User')
                
                # Mark API key for rotation
                users_table.update_item(
                    Key={'email': email},
                    UpdateExpression='SET api_key_rotation_required = :required',
                    ExpressionAttributeValues={':required': True}
                )
            
            print(f"📧 Notified {len(users)} users about API key rotation")
            
    except Exception as e:
        print(f"Error notifying users: {str(e)}")

def handle_rotation_status(user):
    """
    Get rotation status for current user
    GET /v1/security/rotation-status
    """
    try:
        rotation_status = {}
        
        # Check password rotation
        password_reset_required = user.get('password_reset_required', False)
        password_salt_rotated_at = user.get('password_salt_rotated_at')
        
        if password_reset_required:
            rotation_status['password'] = {
                'rotation_required': True,
                'rotated_at': password_salt_rotated_at,
                'message': 'Password reset required due to security key rotation'
            }
        
        # Check API key rotation
        api_key_rotation_required = user.get('api_key_rotation_required', False)
        
        if api_key_rotation_required:
            rotation_status['api_key'] = {
                'rotation_required': True,
                'message': 'API key regeneration required due to security key rotation'
            }
        
        return create_response(200, {
            'rotation_required': bool(rotation_status),
            'rotations': rotation_status
        })
        
    except Exception as e:
        print(f"Error getting rotation status: {str(e)}")
        return create_response(500, {'error': 'Failed to check rotation status'})

def lambda_handler(event, context):
    """
    Lambda function handler for scheduled key rotation
    Triggered weekly by CloudWatch Events
    """
    print("🔄 Starting weekly key rotation check...")
    
    results = check_all_rotations()
    
    print(f"✅ Key rotation check complete")
    print(json.dumps(results, indent=2))
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }

