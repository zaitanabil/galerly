"""
Profile management handlers
"""
from datetime import datetime
from utils.config import users_table, sessions_table
from utils.response import create_response

def handle_update_profile(user, body):
    """Update photographer profile - Simple city input"""
    try:
        # Only photographers can update profile info
        if user.get('role') != 'photographer':
            return create_response(403, {'error': 'Only photographers can update profile'})
        
        # Get current user data
        response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Update profile fields with validation
        if 'name' in body:
            name = body['name'].strip()
            if len(name) > 100:
                return create_response(400, {'error': 'Name must be less than 100 characters'})
            user_data['name'] = name
        if 'username' in body:
            username = body['username'].strip()
            if len(username) < 3:
                return create_response(400, {'error': 'Username must be at least 3 characters long'})
            if len(username) > 50:
                return create_response(400, {'error': 'Username must be less than 50 characters'})
            user_data['username'] = username
        if 'bio' in body:
            bio = body['bio'].strip()
            if len(bio) > 1000:
                return create_response(400, {'error': 'Bio must be less than 1000 characters'})
            user_data['bio'] = bio
        if 'city' in body:
            city = body['city'].strip()
            if len(city) > 100:
                return create_response(400, {'error': 'City name must be less than 100 characters'})
            user_data['city'] = city
        if 'specialties' in body:
            user_data['specialties'] = body['specialties']
        if 'hourly_rate' in body:
            try:
                user_data['hourly_rate'] = float(body['hourly_rate'])
            except (ValueError, TypeError):
                pass  # Invalid price, skip
        if 'rating' in body:
            try:
                user_data['rating'] = float(body['rating'])
            except (ValueError, TypeError):
                pass  # Invalid rating, skip
        
        user_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save to DynamoDB
        users_table.put_item(Item=user_data)
        
        # Update session with new user data
        sessions_response = sessions_table.scan(
            FilterExpression='#user.email = :email',
            ExpressionAttributeNames={'#user': 'user'},
            ExpressionAttributeValues={':email': user['email']}
        )
        
        for session in sessions_response.get('Items', []):
            session['user'] = user_data
            sessions_table.put_item(Item=session)
        
        print(f"✅ Profile updated for {user['email']}")
        
        # Return updated profile
        return create_response(200, {
            'id': user_data['id'],
            'email': user_data['email'],
            'username': user_data.get('username'),
            'name': user_data.get('name'),
            'bio': user_data.get('bio'),
            'city': user_data.get('city'),
            'specialties': user_data.get('specialties', []),
            'role': user_data.get('role'),
            'subscription': user_data.get('subscription')
        })
    except Exception as e:
        print(f"❌ Error updating profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update profile'})

