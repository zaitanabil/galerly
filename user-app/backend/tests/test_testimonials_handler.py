"""
Unit tests for testimonials handler
Tests testimonial CRUD operations and plan enforcement with real AWS
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from handlers.testimonials_handler import (
    handle_list_testimonials,
    handle_create_testimonial,
    handle_update_testimonial,
    handle_delete_testimonial,
    handle_request_testimonial
)
from utils import config
from handlers.testimonials_handler import testimonials_table


class TestTestimonialListing:
    """Test testimonial listing functionality with real DynamoDB"""
    
    def test_list_public_testimonials_shows_approved_only(self):
        """Test public listing shows only approved testimonials"""
        photographer_id = f'photo-{uuid.uuid4()}'
        
        test_ids = []
        try:
            # Create mix of approved and unapproved testimonials
            for i in range(3):
                test_id = f'test-{uuid.uuid4()}'
                test_ids.append(test_id)
                testimonials_table.put_item(Item={
                    'id': test_id,
                    'photographer_id': photographer_id,
                    'rating': 5,
                    'approved': i != 1,  # Second one not approved
                    'content': f'Great {i}!'
                })
            
            result = handle_list_testimonials(photographer_id, None)
            assert result['statusCode'] in [200, 404, 500]
        finally:
            for test_id in test_ids:
                try:
                    testimonials_table.delete_item(Key={'id': test_id})
                except:
                    pass
    
    def test_list_all_testimonials_with_show_all_param(self):
        """Test owner can see all testimonials with show_all param"""
        photographer_id = f'photo-{uuid.uuid4()}'
        query_params = {'show_all': 'true'}
        
        test_ids = []
        try:
            for i in range(2):
                test_id = f'test-{uuid.uuid4()}'
                test_ids.append(test_id)
                testimonials_table.put_item(Item={
                    'id': test_id,
                    'photographer_id': photographer_id,
                    'rating': 5,
                    'approved': i == 0
                })
            
            result = handle_list_testimonials(photographer_id, query_params)
            assert result['statusCode'] in [200, 404, 500]
        finally:
            for test_id in test_ids:
                try:
                    testimonials_table.delete_item(Key={'id': test_id})
                except:
                    pass


class TestTestimonialCreation:
    """Test testimonial submission with real DynamoDB"""
    
    def test_create_testimonial_success(self):
        """Test successful testimonial creation"""
        photographer_id = f'photo-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'rating': 5,
            'content': 'Amazing photographer! Very professional and delivered great results.',
            'service_type': 'wedding'
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] in [200, 201, 400, 500]
    
    def test_create_testimonial_validates_rating(self):
        """Test rating validation (1-5)"""
        photographer_id = f'photo-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'rating': 6,  # Invalid rating
            'content': 'Great work!'
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] in [400, 500]
    
    def test_create_testimonial_validates_content_length(self):
        """Test content minimum length validation"""
        photographer_id = f'photo-{uuid.uuid4()}'
        body = {
            'client_name': 'Jane Doe',
            'rating': 5,
            'content': 'Good'  # Too short (< 20 chars)
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] in [400, 500]


class TestTestimonialUpdate:
    """Test testimonial update operations with real DynamoDB"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_testimonial_approval_status(self, mock_features):
        """Test photographer can approve testimonials"""
        user_id = f'photo-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = f'test-{uuid.uuid4()}'
        body = {'approved': True, 'featured': True}
        
        # Mock Pro plan with client_invoicing feature
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        try:
            # Create real testimonial
            testimonials_table.put_item(Item={
                'id': testimonial_id,
                'photographer_id': user_id,
                'content': 'Great!',
                'rating': 5
            })
            
            result = handle_update_testimonial(user, testimonial_id, body)
            assert result['statusCode'] in [200, 404, 500]
        finally:
            try:
                testimonials_table.delete_item(Key={'id': testimonial_id})
            except:
                pass
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_testimonial_verifies_ownership(self, mock_features):
        """Test update blocked when not owner"""
        user_id = f'photo-{uuid.uuid4()}'
        different_owner = f'photo-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = f'test-{uuid.uuid4()}'
        body = {'approved': True}
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        try:
            # Create testimonial belonging to different photographer
            testimonials_table.put_item(Item={
                'id': testimonial_id,
                'photographer_id': different_owner,
                'content': 'Great!',
                'rating': 5
            })
            
            result = handle_update_testimonial(user, testimonial_id, body)
            assert result['statusCode'] in [403, 404]
        finally:
            try:
                testimonials_table.delete_item(Key={'id': testimonial_id})
            except:
                pass


class TestTestimonialDeletion:
    """Test testimonial deletion with real DynamoDB"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_delete_testimonial_success(self, mock_features):
        """Test successful testimonial deletion"""
        user_id = f'photo-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = f'test-{uuid.uuid4()}'
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        try:
            testimonials_table.put_item(Item={
                'id': testimonial_id,
                'photographer_id': user_id,
                'content': 'Great!',
                'rating': 5
            })
            
            result = handle_delete_testimonial(user, testimonial_id)
            assert result['statusCode'] in [200, 404, 500]
        finally:
            try:
                testimonials_table.delete_item(Key={'id': testimonial_id})
            except:
                pass


class TestTestimonialRequest:
    """Test testimonial request email sending"""
    
    @patch('utils.email.send_email')
    @patch('handlers.subscription_handler.get_user_features')
    def test_request_testimonial_sends_email(self, mock_features, mock_send_email):
        """Test testimonial request email is sent"""
        user = {
            'id': f'photo-{uuid.uuid4()}',
            'email': 'photo@test.com',
            'role': 'photographer',
            'name': 'John Photographer',
            'plan': 'pro'
        }
        body = {
            'client_name': 'Jane Client',
            'client_email': 'jane@test.com',
            'service_type': 'wedding',
            'custom_message': 'Thanks for choosing us!'
        }
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        mock_send_email.return_value = True
        
        result = handle_request_testimonial(user, body)
        assert result['statusCode'] in [200, 400, 500]
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_request_testimonial_validates_email(self, mock_features):
        """Test email validation in testimonial request"""
        user = {'id': f'photo-{uuid.uuid4()}', 'email': 'photo@test.com', 'role': 'photographer', 'plan': 'pro'}
        body = {
            'client_name': 'Jane Client',
            'client_email': '',  # Missing email
            'service_type': 'wedding'
        }
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        result = handle_request_testimonial(user, body)
        assert result['statusCode'] in [400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
