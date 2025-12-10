"""
Testimonials Handler
Manages client testimonials and reviews for photographer portfolios
Pro+ feature - requires Pro or Ultimate plan for management
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb
from utils.response import create_response
from handlers.subscription_handler import get_user_features
import os

# Initialize DynamoDB
testimonials_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_TESTIMONIALS'))


def handle_list_testimonials(photographer_id, query_params=None):
    """
    List testimonials for a photographer (public or authenticated)
    
    GET /api/v1/public/photographers/{photographer_id}/testimonials?approved=true
    """
    try:
        # Query testimonials for this photographer
        response = testimonials_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(photographer_id)
        )
        
        testimonials = response.get('Items', [])
        
        # Filter by approval status if not owner
        show_all = query_params and query_params.get('show_all') == 'true'
        if not show_all:
            testimonials = [t for t in testimonials if t.get('approved') == True]
        
        # Sort by rating (desc) then date (desc)
        testimonials.sort(key=lambda x: (x.get('rating', 0), x.get('created_at', '')), reverse=True)
        
        # Calculate average rating
        if testimonials:
            avg_rating = sum(t.get('rating', 0) for t in testimonials) / len(testimonials)
        else:
            avg_rating = 0
        
        return create_response(200, {
            'testimonials': testimonials,
            'stats': {
                'total': len(testimonials),
                'average_rating': round(avg_rating, 1),
                'five_star': len([t for t in testimonials if t.get('rating') == 5]),
                'four_star': len([t for t in testimonials if t.get('rating') == 4])
            }
        })
        
    except Exception as e:
        print(f"Error listing testimonials: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve testimonials'})


def handle_create_testimonial(photographer_id, body):
    """
    Create a new testimonial (from client or photographer)
    
    POST /api/v1/public/photographers/{photographer_id}/testimonials
    Body: {
        "client_name": "Jane Doe",
        "client_email": "jane@example.com",
        "service_type": "wedding",
        "rating": 5,
        "title": "Amazing experience!",
        "content": "The photographer was professional...",
        "event_date": "2024-06-15",
        "would_recommend": true,
        "display_photo": true
    }
    """
    try:
        # Validate required fields
        client_name = body.get('client_name', '').strip()
        rating = body.get('rating', 0)
        content = body.get('content', '').strip()
        
        if not client_name:
            return create_response(400, {'error': 'Client name is required'})
        if not rating or rating < 1 or rating > 5:
            return create_response(400, {'error': 'Rating must be between 1 and 5'})
        if not content or len(content) < 20:
            return create_response(400, {'error': 'Please provide detailed feedback (min 20 characters)'})
        
        # Create testimonial
        testimonial_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        testimonial = {
            'id': testimonial_id,
            'photographer_id': photographer_id,
            'client_name': client_name,
            'client_email': body.get('client_email', ''),
            'client_initial': client_name[0].upper() if client_name else '?',
            'service_type': body.get('service_type', ''),
            'rating': Decimal(str(rating)),
            'title': body.get('title', ''),
            'content': content,
            'event_date': body.get('event_date', ''),
            'would_recommend': body.get('would_recommend', True),
            'display_photo': body.get('display_photo', False),
            'photo_url': body.get('photo_url', ''),
            'approved': False,  # Requires photographer approval
            'featured': False,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        testimonials_table.put_item(Item=testimonial)
        
        print(f"New testimonial created: {testimonial_id} for photographer {photographer_id}")
        
        return create_response(200, {
            'success': True,
            'message': 'Thank you for your feedback! Your testimonial is pending approval.',
            'testimonial_id': testimonial_id
        })
        
    except Exception as e:
        print(f"Error creating testimonial: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to submit testimonial'})


def handle_update_testimonial(user, testimonial_id, body):
    """
    Update testimonial (photographer only - for approval/featuring) - Pro+ feature
    
    PUT /api/v1/crm/testimonials/{id}
    Body: {
        "approved": true,
        "featured": true
    }
    """
    try:
        # Check plan permission - Pro+ feature
        features, _, _ = get_user_features(user)
        if not features.get('client_invoicing'):  # Testimonials bundled with CRM (Pro+)
            return create_response(403, {
                'error': 'Testimonial management is a Pro feature',
                'upgrade_required': True,
                'required_feature': 'client_invoicing'
            })
        
        # Get existing testimonial
        response = testimonials_table.get_item(Key={'id': testimonial_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Testimonial not found'})
        
        testimonial = response['Item']
        
        # Verify ownership
        if testimonial['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Build update expression
        update_fields = []
        expr_values = {}
        
        if 'approved' in body:
            update_fields.append('approved = :approved')
            expr_values[':approved'] = body['approved']
        
        if 'featured' in body:
            update_fields.append('featured = :featured')
            expr_values[':featured'] = body['featured']
        
        if not update_fields:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update timestamp
        update_fields.append('updated_at = :updated_at')
        expr_values[':updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Execute update
        update_expression = 'SET ' + ', '.join(update_fields)
        
        result = testimonials_table.update_item(
            Key={'id': testimonial_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        return create_response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating testimonial: {str(e)}")
        return create_response(500, {'error': 'Failed to update testimonial'})


def handle_delete_testimonial(user, testimonial_id):
    """Delete a testimonial (photographer only) - Pro+ feature"""
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('client_invoicing'):
            return create_response(403, {
                'error': 'Testimonial management is a Pro feature',
                'upgrade_required': True
            })
        
        # Get testimonial to verify ownership
        response = testimonials_table.get_item(Key={'id': testimonial_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Testimonial not found'})
        
        testimonial = response['Item']
        
        # Verify ownership
        if testimonial['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Delete testimonial
        testimonials_table.delete_item(Key={'id': testimonial_id})
        
        return create_response(200, {'message': 'Testimonial deleted'})
        
    except Exception as e:
        print(f"Error deleting testimonial: {str(e)}")
        return create_response(500, {'error': 'Failed to delete testimonial'})


def handle_request_testimonial(user, body):
    """
    Send testimonial request email to a client - Pro+ feature
    
    POST /api/v1/crm/testimonials/request
    Body: {
        "client_name": "Jane Doe",
        "client_email": "jane@example.com",
        "service_type": "wedding",
        "custom_message": "Thank you for choosing us..."
    }
    """
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('client_invoicing'):
            return create_response(403, {
                'error': 'Testimonial requests are a Pro feature',
                'upgrade_required': True
            })
        
        from utils.email import send_email
        
        client_name = body.get('client_name', '').strip()
        client_email = body.get('client_email', '').strip()
        service_type = body.get('service_type', '')
        custom_message = body.get('custom_message', '')
        
        if not client_email:
            return create_response(400, {'error': 'Client email is required'})
        
        # Generate unique testimonial submission link
        testimonial_token = str(uuid.uuid4())
        frontend_url = os.environ.get('FRONTEND_URL')
        submission_link = f"{frontend_url}/testimonial/{user['id']}?token={testimonial_token}"
        
        # Send email
        photographer_name = user.get('name', 'your photographer')
        
        email_body_html = f"""
        <h2>Share Your Experience</h2>
        <p>Hi {client_name},</p>
        <p>{custom_message or f"Thank you for choosing {photographer_name} for your {service_type}!"}</p>
        <p>We'd love to hear about your experience. Your feedback helps us improve and helps others find the right photographer for their needs.</p>
        <p><a href="{submission_link}" style="display: inline-block; padding: 12px 24px; background-color: #0066CC; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0;">Leave Your Testimonial</a></p>
        <p>Thank you!<br>{photographer_name}</p>
        """
        
        send_email(
            to_addresses=[client_email],
            subject=f"We'd love your feedback - {photographer_name}",
            body_html=email_body_html,
            body_text=f"Hi {client_name}, We'd love to hear about your experience. Please visit {submission_link} to leave your testimonial. Thank you!"
        )
        
        return create_response(200, {
            'success': True,
            'message': 'Testimonial request sent',
            'submission_link': submission_link
        })
        
    except Exception as e:
        print(f"Error requesting testimonial: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to send testimonial request'})
