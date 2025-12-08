"""
Real-time Viewer Tracking Handler
Tracks active viewers on galleries and portfolio pages
Provides real-time location data for 3D globe visualization
"""
import uuid
import time
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import analytics_table, galleries_table
from utils.response import create_response
from utils.geolocation import get_location_from_ip, get_ip_from_request


# In-memory store for active viewers (in production, use Redis with TTL)
# Format: {viewer_id: {user_id, gallery_id, location, last_seen, ...}}
active_viewers = {}

# Viewer timeout in seconds (consider inactive after this time)
VIEWER_TIMEOUT = 60


def cleanup_inactive_viewers():
    """Remove viewers who haven't sent heartbeat in VIEWER_TIMEOUT seconds"""
    current_time = time.time()
    inactive = [
        viewer_id for viewer_id, viewer in active_viewers.items()
        if current_time - viewer.get('last_seen', 0) > VIEWER_TIMEOUT
    ]
    for viewer_id in inactive:
        del active_viewers[viewer_id]
    return len(inactive)


def handle_track_viewer_heartbeat(event):
    """
    Track viewer presence on gallery/portfolio
    Called every 30 seconds from client to maintain active status
    
    Body: {
        'viewer_id': str (optional, auto-generated if not provided),
        'gallery_id': str (optional),
        'page_type': 'gallery' | 'portfolio' | 'client_gallery',
        'gallery_name': str (optional)
    }
    """
    try:
        body = event.get('body', {})
        
        # Get or create viewer ID
        viewer_id = body.get('viewer_id') or str(uuid.uuid4())
        
        # Get client IP and location
        client_ip = get_ip_from_request(event)
        location = get_location_from_ip(client_ip)
        
        # Get user if authenticated (photographer viewing their own gallery shouldn't count)
        from api import get_user_from_token
        user = get_user_from_token(event)
        
        gallery_id = body.get('gallery_id')
        page_type = body.get('page_type', 'gallery')
        gallery_name = body.get('gallery_name', 'Unknown')
        
        # If viewing a gallery, check if they're the owner
        is_owner = False
        gallery_owner_id = None
        if gallery_id and user:
            try:
                gallery_response = galleries_table.get_item(Key={
                    'user_id': user['id'],
                    'id': gallery_id
                })
                if 'Item' in gallery_response:
                    is_owner = True
                    gallery_owner_id = user['id']
            except:
                pass
        
        # If not owner check but we have a gallery_id, try to find the owner
        if gallery_id and not gallery_owner_id:
            try:
                # Scan for gallery to find owner (not efficient, but needed for tracking)
                scan_response = galleries_table.scan(
                    FilterExpression=Attr('id').eq(gallery_id),
                    Limit=1
                )
                if scan_response.get('Items'):
                    gallery_owner_id = scan_response['Items'][0].get('user_id')
            except:
                pass
        
        # Don't track the owner viewing their own gallery
        if is_owner:
            return create_response(200, {
                'viewer_id': viewer_id,
                'tracked': False,
                'reason': 'owner_view'
            })
        
        # Update active viewer
        current_time = time.time()
        active_viewers[viewer_id] = {
            'viewer_id': viewer_id,
            'gallery_id': gallery_id,
            'gallery_name': gallery_name,
            'gallery_owner_id': gallery_owner_id,
            'page_type': page_type,
            'location': {
                'city': location.get('city'),
                'region': location.get('region'),
                'country': location.get('country'),
                'country_code': location.get('country_code'),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude')
            },
            'first_seen': active_viewers.get(viewer_id, {}).get('first_seen', current_time),
            'last_seen': current_time,
            'is_authenticated': user is not None
        }
        
        # Clean up inactive viewers periodically
        cleanup_inactive_viewers()
        
        return create_response(200, {
            'viewer_id': viewer_id,
            'tracked': True,
            'location': location.get('city'),
            'active_viewers': len(active_viewers)
        })
        
    except Exception as e:
        print(f"Error tracking viewer heartbeat: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to track viewer'})


def handle_get_active_viewers(user):
    """
    Get all active viewers for authenticated photographer
    Returns only viewers on galleries owned by this user
    
    Returns: {
        'viewers': [
            {
                'viewer_id': str,
                'gallery_id': str,
                'gallery_name': str,
                'location': {city, region, country, lat, lng},
                'duration': int (seconds),
                'page_type': str
            }
        ],
        'total_active': int,
        'by_country': {country_code: count},
        'by_gallery': {gallery_id: count}
    }
    """
    try:
        # Clean up inactive viewers first
        cleanup_inactive_viewers()
        
        # Filter viewers for this user's galleries
        user_viewers = [
            viewer for viewer in active_viewers.values()
            if viewer.get('gallery_owner_id') == user['id']
        ]
        
        # Calculate stats
        by_country = {}
        by_gallery = {}
        current_time = time.time()
        
        viewers_list = []
        for viewer in user_viewers:
            country_code = viewer.get('location', {}).get('country_code', 'XX')
            gallery_id = viewer.get('gallery_id', 'unknown')
            
            by_country[country_code] = by_country.get(country_code, 0) + 1
            by_gallery[gallery_id] = by_gallery.get(gallery_id, 0) + 1
            
            viewers_list.append({
                'viewer_id': viewer['viewer_id'],
                'gallery_id': viewer.get('gallery_id'),
                'gallery_name': viewer.get('gallery_name'),
                'page_type': viewer.get('page_type'),
                'location': viewer.get('location'),
                'duration': int(current_time - viewer.get('first_seen', current_time))
            })
        
        return create_response(200, {
            'viewers': viewers_list,
            'total_active': len(viewers_list),
            'by_country': by_country,
            'by_gallery': by_gallery,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        print(f"Error getting active viewers: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get active viewers'})


def handle_viewer_disconnect(event):
    """
    Remove viewer from active list when they close the page
    
    Body: {
        'viewer_id': str
    }
    """
    try:
        body = event.get('body', {})
        viewer_id = body.get('viewer_id')
        
        if viewer_id and viewer_id in active_viewers:
            del active_viewers[viewer_id]
        
        return create_response(200, {'success': True})
        
    except Exception as e:
        print(f"Error handling viewer disconnect: {str(e)}")
        return create_response(200, {'success': True})  # Don't fail on disconnect
