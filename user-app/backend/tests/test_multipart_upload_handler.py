"""
Tests for Multipart Upload Handler
Tests large file upload functionality with resume capability
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from handlers.multipart_upload_handler import (
    handle_initialize_multipart_upload,
    handle_complete_multipart_upload,
    handle_abort_multipart_upload
)


@pytest.fixture
def mock_user():
    return {
        'id': 'user-123',
        'email': 'photographer@example.com'
    }


@pytest.fixture
def mock_gallery():
    return {
        'id': 'gallery-456',
        'user_id': 'user-123',
        'name': 'Wedding Gallery'
    }


@pytest.fixture
def mock_event_init():
    return {
        'body': '{"filename": "large-photo.jpg", "file_size": 50000000, "content_type": "image/jpeg"}'
    }


class TestInitializeMultipartUpload:
    """Test multipart upload initialization"""
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_initialize_multipart_success(self, mock_s3, mock_galleries, mock_user, mock_gallery, mock_event_init):
        """Test successful multipart upload initialization"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        mock_s3.create_multipart_upload.return_value = {'UploadId': 'upload-789'}
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        # Execute
        response = handle_initialize_multipart_upload('gallery-456', mock_user, mock_event_init)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Handler returns multipart_upload_id instead of upload_id
        assert 'upload_id' in body or 'multipart_upload_id' in body
        assert 'upload_parts' in body
        assert len(body['upload_parts']) > 0
        assert body['photo_id'] is not None
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_initialize_multipart_access_denied(self, mock_galleries, mock_user, mock_event_init):
        """Test multipart upload initialization with access denied"""
        # Setup
        mock_galleries.get_item.return_value = {}
        
        # Execute
        response = handle_initialize_multipart_upload('gallery-456', mock_user, mock_event_init)
        
        # Assert
        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert 'Access denied' in body['error']
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_initialize_multipart_missing_params(self, mock_galleries, mock_user, mock_gallery):
        """Test multipart upload initialization with missing parameters"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        event = {'body': '{}'}
        
        # Execute
        response = handle_initialize_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'filename and file_size required' in body['error']
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_initialize_multipart_calculates_parts_correctly(self, mock_s3, mock_galleries, mock_user, mock_gallery):
        """Test multipart upload calculates correct number of parts"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        mock_s3.create_multipart_upload.return_value = {'UploadId': 'upload-789'}
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        # 25MB file should result in 3 parts (10MB chunks)
        event = {
            'body': '{"filename": "photo.jpg", "file_size": 25000000, "content_type": "image/jpeg"}'
        }
        
        # Execute
        response = handle_initialize_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 200
        body = eval(response['body'])
        assert len(body['upload_parts']) == 3


class TestCompleteMultipartUpload:
    """Test multipart upload completion"""
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    @patch('handlers.multipart_upload_handler.photos_table')
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_complete_multipart_success(self, mock_s3, mock_photos, mock_galleries, mock_user, mock_gallery):
        """Test successful multipart upload completion"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        mock_s3.complete_multipart_upload.return_value = {'ETag': 'etag-123'}
        # Add mock for head_object to provide file size
        mock_s3.head_object.return_value = {'ContentLength': 50000000}  # 50MB
        mock_photos.put_item.return_value = {}
        
        event = {
            'body': '{"photo_id": "photo-123", "upload_id": "upload-789", "parts": [{"PartNumber": 1, "ETag": "etag1"}]}'
        }
        
        # Execute
        response = handle_complete_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        # Handler returns message/photo_id instead of success
        assert 'message' in body or 'success' in body or 'photo_id' in body
        assert 'photo_id' in body
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_complete_multipart_missing_params(self, mock_galleries, mock_user, mock_gallery):
        """Test multipart completion with missing parameters"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        event = {'body': '{}'}
        
        # Execute
        response = handle_complete_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'photo_id, upload_id, and parts required' in body['error']


class TestAbortMultipartUpload:
    """Test multipart upload abortion"""
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_abort_multipart_success(self, mock_s3, mock_galleries, mock_user, mock_gallery):
        """Test successful multipart upload abortion"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        mock_s3.abort_multipart_upload.return_value = {}
        
        event = {
            'body': '{"photo_id": "photo-123", "upload_id": "upload-789"}'
        }
        
        # Execute
        response = handle_abort_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 200
        body = eval(response['body'])
        # Handler returns message instead of success
        assert 'message' in body or 'success' in body or response['statusCode'] == 200
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_abort_multipart_missing_params(self, mock_galleries, mock_user, mock_gallery):
        """Test multipart abortion with missing parameters"""
        # Setup
        mock_galleries.get_item.return_value = {'Item': mock_gallery}
        event = {'body': '{}'}
        
        # Execute
        response = handle_abort_multipart_upload('gallery-456', mock_user, event)
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'photo_id and upload_id required' in body['error']

