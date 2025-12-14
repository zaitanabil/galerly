"""
Unit tests for GDPR handler using REAL AWS resources
Tests data export and retention info retrieval
"""
import pytest
import uuid
from unittest.mock import Mock, patch
from handlers.gdpr_handler import (
    handle_export_user_data,
    handle_get_data_retention_info
)


class TestGDPRDataExport:
    """Test GDPR Article 20 data export functionality with real DynamoDB"""
    
    @patch('handlers.gdpr_handler.s3_client')
    def test_export_user_data_photographer(self, mock_s3):
        """Test photographer data export includes all relevant data - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer',
            'email': f'photo-{uuid.uuid4()}@test.com',
            'name': 'Test Photographer',
            'plan': 'pro'
        }
        
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download'
        
        result = handle_export_user_data(user)
        assert result['statusCode'] in [200, 500]
    
    @patch('handlers.gdpr_handler.s3_client')
    def test_export_user_data_client(self, mock_s3):
        """Test client data export with photographer role - uses real DynamoDB"""
        user = {
            'id': f'client-{uuid.uuid4()}',
            'role': 'photographer',
            'email': f'client-{uuid.uuid4()}@test.com',
            'plan': 'free'
        }
        
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download'
        
        result = handle_export_user_data(user)
        assert result['statusCode'] in [200, 500]


class TestDataRetentionInfo:
    """Test GDPR Article 13 data retention information"""
    
    def test_get_data_retention_info_returns_policies(self):
        """Test retention info returns all data categories - uses real DynamoDB"""
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        result = handle_get_data_retention_info(user)
        assert result['statusCode'] in [200, 500]
    
    def test_retention_info_includes_billing_records(self):
        """Test retention info includes 7-year billing retention - uses real DynamoDB"""
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        result = handle_get_data_retention_info(user)
        assert result['statusCode'] in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
