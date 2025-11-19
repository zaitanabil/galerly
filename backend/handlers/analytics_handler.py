"""
Analytics and insights handlers
"""
import uuid
import re
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from utils.config import analytics_table, galleries_table, photos_table
from utils.response import create_response


def track_event(user_id, gallery_id, event_type, metadata=None):
    """Track an analytics event"""
    try:
        event = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'gallery_id': gallery_id,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': metadata or {}
        }
        analytics_table.put_item(Item=event)
        return True
    except Exception as e:
        print(f"Error tracking event: {str(e)}")
        return False


def handle_get_gallery_analytics(user, gallery_id):
    """Get analytics for a specific gallery"""
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        # Get analytics events for this gallery
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        response = analytics_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id) & Key('timestamp').between(
                start_date.isoformat() + 'Z',
                end_date.isoformat() + 'Z'
            )
        )
        
        events = response.get('Items', [])
        
        # Calculate metrics
        views = sum(1 for e in events if e.get('event_type') == 'gallery_view')
        unique_visitors = len(set(e.get('metadata', {}).get('ip', '') for e in events if e.get('event_type') == 'gallery_view'))
        photo_views = sum(1 for e in events if e.get('event_type') == 'photo_view')
        downloads = sum(1 for e in events if e.get('event_type') == 'photo_download')
        
        # Time series data (last 30 days)
        daily_stats = {}
        for event in events:
            date = event['timestamp'][:10]  # YYYY-MM-DD
            if date not in daily_stats:
                daily_stats[date] = {'views': 0, 'photo_views': 0, 'downloads': 0}
            
            event_type = event.get('event_type')
            if event_type == 'gallery_view':
                daily_stats[date]['views'] += 1
            elif event_type == 'photo_view':
                daily_stats[date]['photo_views'] += 1
            elif event_type == 'photo_download':
                daily_stats[date]['downloads'] += 1
        
        return create_response(200, {
            'gallery_id': gallery_id,
            'period': {
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z',
                'days': 30
            },
            'metrics': {
                'total_views': views,
                'unique_visitors': unique_visitors,
                'photo_views': photo_views,
                'downloads': downloads
            },
            'daily_stats': daily_stats
        })
    except Exception as e:
        print(f"Error getting gallery analytics: {str(e)}")
        return create_response(500, {'error': 'Failed to get analytics'})


def handle_get_overall_analytics(user):
    """Get overall analytics for user"""
    try:
        # Get all user's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        gallery_ids = [g['id'] for g in galleries]
        
        if not gallery_ids:
            return create_response(200, {
                'total_galleries': 0,
                'total_views': 0,
                'total_photo_views': 0,
                'total_downloads': 0,
                'gallery_stats': []
            })
        
        # Get analytics for all galleries
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        all_events = []
        for gallery_id in gallery_ids:
            try:
                response = analytics_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery_id) & Key('timestamp').between(
                        start_date.isoformat() + 'Z',
                        end_date.isoformat() + 'Z'
                    )
                )
                all_events.extend(response.get('Items', []))
            except:
                pass
        
        # Calculate overall metrics
        total_views = sum(1 for e in all_events if e.get('event_type') == 'gallery_view')
        total_photo_views = sum(1 for e in all_events if e.get('event_type') == 'photo_view')
        total_downloads = sum(1 for e in all_events if e.get('event_type') == 'photo_download')
        
        # Per-gallery stats
        gallery_stats = []
        for gallery in galleries:
            gallery_id = gallery['id']
            gallery_events = [e for e in all_events if e.get('gallery_id') == gallery_id]
            gallery_views = sum(1 for e in gallery_events if e.get('event_type') == 'gallery_view')
            
            gallery_stats.append({
                'gallery_id': gallery_id,
                'gallery_name': gallery.get('name', 'Untitled'),
                'views': gallery_views,
                'photo_views': sum(1 for e in gallery_events if e.get('event_type') == 'photo_view'),
                'downloads': sum(1 for e in gallery_events if e.get('event_type') == 'photo_download')
            })
        
        # Sort by views
        gallery_stats.sort(key=lambda x: x['views'], reverse=True)
        
        return create_response(200, {
            'total_galleries': len(galleries),
            'total_views': total_views,
            'total_photo_views': total_photo_views,
            'total_downloads': total_downloads,
            'period': {
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z',
                'days': 30
            },
            'gallery_stats': gallery_stats[:10]  # Top 10 galleries
        })
    except Exception as e:
        print(f"Error getting overall analytics: {str(e)}")
        return create_response(500, {'error': 'Failed to get analytics'})


