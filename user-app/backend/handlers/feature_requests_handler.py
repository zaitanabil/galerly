"""
Feature Request Voting Handler
Backend for feature request submission and voting
"""

import json
import boto3
from datetime import datetime
import uuid
from utils.auth import get_user_from_token
from utils.response import create_response
from utils.config import get_dynamodb

dynamodb = get_dynamodb()
table = dynamodb.Table('galerly-feature-requests')

def handle_list_feature_requests(event):
    """
    List all feature requests with voting
    GET /feature-requests?status=...&sort=...
    """
    try:
        params = event.get('queryStringParameters') or {}
        status_filter = params.get('status', 'all')  # all, pending, planned, completed
        sort_by = params.get('sort', 'votes')  # votes, recent, oldest
        
        # Scan or query based on status
        if status_filter == 'all':
            response = table.scan()
        else:
            response = table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status_filter}
            )
        
        requests = response.get('Items', [])
        
        # Sort
        if sort_by == 'votes':
            requests.sort(key=lambda x: x.get('votes', 0), reverse=True)
        elif sort_by == 'recent':
            requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'oldest':
            requests.sort(key=lambda x: x.get('created_at', ''))
        
        return create_response(200, {
            'feature_requests': requests,
            'total': len(requests)
        })
        
    except Exception as e:
        print(f"Error listing feature requests: {str(e)}")
        return create_response(500, {'error': f'Failed to list requests: {str(e)}'})


def handle_create_feature_request(event):
    """
    Submit a new feature request
    POST /feature-requests
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        body = json.loads(event.get('body', '{}'))
        
        title = body.get('title', '').strip()
        description = body.get('description', '').strip()
        category = body.get('category', 'general')  # general, ui, integration, other
        
        if not title or len(title) < 10:
            return create_response(400, {'error': 'Title must be at least 10 characters'})
        
        if not description or len(description) < 20:
            return create_response(400, {'error': 'Description must be at least 20 characters'})
        
        # Create feature request
        request_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'id': request_id,
            'title': title,
            'description': description,
            'category': category,
            'status': 'pending',  # pending, planned, in_progress, completed, declined
            'submitter_id': user['user_id'],
            'submitter_name': user.get('name', 'Anonymous'),
            'submitter_email': user.get('email'),
            'votes': 0,
            'voters': [],  # List of user IDs who voted
            'created_at': timestamp,
            'updated_at': timestamp,
            'comments_count': 0
        }
        
        table.put_item(Item=item)
        
        return create_response(201, {
            'feature_request': item,
            'message': 'Feature request submitted successfully'
        })
        
    except Exception as e:
        print(f"Error creating feature request: {str(e)}")
        return create_response(500, {'error': f'Failed to create request: {str(e)}'})


def handle_vote_feature_request(event):
    """
    Vote for a feature request
    POST /feature-requests/{request_id}/vote
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        request_id = event['pathParameters']['request_id']
        user_id = user['user_id']
        
        # Get feature request
        response = table.get_item(Key={'id': request_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Feature request not found'})
        
        item = response['Item']
        voters = item.get('voters', [])
        
        # Check if already voted
        if user_id in voters:
            return create_response(400, {'error': 'You have already voted for this request'})
        
        # Add vote
        voters.append(user_id)
        
        table.update_item(
            Key={'id': request_id},
            UpdateExpression='SET votes = votes + :inc, voters = :voters, updated_at = :time',
            ExpressionAttributeValues={
                ':inc': 1,
                ':voters': voters,
                ':time': datetime.now().isoformat()
            }
        )
        
        return create_response(200, {
            'message': 'Vote recorded successfully',
            'votes': item.get('votes', 0) + 1
        })
        
    except Exception as e:
        print(f"Error voting: {str(e)}")
        return create_response(500, {'error': f'Failed to vote: {str(e)}'})


def handle_unvote_feature_request(event):
    """
    Remove vote from a feature request
    DELETE /feature-requests/{request_id}/vote
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        request_id = event['pathParameters']['request_id']
        user_id = user['user_id']
        
        # Get feature request
        response = table.get_item(Key={'id': request_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Feature request not found'})
        
        item = response['Item']
        voters = item.get('voters', [])
        
        # Check if voted
        if user_id not in voters:
            return create_response(400, {'error': 'You have not voted for this request'})
        
        # Remove vote
        voters.remove(user_id)
        
        table.update_item(
            Key={'id': request_id},
            UpdateExpression='SET votes = votes - :dec, voters = :voters, updated_at = :time',
            ExpressionAttributeValues={
                ':dec': 1,
                ':voters': voters,
                ':time': datetime.now().isoformat()
            }
        )
        
        return create_response(200, {
            'message': 'Vote removed successfully',
            'votes': max(0, item.get('votes', 0) - 1)
        })
        
    except Exception as e:
        print(f"Error removing vote: {str(e)}")
        return create_response(500, {'error': f'Failed to remove vote: {str(e)}'})


def handle_update_feature_request_status(event):
    """
    Update feature request status (admin only)
    PUT /feature-requests/{request_id}/status
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user or user.get('role') != 'admin':
            return create_response(403, {'error': 'Unauthorized'})
        
        request_id = event['pathParameters']['request_id']
        body = json.loads(event.get('body', '{}'))
        
        new_status = body.get('status')
        admin_comment = body.get('comment', '')
        
        if new_status not in ['pending', 'planned', 'in_progress', 'completed', 'declined']:
            return create_response(400, {'error': 'Invalid status'})
        
        # Update status
        table.update_item(
            Key={'id': request_id},
            UpdateExpression='SET #status = :status, admin_comment = :comment, updated_at = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':comment': admin_comment,
                ':time': datetime.now().isoformat()
            }
        )
        
        return create_response(200, {
            'message': 'Status updated successfully',
            'status': new_status
        })
        
    except Exception as e:
        print(f"Error updating status: {str(e)}")
        return create_response(500, {'error': f'Failed to update status: {str(e)}'})
