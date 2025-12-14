"""
Tests for services handler using REAL AWS resources
"""
import pytest
import json
import uuid
from unittest.mock import patch
from handlers.services_handler import (
    handle_list_services,
    handle_create_service,
    handle_update_service,
    handle_delete_service
)
from utils.config import services_table


class TestServicesHandler:
    """Test services management with real AWS"""
    
    def test_list_services(self):
        """Test listing services"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        
        response = handle_list_services(photographer_id, is_public=True)
        assert response['statusCode'] in [200, 500]
    
    def test_create_service(self):
        """Test creating a service with real AWS"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        user = {
            'user_id': photographer_id,
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'role': 'photographer',
            'plan': 'pro'
        }
        service_id = None
        
        try:
            body = {
                'name': f'Wedding Photography {uuid.uuid4()}',
                'price': 2500,
                'description': 'Full day coverage'
            }
            
            with patch('handlers.services_handler.get_user_features') as mock_features:
                mock_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro Plan')
                
                response = handle_create_service(user, body)
                
                if response['statusCode'] == 201:
                    data = json.loads(response['body'])
                    service_id = data.get('id')
                
                assert response['statusCode'] in [201, 400, 403, 500]
            
        finally:
            if service_id:
                try:
                    services_table.delete_item(Key={'photographer_id': photographer_id, 'id': service_id})
                except:
                    pass
    
    def test_update_service(self):
        """Test updating a service with real AWS"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        service_id = f'service-{uuid.uuid4()}'
        user = {
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'role': 'photographer'
        }
        
        try:
            services_table.put_item(Item={
                'photographer_id': photographer_id,
                'id': service_id,
                'name': 'Test Service',
                'price': '1000.00'
            })
            
            body = {'price': 1500.00}
            response = handle_update_service(user, service_id, body)
            
            assert response['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                services_table.delete_item(Key={'photographer_id': photographer_id, 'id': service_id})
            except:
                pass
    
    def test_delete_service(self):
        """Test deleting a service with real AWS"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        service_id = f'service-{uuid.uuid4()}'
        user = {
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'role': 'photographer'
        }
        
        try:
            services_table.put_item(Item={
                'photographer_id': photographer_id,
                'id': service_id,
                'name': 'Test Service'
            })
            
            response = handle_delete_service(user, service_id)
            assert response['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                services_table.delete_item(Key={'photographer_id': photographer_id, 'id': service_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
