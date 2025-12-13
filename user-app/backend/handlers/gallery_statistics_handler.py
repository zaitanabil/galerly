"""
Gallery Statistics Dashboard
Comprehensive statistics and insights for individual galleries
"""
import os
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key, Attr
from utils.config import galleries_table, photos_table, gallery_views_table, photo_views_table
from utils.response import create_response
from utils.plan_enforcement import require_role
from decimal import Decimal


def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@require_role('photographer')
def handle_get_gallery_statistics(user, gallery_id):
    """
    Get comprehensive statistics for a specific gallery
    
    Returns:
    - View counts and trends
    - Photo performance
    - Client engagement
    - Geographic data
    - Time-based analytics
    """
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={'id': gallery_id})
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Item']
        if gallery.get('user_id') != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Time ranges for analysis
        now = datetime.now(timezone.utc)
        last_7_days = (now - timedelta(days=7)).isoformat()
        last_30_days = (now - timedelta(days=30)).isoformat()
        last_90_days = (now - timedelta(days=90)).isoformat()
        
        # Get gallery views
        views_response = gallery_views_table.query(
            IndexName='GalleryViewsByGalleryIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        views = views_response.get('Items', [])
        
        # Calculate view statistics
        total_views = len(views)
        unique_visitors = len(set(v.get('visitor_id', '') for v in views))
        
        views_last_7 = len([v for v in views if v.get('viewed_at', '') >= last_7_days])
        views_last_30 = len([v for v in views if v.get('viewed_at', '') >= last_30_days])
        
        # Geographic distribution
        geo_data = {}
        for view in views:
            country = view.get('country', 'Unknown')
            geo_data[country] = geo_data.get(country, 0) + 1
        
        top_countries = sorted(geo_data.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Device distribution
        device_data = {'desktop': 0, 'mobile': 0, 'tablet': 0, 'unknown': 0}
        for view in views:
            device = view.get('device_type', 'unknown')
            device_data[device] = device_data.get(device, 0) + 1
        
        # Get photos in gallery
        photos_response = photos_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        photos = photos_response.get('Items', [])
        total_photos = len(photos)
        
        # Photo performance
        photo_stats = []
        for photo in photos:
            photo_views_response = photo_views_table.query(
                IndexName='PhotoViewsByPhotoIndex',
                KeyConditionExpression=Key('photo_id').eq(photo['id'])
            )
            photo_views = photo_views_response.get('Items', [])
            
            photo_stats.append({
                'photo_id': photo['id'],
                'filename': photo.get('original_filename', 'Unknown'),
                'views': len(photo_views),
                'favorites': photo.get('favorite_count', 0),
                'downloads': photo.get('download_count', 0),
                'thumbnail_url': photo.get('thumbnail_url', '')
            })
        
        # Sort by views
        photo_stats.sort(key=lambda x: x['views'], reverse=True)
        top_photos = photo_stats[:10]
        
        # Engagement metrics
        total_favorites = sum(p.get('favorite_count', 0) for p in photos)
        total_downloads = sum(p.get('download_count', 0) for p in photos)
        
        # Calculate engagement rate
        engagement_rate = 0
        if total_views > 0:
            engaged_views = len([v for v in views if v.get('duration_seconds', 0) > 30])
            engagement_rate = (engaged_views / total_views) * 100
        
        # Average time spent
        total_duration = sum(v.get('duration_seconds', 0) for v in views)
        avg_time_spent = total_duration / total_views if total_views > 0 else 0
        
        # Daily views trend (last 30 days)
        daily_views = {}
        for i in range(30):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_views[date] = 0
        
        for view in views:
            view_date = view.get('viewed_at', '')[:10]
            if view_date in daily_views:
                daily_views[view_date] += 1
        
        daily_views_list = [{'date': k, 'views': v} for k, v in sorted(daily_views.items())]
        
        # Referrer sources
        referrer_data = {}
        for view in views:
            referrer = view.get('referrer', 'Direct')
            if not referrer or referrer == 'None':
                referrer = 'Direct'
            elif 'google' in referrer.lower():
                referrer = 'Google'
            elif 'facebook' in referrer.lower():
                referrer = 'Facebook'
            elif 'instagram' in referrer.lower():
                referrer = 'Instagram'
            else:
                referrer = 'Other'
            
            referrer_data[referrer] = referrer_data.get(referrer, 0) + 1
        
        top_referrers = sorted(referrer_data.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Gallery settings impact
        is_password_protected = bool(gallery.get('password'))
        is_download_enabled = gallery.get('allow_downloads', False)
        has_expiry = bool(gallery.get('expiry_date'))
        
        # Client activity summary
        client_actions = {
            'total_favorites': total_favorites,
            'total_downloads': total_downloads,
            'photos_with_favorites': len([p for p in photos if p.get('favorite_count', 0) > 0]),
            'photos_with_downloads': len([p for p in photos if p.get('download_count', 0) > 0])
        }
        
        # Performance score (0-100)
        score = 0
        if total_views > 0:
            score += min(30, total_views / 10)  # Up to 30 points for views
        if unique_visitors > 0:
            score += min(20, unique_visitors / 5)  # Up to 20 points for unique visitors
        if engagement_rate > 0:
            score += min(25, engagement_rate / 2)  # Up to 25 points for engagement
        if total_favorites > 0:
            score += min(15, total_favorites / 5)  # Up to 15 points for favorites
        if total_downloads > 0:
            score += min(10, total_downloads / 5)  # Up to 10 points for downloads
        
        score = min(100, int(score))
        
        statistics = {
            'gallery_id': gallery_id,
            'gallery_name': gallery.get('name', 'Untitled'),
            'created_at': gallery.get('created_at', ''),
            
            # Overview
            'overview': {
                'total_views': total_views,
                'unique_visitors': unique_visitors,
                'total_photos': total_photos,
                'performance_score': score,
                'engagement_rate': round(engagement_rate, 2),
                'avg_time_spent_seconds': int(avg_time_spent)
            },
            
            # Trends
            'trends': {
                'views_last_7_days': views_last_7,
                'views_last_30_days': views_last_30,
                'daily_views': daily_views_list
            },
            
            # Photo performance
            'top_photos': top_photos,
            
            # Client engagement
            'client_activity': client_actions,
            
            # Geographic data
            'geography': {
                'top_countries': [{'country': c, 'views': v} for c, v in top_countries]
            },
            
            # Device breakdown
            'devices': device_data,
            
            # Traffic sources
            'referrers': [{'source': r, 'visits': v} for r, v in top_referrers],
            
            # Gallery settings
            'settings_impact': {
                'password_protected': is_password_protected,
                'downloads_enabled': is_download_enabled,
                'has_expiry': has_expiry,
                'privacy': gallery.get('privacy', 'private')
            },
            
            # Recommendations
            'recommendations': generate_gallery_recommendations(
                total_views, engagement_rate, total_favorites, 
                total_downloads, is_password_protected, gallery.get('privacy')
            )
        }
        
        # Convert Decimal objects
        statistics = convert_decimals(statistics)
        
        return create_response(200, statistics)
        
    except Exception as e:
        print(f"Error getting gallery statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get gallery statistics'})


def generate_gallery_recommendations(views, engagement_rate, favorites, downloads, 
                                     is_password_protected, privacy):
    """Generate actionable recommendations based on gallery performance"""
    
    recommendations = []
    
    if views < 10:
        recommendations.append({
            'type': 'visibility',
            'priority': 'high',
            'title': 'Increase Gallery Visibility',
            'description': 'This gallery has few views. Share it more widely.',
            'actions': [
                'Share on social media',
                'Send direct link to clients',
                'Add to your portfolio homepage'
            ]
        })
    
    if engagement_rate < 30:
        recommendations.append({
            'type': 'engagement',
            'priority': 'medium',
            'title': 'Improve Visitor Engagement',
            'description': 'Visitors are not spending much time viewing photos.',
            'actions': [
                'Add compelling gallery description',
                'Use eye-catching cover photo',
                'Ensure photos are high quality'
            ]
        })
    
    if favorites == 0 and views > 5:
        recommendations.append({
            'type': 'interaction',
            'priority': 'medium',
            'title': 'Encourage Photo Selection',
            'description': 'Visitors are not favoriting photos.',
            'actions': [
                'Remind clients to select favorites',
                'Make favorite button more visible',
                'Send selection reminder email'
            ]
        })
    
    if privacy == 'private' and views < 3:
        recommendations.append({
            'type': 'settings',
            'priority': 'low',
            'title': 'Consider Gallery Privacy',
            'description': 'Private galleries limit discoverability.',
            'actions': [
                'Make gallery public if appropriate',
                'Share gallery link with more people',
                'Use password protection instead'
            ]
        })
    
    if downloads == 0 and favorites > 0:
        recommendations.append({
            'type': 'conversion',
            'priority': 'high',
            'title': 'Convert Favorites to Downloads',
            'description': 'Clients are favoriting but not downloading.',
            'actions': [
                'Send download instructions',
                'Verify downloads are enabled',
                'Follow up with clients'
            ]
        })
    
    if not recommendations:
        recommendations.append({
            'type': 'success',
            'priority': 'info',
            'title': 'Gallery Performing Well',
            'description': 'Your gallery metrics look good!',
            'actions': [
                'Keep sharing quality content',
                'Monitor engagement trends',
                'Request client feedback'
            ]
        })
    
    return recommendations

