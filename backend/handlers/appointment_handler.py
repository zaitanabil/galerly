"""
Appointment scheduler handlers
"""
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import appointments_table, users_table
from utils.response import create_response
from utils.email import send_email

def handle_list_appointments(user, query_params=None):
    """List appointments for user"""
    try:
        response = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        appointments = response.get('Items', [])
        # Sort by start_time
        appointments.sort(key=lambda x: x.get('start_time', ''))
        return create_response(200, {'appointments': appointments})
    except Exception as e:
        print(f"Error listing appointments: {str(e)}")
        return create_response(500, {'error': 'Failed to list appointments'})

def handle_create_appointment(user, body):
    """Create new appointment (Photographer initiated - Auto Confirmed)"""
    try:
        # Check Plan Limits
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('scheduler'):
             return create_response(403, {
                 'error': 'Scheduling is available on the Ultimate plan.',
                 'upgrade_required': True
             })

        # Validate
        required = ['client_email', 'start_time', 'end_time', 'service_type']
        if not all(k in body for k in required):
            return create_response(400, {'error': 'Missing required fields'})
            
        # Basic overlap check (naive)
        start = body['start_time']
        end = body['end_time']
        
        # Query existing appointments for this user
        existing = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id'])
        ).get('Items', [])
        
        for appt in existing:
            if appt.get('status') == 'cancelled': continue
            # Check overlap
            existing_start = appt.get('start_time')
            existing_end = appt.get('end_time')
            if existing_start and existing_end:
                if (start < existing_end and end > existing_start):
                    return create_response(409, {'error': 'Time slot conflict'})
        
        appt_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        appointment = {
            'id': appt_id,
            'user_id': user['id'],
            'client_name': body.get('client_name', ''),
            'client_email': body['client_email'],
            'start_time': start,
            'end_time': end,
            'service_type': body['service_type'],
            'status': 'confirmed',
            'notes': body.get('notes', ''),
            'created_at': current_time,
            'updated_at': current_time
        }
        
        appointments_table.put_item(Item=appointment)
        
        # Send confirmation email
        try:
            photographer_name = user.get('name', 'Your Photographer')
            send_email(
                to_addresses=[body['client_email']],
                subject=f"Appointment Confirmed: {body['service_type']}",
                body_html=f"<p>Hi {body.get('client_name','')},</p><p>Your appointment for <strong>{body['service_type']}</strong> with {photographer_name} is confirmed for {start}.</p>",
                body_text=f"Hi {body.get('client_name','')}, Your appointment for {body['service_type']} with {photographer_name} is confirmed for {start}."
            )
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")
            
        return create_response(201, appointment)
    except Exception as e:
        print(f"Error creating appointment: {str(e)}")
        return create_response(500, {'error': 'Failed to create appointment'})

