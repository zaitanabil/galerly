"""
Video playback analytics tracking
Tracks video views, watch time, and engagement
"""
from datetime import datetime, timezone
from decimal import Decimal
from utils.config import video_analytics_table
from utils.response import create_response


def handle_track_video_view(body):
    """
    Track video view event
    Called from frontend when video starts playing
    """
    try:
        photo_id = body.get('photo_id')
        gallery_id = body.get('gallery_id')
        user_id = body.get('user_id')  # Optional - client viewing
        duration_watched = body.get('duration_watched', 0)  # Seconds watched
        total_duration = body.get('total_duration', 0)  # Total video length
        quality = body.get('quality', 'auto')  # 720p, 1080p, 2160p, auto
        session_id = body.get('session_id')  # Unique per viewing session
        
        if not photo_id or not gallery_id:
            return create_response(400, {'error': 'photo_id and gallery_id required'})
        
        # Create analytics entry
        event_id = f"{session_id or photo_id}_{datetime.now(timezone.utc).timestamp()}"
        
        event = {
            'id': event_id,
            'photo_id': photo_id,
            'gallery_id': gallery_id,
            'user_id': user_id or 'anonymous',
            'event_type': 'video_view',
            'duration_watched': Decimal(str(duration_watched)),
            'total_duration': Decimal(str(total_duration)),
            'completion_rate': Decimal(str((duration_watched / total_duration * 100) if total_duration > 0 else 0)),
            'quality': quality,
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        video_analytics_table.put_item(Item=event)
        
        return create_response(200, {'success': True})
        
    except Exception as e:
        print(f"Error tracking video view: {str(e)}")
        return create_response(500, {'error': 'Failed to track video view'})


def handle_get_video_analytics(user, photo_id):
    """
    Get analytics for a specific video
    Photographer-only endpoint
    """
    try:
        from boto3.dynamodb.conditions import Key, Attr
        
        # Try querying with index first
        try:
            response = video_analytics_table.query(
                IndexName='PhotoIdIndex',
                KeyConditionExpression=Key('photo_id').eq(photo_id)
            )
            events = response.get('Items', [])
        except Exception as query_error:
            # Fallback to scan if index query fails (e.g., in tests)
            print(f"Query failed, falling back to scan: {str(query_error)}")
            response = video_analytics_table.scan(
                FilterExpression=Attr('photo_id').eq(photo_id)
            )
            events = response.get('Items', [])
        
        # Calculate statistics
        total_views = len(events)
        total_watch_time = sum(float(e.get('duration_watched', 0)) for e in events)
        avg_completion = sum(float(e.get('completion_rate', 0)) for e in events) / total_views if total_views > 0 else 0
        
        # Quality breakdown
        quality_counts = {}
        for event in events:
            quality = event.get('quality', 'unknown')
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        return create_response(200, {
            'photo_id': photo_id,
            'total_views': total_views,
            'total_watch_time_seconds': round(total_watch_time, 2),
            'total_watch_time_minutes': round(total_watch_time / 60, 2),
            'average_completion_rate': round(avg_completion, 2),
            'quality_breakdown': quality_counts,
            'events': events
        })
        
    except Exception as e:
        print(f"Error getting video analytics: {str(e)}")
        return create_response(500, {'error': 'Failed to get video analytics'})

