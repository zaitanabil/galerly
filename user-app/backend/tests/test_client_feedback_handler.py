"""
Unit tests for client feedback handler
Tests structured feedback collection for galleries
"""
import pytest
from unittest.mock import Mock, patch
from handlers.client_feedback_handler import (
    handle_submit_client_feedback,
    handle_get_gallery_feedback
)


class TestClientFeedbackSubmission:
    """Test client feedback submission"""
    
    @patch('handlers.client_feedback_handler.client_feedback_table')
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_submit_feedback_success(self, mock_galleries, mock_feedback):
        """Test successful feedback submission"""
        gallery_id = 'gallery123'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'overall_rating': 5,
            'photo_quality_rating': 5,
            'delivery_time_rating': 4,
            'communication_rating': 5,
            'value_rating': 5,
            'would_recommend': True,
            'comments': 'Amazing photographer! Very professional.',
            'photo_feedback': [
                {'photo_id': 'photo1', 'rating': 5, 'comment': 'Love this shot!'}
            ]
        }
        
        # Mock gallery exists
        mock_galleries.query.return_value = {
            'Items': [{
                'id': 'gallery123',
                'user_id': 'photo123',
                'name': 'Wedding Gallery'
            }]
        }
        
        mock_feedback.put_item.return_value = {}
        
        result = handle_submit_client_feedback(gallery_id, body)
        assert result['statusCode'] == 200  # Handler returns 200, not 201
        assert mock_feedback.put_item.called
    
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_submit_feedback_validates_gallery_exists(self, mock_galleries):
        """Test feedback submission validates gallery existence"""
        gallery_id = 'nonexistent'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'overall_rating': 5,
            'comments': 'Great work!'
        }
        
        # Mock gallery not found
        mock_galleries.query.return_value = {'Items': []}
        
        result = handle_submit_client_feedback(gallery_id, body)
        assert result['statusCode'] == 404
    
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_submit_feedback_validates_email(self, mock_galleries):
        """Test email validation"""
        gallery_id = 'gallery123'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'invalid-email',  # Invalid format
            'overall_rating': 5,
            'comments': 'Great work!'
        }
        
        mock_galleries.query.return_value = {
            'Items': [{'id': 'gallery123', 'user_id': 'photo123'}]
        }
        
        result = handle_submit_client_feedback(gallery_id, body)
        assert result['statusCode'] == 400
    
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_submit_feedback_validates_rating_range(self, mock_galleries):
        """Test rating must be 1-5"""
        gallery_id = 'gallery123'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'overall_rating': 6,  # Invalid (> 5)
            'comments': 'Great work!'
        }
        
        mock_galleries.query.return_value = {
            'Items': [{'id': 'gallery123', 'user_id': 'photo123'}]
        }
        
        result = handle_submit_client_feedback(gallery_id, body)
        assert result['statusCode'] == 400


class TestGalleryFeedbackRetrieval:
    """Test feedback retrieval for galleries"""
    
    @patch('handlers.client_feedback_handler.client_feedback_table')
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_get_gallery_feedback_photographer_access(self, mock_galleries, mock_feedback):
        """Test photographer can view all feedback for their gallery"""
        gallery_id = 'gallery123'
        user = {'id': 'photo123', 'role': 'photographer', 'plan': 'pro'}
        
        # Mock gallery ownership - use get_item, not query
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'photo123',
                'name': 'Test Gallery'
            }
        }
        
        # Mock feedback
        mock_feedback.query.return_value = {
            'Items': [
                {'id': 'fb1', 'overall_rating': 5, 'comments': 'Great!'},
                {'id': 'fb2', 'overall_rating': 4, 'comments': 'Good work'}
            ]
        }
        
        result = handle_get_gallery_feedback(gallery_id, user)
        assert result['statusCode'] == 200
    
    @patch('handlers.client_feedback_handler.galleries_table')
    def test_get_gallery_feedback_blocks_non_owner(self, mock_galleries):
        """Test non-owner cannot view feedback"""
        gallery_id = 'gallery123'
        user = {'id': 'photo456', 'role': 'photographer', 'plan': 'pro'}  # Different owner
        
        # Mock gallery not found for this user (get_item returns nothing)
        mock_galleries.get_item.return_value = {}
        
        result = handle_get_gallery_feedback(gallery_id, user)
        assert result['statusCode'] == 404  # Returns 404, not 403


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
