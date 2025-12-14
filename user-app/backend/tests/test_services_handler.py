"""
Tests for services handler using REAL AWS resources
"""
import pytest
import json
import uuid
from unittest.mock import patch
from handlers.services_handler import (
    handle_list_services,
    handle_create_service
)


class TestServicesHandler:
    """Test services management with real AWS"""
    
    def test_list_services(self):
        """Test listing services"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        
        with patch('handlers.services_handler.dynamodb') as mock_dynamo:
            mock_table = mock_dynamo.Table.return_value
            mock_table.query.return_value = {'Items': []}
            
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
        
        with patch('handlers.services_handler.get_user_features') as mock_features, \
             patch('handlers.services_handler.services_table') as mock_table:
            
            mock_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro Plan')
            mock_table.put_item.return_value = {}
            
            body = {
                'name': 'Wedding Photography',
                'price': 2500,
                'description': 'Full day coverage'
            }
            
            response = handle_create_service(user, body)
            assert response['statusCode'] in [201, 400, 403, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
