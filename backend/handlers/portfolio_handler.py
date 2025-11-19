"""
Portfolio customization handlers
"""
from boto3.dynamodb.conditions import Key
from utils.config import users_table, galleries_table
from utils.response import create_response

def handle_get_portfolio_settings(user):
    """Get portfolio customization settings for current user"""
    try:
        # Get user data which contains portfolio settings
        response = users_table.get_item(Key={'email': user['email']})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Extract portfolio settings (defaults if not set)
        portfolio_settings = {
            'theme': user_data.get('portfolio_theme', 'default'),
            'primary_color': user_data.get('portfolio_primary_color', '#0066CC'),
            'secondary_color': user_data.get('portfolio_secondary_color', '#FFD700'),
            'logo_url': user_data.get('portfolio_logo_url', ''),
            'cover_image_url': user_data.get('portfolio_cover_image_url', ''),
            'about_section': user_data.get('portfolio_about', ''),
            'show_contact_form': user_data.get('portfolio_show_contact_form', True),
            'social_links': user_data.get('portfolio_social_links', {
                'instagram': '',
                'website': '',
                'facebook': '',
                'twitter': ''
            }),
            'featured_galleries': user_data.get('portfolio_featured_galleries', []),
            'portfolio_sections': user_data.get('portfolio_sections', []),
            'custom_domain': user_data.get('portfolio_custom_domain', '')
        }
        
        return create_response(200, portfolio_settings)
    except Exception as e:
        print(f"Error getting portfolio settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load portfolio settings'})

def handle_update_portfolio_settings(user, body):
    """Update portfolio customization settings"""
    try:
        # Build update expression
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        # Theme
        if 'theme' in body:
            update_expressions.append('portfolio_theme = :theme')
            expression_values[':theme'] = body['theme']
        
        # Colors
        if 'primary_color' in body:
            update_expressions.append('portfolio_primary_color = :primary_color')
            expression_values[':primary_color'] = body['primary_color']
        
        if 'secondary_color' in body:
            update_expressions.append('portfolio_secondary_color = :secondary_color')
            expression_values[':secondary_color'] = body['secondary_color']
        
        # Logo and cover image
        if 'logo_url' in body:
            update_expressions.append('portfolio_logo_url = :logo_url')
            expression_values[':logo_url'] = body['logo_url']
        
        if 'cover_image_url' in body:
            update_expressions.append('portfolio_cover_image_url = :cover_image_url')
            expression_values[':cover_image_url'] = body['cover_image_url']
        
        # About section
        if 'about_section' in body:
            update_expressions.append('portfolio_about = :about_section')
            expression_values[':about_section'] = body['about_section']
        
        # Contact form
        if 'show_contact_form' in body:
            update_expressions.append('portfolio_show_contact_form = :show_contact_form')
            expression_values[':show_contact_form'] = body['show_contact_form']
        
        # Social links
        if 'social_links' in body:
            update_expressions.append('portfolio_social_links = :social_links')
            expression_values[':social_links'] = body['social_links']
        
        # Featured galleries
        if 'featured_galleries' in body:
            update_expressions.append('portfolio_featured_galleries = :featured_galleries')
            expression_values[':featured_galleries'] = body['featured_galleries']
        
        # Portfolio sections
        if 'portfolio_sections' in body:
            update_expressions.append('portfolio_sections = :portfolio_sections')
            expression_values[':portfolio_sections'] = body['portfolio_sections']
        
        # Custom domain
        if 'custom_domain' in body:
            update_expressions.append('portfolio_custom_domain = :custom_domain')
            expression_values[':custom_domain'] = body['custom_domain']
        
        # Always update updated_at
        from datetime import datetime
        update_expressions.append('updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        if not update_expressions:
            return create_response(400, {'error': 'No fields to update'})
        
        # Update user record
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names if expression_names else None
        )
        
        # Return updated settings
        return handle_get_portfolio_settings(user)
    except Exception as e:
        print(f"Error updating portfolio settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update portfolio settings'})

def handle_get_public_portfolio(photographer_id):
    """Get public portfolio view with customization applied"""
    try:
        # Get photographer data
        response = users_table.scan(
            FilterExpression='id = :id AND #role = :role',
            ExpressionAttributeValues={':id': photographer_id, ':role': 'photographer'},
            ExpressionAttributeNames={'#role': 'role'}
        )
        
        users = response.get('Items', [])
        if not users:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = users[0]
        
        # Get portfolio settings
        portfolio_settings = {
            'theme': photographer.get('portfolio_theme', 'default'),
            'primary_color': photographer.get('portfolio_primary_color', '#0066CC'),
            'secondary_color': photographer.get('portfolio_secondary_color', '#FFD700'),
            'logo_url': photographer.get('portfolio_logo_url', ''),
            'cover_image_url': photographer.get('portfolio_cover_image_url', ''),
            'about_section': photographer.get('portfolio_about', photographer.get('bio', '')),
            'show_contact_form': photographer.get('portfolio_show_contact_form', True),
            'social_links': photographer.get('portfolio_social_links', {
                'instagram': '',
                'website': '',
                'facebook': '',
                'twitter': ''
            }),
            'featured_galleries': photographer.get('portfolio_featured_galleries', []),
            'portfolio_sections': photographer.get('portfolio_sections', [])
        }
        
        # Get photographer's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        )
        all_galleries = galleries_response.get('Items', [])
        
        # Filter to only PUBLIC galleries
        public_galleries = [g for g in all_galleries if g.get('privacy', 'private') == 'public']
        
        # Sort galleries: featured first, then by date
        featured_ids = portfolio_settings.get('featured_galleries', [])
        featured_galleries = [g for g in public_galleries if g['id'] in featured_ids]
        other_galleries = [g for g in public_galleries if g['id'] not in featured_ids]
        
        # Sort featured by featured order, others by date
        featured_galleries.sort(key=lambda x: featured_ids.index(x['id']) if x['id'] in featured_ids else 999)
        other_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        sorted_galleries = featured_galleries + other_galleries
        
        # Remove sensitive info
        for gallery in sorted_galleries:
            gallery.pop('client_name', None)
            gallery.pop('client_email', None)
            gallery.pop('password', None)
        
        return create_response(200, {
            'photographer': {
                'id': photographer['id'],
                'name': photographer.get('name'),
                'username': photographer.get('username'),
                'city': photographer.get('city'),
                'bio': photographer.get('bio'),
                'specialties': photographer.get('specialties', [])
            },
            'portfolio': portfolio_settings,
            'galleries': sorted_galleries,
            'gallery_count': len(sorted_galleries),
            'photo_count': sum(int(g.get('photo_count', 0)) for g in sorted_galleries)
        })
    except Exception as e:
        print(f"Error getting public portfolio: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load portfolio'})

