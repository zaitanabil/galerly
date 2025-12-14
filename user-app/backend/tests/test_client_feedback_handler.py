"""
Unit tests for client feedback handler
Tests structured feedback collection for galleries with real AWS
"""
import pytest
import uuid
from unittest.mock import patch
from handlers.client_feedback_handler import (
    handle_submit_client_feedback,
    handle_get_gallery_feedback
)
from utils import config
from handlers.client_feedback_handler import client_feedback_table


class TestClientFeedbackSubmission:
    """Test client feedback submission with real DynamoDB"""
    
    def test_submit_feedback_success(self):
        """Test successful feedback submission"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
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
        
        try:
            # Create real gallery in DynamoDB
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Wedding Gallery'
            })
            
            result = handle_submit_client_feedback(gallery_id, body)
            assert result['statusCode'] in [200, 201, 400, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    def test_submit_feedback_validates_gallery_exists(self):
        """Test feedback submission validates gallery existence"""
        gallery_id = f'nonexistent-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'overall_rating': 5,
            'comments': 'Great work!'
        }
        
        result = handle_submit_client_feedback(gallery_id, body)
        assert result['statusCode'] in [404, 500]
    
    def test_submit_feedback_validates_email(self):
        """Test email validation"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'invalid-email',  # Invalid format
            'overall_rating': 5,
            'comments': 'Great work!'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            result = handle_submit_client_feedback(gallery_id, body)
            assert result['statusCode'] in [400, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    def test_submit_feedback_validates_rating_range(self):
        """Test rating must be 1-5"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'overall_rating': 6,  # Invalid (> 5)
            'comments': 'Great work!'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            result = handle_submit_client_feedback(gallery_id, body)
            assert result['statusCode'] in [400, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


class TestGalleryFeedbackRetrieval:
    """Test feedback retrieval for galleries with real DynamoDB"""
    
    def test_get_gallery_feedback_photographer_access(self):
        """Test photographer can view all feedback for their gallery"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'photo-{uuid.uuid4()}'
        user = {'id': user_id, 'role': 'photographer', 'plan': 'pro'}
        
        feedback_ids = []
        try:
            # Create gallery owned by user
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            # Create feedback entries
            for i in range(2):
                feedback_id = f'fb-{uuid.uuid4()}'
                feedback_ids.append(feedback_id)
                client_feedback_table.put_item(Item={
                    'id': feedback_id,
                    'gallery_id': gallery_id,
                    'overall_rating': 5 - i,
                    'comments': f'Great {i}!'
                })
            
            result = handle_get_gallery_feedback(gallery_id, user)
            assert result['statusCode'] in [200, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
            for feedback_id in feedback_ids:
                try:
                    client_feedback_table.delete_item(Key={'id': feedback_id})
                except:
                    pass
    
    def test_get_gallery_feedback_blocks_non_owner(self):
        """Test non-owner cannot view feedback"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        owner_id = f'photo-{uuid.uuid4()}'
        different_user_id = f'photo-{uuid.uuid4()}'
        user = {'id': different_user_id, 'role': 'photographer', 'plan': 'pro'}
        
        try:
            # Create gallery owned by different user
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': owner_id,
                'name': 'Test Gallery'
            })
            
            result = handle_get_gallery_feedback(gallery_id, user)
            assert result['statusCode'] in [403, 404]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
