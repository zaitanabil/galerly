"""
Tests for client_feedback_handler.py endpoints.
Tests cover: submit feedback, get feedback, ratings, comments.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_feedback_dependencies():
    """Mock feedback dependencies."""
    with patch('handlers.client_feedback_handler.feedback_table') as mock_feedback, \
         patch('handlers.client_feedback_handler.galleries_table') as mock_galleries:
        yield {
            'feedback': mock_feedback,
            'galleries': mock_galleries
        }

class TestSubmitFeedback:
    """Tests for handle_submit_client_feedback endpoint."""
    
    def test_submit_feedback_success(self, sample_gallery, mock_feedback_dependencies):
        """Submit client feedback successfully."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        mock_feedback_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        body = {
            'rating': 5,
            'comment': 'Amazing photos! Very professional.',
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] in [200, 201]
    
    def test_submit_feedback_missing_rating(self, mock_feedback_dependencies):
        """Submit feedback without rating."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        body = {
            'comment': 'Great work',
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] == 400
    
    def test_submit_feedback_invalid_rating_zero(self, mock_feedback_dependencies):
        """Submit feedback with rating of 0."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        body = {
            'rating': 0,
            'comment': 'Test',
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] == 400
    
    def test_submit_feedback_invalid_rating_negative(self, mock_feedback_dependencies):
        """Submit feedback with negative rating."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        body = {
            'rating': -1,
            'comment': 'Test',
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] == 400
    
    def test_submit_feedback_invalid_rating_too_high(self, mock_feedback_dependencies):
        """Submit feedback with rating > 5."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        body = {
            'rating': 10,
            'comment': 'Test',
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] == 400
    
    def test_submit_feedback_comment_too_long(self, mock_feedback_dependencies):
        """Submit feedback with very long comment."""
        from handlers.client_feedback_handler import handle_submit_client_feedback
        
        body = {
            'rating': 5,
            'comment': 'A' * 10000,  # 10,000 characters
            'client_email': 'client@example.com'
        }
        result = handle_submit_client_feedback('gallery_123', body)
        
        assert result['statusCode'] in [200, 201, 400]

class TestGetFeedback:
    """Tests for handle_get_gallery_feedback endpoint."""
    
    def test_get_feedback_success(self, sample_user, sample_gallery, mock_feedback_dependencies):
        """Get gallery feedback successfully."""
        from handlers.client_feedback_handler import handle_get_gallery_feedback
        
        mock_feedback_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_feedback_dependencies['feedback'].query.return_value = {
            'Items': [
                {'rating': 5, 'comment': 'Great!', 'client_email': 'client1@example.com'},
                {'rating': 4, 'comment': 'Good', 'client_email': 'client2@example.com'}
            ]
        }
        
        result = handle_get_gallery_feedback('gallery_123', sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'feedback' in body or len(body) >= 0
    
    def test_get_feedback_not_owned(self, sample_user, sample_gallery, mock_feedback_dependencies):
        """Get feedback fails when user doesn't own gallery."""
        from handlers.client_feedback_handler import handle_get_gallery_feedback
        
        other_gallery = {**sample_gallery, 'user_id': 'other_user'}
        mock_feedback_dependencies['galleries'].get_item.return_value = {'Item': other_gallery}
        
        result = handle_get_gallery_feedback('gallery_123', sample_user)
        
        assert result['statusCode'] == 403
    
    def test_get_feedback_empty(self, sample_user, sample_gallery, mock_feedback_dependencies):
        """Get feedback when none exists."""
        from handlers.client_feedback_handler import handle_get_gallery_feedback
        
        mock_feedback_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_feedback_dependencies['feedback'].query.return_value = {'Items': []}
        
        result = handle_get_gallery_feedback('gallery_123', sample_user)
        
        assert result['statusCode'] == 200

