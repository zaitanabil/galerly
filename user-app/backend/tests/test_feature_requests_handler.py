"""
Tests for Feature Requests Handler
"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.feature_requests_handler import (
    handle_list_feature_requests,
    handle_create_feature_request,
    handle_vote_feature_request,
    handle_unvote_feature_request
)


class TestFeatureRequestsHandler:
    """Test feature request functionality"""
    
    @patch('handlers.feature_requests_handler.table')
    def test_list_feature_requests(self, mock_table):
        """Test listing feature requests"""
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'req1',
                    'title': 'Test Feature',
                    'votes': 5,
                    'status': 'pending'
                }
            ]
        }
        
        event = {'queryStringParameters': {'status': 'all', 'sort': 'votes'}}
        response = handle_list_feature_requests(event)
        
        assert response['statusCode'] == 200
        assert 'feature_requests' in response['body']
    
    @patch('handlers.feature_requests_handler.get_user_from_token')
    @patch('handlers.feature_requests_handler.table')
    def test_create_feature_request(self, mock_table, mock_get_user):
        """Test creating feature request"""
        mock_get_user.return_value = {'user_id': 'user1', 'name': 'Test User', 'email': 'test@example.com'}
        
        event = {
            'body': '{"title": "New Feature Request", "description": "This is a test feature request", "category": "general"}'
        }
        
        response = handle_create_feature_request(event)
        
        assert response['statusCode'] == 201
        assert mock_table.put_item.called
    
    @patch('handlers.feature_requests_handler.get_user_from_token')
    @patch('handlers.feature_requests_handler.table')
    def test_vote_feature_request(self, mock_table, mock_get_user):
        """Test voting on feature request"""
        mock_get_user.return_value = {'user_id': 'user1'}
        mock_table.get_item.return_value = {
            'Item': {'id': 'req1', 'votes': 5, 'voters': []}
        }
        
        event = {'pathParameters': {'request_id': 'req1'}}
        response = handle_vote_feature_request(event)
        
        assert response['statusCode'] == 200
        assert mock_table.update_item.called
