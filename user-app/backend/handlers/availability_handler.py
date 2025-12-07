"""
Availability and calendar integration handlers
Real-time availability checking, time zone handling, and calendar sync
"""
import os
import uuid
from datetime import datetime, timedelta, time
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, appointments_table, users_table
from utils.response import create_response
from handlers.subscription_handler import get_user_features

# Availability settings table (stores photographer's working hours and preferences)
availability_settings_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_AVAILABILITY_SETTINGS', 'galerly-availability-settings-local'))


def handle_get_availability_settings(user):
    """Get photographer's availability settings"""
    try:
        response = availability_settings_table.get_item(Key={'user_id': user['id']})
        
        if 'Item' in response:
            return create_response(200, response['Item'])
        else:
            # Return default settings
            default_settings = {
                'user_id': user['id'],
                'timezone': 'America/New_York',
                'working_hours': {
                    'monday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'tuesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'wednesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'thursday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'friday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'saturday': {'enabled': False, 'start': '10:00', 'end': '15:00'},
                    'sunday': {'enabled': False, 'start': '10:00', 'end': '15:00'}
                },
                'slot_duration': 60,  # minutes
                'buffer_time': 15,  # minutes between appointments
                'booking_window': {
                    'min_hours_ahead': 24,  # Must book at least 24 hours in advance
                    'max_days_ahead': 60  # Can book up to 60 days in advance
                },
                'auto_approve': False  # If true, bookings are auto-confirmed
            }
            return create_response(200, default_settings)
            
    except Exception as e:
        print(f"Error getting availability settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get availability settings'})


def handle_update_availability_settings(user, body):
    """Update photographer's availability settings"""
    try:
        # Check plan access
        features, _, _ = get_user_features(user)
        if not features.get('scheduler'):
            return create_response(403, {
                'error': 'Scheduling is available on the Ultimate plan.',
                'upgrade_required': True
            })
        
        settings = {
            'user_id': user['id'],
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Update allowed fields
        allowed_fields = [
            'timezone', 'working_hours', 'slot_duration', 
            'buffer_time', 'booking_window', 'auto_approve'
        ]
        
        for field in allowed_fields:
            if field in body:
                settings[field] = body[field]
        
        availability_settings_table.put_item(Item=settings)
        
        return create_response(200, settings)
        
    except Exception as e:
        print(f"Error updating availability settings: {str(e)}")
        return create_response(500, {'error': 'Failed to update settings'})


def handle_get_available_slots(photographer_id, query_params):
    """
    Get available time slots for a photographer
    Query params: date (YYYY-MM-DD), timezone (optional)
    """
    try:
        # Verify photographer exists and has scheduler enabled
        user_response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('id').eq(photographer_id)
        )
        
        if not user_response.get('Items'):
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = user_response['Items'][0]
        
        # Check scheduler feature
        features, _, _ = get_user_features(photographer)
        if not features.get('scheduler'):
            return create_response(403, {'error': 'Online booking not available'})
        
        # Get date from query params
        date_str = query_params.get('date')
        if not date_str:
            return create_response(400, {'error': 'date parameter required (YYYY-MM-DD)'})
        
        try:
            requested_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return create_response(400, {'error': 'Invalid date format. Use YYYY-MM-DD'})
        
        # Get availability settings
        settings_response = availability_settings_table.get_item(Key={'user_id': photographer_id})
        
        if 'Item' in settings_response:
            settings = settings_response['Item']
        else:
            # Use defaults
            settings = {
                'timezone': 'America/New_York',
                'working_hours': {
                    'monday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'tuesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'wednesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'thursday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'friday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
                    'saturday': {'enabled': False, 'start': '10:00', 'end': '15:00'},
                    'sunday': {'enabled': False, 'start': '10:00', 'end': '15:00'}
                },
                'slot_duration': 60,
                'buffer_time': 15
            }
        
        # Get day of week
        day_name = requested_date.strftime('%A').lower()
        day_settings = settings['working_hours'].get(day_name, {'enabled': False})
        
        if not day_settings.get('enabled'):
            return create_response(200, {
                'date': date_str,
                'available_slots': [],
                'message': 'Not available on this day'
            })
        
        # Generate time slots based on working hours
        start_time_str = day_settings.get('start', '09:00')
        end_time_str = day_settings.get('end', '17:00')
        slot_duration = settings.get('slot_duration', 60)
        buffer_time = settings.get('buffer_time', 15)
        
        # Parse working hours
        start_hour, start_min = map(int, start_time_str.split(':'))
        end_hour, end_min = map(int, end_time_str.split(':'))
        
        work_start = datetime.combine(requested_date.date(), time(start_hour, start_min))
        work_end = datetime.combine(requested_date.date(), time(end_hour, end_min))
        
        # Generate all possible slots
        all_slots = []
        current_slot = work_start
        
        while current_slot + timedelta(minutes=slot_duration) <= work_end:
            all_slots.append({
                'start': current_slot.isoformat() + 'Z',
                'end': (current_slot + timedelta(minutes=slot_duration)).isoformat() + 'Z',
                'available': True
            })
            current_slot += timedelta(minutes=slot_duration + buffer_time)
        
        # Get existing appointments for this day
        day_start = requested_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        day_end = requested_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        
        existing_appointments = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        ).get('Items', [])
        
        # Filter appointments for this day that are not cancelled
        day_appointments = [
            appt for appt in existing_appointments
            if appt.get('status') != 'cancelled'
            and day_start <= appt.get('start_time', '') < day_end
        ]
        
        # Mark conflicting slots as unavailable
        for slot in all_slots:
            slot_start = slot['start']
            slot_end = slot['end']
            
            for appt in day_appointments:
                appt_start = appt.get('start_time')
                appt_end = appt.get('end_time')
                
                # Check if slot overlaps with appointment
                if appt_start and appt_end:
                    if (slot_start < appt_end and slot_end > appt_start):
                        slot['available'] = False
                        break
        
        # Filter to only available slots
        available_slots = [slot for slot in all_slots if slot['available']]
        
        return create_response(200, {
            'date': date_str,
            'photographer_id': photographer_id,
            'timezone': settings.get('timezone', 'America/New_York'),
            'available_slots': available_slots,
            'total_slots': len(all_slots),
            'available_count': len(available_slots)
        })
        
    except Exception as e:
        print(f"Error getting available slots: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get available slots'})


def handle_check_slot_availability(photographer_id, body):
    """
    Check if a specific time slot is available
    Body: { start_time, end_time }
    """
    try:
        start_time = body.get('start_time')
        end_time = body.get('end_time')
        
        if not start_time or not end_time:
            return create_response(400, {'error': 'start_time and end_time required'})
        
        # Get existing appointments
        existing = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        ).get('Items', [])
        
        # Check for conflicts
        for appt in existing:
            if appt.get('status') == 'cancelled':
                continue
            
            appt_start = appt.get('start_time')
            appt_end = appt.get('end_time')
            
            if appt_start and appt_end:
                # Check overlap
                if (start_time < appt_end and end_time > appt_start):
                    return create_response(200, {
                        'available': False,
                        'conflict': True,
                        'message': 'Time slot conflicts with existing appointment'
                    })
        
        return create_response(200, {
            'available': True,
            'conflict': False,
            'message': 'Time slot is available'
        })
        
    except Exception as e:
        print(f"Error checking slot availability: {str(e)}")
        return create_response(500, {'error': 'Failed to check availability'})


