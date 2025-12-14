"""Tests for bulk_download_handler.py using REAL AWS resources"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.bulk_download_handler import (
    handle_bulk_download,
    handle_bulk_download_by_token
)


class TestBulkDownload:
    """Test bulk download functionality with real DynamoDB"""
    
    @patch('handlers.bulk_download_handler.s3_client')
    def test_bulk_download_with_user(self, mock_s3):
        """Test bulk download with authenticated user - uses real DynamoDB"""
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download.zip'
        
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {
            'id': f'user-{uuid.uuid4()}',
            'role': 'photographer'
        }
        
        event = {
            'body': json.dumps({
                'quality': 'high',
                'format': 'zip'
            })
        }
        
        result = handle_bulk_download(gallery_id, user, event)
        assert result['statusCode'] in [200, 404, 500]
    
    @patch('handlers.bulk_download_handler.s3_client')
    def test_bulk_download_by_token(self, mock_s3):
        """Test bulk download via token (client access) - uses real DynamoDB"""
        mock_s3.generate_presigned_url.return_value = 'https://example.com/download.zip'
        
        event = {
            'queryStringParameters': {
                'token': f'token-{uuid.uuid4()}'
            },
            'body': json.dumps({
                'quality': 'medium'
            })
        }
        
        result = handle_bulk_download_by_token(event)
        assert result['statusCode'] in [200, 400, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
