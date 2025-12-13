"""
Client Engagement Analytics Handler
Tracks photo/video engagement, client preferences, and generates insights
"""
import uuid
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import analytics_table, galleries_table, photos_table
from utils.response import create_response

# Analytics time range configuration from environment
ANALYTICS_DEFAULT_DAYS = int(os.environ.get('ANALYTICS_DEFAULT_DAYS', '30'))  # Default 30-day window
ANALYTICS_MAX_DAYS = int(os.environ.get('ANALYTICS_MAX_DAYS', '365'))  # Maximum 1 year


def handle_track_visit(body):
    """Track a gallery visit"""
    try:
        gallery_id = body.get('gallery_id')
        if not gallery_id:
            return create_response(400, {'error': 'gallery_id required'})
        
        # Note: gallery_id can be 'general' for non-gallery pages
        
        # Extract metadata fields, allowing them to be at top level or in metadata object
        metadata = body.get('metadata', {})
        
        event = {
            'id': str(uuid.uuid4()),
            'gallery_id': gallery_id,
            'event_type': 'visit',
            'timestamp': body.get('event_time', datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'),
            'metadata': {
                'path': body.get('path') or metadata.get('path', ''),
                'referrer': body.get('referrer') or metadata.get('referrer', ''),
                'screen_width': body.get('screen_width') or metadata.get('screen_width'),
                'screen_height': body.get('screen_height') or metadata.get('screen_height')
            }
        }
        
        analytics_table.put_item(Item=event)
        return create_response(200, {'success': True})
    except Exception as e:
        print(f"Error tracking visit: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to track visit'})


def handle_track_event(body):
    """Track a general event"""
    try:
        gallery_id = body.get('gallery_id')
        event_type = body.get('event_type')
        
        if not gallery_id or not event_type:
            return create_response(400, {'error': 'gallery_id and event_type required'})
        
        # Collect all non-standard fields as metadata
        standard_fields = {'gallery_id', 'event_type', 'event_time', 'metadata'}
        metadata = body.get('metadata', {})
        
        # Add any extra fields to metadata
        for key, value in body.items():
            if key not in standard_fields and value is not None:
                metadata[key] = value
        
        event = {
            'id': str(uuid.uuid4()),
            'gallery_id': gallery_id,
            'event_type': event_type,
            'timestamp': body.get('event_time', datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'),
            'metadata': metadata
        }
        
        analytics_table.put_item(Item=event)
        return create_response(200, {'success': True})
    except Exception as e:
        print(f"Error tracking event: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to track event'})


def handle_track_photo_engagement(body):
    """Track photo engagement (view, zoom, download, favorite, share)"""
    try:
        gallery_id = body.get('gallery_id')
        photo_id = body.get('photo_id')
        event_type = body.get('event_type')  # view, zoom, download, favorite, share
        duration = body.get('duration', 0)  # Time spent in seconds
        
        if not all([gallery_id, photo_id, event_type]):
            return create_response(400, {'error': 'gallery_id, photo_id, and event_type required'})
        
        # Convert duration to Decimal for DynamoDB
        if isinstance(duration, (int, float)):
            duration = Decimal(str(duration))
        
        event = {
            'id': str(uuid.uuid4()),
            'gallery_id': gallery_id,
            'photo_id': photo_id,
            'event_type': f'photo_{event_type}',  # photo_view, photo_zoom, etc.
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'duration': duration,
            'metadata': {
                'event_time': body.get('event_time', datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z')
            }
        }
        
        analytics_table.put_item(Item=event)
        return create_response(200, {'success': True})
    except Exception as e:
        print(f"Error tracking photo engagement: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to track photo engagement'})


def handle_track_video_engagement(body):
    """Track video engagement (play, pause, complete)"""
    try:
        gallery_id = body.get('gallery_id')
        photo_id = body.get('photo_id')  # Video is stored as a photo
        event_type = body.get('event_type')  # play, pause, complete
        video_timestamp = body.get('video_timestamp', 0)  # Current video position
        session_duration = body.get('session_duration', 0)  # Total viewing duration
        
        if not all([gallery_id, photo_id, event_type]):
            return create_response(400, {'error': 'gallery_id, photo_id, and event_type required'})
        
        # Convert to Decimal for DynamoDB
        video_timestamp = Decimal(str(video_timestamp)) if isinstance(video_timestamp, (int, float)) else video_timestamp
        session_duration = Decimal(str(session_duration)) if isinstance(session_duration, (int, float)) else session_duration
        
        event = {
            'id': str(uuid.uuid4()),
            'gallery_id': gallery_id,
            'photo_id': photo_id,
            'event_type': f'video_{event_type}',  # video_play, video_pause, video_complete
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'video_timestamp': video_timestamp,
            'duration': session_duration,
            'metadata': {
                'event_time': body.get('event_time', datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z')
            }
        }
        
        analytics_table.put_item(Item=event)
        return create_response(200, {'success': True})
    except Exception as e:
        print(f"Error tracking video engagement: {str(e)}")
        return create_response(500, {'error': 'Failed to track video engagement'})


def handle_get_gallery_engagement(user, gallery_id):
    """Get engagement summary for all photos/videos in a gallery"""
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        # Get all photos in gallery
        photos_response = photos_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        photos = photos_response.get('Items', [])
        
        # Get analytics events for this gallery
        try:
            analytics_response = analytics_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
        except Exception:
            # If index doesn't exist, fall back to scan
            analytics_response = analytics_table.scan(
                FilterExpression=Attr('gallery_id').eq(gallery_id)
            )
        
        events = analytics_response.get('Items', [])
        
        # Aggregate engagement by photo
        photo_engagement = {}
        for photo in photos:
            photo_id = photo['id']
            photo_events = [e for e in events if e.get('photo_id') == photo_id]
            
            # Count views (both photo_view and video_play/video_complete count as views)
            views = len([e for e in photo_events if any(x in e.get('event_type', '') for x in ['view', 'play', 'complete'])])
            
            # Sum total time spent
            total_time = sum(float(e.get('duration', 0)) for e in photo_events if e.get('duration'))
            
            # Count favorites (photo_favorite or video_favorite)
            favorites = len([e for e in photo_events if 'favorite' in e.get('event_type', '')])
            
            # Count downloads (photo_download or video_download)
            downloads = len([e for e in photo_events if 'download' in e.get('event_type', '')])
            
            # Get download timestamps
            download_events = [e for e in photo_events if 'download' in e.get('event_type', '')]
            download_timestamps = [e.get('timestamp') for e in download_events if e.get('timestamp')]
            
            # Calculate engagement score as INTEGER
            engagement_score = (views * 1) + (favorites * 3) + (downloads * 5) + int(total_time * 0.1)
            
            photo_engagement[photo_id] = {
                'photo_id': photo_id,
                'filename': photo.get('filename', 'Untitled'),
                'type': photo.get('type', 'image'),
                'thumbnail_url': photo.get('thumbnail_url'),
                'total_views': views,
                'total_time_spent': round(total_time, 2),
                'favorite_count': favorites,
                'download_count': downloads,
                'was_downloaded': downloads > 0,
                'download_timestamps': download_timestamps,
                'engagement_score': int(engagement_score),
                'last_viewed': max([e.get('timestamp') for e in photo_events if e.get('timestamp')], default=None)
            }
        
        # Return as array sorted by engagement score
        result = sorted(photo_engagement.values(), key=lambda x: x['engagement_score'], reverse=True)
        
        return create_response(200, result)
    except Exception as e:
        print(f"Error getting gallery engagement: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get engagement data'})


def handle_get_client_preferences(user, gallery_id):
    """Analyze client behavior and preferences"""
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        # Get analytics events for this gallery
        try:
            analytics_response = analytics_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
        except Exception:
            analytics_response = analytics_table.scan(
                FilterExpression=Attr('gallery_id').eq(gallery_id)
            )
        
        events = analytics_response.get('Items', [])
        
        if not events:
            return create_response(200, {})
        
        # Analyze engagement patterns
        # Count views from both photos (photo_view) and videos (video_play, video_complete)
        view_events = [e for e in events if any(x in e.get('event_type', '') for x in ['view', 'play', 'complete'])]
        favorite_events = [e for e in events if 'favorite' in e.get('event_type', '')]
        
        total_views = len(view_events)
        total_favorites = len(favorite_events)
        total_time = sum(float(e.get('duration', 0)) for e in events if e.get('duration'))
        
        # Calculate metrics
        avg_time_per_photo = (total_time / total_views) if total_views > 0 else 0
        favorite_rate = (total_favorites / total_views) if total_views > 0 else 0
        
        # Determine engagement pattern
        if avg_time_per_photo < 3:
            engagement_pattern = 'quick_browser'
        elif avg_time_per_photo > 10:
            engagement_pattern = 'detailed_reviewer'
        else:
            engagement_pattern = 'selective_engager'
        
        # Determine decision speed
        if favorite_rate > 0.3:
            decision_speed = 'decisive'
        elif favorite_rate > 0.1:
            decision_speed = 'moderate'
        else:
            decision_speed = 'selective'
        
        # Get favorite photo types
        favorite_photo_ids = [e.get('photo_id') for e in favorite_events if e.get('photo_id')]
        favorite_types = []
        for photo_id in favorite_photo_ids:
            try:
                photo = photos_table.get_item(Key={'id': photo_id}).get('Item')
                if photo:
                    photo_type = photo.get('type', 'image')
                    favorite_types.append(photo_type)
            except:
                continue
        
        # Count type preferences
        from collections import Counter
        type_counts = Counter(favorite_types)
        preferred_types = [t for t, c in type_counts.most_common(3)]
        
        preferences = {
            'engagement_pattern': engagement_pattern,
            'decision_speed': decision_speed,
            'avg_time_per_photo': float(avg_time_per_photo),
            'favorite_rate': float(favorite_rate),
            'preferred_styles': [],  # Would need photo metadata for this
            'favorite_photo_types': preferred_types
        }
        
        return create_response(200, preferences)
    except Exception as e:
        print(f"Error getting client preferences: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to analyze preferences'})


def handle_get_overall_engagement(user):
    """Get overall engagement analytics across all user's galleries"""
    try:
        print(f"[ENGAGEMENT] Getting overall engagement for user: {user.get('id')}")
        
        # Get all user's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        gallery_ids = [g['id'] for g in galleries]
        
        print(f"[ENGAGEMENT] Found {len(galleries)} galleries: {gallery_ids}")

        if not gallery_ids:
            return create_response(200, {
                'metrics': {
                    'total_views': 0,
                    'total_downloads': 0,
                    'total_favorites': 0,
                    'total_comments': 0,
                    'total_time_spent': 0,
                    'avg_engagement_score': 0
                },
                'daily_stats': [],
                'top_photos': [],
                'gallery_stats': []
            })

        # Get all events for all galleries
        all_events = []
        for gallery_id in gallery_ids:
            try:
                analytics_response = analytics_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery_id)
                )
                all_events.extend(analytics_response.get('Items', []))
            except:
                pass

        # Calculate overall metrics from engagement events
        view_events = [e for e in all_events if any(x in e.get('event_type', '') for x in ['view', 'play', 'complete'])]
        download_events = [e for e in all_events if 'download' in e.get('event_type', '')]
        favorite_events = [e for e in all_events if 'favorite' in e.get('event_type', '')]
        comment_events = [e for e in all_events if e.get('event_type') == 'comment']
        
        total_views = len(view_events)
        total_downloads = len(download_events)
        total_favorites = len(favorite_events)
        total_comments = len(comment_events)
        total_time_spent = sum(float(e.get('duration', 0)) for e in all_events if e.get('duration'))
        
        # Calculate daily stats (last N days from config)
        from datetime import timedelta
        from collections import defaultdict
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=ANALYTICS_DEFAULT_DAYS)
        
        daily_stats = {}
        for i in range(ANALYTICS_DEFAULT_DAYS + 1):
            d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats[d] = {'views': 0, 'downloads': 0}
        
        for event in all_events:
            date = event.get('timestamp', '')[:10]
            if date in daily_stats:
                event_type = event.get('event_type', '')
                if any(x in event_type for x in ['view', 'play', 'complete']):
                    daily_stats[date]['views'] += 1
                elif 'download' in event_type:
                    daily_stats[date]['downloads'] += 1
        
        # Convert to list
        daily_stats_list = [{'date': k, 'views': v['views'], 'downloads': v['downloads']} for k, v in sorted(daily_stats.items())]
        
        # Get top photos across all galleries
        photo_stats = {}
        for event in all_events:
            photo_id = event.get('photo_id')
            if photo_id:
                if photo_id not in photo_stats:
                    photo_stats[photo_id] = {'views': 0, 'time_spent': 0, 'favorites': 0, 'downloads': 0}
                
                event_type = event.get('event_type', '')
                if any(x in event_type for x in ['view', 'play', 'complete']):
                    photo_stats[photo_id]['views'] += 1
                if 'favorite' in event_type:
                    photo_stats[photo_id]['favorites'] += 1
                if 'download' in event_type:
                    photo_stats[photo_id]['downloads'] += 1
                if event.get('duration'):
                    photo_stats[photo_id]['time_spent'] += float(event.get('duration', 0))
        
        # Get top 10 photos
        top_photo_ids = sorted(photo_stats.keys(), 
                              key=lambda x: (photo_stats[x]['views'] * 2 + 
                                           photo_stats[x]['favorites'] * 3 + 
                                           photo_stats[x]['downloads'] * 4),
                              reverse=True)[:10]
        
        top_photos = []
        for photo_id in top_photo_ids:
            try:
                photo = photos_table.get_item(Key={'id': photo_id}).get('Item')
                if photo:
                    stats = photo_stats[photo_id]
                    # Calculate engagement score (0-100)
                    score = min(100, (
                        stats['views'] * 2 +
                        stats['favorites'] * 10 +
                        stats['downloads'] * 15 +
                        min(stats['time_spent'], 60) * 0.5
                    ))
                    
                    top_photos.append({
                        'id': photo_id,
                        'name': photo.get('filename', 'Untitled'),
                        'thumbnail_url': photo.get('thumbnail_url') or photo.get('url'),
                        'views': stats['views'],
                        'favorites': stats['favorites'],
                        'downloads': stats['downloads'],
                        'avg_time_seconds': stats['time_spent'] / max(stats['views'], 1),
                        'engagement_score': int(score)
                    })
            except:
                continue
        
        # Get per-gallery stats
        gallery_stats = []
        for gallery in galleries:
            gallery_id = gallery['id']
            gallery_events = [e for e in all_events if e.get('gallery_id') == gallery_id]
            
            gallery_views = len([e for e in gallery_events if any(x in e.get('event_type', '') for x in ['view', 'play', 'complete'])])
            gallery_downloads = len([e for e in gallery_events if 'download' in e.get('event_type', '')])
            gallery_favorites = len([e for e in gallery_events if 'favorite' in e.get('event_type', '')])
            
            gallery_stats.append({
                'gallery_id': gallery_id,
                'gallery_name': gallery.get('name', 'Untitled'),
                'cover_photo': gallery.get('cover_photo') or gallery.get('thumbnail_url'),
                'views': gallery_views,
                'downloads': gallery_downloads,
                'favorites': gallery_favorites
            })
        
        # Sort by views
        gallery_stats.sort(key=lambda x: x['views'], reverse=True)
        
        # Calculate average engagement score
        avg_engagement_score = sum(p['engagement_score'] for p in top_photos) / max(len(top_photos), 1) if top_photos else 0
        
        result = {
            'metrics': {
                'total_views': total_views,
                'total_downloads': total_downloads,
                'total_favorites': total_favorites,
                'total_comments': total_comments,
                'total_time_spent': int(total_time_spent),
                'avg_engagement_score': int(avg_engagement_score)
            },
            'daily_stats': daily_stats_list,
            'top_photos': top_photos,
            'gallery_stats': gallery_stats[:10]  # Top 10 galleries
        }
        
        print(f"[ENGAGEMENT] Returning metrics: views={total_views}, downloads={total_downloads}, favorites={total_favorites}")
        print(f"[ENGAGEMENT] Daily stats count: {len(daily_stats_list)}, Top photos: {len(top_photos)}")
        
        return create_response(200, result)
    except Exception as e:
        print(f"Error getting overall engagement: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get overall engagement'})


def handle_get_gallery_engagement_summary(user, gallery_id):
    """Get gallery-level engagement analytics summary (for analytics page)"""
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        print(f"[ENGAGEMENT] Getting summary for gallery: {gallery_id}")
        
        # Get all events for this gallery
        try:
            analytics_response = analytics_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
        except:
            analytics_response = analytics_table.scan(
                FilterExpression=Attr('gallery_id').eq(gallery_id)
            )
        
        all_events = analytics_response.get('Items', [])
        
        # Calculate overall metrics from engagement events (SAME LOGIC AS OVERALL)
        view_events = [e for e in all_events if any(x in e.get('event_type', '') for x in ['view', 'play', 'complete'])]
        download_events = [e for e in all_events if 'download' in e.get('event_type', '')]
        favorite_events = [e for e in all_events if 'favorite' in e.get('event_type', '')]
        comment_events = [e for e in all_events if e.get('event_type') == 'comment']
        
        total_views = len(view_events)
        total_downloads = len(download_events)
        total_favorites = len(favorite_events)
        total_comments = len(comment_events)
        total_time_spent = sum(float(e.get('duration', 0)) for e in all_events if e.get('duration'))
        
        print(f"[ENGAGEMENT] Gallery summary - views={total_views}, downloads={total_downloads}, favorites={total_favorites}")
        
        # Calculate daily stats (last N days from config)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=ANALYTICS_DEFAULT_DAYS)
        
        daily_stats = {}
        for i in range(ANALYTICS_DEFAULT_DAYS + 1):
            d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats[d] = {'views': 0, 'downloads': 0}
        
        for event in all_events:
            date = event.get('timestamp', '')[:10]
            if date in daily_stats:
                event_type = event.get('event_type', '')
                if any(x in event_type for x in ['view', 'play', 'complete']):
                    daily_stats[date]['views'] += 1
                elif 'download' in event_type:
                    daily_stats[date]['downloads'] += 1
        
        daily_stats_list = [{'date': k, 'views': v['views'], 'downloads': v['downloads']} for k, v in sorted(daily_stats.items())]
        
        # Get top photos across this gallery (SAME LOGIC AS OVERALL)
        photo_stats = {}
        for event in all_events:
            photo_id = event.get('photo_id')
            if photo_id:
                if photo_id not in photo_stats:
                    photo_stats[photo_id] = {'views': 0, 'time_spent': 0, 'favorites': 0, 'downloads': 0}
                
                event_type = event.get('event_type', '')
                if any(x in event_type for x in ['view', 'play', 'complete']):
                    photo_stats[photo_id]['views'] += 1
                if 'favorite' in event_type:
                    photo_stats[photo_id]['favorites'] += 1
                if 'download' in event_type:
                    photo_stats[photo_id]['downloads'] += 1
                if event.get('duration'):
                    photo_stats[photo_id]['time_spent'] += float(event.get('duration', 0))
        
        # Get top 10 photos
        top_photo_ids = sorted(photo_stats.keys(), 
                              key=lambda x: (photo_stats[x]['views'] * 2 + 
                                           photo_stats[x]['favorites'] * 3 + 
                                           photo_stats[x]['downloads'] * 4),
                              reverse=True)[:10]
        
        top_photos = []
        for photo_id in top_photo_ids:
            try:
                photo = photos_table.get_item(Key={'id': photo_id}).get('Item')
                if photo:
                    stats = photo_stats[photo_id]
                    # Calculate engagement score (0-100)
                    score = min(100, (
                        stats['views'] * 2 +
                        stats['favorites'] * 10 +
                        stats['downloads'] * 15 +
                        min(stats['time_spent'], 60) * 0.5
                    ))
                    
                    top_photos.append({
                        'id': photo_id,
                        'name': photo.get('filename', 'Untitled'),
                        'thumbnail_url': photo.get('thumbnail_url') or photo.get('url'),
                        'views': stats['views'],
                        'favorites': stats['favorites'],
                        'downloads': stats['downloads'],
                        'avg_time_seconds': stats['time_spent'] / max(stats['views'], 1),
                        'engagement_score': int(score)
                    })
            except:
                continue
        
        # Calculate average engagement score
        avg_engagement_score = sum(p['engagement_score'] for p in top_photos) / max(len(top_photos), 1) if top_photos else 0
        
        return create_response(200, {
            'metrics': {
                'total_views': total_views,
                'total_downloads': total_downloads,
                'total_favorites': total_favorites,
                'total_comments': total_comments,
                'total_time_spent': int(total_time_spent),
                'avg_engagement_score': int(avg_engagement_score)
            },
            'daily_stats': daily_stats_list,
            'top_photos': top_photos
        })
    except Exception as e:
        print(f"Error getting gallery engagement summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get engagement summary'})


