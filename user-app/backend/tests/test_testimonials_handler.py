"""Tests for Testimonials Handler"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.testimonials_handler import handle_list_testimonials, handle_create_testimonial

class TestTestimonialsHandler:
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_list_testimonials(self, mock_table):
        mock_table.query.return_value = {'Items': [{'id': 'test1', 'rating': 5, 'approved': True}]}
        response = handle_list_testimonials('photo1', query_params={})
        assert response['statusCode'] == 200
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_create_testimonial(self, mock_table):
        photographer_id = 'photo1'
        # Content must be at least 20 characters per handler validation
        body = {'client_name': 'Test Client', 'rating': 5, 'content': 'This photographer did an amazing job capturing our special day!', 'client_email': 'test@example.com'}
        response = handle_create_testimonial(photographer_id, body)
        assert response['statusCode'] == 200
        assert mock_table.put_item.called
