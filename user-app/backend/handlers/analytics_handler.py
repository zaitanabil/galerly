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
        bulk_downloads = sum(1 for e in events if e.get('event_type') == 'bulk_download')
        
        # Time series data (last 30 days)
        daily_stats = {}
        photo_stats = {}
        
        for event in events:
            date = event['timestamp'][:10]  # YYYY-MM-DD
            if date not in daily_stats:
                daily_stats[date] = {'views': 0, 'photo_views': 0, 'downloads': 0}
            
            event_type = event.get('event_type')
            if event_type == 'gallery_view':
                daily_stats[date]['views'] += 1
            elif event_type == 'photo_view':
                daily_stats[date]['photo_views'] += 1
                
                # Aggregate photo views
                meta = event.get('metadata', {})
                pid = meta.get('photo_id')
                if pid:
                    if pid not in photo_stats:
                        photo_stats[pid] = 0
                    photo_stats[pid] += 1
                    
            elif event_type == 'photo_download':
                daily_stats[date]['downloads'] += 1
            elif event_type == 'bulk_download':
                if 'bulk_downloads' not in daily_stats[date]:
                    daily_stats[date]['bulk_downloads'] = 0
                daily_stats[date]['bulk_downloads'] += 1
                
        # Get top photos
        top_photo_ids = sorted(photo_stats.keys(), key=lambda x: photo_stats[x], reverse=True)[:10]
        
        # Fetch photo details
        top_photos = []
        if top_photo_ids:
            try:
                for pid in top_photo_ids:
                    try:
                        p_item = photos_table.get_item(Key={'id': pid}).get('Item')
                        if p_item:
                            top_photos.append({
                                'id': pid,
                                'url': p_item.get('url'),
                                'thumbnail_url': p_item.get('thumbnail_url') or p_item.get('url'),
                                'name': p_item.get('filename', 'Untitled'),
                                'views': photo_stats[pid],
                                'avg_time_seconds': 0  # Placeholder
                            })
                    except:
                        continue
            except Exception as e:
                print(f"Error fetching photo details: {e}")
        
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
                'downloads': downloads,
                'bulk_downloads': bulk_downloads
            },
            'daily_stats': daily_stats,
            'top_photos': top_photos
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
                'total_bulk_downloads': 0,
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
        total_bulk_downloads = sum(1 for e in all_events if e.get('event_type') == 'bulk_download')
        
        # Per-gallery stats
        gallery_stats = []
        daily_stats = {}
        photo_stats = {}
        
        # Initialize last 30 days in daily_stats
        for i in range(30):
            d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats[d] = {'views': 0, 'downloads': 0}

        for event in all_events:
            date = event['timestamp'][:10]
            event_type = event.get('event_type')
            
            # Populate daily stats if date is within range
            if date in daily_stats:
                if event_type == 'gallery_view':
                    daily_stats[date]['views'] += 1
                elif event_type in ['photo_download', 'bulk_download']:
                    daily_stats[date]['downloads'] += 1
            
            # Aggregate photo views
            if event_type == 'photo_view':
                meta = event.get('metadata', {})
                pid = meta.get('photo_id')
                if pid:
                    if pid not in photo_stats:
                        photo_stats[pid] = 0
                    photo_stats[pid] += 1

        # Get top photos across all galleries
        top_photo_ids = sorted(photo_stats.keys(), key=lambda x: photo_stats[x], reverse=True)[:10]
        
        # Fetch photo details
        top_photos = []
        if top_photo_ids:
            try:
                for pid in top_photo_ids:
                    try:
                        p_item = photos_table.get_item(Key={'id': pid}).get('Item')
                        if p_item:
                            top_photos.append({
                                'id': pid,
                                'url': p_item.get('url'),
                                'thumbnail_url': p_item.get('thumbnail_url') or p_item.get('url'),
                                'name': p_item.get('filename', 'Untitled'),
                                'views': photo_stats[pid],
                                'avg_time_seconds': 0  # Placeholder
                            })
                    except:
                        continue
            except Exception as e:
                print(f"Error fetching photo details: {e}")

        for gallery in galleries:
            gallery_id = gallery['id']
            gallery_events = [e for e in all_events if e.get('gallery_id') == gallery_id]
            gallery_views = sum(1 for e in gallery_events if e.get('event_type') == 'gallery_view')
            gallery_downloads = sum(1 for e in gallery_events if e.get('event_type') in ['photo_download', 'bulk_download'])
            
            gallery_stats.append({
                'gallery_id': gallery_id,
                'gallery_name': gallery.get('name', 'Untitled'),
                'cover_photo': gallery.get('cover_photo') or gallery.get('cover_photo_url') or gallery.get('thumbnail_url'),
                'views': gallery_views,
                'photo_views': sum(1 for e in gallery_events if e.get('event_type') == 'photo_view'),
                'downloads': gallery_downloads,
                'bulk_downloads': sum(1 for e in gallery_events if e.get('event_type') == 'bulk_download')
            })
        
        # Sort by views
        gallery_stats.sort(key=lambda x: x['views'], reverse=True)
        
        # Convert daily_stats to list for frontend
        daily_stats_list = [{'date': k, 'views': v['views'], 'downloads': v['downloads']} for k, v in sorted(daily_stats.items())]
        
        return create_response(200, {
            'total_galleries': len(galleries),
            'total_views': total_views,
            'total_photo_views': total_photo_views,
            'total_downloads': total_downloads,
            'total_bulk_downloads': total_bulk_downloads,
            'period': {
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z',
                'days': 30
            },
            'daily_stats': daily_stats_list,
            'gallery_stats': gallery_stats[:10],  # Top 10 galleries
            'top_photos': top_photos
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
            
            # Increment gallery view count atomically
            try:
                galleries_table.update_item(
                    Key={'user_id': owner_user_id, 'id': gallery_id},
                    UpdateExpression='SET view_count = if_not_exists(view_count, :zero) + :inc',
                    ExpressionAttributeValues={':inc': 1, ':zero': 0}
                )
            except Exception as update_err:
                print(f"Failed to increment view_count: {update_err}")
                
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
            
            # Increment gallery download count atomically (optional but useful)
            try:
                galleries_table.update_item(
                    Key={'user_id': owner_user_id, 'id': gallery_id},
                    UpdateExpression='SET download_count = if_not_exists(download_count, :zero) + :inc',
                    ExpressionAttributeValues={':inc': 1, ':zero': 0}
                )
            except Exception as update_err:
                # Ignore if field doesn't exist or other error, not critical
                pass
                
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


def handle_track_bulk_download(gallery_id, viewer_user_id=None, metadata=None, client_ip=None):
    """
    Track bulk download event - tracks when a user downloads all photos from a gallery
    Tracks all downloads and uses IP address to identify if it's the owner
    Sends email notification to photographer
    """
    try:
        print(f"Tracking bulk download for gallery {gallery_id}")
        print(f"   Viewer user ID: {viewer_user_id}")
        print(f"   Client IP: {client_ip}")
        print(f"   Metadata: {metadata}")
        
        # Validate gallery_id
        if not gallery_id or not isinstance(gallery_id, str):
            return create_response(400, {'error': 'Invalid gallery ID'})
        
        # Get gallery to find owner's user_id
        gallery_response = galleries_table.scan(
            FilterExpression='id = :gid',
            ExpressionAttributeValues={':gid': gallery_id}
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        owner_user_id = gallery.get('user_id')
        
        print(f"   Gallery owner: {owner_user_id}")
        print(f"   Viewer: {viewer_user_id if viewer_user_id else 'Anonymous'}")
        
        # Track ALL downloads (including owner downloads)
        # Determine if downloader is the owner by checking:
        # 1. User ID match (if authenticated)
        # 2. IP address match with owner's recent activity
        if owner_user_id:
            # Add photo count to metadata
            photo_count = gallery.get('photo_count', 0)
            
            # Check if this is an owner download
            is_owner_download = False
            
            # Method 1: Check user ID (if authenticated)
            if viewer_user_id and viewer_user_id == owner_user_id:
                is_owner_download = True
                print(f"   ✓ Owner detected by user ID match")
            
            # Method 2: Check IP address against owner's recent activity
            elif client_ip and client_ip != 'unknown':
                try:
                    # Get owner's recent events to find their IP addresses
                    owner_events = analytics_table.query(
                        IndexName='UserIdIndex',
                        KeyConditionExpression=Key('user_id').eq(owner_user_id),
                        ScanIndexForward=False,  # Most recent first
                        Limit=20  # Check last 20 events
                    )
                    
                    # Check if this IP matches any recent owner activity
                    for event in owner_events.get('Items', []):
                        event_metadata = event.get('metadata', {})
                        event_ip = event_metadata.get('ip')
                        if event_ip and event_ip == client_ip:
                            is_owner_download = True
                            print(f"   ✓ Owner detected by IP match: {client_ip}")
                            break
                except Exception as e:
                    print(f"    Could not check IP history: {str(e)}")
            
            download_metadata = {
                'photo_count': photo_count,
                'is_owner_download': is_owner_download,
                'viewer_is_authenticated': viewer_user_id is not None,
                'ip': client_ip,
                **(metadata or {})
            }
            
            print(f"   Tracking event for owner {owner_user_id}")
            print(f"   Is owner download: {is_owner_download}")
            track_event(owner_user_id, gallery_id, 'bulk_download', download_metadata)
            
            # Increment gallery download count atomically
            try:
                galleries_table.update_item(
                    Key={'user_id': owner_user_id, 'id': gallery_id},
                    UpdateExpression='SET download_count = if_not_exists(download_count, :zero) + :inc',
                    ExpressionAttributeValues={':inc': 1, ':zero': 0}
                )
            except Exception as update_err:
                pass
            
            # Send email notification to photographer
            try:
                from utils.email import send_email
                from utils.config import users_table
                
                # Get photographer details - use scan with id filter since 'email' is the primary key
                photographer_response = users_table.scan(
                    FilterExpression='id = :user_id',
                    ExpressionAttributeValues={':user_id': owner_user_id}
                )
                
                photographers = photographer_response.get('Items', [])
                if photographers:
                    photographer = photographers[0]
                    photographer_name = photographer.get('name', 'Photographer')
                    photographer_email = photographer.get('email')
                    
                    print(f"   Photographer: {photographer_name} ({photographer_email})")
                    
                    if photographer_email:
                        # Determine downloader type
                        downloader_type = metadata.get('downloader_type', 'viewer') if metadata else 'viewer'
                        downloader_name = metadata.get('downloader_name', 'A visitor') if metadata else 'A visitor'
                        
                        # Add context if owner downloaded their own gallery
                        if is_owner_download:
                            downloader_name = f"{photographer_name} (you)"
                            downloader_type = "photographer (self)"
                        
                        print(f"   Sending email notification...")
                        print(f"   Downloader: {downloader_name} ({downloader_type})")
                        
                        # Send notification email
                        send_email(
                            to_email=photographer_email,
                            template_name='bulk_download_notification',
                            template_vars={
                                'photographer_name': photographer_name,
                                'gallery_name': gallery.get('name', 'Your gallery'),
                                'gallery_id': gallery_id,
                                'photo_count': photo_count,
                                'downloader_type': downloader_type,
                                'downloader_name': downloader_name,
                                'download_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
                                'gallery_url': f"{metadata.get('frontend_url', os.environ.get('FRONTEND_URL'))}/gallery?id={gallery_id}" if metadata else f"{os.environ.get('FRONTEND_URL')}/gallery?id={gallery_id}"
                            }
                        )
                        print(f"Sent bulk download notification to {photographer_email}")
                    else:
                        print(f" No email address for photographer")
                else:
                    print(f" Photographer not found in database")
            except Exception as email_error:
                print(f"Failed to send bulk download notification email: {str(email_error)}")
                import traceback
                traceback.print_exc()
                # Don't fail tracking if email fails
            
            return create_response(200, {'status': 'tracked'})
        else:
            return create_response(404, {'error': 'Gallery owner not found'})
    except Exception as e:
        print(f"Error tracking bulk download: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(200, {'status': 'tracked'})  # Don't fail tracking


def handle_get_bulk_downloads(user):
    """
    Get bulk download events for authenticated photographer
    Returns list of all bulk download events across all their galleries
    """
    from decimal import Decimal
    
    try:
        # Get all user's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        gallery_ids = [g['id'] for g in galleries]
        
        # Create gallery name lookup
        gallery_names = {g['id']: g.get('name', 'Untitled') for g in galleries}
        
        if not gallery_ids:
            # Return consistent structure even when no galleries exist
            return create_response(200, {
                'events': [],
                'count': 0,
                'statistics': {
                    'total_downloads': 0,
                    'unique_visitors': 0,
                    'repeat_downloads': 0,
                    'unique_visitors_info': []
                }
            })
        
        # Get bulk download events for all galleries
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # Last 90 days
        
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
                # Filter for bulk_download events only
                bulk_downloads = [e for e in response.get('Items', []) if e.get('event_type') == 'bulk_download']
                
                # Add gallery name to each event
                for event in bulk_downloads:
                    event['gallery_name'] = gallery_names.get(gallery_id, 'Unknown')
                
                all_events.extend(bulk_downloads)
            except Exception as e:
                print(f"Error fetching events for gallery {gallery_id}: {str(e)}")
                continue
        
        # Sort by timestamp (newest first for display)
        all_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # First pass: Count downloads per unique identifier (IP + authenticated user)
        # Track first_seen as the OLDEST timestamp for each visitor
        visitor_download_count = {}  # visitor_key -> count
        visitor_info_map = {}  # visitor_key -> info
        
        for event in all_events:
            metadata = event.get('metadata', {})
            ip = metadata.get('ip', 'unknown')
            downloader_name = metadata.get('downloader_name', 'Unknown')
            downloader_type = metadata.get('downloader_type', 'viewer')
            is_authenticated = metadata.get('viewer_is_authenticated', False)
            event_timestamp = event.get('timestamp')
            
            # Create unique visitor key
            # For authenticated users: use name+type, for anonymous: use IP
            if is_authenticated and downloader_name != 'A visitor':
                visitor_key = f"auth_{downloader_name}_{downloader_type}"
            else:
                visitor_key = f"ip_{ip}"
            
            # Count downloads and track first_seen (oldest timestamp)
            if visitor_key not in visitor_download_count:
                visitor_download_count[visitor_key] = 0
                visitor_info_map[visitor_key] = {
                    'name': downloader_name,
                    'type': downloader_type,
                    'ip': ip,
                    'first_seen': event_timestamp,  # Will be updated to oldest
                    'is_authenticated': is_authenticated
                }
            else:
                # Update first_seen to the oldest timestamp (earliest)
                current_first = visitor_info_map[visitor_key]['first_seen']
                if event_timestamp and (not current_first or event_timestamp < current_first):
                    visitor_info_map[visitor_key]['first_seen'] = event_timestamp
            
            visitor_download_count[visitor_key] += 1
        
        # Second pass: Add visitor tracking info to each event
        for event in all_events:
            metadata = event.get('metadata', {})
            ip = metadata.get('ip', 'unknown')
            downloader_name = metadata.get('downloader_name', 'Unknown')
            downloader_type = metadata.get('downloader_type', 'viewer')
            is_authenticated = metadata.get('viewer_is_authenticated', False)
            
            # Recreate visitor key
            if is_authenticated and downloader_name != 'A visitor':
                visitor_key = f"auth_{downloader_name}_{downloader_type}"
            else:
                visitor_key = f"ip_{ip}"
            
            # Get total count for this visitor
            total_count = visitor_download_count.get(visitor_key, 1)
            
            # Add visitor tracking info
            event['is_repeat_visitor'] = total_count > 1
            event['visitor_download_count'] = total_count
            event['visitor_id'] = visitor_key
        
        # Calculate summary statistics
        unique_visitors = len(visitor_download_count)
        total_downloads = len(all_events)
        repeat_downloads = sum(1 for e in all_events if e.get('is_repeat_visitor'))
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        all_events = convert_decimals(all_events)
        
        return create_response(200, {
            'events': all_events,
            'count': len(all_events),
            'statistics': {
                'total_downloads': total_downloads,
                'unique_visitors': unique_visitors,
                'repeat_downloads': repeat_downloads,
                'unique_visitors_info': [
                    {
                        'visitor_id': key,
                        'name': info['name'],
                        'type': info['type'],
                        'download_count': visitor_download_count[key],
                        'first_seen': info['first_seen'],
                        'is_authenticated': info['is_authenticated']
                    }
                    for key, info in visitor_info_map.items()
                ]
            }
        })
        
    except Exception as e:
        print(f"Error getting bulk download events: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get bulk download logs'})

