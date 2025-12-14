"""
Unit tests for multipart upload handler
Tests large file upload initialization, completion, and abort
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.multipart_upload_handler import (
    handle_initialize_multipart_upload,
    handle_complete_multipart_upload,
    handle_abort_multipart_upload
)


class TestMultipartUploadInitialization:
    """Test multipart upload initialization"""
    
    @patch('handlers.subscription_handler.enforce_storage_limit')
    @patch('handlers.multipart_upload_handler.s3_client')
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_initialize_upload_success(self, mock_galleries, mock_s3, mock_storage):
        """Test successful multipart upload initialization"""
        gallery_id = 'gallery123'
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"filename": "large_photo.raw", "file_size": 104857600, "content_type": "image/raw"}'
        }
        
        # Mock gallery ownership
        mock_galleries.get_item.return_value = {
            'Item': {
                'id': 'gallery123',
                'user_id': 'user123',
                'name': 'Test Gallery'
            }
        }
        
        # Mock storage limit check passes
        mock_storage.return_value = (True, None)
        
        # Mock S3 multipart upload creation
        mock_s3.create_multipart_upload.return_value = {
            'UploadId': 'upload123'
        }
        
        result = handle_initialize_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 200
        assert mock_s3.create_multipart_upload.called
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_initialize_upload_blocks_non_owner(self, mock_galleries):
        """Test initialization blocked for non-gallery owner"""
        gallery_id = 'gallery123'
        user = {'id': 'user456', 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}  # Different user
        event = {
            'body': '{"filename": "photo.jpg", "file_size": 1048576}'
        }
        
        # Mock gallery owned by different user
        mock_galleries.get_item.return_value = {}  # No Item means not found for this user
        
        result = handle_initialize_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 403
    
    @patch('handlers.subscription_handler.enforce_storage_limit')
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_initialize_upload_enforces_storage_limit(self, mock_galleries, mock_storage):
        """Test storage limit enforcement on initialization"""
        gallery_id = 'gallery123'
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"filename": "huge_file.raw", "file_size": 10737418240}'  # 10GB
        }
        
        mock_galleries.get_item.return_value = {
            'Item': {'id': 'gallery123', 'user_id': 'user123'}
        }
        
        # Mock storage limit exceeded
        mock_storage.return_value = (False, 'Storage limit exceeded')
        
        result = handle_initialize_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 403


class TestMultipartUploadCompletion:
    """Test multipart upload completion"""
    
    @patch('handlers.multipart_upload_handler.s3_client')
    @patch('handlers.multipart_upload_handler.photos_table')
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_complete_upload_success(self, mock_galleries, mock_photos, mock_s3):
        """Test successful multipart upload completion"""
        gallery_id = 'gallery123'
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123", "parts": [{"PartNumber": 1, "ETag": "etag1"}]}'
        }
        
        mock_galleries.get_item.return_value = {
            'Item': {'id': 'gallery123', 'user_id': 'user123'}
        }
        
        # Mock S3 complete multipart upload
        mock_s3.complete_multipart_upload.return_value = {
            'Location': 's3://bucket/photo123.jpg'
        }
        
        # Mock S3 head_object for file size
        mock_s3.head_object.return_value = {
            'ContentLength': 1048576  # 1 MB
        }
        
        # Mock photo table update
        mock_photos.update_item.return_value = {
            'Attributes': {'id': 'photo123', 'status': 'uploaded'}
        }
        
        result = handle_complete_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 200
        assert mock_s3.complete_multipart_upload.called
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_complete_upload_verifies_ownership(self, mock_galleries):
        """Test completion verifies gallery ownership"""
        gallery_id = 'gallery123'
        user = {'id': 'user456', 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}  # Different user
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123", "parts": []}'
        }
        
        mock_galleries.get_item.return_value = {}  # No Item
        
        result = handle_complete_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 403


class TestMultipartUploadAbort:
    """Test multipart upload abort/cleanup"""
    
    @patch('handlers.multipart_upload_handler.s3_client')
    @patch('handlers.multipart_upload_handler.photos_table')
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_abort_upload_success(self, mock_galleries, mock_photos, mock_s3):
        """Test successful upload abort and cleanup"""
        gallery_id = 'gallery123'
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123"}'
        }
        
        mock_galleries.get_item.return_value = {
            'Item': {'id': 'gallery123', 'user_id': 'user123'}
        }
        
        # Mock S3 abort
        mock_s3.abort_multipart_upload.return_value = {}
        
        result = handle_abort_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 200
        assert mock_s3.abort_multipart_upload.called
    
    @patch('handlers.multipart_upload_handler.galleries_table')
    def test_abort_upload_blocks_non_owner(self, mock_galleries):
        """Test abort blocked for non-owner"""
        gallery_id = 'gallery123'
        user = {'id': 'user456', 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123"}'
        }
        
        mock_galleries.get_item.return_value = {}  # No Item
        
        result = handle_abort_multipart_upload(gallery_id, user, event)
        assert result['statusCode'] == 403


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
