"""
Photographer directory handlers (PUBLIC)
"""
from boto3.dynamodb.conditions import Key
from utils.config import users_table, galleries_table, photos_table
from utils.response import create_response

def handle_list_photographers(query_params=None):
    """List all photographers with advanced filters - PUBLIC ACCESS"""
    try:
        # Parse query parameters
        city = query_params.get('city') if query_params else None
        specialty = query_params.get('specialty') if query_params else None
        min_price = query_params.get('min_price')
        max_price = query_params.get('max_price')
        min_rating = query_params.get('min_rating')
        sort_by = query_params.get('sort', 'photo_count_desc') if query_params else 'photo_count_desc'
        
        # Scan users table for photographers
        response = users_table.scan()
        all_users = response.get('Items', [])
        
        # Filter for photographers only
        photographers = [u for u in all_users if u.get('role') == 'photographer']
        
        # Filter by city if provided
        if city:
            city_lower = city.lower()
            photographers = [p for p in photographers if city_lower in p.get('city', '').lower()]
        
        # Filter by specialty if provided
        if specialty:
            specialty_lower = specialty.lower()
            photographers = [
                p for p in photographers
                if specialty_lower in [s.lower() for s in p.get('specialties', [])]
            ]
        
        # Filter by price range if provided
        if min_price or max_price:
            filtered_photographers = []
            for p in photographers:
                photographer_price = p.get('hourly_rate') or p.get('price_per_hour') or 0
                try:
                    photographer_price = float(photographer_price)
                    min_price_val = float(min_price) if min_price else 0
                    max_price_val = float(max_price) if max_price else float('inf')
                    if min_price_val <= photographer_price <= max_price_val:
                        filtered_photographers.append(p)
                except (ValueError, TypeError):
                    # If price is not numeric, skip price filter for this photographer
                    if not min_price and not max_price:
                        filtered_photographers.append(p)
            photographers = filtered_photographers
        
        # Filter by rating if provided
        if min_rating:
            try:
                min_rating_val = float(min_rating)
                filtered_photographers = []
                for p in photographers:
                    photographer_rating = p.get('rating') or p.get('average_rating') or 0
                    try:
                        photographer_rating = float(photographer_rating)
                        if photographer_rating >= min_rating_val:
                            filtered_photographers.append(p)
                    except (ValueError, TypeError):
                        pass  # Skip photographers without rating
                photographers = filtered_photographers
            except (ValueError, TypeError):
                pass  # Invalid min_rating, skip filter
        
        # For each photographer, get their PUBLIC gallery count and photo count
        photographer_list = []
        for photographer in photographers:
            photographer_id = photographer['id']
            
            # Query galleries for this photographer
            try:
                galleries_response = galleries_table.query(
                    KeyConditionExpression=Key('user_id').eq(photographer_id)
                )
                all_galleries = galleries_response.get('Items', [])
                
                # Filter to only PUBLIC galleries
                public_galleries = [g for g in all_galleries if g.get('privacy', 'private') == 'public']
                gallery_count = len(public_galleries)
                
                # Count total photos (only from public galleries)
                photo_count = sum(int(g.get('photo_count', 0)) for g in public_galleries)
                
                # Get cover image (first photo from first public gallery)
                cover_image = None
                for gallery in public_galleries:
                    if gallery.get('photo_count', 0) > 0:
                        try:
                            photos_response = photos_table.query(
                                IndexName='GalleryIdIndex',
                                KeyConditionExpression=Key('gallery_id').eq(gallery['id']),
                                Limit=1
                            )
                            photos = photos_response.get('Items', [])
                            if photos:
                                cover_image = photos[0].get('url')
                                break
                        except:
                            pass
                
            except:
                gallery_count = 0
                photo_count = 0
                cover_image = None
            
            # Only include photographers with at least one public gallery
            if gallery_count > 0:
                photographer_list.append({
                    'id': photographer['id'],
                    'name': photographer.get('name'),
                    'username': photographer.get('username'),
                    'city': photographer.get('city'),
                    'bio': photographer.get('bio'),
                    'specialties': photographer.get('specialties', []),
                    'hourly_rate': photographer.get('hourly_rate'),
                    'rating': photographer.get('rating') or photographer.get('average_rating'),
                    'gallery_count': gallery_count,
                    'photo_count': photo_count,
                    'cover_image': cover_image
                })
        
        # Sort photographers
        if sort_by == 'photo_count_desc':
            photographer_list.sort(key=lambda x: x['photo_count'], reverse=True)
        elif sort_by == 'photo_count_asc':
            photographer_list.sort(key=lambda x: x['photo_count'], reverse=False)
        elif sort_by == 'rating_desc':
            photographer_list.sort(key=lambda x: x.get('rating', 0) or 0, reverse=True)
        elif sort_by == 'rating_asc':
            photographer_list.sort(key=lambda x: x.get('rating', 0) or 0, reverse=False)
        elif sort_by == 'name_asc':
            photographer_list.sort(key=lambda x: (x.get('name') or x.get('username', '')).lower(), reverse=False)
        elif sort_by == 'name_desc':
            photographer_list.sort(key=lambda x: (x.get('name') or x.get('username', '')).lower(), reverse=True)
        elif sort_by == 'price_asc':
            photographer_list.sort(key=lambda x: x.get('hourly_rate', 0) or 0, reverse=False)
        elif sort_by == 'price_desc':
            photographer_list.sort(key=lambda x: x.get('hourly_rate', 0) or 0, reverse=True)
        else:
            # Default: Sort by photo count (most active first)
            photographer_list.sort(key=lambda x: x['photo_count'], reverse=True)
        
        return create_response(200, {
            'photographers': photographer_list,
            'total': len(photographer_list)
        })
    except Exception as e:
        print(f"Error listing photographers: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load photographers'})

def handle_get_photographer(photographer_id):
    """Get photographer profile with their PUBLIC galleries only - PUBLIC ACCESS"""
    try:
        # Get photographer user data
        response = users_table.scan(
            FilterExpression='id = :id AND #role = :role',
            ExpressionAttributeValues={':id': photographer_id, ':role': 'photographer'},
            ExpressionAttributeNames={'#role': 'role'}
        )
        
        users = response.get('Items', [])
        if not users:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = users[0]
        
        # Get photographer's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        )
        all_galleries = galleries_response.get('Items', [])
        
        # Filter to only PUBLIC galleries (privacy = 'public')
        public_galleries = [g for g in all_galleries if g.get('privacy', 'private') == 'public']
        
        # For each public gallery, get photos and remove sensitive info
        for gallery in public_galleries:
            try:
                photos_response = photos_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery['id'])
                )
                gallery['photos'] = photos_response.get('Items', [])
            except:
                gallery['photos'] = []
            
            # Remove sensitive client information
            gallery.pop('client_name', None)
            gallery.pop('client_email', None)
            gallery.pop('password', None)
        
        # Calculate stats (only from public galleries)
        photo_count = sum(len(g.get('photos', [])) for g in public_galleries)
        
        return create_response(200, {
            'id': photographer['id'],
            'name': photographer.get('name'),
            'username': photographer.get('username'),
            'city': photographer.get('city'),
            'bio': photographer.get('bio'),
            'specialties': photographer.get('specialties', []),
            'gallery_count': len(public_galleries),
            'photo_count': photo_count,
            'galleries': public_galleries
        })
    except Exception as e:
        print(f"Error getting photographer: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load photographer'})

