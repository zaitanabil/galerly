"""
Subscription management and plan enforcement
"""
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table, dynamodb
from utils.response import create_response
from handlers.billing_handler import PLANS

subscriptions_table = dynamodb.Table('galerly-subscriptions')


def get_user_plan_limits(user):
    """Get plan limits for user - fetches plan from DynamoDB to ensure latest status"""
    # Get user's current plan directly from DynamoDB (not from session cache)
    # This ensures we have the latest subscription status after webhook updates
    try:
        user_email = user.get('email')
        if user_email:
            user_response = users_table.get_item(Key={'email': user_email})
            if 'Item' in user_response:
                db_user = user_response['Item']
                # Use 'plan' field (new), fallback to 'subscription' (legacy)
                plan_id = db_user.get('plan', db_user.get('subscription', 'free'))
                print(f"📋 get_user_plan_limits: User {user_email} plan from DB: {plan_id}")
            else:
                plan_id = user.get('plan', user.get('subscription', 'free'))
                print(f"⚠️  User not found in DB, using session plan: {plan_id}")
        else:
            plan_id = user.get('plan', user.get('subscription', 'free'))
            print(f"⚠️  No email in user object, using session plan: {plan_id}")
    except Exception as e:
        print(f"⚠️  Error fetching user from DB: {str(e)}, using session plan")
        plan_id = user.get('plan', user.get('subscription', 'free'))
    
    plan = PLANS.get(plan_id, PLANS['free'])
    
    return {
        'plan': plan_id,
        'plan_name': plan['name'],
        'galleries_per_month': plan['galleries_per_month'],
        'storage_gb': plan['storage_gb'],
        'features': plan['features']
    }


def check_gallery_limit(user):
    """Check if user can create more galleries this month"""
    # Get plan limits (which fetches from DB)
    plan_limits = get_user_plan_limits(user)
    plan_id = plan_limits['plan']
    plan = PLANS.get(plan_id, PLANS['free'])
    
    # Check current month galleries
    try:
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        
        galleries = response.get('Items', [])
        current_month = datetime.utcnow().strftime('%Y-%m')
        
        # Count galleries created this month
        monthly_count = sum(
            1 for g in galleries 
            if g.get('created_at', '').startswith(current_month)
        )
        
        limit = plan['galleries_per_month']
        
        # Unlimited plans
        if limit == -1:
            return {
                'allowed': True,
                'remaining': -1,
                'used': monthly_count,
                'limit': -1
            }
        
        remaining = limit - monthly_count
        
        return {
            'allowed': remaining > 0,
            'remaining': max(0, remaining),
            'used': monthly_count,
            'limit': limit
        }
    except Exception as e:
        print(f"Error checking gallery limit: {str(e)}")
        limit = plan['galleries_per_month']
        return {
            'allowed': True,
            'remaining': limit if limit != -1 else -1,
            'used': 0,
            'limit': limit
        }


def check_storage_limit(user):
    """Check storage usage against plan limit"""
    # Get plan limits (which fetches from DB)
    plan_limits = get_user_plan_limits(user)
    plan_id = plan_limits['plan']
    plan = PLANS.get(plan_id, PLANS['free'])
    
    try:
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        
        galleries = response.get('Items', [])
        total_storage_mb = sum(float(g.get('storage_used', 0)) for g in galleries)
        total_storage_gb = total_storage_mb / 1024
        
        limit_gb = plan['storage_gb']
        usage_percent = (total_storage_gb / limit_gb * 100) if limit_gb > 0 else 0
        
        return {
            'used_gb': round(total_storage_gb, 2),
            'limit_gb': limit_gb,
            'usage_percent': round(usage_percent, 2),
            'remaining_gb': max(0, limit_gb - total_storage_gb) if limit_gb > 0 else -1
        }
    except Exception as e:
        print(f"Error checking storage limit: {str(e)}")
        return {
            'used_gb': 0,
            'limit_gb': plan['storage_gb'],
            'usage_percent': 0,
            'remaining_gb': plan['storage_gb']
        }


def handle_get_usage(user):
    """Get current usage and limits"""
    gallery_limit = check_gallery_limit(user)
    storage_limit = check_storage_limit(user)
    plan_limits = get_user_plan_limits(user)
    
    return create_response(200, {
        'plan': plan_limits,
        'gallery_limit': gallery_limit,
        'storage_limit': storage_limit
    })


def enforce_gallery_limit(user):
    """Enforce gallery creation limit - returns (allowed, error_message)"""
    gallery_limit = check_gallery_limit(user)
    
    if not gallery_limit['allowed']:
        plan_limits = get_user_plan_limits(user)
        return False, f"You've reached your monthly gallery limit ({plan_limits['galleries_per_month']}). Upgrade to create unlimited galleries."
    
    return True, None


def enforce_storage_limit(user, additional_mb):
    """Enforce storage limit - returns (allowed, error_message)"""
    storage_limit = check_storage_limit(user)
    
    if storage_limit['limit_gb'] == -1:  # Unlimited
        return True, None
    
    additional_gb = additional_mb / 1024
    if storage_limit['remaining_gb'] < additional_gb:
        plan_limits = get_user_plan_limits(user)
        return False, f"Insufficient storage. You have {storage_limit['remaining_gb']:.2f} GB remaining. Upgrade to {plan_limits['plan_name']} for more storage."
    
    return True, None

