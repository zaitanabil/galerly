"""
Galerly - Contact/Support Handler
Handles contact form submissions and support tickets
"""
import uuid
import re
from datetime import datetime
from utils.config import dynamodb
from utils.response import create_response
import os

# Initialize DynamoDB
contact_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_CONTACT'))


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def handle_contact_submit(body):
    """
    Handle contact form submission
    
    POST /api/v1/contact/submit
    Body: {
        "name": "John Doe",
        "email": "john@example.com",
        "issueType": "account",
        "message": "Description of the issue"
    }
    """
    try:
        # Validate input
        name = body.get('name', '').strip()
        email = body.get('email', '').strip().lower()
        issue_type = body.get('issueType', '').strip()
        message = body.get('message', '').strip()
        
        # Validation
        if not name:
            return create_response(400, {'error': 'Name is required'})
        
        if not email:
            return create_response(400, {'error': 'Email is required'})
        
        if not validate_email(email):
            return create_response(400, {'error': 'Invalid email format'})
        
        if not issue_type:
            return create_response(400, {'error': 'Issue type is required'})
        
        valid_issue_types = ['account', 'gallery', 'upload', 'sharing', 'billing', 'technical', 'other']
        if issue_type not in valid_issue_types:
            return create_response(400, {'error': 'Invalid issue type'})
        
        if not message or len(message) < 10:
            return create_response(400, {'error': 'Please provide a detailed description (min 10 characters)'})
        
        if len(message) > 5000:
            return create_response(400, {'error': 'Message is too long (max 5000 characters)'})
        
        # Create ticket
        ticket_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        ticket = {
            'id': ticket_id,
            'name': name,
            'email': email,
            'issue_type': issue_type,
            'message': message,
            'status': 'new',
            'created_at': timestamp,
            'updated_at': timestamp,
            'source': 'website'
        }
        
        contact_table.put_item(Item=ticket)
        
        print(f"New support ticket: {ticket_id} from {email}")
        
        return create_response(200, {
            'message': 'Thank you for contacting us. We\'ll get back to you shortly.',
            'ticket_id': ticket_id,
            'success': True
        })
        
    except Exception as e:
        print(f"Contact form error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to submit your request',
            'message': str(e)
        })


def handle_get_tickets(user):
    """
    Get all support tickets (admin only)
    
    GET /api/v1/contact/tickets?status=new
    """
    try:
        # This would be admin-only in production
        # For now, return basic stats
        
        response = contact_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'new'
            }
        )
        
        tickets = response.get('Items', [])
        
        # Sort by created_at
        tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return create_response(200, {
            'tickets': tickets[:50],  # Limit to 50 most recent
            'count': len(tickets)
        })
        
    except Exception as e:
        print(f"Get tickets error: {str(e)}")
        return create_response(500, {
            'error': 'Failed to retrieve tickets',
            'message': str(e)
        })


def handle_update_ticket_status(ticket_id, body, user):
    """
    Update ticket status (admin only)
    
    PUT /api/v1/contact/tickets/{id}
    Body: { "status": "resolved" }
    """
    try:
        status = body.get('status', '').strip()
        
        valid_statuses = ['new', 'in_progress', 'resolved', 'closed']
        if status not in valid_statuses:
            return create_response(400, {'error': 'Invalid status'})
        
        contact_table.update_item(
            Key={'id': ticket_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        print(f"Ticket {ticket_id} updated to {status}")
        
        return create_response(200, {
            'message': 'Ticket status updated',
            'status': status
        })
        
    except Exception as e:
        print(f"Update ticket error: {str(e)}")
        return create_response(500, {
            'error': 'Failed to update ticket',
            'message': str(e)
        })

