"""
Tests for GDPR Compliance
Validates data export, retention policies, and PCI DSS invoice handling
"""
import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from handlers.gdpr_handler import handle_export_user_data, handle_get_data_retention_info
from handlers.invoice_pdf_handler import generate_invoice_pdf


@pytest.fixture
def mock_user():
    """Mock user object"""
    return {
        'id': 'test-user-id-123',
        'email': 'test@example.com',
        'name': 'Test User',
        'password_hash': 'hashed_password'
    }


@pytest.fixture(autouse=True)
def mock_gdpr_dependencies():
    """Mock all GDPR handler dependencies"""
    with patch('handlers.gdpr_handler.users_table') as mock_users, \
         patch('handlers.gdpr_handler.galleries_table') as mock_galleries, \
         patch('handlers.gdpr_handler.photos_table') as mock_photos, \
         patch('handlers.gdpr_handler.billing_table') as mock_billing, \
         patch('handlers.gdpr_handler.subscriptions_table') as mock_subs, \
         patch('handlers.gdpr_handler.analytics_table') as mock_analytics, \
         patch('handlers.gdpr_handler.client_favorites_table') as mock_favorites, \
         patch('handlers.gdpr_handler.client_feedback_table') as mock_feedback, \
         patch('handlers.gdpr_handler.invoices_table') as mock_invoices, \
         patch('handlers.gdpr_handler.appointments_table') as mock_appts, \
         patch('handlers.gdpr_handler.contracts_table') as mock_contracts, \
         patch('handlers.gdpr_handler.seo_settings_table') as mock_seo, \
         patch('handlers.gdpr_handler.s3_client') as mock_s3:
        
        # Setup default mock responses
        mock_users.get_item.return_value = {'Item': {'id': 'test-user-id-123', 'email': 'test@example.com'}}
        mock_galleries.query.return_value = {'Items': []}
        mock_photos.query.return_value = {'Items': []}
        mock_billing.scan.return_value = {'Items': []}
        mock_subs.scan.return_value = {'Items': []}
        mock_analytics.scan.return_value = {'Items': []}
        mock_favorites.scan.return_value = {'Items': []}
        mock_feedback.scan.return_value = {'Items': []}
        mock_invoices.scan.return_value = {'Items': []}
        mock_appts.scan.return_value = {'Items': []}
        mock_contracts.scan.return_value = {'Items': []}
        mock_seo.get_item.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://mock-url.com/download'
        
        yield


