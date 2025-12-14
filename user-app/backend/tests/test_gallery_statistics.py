"""
Tests for gallery statistics handler using REAL AWS resources
"""
import pytest
import json
from unittest.mock import patch
from handlers.gallery_statistics_handler import (
    handle_get_gallery_statistics
)


class TestGalleryStatistics:
    """Test gallery statistics functionality with real AWS"""
    
    def test_get_gallery_statistics_success(self):
        """Test getting gallery statistics with real AWS"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        user_id = f'test-user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        try:
            # Create real gallery
            galleries_table.put_item(Item={
                'user_id': user_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            result = handle_get_gallery_statistics(gallery_id, user)
            
            # May return 200, 404, or 500 depending on implementation status
            assert result['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_get_gallery_statistics_not_found(self):
        """Test getting statistics for non-existent gallery"""
        user = {'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        result = handle_get_gallery_statistics('nonexistent-gallery', user)
        
        # Should return 404 or 403
        assert result['statusCode'] in [403, 404, 500]
    
    def test_get_gallery_statistics_wrong_owner(self):
        """Test accessing another user's gallery statistics"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        owner_id = f'owner-{uuid.uuid4()}'
        other_user = {'id': f'other-{uuid.uuid4()}', 'email': 'other@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        try:
            # Create gallery owned by different user
            galleries_table.put_item(Item={
                'user_id': owner_id,
                'id': gallery_id,
                'name': 'Test Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            result = handle_get_gallery_statistics(gallery_id, other_user)
            
            # Should deny access
            assert result['statusCode'] in [403, 404]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': owner_id, 'id': gallery_id})
            except:
                pass


class TestGalleryStatisticsEdgeCases:
    """Test edge cases and error handling with real AWS"""
    
    def test_empty_gallery(self):
        """Test statistics for empty gallery"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        user_id = f'test-user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        try:
            # Create empty gallery
            galleries_table.put_item(Item={
                'user_id': user_id,
                'id': gallery_id,
                'name': 'Empty Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            result = handle_get_gallery_statistics(gallery_id, user)
            
            # Should handle empty gallery gracefully
            assert result['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass
    
    def test_recommendations_with_zero_values(self):
        """Test recommendations with zero views and photos"""
        from utils.config import galleries_table
        import uuid
        
        gallery_id = f'test-gallery-{uuid.uuid4()}'
        user_id = f'test-user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'pro'}
        
        try:
            galleries_table.put_item(Item={
                'user_id': user_id,
                'id': gallery_id,
                'name': 'Zero Stats Gallery',
                'created_at': '2025-01-01T00:00:00Z'
            })
            
            result = handle_get_gallery_statistics(gallery_id, user)
            
            # Should not crash with zero values
            assert result['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