def handle_create_public_appointment_request(photographer_id, body):
    """Create new appointment request (Client initiated - Pending)"""
    try:
        # Verify photographer exists
        user_response = users_table.get_item(Key={'id': photographer_id})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = user_response['Item']
        
        # Check if photographer has scheduler feature
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(photographer)
        
        if not features.get('scheduler'):
             return create_response(403, {
                 'error': 'This photographer does not have online booking enabled.'
             })
        
        # Validate
        required = ['client_name', 'client_email', 'start_time', 'end_time', 'service_type']
        if not all(k in body for k in required):
            return create_response(400, {'error': 'Missing required fields'})
            
        start = body['start_time']
        end = body['end_time']
        
        # Basic overlap check with existing confirmed appointments
        existing = appointments_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        ).get('Items', [])
        
        for appt in existing:
            if appt.get('status') == 'cancelled': continue
            existing_start = appt.get('start_time')
            existing_end = appt.get('end_time')
            if existing_start and existing_end:
                if (start < existing_end and end > existing_start):
                    return create_response(409, {'error': 'Time slot conflict'})
        
        appt_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        appointment = {
            'id': appt_id,
            'user_id': photographer_id,
            'client_name': body['client_name'],
            'client_email': body['client_email'],
            'start_time': start,
            'end_time': end,
            'service_type': body['service_type'],
            'status': 'pending', # Pending approval
            'notes': body.get('notes', ''),
            'created_at': current_time,
            'updated_at': current_time,
            'source': 'public_booking'
        }
        
        appointments_table.put_item(Item=appointment)
        
        # Send notification to Photographer
        try:
            send_email(
                to_addresses=[photographer['email']],
                subject=f"New Booking Request: {body['service_type']}",
                body_html=f"""
                <h2>New Booking Request</h2>
                <p><strong>Client:</strong> {body['client_name']} ({body['client_email']})</p>
                <p><strong>Service:</strong> {body['service_type']}</p>
                <p><strong>Time:</strong> {start}</p>
                <p><strong>Notes:</strong> {body.get('notes', 'None')}</p>
                <p>Please log in to your dashboard to confirm or decline.</p>
                """,
                body_text=f"New Booking Request from {body['client_name']} for {body['service_type']} at {start}."
            )
        except Exception as e:
            print(f"Failed to notify photographer: {str(e)}")
            
        # Send acknowledgement to Client
        try:
            send_email(
                to_addresses=[body['client_email']],
                subject=f"Booking Request Received: {body['service_type']}",
                body_html=f"<p>Hi {body['client_name']},</p><p>We have received your booking request for <strong>{body['service_type']}</strong> with {photographer.get('name', 'the photographer')}.</p><p>You will receive a confirmation once the request is approved.</p>",
                body_text=f"Hi {body['client_name']}, We have received your booking request. You will receive a confirmation once approved."
            )
        except Exception as e:
            print(f"Failed to send acknowledgement email: {str(e)}")
            
        return create_response(201, appointment)
    except Exception as e:
        print(f"Error creating appointment request: {str(e)}")
        return create_response(500, {'error': 'Failed to submit booking request'})

def handle_update_appointment(appt_id, user, body):
    """Update appointment"""
    try:
        response = appointments_table.get_item(Key={'id': appt_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Appointment not found'})
            
        appt = response['Item']
        if appt['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        fields = ['status', 'notes', 'start_time', 'end_time']
        old_status = appt.get('status')
        new_status = body.get('status')
        
        for f in fields:
            if f in body:
                appt[f] = body[f]
                
        appt['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        appointments_table.put_item(Item=appt)
        
        # If status changed to confirmed/cancelled, notify client
        if new_status and new_status != old_status:
            try:
                subject = f"Appointment Update: {appt.get('service_type')}"
                msg = f"Your appointment status has been updated to: {new_status.upper()}."
                if new_status == 'confirmed':
                    msg = f"Good news! Your appointment for {appt.get('service_type')} has been confirmed."
                elif new_status == 'cancelled':
                    msg = f"Your appointment for {appt.get('service_type')} has been cancelled."
                    
                send_email(
                    to_addresses=[appt['client_email']],
                    subject=subject,
                    body_html=f"<p>Hi {appt.get('client_name', '')},</p><p>{msg}</p>",
                    body_text=f"Hi {appt.get('client_name', '')}, {msg}"
                )
            except Exception as e:
                print(f"Failed to send update email: {str(e)}")
        
        return create_response(200, appt)
    except Exception as e:
        print(f"Error updating appointment: {str(e)}")
        return create_response(500, {'error': 'Failed to update appointment'})

def handle_delete_appointment(appt_id, user):
    """Delete/Cancel appointment"""
    try:
        response = appointments_table.get_item(Key={'id': appt_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Appointment not found'})
            
        if response['Item']['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        appointments_table.delete_item(Key={'id': appt_id})
        return create_response(200, {'message': 'Appointment deleted'})
    except Exception as e:
        print(f"Error deleting appointment: {str(e)}")
        return create_response(500, {'error': 'Failed to delete appointment'})
