"""
Tests for scheduled handler using REAL AWS resources
"""
import pytest
import uuid
import json
from handlers.scheduled_handler import handle_process_scheduled_tasks
from utils.config import users_table


class TestScheduledTasks:
    """Test scheduled task processing with real AWS"""
    
    def test_process_scheduled_tasks(self):
        """Test processing scheduled tasks"""
        event = {}
        context = None
        
        # Should run without errors
        result = handle_process_scheduled_tasks(event, context)
        assert result is None or isinstance(result, dict)
    
    def test_scheduled_tasks_with_users(self):
        """Test scheduled tasks with real users"""
        user_id = f'user-{uuid.uuid4()}'
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': f'{user_id}@test.com',
                'role': 'photographer',
                'plan': 'free'
            })
            
            result = handle_process_scheduled_tasks({}, None)
            assert result is None or isinstance(result, dict)
            
        finally:
            try:
                users_table.delete_item(Key={'email': f'{user_id}@test.com'})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
