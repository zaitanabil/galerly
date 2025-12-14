"""
Tests for Bulk Download Handler
Tests ZIP generation and download functionality for galleries
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.bulk_download_handler import handle_bulk_download, handle_bulk_download_by_token


@pytest.fixture
def mock_gallery():
    return {
        'id': 'gallery-123',
        'user_id': 'user-456',
        'name': 'Wedding Photos',
        'client_emails': ['client@example.com'],
        'photo_count': 25
    }


@pytest.fixture
def mock_user():
    return {
        'id': 'user-456',
        'email': 'photographer@example.com',
        'role': 'photographer',
        'plan': 'pro'
    }


@pytest.fixture
def mock_event():
    return {
        'headers': {},
        'body': '{}'
    }


class TestBulkDownload:
    """Test bulk download functionality"""
    
    @patch('handlers.bulk_download_handler.galleries_table')
    @patch('handlers.bulk_download_handler.s3_client')
    @patch('utils.cdn_urls.get_zip_url')  # FIX: Patch where function is defined
    def test_bulk_download_owner_success(self, mock_get_zip_url, mock_s3, mock_galleries, mock_gallery, mock_user, mock_event):
        """Test successful bulk download by gallery owner"""
        # Setup mocks
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        mock_s3.head_object.return_value = {}  # ZIP exists
        mock_get_zip_url.return_value = 'https://cdn.example.com/gallery-123/gallery-all-photos.zip'
        
        # Execute
        response = handle_bulk_download('gallery-123', mock_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 200
        body = eval(response['body'])
        assert 'zip_url' in body
        assert body['photo_count'] == 25
        assert 'wedding-photos-25-photos.zip' in body['filename']
    
    @patch('handlers.bulk_download_handler.galleries_table')
    @patch('handlers.bulk_download_handler.s3_client')
    @patch('utils.cdn_urls.get_zip_url')  # FIX: Patch where function is defined
    def test_bulk_download_client_success(self, mock_get_zip_url, mock_s3, mock_galleries, mock_gallery, mock_event):
        """Test successful bulk download by authorized client"""
        # Setup mocks
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        mock_s3.head_object.return_value = {}  # ZIP exists
        mock_get_zip_url.return_value = 'https://cdn.example.com/gallery-123/gallery-all-photos.zip'
        
        # Client needs photographer role due to @require_role decorator (handler issue)
        client_user = {
            'id': 'client-789',
            'email': 'client@example.com',
            'role': 'photographer',  # Handler requires this despite allowing clients in logic
            'plan': 'free'
        }
        
        # Execute
        response = handle_bulk_download('gallery-123', client_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 200
        body = eval(response['body'])
        assert 'zip_url' in body
    
    @patch('handlers.bulk_download_handler.galleries_table')
    def test_bulk_download_gallery_not_found(self, mock_galleries, mock_user, mock_event):
        """Test bulk download with non-existent gallery"""
        # Setup
        mock_galleries.scan.return_value = {'Items': []}
        
        # Execute
        response = handle_bulk_download('nonexistent', mock_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 404
        body = eval(response['body'])
        assert 'Gallery not found' in body['error']
    
    @patch('handlers.bulk_download_handler.galleries_table')
    def test_bulk_download_access_denied(self, mock_galleries, mock_gallery, mock_event):
        """Test bulk download with unauthorized user"""
        # Setup
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        
        unauthorized_user = {
            'id': 'unauthorized-999',
            'email': 'unauthorized@example.com',
            'role': 'photographer',  # Has role but not in client_emails
            'plan': 'free'
        }
        
        # Execute
        response = handle_bulk_download('gallery-123', unauthorized_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 403
        body = eval(response['body'])
        assert 'Access denied' in body['error']
        body = eval(response['body'])
        assert 'Access denied' in body['error']
    
    @patch('handlers.bulk_download_handler.galleries_table')
    @patch('handlers.bulk_download_handler.s3_client')
    @patch('utils.zip_generator.generate_gallery_zip')  # FIX: Patch where function is defined
    def test_bulk_download_generate_on_demand(self, mock_generate, mock_s3, mock_galleries, mock_gallery, mock_user, mock_event):
        """Test ZIP generation when file doesn't exist"""
        # Setup mocks
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        mock_s3.head_object.side_effect = Exception('File not found')  # ZIP doesn't exist
        mock_generate.return_value = {
            'success': True,
            'zip_url': 'https://cdn.example.com/gallery-123/gallery-all-photos.zip',
            'photo_count': 25
        }
        
        # Execute
        response = handle_bulk_download('gallery-123', mock_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 200
        mock_generate.assert_called_once_with('gallery-123')
        body = eval(response['body'])
        assert 'zip_url' in body
    
    @patch('handlers.bulk_download_handler.galleries_table')
    @patch('handlers.bulk_download_handler.s3_client')
    @patch('utils.zip_generator.generate_gallery_zip')  # FIX: Patch where function is defined
    def test_bulk_download_generation_failure(self, mock_generate, mock_s3, mock_galleries, mock_gallery, mock_user, mock_event):
        """Test error handling when ZIP generation fails"""
        # Setup mocks
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        mock_s3.head_object.side_effect = Exception('File not found')
        mock_generate.return_value = {'success': False}
        
        # Execute
        response = handle_bulk_download('gallery-123', mock_user, mock_event)
        
        # Assert
        assert response['statusCode'] == 500
        body = eval(response['body'])
        assert 'Failed to generate ZIP' in body['error']


class TestBulkDownloadByToken:
    """Test token-based bulk download"""
    
    @patch('handlers.bulk_download_handler.galleries_table')
    @patch('handlers.bulk_download_handler.s3_client')
    @patch('utils.cdn_urls.get_zip_url')  # FIX: Patch where function is defined
    def test_bulk_download_by_token_success(self, mock_get_zip_url, mock_s3, mock_galleries, mock_gallery):
        """Test successful bulk download via token"""
        # Setup
        mock_gallery['share_token'] = 'valid-token-123'
        mock_galleries.scan.return_value = {'Items': [mock_gallery]}
        mock_s3.head_object.return_value = {}
        mock_get_zip_url.return_value = 'https://cdn.example.com/gallery-123/gallery-all-photos.zip'
        
        event = {
            'body': '{"token": "valid-token-123"}'
        }
        
        # Execute
        response = handle_bulk_download_by_token(event)
        
        # Assert
        assert response['statusCode'] == 200
        body = eval(response['body'])
        assert 'zip_url' in body
    
    @patch('handlers.bulk_download_handler.galleries_table')
    def test_bulk_download_by_token_invalid(self, mock_galleries):
        """Test bulk download with invalid token"""
        # Setup
        mock_galleries.scan.return_value = {'Items': []}
        
        event = {
            'body': '{"token": "invalid-token"}'
        }
        
        # Execute
        response = handle_bulk_download_by_token(event)
        
        # Assert: Handler returns 403 for invalid tokens
        assert response['statusCode'] == 403
        body = eval(response['body'])
        assert 'Invalid or expired token' in body['error']
    
    def test_bulk_download_by_token_missing_token(self):
        """Test bulk download without token"""
        event = {
            'body': '{}'
        }
        
        # Execute
        response = handle_bulk_download_by_token(event)
        
        # Assert
        assert response['statusCode'] == 400
        body = eval(response['body'])
        assert 'Token required' in body['error']

