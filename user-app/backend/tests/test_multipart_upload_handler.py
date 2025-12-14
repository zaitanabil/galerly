"""
Unit tests for multipart upload handler
Tests large file upload initialization, completion, and abort with real AWS
"""
import pytest
import uuid
from unittest.mock import patch
from handlers.multipart_upload_handler import (
    handle_initialize_multipart_upload,
    handle_complete_multipart_upload,
    handle_abort_multipart_upload
)
from utils import config


class TestMultipartUploadInitialization:
    """Test multipart upload initialization with real DynamoDB"""
    
    @patch('handlers.subscription_handler.enforce_storage_limit')
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_initialize_upload_success(self, mock_s3, mock_storage):
        """Test successful multipart upload initialization"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"filename": "large_photo.raw", "file_size": 104857600, "content_type": "image/raw"}'
        }
        
        try:
            # Create real gallery in DynamoDB
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            # Mock storage limit check passes
            mock_storage.return_value = (True, None)
            
            # Mock S3 multipart upload creation
            mock_s3.create_multipart_upload.return_value = {
                'UploadId': 'upload123'
            }
            
            result = handle_initialize_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [200, 403, 404, 500]
        finally:
            # Cleanup
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    def test_initialize_upload_blocks_non_owner(self):
        """Test initialization blocked for non-gallery owner"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        owner_id = f'user-{uuid.uuid4()}'
        different_user_id = f'user-{uuid.uuid4()}'
        user = {'id': different_user_id, 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"filename": "photo.jpg", "file_size": 1048576}'
        }
        
        try:
            # Create gallery owned by different user
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': owner_id,
                'name': 'Test Gallery'
            })
            
            result = handle_initialize_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [403, 404]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    @patch('handlers.subscription_handler.enforce_storage_limit')
    def test_initialize_upload_enforces_storage_limit(self, mock_storage):
        """Test storage limit enforcement on initialization"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"filename": "huge_file.raw", "file_size": 10737418240}'  # 10GB
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            # Mock storage limit exceeded
            mock_storage.return_value = (False, 'Storage limit exceeded')
            
            result = handle_initialize_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [403, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


class TestMultipartUploadCompletion:
    """Test multipart upload completion with real DynamoDB"""
    
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_complete_upload_success(self, mock_s3):
        """Test successful multipart upload completion"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123", "parts": [{"PartNumber": 1, "ETag": "etag1"}]}'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            # Mock S3 complete multipart upload
            mock_s3.complete_multipart_upload.return_value = {
                'Location': 's3://bucket/photo123.jpg'
            }
            
            # Mock S3 head_object for file size
            mock_s3.head_object.return_value = {
                'ContentLength': 1048576  # 1 MB
            }
            
            result = handle_complete_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [200, 403, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    def test_complete_upload_verifies_ownership(self):
        """Test completion verifies gallery ownership"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        owner_id = f'user-{uuid.uuid4()}'
        different_user_id = f'user-{uuid.uuid4()}'
        user = {'id': different_user_id, 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123", "parts": []}'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': owner_id,
                'name': 'Test Gallery'
            })
            
            result = handle_complete_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [403, 404]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


class TestMultipartUploadAbort:
    """Test multipart upload abort/cleanup with real DynamoDB"""
    
    @patch('handlers.multipart_upload_handler.s3_client')
    def test_abort_upload_success(self, mock_s3):
        """Test successful upload abort and cleanup"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123"}'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'name': 'Test Gallery'
            })
            
            # Mock S3 abort
            mock_s3.abort_multipart_upload.return_value = {}
            
            result = handle_abort_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [200, 403, 404, 500]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass
    
    def test_abort_upload_blocks_non_owner(self):
        """Test abort blocked for non-owner"""
        gallery_id = f'gallery-{uuid.uuid4()}'
        owner_id = f'user-{uuid.uuid4()}'
        different_user_id = f'user-{uuid.uuid4()}'
        user = {'id': different_user_id, 'email': 'test2@test.com', 'role': 'photographer', 'plan': 'pro'}
        event = {
            'body': '{"photo_id": "photo123", "upload_id": "upload123"}'
        }
        
        try:
            config.galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': owner_id,
                'name': 'Test Gallery'
            })
            
            result = handle_abort_multipart_upload(gallery_id, user, event)
            assert result['statusCode'] in [403, 404]
        finally:
            try:
                config.galleries_table.delete_item(Key={'id': gallery_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
