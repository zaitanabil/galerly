"""
Leads & CRM Handler
Manages lead capture, scoring, and follow-up automation
Pro/Ultimate plan feature
"""
import uuid
import re
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, users_table
from utils.response import create_response
from utils.email import send_email
import os

# Initialize DynamoDB tables
leads_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_LEADS'))
followup_sequences_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_FOLLOWUP_SEQUENCES'))


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def calculate_lead_score(lead_data):
    """
    Calculate lead quality score (0-100)
    
    Scoring factors:
    - Source quality: 0-20 points
    - Message quality: 0-20 points
    - Service interest: 0-20 points
    - Budget indication: 0-20 points
    - Timeline urgency: 0-20 points
    """
    score = 0
    
    # Source quality (20 points)
    source = lead_data.get('source', '')
    source_scores = {
        'portfolio_contact': 20,
        'booking_request': 18,
        'pricing_inquiry': 15,
        'website_contact': 12,
        'newsletter': 8,
        'other': 5
    }
    score += source_scores.get(source, 5)
    
    # Message quality (20 points)
    message = lead_data.get('message', '')
    if len(message) > 200:
        score += 20
    elif len(message) > 100:
        score += 15
    elif len(message) > 50:
        score += 10
    else:
        score += 5
    
    # Service interest specificity (20 points)
    service_type = lead_data.get('service_type', '')
    if service_type and service_type != 'other':
        score += 20
    elif service_type:
        score += 10
    
    # Budget indication (20 points)
    budget = lead_data.get('budget', '')
    budget_scores = {
        '5000+': 20,
        '3000-5000': 18,
        '1000-3000': 15,
        '500-1000': 10,
        'not_specified': 5
    }
    score += budget_scores.get(budget, 5)
    
    # Timeline urgency (20 points)
    timeline = lead_data.get('timeline', '')
    timeline_scores = {
        'within_week': 20,
        'within_month': 18,
        '1-3_months': 15,
        '3-6_months': 10,
        '6+_months': 5,
        'not_specified': 3
    }
    score += timeline_scores.get(timeline, 3)
    
    return min(100, score)


