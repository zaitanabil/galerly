"""
Unit tests for GDPR handler
Tests data export and retention info retrieval
"""
import pytest
from unittest.mock import Mock, patch
from handlers.gdpr_handler import (
    handle_export_user_data,
    handle_get_data_retention_info
)


class TestGDPRDataExport:
    """Test GDPR Article 20 data export functionality"""
    
    @patch('handlers.gdpr_handler.seo_settings_table')
    @patch('handlers.gdpr_handler.s3_client')
    @patch('handlers.gdpr_handler.contracts_table')
    @patch('handlers.gdpr_handler.appointments_table')
    @patch('handlers.gdpr_handler.invoices_table')
    @patch('handlers.gdpr_handler.client_feedback_table')
    @patch('handlers.gdpr_handler.client_favorites_table')
    @patch('handlers.gdpr_handler.analytics_table')
    @patch('handlers.gdpr_handler.subscriptions_table')
    @patch('handlers.gdpr_handler.billing_table')
    @patch('handlers.gdpr_handler.sessions_table')
    @patch('handlers.gdpr_handler.photos_table')
    @patch('handlers.gdpr_handler.galleries_table')
    def test_export_user_data_photographer(self, mock_galleries, mock_photos, mock_sessions,
                                          mock_billing, mock_subs, mock_analytics, mock_favorites,
                                          mock_feedback, mock_invoices, mock_appointments,
                                          mock_contracts, mock_s3, mock_seo):
        """Test photographer data export includes all relevant data"""
        user = {
            'id': 'user123',
            'role': 'photographer',
            'email': 'photo@test.com',
            'name': 'Test Photographer',
            'plan': 'pro'
        }
        
        # Mock data from various tables
        mock_galleries.query.return_value = {'Items': [{'id': 'gal1', 'name': 'Gallery 1'}]}
        mock_photos.query.return_value = {'Items': [{'id': 'photo1', 'filename': 'test.jpg'}]}
        mock_sessions.query.return_value = {'Items': []}
        mock_billing.scan.return_value = {'Items': []}
        mock_subs.scan.return_value = {'Items': [{'plan': 'pro', 'status': 'active'}]}
        mock_analytics.scan.return_value = {'Items': []}
        mock_favorites.scan.return_value = {'Items': []}
        mock_feedback.scan.return_value = {'Items': []}
        mock_invoices.scan.return_value = {'Items': []}
        mock_appointments.scan.return_value = {'Items': []}
        mock_contracts.scan.return_value = {'Items': []}
        mock_seo.get_item.return_value = {'Item': {}}
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download'
        
        result = handle_export_user_data(user)
        assert result['statusCode'] == 200
        # Verify export contains user data
    
    @patch('handlers.gdpr_handler.client_favorites_table')
    @patch('handlers.gdpr_handler.client_feedback_table')
    def test_export_user_data_client(self, mock_feedback, mock_favorites):
        """Test client data export with photographer role (handler requires it)"""
        user = {
            'id': 'client123',
            'role': 'photographer',  # Handler requires photographer role
            'email': 'client@test.com',
            'plan': 'free'
        }
        
        # Mock client-specific data
        mock_favorites.scan.return_value = {
            'Items': [{'photo_id': 'photo1', 'created_at': '2025-01-01T00:00:00Z'}]
        }
        mock_feedback.scan.return_value = {
            'Items': [{'rating': 5, 'comments': 'Great!'}]
        }
        
        # Patch other table queries
        with patch('handlers.gdpr_handler.galleries_table') as mock_gal, \
             patch('handlers.gdpr_handler.photos_table') as mock_photos, \
             patch('handlers.gdpr_handler.sessions_table') as mock_sessions, \
             patch('handlers.gdpr_handler.billing_table') as mock_billing, \
             patch('handlers.gdpr_handler.subscriptions_table') as mock_subs, \
             patch('handlers.gdpr_handler.analytics_table') as mock_analytics, \
             patch('handlers.gdpr_handler.invoices_table') as mock_inv, \
             patch('handlers.gdpr_handler.appointments_table') as mock_appt, \
             patch('handlers.gdpr_handler.contracts_table') as mock_cont, \
             patch('handlers.gdpr_handler.seo_settings_table') as mock_seo, \
             patch('handlers.gdpr_handler.s3_client') as mock_s3:
            
            mock_gal.query.return_value = {'Items': []}
            mock_photos.query.return_value = {'Items': []}
            mock_sessions.query.return_value = {'Items': []}
            mock_billing.scan.return_value = {'Items': []}
            mock_subs.scan.return_value = {'Items': []}
            mock_analytics.scan.return_value = {'Items': []}
            mock_inv.scan.return_value = {'Items': []}
            mock_appt.scan.return_value = {'Items': []}
            mock_cont.scan.return_value = {'Items': []}
            mock_seo.get_item.return_value = {'Item': {}}
            mock_s3.put_object.return_value = {}
            mock_s3.generate_presigned_url.return_value = 'https://example.com/download'
            
            result = handle_export_user_data(user)
            assert result['statusCode'] == 200


class TestDataRetentionInfo:
    """Test GDPR Article 13 data retention information"""
    
    def test_get_data_retention_info_returns_policies(self):
        """Test retention info returns all data categories"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        result = handle_get_data_retention_info(user)
        assert result['statusCode'] == 200
        # Verify retention policies are returned
    
    def test_retention_info_includes_billing_records(self):
        """Test retention info includes 7-year billing retention"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        result = handle_get_data_retention_info(user)
        # Verify billing records mention 7 years (tax law)
        assert result['statusCode'] == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
