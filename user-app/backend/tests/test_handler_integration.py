"""
Integration tests for handler decorators and plan enforcement
Tests end-to-end functionality of decorated handlers
"""
import pytest
from unittest.mock import Mock, patch
import json


class TestDecoratorIntegration:
    """Test decorator integration across handlers"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.invoice_handler.invoices_table')
    def test_invoice_creation_with_pro_plan(self, mock_table, mock_features):
        """Test invoice creation succeeds with Pro plan"""
        from handlers.invoice_handler import handle_create_invoice
        
        user = {'id': 'user123', 'email': 'user@test.com', 'role': 'photographer', 'plan': 'pro'}
        body = {
            'client_name': 'Test Client',
            'client_email': 'client@test.com',
            'amount': 1000,
            'due_date': '2025-12-31',
            'items': [{'description': 'Photography service', 'quantity': 1, 'price': 1000}]
        }
        
        # Mock Pro plan with invoicing feature
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        mock_table.put_item.return_value = {}
        
        result = handle_create_invoice(user, body)
        assert result['statusCode'] == 201
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_raw_vault_blocked_without_ultimate_plan(self, mock_features):
        """Test RAW vault blocked without Ultimate plan"""
        from handlers.raw_vault_handler import handle_archive_raw_file
        
        user = {'id': 'user123', 'email': 'test@example.com', 'role': 'photographer', 'plan': 'pro'}
        body = {'photo_id': 'photo123', 'filename': 'test.raw'}
        
        # Mock Pro plan without raw_vault feature
        mock_features.return_value = ({'raw_vault': False}, {}, 'pro')
        
        result = handle_archive_raw_file(user, body)
        assert result['statusCode'] == 403
        response_body = json.loads(result['body'])
        assert 'upgrade_required' in response_body
    
    def test_client_role_blocked_from_photographer_functions(self):
        """Test client role blocked from photographer-only functions"""
        from handlers.gallery_handler import handle_create_gallery
        
        client_user = {'id': 'client123', 'role': 'client'}
        body = {'name': 'Test Gallery', 'client_name': 'Client Name'}
        
        result = handle_create_gallery(client_user, body)
        assert result['statusCode'] == 403
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.email_template_handler.email_templates_table')
    def test_email_templates_requires_pro_plan(self, mock_table, mock_features):
        """Test email template management requires Pro plan"""
        from handlers.email_template_handler import handle_save_template  # Changed from handle_create_template
        
        user = {'id': 'user123', 'email': 'test@example.com', 'role': 'photographer', 'plan': 'starter'}
        body = {
            'template_type': 'gallery_shared',
            'subject': 'Welcome!',
            'body': 'Hello {client_name}'
        }
        
        # Mock Starter plan without custom templates
        mock_features.return_value = ({'custom_email_templates': False}, {}, 'starter')
        
        result = handle_save_template(user, body)
        assert result['statusCode'] == 403


class TestMultipleDecoratorStacking:
    """Test handlers with multiple stacked decorators"""
    
    @patch('handlers.subscription_handler.get_user_features')
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_testimonial_management_requires_plan_and_role(self, mock_table, mock_features):
        """Test testimonial management requires both Pro plan and photographer role"""
        from handlers.testimonials_handler import handle_update_testimonial
        
        # Test with correct plan and role
        user = {'id': 'photo123', 'email': 'test@example.com', 'role': 'photographer', 'plan': 'pro'}
        testimonial_id = 'test123'
        body = {'approved': True}
        
        mock_features.return_value = ({'client_invoicing': True}, {}, 'pro')
        mock_table.get_item.return_value = {
            'Item': {'id': 'test123', 'photographer_id': 'photo123'}
        }
        mock_table.update_item.return_value = {'Attributes': {}}
        
        result = handle_update_testimonial(user, testimonial_id, body)
        assert result['statusCode'] == 200


class TestPublicEndpointsNoDecorators:
    """Test public endpoints work without authentication"""
    
    @patch('handlers.testimonials_handler.testimonials_table')
    def test_public_testimonial_creation(self, mock_table):
        """Test public can submit testimonials"""
        from handlers.testimonials_handler import handle_create_testimonial
        
        photographer_id = 'photo123'
        body = {
            'client_name': 'Jane Doe',
            'rating': 5,
            'content': 'Excellent photographer! Highly recommend for any event.'
        }
        
        mock_table.put_item.return_value = {}
        
        result = handle_create_testimonial(photographer_id, body)
        assert result['statusCode'] == 200  # Handler returns 200, not 201
    
    @patch('handlers.leads_handler.leads_table')
    @patch('handlers.leads_handler.users_table')
    def test_public_lead_capture(self, mock_users, mock_leads):
        """Test public can submit leads"""
        from handlers.leads_handler import handle_capture_lead
        
        photographer_id = 'photo123'
        body = {
            'name': 'John Client',
            'email': 'john@test.com',
            'message': 'Interested in wedding photography services for June 2025.',
            'service_type': 'wedding'
        }
        
        # Mock photographer exists
        mock_users.get_item.return_value = {
            'Item': {'id': 'photo123', 'name': 'Pro Photographer'}
        }
        mock_leads.put_item.return_value = {}
        
        result = handle_capture_lead(photographer_id, body)
        assert result['statusCode'] == 200  # Handler returns 200, not 201


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
