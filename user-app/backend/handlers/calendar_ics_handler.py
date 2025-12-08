"""
Calendar ICS Export Handler
Generate ICS calendar feeds and export individual appointments
"""

import json
import boto3
from datetime import datetime, timedelta
from utils.auth import get_user_from_token
from utils.response import create_response
from utils.config import get_dynamodb

dynamodb = get_dynamodb()

def handle_export_appointment_ics(event):
    """
    Export a single appointment as ICS file
    GET /appointments/{appointment_id}/ics
    """
    try:
        # Can be accessed by photographer or client (with token in URL)
        appointment_id = event['pathParameters']['appointment_id']
        
        # Get appointment
        appointments_table = dynamodb.Table('galerly-appointments')
        response = appointments_table.get_item(Key={'id': appointment_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Appointment not found'})
        
        appointment = response['Item']
        
        # Generate ICS content
        ics_content = generate_appointment_ics(appointment)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/calendar',
                'Content-Disposition': f'attachment; filename="appointment_{appointment_id}.ics"',
                'Access-Control-Allow-Origin': '*'
            },
            'body': ics_content
        }
        
    except Exception as e:
        print(f"Error exporting appointment ICS: {str(e)}")
        return create_response(500, {'error': f'Failed to export ICS: {str(e)}'})


def handle_export_calendar_feed(event):
    """
    Export calendar feed with all appointments
    GET /calendar/feed.ics?photographer_id={id}&token={token}
    """
    try:
        params = event.get('queryStringParameters') or {}
        photographer_id = params.get('photographer_id')
        token = params.get('token')
        
        if not photographer_id or not token:
            return create_response(400, {'error': 'Missing parameters'})
        
        # Verify feed token
        users_table = dynamodb.Table('galerly-users')
        user_response = users_table.get_item(Key={'id': photographer_id})
        
        if 'Item' not in user_response:
            return create_response(404, {'error': 'Photographer not found'})
        
        user = user_response['Item']
        
        # Verify calendar feed token
        if user.get('calendar_feed_token') != token:
            return create_response(403, {'error': 'Invalid token'})
        
        # Get all appointments for photographer
        appointments_table = dynamodb.Table('galerly-appointments')
        response = appointments_table.query(
            IndexName='photographer_date_index',
            KeyConditionExpression='photographer_id = :pid',
            ExpressionAttributeValues={
                ':pid': photographer_id
            }
        )
        
        appointments = response.get('Items', [])
        
        # Generate ICS feed
        ics_content = generate_calendar_feed(appointments, user)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/calendar; charset=utf-8',
                'Content-Disposition': f'inline; filename="calendar.ics"',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache, must-revalidate'
            },
            'body': ics_content
        }
        
    except Exception as e:
        print(f"Error exporting calendar feed: {str(e)}")
        return create_response(500, {'error': f'Failed to export feed: {str(e)}'})


def handle_generate_calendar_token(event):
    """
    Generate or regenerate calendar feed token
    POST /calendar/token
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user or user.get('role') != 'photographer':
            return create_response(403, {'error': 'Unauthorized'})
        
        photographer_id = user['user_id']
        
        # Generate new token
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Save token
        users_table = dynamodb.Table('galerly-users')
        users_table.update_item(
            Key={'id': photographer_id},
            UpdateExpression='SET calendar_feed_token = :token',
            ExpressionAttributeValues={':token': token}
        )
        
        # Generate feed URL
        import os
        api_domain = os.environ.get('API_DOMAIN', 'https://api.galerly.com')
        feed_url = f"{api_domain}/v1/calendar/feed.ics?photographer_id={photographer_id}&token={token}"
        
        return create_response(200, {
            'token': token,
            'feed_url': feed_url,
            'instructions': {
                'google_calendar': 'Add by URL in Google Calendar settings',
                'apple_calendar': 'File > New Calendar Subscription',
                'outlook': 'Add calendar from Internet'
            }
        })
        
    except Exception as e:
        print(f"Error generating calendar token: {str(e)}")
        return create_response(500, {'error': f'Failed to generate token: {str(e)}'})


def generate_appointment_ics(appointment):
    """Generate ICS content for a single appointment"""
    
    # Format datetime for ICS (YYYYMMDDTHHMMSSZ)
    start_dt = datetime.fromisoformat(appointment['start_time'].replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(appointment['end_time'].replace('Z', '+00:00'))
    
    start_str = start_dt.strftime('%Y%m%dT%H%M%SZ')
    end_str = end_dt.strftime('%Y%m%dT%H%M%SZ')
    created_str = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    
    # Build ICS content
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Galerly//Photography Scheduler//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Galerly Appointments
X-WR-TIMEZONE:UTC

BEGIN:VEVENT
UID:{appointment['id']}@galerly.com
DTSTAMP:{created_str}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{appointment.get('title', 'Photography Session')}
DESCRIPTION:{format_description(appointment)}
LOCATION:{appointment.get('location', '')}
STATUS:{get_ics_status(appointment.get('status', 'pending'))}
CLASS:PUBLIC
TRANSP:OPAQUE
SEQUENCE:0
END:VEVENT

END:VCALENDAR"""
    
    return ics


def generate_calendar_feed(appointments, photographer):
    """Generate ICS feed with multiple appointments"""
    
    created_str = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    
    # Start calendar
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Galerly//Photography Scheduler//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{photographer.get('business_name', photographer.get('name', 'Galerly'))} Schedule
X-WR-TIMEZONE:UTC
X-WR-CALDESC:Photography appointments and sessions
"""
    
    # Add each appointment
    for appointment in appointments:
        try:
            start_dt = datetime.fromisoformat(appointment['start_time'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(appointment['end_time'].replace('Z', '+00:00'))
            
            start_str = start_dt.strftime('%Y%m%dT%H%M%SZ')
            end_str = end_dt.strftime('%Y%m%dT%H%M%SZ')
            
            ics += f"""
BEGIN:VEVENT
UID:{appointment['id']}@galerly.com
DTSTAMP:{created_str}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{appointment.get('title', 'Photography Session')}
DESCRIPTION:{format_description(appointment)}
LOCATION:{appointment.get('location', '')}
STATUS:{get_ics_status(appointment.get('status', 'pending'))}
CLASS:PUBLIC
TRANSP:OPAQUE
SEQUENCE:0
END:VEVENT
"""
        except Exception as e:
            print(f"Error adding appointment {appointment.get('id')} to feed: {str(e)}")
            continue
    
    # End calendar
    ics += "\nEND:VCALENDAR"
    
    return ics


def format_description(appointment):
    """Format appointment description for ICS"""
    description = appointment.get('notes', '')
    
    # Add client info
    if appointment.get('client_name'):
        description += f"\\n\\nClient: {appointment['client_name']}"
    if appointment.get('client_email'):
        description += f"\\nEmail: {appointment['client_email']}"
    if appointment.get('client_phone'):
        description += f"\\nPhone: {appointment['client_phone']}"
    
    # Add session details
    if appointment.get('session_type'):
        description += f"\\n\\nType: {appointment['session_type']}"
    if appointment.get('duration'):
        description += f"\\nDuration: {appointment['duration']} minutes"
    
    # Escape special characters for ICS
    description = description.replace(',', '\\,')
    description = description.replace(';', '\\;')
    description = description.replace('\n', '\\n')
    
    return description


def get_ics_status(status):
    """Map appointment status to ICS status"""
    status_map = {
        'confirmed': 'CONFIRMED',
        'pending': 'TENTATIVE',
        'cancelled': 'CANCELLED',
        'completed': 'CONFIRMED'
    }
    return status_map.get(status, 'TENTATIVE')
