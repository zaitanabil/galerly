"""
Dashboard and statistics handlers
"""
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table
from utils.response import create_response

# Plan storage limits in GB
PLAN_STORAGE_LIMITS = {
    'free': 5,
    'starter': 5,
    'plus': 50,
    'pro': 200,
    # Legacy names
    'professional': 50,
    'business': 200
}

def handle_dashboard_stats(user):
    """Get dashboard statistics for THIS USER ONLY"""
    try:
        # Query only this user's galleries
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        user_galleries = response.get('Items', [])
        
        total_photos = sum(int(g.get('photo_count', 0)) for g in user_galleries)
        total_views = sum(int(g.get('view_count', 0)) for g in user_galleries)
        
        # Calculate actual storage from galleries (in MB)
        total_storage_mb = sum(float(g.get('storage_used', 0)) for g in user_galleries)
        total_storage_gb = round(total_storage_mb / 1024, 2)  # Convert MB to GB
        
        # Get user's subscription plan
        user_subscription = user.get('subscription', 'starter')
        storage_limit_gb = PLAN_STORAGE_LIMITS.get(user_subscription, 5)
        
        # Calculate storage stats
        storage_available_gb = max(0, storage_limit_gb - total_storage_gb)
        storage_percent = round((total_storage_gb / storage_limit_gb * 100), 1) if storage_limit_gb > 0 else 0
        
        # Recent activity
        recent_galleries = sorted(user_galleries, key=lambda x: x.get('updated_at', ''), reverse=True)[:5]
        
        return create_response(200, {
            'stats': {
                'total_galleries': len(user_galleries),
                'total_photos': total_photos,
                'total_views': total_views,
                'storage_used_mb': round(total_storage_mb, 2),
                'storage_used_gb': total_storage_gb,
                'storage_limit_gb': storage_limit_gb,
                'storage_available_gb': round(storage_available_gb, 2),
                'storage_percent': storage_percent
            },
            'recent_galleries': recent_galleries,
            'subscription': user_subscription
        })
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(200, {
            'stats': {
                'total_galleries': 0,
                'total_photos': 0,
                'total_views': 0,
                'storage_used_mb': 0,
                'storage_used_gb': 0,
                'storage_limit_gb': 5,
                'storage_available_gb': 5,
                'storage_percent': 0
            },
            'recent_galleries': [],
            'subscription': user.get('subscription', 'starter')
        })

