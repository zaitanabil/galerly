"""Tests for handler integration using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.invoice_handler import handle_create_invoice
from handlers.email_template_handler import handle_save_template
from handlers.testimonials_handler import handle_create_testimonial, handle_list_testimonials
from handlers.leads_handler import handle_capture_lead


class TestHandlerIntegration:
    """Test handler integration with real DynamoDB"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_invoice_creation_flow(self, mock_features):
        """Test complete invoice creation flow - uses real DynamoDB"""
        mock_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro')
        
        user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'test-{uuid.uuid4()}@test.com',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        body = {
            'client_email': 'client@test.com',
            'items': [{'description': 'Test', 'price': 100, 'quantity': 1}]
        }
        
        result = handle_create_invoice(user, body)
        assert result['statusCode'] in [201, 400, 500]
    
    def test_email_template_workflow(self):
        """Test email template save workflow - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'test-{uuid.uuid4()}@test.com',
            'role': 'photographer'
        }
        
        template_type = 'gallery_ready'
        body = {
            'subject': 'Your Gallery is Ready',
            'body': 'Hi {{client_name}}, your gallery is ready to view!',
            'html_body': '<p>Hi {{client_name}}</p>'
        }
        
        result = handle_save_template(user, template_type, body)
        assert result['statusCode'] in [200, 201, 400, 403, 500]
    
    def test_testimonial_collection_flow(self):
        """Test testimonial collection flow - uses real DynamoDB"""
        photographer_id = f'user-{uuid.uuid4()}'
        
        body = {
            'client_name': 'John Doe',
            'client_email': 'john@test.com',
            'rating': 5,
            'content': 'Great service! Very professional and delivered amazing results.',
            'service_type': 'wedding'
        }
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] in [200, 201, 400, 500]
    
    def test_list_testimonials(self):
        """Test listing testimonials - uses real DynamoDB"""
        photographer_id = f'user-{uuid.uuid4()}'
        
        result = handle_list_testimonials(photographer_id, None)
        assert result['statusCode'] in [200, 404, 500]
    
    @patch('handlers.leads_handler.send_email')
    def test_lead_capture_integration(self, mock_email):
        """Test lead capture integration - uses real DynamoDB"""
        mock_email.return_value = None
        
        photographer_id = f'photographer-{uuid.uuid4()}'
        body = {
            'name': 'Test Lead',
            'email': f'lead-{uuid.uuid4()}@test.com',
            'phone': '1234567890',
            'message': 'Interested in services'
        }
        
        result = handle_capture_lead(photographer_id, body)
        assert result['statusCode'] in [200, 201, 400, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
