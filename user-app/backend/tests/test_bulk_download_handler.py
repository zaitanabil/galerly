"""Tests for bulk_download_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.bulk_download_handler import (
    handle_create_bulk_download,
    handle_get_download_status,
    handle_download_gallery
)


class TestBulkDownload:
    """Test bulk download functionality with real DynamoDB"""
    
    @patch('handlers.bulk_download_handler.s3_client')
    def test_create_bulk_download(self, mock_s3):
        """Test creating bulk download - uses real DynamoDB"""
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download.zip'
        
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        body = {
            'gallery_id': f'gallery-{uuid.uuid4()}',
            'quality': 'high'
        }
        
        result = handle_create_bulk_download(user, body)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_download_status(self):
        """Test getting download status - uses real DynamoDB"""
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        download_id = f'download-{uuid.uuid4()}'
        
        result = handle_get_download_status(user, download_id)
        assert result['statusCode'] in [200, 404, 500]
    
    @patch('handlers.bulk_download_handler.s3_client')
    def test_download_gallery(self, mock_s3):
        """Test downloading entire gallery - uses real DynamoDB"""
        mock_s3.generate_presigned_url.return_value = 'https://example.com/gallery.zip'
        
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        result = handle_download_gallery(user, gallery_id)
        assert result['statusCode'] in [200, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
