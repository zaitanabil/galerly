"""
Tests for email_template_handler.py - Pro Feature
Tests cover: list templates, get template, save template, delete template, preview, Pro plan enforcement
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_template_dependencies():
    """Mock email template dependencies."""
    with patch('handlers.email_template_handler.email_templates_table') as mock_table, \
         patch('handlers.email_template_handler.check_pro_plan') as mock_check_pro:
        # Mock Pro plan check to return True by default
        mock_check_pro.return_value = True
        yield {
            'table': mock_table,
            'check_pro': mock_check_pro
        }

@pytest.fixture
def sample_pro_user():
    """Sample Pro plan user."""
    return {
        'id': 'user_pro',
        'email': 'pro@example.com',
        'name': 'Pro User',
        'plan': 'pro'
    }

@pytest.fixture
def sample_free_user():
    """Sample free plan user."""
    return {
        'id': 'user_free',
        'email': 'free@example.com',
        'name': 'Free User',
        'plan': 'free'
    }

class TestListTemplates:
    """Tests for handle_list_templates endpoint."""
    
    def test_list_templates_pro_user(self, sample_pro_user, mock_template_dependencies):
        """Pro user can list templates."""
        from handlers.email_template_handler import handle_list_templates
        
        mock_template_dependencies['table'].query.return_value = {
            'Items': [
                {'user_id': 'user_pro', 'template_type': 'gallery_shared_with_account', 'updated_at': '2024-01-01'}
            ]
        }
        
        result = handle_list_templates(sample_pro_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'templates' in body
        assert body['custom_count'] == 1
        assert body['total_available'] > 0
    
    def test_list_templates_free_user(self, sample_free_user, mock_template_dependencies):
        """Free user cannot list templates."""
        from handlers.email_template_handler import handle_list_templates
        
        # FIX: Override fixture to return False for free user
        mock_template_dependencies['check_pro'].return_value = False
        
        result = handle_list_templates(sample_free_user)
        
        assert result['statusCode'] == 403
        body = json.loads(result['body'])
        assert 'upgrade_required' in body
        assert body['upgrade_required'] == True

class TestGetTemplate:
    """Tests for handle_get_template endpoint."""
    
    def test_get_custom_template(self, sample_pro_user, mock_template_dependencies):
        """Get user's custom template."""
        from handlers.email_template_handler import handle_get_template
        
        mock_template_dependencies['table'].get_item.return_value = {
            'Item': {
                'user_id': 'user_pro',
                'template_type': 'gallery_shared_with_account',
                'subject': 'Custom Subject',
                'html_body': '<html>Custom HTML</html>',
                'text_body': 'Custom Text'
            }
        }
        
        result = handle_get_template(sample_pro_user, 'gallery_shared_with_account')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['is_custom'] == True
        assert body['template']['subject'] == 'Custom Subject'
    
    def test_get_default_template(self, sample_pro_user, mock_template_dependencies):
        """Get default template when no custom exists."""
        from handlers.email_template_handler import handle_get_template
        
        mock_template_dependencies['table'].get_item.return_value = {}
        
        result = handle_get_template(sample_pro_user, 'gallery_shared_with_account')
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['is_custom'] == False
        assert 'variables' in body
    
    def test_get_invalid_template_type(self, sample_pro_user, mock_template_dependencies):
        """Cannot get invalid template type."""
        from handlers.email_template_handler import handle_get_template
        
        result = handle_get_template(sample_pro_user, 'invalid_type')
        
        assert result['statusCode'] == 400
    
    def test_get_template_free_user(self, sample_free_user, mock_template_dependencies):
        """Free user cannot get templates."""
        from handlers.email_template_handler import handle_get_template
        
        # FIX: Override fixture to return False for free user
        mock_template_dependencies['check_pro'].return_value = False
        
        result = handle_get_template(sample_free_user, 'gallery_shared_with_account')
        
        assert result['statusCode'] == 403

