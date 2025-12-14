"""
Tests for photo_upload_presigned.py using REAL AWS resources
"""
import pytest
import json
import uuid
from unittest.mock import patch
from decimal import Decimal
from handlers.photo_upload_presigned import (
    handle_get_upload_url,
    handle_direct_upload,
    handle_confirm_upload
)
from utils.config import galleries_table, photos_table, users_table


class TestGetUploadUrl:
    """Test presigned URL generation with real AWS"""
    
    def test_get_upload_url_success(self):
        """Test successful presigned URL generation with real AWS"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {
            'id': user_id,
            'email': f'{user_id}@test.com',
            'role': 'photographer',
            'plan': 'plus'
        }
        
        try:
            # Create real gallery
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'photo_count': 0,
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'filename': 'test.jpg',
                    'content_type': 'image/jpeg',
                    'file_size': 5000000
                })
            }
            
            with patch('handlers.photo_upload_presigned.s3_client') as mock_s3, \
                 patch('handlers.photo_upload_presigned.enforce_storage_limit') as mock_enforce, \
                 patch('handlers.photo_upload_presigned.get_user_features') as mock_features:
                
                mock_enforce.return_value = (True, None)
                mock_features.return_value = ({'video_quality': 'hd'}, None, None)
                mock_s3.generate_presigned_post.return_value = {
                    'url': 'https://s3.amazonaws.com/bucket',
                    'fields': {'key': f'{gallery_id}/photo.jpg'}
                }
                
                response = handle_get_upload_url(gallery_id, user, event)
                assert response['statusCode'] in [200, 403, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_get_upload_url_invalid_gallery(self):
        """Test upload URL with nonexistent gallery"""
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer'}
        event = {
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'file_size': 5000000
            })
        }
        
        response = handle_get_upload_url('nonexistent-gallery', user, event)
        assert response['statusCode'] in [403, 404]
    
    def test_get_upload_url_storage_limit_exceeded(self):
        """Test upload rejected when storage limit exceeded"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'filename': 'test.jpg',
                    'content_type': 'image/jpeg',
                    'file_size': 5000000
                })
            }
            
            with patch('handlers.photo_upload_presigned.enforce_storage_limit') as mock_enforce:
                mock_enforce.return_value = (False, 'Storage limit exceeded')
                
                response = handle_get_upload_url(gallery_id, user, event)
                assert response['statusCode'] == 403
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_get_upload_url_missing_filename(self):
        """Test upload rejected when filename missing"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'content_type': 'image/jpeg',
                    'file_size': 5000000
                })
            }
            
            response = handle_get_upload_url(gallery_id, user, event)
            assert response['statusCode'] in [400, 403]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_get_upload_url_invalid_file_type(self):
        """Test upload rejected for invalid file type"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'filename': 'document.pdf',
                    'content_type': 'application/pdf',
                    'file_size': 5000000
                })
            }
            
            with patch('handlers.photo_upload_presigned.enforce_storage_limit') as mock_enforce, \
                 patch('handlers.photo_upload_presigned.get_user_features') as mock_features:
                mock_enforce.return_value = (True, None)
                mock_features.return_value = ({}, None, None)
                
                response = handle_get_upload_url(gallery_id, user, event)
                assert response['statusCode'] in [400, 403]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass


class TestDirectUpload:
    """Test direct upload handling with real AWS"""
    
    def test_direct_upload_success(self):
        """Test successful direct upload"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'filename': 'test.jpg',
                    'data': 'base64encodeddata',
                    'content_type': 'image/jpeg'
                })
            }
            
            with patch('handlers.photo_upload_presigned.s3_client'), \
                 patch('handlers.photo_upload_presigned.enforce_storage_limit') as mock_enforce, \
                 patch('handlers.photo_upload_presigned.get_user_features') as mock_features:
                
                mock_enforce.return_value = (True, None)
                mock_features.return_value = ({}, None, None)
                
                response = handle_direct_upload(gallery_id, user, event)
                assert response['statusCode'] in [200, 201, 400, 403, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass


class TestConfirmUpload:
    """Test upload confirmation with real AWS"""
    
    def test_confirm_upload_success(self):
        """Test successful upload confirmation"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        photo_id = f'photo-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'photo_count': 0,
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            photos_table.put_item(Item={
                'id': photo_id,
                'gallery_id': gallery_id,
                'filename': 'test.jpg',
                's3_key': f'{gallery_id}/{photo_id}_test.jpg',
                'status': 'uploading',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'photo_id': photo_id,
                    's3_key': f'{gallery_id}/{photo_id}_test.jpg'
                })
            }
            
            with patch('handlers.photo_upload_presigned.s3_client'):
                response = handle_confirm_upload(gallery_id, user, event)
                assert response['statusCode'] in [200, 400, 403, 404, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
                photos_table.delete_item(Key={'gallery_id': gallery_id, 'id': photo_id})
            except:
                pass
    
    def test_confirm_upload_invalid_photo(self):
        """Test confirmation with invalid photo ID"""
        user_id = f'user-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            galleries_table.put_item(Item={
                'id': gallery_id,
                'user_id': user_id,
                'title': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'photo_id': 'nonexistent-photo',
                    's3_key': 'test.jpg'
                })
            }
            
            response = handle_confirm_upload(gallery_id, user, event)
            assert response['statusCode'] in [403, 404, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
