"""
Dashboard and statistics handlers
Dashboard stats filtered by plan tier
"""
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table
from utils.response import create_response
from handlers.subscription_handler import get_user_features

def handle_dashboard_stats(user):
    """Get dashboard statistics for THIS USER ONLY - filtered by plan"""
    try:
        # Check user's analytics level for filtering
        features, plan_id, _ = get_user_features(user)
        analytics_level = features.get('analytics_level', 'basic')
        
        # Determine data retention based on plan
        max_retention_days = {
            'basic': 7,      # Free/Starter
            'advanced': 30,  # Plus
            'pro': 90        # Pro/Ultimate
        }.get(analytics_level, 7)
        
        # Query only this user's galleries
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        user_galleries = response.get('Items', [])
        
        total_photos = sum(int(g.get('photo_count', 0)) for g in user_galleries)
        # Use atomic counters from galleries for totals (more accurate than summing logs)
        total_views = sum(int(g.get('view_count', 0)) for g in user_galleries)
        total_downloads = sum(int(g.get('download_count', 0)) for g in user_galleries)
        
        # Calculate actual storage from galleries (in MB)
        total_storage_mb = sum(float(g.get('storage_used', 0)) for g in user_galleries)
        total_storage_gb = round(total_storage_mb / 1024, 2)  # Convert MB to GB
        
        # Get user's subscription plan and limits using the new feature system
        from handlers.subscription_handler import get_user_plan_limits
        plan_limits = get_user_plan_limits(user)
        
        user_subscription = plan_limits['plan']
        storage_limit_gb = plan_limits['storage_gb']
        
        # Calculate storage stats
        if storage_limit_gb == -1:
            storage_available_gb = 999999 # Unlimited
            storage_percent = 0
        else:
            storage_available_gb = max(0, storage_limit_gb - total_storage_gb)
            storage_percent = round((total_storage_gb / storage_limit_gb * 100), 1) if storage_limit_gb > 0 else 0
        
        # Recent activity
        recent_galleries = sorted(user_galleries, key=lambda x: x.get('updated_at', ''), reverse=True)[:5]
        
        # SELF-HEALING: Check for missing thumbnails in recent galleries
        # This fixes the dashboard preview without needing to open the gallery
        for g in recent_galleries:
            # Fix photo count if needed (simple check if 0 but has photos is too expensive to do perfectly, 
            # but we can rely on list_galleries fixing it eventually if we added logic there, 
            # or just rely on atomic updates for future. 
            # For now, let's fix thumbnails which is the visual bug)
            
            if not g.get('thumbnail_url') and g.get('photo_count', 0) > 0:
                try:
                    # Find a photo to use as thumbnail
                    from utils.config import photos_table
                    p_response = photos_table.query(
                        IndexName='GalleryIdIndex',
                        KeyConditionExpression=Key('gallery_id').eq(g['id']),
                        Limit=1,
                        ProjectionExpression='thumbnail_url, medium_url, #url'
                    )
                    items = p_response.get('Items', [])
                    if items:
                        # Prefer thumbnail, then medium, then original
                        item = items[0]
                        thumb = item.get('thumbnail_url') or item.get('medium_url') or item.get('url')
                        
                        if thumb:
                            print(f"Fixing dashboard thumbnail for gallery {g['id']}")
                            # Update DB
                            galleries_table.update_item(
                                Key={'user_id': user['id'], 'id': g['id']},
                                UpdateExpression="SET thumbnail_url = :t",
                                ExpressionAttributeValues={':t': thumb}
                            )
                            # Update local object for display
                            g['thumbnail_url'] = thumb
                            g['cover_photo'] = thumb # Fallback for frontend
                except Exception as e:
                    print(f"Failed to fix dashboard thumbnail: {e}")

        
        # Get real analytics with plan-appropriate date range
        from handlers.analytics_handler import handle_get_overall_analytics
        
        # Pass date range based on retention
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=max_retention_days)
        
        analytics_response = handle_get_overall_analytics(user, {
            'start_date': start_date.isoformat() + 'Z',
            'end_date': end_date.isoformat() + 'Z'
        })
        analytics_data = analytics_response.get('body') if isinstance(analytics_response, dict) else {}
        if isinstance(analytics_data, str):
            import json
            try:
                analytics_data = json.loads(analytics_data)
            except:
                analytics_data = {}
        
        # Build response based on analytics level
        response_data = {
            'stats': {
                'total_galleries': len(user_galleries),
                'total_photos': total_photos,
                'storage_used_mb': round(total_storage_mb, 2),
                'storage_used_gb': total_storage_gb,
                'storage_limit_gb': storage_limit_gb,
                'storage_available_gb': round(storage_available_gb, 2),
                'storage_percent': storage_percent
            },
            'recent_galleries': recent_galleries,
            'subscription': user_subscription,
            'analytics_level': analytics_level,
            'retention_days': max_retention_days
        }
        
        # Add analytics based on plan level
        if analytics_level == 'basic':
            response_data['stats']['total_views'] = analytics_data.get('total_views', 0)
            response_data['stats']['total_downloads'] = 0
            response_data['message'] = 'Upgrade to Plus for detailed analytics'
        elif analytics_level == 'advanced':
            response_data['stats']['total_views'] = analytics_data.get('total_views', 0)
            response_data['stats']['total_downloads'] = analytics_data.get('total_downloads', 0)
            response_data['analytics'] = analytics_data
            response_data['message'] = 'Upgrade to Pro for extended retention and exports'
        else:  # pro
            response_data['stats']['total_views'] = analytics_data.get('total_views', 0)
            response_data['stats']['total_downloads'] = analytics_data.get('total_downloads', 0) + analytics_data.get('total_bulk_downloads', 0)
            response_data['analytics'] = analytics_data
        
        return create_response(200, response_data)
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
