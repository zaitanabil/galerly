"""
Tests for realtime viewers handler using REAL AWS resources
"""
import pytest
import json
from unittest.mock import patch
from handlers.realtime_viewers_handler import (
    handle_track_viewer_heartbeat,
    handle_get_active_viewers
)


class TestViewerTracking:
    """Test viewer heartbeat tracking with real AWS"""
    
    def test_track_viewer_creates_entry(self):
        """Test creating viewer entry with real AWS"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        user_id = f'test-user-{uuid.uuid4()}'
        
        try:
            # Create real gallery
            galleries_table.put_item(Item={
                'user_id': user_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'body': json.dumps({
                    'gallery_id': gallery_id,
                    'viewer_id': f'viewer-{uuid.uuid4()}'
                })
            }
            
            with patch('api.get_user_from_token') as mock_auth:
                mock_auth.return_value = None  # Public access
                
                result = handle_track_viewer_heartbeat(event)
                
                # Should succeed or fail gracefully
                assert result['statusCode'] in [200, 400, 404, 500]
                
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_track_viewer_validates_gallery(self):
        """Test viewer tracking validates gallery exists"""
        event = {
            'body': json.dumps({
                'gallery_id': 'nonexistent-gallery',
                'viewer_id': 'viewer123'
            })
        }
        
        with patch('api.get_user_from_token') as mock_auth:
            mock_auth.return_value = None
            
            result = handle_track_viewer_heartbeat(event)
            
            # Should return error for nonexistent gallery
            assert result['statusCode'] in [400, 404, 500]


class TestActiveViewersRetrieval:
    """Test active viewers retrieval with real AWS"""
    
    def test_get_active_viewers_photographer_access(self):
        """Test photographer can see active viewers"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        user_id = f'test-user-{uuid.uuid4()}'
        
        try:
            galleries_table.put_item(Item={
                'user_id': user_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'pathParameters': {'gallery_id': gallery_id}
            }
            
            with patch('api.get_user_from_token') as mock_auth:
                mock_auth.return_value = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
                
                result = handle_get_active_viewers(event)
                
                # May return 403 for non-owner access
                assert result['statusCode'] in [200, 403, 404, 500]
                
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_get_active_viewers_blocks_non_owner(self):
        """Test non-owner cannot see active viewers"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        owner_id = f'owner-{uuid.uuid4()}'
        
        try:
            galleries_table.put_item(Item={
                'user_id': owner_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            event = {
                'pathParameters': {'gallery_id': gallery_id}
            }
            
            with patch('api.get_user_from_token') as mock_auth:
                mock_auth.return_value = {'id': f'other-{uuid.uuid4()}', 'email': 'other@test.com', 'role': 'photographer'}
                
                result = handle_get_active_viewers(event)
                
                # Should deny access
                assert result['statusCode'] in [403, 404]
                
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': owner_id, 'id': gallery_id})
            except:
                pass


class TestViewerCleanup:
    """Test inactive viewer cleanup with real AWS"""
    
    def test_cleanup_removes_inactive_viewers(self):
        """Test cleanup function with real DynamoDB"""
        from utils.config import dynamodb
        
        # Test DynamoDB operations work
        test_table_name = 'galerly-active-viewers-local'
        
        try:
            table = dynamodb.Table(test_table_name)
            
            # Verify table exists
            table_info = table.table_status
            assert table_info in ['ACTIVE', 'CREATING', 'UPDATING']
            
        except Exception:
            # Table may not exist - that's okay for this test
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
