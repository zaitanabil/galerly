"""
Galerly - Newsletter Handler
Handles newsletter subscription management
"""
import re
from datetime import datetime
from utils.config import dynamodb
from utils.response import create_response
import os

# Initialize DynamoDB
newsletters_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NEWSLETTERS'))


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def handle_newsletter_subscribe(body):
    """
    Handle newsletter subscription
    
    POST /api/v1/newsletter/subscribe
    Body: {
        "email": "user@example.com",
        "firstName": "John"
    }
    """
    try:
        # Validate input
        email = body.get('email', '').strip().lower()
        first_name = body.get('firstName', '').strip()
        
        if not email:
            return create_response(400, {'error': 'Email is required'})
        
        if not validate_email(email):
            return create_response(400, {'error': 'Invalid email format'})
        
        if not first_name:
            return create_response(400, {'error': 'First name is required'})
        
        # Check if already subscribed
        try:
            response = newsletters_table.get_item(Key={'email': email})
            if 'Item' in response:
                existing = response['Item']
                if existing.get('status') == 'active':
                    return create_response(200, {
                        'message': 'You are already subscribed to our newsletter!',
                        'already_subscribed': True
                    })
                else:
                    # Reactivate subscription
                    newsletters_table.update_item(
                        Key={'email': email},
                        UpdateExpression='SET #status = :status, firstName = :firstName, subscribed_at = :subscribed_at',
                        ExpressionAttributeNames={
                            '#status': 'status'
                        },
                        ExpressionAttributeValues={
                            ':status': 'active',
                            ':firstName': first_name,
                            ':subscribed_at': datetime.utcnow().isoformat() + 'Z'
                        }
                    )
                    return create_response(200, {
                        'message': 'Welcome back! Your subscription has been reactivated.',
                        'reactivated': True
                    })
        except Exception as e:
            print(f"Error checking existing subscription: {str(e)}")
        
        # Create new subscription
        newsletters_table.put_item(
            Item={
                'email': email,
                'firstName': first_name,
                'subscribed_at': datetime.utcnow().isoformat() + 'Z',
                'status': 'active',
                'source': 'website',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        print(f"New newsletter subscription: {email}")
        
        return create_response(200, {
            'message': 'Thank you for subscribing! Welcome to the Galerly community.',
            'success': True
        })
        
    except Exception as e:
        print(f"Newsletter subscription error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to process subscription',
            'message': str(e)
        })


def handle_newsletter_unsubscribe(body):
    """
    Handle newsletter unsubscription
    
    POST /api/v1/newsletter/unsubscribe
    Body: {
        "email": "user@example.com"
    }
    """
    try:
        email = body.get('email', '').strip().lower()
        
        if not email:
            return create_response(400, {'error': 'Email is required'})
        
        if not validate_email(email):
            return create_response(400, {'error': 'Invalid email format'})
        
        # Update subscription status
        newsletters_table.update_item(
            Key={'email': email},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'unsubscribed',
                ':updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        print(f"Newsletter unsubscribed: {email}")
        
        return create_response(200, {
            'message': 'You have been unsubscribed from our newsletter.',
            'success': True
        })
        
    except Exception as e:
        print(f"Newsletter unsubscription error: {str(e)}")
        return create_response(500, {
            'error': 'Failed to process unsubscription',
            'message': str(e)
        })


def handle_get_newsletter_stats(user):
    """
    Get newsletter subscription stats (admin only)
    
    GET /api/v1/newsletter/stats
    """
    try:
        # This would be admin-only in production
        # For now, we'll return basic stats
        
        response = newsletters_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'active'
            },
            Select='COUNT'
        )
        
        active_count = response.get('Count', 0)
        
        return create_response(200, {
            'active_subscribers': active_count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        print(f"Newsletter stats error: {str(e)}")
        return create_response(500, {
            'error': 'Failed to retrieve stats',
            'message': str(e)
        })