def handle_get_busy_times(photographer_id, query_params):
    """
    Get busy/booked times for calendar display
    Query params: start_date, end_date (ISO format)
    """
    try:
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        
        if not start_date or not end_date:
            return create_response(400, {'error': 'start_date and end_date required'})
        
        # Get appointments in date range
        appointments = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        ).get('Items', [])
        
        # Filter by date range and status
        busy_times = []
        for appt in appointments:
            if appt.get('status') == 'cancelled':
                continue
            
            appt_start = appt.get('start_time', '')
            if start_date <= appt_start <= end_date:
                busy_times.append({
                    'id': appt['id'],
                    'start': appt['start_time'],
                    'end': appt['end_time'],
                    'service_type': appt.get('service_type'),
                    'status': appt.get('status')
                })
        
        return create_response(200, {
            'busy_times': busy_times,
            'count': len(busy_times)
        })
        
    except Exception as e:
        print(f"Error getting busy times: {str(e)}")
        return create_response(500, {'error': 'Failed to get busy times'})


def handle_generate_ical_feed(photographer_id):
    """
    Generate iCal feed for calendar subscription
    Returns .ics content
    """
    try:
        # Verify photographer exists
        user_response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('id').eq(photographer_id)
        )
        
        if not user_response.get('Items'):
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = user_response['Items'][0]
        
        # Get all confirmed appointments
        appointments = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        ).get('Items', [])
        
        # Filter to confirmed/pending only
        appointments = [a for a in appointments if a.get('status') in ['confirmed', 'pending']]
        
        # Generate iCal content
        ical_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Galerly//Photographer Calendar//EN
X-WR-CALNAME:Galerly Bookings
X-WR-TIMEZONE:UTC
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
        
        for appt in appointments:
            # Format times for iCal (remove separators and timezone)
            start = appt.get('start_time', '').replace('-', '').replace(':', '').split('.')[0] + 'Z'
            end = appt.get('end_time', '').replace('-', '').replace(':', '').split('.')[0] + 'Z'
            created = appt.get('created_at', '').replace('-', '').replace(':', '').split('.')[0] + 'Z'
            
            ical_content += f"""BEGIN:VEVENT
UID:{appt['id']}@galerly.com
DTSTAMP:{created}
DTSTART:{start}
DTEND:{end}
SUMMARY:{appt.get('service_type', 'Appointment')} - {appt.get('client_name', 'Client')}
DESCRIPTION:Service: {appt.get('service_type', '')}\\nClient: {appt.get('client_name', '')}\\nEmail: {appt.get('client_email', '')}\\nNotes: {appt.get('notes', '')}
STATUS:{appt.get('status', 'CONFIRMED').upper()}
SEQUENCE:0
END:VEVENT
"""
        
        ical_content += "END:VCALENDAR"
        
        # Return as downloadable .ics file
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/calendar; charset=utf-8',
                'Content-Disposition': f'attachment; filename="galerly-calendar-{photographer_id}.ics"',
                'Access-Control-Allow-Origin': '*'
            },
            'body': ical_content
        }
        
    except Exception as e:
        print(f"Error generating iCal feed: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to generate calendar feed'})
