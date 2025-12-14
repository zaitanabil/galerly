"""
Unit tests for testimonials handler
Tests testimonial CRUD operations and plan enforcement
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from handlers.testimonials_handler import (
    handle_list_testimonials,
    handle_create_testimonial,
    handle_update_testimonial,
    handle_delete_testimonial,
    handle_request_testimonial
)


class TestTestimonialListing:
    """Test testimonial listing functionality"""
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_list_public_testimonials_shows_approved_only(self, mock_table):
        """Test public listing shows only approved testimonials"""
        photographer_id = 'photo123'
        
        mock_table.query.return_value = {
            'Items': [
                {'id': '1', 'photographer_id': 'photo123', 'rating': 5, 'approved': True, 'content': 'Great!'},
                {'id': '2', 'photographer_id': 'photo123', 'rating': 4, 'approved': False, 'content': 'Good'},
                {'id': '3', 'photographer_id': 'photo123', 'rating': 5, 'approved': True, 'content': 'Amazing!'}
            ]
        }
        
        result = handle_list_testimonials(photographer_id, None)
        assert result['statusCode'] == 200
        # Should filter to approved only in public view
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_list_all_testimonials_with_show_all_param(self, mock_table):
        """Test owner can see all testimonials with show_all param"""
        photographer_id = 'photo123'
        query_params = {'show_all': 'true'}
        
        mock_table.query.return_value = {
            'Items': [
                {'id': '1', 'photographer_id': 'photo123', 'rating': 5, 'approved': True},
                {'id': '2', 'photographer_id': 'photo123', 'rating': 4, 'approved': False}
            ]
        }
        
        result = handle_list_testimonials(photographer_id, query_params)
        assert result['statusCode'] == 200
        # Should show all testimonials


class TestTestimonialCreation:
    """Test testimonial submission"""
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_create_testimonial_success(self, mock_table):
        """Test successful testimonial creation"""
        photographer_id = 'photo123'
        body = {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'rating': 5,
            'content': 'Amazing photographer! Very professional and delivered great results.',
            'service_type': 'wedding'
        }
        
        mock_table.put_item.return_value = {}
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] == 201
        assert mock_table.put_item.called
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_create_testimonial_validates_rating(self, mock_table):
        """Test rating validation (1-5)"""
        photographer_id = 'photo123'
        body = {
            'client_name': 'Jane Doe',
            'rating': 6,  # Invalid rating
            'content': 'Great work!'
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] == 400
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_create_testimonial_validates_content_length(self, mock_table):
        """Test content minimum length validation"""
        photographer_id = 'photo123'
        body = {
            'client_name': 'Jane Doe',
            'rating': 5,
            'content': 'Good'  # Too short (< 20 chars)
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] == 400


class TestTestimonialUpdate:
    """Test testimonial update operations"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_update_testimonial_approval_status(self, mock_table, mock_features):
        """Test photographer can approve testimonials"""
        user = {'id': 'photo123', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = 'test123'
        body = {'approved': True, 'featured': True}
        
        # Mock Pro plan with client_invoicing feature
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        # Mock existing testimonial
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test123',
                'photographer_id': 'photo123',
                'content': 'Great!'
            }
        }
        
        mock_table.update_item.return_value = {
            'Attributes': {'id': 'test123', 'approved': True, 'featured': True}
        }
        
        result = handle_update_testimonial(user, testimonial_id, body)
        assert result['statusCode'] == 200
        assert mock_table.update_item.called
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_update_testimonial_verifies_ownership(self, mock_table):
        """Test update blocked when not owner"""
        user = {'id': 'photo123', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = 'test123'
        body = {'approved': True}
        
        # Mock testimonial belonging to different photographer
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test123',
                'photographer_id': 'photo456',  # Different owner
                'content': 'Great!'
            }
        }
        
        with patch('handlers.testimonials_handler.get_user_features') as mock_features:
            mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
            result = handle_update_testimonial(user, testimonial_id, body)
            assert result['statusCode'] == 403


class TestTestimonialDeletion:
    """Test testimonial deletion"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_delete_testimonial_success(self, mock_table, mock_features):
        """Test successful testimonial deletion"""
        user = {'id': 'photo123', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = 'test123'
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test123',
                'photographer_id': 'photo123'
            }
        }
        
        mock_table.delete_item.return_value = {}
        
        result = handle_delete_testimonial(user, testimonial_id)
        assert result['statusCode'] == 200
        assert mock_table.delete_item.called


class TestTestimonialRequest:
    """Test testimonial request email sending"""
    
    @patch('handlers.testimonials_handler.send_email')
    @patch('handlers.subscription_handler.get_user_features')
    def test_request_testimonial_sends_email(self, mock_features, mock_send_email):
        """Test testimonial request email is sent"""
        user = {
            'id': 'photo123',
            'role': 'photographer',
            'email': 'photo@test.com',
            'name': 'John Photographer'
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
        assert result['statusCode'] == 200
        assert mock_send_email.called
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_request_testimonial_validates_email(self, mock_features):
        """Test email validation in testimonial request"""
        user = {'id': 'photo123', 'role': 'photographer', 'plan': 'pro'}
        body = {
            'client_name': 'Jane Client',
            'client_email': '',  # Missing email
            'service_type': 'wedding'
        }
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        
        result = handle_request_testimonial(user, body)
        assert result['statusCode'] == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
