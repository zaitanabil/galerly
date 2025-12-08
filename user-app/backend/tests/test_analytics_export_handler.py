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
    
    @patch('handlers.analytics_export_handler.get_user_from_token')
    @patch('handlers.analytics_export_handler.generate_summary_csv')
    def test_export_csv(self, mock_generate, mock_get_user):
        """Test CSV export"""
        mock_get_user.return_value = {'user_id': 'photo1', 'role': 'photographer'}
        mock_generate.return_value = [
            {'Date': '2025-01-01', 'Views': 100, 'Downloads': 50}
        ]
        
        event = {
            'queryStringParameters': {
                'type': 'summary',
                'start_date': '2025-01-01',
                'end_date': '2025-01-31'
            }
        }
        
        response = handle_export_analytics_csv(event)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/csv'
    
    @patch('handlers.analytics_export_handler.get_user_from_token')
    def test_export_pdf(self, mock_get_user):
        """Test PDF export"""
        mock_get_user.return_value = {'user_id': 'photo1', 'role': 'photographer'}
        
        event = {
            'body': '{"type": "summary", "start_date": "2025-01-01", "end_date": "2025-01-31"}'
        }
        
        response = handle_export_analytics_pdf(event)
        
        assert response['statusCode'] == 200
        assert 'pdf_url' in response['body']
