"""
Subscription management and plan enforcement
"""
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table, dynamodb, features_table, user_features_table
from utils.response import create_response
from handlers.billing_handler import PLANS

subscriptions_table = dynamodb.Table('galerly-subscriptions')


def get_user_features(user):
    """
    Get consolidated features for a user.
    Merges plan defaults with specific overrides from user_features table.
    """
    try:
        user_id = user.get('id')
        
        # 1. Get user plan from DB
        user_response = {}
        if user.get('email'):
            try:
                user_response = users_table.get_item(Key={'email': user['email']})
            except Exception as e:
                print(f"Error fetching user by email: {e}")
        
        if 'Item' not in user_response and user_id:
            # Fallback to querying by ID using GSI
            try:
                resp = users_table.query(
                    IndexName='UserIdIndex', 
                    KeyConditionExpression=Key('id').eq(user_id)
                )
                if resp.get('Items'):
                    user_response = {'Item': resp['Items'][0]}
            except Exception as e:
                print(f"Error fetching user by ID: {e}")
        
        # 2. Get manual feature overrides/assignments
        user_features_items = []
        if user_id:
            try:
                response = user_features_table.query(
                    KeyConditionExpression=Key('user_id').eq(user_id)
                )
                user_features_items = response.get('Items', [])
            except Exception as e:
                print(f"Error fetching feature overrides: {e}")
        
        # 3. Get all feature definitions to map feature_id -> values
        
        # Fetch user details to get plan
        user_plan_id = 'free'
        if 'Item' in user_response:
            user_plan_id = user_response['Item'].get('plan') or user_response['Item'].get('subscription') or 'free'
        else:
            # Fallback to what's in the user object if DB fetch failed
            user_plan_id = user.get('plan') or user.get('subscription') or 'free'
        
        # Normalize plan
        normalized_plan_id = user_plan_id
        plan_def = PLANS.get(normalized_plan_id, PLANS.get('free'))
        
        # Start with defaults from the plan definition
        features = {
            'storage_gb': plan_def.get('storage_gb', 2),
            'galleries_per_month': plan_def.get('galleries_per_month', 3),
            'video_minutes': 0, 
            'video_quality': 'hd', # hd or 4k
            'remove_branding': False,
            'custom_domain': False,
            'raw_support': False,
            'analytics_level': 'basic', # basic, advanced, pro
            'email_templates': False,
            'client_favorites': False,
            'seo_tools': False,
            'raw_vault': False,
            'client_invoicing': False,
            'scheduler': False,
            'e_signatures': False,
            'watermarking': False
        }
        
        # Collect all feature IDs: from plan definition + manual overrides
        feature_ids = set(plan_def.get('feature_ids', []))
        
        # Add overrides
        for item in user_features_items:
            fid = item.get('feature_id')
            if fid:
                feature_ids.add(fid)
                
        # Resolve feature IDs to limits
        # We process them in order of "power" to ensure upgrades override defaults
        
        # Storage Resolution
        if 'storage_unlimited' in feature_ids:
            features['storage_gb'] = -1
        elif 'storage_1tb' in feature_ids or 'storage_1000gb' in feature_ids:
            features['storage_gb'] = 1000
        elif 'storage_200gb' in feature_ids:
            features['storage_gb'] = 200
        elif 'storage_100gb' in feature_ids:
            features['storage_gb'] = 100
        elif 'storage_50gb' in feature_ids:
            features['storage_gb'] = 50
        elif 'storage_10gb' in feature_ids:
            features['storage_gb'] = 10
        elif 'storage_3gb' in feature_ids:
            features['storage_gb'] = 3
        elif 'storage_1gb' in feature_ids:
            features['storage_gb'] = 1
            
        # Gallery Limits
        if 'unlimited_galleries' in feature_ids:
            features['galleries_per_month'] = -1
            
        # Video Support
        if 'video_4k_unlimited' in feature_ids:
            features['video_minutes'] = -1
            features['video_quality'] = '4k'
        elif 'video_10hr_4k' in feature_ids:
            features['video_minutes'] = 600
            features['video_quality'] = '4k'
        elif 'video_4hr_4k' in feature_ids:
            features['video_minutes'] = 240
            features['video_quality'] = '4k'
        elif 'video_2hr_4k' in feature_ids:
            features['video_minutes'] = 120
            features['video_quality'] = '4k'
        elif 'video_1hr_hd' in feature_ids or 'video_60min_hd' in feature_ids:
            features['video_minutes'] = 60
            features['video_quality'] = 'hd'
        elif 'video_60min_4k' in feature_ids:
            features['video_minutes'] = 60
            features['video_quality'] = '4k'
        elif 'video_30min_4k' in feature_ids:
            features['video_minutes'] = 30
            features['video_quality'] = '4k'
        elif 'video_30min_hd' in feature_ids:
            features['video_minutes'] = 30
            features['video_quality'] = 'hd'
        elif 'video_15min_hd' in feature_ids:
            features['video_minutes'] = 15
            features['video_quality'] = 'hd'
        elif 'video_10min_hd' in feature_ids:
            features['video_minutes'] = 10
            features['video_quality'] = 'hd'
        elif 'video_none' in feature_ids:
            features['video_minutes'] = 0
            features['video_quality'] = 'none'
            
        # Branding & Domain
        if 'no_branding' in feature_ids or 'white_label' in feature_ids:
            features['remove_branding'] = True
        elif 'branding_on' in feature_ids:
            features['remove_branding'] = False
            
        if 'watermarking' in feature_ids:
            features['watermarking'] = True
            
        if 'custom_domain' in feature_ids:
            features['custom_domain'] = True
            
        # Advanced Features
        if 'client_invoicing' in feature_ids or 'smart_invoicing' in feature_ids:
            features['client_invoicing'] = True
            
        if 'scheduler' in feature_ids:
            features['scheduler'] = True
            
        if 'e_signatures' in feature_ids:
            features['e_signatures'] = True
            
        # Client Favorites (Starter+)
        if 'client_favorites' in feature_ids or 'client_proofing' in feature_ids:
            features['client_favorites'] = True

        if 'raw_support' in feature_ids or 'raw_vault' in feature_ids:
            features['raw_support'] = True
            
        if 'raw_vault' in feature_ids:
            features['raw_vault'] = True

        if 'email_templates' in feature_ids:
            features['email_templates'] = True
            
        # SEO Tools (Pro & Ultimate)
        if 'seo_tools' in feature_ids:
            features['seo_tools'] = True
            
        # Analytics Level
        if 'analytics_pro' in feature_ids or 'visitor_insights' in feature_ids:
            features['analytics_level'] = 'pro'
        elif 'analytics_advanced' in feature_ids:
            features['analytics_level'] = 'advanced'
            
        return features, normalized_plan_id, plan_def['name']

    except Exception as e:
        print(f"Error fetching user features: {e}")
        # Fallback to defaults (Free plan limits)
        return {
            'storage_gb': 2,
            'galleries_per_month': 3
        }, 'free', 'Free'


