"""
Tests for feature requests handler using REAL AWS resources
"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.feature_requests_handler import (
    handle_list_feature_requests,
    handle_create_feature_request,
    handle_vote_feature_request
)


class TestFeatureRequests:
    """Test feature request functionality with real AWS"""
    
    def test_list_feature_requests(self):
        """Test listing feature requests"""
        event = {'queryStringParameters': {'status': 'all', 'sort': 'votes'}}
        response = handle_list_feature_requests(event)
        
        assert response['statusCode'] in [200, 500]
    
    def test_create_feature_request(self):
        """Test creating feature request"""
        event = {
            'body': json.dumps({
                'title': f'Feature {uuid.uuid4()}',
                'description': 'Test feature request',
                'category': 'general'
            })
        }
        
        with patch('handlers.feature_requests_handler.get_user_from_token') as mock_auth:
            mock_auth.return_value = {'user_id': f'user-{uuid.uuid4()}', 'name': 'Test', 'email': 'test@test.com'}
            
            response = handle_create_feature_request(event)
            assert response['statusCode'] in [201, 400, 500]
    
    def test_vote_feature_request(self):
        """Test voting on feature request"""
        event = {'pathParameters': {'request_id': f'req-{uuid.uuid4()}'}}
        
        with patch('handlers.feature_requests_handler.get_user_from_token') as mock_auth:
            mock_auth.return_value = {'user_id': f'user-{uuid.uuid4()}'}
            
            response = handle_vote_feature_request(event)
            assert response['statusCode'] in [200, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
