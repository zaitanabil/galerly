"""
Tests for Analytics Export Handler
"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.analytics_export_handler import (
    handle_export_analytics_csv,
    handle_export_analytics_pdf,
    generate_summary_csv
)


class TestAnalyticsExportHandler:
    """Test analytics export functionality"""
    
    @patch('handlers.analytics_export_handler.generate_summary_csv')
    @patch('handlers.analytics_export_handler.dynamodb')
    @patch('handlers.subscription_handler.get_user_features')
    def test_export_csv(self, mock_get_features, mock_dynamodb, mock_generate):
        """Test CSV export"""
        # Mock user with required fields for decorator
        user = {
            'id': 'photo1',
            'email': 'photographer@test.com',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        # Mock get_user_features to allow access
        mock_get_features.return_value = (
            {'analytics_export': True},  # features
            'pro',  # plan_id
            'Pro'  # plan_name
        )
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.return_value = {'Items': []}
        
        mock_generate.return_value = [
            {'Date': '2025-01-01', 'Views': 100, 'Downloads': 50}
        ]
        
        query_params = {
            'type': 'summary',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        }
        
        response = handle_export_analytics_csv(user, query_params)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/csv'
    
    @patch('handlers.analytics_export_handler.dynamodb')
    @patch('handlers.analytics_export_handler.s3_client')
    @patch('handlers.subscription_handler.get_user_features')
    def test_export_pdf(self, mock_get_features, mock_s3, mock_dynamodb):
        """Test PDF export"""
        # Mock user with required fields for decorator
        user = {
            'id': 'photo1',
            'email': 'photographer@test.com',
            'role': 'photographer',
            'plan': 'pro'
        }
        
        # Mock get_user_features to allow access
        mock_get_features.return_value = (
            {'analytics_export': True},  # features
            'pro',  # plan_id
            'Pro'  # plan_name
        )
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.return_value = {'Items': []}
        
        # Mock S3 upload
        mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/report.pdf'
        
        body = {
            'type': 'summary',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        }
        
        response = handle_export_analytics_pdf(user, body)
        
        assert response['statusCode'] == 200