def get_user_plan_limits(user):
    """Get plan limits for user - fetches plan from DynamoDB to ensure latest status"""
    # Get user's current plan directly from DynamoDB (not from session cache)
    try:
        # Fetch consolidated features using new logic
        features, plan_id, plan_name = get_user_features(user)
        
        return {
            'plan': plan_id,
            'plan_name': plan_name,
            'galleries_per_month': features['galleries_per_month'],
            'storage_gb': features['storage_gb'],
            'features': features # Include raw features dict if needed
        }
    except Exception as e:
        print(f"⚠️  Error in get_user_plan_limits: {str(e)}")
        # Fallback
    return {
            'plan': 'free',
            'plan_name': 'Free',
                'galleries_per_month': 3,
                'storage_gb': 2,
            'features': {}
    }



def check_gallery_limit(user):
    """Check if user can create more galleries this month"""
    # Get plan limits (which fetches from DB)
    plan_limits = get_user_plan_limits(user)
    plan_id = plan_limits['plan']
    
    # Ensure we have a valid plan
    if not plan_id:
        plan_id = 'free'
    
    plan = PLANS.get(plan_id)
    if not plan:
        plan = PLANS.get('free')
    
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
    
    # Ensure we have a valid plan
    if not plan_id:
        plan_id = 'free'
    
    plan = PLANS.get(plan_id)
    if not plan:
        plan = PLANS.get('free')
    
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
