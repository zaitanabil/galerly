"""
Tests for client_handler.py endpoints.
Tests cover: get client gallery, get client gallery by token (with pagination).
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_tables():
    """Mock DynamoDB tables used by client_handler."""
    with patch('handlers.client_handler.galleries_table') as mock_galleries, \
         patch('handlers.client_handler.photos_table') as mock_photos, \
         patch('handlers.client_handler.users_table') as mock_users:
        yield {
            'galleries': mock_galleries,
            'photos': mock_photos,
            'users': mock_users
        }

@pytest.fixture
def sample_client():
    """Sample client user."""
    return {
        'id': 'client_123',
        'email': 'client@example.com',
        'name': 'Test Client',
        'role': 'client'
    }

# Test: handle_get_client_gallery
class TestHandleGetClientGallery:
    """Tests for handle_get_client_gallery endpoint."""
    
    def test_get_client_gallery_success(self, sample_user, sample_gallery, sample_photo, sample_client, mock_tables):
        """Get client gallery successfully with access check."""
        from handlers.client_handler import handle_get_client_gallery
        
        # Client has access
        gallery_with_access = {**sample_gallery, 'client_emails': [sample_client['email']]}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_access]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': None
        }
        
        result = handle_get_client_gallery('gallery_123', sample_client, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['id'] == 'gallery_123'
        assert 'photos' in body
        assert len(body['photos']) == 1
    
    def test_get_client_gallery_no_access(self, sample_gallery, sample_client, mock_tables):
        """Get client gallery fails when client has no access."""
        from handlers.client_handler import handle_get_client_gallery
        
        # Client NOT in client_emails
        gallery_no_access = {**sample_gallery, 'client_emails': ['other@example.com']}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_no_access]}
        
        result = handle_get_client_gallery('gallery_123', sample_client, query_params=None)
        
        assert result['statusCode'] == 403
        body = json.loads(result['body'])
        assert 'access' in body['error'].lower()
    
    def test_get_client_gallery_with_pagination(self, sample_user, sample_gallery, sample_photo, sample_client, mock_tables):
        """Get client gallery with pagination parameters."""
        from handlers.client_handler import handle_get_client_gallery
        
        gallery_with_access = {**sample_gallery, 'client_emails': [sample_client['email']]}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_access]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': {'id': 'next_photo'}
        }
        
        query_params = {'page_size': '20', 'last_key': json.dumps({'id': 'prev_photo'})}
        result = handle_get_client_gallery('gallery_123', sample_client, query_params=query_params)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'pagination' in body
        assert body['pagination']['page_size'] == 20
        assert body['pagination']['has_more'] is True
    
    def test_get_client_gallery_pagination_enforces_limits(self, sample_user, sample_gallery, sample_client, mock_tables):
        """Get client gallery enforces pagination limits."""
        from handlers.client_handler import handle_get_client_gallery
        
        gallery_with_access = {**sample_gallery, 'client_emails': [sample_client['email']]}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_access]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {'Items': [], 'LastEvaluatedKey': None}
        
        # Test min enforcement (0 -> 1)
        result = handle_get_client_gallery('gallery_123', sample_client, query_params={'page_size': '0'})
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 1
        
        # Test max enforcement (200 -> 100)
        result = handle_get_client_gallery('gallery_123', sample_client, query_params={'page_size': '200'})
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 100
    
    def test_get_client_gallery_photo_exception_handled(self, sample_user, sample_gallery, sample_client, mock_tables):
        """Get client gallery handles photo loading exceptions."""
        from handlers.client_handler import handle_get_client_gallery
        
        gallery_with_access = {**sample_gallery, 'client_emails': [sample_client['email']]}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_access]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.side_effect = Exception("DynamoDB error")
        
        result = handle_get_client_gallery('gallery_123', sample_client, query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['photos'] == []
        assert body['photo_count'] == 0
    
    def test_get_client_gallery_pagination_metadata_only_when_requested(self, sample_user, sample_gallery, sample_photo, sample_client, mock_tables):
        """Get client gallery includes pagination metadata only when pagination params are provided."""
        from handlers.client_handler import handle_get_client_gallery
        
        gallery_with_access = {**sample_gallery, 'client_emails': [sample_client['email']]}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_access]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': None
        }
        
        # Without pagination params
        result = handle_get_client_gallery('gallery_123', sample_client, query_params=None)
        body = json.loads(result['body'])
        assert 'pagination' not in body
        
        # With other query params (not pagination)
        result = handle_get_client_gallery('gallery_123', sample_client, query_params={'sort': 'desc'})
        body = json.loads(result['body'])
        assert 'pagination' not in body
        
        # With pagination params
        result = handle_get_client_gallery('gallery_123', sample_client, query_params={'page_size': '10'})
        body = json.loads(result['body'])
        assert 'pagination' in body

# Test: handle_get_client_gallery_by_token
class TestHandleGetClientGalleryByToken:
    """Tests for handle_get_client_gallery_by_token endpoint (public access)."""
    
    def test_get_gallery_by_token_success(self, sample_user, sample_gallery, sample_photo, mock_tables):
        """Get gallery by token successfully."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        gallery_with_token = {**sample_gallery, 'share_token': 'test_token_123'}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_token]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': None
        }
        
        result = handle_get_client_gallery_by_token('test_token_123', query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['id'] == 'gallery_123'
        assert 'photos' in body
    
    def test_get_gallery_by_token_not_found(self, mock_tables):
        """Get gallery by token returns 404 when token not found."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        mock_tables['galleries'].scan.return_value = {'Items': []}
        
        result = handle_get_client_gallery_by_token('invalid_token', query_params=None)
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert 'not found' in body['error'].lower()
    
    def test_get_gallery_by_token_with_pagination(self, sample_user, sample_gallery, sample_photo, mock_tables):
        """Get gallery by token with pagination."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        gallery_with_token = {**sample_gallery, 'share_token': 'test_token_123'}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_token]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': {'id': 'next_photo'}
        }
        
        query_params = {'page_size': '25'}
        result = handle_get_client_gallery_by_token('test_token_123', query_params=query_params)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'pagination' in body
        assert body['pagination']['page_size'] == 25
        assert body['pagination']['has_more'] is True
    
    def test_get_gallery_by_token_pagination_enforces_limits(self, sample_user, sample_gallery, mock_tables):
        """Get gallery by token enforces pagination limits."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        gallery_with_token = {**sample_gallery, 'share_token': 'test_token_123'}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_token]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {'Items': [], 'LastEvaluatedKey': None}
        
        # Test min enforcement
        result = handle_get_client_gallery_by_token('test_token_123', query_params={'page_size': '-5'})
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 1
        
        # Test max enforcement
        result = handle_get_client_gallery_by_token('test_token_123', query_params={'page_size': '500'})
        body = json.loads(result['body'])
        assert body['pagination']['page_size'] == 100
    
    def test_get_gallery_by_token_photo_exception_handled(self, sample_user, sample_gallery, mock_tables):
        """Get gallery by token handles photo loading exceptions."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        gallery_with_token = {**sample_gallery, 'share_token': 'test_token_123'}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_token]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.side_effect = Exception("DynamoDB error")
        
        result = handle_get_client_gallery_by_token('test_token_123', query_params=None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['photos'] == []
        assert body['photo_count'] == 0
    
    def test_get_gallery_by_token_uses_projection(self, sample_user, sample_gallery, sample_photo, mock_tables):
        """Get gallery by token uses ProjectionExpression for optimization."""
        from handlers.client_handler import handle_get_client_gallery_by_token
        
        gallery_with_token = {**sample_gallery, 'share_token': 'test_token_123'}
        
        mock_tables['galleries'].scan.return_value = {'Items': [gallery_with_token]}
        mock_tables['users'].query.return_value = {'Items': [sample_user]}
        mock_tables['photos'].query.return_value = {
            'Items': [sample_photo],
            'LastEvaluatedKey': None
        }
        
        handle_get_client_gallery_by_token('test_token_123', query_params=None)
        
        # Verify ProjectionExpression was used
        call_kwargs = mock_tables['photos'].query.call_args[1]
        assert 'ProjectionExpression' in call_kwargs
        assert '#st' in call_kwargs['ExpressionAttributeNames']

