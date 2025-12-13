"""
Enhanced Client Photo Selection Workflow
Helps clients select their favorite photos with improved UX and tracking
"""
import os
import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr
from utils.config import (
    galleries_table, photos_table, client_selections_table,
    users_table, dynamodb
)
from utils.response import create_response


def handle_create_selection_session(user, body):
    """
    Create a new selection session for a client
    Tracks the client's selection process
    
    Request:
    {
        "gallery_id": str,
        "client_email": str,
        "client_name": str,
        "max_selections": int (optional),
        "deadline": str (optional ISO date)
    }
    """
    try:
        gallery_id = body.get('gallery_id')
        client_email = body.get('client_email')
        client_name = body.get('client_name', '')
        max_selections = body.get('max_selections')
        deadline = body.get('deadline')
        
        if not gallery_id or not client_email:
            return create_response(400, {'error': 'gallery_id and client_email required'})
        
        # Verify gallery exists and belongs to user
        gallery_response = galleries_table.get_item(Key={'id': gallery_id})
        if 'Item' not in gallery_response:
            return create_response(404, {'error': 'Gallery not found'})
        
        gallery = gallery_response['Item']
        if gallery.get('user_id') != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Create selection session
        session_id = str(uuid.uuid4())
        session = {
            'id': session_id,
            'gallery_id': gallery_id,
            'photographer_id': user['id'],
            'client_email': client_email,
            'client_name': client_name,
            'max_selections': max_selections,
            'deadline': deadline,
            'status': 'active',
            'selections': [],
            'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        client_selections_table.put_item(Item=session)
        
        return create_response(200, {
            'success': True,
            'session': session,
            'selection_url': f"{os.environ.get('FRONTEND_URL')}/gallery/{gallery_id}/select?session={session_id}"
        })
        
    except Exception as e:
        print(f"Error creating selection session: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create selection session'})


def handle_add_to_selection(user_or_client, body):
    """
    Add a photo to the client's selection
    Can be called by client or photographer
    
    Request:
    {
        "session_id": str,
        "photo_id": str,
        "note": str (optional)
    }
    """
    try:
        session_id = body.get('session_id')
        photo_id = body.get('photo_id')
        note = body.get('note', '')
        
        if not session_id or not photo_id:
            return create_response(400, {'error': 'session_id and photo_id required'})
        
        # Get selection session
        session_response = client_selections_table.get_item(Key={'id': session_id})
        if 'Item' not in session_response:
            return create_response(404, {'error': 'Selection session not found'})
        
        session = session_response['Item']
        
        # Check if session is still active
        if session.get('status') != 'active':
            return create_response(400, {'error': 'Selection session is not active'})
        
        # Check max selections limit
        current_selections = session.get('selections', [])
        max_selections = session.get('max_selections')
        
        if max_selections and len(current_selections) >= max_selections:
            return create_response(400, {
                'error': f'Maximum {max_selections} selections allowed',
                'limit_reached': True
            })
        
        # Check if photo already selected
        if any(s.get('photo_id') == photo_id for s in current_selections):
            return create_response(400, {'error': 'Photo already in selection'})
        
        # Add photo to selection
        selection_item = {
            'photo_id': photo_id,
            'note': note,
            'selected_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        current_selections.append(selection_item)
        
        # Update session
        client_selections_table.update_item(
            Key={'id': session_id},
            UpdateExpression='SET selections = :selections, updated_at = :updated',
            ExpressionAttributeValues={
                ':selections': current_selections,
                ':updated': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        return create_response(200, {
            'success': True,
            'selections_count': len(current_selections),
            'max_selections': max_selections,
            'remaining': (max_selections - len(current_selections)) if max_selections else None
        })
        
    except Exception as e:
        print(f"Error adding to selection: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to add to selection'})


def handle_remove_from_selection(user_or_client, body):
    """
    Remove a photo from the client's selection
    
    Request:
    {
        "session_id": str,
        "photo_id": str
    }
    """
    try:
        session_id = body.get('session_id')
        photo_id = body.get('photo_id')
        
        if not session_id or not photo_id:
            return create_response(400, {'error': 'session_id and photo_id required'})
        
        # Get selection session
        session_response = client_selections_table.get_item(Key={'id': session_id})
        if 'Item' not in session_response:
            return create_response(404, {'error': 'Selection session not found'})
        
        session = session_response['Item']
        current_selections = session.get('selections', [])
        
        # Remove photo
        updated_selections = [s for s in current_selections if s.get('photo_id') != photo_id]
        
        if len(updated_selections) == len(current_selections):
            return create_response(404, {'error': 'Photo not in selection'})
        
        # Update session
        client_selections_table.update_item(
            Key={'id': session_id},
            UpdateExpression='SET selections = :selections, updated_at = :updated',
            ExpressionAttributeValues={
                ':selections': updated_selections,
                ':updated': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        return create_response(200, {
            'success': True,
            'selections_count': len(updated_selections)
        })
        
    except Exception as e:
        print(f"Error removing from selection: {str(e)}")
        return create_response(500, {'error': 'Failed to remove from selection'})


def handle_get_selection_session(user_or_client, session_id):
    """
    Get details of a selection session
    """
    try:
        session_response = client_selections_table.get_item(Key={'id': session_id})
        if 'Item' not in session_response:
            return create_response(404, {'error': 'Selection session not found'})
        
        session = session_response['Item']
        
        # Get photo details for selections
        selections_with_details = []
        for selection in session.get('selections', []):
            photo_response = photos_table.get_item(Key={'id': selection['photo_id']})
            if 'Item' in photo_response:
                photo = photo_response['Item']
                selections_with_details.append({
                    **selection,
                    'photo': {
                        'id': photo['id'],
                        'thumbnail_url': photo.get('thumbnail_url', ''),
                        'filename': photo.get('original_filename', ''),
                        'file_size': photo.get('file_size', 0)
                    }
                })
        
        session['selections'] = selections_with_details
        
        return create_response(200, session)
        
    except Exception as e:
        print(f"Error getting selection session: {str(e)}")
        return create_response(500, {'error': 'Failed to get selection session'})


def handle_submit_selection(user_or_client, body):
    """
    Submit the final selection (client confirms their choices)
    
    Request:
    {
        "session_id": str,
        "message": str (optional - message to photographer)
    }
    """
    try:
        session_id = body.get('session_id')
        message = body.get('message', '')
        
        if not session_id:
            return create_response(400, {'error': 'session_id required'})
        
        # Get selection session
        session_response = client_selections_table.get_item(Key={'id': session_id})
        if 'Item' not in session_response:
            return create_response(404, {'error': 'Selection session not found'})
        
        session = session_response['Item']
        
        if session.get('status') != 'active':
            return create_response(400, {'error': 'Selection already submitted'})
        
        selections = session.get('selections', [])
        if not selections:
            return create_response(400, {'error': 'No photos selected'})
        
        # Update session status
        client_selections_table.update_item(
            Key={'id': session_id},
            UpdateExpression='SET #status = :status, submitted_at = :submitted, client_message = :message',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'submitted',
                ':submitted': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
                ':message': message
            }
        )
        
        # Mark photos as favorited in photos table
        for selection in selections:
            try:
                photos_table.update_item(
                    Key={'id': selection['photo_id']},
                    UpdateExpression='SET favorite_count = if_not_exists(favorite_count, :zero) + :inc',
                    ExpressionAttributeValues={
                        ':zero': 0,
                        ':inc': 1
                    }
                )
            except Exception as e:
                print(f"Error updating favorite count for photo {selection['photo_id']}: {str(e)}")
        
        # Send notification to photographer (if email automation is enabled)
        try:
            photographer_id = session.get('photographer_id')
            photographer_response = users_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('id').eq(photographer_id),
                Limit=1
            )
            
            if photographer_response.get('Items'):
                photographer = photographer_response['Items'][0]
                # Email notification would be sent here via SES or email automation
                print(f"Selection submitted notification for photographer: {photographer.get('email')}")
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
        
        return create_response(200, {
            'success': True,
            'message': 'Selection submitted successfully',
            'selections_count': len(selections),
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error submitting selection: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to submit selection'})


def handle_list_selection_sessions(user, query_params):
    """
    List all selection sessions for a photographer
    """
    try:
        photographer_id = user['id']
        
        # Query sessions for this photographer
        response = client_selections_table.query(
            IndexName='PhotographerSelectionSessionsIndex',
            KeyConditionExpression=Key('photographer_id').eq(photographer_id)
        )
        
        sessions = response.get('Items', [])
        
        # Sort by created_at
        sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Filter by status if provided
        status_filter = query_params.get('status')
        if status_filter:
            sessions = [s for s in sessions if s.get('status') == status_filter]
        
        return create_response(200, {
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        print(f"Error listing selection sessions: {str(e)}")
        return create_response(500, {'error': 'Failed to list selection sessions'})

