"""
Profile management handlers
"""
from datetime import datetime
from decimal import Decimal
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
            
            # Check if username is already taken by another user
            try:
                response = users_table.scan(
                    FilterExpression='username = :username AND email <> :email',
                    ExpressionAttributeValues={
                        ':username': username,
                        ':email': user['email']
                    },
                    Limit=1
                )
                if response.get('Items'):
                    return create_response(400, {'error': 'Username is already taken. Please choose another one.'})
            except Exception as e:
                print(f"Error checking username availability: {str(e)}")
                return create_response(500, {'error': 'Failed to check username availability'})
            
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
                user_data['hourly_rate'] = Decimal(str(body['hourly_rate']))
            except (ValueError, TypeError):
                pass  # Invalid price, skip
        if 'rating' in body:
            try:
                user_data['rating'] = Decimal(str(body['rating']))
            except (ValueError, TypeError):
                pass  # Invalid rating, skip
        
        # Watermark settings
        if 'watermark_enabled' in body or 'watermark_text' in body or 'watermark_position' in body or 'watermark_logo_s3_key' in body:
            from handlers.subscription_handler import get_user_features
            features, _, _ = get_user_features(user)
            
            # Watermarking requires Plus plan or higher
            if not features.get('remove_branding') and not features.get('watermarking'):
                 # Allow disabling watermark, but not enabling or customizing if not allowed
                 if body.get('watermark_enabled') is True:
                     return create_response(403, {
                         'error': 'Custom watermarking is available on Plus, Pro, and Ultimate plans.',
                         'upgrade_required': True
                     })

        if 'watermark_enabled' in body:
            user_data['watermark_enabled'] = bool(body['watermark_enabled'])
        if 'watermark_text' in body:
            user_data['watermark_text'] = str(body['watermark_text']).strip()
        if 'watermark_logo_s3_key' in body:
            # Store S3 key for logo image
            user_data['watermark_logo_s3_key'] = str(body['watermark_logo_s3_key']).strip()
        if 'watermark_type' in body:
            # Type: 'text' or 'logo'
            wm_type = str(body['watermark_type']).strip()
            if wm_type in ['text', 'logo']:
                user_data['watermark_type'] = wm_type
        if 'watermark_position' in body:
            position = str(body['watermark_position']).strip()
            if position in ['bottom-right', 'bottom-left', 'top-right', 'top-left', 'center']:
                user_data['watermark_position'] = position
        if 'watermark_opacity' in body:
            try:
                opacity = float(body['watermark_opacity'])
                if 0.0 <= opacity <= 1.0:
                    user_data['watermark_opacity'] = Decimal(str(opacity))
            except (ValueError, TypeError):
                pass
        if 'watermark_size' in body:
            # Size as percentage of image (for logo watermarks)
            try:
                size = float(body['watermark_size'])
                if 1.0 <= size <= 50.0:  # 1-50% of image
                    user_data['watermark_size'] = Decimal(str(size))
            except (ValueError, TypeError):
                pass

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
        
        print(f"Profile updated for {user['email']}")
        
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
        print(f"Error updating profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update profile'})

