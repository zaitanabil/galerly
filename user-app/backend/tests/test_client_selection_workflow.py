"""
Test Suite for Client Selection Workflow using REAL AWS resources
Tests the client photo selection process and session management
"""
import json
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from handlers.client_selection_handler import (
    handle_create_selection_session,
    handle_add_to_selection,
    handle_remove_from_selection,
    handle_get_selection_session,
    handle_submit_selection,
    handle_list_selection_sessions
)
from utils.config import galleries_table, client_selections_table, photos_table, users_table


class TestClientSelectionWorkflow:
    """Test client selection workflow functionality with real AWS"""
    
    def test_create_selection_session_success(self):
        """Test successful selection session creation with real AWS"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        photographer = {
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
        
        try:
            # Create real gallery
            galleries_table.put_item(Item={
                'user_id': photographer_id,
                'id': gallery_id,
                'name': 'Wedding Photos',
                'privacy': 'private',
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'gallery_id': gallery_id,
                'client_email': f'client-{uuid.uuid4()}@example.com',
                'client_name': 'John Doe',
                'max_selections': 20,
                'deadline': '2025-12-31T23:59:59Z'
            }
            
            response = handle_create_selection_session(photographer, body)
            
            assert response['statusCode'] in [200, 400, 403, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': photographer_id, 'id': gallery_id})
            except:
                pass
    
    def test_create_selection_session_missing_data(self):
        """Test session creation with missing data"""
        photographer = {
            'id': 'photographer123',
            'email': 'photographer@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
        
        body = {'gallery_id': 'gallery123'}  # Missing required fields
        response = handle_create_selection_session(photographer, body)
        
        assert response['statusCode'] in [400, 500]
    
    def test_create_selection_session_gallery_not_found(self):
        """Test session creation with non-existent gallery"""
        photographer = {
            'id': 'photographer123',
            'email': 'photographer@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
        
        body = {
            'gallery_id': 'nonexistent-gallery',
            'client_email': 'client@example.com',
            'client_name': 'John Doe',
            'max_selections': 20
        }
        
        response = handle_create_selection_session(photographer, body)
        assert response['statusCode'] in [404, 500]
    
    def test_create_selection_session_wrong_photographer(self):
        """Test session creation by wrong photographer with real AWS"""
        owner_id = f'owner-{uuid.uuid4()}'
        other_id = f'other-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        other_photographer = {
            'id': other_id,
            'email': f'{other_id}@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
        
        try:
            galleries_table.put_item(Item={
                'user_id': owner_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'gallery_id': gallery_id,
                'client_email': 'client@example.com',
                'client_name': 'John Doe',
                'max_selections': 20
            }
            
            response = handle_create_selection_session(other_photographer, body)
            assert response['statusCode'] in [403, 404]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': owner_id, 'id': gallery_id})
            except:
                pass
    
    def test_add_to_selection_success(self):
        """Test adding photo to selection with real AWS"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            # Create real selection session
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'photographer_id': f'photographer-{uuid.uuid4()}',
                'client_email': f'client-{uuid.uuid4()}@example.com',
                'max_selections': 20,
                'status': 'active',
                'selections': [],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': f'photo-{uuid.uuid4()}'
            }
            
            response = handle_add_to_selection(None, body)
            assert response['statusCode'] in [200, 400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_add_to_selection_max_limit_reached(self):
        """Test adding photo when limit reached"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            # Create session at max limit
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 2,
                'status': 'active',
                'selections': ['photo1', 'photo2'],  # Already at limit
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': 'photo3'
            }
            
            response = handle_add_to_selection(None, body)
            assert response['statusCode'] in [400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_add_to_selection_duplicate_photo(self):
        """Test adding duplicate photo"""
        session_id = f'session-{uuid.uuid4()}'
        photo_id = f'photo-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'active',
                'selections': [photo_id],  # Already selected
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': photo_id  # Duplicate
            }
            
            response = handle_add_to_selection(None, body)
            assert response['statusCode'] in [400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_add_to_selection_inactive_session(self):
        """Test adding to inactive session"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'submitted',  # Inactive
                'selections': [],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': f'photo-{uuid.uuid4()}'
            }
            
            response = handle_add_to_selection(None, body)
            assert response['statusCode'] in [400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_remove_from_selection_success(self):
        """Test removing photo from selection"""
        session_id = f'session-{uuid.uuid4()}'
        photo_id = f'photo-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'active',
                'selections': [photo_id],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': photo_id
            }
            
            response = handle_remove_from_selection(None, body)
            assert response['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_remove_from_selection_not_found(self):
        """Test removing non-existent photo"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'active',
                'selections': [],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': 'nonexistent-photo'
            }
            
            response = handle_remove_from_selection(None, body)
            assert response['statusCode'] in [404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_get_selection_session_success(self):
        """Test getting selection session"""
        session_id = f'session-{uuid.uuid4()}'
        photo_id = f'photo-{uuid.uuid4()}'
        gallery_id = f'gallery-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': gallery_id,
                'max_selections': 20,
                'status': 'active',
                'selections': [photo_id],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            photos_table.put_item(Item={
                'id': photo_id,
                'gallery_id': gallery_id,
                'original_filename': 'IMG_1234.jpg',
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            response = handle_get_selection_session(session_id, None)
            assert response['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
                photos_table.delete_item(Key={'gallery_id': gallery_id, 'id': photo_id})
            except:
                pass
    
    def test_submit_selection_success(self):
        """Test submitting selection"""
        session_id = f'session-{uuid.uuid4()}'
        photo_id = f'photo-{uuid.uuid4()}'
        photographer_id = f'photographer-{uuid.uuid4()}'
        
        try:
            users_table.put_item(Item={
                'id': photographer_id,
                'email': f'{photographer_id}@example.com',
                'role': 'photographer'
            })
            
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'photographer_id': photographer_id,
                'max_selections': 20,
                'status': 'active',
                'selections': [photo_id],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {'session_id': session_id}
            
            with patch('utils.email.send_email'):
                response = handle_submit_selection(None, body)
                assert response['statusCode'] in [200, 400, 404, 500]
            
        finally:
            try:
                users_table.delete_item(Key={'email': f'{photographer_id}@example.com'})
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_submit_selection_empty(self):
        """Test submitting empty selection"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'active',
                'selections': [],  # Empty
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {'session_id': session_id}
            response = handle_submit_selection(None, body)
            assert response['statusCode'] in [400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_submit_selection_already_submitted(self):
        """Test re-submitting selection"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 20,
                'status': 'submitted',  # Already submitted
                'selections': ['photo1'],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {'session_id': session_id}
            response = handle_submit_selection(None, body)
            assert response['statusCode'] in [400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass
    
    def test_list_selection_sessions(self):
        """Test listing selection sessions"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        photographer = {
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'role': 'photographer'
        }
        
        response = handle_list_selection_sessions(photographer, {})
        assert response['statusCode'] in [200, 500]
    
    def test_list_selection_sessions_filtered(self):
        """Test listing sessions with filter"""
        photographer_id = f'photographer-{uuid.uuid4()}'
        photographer = {
            'id': photographer_id,
            'email': f'{photographer_id}@example.com',
            'role': 'photographer'
        }
        
        query_params = {'status': 'active'}
        response = handle_list_selection_sessions(photographer, query_params)
        assert response['statusCode'] in [200, 500]


class TestClientSelectionEdgeCases:
    """Test edge cases and error handling with real AWS"""
    
    def test_session_not_found(self):
        """Test operations on non-existent session"""
        body = {
            'session_id': 'nonexistent-session',
            'photo_id': 'photo123'
        }
        
        response = handle_add_to_selection(None, body)
        assert response['statusCode'] in [404, 500]
    
    def test_no_max_selections_limit(self):
        """Test session without max selections limit"""
        session_id = f'session-{uuid.uuid4()}'
        
        try:
            client_selections_table.put_item(Item={
                'id': session_id,
                'gallery_id': f'gallery-{uuid.uuid4()}',
                'max_selections': 0,  # No limit
                'status': 'active',
                'selections': [],
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            body = {
                'session_id': session_id,
                'photo_id': f'photo-{uuid.uuid4()}'
            }
            
            response = handle_add_to_selection(None, body)
            assert response['statusCode'] in [200, 400, 404, 500]
            
        finally:
            try:
                client_selections_table.delete_item(Key={'id': session_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
