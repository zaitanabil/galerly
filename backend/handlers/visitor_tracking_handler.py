"""
Visitor Tracking Handler
Tracks all website visitors and their behavior for UX improvement
"""
import boto3
import uuid
import json
from datetime import datetime
from decimal import Decimal
from utils.response import create_response

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
visitor_table = dynamodb.Table('galerly-visitor-tracking')


def safe_decimal(value, default=0):
    """Safely convert value to Decimal for numeric values only"""
    try:
        if value is None:
            return Decimal(str(default))
        # Check if value is actually numeric
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        # Try to convert string to float first
        if isinstance(value, str):
            # Remove any whitespace and check if it's a number
            value = value.strip()
            if value:
                float_val = float(value)
                return Decimal(str(float_val))
        return Decimal(str(default))
    except (ValueError, TypeError, ArithmeticError):
        return Decimal(str(default))


def handle_track_visit(body):
    """
    Track a page visit
    
    Body should contain:
    - session_id: Unique session identifier
    - visitor_id: Unique visitor identifier (persists across sessions)
    - page_url: Current page URL
    - page_title: Page title
    - referrer: Where visitor came from
    - user_agent: Browser info
    - device: Device info object
    - location: Geolocation data
    - performance: Performance metrics
    - duration: Time spent on page
    - interaction: Interaction data (scroll, clicks)
    - session_pages_viewed: Total pages viewed in session
    """
    try:
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Extract required fields
        session_id = body.get('session_id', '')
        visitor_id = body.get('visitor_id', '')
        page_url = body.get('page_url', '')
        referrer = body.get('referrer', '')
        user_agent = body.get('user_agent', '')
        
        # Validate required fields
        if not session_id or not page_url:
            return create_response(400, {'error': 'session_id and page_url are required'})
        
        # Device info
        device_info = body.get('device', {})
        device_type = device_info.get('type', 'unknown')
        browser = device_info.get('browser', 'unknown')
        os = device_info.get('os', 'unknown')
        screen_resolution = device_info.get('screen_resolution', '')
        viewport_size = device_info.get('viewport_size', '')
        pixel_ratio = safe_decimal(device_info.get('pixel_ratio', 1), 1)
        touch_support = device_info.get('touch_support', False)
        
        # Location info
        location = body.get('location', {})
        country = location.get('country', '')
        country_code = location.get('country_code', '')
        city = location.get('city', '')
        region = location.get('region', '')
        latitude = safe_decimal(location.get('latitude', 0), 0)
        longitude = safe_decimal(location.get('longitude', 0), 0)
        timezone = location.get('timezone', '')
        ip_address = location.get('ip', '')
        location_accuracy = location.get('accuracy', 'ip-based')
        
        # Performance metrics
        performance = body.get('performance', {})
        page_load_time = safe_decimal(performance.get('page_load_time', 0), 0)
        dom_content_loaded = safe_decimal(performance.get('dom_content_loaded', 0), 0)
        dom_complete = safe_decimal(performance.get('dom_complete', 0), 0)
        first_paint = safe_decimal(performance.get('first_paint', 0), 0)
        first_contentful_paint = safe_decimal(performance.get('first_contentful_paint', 0), 0)
        connection_type = performance.get('connection_type', 'unknown')
        connection_downlink = safe_decimal(performance.get('connection_downlink', 0), 0)
        connection_rtt = safe_decimal(performance.get('connection_rtt', 0), 0)
        
        # Time tracking
        duration = safe_decimal(body.get('duration', 0), 0)
        
        # Interaction data
        interaction = body.get('interaction', {})
        scroll_depth = safe_decimal(interaction.get('scroll_depth', 0), 0)
        clicks = int(interaction.get('clicks', 0))
        
        # Session info
        session_pages_viewed = int(body.get('session_pages_viewed', 1))
        
        # Store visit event
        item = {
            'id': event_id,
            'session_id': session_id,
            'event_type': 'page_view',
            'timestamp': timestamp,
            
            # Page info
            'page_url': page_url,
            'referrer': referrer,
            
            # Device info
            'device_type': device_type,
            'browser': browser,
            'os': os,
            'screen_resolution': screen_resolution,
            'viewport_size': viewport_size,
            'pixel_ratio': pixel_ratio,
            'touch_support': touch_support,
            'user_agent': user_agent,
            
            # Location
            'country': country,
            'country_code': country_code,
            'city': city,
            'region': region,
            'latitude': latitude,
            'longitude': longitude,
            'timezone': timezone,
            'ip_address': ip_address,
            'location_accuracy': location_accuracy,
            
            # Performance
            'page_load_time': page_load_time,
            'dom_content_loaded': dom_content_loaded,
            'dom_complete': dom_complete,
            'first_paint': first_paint,
            'first_contentful_paint': first_contentful_paint,
            'connection_type': connection_type,
            'connection_downlink_mbps': connection_downlink,
            'connection_rtt_ms': connection_rtt,
            
            # Time & Interaction
            'duration_seconds': duration,
            'scroll_depth': scroll_depth,
            'clicks': clicks,
            
            # Session tracking
            'session_pages_viewed': session_pages_viewed,
            
            # Metadata
            'created_at': timestamp
        }
        
        # Add visitor_id if provided
        if visitor_id:
            item['visitor_id'] = visitor_id
        
        visitor_table.put_item(Item=item)
        
        return create_response(200, {
            'success': True,
            'event_id': event_id,
            'message': 'Visit tracked successfully'
        })
        
    except Exception as e:
        print(f"❌ Error tracking visit: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to track visit: {str(e)}'})


def handle_track_event(body):
    """
    Track a custom event (button click, form submission, engagement, etc.)
    
    Body should contain:
    - session_id: Session identifier
    - visitor_id: Visitor identifier
    - event_type: Type of event (click_link, click_button, form_submit, scroll_milestone, page_engagement, etc.)
    - event_category: Category (navigation, interaction, conversion, engagement, error)
    - event_label: Label/description
    - event_value: Optional numeric value
    - page_url: Current page
    - metadata: Additional event data (JSON object)
    """
    try:
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        session_id = body.get('session_id', '')
        visitor_id = body.get('visitor_id', '')
        event_type = body.get('event_type', 'custom_event')
        event_category = body.get('event_category', 'interaction')
        event_label = body.get('event_label', '')
        event_value = body.get('event_value', 0)
        page_url = body.get('page_url', '')
        metadata = body.get('metadata', {})
        
        if not session_id or not event_type:
            return create_response(400, {'error': 'session_id and event_type are required'})
        
        # Build item
        item = {
            'id': event_id,
            'session_id': session_id,
            'event_type': event_type,
            'event_category': event_category,
            'event_label': event_label,
            'event_value': safe_decimal(event_value, 0),
            'page_url': page_url,
            'timestamp': timestamp,
            'created_at': timestamp
        }
        
        # Add visitor_id if provided
        if visitor_id:
            item['visitor_id'] = visitor_id
        
        # Add metadata if provided (sanitize and convert properly)
        if metadata and isinstance(metadata, dict):
            # Convert metadata values appropriately for DynamoDB
            converted_metadata = {}
            for key, value in metadata.items():
                try:
                    if value is None:
                        converted_metadata[key] = ''
                    elif isinstance(value, bool):
                        converted_metadata[key] = value
                    elif isinstance(value, (int, float)):
                        # Only convert numeric types to Decimal
                        converted_metadata[key] = Decimal(str(value))
                    elif isinstance(value, str):
                        # Keep strings as-is (don't try to convert to Decimal)
                        converted_metadata[key] = value
                    elif isinstance(value, (list, dict)):
                        # Convert complex types to JSON string
                        converted_metadata[key] = json.dumps(value)
                    else:
                        # Fallback: convert to string
                        converted_metadata[key] = str(value)
                except Exception as conv_error:
                    print(f"⚠️  Failed to convert metadata key '{key}': {str(conv_error)}")
                    converted_metadata[key] = str(value) if value is not None else ''
            
            item['metadata'] = converted_metadata
        
        visitor_table.put_item(Item=item)
        
        return create_response(200, {
            'success': True,
            'event_id': event_id
        })
        
    except Exception as e:
        print(f"❌ Error tracking event: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to track event: {str(e)}'})


def handle_track_session_end(body):
    """
    Track session end with summary
    
    Body should contain:
    - session_id: Session identifier
    - visitor_id: Visitor identifier
    - total_duration: Total session duration in seconds
    - page_duration: Current page duration
    - total_pages_viewed: Number of pages viewed
    - total_interactions: Number of interactions
    - final_scroll_depth: Final scroll depth percentage
    - final_clicks: Total clicks
    - exit_page: Last page viewed
    """
    try:
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        session_id = body.get('session_id', '')
        visitor_id = body.get('visitor_id', '')
        total_duration = body.get('total_duration', 0)
        page_duration = body.get('page_duration', 0)
        total_pages_viewed = body.get('total_pages_viewed', 0)
        total_interactions = body.get('total_interactions', 0)
        final_scroll_depth = body.get('final_scroll_depth', 0)
        final_clicks = body.get('final_clicks', 0)
        exit_page = body.get('exit_page', '')
        
        if not session_id:
            return create_response(400, {'error': 'session_id is required'})
        
        item = {
            'id': event_id,
            'session_id': session_id,
            'event_type': 'session_end',
            'timestamp': timestamp,
            'total_duration': safe_decimal(total_duration, 0),
            'page_duration': safe_decimal(page_duration, 0),
            'total_pages_viewed': int(total_pages_viewed),
            'total_interactions': int(total_interactions),
            'final_scroll_depth': safe_decimal(final_scroll_depth, 0),
            'final_clicks': int(final_clicks),
            'exit_page': exit_page,
            'created_at': timestamp
        }
        
        # Add visitor_id if provided
        if visitor_id:
            item['visitor_id'] = visitor_id
        
        visitor_table.put_item(Item=item)
        
        return create_response(200, {
            'success': True,
            'event_id': event_id
        })
        
    except Exception as e:
        print(f"❌ Error tracking session end: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to track session end: {str(e)}'})


def handle_get_visitor_analytics(user, query_params):
    """
    Get visitor analytics (AUTHENTICATED - photographer only)
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    - page: Specific page to filter
    - event_type: Specific event type
    - limit: Number of records to return (default 100, max 1000)
    """
    try:
        limit = min(int(query_params.get('limit', 100)), 1000)
        event_type_filter = query_params.get('event_type')
        
        # Scan table with optional filters
        scan_params = {
            'Limit': limit
        }
        
        if event_type_filter:
            scan_params['FilterExpression'] = 'event_type = :event_type'
            scan_params['ExpressionAttributeValues'] = {':event_type': event_type_filter}
        
        response = visitor_table.scan(**scan_params)
        items = response.get('Items', [])
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        items = convert_decimals(items)
        
        # Calculate basic summary stats
        total_events = len(items)
        page_views = [item for item in items if item.get('event_type') == 'page_view']
        session_ends = [item for item in items if item.get('event_type') == 'session_end']
        
        # Unique sessions and visitors
        unique_sessions = len(set(item.get('session_id') for item in items if item.get('session_id')))
        unique_visitors = len(set(item.get('visitor_id') for item in items if item.get('visitor_id')))
        
        # Device breakdown
        device_counts = {}
        for item in page_views:
            device = item.get('device_type', 'unknown')
            device_counts[device] = device_counts.get(device, 0) + 1
        
        # Top pages
        page_counts = {}
        for item in page_views:
            page_url = item.get('page_url', '')
            page_counts[page_url] = page_counts.get(page_url, 0) + 1
        
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Average session duration
        avg_session_duration = 0
        if session_ends:
            total_duration = sum(item.get('total_duration', 0) for item in session_ends)
            avg_session_duration = total_duration / len(session_ends)
        
        summary = {
            'total_events': total_events,
            'unique_sessions': unique_sessions,
            'unique_visitors': unique_visitors,
            'total_page_views': len(page_views),
            'total_session_ends': len(session_ends),
            'avg_session_duration_seconds': round(avg_session_duration, 2),
            'device_breakdown': device_counts,
            'top_pages': [{'url': url, 'views': count} for url, count in top_pages]
        }
        
        return create_response(200, {
            'summary': summary,
            'events': items,
            'count': len(items)
        })
        
    except Exception as e:
        print(f"❌ Error getting visitor analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to get analytics: {str(e)}'})