def handle_capture_lead(photographer_id, body):
    """
    Capture a new lead from portfolio contact form or booking request
    
    POST /api/v1/public/photographers/{photographer_id}/lead
    Body: {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1234567890",
        "service_type": "wedding",
        "budget": "3000-5000",
        "timeline": "within_month",
        "event_date": "2025-06-15",
        "message": "Looking for wedding photographer...",
        "source": "portfolio_contact",
        "referral_source": "google"
    }
    """
    try:
        # Verify photographer exists
        user_response = users_table.get_item(Key={'id': photographer_id})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = user_response['Item']
        
        # Validate required fields
        name = body.get('name', '').strip()
        email = body.get('email', '').strip().lower()
        message = body.get('message', '').strip()
        
        if not name:
            return create_response(400, {'error': 'Name is required'})
        if not email:
            return create_response(400, {'error': 'Email is required'})
        if not validate_email(email):
            return create_response(400, {'error': 'Invalid email format'})
        if not message or len(message) < 10:
            return create_response(400, {'error': 'Please provide more details (min 10 characters)'})
        
        # Create lead entry
        lead_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        lead = {
            'id': lead_id,
            'photographer_id': photographer_id,
            'name': name,
            'email': email,
            'phone': body.get('phone', ''),
            'service_type': body.get('service_type', ''),
            'budget': body.get('budget', 'not_specified'),
            'timeline': body.get('timeline', 'not_specified'),
            'event_date': body.get('event_date', ''),
            'message': message,
            'source': body.get('source', 'website_contact'),
            'referral_source': body.get('referral_source', ''),
            'status': 'new',
            'tags': body.get('tags', []),
            'notes': [],
            'created_at': timestamp,
            'updated_at': timestamp,
            'last_contacted_at': None,
            'follow_up_count': 0
        }
        
        # Calculate lead score
        lead['score'] = calculate_lead_score(lead)
        
        # Determine quality tier
        if lead['score'] >= 80:
            lead['quality'] = 'hot'
        elif lead['score'] >= 60:
            lead['quality'] = 'warm'
        elif lead['score'] >= 40:
            lead['quality'] = 'cold'
        else:
            lead['quality'] = 'low'
        
        leads_table.put_item(Item=lead)
        
        # Send notification to photographer
        try:
            photographer_email = photographer.get('email')
            photographer_name = photographer.get('name', 'there')
            
            if photographer_email:
                send_email(
                    to_addresses=[photographer_email],
                    subject=f"New {lead['quality'].upper()} Lead: {name}",
                    body_html=f"""
                    <h2>New Lead Captured!</h2>
                    <p>Hi {photographer_name},</p>
                    <p>You have a new <strong>{lead['quality']}</strong> quality lead:</p>
                    <ul>
                        <li><strong>Name:</strong> {name}</li>
                        <li><strong>Email:</strong> {email}</li>
                        <li><strong>Phone:</strong> {lead['phone'] or 'Not provided'}</li>
                        <li><strong>Service:</strong> {lead['service_type'] or 'Not specified'}</li>
                        <li><strong>Budget:</strong> ${lead['budget']}</li>
                        <li><strong>Timeline:</strong> {lead['timeline']}</li>
                        <li><strong>Lead Score:</strong> {lead['score']}/100</li>
                    </ul>
                    <p><strong>Message:</strong></p>
                    <p>{message}</p>
                    <p><a href="{os.environ.get('FRONTEND_URL')}/crm/leads/{lead_id}">View Lead Details</a></p>
                    """,
                    body_text=f"New {lead['quality']} lead from {name} ({email}). Score: {lead['score']}/100. Message: {message}"
                )
        except Exception as email_error:
            print(f"Failed to send lead notification: {str(email_error)}")
        
        # Trigger automated follow-up sequence
        try:
            handle_trigger_followup_sequence(photographer_id, lead_id, lead['quality'])
        except Exception as seq_error:
            print(f"Failed to trigger follow-up sequence: {str(seq_error)}")
        
        print(f"New lead captured: {lead_id} for photographer {photographer_id}")
        
        return create_response(200, {
            'success': True,
            'message': 'Thank you for your inquiry! We\'ll be in touch soon.',
            'lead_id': lead_id
        })
        
    except Exception as e:
        print(f"Error capturing lead: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to submit inquiry'})


def handle_list_leads(user, query_params=None):
    """
    List leads for photographer with filtering
    
    GET /api/v1/crm/leads?status=new&quality=hot&limit=50
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('client_invoicing'):  # CRM is bundled with invoicing (Pro+)
            return create_response(403, {
                'error': 'CRM features are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Get query parameters
        status = query_params.get('status') if query_params else None
        quality = query_params.get('quality') if query_params else None
        limit = int(query_params.get('limit', 50)) if query_params else 50
        
        # Query leads for this photographer
        response = leads_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(user['id']),
            ScanIndexForward=False  # Most recent first
        )
        
        leads = response.get('Items', [])
        
        # Apply filters
        if status:
            leads = [l for l in leads if l.get('status') == status]
        if quality:
            leads = [l for l in leads if l.get('quality') == quality]
        
        # Limit results
        leads = leads[:limit]
        
        # Calculate stats
        total_leads = len(leads)
        hot_leads = len([l for l in leads if l.get('quality') == 'hot'])
        warm_leads = len([l for l in leads if l.get('quality') == 'warm'])
        new_leads = len([l for l in leads if l.get('status') == 'new'])
        
        return create_response(200, {
            'leads': leads,
            'stats': {
                'total': total_leads,
                'hot': hot_leads,
                'warm': warm_leads,
                'new': new_leads
            }
        })
        
    except Exception as e:
        print(f"Error listing leads: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve leads'})


def handle_get_lead(user, lead_id):
    """Get single lead details"""
    try:
        response = leads_table.get_item(Key={'id': lead_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Lead not found'})
        
        lead = response['Item']
        
        # Verify ownership
        if lead['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        return create_response(200, lead)
        
    except Exception as e:
        print(f"Error getting lead: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve lead'})


def handle_update_lead(user, lead_id, body):
    """
    Update lead status, notes, tags
    
    PUT /api/v1/crm/leads/{id}
    Body: {
        "status": "contacted",
        "notes": "Spoke with client, interested in wedding package",
        "tags": ["wedding", "summer_2025", "high_priority"]
    }
    """
    try:
        # Get existing lead
        response = leads_table.get_item(Key={'id': lead_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Lead not found'})
        
        lead = response['Item']
        
        # Verify ownership
        if lead['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Build update expression
        update_fields = []
        expr_values = {}
        expr_names = {}
        
        if 'status' in body:
            valid_statuses = ['new', 'contacted', 'qualified', 'proposal_sent', 'negotiating', 'won', 'lost']
            if body['status'] in valid_statuses:
                update_fields.append('#status = :status')
                expr_names['#status'] = 'status'
                expr_values[':status'] = body['status']
        
        if 'notes' in body and body['notes']:
            # Append note to notes array
            new_note = {
                'id': str(uuid.uuid4()),
                'text': body['notes'],
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'created_by': user['id']
            }
            current_notes = lead.get('notes', [])
            current_notes.append(new_note)
            update_fields.append('notes = :notes')
            expr_values[':notes'] = current_notes
        
        if 'tags' in body:
            update_fields.append('tags = :tags')
            expr_values[':tags'] = body['tags']
        
        if 'last_contacted_at' in body:
            update_fields.append('last_contacted_at = :last_contacted')
            expr_values[':last_contacted'] = body['last_contacted_at']
            update_fields.append('follow_up_count = follow_up_count + :inc')
            expr_values[':inc'] = 1
        
        if not update_fields:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update timestamp
        update_fields.append('updated_at = :updated_at')
        expr_values[':updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Execute update
        update_expression = 'SET ' + ', '.join(update_fields)
        
        kwargs = {
            'Key': {'id': lead_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expr_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expr_names:
            kwargs['ExpressionAttributeNames'] = expr_names
        
        result = leads_table.update_item(**kwargs)
        
        return create_response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating lead: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update lead'})


def handle_trigger_followup_sequence(photographer_id, lead_id, lead_quality):
    """
    Trigger automated follow-up email sequence
    
    Sequences:
    - Hot leads: Immediate + 1 day + 3 days
    - Warm leads: 1 day + 3 days + 7 days
    - Cold leads: 3 days + 7 days + 14 days
    """
    try:
        sequence_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Define email schedule based on quality
        if lead_quality == 'hot':
            schedule = [
                {'delay_hours': 0, 'template': 'immediate_response'},
                {'delay_hours': 24, 'template': 'followup_1'},
                {'delay_hours': 72, 'template': 'followup_2'}
            ]
        elif lead_quality == 'warm':
            schedule = [
                {'delay_hours': 24, 'template': 'warm_intro'},
                {'delay_hours': 72, 'template': 'followup_1'},
                {'delay_hours': 168, 'template': 'followup_2'}
            ]
        else:  # cold or low
            schedule = [
                {'delay_hours': 72, 'template': 'cold_intro'},
                {'delay_hours': 168, 'template': 'followup_1'},
                {'delay_hours': 336, 'template': 'followup_2'}
            ]
        
        # Create sequence entry
        sequence = {
            'id': sequence_id,
            'photographer_id': photographer_id,
            'lead_id': lead_id,
            'quality': lead_quality,
            'schedule': schedule,
            'status': 'active',
            'current_step': 0,
            'emails_sent': 0,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        followup_sequences_table.put_item(Item=sequence)
        
        print(f"Follow-up sequence {sequence_id} triggered for lead {lead_id}")
        
        return True
        
    except Exception as e:
        print(f"Error triggering follow-up sequence: {str(e)}")
        return False


def handle_process_followup_sequences(event, context):
    """
    Process pending follow-up emails (scheduled Lambda)
    Runs every hour to check and send scheduled emails
    """
    try:
        # Scan for active sequences
        response = followup_sequences_table.scan(
            FilterExpression=Attr('status').eq('active')
        )
        
        sequences = response.get('Items', [])
        processed = 0
        
        for sequence in sequences:
            try:
                current_step = sequence.get('current_step', 0)
                schedule = sequence.get('schedule', [])
                
                if current_step >= len(schedule):
                    # Sequence completed
                    followup_sequences_table.update_item(
                        Key={'id': sequence['id']},
                        UpdateExpression='SET #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': 'completed'}
                    )
                    continue
                
                # Get lead details
                lead_response = leads_table.get_item(Key={'id': sequence['lead_id']})
                if 'Item' not in lead_response:
                    continue
                
                lead = lead_response['Item']
                
                # Check if it's time to send next email
                created_at = datetime.fromisoformat(sequence['created_at'].replace('Z', '+00:00'))
                delay_hours = schedule[current_step]['delay_hours']
                send_time = created_at + timedelta(hours=delay_hours)
                
                if datetime.utcnow() >= send_time.replace(tzinfo=None):
                    # Send email
                    template = schedule[current_step]['template']
                    
                    # Get photographer details
                    photographer_response = users_table.get_item(
                        Key={'id': sequence['photographer_id']}
                    )
                    photographer = photographer_response['Item']
                    
                    # Send follow-up email (simplified)
                    send_email(
                        to_addresses=[lead['email']],
                        subject=f"Follow-up from {photographer.get('name', 'your photographer')}",
                        body_html=f"<p>Hi {lead['name']},</p><p>Following up on your inquiry...</p>",
                        body_text=f"Hi {lead['name']}, Following up on your inquiry..."
                    )
                    
                    # Update sequence
                    followup_sequences_table.update_item(
                        Key={'id': sequence['id']},
                        UpdateExpression='SET current_step = current_step + :inc, emails_sent = emails_sent + :inc, updated_at = :updated_at',
                        ExpressionAttributeValues={
                            ':inc': 1,
                            ':updated_at': datetime.utcnow().isoformat() + 'Z'
                        }
                    )
                    
                    # Update lead
                    leads_table.update_item(
                        Key={'id': lead['id']},
                        UpdateExpression='SET last_contacted_at = :timestamp, follow_up_count = follow_up_count + :inc',
                        ExpressionAttributeValues={
                            ':timestamp': datetime.utcnow().isoformat() + 'Z',
                            ':inc': 1
                        }
                    )
                    
                    processed += 1
                    
            except Exception as seq_error:
                print(f"Error processing sequence {sequence.get('id')}: {str(seq_error)}")
                continue
        
        print(f"Processed {processed} follow-up emails")
        
        return {
            'statusCode': 200,
            'body': f'Processed {processed} emails'
        }
        
    except Exception as e:
        print(f"Error processing follow-up sequences: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': 'Error processing sequences'
        }


def handle_cancel_followup_sequence(user, lead_id):
    """Cancel automated follow-up sequence for a lead"""
    try:
        # Find sequence for this lead
        response = followup_sequences_table.scan(
            FilterExpression=Attr('lead_id').eq(lead_id) & Attr('photographer_id').eq(user['id']) & Attr('status').eq('active')
        )
        
        sequences = response.get('Items', [])
        
        for sequence in sequences:
            followup_sequences_table.update_item(
                Key={'id': sequence['id']},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'cancelled',
                    ':updated_at': datetime.utcnow().isoformat() + 'Z'
                }
            )
        
        return create_response(200, {'message': 'Follow-up sequence cancelled'})
        
    except Exception as e:
        print(f"Error cancelling follow-up: {str(e)}")
        return create_response(500, {'error': 'Failed to cancel sequence'})
