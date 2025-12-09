"""
Services Pricing Handler
Manages photographer service offerings and pricing for portfolio/booking pages
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import dynamodb
from utils.response import create_response
import os

# Initialize DynamoDB
services_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SERVICES'))


def handle_list_services(photographer_id, is_public=True):
    """
    List services for a photographer
    
    GET /api/v1/public/photographers/{photographer_id}/services
    GET /api/v1/services (authenticated photographer)
    """
    try:
        # Query services for this photographer
        response = services_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(photographer_id)
        )
        
        services = response.get('Items', [])
        
        # Filter by active status if public view
        if is_public:
            services = [s for s in services if s.get('active') == True]
        
        # Sort by display_order
        services.sort(key=lambda x: x.get('display_order', 999))
        
        return create_response(200, {'services': services})
        
    except Exception as e:
        print(f"Error listing services: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve services'})


def handle_create_service(user, body):
    """
    Create a new service offering
    
    POST /api/v1/services
    Body: {
        "name": "Wedding Photography",
        "category": "wedding",
        "description": "Full day coverage...",
        "price": 2500,
        "currency": "USD",
        "duration_hours": 8,
        "included_photos": 500,
        "included_items": ["Full day coverage", "Online gallery", "High-res downloads"],
        "active": true,
        "display_order": 1
    }
    """
    try:
        # Validate required fields
        name = body.get('name', '').strip()
        if not name:
            return create_response(400, {'error': 'Service name is required'})
        
        # Create service
        service_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        service = {
            'id': service_id,
            'photographer_id': user['id'],
            'name': name,
            'category': body.get('category', 'other'),
            'description': body.get('description', ''),
            'price': Decimal(str(body.get('price', 0))),
            'currency': body.get('currency', 'USD'),
            'duration_hours': body.get('duration_hours', 0),
            'included_photos': body.get('included_photos', 0),
            'included_items': body.get('included_items', []),
            'addons_available': body.get('addons_available', []),
            'booking_deposit': Decimal(str(body.get('booking_deposit', 0))),
            'active': body.get('active', True),
            'display_order': body.get('display_order', 999),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        services_table.put_item(Item=service)
        
        print(f"New service created: {service_id} for photographer {user['id']}")
        
        return create_response(201, service)
        
    except Exception as e:
        print(f"Error creating service: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create service'})


def handle_update_service(user, service_id, body):
    """
    Update service details
    
    PUT /api/v1/services/{id}
    """
    try:
        # Get existing service
        response = services_table.get_item(Key={'id': service_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Service not found'})
        
        service = response['Item']
        
        # Verify ownership
        if service['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Build update expression
        update_fields = []
        expr_values = {}
        
        updateable = [
            'name', 'category', 'description', 'currency', 
            'duration_hours', 'included_photos', 'included_items',
            'addons_available', 'active', 'display_order'
        ]
        
        for field in updateable:
            if field in body:
                update_fields.append(f'{field} = :{field}')
                expr_values[f':{field}'] = body[field]
        
        # Handle decimal fields separately
        if 'price' in body:
            update_fields.append('price = :price')
            expr_values[':price'] = Decimal(str(body['price']))
        
        if 'booking_deposit' in body:
            update_fields.append('booking_deposit = :booking_deposit')
            expr_values[':booking_deposit'] = Decimal(str(body['booking_deposit']))
        
        if not update_fields:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update timestamp
        update_fields.append('updated_at = :updated_at')
        expr_values[':updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Execute update
        update_expression = 'SET ' + ', '.join(update_fields)
        
        result = services_table.update_item(
            Key={'id': service_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        return create_response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating service: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update service'})


def handle_delete_service(user, service_id):
    """Delete a service"""
    try:
        # Get service to verify ownership
        response = services_table.get_item(Key={'id': service_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Service not found'})
        
        service = response['Item']
        
        # Verify ownership
        if service['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Delete service
        services_table.delete_item(Key={'id': service_id})
        
        return create_response(200, {'message': 'Service deleted'})
        
    except Exception as e:
        print(f"Error deleting service: {str(e)}")
        return create_response(500, {'error': 'Failed to delete service'})


def handle_get_service(service_id, photographer_id=None):
    """Get single service details"""
    try:
        response = services_table.get_item(Key={'id': service_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Service not found'})
        
        service = response['Item']
        
        # If photographer_id is provided, verify ownership or public access
        if photographer_id and service['photographer_id'] != photographer_id:
            if not service.get('active'):
                return create_response(403, {'error': 'Service not available'})
        
        return create_response(200, service)
        
    except Exception as e:
        print(f"Error getting service: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve service'})