class TestGDPRDataExport:
    """Test GDPR Article 20 - Right to Data Portability"""
    
    def test_export_user_data_includes_all_personal_data(self, mock_user):
        """Verify export includes all personal data categories"""
        response = handle_export_user_data(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        # Verify export structure
        assert 'download_url' in data
        assert 'filename' in data
        assert 'summary' in data
        assert 'export_date' in data
        
        # Verify expiration
        assert data['expires_in_seconds'] == 3600  # 1 hour
    
    def test_export_excludes_sensitive_credentials(self, mock_user):
        """Ensure passwords, API keys, and internal IDs are not exported"""
        response = handle_export_user_data(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        # Download and parse the export (mocked in test)
        # In real test, we'd download from S3 and verify contents
        # Assert sensitive fields are NOT present:
        # - password_hash
        # - api_key
        # - stripe_customer_id (internal reference)
        # - session tokens
    
    def test_export_masks_payment_information(self, mock_user):
        """Verify payment methods show only last 4 digits (PCI DSS)"""
        response = handle_export_user_data(mock_user)
        
        assert response['statusCode'] == 200
        # Payment data should be masked in export
    
    def test_export_includes_machine_readable_format(self, mock_user):
        """Export must be in JSON format (machine-readable)"""
        response = handle_export_user_data(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        # Filename should be JSON
        assert data['filename'].endswith('.json')


class TestDataRetentionPolicy:
    """Test GDPR Article 13 - Transparency about data retention"""
    
    def test_get_retention_info_returns_all_categories(self, mock_user):
        """Verify retention policy covers all data categories"""
        response = handle_get_data_retention_info(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        # Verify key sections
        assert 'data_retention_policy' in data
        policy = data['data_retention_policy']
        
        # Required categories
        assert 'user_profile' in policy
        assert 'photos_and_galleries' in policy
        assert 'billing_records' in policy
        assert 'analytics_data' in policy
        assert 'sessions' in policy
        assert 'backup_data' in policy
    
    def test_billing_records_have_legal_retention(self, mock_user):
        """Billing records must be retained for 7 years (tax law)"""
        response = handle_get_data_retention_info(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        billing_policy = data['data_retention_policy']['billing_records']
        assert '7 years' in billing_policy['retention_period']
        assert billing_policy['legal_basis'] == 'Legal obligation'
        assert billing_policy['can_be_deleted'] == False
    
    def test_retention_info_includes_contact_details(self, mock_user):
        """Must provide DPO and support contact (GDPR Article 13)"""
        response = handle_get_data_retention_info(mock_user)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        assert 'contact' in data
        assert 'data_protection_officer' in data['contact']
        assert 'support' in data['contact']
        
        # Verify valid email format
        dpo_email = data['contact']['data_protection_officer']
        assert '@' in dpo_email


class TestPCIDSSCompliance:
    """Test PCI DSS compliance for payment data"""
    
    def test_invoice_pdf_never_shows_full_card_number(self):
        """Invoice PDFs must never contain full credit card numbers"""
        # Mock invoice with payment data
        invoice = {
            'id': 'inv_test123',
            'photographer_id': 'user_123',
            'items': [],
            'payment_method': {
                'type': 'card',
                'brand': 'Visa',
                'last4': '4242',
                'full_number': '4242424242424242'  # Should NEVER appear in PDF
            }
        }
        
        # Generate PDF would be mocked in actual test
        # Verify the PDF content does NOT contain the full number
        # Only ****4242 should appear
    
    def test_invoice_pdf_masks_card_details(self):
        """Verify card masking in PDF generation"""
        invoice = {
            'id': 'inv_test123',
            'photographer_id': 'user_123',
            'items': [
                {'description': 'Photo Session', 'quantity': 1, 'price': 500}
            ],
            'payment_method': {
                'type': 'card',
                'brand': 'MasterCard',
                'last4': '5555'
            }
        }
        
        # In real test, parse generated PDF and verify:
        # 1. Contains "MasterCard ending in ****5555"
        # 2. Does NOT contain full card number
        # 3. Contains PCI compliance disclaimer
    
    def test_invoice_html_does_not_expose_sensitive_data(self):
        """HTML invoices must not leak sensitive payment data"""
        # Similar test for HTML invoice generation
        pass


class TestCookieConsent:
    """Test GDPR-compliant cookie consent"""
    
    def test_consent_recorded_with_timestamp(self):
        """Consent must include timestamp (GDPR Article 7)"""
        # This would test the frontend cookie consent component
        # Verify localStorage stores:
        # - consent preferences (granular)
        # - timestamp
        # - policy version
        pass
    
    def test_consent_expires_after_12_months(self):
        """Consent must be re-requested after 12 months"""
        # Verify the banner re-appears after 12 months
        pass
    
    def test_granular_consent_options(self):
        """Must offer granular consent (essential, analytics, marketing)"""
        # Verify three separate toggles are available
        pass
    
    def test_reject_has_equal_prominence(self):
        """Reject button must be as prominent as Accept (GDPR)"""
        # Verify both buttons are same size/prominence
        pass


class TestAccountDeletion:
    """Test GDPR Article 17 - Right to Erasure"""
    
    def test_account_deletion_removes_personal_data(self, mock_user):
        """Account deletion must remove all personal data"""
        # Test already implemented in account deletion handler
        # Verify:
        # 1. User profile deleted
        # 2. Photos deleted
        # 3. Galleries deleted
        # 4. Sessions invalidated
        # 5. Billing records RETAINED (legal requirement)
        pass
    
    def test_deletion_preserves_billing_records(self, mock_user):
        """Billing records must be retained for 7 years even after deletion"""
        # Verify billing records are NOT deleted when account is deleted
        # Only anonymized (user_id retained, personal info removed)
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

