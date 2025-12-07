"""
Client Feedback Handler
Structured feedback collection for galleries
"""
import uuid
import re
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table
from utils.response import create_response

# Initialize DynamoDB
import boto3
import os
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))
client_feedback_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_CLIENT_FEEDBACK'))


def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def handle_submit_client_feedback(gallery_id, body):
    """
    Submit structured client feedback for a gallery
    
    POST /api/v1/client/feedback/{gallery_id}
    Body: {
        "client_name": "John Doe",
        "client_email": "john@example.com",
        "overall_rating": 5,
        "photo_quality_rating": 5,
        "delivery_time_rating": 4,
        "communication_rating": 5,
        "value_rating": 5,
        "would_recommend": true,
        "comments": "Great work!",
        "photo_feedback": [
            {"photo_id": "123", "rating": 5, "comment": "Love this one!"}
        ]
    }
    """
    try:
        # Validate gallery exists and get owner
        # Use GalleryIdIndex to find gallery
        gallery_response = galleries_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('id').eq(gallery_id)
        )
        
        if not gallery_response.get('Items'):
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Items'][0]
        photographer_id = gallery.get('user_id')
        
        # Validate input
        client_name = body.get('client_name', '').strip()
        client_email = body.get('client_email', '').strip().lower()
        overall_rating = body.get('overall_rating')
        comments = body.get('comments', '').strip()
        
        # Validation
        if not client_name:
            return create_response(400, {'error': 'Name is required'})
        
        if not client_email:
            return create_response(400, {'error': 'Email is required'})
        
        if not validate_email(client_email):
            return create_response(400, {'error': 'Invalid email format'})
        
        if overall_rating is None:
            return create_response(400, {'error': 'Overall rating is required'})
        
        if not isinstance(overall_rating, int) or overall_rating < 1 or overall_rating > 5:
            return create_response(400, {'error': 'Overall rating must be between 1 and 5'})
        
        # Validate optional ratings
        photo_quality_rating = body.get('photo_quality_rating')
        if photo_quality_rating is not None:
            if not isinstance(photo_quality_rating, int) or photo_quality_rating < 1 or photo_quality_rating > 5:
                return create_response(400, {'error': 'Photo quality rating must be between 1 and 5'})
        
        delivery_time_rating = body.get('delivery_time_rating')
        if delivery_time_rating is not None:
            if not isinstance(delivery_time_rating, int) or delivery_time_rating < 1 or delivery_time_rating > 5:
                return create_response(400, {'error': 'Delivery time rating must be between 1 and 5'})
        
        communication_rating = body.get('communication_rating')
        if communication_rating is not None:
            if not isinstance(communication_rating, int) or communication_rating < 1 or communication_rating > 5:
                return create_response(400, {'error': 'Communication rating must be between 1 and 5'})
        
        value_rating = body.get('value_rating')
        if value_rating is not None:
            if not isinstance(value_rating, int) or value_rating < 1 or value_rating > 5:
                return create_response(400, {'error': 'Value rating must be between 1 and 5'})
        
        if len(comments) > 5000:
            return create_response(400, {'error': 'Comments are too long (max 5000 characters)'})
        
        # Validate photo feedback if provided
        photo_feedback = body.get('photo_feedback', [])
        if not isinstance(photo_feedback, list):
            return create_response(400, {'error': 'Photo feedback must be an array'})
        
        for pf in photo_feedback:
            if not isinstance(pf, dict):
                return create_response(400, {'error': 'Invalid photo feedback format'})
            if 'photo_id' not in pf:
                return create_response(400, {'error': 'Photo feedback must include photo_id'})
            if 'rating' in pf:
                rating = pf.get('rating')
                if not isinstance(rating, int) or rating < 1 or rating > 5:
                    return create_response(400, {'error': 'Photo rating must be between 1 and 5'})
        
        # Create feedback record
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        feedback = {
            'id': feedback_id,
            'gallery_id': gallery_id,
            'photographer_id': photographer_id,
            'client_name': client_name,
            'client_email': client_email,
            'overall_rating': overall_rating,
            'photo_quality_rating': photo_quality_rating,
            'delivery_time_rating': delivery_time_rating,
            'communication_rating': communication_rating,
            'value_rating': value_rating,
            'would_recommend': body.get('would_recommend', False),
            'comments': comments,
            'photo_feedback': photo_feedback,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        client_feedback_table.put_item(Item=feedback)
        
        print(f"Client feedback submitted: {feedback_id} for gallery {gallery_id}")
        
        return create_response(200, {
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback_id,
            'success': True
        })
        
    except Exception as e:
        print(f"Client feedback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to submit feedback',
            'message': str(e)
        })


def handle_get_gallery_feedback(gallery_id, user):
    """
    Get feedback for a gallery (photographer only)
    
    GET /api/v1/client/feedback/{gallery_id}
    """
    try:
        # Verify gallery ownership
        gallery_response = galleries_table.get_item(Key={
            'user_id': user['id'],
            'id': gallery_id
        })
        
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        # Get feedback for this gallery
        response = client_feedback_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        
        feedback_items = response.get('Items', [])
        
        # Sort by created_at (newest first)
        feedback_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate average ratings
        total = len(feedback_items)
        if feedback_items:
            avg_overall = sum(f.get('overall_rating', 0) for f in feedback_items) / total
            avg_photo_quality = sum(f.get('photo_quality_rating', 0) for f in feedback_items if f.get('photo_quality_rating')) / max(1, sum(1 for f in feedback_items if f.get('photo_quality_rating')))
            avg_delivery = sum(f.get('delivery_time_rating', 0) for f in feedback_items if f.get('delivery_time_rating')) / max(1, sum(1 for f in feedback_items if f.get('delivery_time_rating')))
            avg_communication = sum(f.get('communication_rating', 0) for f in feedback_items if f.get('communication_rating')) / max(1, sum(1 for f in feedback_items if f.get('communication_rating')))
            avg_value = sum(f.get('value_rating', 0) for f in feedback_items if f.get('value_rating')) / max(1, sum(1 for f in feedback_items if f.get('value_rating')))
            would_recommend_pct = (sum(1 for f in feedback_items if f.get('would_recommend')) / total) * 100
        else:
            avg_overall = 0
            avg_photo_quality = 0
            avg_delivery = 0
            avg_communication = 0
            avg_value = 0
            would_recommend_pct = 0
        
        return create_response(200, {
            'feedback': feedback_items,
            'summary': {
                'total_responses': total,
                'average_overall_rating': round(avg_overall, 2),
                'average_photo_quality_rating': round(avg_photo_quality, 2) if avg_photo_quality > 0 else None,
                'average_delivery_time_rating': round(avg_delivery, 2) if avg_delivery > 0 else None,
                'average_communication_rating': round(avg_communication, 2) if avg_communication > 0 else None,
                'average_value_rating': round(avg_value, 2) if avg_value > 0 else None,
                'would_recommend_percentage': round(would_recommend_pct, 1)
            }
        })
        
    except Exception as e:
        print(f"Get feedback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to retrieve feedback',
            'message': str(e)
        })