class TestSaveTemplate:
    """Tests for handle_save_template endpoint."""
    
    def test_save_template_success(self, sample_pro_user, mock_template_dependencies):
        """Save custom template successfully."""
        from handlers.email_template_handler import handle_save_template
        
        mock_template_dependencies['table'].get_item.return_value = {}
        
        body = {
            'subject': 'New Gallery: {gallery_name}',
            'html_body': '<html><body>Hi {client_name}, check out {gallery_url}</body></html>',
            'text_body': 'Hi {client_name}, view at {gallery_url}'
        }
        
        result = handle_save_template(sample_pro_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 200
        mock_template_dependencies['table'].put_item.assert_called_once()
    
    def test_save_template_missing_subject(self, sample_pro_user, mock_template_dependencies):
        """Cannot save template without subject."""
        from handlers.email_template_handler import handle_save_template
        
        body = {
            'html_body': '<html>Test</html>',
            'text_body': 'Test'
        }
        
        result = handle_save_template(sample_pro_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 400
    
    def test_save_template_missing_body(self, sample_pro_user, mock_template_dependencies):
        """Cannot save template without any body."""
        from handlers.email_template_handler import handle_save_template
        
        body = {
            'subject': 'Test Subject'
        }
        
        result = handle_save_template(sample_pro_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 400
    
    def test_save_template_invalid_type(self, sample_pro_user, mock_template_dependencies):
        """Cannot save invalid template type."""
        from handlers.email_template_handler import handle_save_template
        
        body = {
            'subject': 'Test',
            'html_body': '<html>Test</html>'
        }
        
        result = handle_save_template(sample_pro_user, 'invalid_type', body)
        
        assert result['statusCode'] == 400
    
    def test_save_template_free_user(self, sample_free_user, mock_template_dependencies):
        """Free user cannot save templates."""
        from handlers.email_template_handler import handle_save_template
        
        # FIX: Override fixture to return False for free user
        mock_template_dependencies['check_pro'].return_value = False
        
        body = {
            'subject': 'Test',
            'html_body': '<html>Test</html>'
        }
        
        result = handle_save_template(sample_free_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 403

class TestDeleteTemplate:
    """Tests for handle_delete_template endpoint."""
    
    def test_delete_template_success(self, sample_pro_user, mock_template_dependencies):
        """Delete custom template successfully."""
        from handlers.email_template_handler import handle_delete_template
        
        result = handle_delete_template(sample_pro_user, 'gallery_shared_with_account')
        
        assert result['statusCode'] == 200
        mock_template_dependencies['table'].delete_item.assert_called_once()
    
    def test_delete_template_invalid_type(self, sample_pro_user, mock_template_dependencies):
        """Cannot delete invalid template type."""
        from handlers.email_template_handler import handle_delete_template
        
        result = handle_delete_template(sample_pro_user, 'invalid_type')
        
        assert result['statusCode'] == 400
    
    def test_delete_template_free_user(self, sample_free_user, mock_template_dependencies):
        """Free user cannot delete templates."""
        from handlers.email_template_handler import handle_delete_template
        
        # FIX: Override fixture to return False for free user
        mock_template_dependencies['check_pro'].return_value = False
        
        result = handle_delete_template(sample_free_user, 'gallery_shared_with_account')
        
        assert result['statusCode'] == 403

class TestPreviewTemplate:
    """Tests for handle_preview_template endpoint."""
    
    def test_preview_template_success(self, sample_pro_user, mock_template_dependencies):
        """Preview template with sample data."""
        from handlers.email_template_handler import handle_preview_template
        
        body = {
            'subject': 'Gallery: {gallery_name}',
            'html_body': '<html>Hi {client_name}, view at {gallery_url}</html>',
            'text_body': 'Hi {client_name}, view at {gallery_url}'
        }
        
        result = handle_preview_template(sample_pro_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'preview' in response_body
        assert 'Sample Wedding Gallery' in response_body['preview']['subject']
        assert 'John Smith' in response_body['preview']['html']
    
    def test_preview_template_invalid_variable(self, sample_pro_user, mock_template_dependencies):
        """Preview fails with invalid variable."""
        from handlers.email_template_handler import handle_preview_template
        
        body = {
            'subject': 'Gallery: {invalid_var}',
            'html_body': '<html>Test</html>',
            'text_body': 'Test'
        }
        
        result = handle_preview_template(sample_pro_user, 'gallery_shared_with_account', body)
        
        assert result['statusCode'] == 400
    
    def test_preview_template_free_user(self, sample_free_user, mock_template_dependencies):
        """Free user cannot preview templates."""
        from handlers.email_template_handler import handle_preview_template
        
        # FIX: Override fixture to return False for free user
        mock_template_dependencies['check_pro'].return_value = False
        
        body = {
            'subject': 'Test',
            'html_body': '<html>Test</html>'
        }
        
        result = handle_preview_template(sample_free_user, 'gallery_shared', body)
        
        assert result['statusCode'] == 403

class TestGetUserTemplate:
    """Tests for get_user_template utility function."""
    
    def test_get_user_custom_template(self, mock_template_dependencies):
        """Get user's custom template."""
        from handlers.email_template_handler import get_user_template
        
        mock_template_dependencies['table'].get_item.return_value = {
            'Item': {
                'subject': 'Custom',
                'html_body': '<html>Custom</html>',
                'text_body': 'Custom'
            }
        }
        
        template = get_user_template('user_123', 'gallery_shared_with_account')
        
        assert template['subject'] == 'Custom'
        assert template['html'] == '<html>Custom</html>'
    
    def test_get_user_default_template(self, mock_template_dependencies):
        """Get default template when no custom exists."""
        from handlers.email_template_handler import get_user_template
        
        mock_template_dependencies['table'].get_item.return_value = {}
        
        template = get_user_template('user_123', 'gallery_shared_with_account')
        
        # Should return default template
        assert 'subject' in template
        assert 'html' in template

class TestPlanEnforcement:
    """Tests for Pro plan enforcement across all endpoints."""
    
    def test_plus_plan_denied(self, mock_template_dependencies):
        """Plus plan users cannot access templates."""
        from handlers.email_template_handler import handle_list_templates
        
        # FIX: Override fixture to return False for plus plan user
        mock_template_dependencies['check_pro'].return_value = False
        
        plus_user = {
            'id': 'user_plus',
            'email': 'plus@example.com',
            'plan': 'plus'
        }
        
        result = handle_list_templates(plus_user)
        
        assert result['statusCode'] == 403
    
    def test_pro_plan_allowed(self, mock_template_dependencies):
        """Pro plan is allowed."""
        from handlers.email_template_handler import handle_list_templates
        
        pro_user = {
            'id': 'user_prof',
            'email': 'prof@example.com',
            'plan': 'pro'
        }
        
        mock_template_dependencies['table'].query.return_value = {'Items': []}
        
        result = handle_list_templates(pro_user)
        
        assert result['statusCode'] == 200

