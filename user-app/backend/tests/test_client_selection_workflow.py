"""
Test Suite for Client Selection Workflow
Tests the client photo selection process and session management
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from handlers.client_selection_handler import (
    handle_create_selection_session,
    handle_add_to_selection,
    handle_remove_from_selection,
    handle_get_selection_session,
    handle_submit_selection,
    handle_list_selection_sessions
)


class TestClientSelectionWorkflow:
    """Test client selection workflow functionality"""
    
    @pytest.fixture
    def mock_photographer(self):
        """Mock photographer user"""
        return {
            'id': 'photographer123',
            'email': 'photographer@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
    
    @pytest.fixture
    def mock_gallery(self):
        """Mock gallery data"""
        return {
            'id': 'gallery123',
            'user_id': 'photographer123',
            'name': 'Wedding Photos',
            'privacy': 'private'
        }
    
    @pytest.fixture
    def mock_session(self):
        """Mock selection session"""
        return {
            'id': 'session123',
            'gallery_id': 'gallery123',
            'photographer_id': 'photographer123',
            'client_email': 'client@example.com',
            'client_name': 'John Doe',
            'max_selections': 20,
            'deadline': '2025-12-31T23:59:59Z',
            'status': 'active',
            'selections': [],
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z'
        }
    
    @pytest.fixture
    def mock_photo(self):
        """Mock photo data"""
        return {
            'id': 'photo123',
            'gallery_id': 'gallery123',
            'original_filename': 'IMG_1234.jpg',
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'file_size': 5000000,
            'favorite_count': 0
        }
    
    @patch('handlers.client_selection_handler.galleries_table')
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_create_selection_session_success(
        self, mock_selections_table, mock_galleries_table,
        mock_photographer, mock_gallery
    ):
        """Test successful selection session creation"""
        mock_galleries_table.get_item.return_value = {'Item': mock_gallery}
        
        body = {
            'gallery_id': 'gallery123',
            'client_email': 'client@example.com',
            'client_name': 'John Doe',
            'max_selections': 20,
            'deadline': '2025-12-31T23:59:59Z'
        }
        
        response = handle_create_selection_session(mock_photographer, body)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body_data['success'] == True
        assert 'session' in body_data
        assert 'selection_url' in body_data
        assert body_data['session']['gallery_id'] == 'gallery123'
        assert body_data['session']['client_email'] == 'client@example.com'
        assert body_data['session']['status'] == 'active'
        
        # Verify table.put_item was called
        mock_selections_table.put_item.assert_called_once()
    
    @patch('handlers.client_selection_handler.galleries_table')
    def test_create_selection_session_missing_data(
        self, mock_galleries_table, mock_photographer
    ):
        """Test session creation with missing required data"""
        body = {
            'gallery_id': 'gallery123'
            # Missing client_email
        }
        
        response = handle_create_selection_session(mock_photographer, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'error' in body_data
    
    @patch('handlers.client_selection_handler.galleries_table')
    def test_create_selection_session_gallery_not_found(
        self, mock_galleries_table, mock_photographer
    ):
        """Test session creation for non-existent gallery"""
        mock_galleries_table.get_item.return_value = {}
        
        body = {
            'gallery_id': 'nonexistent',
            'client_email': 'client@example.com'
        }
        
        response = handle_create_selection_session(mock_photographer, body)
        
        assert response['statusCode'] == 404
    
    @patch('handlers.client_selection_handler.galleries_table')
    def test_create_selection_session_wrong_photographer(
        self, mock_galleries_table, mock_photographer
    ):
        """Test session creation for gallery owned by another photographer"""
        wrong_gallery = {
            'id': 'gallery123',
            'user_id': 'different_photographer',
            'name': 'Test Gallery'
        }
        mock_galleries_table.get_item.return_value = {'Item': wrong_gallery}
        
        body = {
            'gallery_id': 'gallery123',
            'client_email': 'client@example.com'
        }
        
        response = handle_create_selection_session(mock_photographer, body)
        
        assert response['statusCode'] == 403
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_add_to_selection_success(
        self, mock_selections_table, mock_session
    ):
        """Test successfully adding photo to selection"""
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo123',
            'note': 'Love this photo!'
        }
        
        response = handle_add_to_selection(None, body)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body_data['success'] == True
        assert body_data['selections_count'] == 1
        assert body_data['max_selections'] == 20
        assert body_data['remaining'] == 19
        
        # Verify update was called
        mock_selections_table.update_item.assert_called_once()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_add_to_selection_max_limit_reached(
        self, mock_selections_table, mock_session
    ):
        """Test adding photo when max limit reached"""
        # Fill up selections to max
        mock_session['selections'] = [
            {'photo_id': f'photo{i}', 'note': ''} 
            for i in range(20)
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo999'
        }
        
        response = handle_add_to_selection(None, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'limit_reached' in body_data
        assert body_data['limit_reached'] == True
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_add_to_selection_duplicate_photo(
        self, mock_selections_table, mock_session
    ):
        """Test adding photo that's already in selection"""
        mock_session['selections'] = [
            {'photo_id': 'photo123', 'note': 'Already selected'}
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo123'
        }
        
        response = handle_add_to_selection(None, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'already' in body_data['error'].lower()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_add_to_selection_inactive_session(
        self, mock_selections_table, mock_session
    ):
        """Test adding to inactive session"""
        mock_session['status'] = 'submitted'
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo123'
        }
        
        response = handle_add_to_selection(None, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'not active' in body_data['error'].lower()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_remove_from_selection_success(
        self, mock_selections_table, mock_session
    ):
        """Test successfully removing photo from selection"""
        mock_session['selections'] = [
            {'photo_id': 'photo123', 'note': 'Test'},
            {'photo_id': 'photo456', 'note': 'Test2'}
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo123'
        }
        
        response = handle_remove_from_selection(None, body)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body_data['success'] == True
        assert body_data['selections_count'] == 1
        
        # Verify update was called
        mock_selections_table.update_item.assert_called_once()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_remove_from_selection_not_found(
        self, mock_selections_table, mock_session
    ):
        """Test removing photo that's not in selection"""
        mock_session['selections'] = [
            {'photo_id': 'photo123', 'note': 'Test'}
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo999'  # Not in selection
        }
        
        response = handle_remove_from_selection(None, body)
        
        assert response['statusCode'] == 404
    
    @patch('handlers.client_selection_handler.client_selections_table')
    @patch('handlers.client_selection_handler.photos_table')
    def test_get_selection_session_success(
        self, mock_photos_table, mock_selections_table,
        mock_session, mock_photo
    ):
        """Test getting selection session with photo details"""
        mock_session['selections'] = [
            {'photo_id': 'photo123', 'note': 'Great shot!'}
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        mock_photos_table.get_item.return_value = {'Item': mock_photo}
        
        response = handle_get_selection_session(None, 'session123')
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body_data['id'] == 'session123'
        assert len(body_data['selections']) == 1
        assert 'photo' in body_data['selections'][0]
        assert body_data['selections'][0]['photo']['id'] == 'photo123'
    
    @patch('handlers.client_selection_handler.client_selections_table')
    @patch('handlers.client_selection_handler.photos_table')
    @patch('handlers.client_selection_handler.users_table')
    def test_submit_selection_success(
        self, mock_users_table, mock_photos_table,
        mock_selections_table, mock_session
    ):
        """Test successful selection submission"""
        mock_session['selections'] = [
            {'photo_id': 'photo123', 'note': 'Love it!'},
            {'photo_id': 'photo456', 'note': 'Perfect!'}
        ]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        mock_users_table.query.return_value = {
            'Items': [{'email': 'photographer@example.com'}]
        }
        
        body = {
            'session_id': 'session123',
            'message': 'These are my favorites!'
        }
        
        response = handle_submit_selection(None, body)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body_data['success'] == True
        assert body_data['selections_count'] == 2
        assert body_data['session_id'] == 'session123'
        
        # Verify status update was called
        mock_selections_table.update_item.assert_called_once()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_submit_selection_empty(
        self, mock_selections_table, mock_session
    ):
        """Test submitting selection with no photos"""
        mock_session['selections'] = []
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123'
        }
        
        response = handle_submit_selection(None, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'no photos' in body_data['error'].lower()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_submit_selection_already_submitted(
        self, mock_selections_table, mock_session
    ):
        """Test submitting selection that's already submitted"""
        mock_session['status'] = 'submitted'
        mock_session['selections'] = [{'photo_id': 'photo123', 'note': ''}]
        mock_selections_table.get_item.return_value = {'Item': mock_session}
        
        body = {
            'session_id': 'session123'
        }
        
        response = handle_submit_selection(None, body)
        
        assert response['statusCode'] == 400
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'already submitted' in body_data['error'].lower()
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_list_selection_sessions(
        self, mock_selections_table, mock_photographer
    ):
        """Test listing all selection sessions for photographer"""
        sessions = [
            {
                'id': 'session1',
                'photographer_id': 'photographer123',
                'status': 'active',
                'created_at': '2025-01-01T00:00:00Z'
            },
            {
                'id': 'session2',
                'photographer_id': 'photographer123',
                'status': 'submitted',
                'created_at': '2025-01-02T00:00:00Z'
            }
        ]
        mock_selections_table.query.return_value = {'Items': sessions}
        
        response = handle_list_selection_sessions(mock_photographer, {})
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert 'sessions' in body_data
        assert body_data['count'] == 2
        assert len(body_data['sessions']) == 2
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_list_selection_sessions_filtered(
        self, mock_selections_table, mock_photographer
    ):
        """Test listing sessions filtered by status"""
        sessions = [
            {'id': 'session1', 'photographer_id': 'photographer123', 'status': 'active'},
            {'id': 'session2', 'photographer_id': 'photographer123', 'status': 'submitted'},
            {'id': 'session3', 'photographer_id': 'photographer123', 'status': 'submitted'}
        ]
        mock_selections_table.query.return_value = {'Items': sessions}
        
        query_params = {'status': 'submitted'}
        response = handle_list_selection_sessions(mock_photographer, query_params)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        # Should only return submitted sessions
        assert body_data['count'] == 2
        assert all(s['status'] == 'submitted' for s in body_data['sessions'])


class TestClientSelectionEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_session_not_found(self, mock_selections_table):
        """Test operations on non-existent session"""
        mock_selections_table.get_item.return_value = {}
        
        # Add to selection
        response = handle_add_to_selection(None, {
            'session_id': 'nonexistent',
            'photo_id': 'photo123'
        })
        assert response['statusCode'] == 404
        
        # Remove from selection
        response = handle_remove_from_selection(None, {
            'session_id': 'nonexistent',
            'photo_id': 'photo123'
        })
        assert response['statusCode'] == 404
        
        # Get session
        response = handle_get_selection_session(None, 'nonexistent')
        assert response['statusCode'] == 404
    
    @patch('handlers.client_selection_handler.client_selections_table')
    def test_no_max_selections_limit(
        self, mock_selections_table
    ):
        """Test selection without max limit"""
        session = {
            'id': 'session123',
            'gallery_id': 'gallery123',
            'status': 'active',
            'selections': [],
            'max_selections': None  # No limit
        }
        mock_selections_table.get_item.return_value = {'Item': session}
        
        body = {
            'session_id': 'session123',
            'photo_id': 'photo123'
        }
        
        response = handle_add_to_selection(None, body)
        
        assert response['statusCode'] == 200
        body_data = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert body_data['remaining'] is None  # No limit
    
    def test_missing_required_fields(self):
        """Test handlers with missing required fields"""
        # Create session without gallery_id
        response = handle_create_selection_session(
            {'id': 'user123'}, 
            {'client_email': 'client@example.com'}
        )
        assert response['statusCode'] == 400
        
        # Add to selection without session_id
        response = handle_add_to_selection(None, {'photo_id': 'photo123'})
        assert response['statusCode'] == 400
        
        # Remove without photo_id
        response = handle_remove_from_selection(None, {'session_id': 'session123'})
        assert response['statusCode'] == 400
        
        # Submit without session_id
        response = handle_submit_selection(None, {})
        assert response['statusCode'] == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

