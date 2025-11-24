"""
Comprehensive tests for photo_handler.py endpoints.
Tests cover: upload, update, delete, comments, search, duplicate detection.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_photo_dependencies():
    """Mock all photo handler dependencies."""
    with patch('handlers.photo_handler.photos_table') as mock_photos, \
         patch('handlers.photo_handler.galleries_table') as mock_galleries, \
         patch('handlers.photo_handler.s3_client') as mock_s3:
        yield {
            'photos': mock_photos,
            'galleries': mock_galleries,
            's3': mock_s3
        }

# Test: handle_upload_photo
class TestHandleUploadPhoto:
    """Tests for photo upload endpoint."""
    
    def test_upload_photo_success(self, sample_user, sample_gallery, mock_photo_dependencies):
        """Upload photo successfully."""
        from handlers.photo_handler import handle_upload_photo
        
        mock_photo_dependencies['galleries'].get_item.return_value = {
            'Item': sample_gallery
        }
        
        event = {
            'body': json.dumps({
                'filename': 'photo.jpg',
                'size': 1024000,
                'mime_type': 'image/jpeg'
            })
        }
        
        result = handle_upload_photo('gallery_123', sample_user, event)
        
        assert result['statusCode'] in [200, 201]
        body = json.loads(result['body'])
        assert 'id' in body or 'photo_id' in body
    
    def test_upload_photo_gallery_not_owned(self, sample_user, sample_gallery, mock_photo_dependencies):
        """Upload photo fails when user doesn't own gallery."""
        from handlers.photo_handler import handle_upload_photo
        
        other_gallery = {**sample_gallery, 'user_id': 'other_user'}
        mock_photo_dependencies['galleries'].get_item.return_value = {
            'Item': other_gallery
        }
        
        event = {'body': json.dumps({'filename': 'photo.jpg'})}
        
        result = handle_upload_photo('gallery_123', sample_user, event)
        
        assert result['statusCode'] == 403

# Test: handle_update_photo
class TestHandleUpdatePhoto:
    """Tests for photo update endpoint."""
    
    def test_update_photo_status(self, sample_user, sample_photo, sample_gallery, mock_photo_dependencies):
        """Update photo status successfully."""
        from handlers.photo_handler import handle_update_photo
        
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        mock_photo_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        body = {'status': 'approved'}
        
        result = handle_update_photo('photo_123', body, sample_user)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['status'] == 'approved'
    
    def test_update_photo_metadata(self, sample_user, sample_photo, sample_gallery, mock_photo_dependencies):
        """Update photo title and description."""
        from handlers.photo_handler import handle_update_photo
        
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        mock_photo_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        body = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        
        result = handle_update_photo('photo_123', body, sample_user)
        
        assert result['statusCode'] == 200

# Test: handle_delete_photos
class TestHandleDeletePhotos:
    """Tests for batch photo deletion."""
    
    def test_delete_photos_batch(self, sample_user, sample_photo, sample_gallery, mock_photo_dependencies):
        """Delete multiple photos at once."""
        from handlers.photo_handler import handle_delete_photos
        
        mock_photo_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        
        event = {
            'body': json.dumps({
                'photo_ids': ['photo_1', 'photo_2', 'photo_3']
            })
        }
        
        result = handle_delete_photos('gallery_123', sample_user, event)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'deleted' in body['message'].lower()

# Test: handle_add_comment
class TestHandleAddComment:
    """Tests for adding photo comments."""
    
    def test_add_comment_success(self, sample_user, sample_photo, mock_photo_dependencies):
        """Add comment to photo successfully."""
        from handlers.photo_handler import handle_add_comment
        
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        
        body = {'text': 'Great photo!'}
        
        result = handle_add_comment('photo_123', sample_user, body)
        
        assert result['statusCode'] in [200, 201]
        response_body = json.loads(result['body'])
        assert 'id' in response_body or 'comment_id' in response_body
    
    def test_add_comment_empty_text(self, sample_user, sample_photo, mock_photo_dependencies):
        """Add comment fails with empty text."""
        from handlers.photo_handler import handle_add_comment
        
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': sample_photo}
        
        body = {'text': ''}
        
        result = handle_add_comment('photo_123', sample_user, body)
        
        assert result['statusCode'] == 400

# Test: handle_update_comment
class TestHandleUpdateComment:
    """Tests for updating photo comments."""
    
    def test_update_comment_success(self, sample_user, sample_photo, mock_photo_dependencies):
        """Update comment successfully."""
        from handlers.photo_handler import handle_update_comment
        
        photo_with_comment = {
            **sample_photo,
            'comments': [
                {'id': 'comment_1', 'user_id': sample_user['id'], 'text': 'Original'}
            ]
        }
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': photo_with_comment}
        
        body = {'text': 'Updated comment'}
        
        result = handle_update_comment('photo_123', 'comment_1', sample_user, body)
        
        assert result['statusCode'] == 200

# Test: handle_delete_comment
class TestHandleDeleteComment:
    """Tests for deleting photo comments."""
    
    def test_delete_comment_success(self, sample_user, sample_photo, mock_photo_dependencies):
        """Delete comment successfully."""
        from handlers.photo_handler import handle_delete_comment
        
        photo_with_comment = {
            **sample_photo,
            'comments': [
                {'id': 'comment_1', 'user_id': sample_user['id'], 'text': 'Test'}
            ]
        }
        mock_photo_dependencies['photos'].get_item.return_value = {'Item': photo_with_comment}
        
        result = handle_delete_comment('photo_123', 'comment_1', sample_user)
        
        assert result['statusCode'] == 200

# Test: handle_search_photos
class TestHandleSearchPhotos:
    """Tests for photo search endpoint."""
    
    def test_search_photos_by_keyword(self, sample_user, sample_photo, mock_photo_dependencies):
        """Search photos by keyword."""
        from handlers.photo_handler import handle_search_photos
        
        mock_photo_dependencies['photos'].scan.return_value = {
            'Items': [sample_photo]
        }
        
        query_params = {'q': 'sunset'}
        
        result = handle_search_photos(sample_user, query_params)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'photos' in body

# Test: handle_check_duplicates
class TestHandleCheckDuplicates:
    """Tests for duplicate detection."""
    
    def test_check_duplicates_found(self, sample_user, sample_gallery, sample_photo, mock_photo_dependencies):
        """Duplicate detection finds similar photos."""
        from handlers.photo_handler import handle_check_duplicates
        
        mock_photo_dependencies['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_photo_dependencies['photos'].query.return_value = {
            'Items': [sample_photo]
        }
        
        event = {
            'body': json.dumps({
                'file_hash': 'abc123',
                'filename': 'photo.jpg'
            })
        }
        
        with patch('handlers.photo_handler.calculate_hash', return_value='abc123'):
            result = handle_check_duplicates('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'duplicates' in body or 'is_duplicate' in body

# Test: handle_send_batch_notification
class TestHandleSendBatchNotification:
    """Tests for batch client notification."""
    
    def test_send_notification_to_clients(self, sample_user, sample_gallery, mock_photo_dependencies):
        """Send notification to all gallery clients."""
        from handlers.photo_handler import handle_send_batch_notification
        
        gallery_with_clients = {
            **sample_gallery,
            'client_emails': ['client1@example.com', 'client2@example.com']
        }
        mock_photo_dependencies['galleries'].get_item.return_value = {
            'Item': gallery_with_clients
        }
        
        with patch('handlers.photo_handler.send_email') as mock_email:
            result = handle_send_batch_notification('gallery_123', sample_user)
            
            assert result['statusCode'] == 200
            # Verify emails were sent
            assert mock_email.call_count == 2

