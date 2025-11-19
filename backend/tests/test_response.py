"""
Test response utilities
"""
import json
import pytest
from utils.response import create_response


class TestCreateResponse:
    """Test the create_response utility function"""
    
    def test_create_response_basic(self):
        """Test basic response creation"""
        response = create_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert body['message'] == 'success'
    
    def test_create_response_headers(self):
        """Test response headers are set correctly"""
        response = create_response(200, {})
        headers = response['headers']
        
        # Check CORS headers
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert 'Access-Control-Allow-Credentials' in headers
        
        # Check security headers
        assert 'Content-Security-Policy' in headers
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Strict-Transport-Security' in headers
    
    def test_create_response_error(self):
        """Test error response creation"""
        response = create_response(400, {'error': 'Bad request'})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'
    
    def test_create_response_with_complex_data(self):
        """Test response with complex nested data"""
        data = {
            'user': {
                'id': 'test-123',
                'email': 'test@example.com'
            },
            'galleries': [
                {'id': '1', 'name': 'Gallery 1'},
                {'id': '2', 'name': 'Gallery 2'}
            ]
        }
        
        response = create_response(200, data)
        body = json.loads(response['body'])
        
        assert body['user']['id'] == 'test-123'
        assert len(body['galleries']) == 2