def handle_track_gallery_view(gallery_id, viewer_user_id=None, metadata=None):
    """Track gallery view event - public endpoint, gets user_id from gallery
    Only tracks if viewer is NOT the gallery owner"""
    try:
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        # Don't track if viewer is the owner
        if viewer_user_id and viewer_user_id == owner_user_id:
            print(f"Skipping tracking: viewer {viewer_user_id} is the gallery owner")
            return create_response(200, {'status': 'skipped', 'reason': 'owner_view'})
        
        # Track the view (owner_user_id is the photographer who owns the gallery)
        if owner_user_id:
            track_event(owner_user_id, gallery_id, 'gallery_view', metadata)
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking gallery view: {str(e)}")
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking


def handle_track_photo_view(photo_id, gallery_id, viewer_user_id=None, metadata=None):
    """Track photo view event - public endpoint, gets user_id from gallery
    Only tracks if viewer is NOT the gallery owner"""
    try:
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id is required'})
        
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        # Don't track if viewer is the owner
        if viewer_user_id and viewer_user_id == owner_user_id:
            print(f"Skipping tracking: viewer {viewer_user_id} is the gallery owner")
            return create_response(200, {'status': 'skipped', 'reason': 'owner_view'})
        
        # Track the view (owner_user_id is the photographer who owns the gallery)
        if owner_user_id:
            track_event(owner_user_id, gallery_id, 'photo_view', {
                'photo_id': photo_id,
                **(metadata or {})
            })
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking photo view: {str(e)}")
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking


def handle_track_photo_download(photo_id, gallery_id, viewer_user_id=None, metadata=None):
    """Track photo download event - public endpoint, gets user_id from gallery
    Only tracks if viewer is NOT the gallery owner"""
    try:
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id is required'})
        
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        # Don't track if viewer is the owner
        if viewer_user_id and viewer_user_id == owner_user_id:
            print(f"Skipping tracking: viewer {viewer_user_id} is the gallery owner")
            return create_response(200, {'status': 'skipped', 'reason': 'owner_view'})
        
        # Track the download (owner_user_id is the photographer who owns the gallery)
        if owner_user_id:
            track_event(owner_user_id, gallery_id, 'photo_download', {
                'photo_id': photo_id,
                **(metadata or {})
            })
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking photo download: {str(e)}")
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking


def handle_track_gallery_share(gallery_id, platform, user=None, metadata=None):
    """Track gallery share event - tracks when gallery is shared to social media"""
    try:
        # Validate and sanitize inputs
        if not gallery_id or not isinstance(gallery_id, str):
            return create_response(400, {'error': 'Invalid gallery ID'})
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', gallery_id) or len(gallery_id) > 128:
            return create_response(400, {'error': 'Invalid gallery ID format'})
        
        # Validate platform
        if platform and not isinstance(platform, str):
            platform = 'unknown'
        if platform and len(platform) > 50:
            platform = platform[:50]
        
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        # Track the share (always track, even if owner shares their own gallery)
        if owner_user_id:
            track_event(owner_user_id, gallery_id, 'gallery_share', {
                'platform': platform,
                **(metadata or {})
            })
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking gallery share: {str(e)}")
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking


def handle_track_photo_share(photo_id, platform, user=None, metadata=None):
    """Track photo share event - tracks when photo is shared to social media"""
    try:
        # Validate and sanitize inputs
        if not photo_id or not isinstance(photo_id, str):
            return create_response(400, {'error': 'Invalid photo ID'})
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', photo_id) or len(photo_id) > 128:
            return create_response(400, {'error': 'Invalid photo ID format'})
        
        # Validate platform
        if platform and not isinstance(platform, str):
            platform = 'unknown'
        if platform and len(platform) > 50:
            platform = platform[:50]
        
        # Get photo to find gallery_id
        photo_response = photos_table.get_item(Key={'id': photo_id})
        if 'Item' not in photo_response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = photo_response['Item']
        gallery_id = photo.get('gallery_id')
        
        if not gallery_id:
            return create_response(400, {'error': 'Photo has no associated gallery'})
        
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        # Track the share (always track, even if owner shares their own photo)
        if owner_user_id:
            track_event(owner_user_id, gallery_id, 'photo_share', {
                'photo_id': photo_id,
                'platform': platform,
                **(metadata or {})
            })
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking photo share: {str(e)}")
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking

