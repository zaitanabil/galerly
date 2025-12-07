"""
Tests for gallery_handler.py endpoints.
Tests cover: list galleries, create gallery, get gallery, update gallery, delete gallery.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from boto3.dynamodb.conditions import Key
import json

@pytest.fixture
def mock_tables_and_clients():
    """Mock DynamoDB tables and S3 client used by gallery_handler."""
    with patch('handlers.gallery_handler.galleries_table') as mock_galleries, \
         patch('handlers.gallery_handler.photos_table') as mock_photos, \
         patch('handlers.gallery_handler.s3_client') as mock_s3:
        
        yield {
            'galleries': mock_galleries,
            'photos': mock_photos,
            's3': mock_s3
        }

# Test: handle_list_galleries
class TestHandleListGalleries:
    """Tests for handle_list_galleries endpoint."""
    
    def test_list_galleries_success(self, sample_user, sample_gallery, mock_tables_and_clients):
        """List galleries returns user's galleries."""
        from handlers.gallery_handler import handle_list_galleries
        
        # Mock DynamoDB response
        mock_tables_and_clients['galleries'].query.return_value = {
            'Items': [sample_gallery, {**sample_gallery, 'id': 'gallery_456', 'name': 'Gallery 2'}]
        }
        
        result = handle_list_galleries(sample_user, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'galleries' in body
        assert len(body['galleries']) == 2
        assert body['total'] == 2
    
    def test_list_galleries_with_search(self, sample_user, sample_gallery, mock_tables_and_clients):
        """List galleries with search filter."""
        from handlers.gallery_handler import handle_list_galleries
        
        mock_tables_and_clients['galleries'].query.return_value = {
            'Items': [sample_gallery]
        }
        
        result = handle_list_galleries(sample_user, query_params={'search': 'Test'})
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert len(body['galleries']) == 1
        assert 'Test' in body['galleries'][0]['name']
    
    def test_list_galleries_archived_filter(self, sample_user, sample_gallery, mock_tables_and_clients):
        """List galleries excludes archived galleries by default."""
        from handlers.gallery_handler import handle_list_galleries
        
        archived_gallery = {**sample_gallery, 'id': 'gallery_archived', 'archived': True}
        mock_tables_and_clients['galleries'].query.return_value = {
            'Items': [sample_gallery, archived_gallery]
        }
        
        result = handle_list_galleries(sample_user, query_params={'show_archived': 'false'})
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert len(body['galleries']) == 1
        assert body['galleries'][0]['id'] == 'gallery_123'
    
    def test_list_galleries_empty(self, sample_user, mock_tables_and_clients):
        """List galleries returns empty list when user has no galleries."""
        from handlers.gallery_handler import handle_list_galleries
        
        mock_tables_and_clients['galleries'].query.return_value = {'Items': []}
        
        result = handle_list_galleries(sample_user, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['galleries'] == []
        assert body['total'] == 0
    
    def test_list_galleries_uses_projection(self, sample_user, sample_gallery, mock_tables_and_clients):
        """List galleries uses ProjectionExpression for optimization."""
        from handlers.gallery_handler import handle_list_galleries
        
        mock_tables_and_clients['galleries'].query.return_value = {'Items': [sample_gallery]}
        
        handle_list_galleries(sample_user, query_params=None)
        
        # Verify ProjectionExpression was used
        call_kwargs = mock_tables_and_clients['galleries'].query.call_args[1]
        assert 'ProjectionExpression' in call_kwargs
        assert '#n' in call_kwargs['ProjectionExpression']  # name field

# Test: handle_create_gallery
class TestHandleCreateGallery:
    """Tests for handle_create_gallery endpoint."""
    
    def test_create_gallery_success(self, sample_user, mock_tables_and_clients):
        """Create gallery successfully."""
        from handlers.gallery_handler import handle_create_gallery
        
        with patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)):
            body = {
                'name': 'New Gallery',
                # FIX: Handler expects 'clientEmails' (camelCase), not 'client_emails'
                'clientEmails': ['client@example.com']
            }
            
            result = handle_create_gallery(sample_user, body)
            
            assert result['statusCode'] == 201
            response_body = json.loads(result['body'])
            assert response_body['name'] == 'New Gallery'
            assert 'id' in response_body
            assert len(response_body['client_emails']) == 1
            
            # Verify galleries table was called
            assert mock_tables_and_clients['galleries'].put_item.called
    
    def test_create_gallery_missing_name(self, sample_user, mock_tables_and_clients):
        """Create gallery fails without name."""
        from handlers.gallery_handler import handle_create_gallery
        
        body = {'client_emails': []}
        
        result = handle_create_gallery(sample_user, body)
        
        assert result['statusCode'] == 400
        body_data = json.loads(result['body'])
        assert 'error' in body_data
    
    def test_create_gallery_exceeds_limit(self, sample_user, mock_tables_and_clients):
        """Create gallery fails when gallery limit exceeded."""
        from handlers.gallery_handler import handle_create_gallery
        
        with patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(False, 'Gallery limit exceeded')):
            body = {'name': 'New Gallery', 'client_emails': []}
            
            result = handle_create_gallery(sample_user, body)
            
            assert result['statusCode'] == 403
            body_data = json.loads(result['body'])
            assert 'limit' in body_data['error'].lower()

# Test: handle_get_gallery
class TestHandleGetGallery:
    """Tests for handle_get_gallery endpoint."""
    
    def test_get_gallery_success(self, sample_user, sample_gallery, sample_photo, mock_tables_and_clients):
        """Get gallery with photos successfully."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        # FIX: Handler makes two queries - one for COUNT, one for photos
        # Return different values based on Select parameter
        def query_side_effect(**kwargs):
            if kwargs.get('Select') == 'COUNT':
                return {'Count': 1}  # For the COUNT query
            else:
                return {
                    'Items': [sample_photo],
                    'LastEvaluatedKey': None
                }  # For the photos fetch query
        
        mock_tables_and_clients['photos'].query.side_effect = query_side_effect
        
        result = handle_get_gallery('gallery_123', user=sample_user, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['id'] == 'gallery_123'
        assert 'photos' in body
        assert len(body['photos']) == 1
        assert body['photo_count'] == 1
    
    def test_get_gallery_with_pagination(self, sample_user, sample_gallery, sample_photo, mock_tables_and_clients):
        """Get gallery with pagination parameters."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_tables_and_clients['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': {'id': 'next_photo'}
        }
        
        query_params = {'page_size': '10'}
        result = handle_get_gallery('gallery_123', user=sample_user, query_params=query_params)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'pagination' in body
        assert body['pagination']['page_size'] == 10
        assert body['pagination']['has_more'] is True
        assert body['pagination']['next_key'] == {'id': 'next_photo'}
    
    def test_get_gallery_pagination_enforces_limits(self, sample_user, sample_gallery, mock_tables_and_clients):
        """Get gallery enforces min 1, max 100 page_size."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_tables_and_clients['photos'].query.return_value = {'Items': [], 'LastEvaluatedKey': None}
        
        # Test max enforcement (150 -> 100)
        result = handle_get_gallery('gallery_123', user=sample_user, query_params={'page_size': '150'})
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 100
        
        # Test min enforcement (0 -> 1)
        result = handle_get_gallery('gallery_123', user=sample_user, query_params={'page_size': '0'})
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 1
    
    def test_get_gallery_not_found(self, sample_user, mock_tables_and_clients):
        """Get gallery returns 404 when gallery not found."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {}
        
        result = handle_get_gallery('nonexistent', user=sample_user, query_params=None)
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert 'error' in body
    
    def test_get_gallery_requires_auth(self, mock_tables_and_clients):
        """Get gallery requires authentication."""
        from handlers.gallery_handler import handle_get_gallery
        
        result = handle_get_gallery('gallery_123', user=None, query_params=None)
        
        assert result['statusCode'] == 401
        body = json.loads(result['body'])
        assert 'Authentication required' in body['error']
    
    def test_get_gallery_photo_exception_handled(self, sample_user, sample_gallery, mock_tables_and_clients):
        """Get gallery handles photo loading exceptions gracefully."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        # FIX: Handler makes COUNT query first, then photo query - both should raise exception
        mock_tables_and_clients['photos'].query.side_effect = Exception("DynamoDB error")
        
        result = handle_get_gallery('gallery_123', user=sample_user, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['photos'] == []
        # FIX: When count query fails, handler keeps existing photo_count from gallery (10 in sample_gallery)
        # If photo_count doesn't exist in gallery, fallback uses len(photos) = 0
        assert body['photo_count'] == sample_gallery.get('photo_count', 0)
    
    def test_get_gallery_uses_projection(self, sample_user, sample_gallery, sample_photo, mock_tables_and_clients):
        """Get gallery uses ProjectionExpression for photos."""
        from handlers.gallery_handler import handle_get_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        # FIX: Handler makes two queries - COUNT and photo fetch
        def query_side_effect(**kwargs):
            if kwargs.get('Select') == 'COUNT':
                return {'Count': 1}
            else:
                return {
                    'Items': [sample_photo],
                    'LastEvaluatedKey': None
                }
        
        mock_tables_and_clients['photos'].query.side_effect = query_side_effect
        
        handle_get_gallery('gallery_123', user=sample_user, query_params=None)
        
        # FIX: Handler makes two queries - COUNT and photo fetch
        # Verify ProjectionExpression was used in the photo fetch call
        calls = mock_tables_and_clients['photos'].query.call_args_list
        # Find the call without Select='COUNT'
        photo_fetch_call = None
        for call in calls:
            call_kwargs = call[1] if len(call) > 1 else call.kwargs
            if call_kwargs.get('Select') != 'COUNT':
                photo_fetch_call = call_kwargs
                break
        
        assert photo_fetch_call is not None
        assert 'ProjectionExpression' in photo_fetch_call

# Test: handle_update_gallery
class TestHandleUpdateGallery:
    """Tests for handle_update_gallery endpoint."""
    
    def test_update_gallery_success(self, sample_user, sample_gallery, mock_tables_and_clients):
        """Update gallery successfully."""
        from handlers.gallery_handler import handle_update_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        body = {'name': 'Updated Gallery Name'}
        result = handle_update_gallery('gallery_123', sample_user, body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['name'] == 'Updated Gallery Name'
        
        # Verify cache invalidation was called
    
    def test_update_gallery_tags(self, sample_user, sample_gallery, mock_tables_and_clients):
        """Update gallery tags successfully."""
        from handlers.gallery_handler import handle_update_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        
        body = {'tags': ['wedding', 'outdoor', 'sunset']}
        result = handle_update_gallery('gallery_123', sample_user, body)
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'tags' in response_body
        assert response_body['tags'] == ['wedding', 'outdoor', 'sunset']
    
    def test_update_gallery_not_found(self, sample_user, mock_tables_and_clients):
        """Update gallery fails when gallery not found."""
        from handlers.gallery_handler import handle_update_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {}
        
        body = {'name': 'Updated Name'}
        result = handle_update_gallery('nonexistent', sample_user, body)
        
        assert result['statusCode'] == 404

# Test: handle_delete_gallery
class TestHandleDeleteGallery:
    """Tests for handle_delete_gallery endpoint."""
    
    def test_delete_gallery_success(self, sample_user, sample_gallery, sample_photo, mock_tables_and_clients):
        """Delete gallery and all photos successfully."""
        from handlers.gallery_handler import handle_delete_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {'Item': sample_gallery}
        mock_tables_and_clients['photos'].query.return_value = {'Items': [sample_photo]}
        
        result = handle_delete_gallery('gallery_123', sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'deleted successfully' in body['message']
        
        # Verify gallery was deleted
        assert mock_tables_and_clients['galleries'].delete_item.called
    
    def test_delete_gallery_not_found(self, sample_user, mock_tables_and_clients):
        """Delete gallery fails when gallery not found."""
        from handlers.gallery_handler import handle_delete_gallery
        
        mock_tables_and_clients['galleries'].get_item.return_value = {}
        
        result = handle_delete_gallery('nonexistent', sample_user)
        
        assert result['statusCode'] == 404

