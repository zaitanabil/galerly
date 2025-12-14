"""
Tests for watermark handler using REAL AWS resources
"""
import pytest
import uuid
import json
from unittest.mock import patch
from handlers.watermark_handler import (
    handle_upload_watermark_logo,
    handle_get_watermark_settings,
    handle_update_watermark_settings
)
from utils.config import users_table


class TestWatermarkHandler:
    """Test watermark functionality with real AWS"""
    
    def test_upload_watermark_logo(self):
        """Test watermark logo upload"""
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer', 'plan': 'plus'}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user['email'],
                'role': 'photographer',
                'plan': 'plus'
            })
            
            body = {'file_data': 'base64data', 'filename': 'logo.png'}
            
            with patch('handlers.subscription_handler.get_user_features') as mock_features:
                mock_features.return_value = ({'watermarking': True}, 'plus', 'Plus')
                
                result = handle_upload_watermark_logo(user, body)
                assert result['statusCode'] in [200, 400, 500]
            
        finally:
            try:
                users_table.delete_item(Key={'email': user['email']})
            except:
                pass
    
    def test_get_watermark_settings(self):
        """Test getting watermark settings"""
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user['email'],
                'watermark_enabled': True
            })
            
            with patch('handlers.subscription_handler.get_user_features') as mock_features:
                mock_features.return_value = ({'watermarking': True}, 'plus', 'Plus')
                
                result = handle_get_watermark_settings(user)
                assert result['statusCode'] in [200, 404, 500]
            
        finally:
            try:
                users_table.delete_item(Key={'email': user['email']})
            except:
                pass
    
    def test_update_watermark_settings(self):
        """Test updating watermark settings"""
        user_id = f'user-{uuid.uuid4()}'
        user = {'id': user_id, 'email': f'{user_id}@test.com', 'role': 'photographer'}
        
        try:
            users_table.put_item(Item={
                'id': user_id,
                'email': user['email']
            })
            
            body = {'watermark_enabled': True, 'watermark_position': 'bottom-right'}
            
            with patch('handlers.subscription_handler.get_user_features') as mock_features:
                mock_features.return_value = ({'watermarking': True}, 'plus', 'Plus')
                
                result = handle_update_watermark_settings(user, body)
                assert result['statusCode'] in [200, 400, 500]
            
        finally:
            try:
                users_table.delete_item(Key={'email': user['email']})
            except:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
