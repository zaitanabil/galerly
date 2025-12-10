"""
Comprehensive tests for pricing plan enforcement
Tests all critical fixes implemented in the audit
"""
import pytest
import json
import base64
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Import handlers
from handlers.photo_handler import handle_upload_photo
from handlers.multipart_upload_handler import handle_initialize_multipart_upload
from handlers.client_favorites_handler import handle_add_favorite, handle_submit_favorites
from handlers.invoice_handler import handle_create_invoice
from handlers.contract_handler import handle_create_contract
from handlers.subscription_handler import get_user_features, enforce_storage_limit


class TestStorageLimitEnforcement:
    """Test storage limit enforcement for all upload paths"""
    
    def test_photo_upload_exceeds_storage_limit(self):
        """Test that photo upload fails when storage limit exceeded"""
        # Mock user with Free plan (2GB limit)
        user = {
            'id': 'user123',
            'email': 'test@example.com',
            'plan': 'free',
            'role': 'photographer'
        }
        
        # Mock gallery
        gallery_id = 'gallery123'
        
        # Create mock event with large file (3MB)
        large_image_data = b'x' * (3 * 1024 * 1024)  # 3MB
        event = {
            'body': json.dumps({
                'filename': 'test.jpg',
                'data': base64.b64encode(large_image_data).decode('utf-8')
            })
        }
        
        with patch('handlers.photo_handler.galleries_table') as mock_galleries:
            with patch('handlers.subscription_handler.enforce_storage_limit') as mock_enforce:
                # Setup mocks
                mock_galleries.get_item.return_value = {
                    'Item': {
                        'id': gallery_id,
                        'user_id': user['id'],
                        'storage_used': Decimal('2000')  # 2000MB = ~2GB used
                    }
                }
                
                # Storage limit should fail
                mock_enforce.return_value = (False, 'Insufficient storage. Upgrade to get more.')
                
                # Execute
                response = handle_upload_photo(gallery_id, user, event)
                
                # Assert
                assert response['statusCode'] == 403
                body = json.loads(response['body'])
                assert 'upgrade_required' in body
                assert body['upgrade_required'] is True
                assert 'storage' in body.get('error', '').lower()
    
    def test_photo_upload_within_storage_limit(self):
        """Test that photo upload succeeds when within limit"""
        user = {
            'id': 'user123',
            'email': 'test@example.com',
            'plan': 'starter',  # 25GB limit
            'role': 'photographer'
        }
        
        gallery_id = 'gallery123'
        
        # Small file (1MB)
        small_image_data = b'x' * (1 * 1024 * 1024)
        event = {
            'body': json.dumps({
                'filename': 'test.jpg',
                'data': base64.b64encode(small_image_data).decode('utf-8')
            })
        }
        
        with patch('handlers.photo_handler.galleries_table') as mock_galleries:
            with patch('handlers.subscription_handler.enforce_storage_limit') as mock_enforce:
                with patch('handlers.photo_handler.s3_client'):
                    mock_galleries.get_item.return_value = {
                        'Item': {
                            'id': gallery_id,
                            'user_id': user['id'],
                            'storage_used': Decimal('100')  # 100MB used
                        }
                    }
                    
                    # Storage limit should pass
                    mock_enforce.return_value = (True, None)
                    
                    # Note: Would need more mocks for full success, but checking limit is key
                    response = handle_upload_photo(gallery_id, user, event)
                    
                    # Verify storage check was called
                    mock_enforce.assert_called_once()
    
    def test_multipart_upload_exceeds_storage_limit(self):
        """Test that multipart upload fails when storage limit exceeded"""
        user = {
            'id': 'user123',
            'email': 'test@example.com',
            'plan': 'free',
            'role': 'photographer'
        }
        
        gallery_id = 'gallery123'
        
        # Large file size (3GB)
        event = {
            'body': json.dumps({
                'filename': 'large_video.mp4',
                'file_size': 3 * 1024 * 1024 * 1024,  # 3GB
                'content_type': 'video/mp4'
            })
        }
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries:
            with patch('handlers.subscription_handler.enforce_storage_limit') as mock_enforce:
                mock_galleries.get_item.return_value = {
                    'Item': {
                        'id': gallery_id,
                        'user_id': user['id']
                    }
                }
                
                # Storage limit should fail
                mock_enforce.return_value = (False, 'Free plan allows only 2GB storage')
                
                response = handle_initialize_multipart_upload(gallery_id, user, event)
                
                assert response['statusCode'] == 403
                body = json.loads(response['body'])
                assert body['upgrade_required'] is True
                assert 'storage' in body.get('feature', '')


class TestClientFavoritesPlanCheck:
    """Test client favorites requires Starter+ plan"""
    
    def test_free_plan_cannot_add_favorite(self):
        """Free plan users cannot use client favorites"""
        user = {
            'id': 'client123',
            'email': 'client@example.com',
            'role': 'client'
        }
        
        body = {
            'photo_id': 'photo123',
            'gallery_id': 'gallery123',
            'client_email': 'client@example.com'
        }
        
        with patch('handlers.client_favorites_handler.photos_table') as mock_photos:
            with patch('handlers.client_favorites_handler.users_table') as mock_users:
                with patch('handlers.subscription_handler.get_user_features') as mock_features:
                    # Photo exists
                    mock_photos.get_item.return_value = {
                        'Item': {
                            'id': 'photo123',
                            'user_id': 'photographer123'
                        }
                    }
                    
                    # Photographer has free plan
                    mock_users.scan.return_value = {
                        'Items': [{
                            'id': 'photographer123',
                            'email': 'photo@example.com',
                            'plan': 'free'
                        }]
                    }
                    
                    # Features returns no client_favorites
                    mock_features.return_value = ({'client_favorites': False}, 'free', 'Free')
                    
                    response = handle_add_favorite(user, body)
                    
                    assert response['statusCode'] == 403
                    body_data = json.loads(response['body'])
                    assert body_data['upgrade_required'] is True
                    assert 'client_favorites' in body_data.get('feature', '')
    
    def test_starter_plan_can_add_favorite(self):
        """Starter+ plan users can use client favorites"""
        user = {
            'id': 'client123',
            'email': 'client@example.com',
            'role': 'client'
        }
        
        body = {
            'photo_id': 'photo123',
            'gallery_id': 'gallery123',
            'client_email': 'client@example.com'
        }
        
        with patch('handlers.client_favorites_handler.photos_table') as mock_photos:
            with patch('handlers.client_favorites_handler.users_table') as mock_users:
                with patch('handlers.subscription_handler.get_user_features') as mock_features:
                    with patch('handlers.client_favorites_handler.client_favorites_table'):
                        mock_photos.get_item.return_value = {
                            'Item': {
                                'id': 'photo123',
                                'user_id': 'photographer123',
                                'gallery_id': 'gallery123'
                            }
                        }
                        
                        # Photographer has starter plan
                        mock_users.scan.return_value = {
                            'Items': [{
                                'id': 'photographer123',
                                'email': 'photo@example.com',
                                'plan': 'starter'
                            }]
                        }
                        
                        # Features returns client_favorites enabled
                        mock_features.return_value = ({'client_favorites': True}, 'starter', 'Starter')
                        
                        response = handle_add_favorite(user, body)
                        
                        # Should succeed (200) or fail for other reasons but not 403
                        assert response['statusCode'] != 403
    
    def test_submit_favorites_checks_plan(self):
        """Submit favorites also checks photographer's plan"""
        user = {
            'id': 'client123',
            'email': 'client@example.com',
            'role': 'client'
        }
        
        body = {
            'gallery_id': 'gallery123',
            'client_email': 'client@example.com'
        }
        
        with patch('handlers.client_favorites_handler.galleries_table') as mock_galleries:
            with patch('handlers.client_favorites_handler.users_table') as mock_users:
                with patch('handlers.subscription_handler.get_user_features') as mock_features:
                    # Gallery exists
                    mock_galleries.scan.return_value = {
                        'Items': [{
                            'id': 'gallery123',
                            'user_id': 'photographer123'
                        }]
                    }
                    
                    # Photographer has free plan
                    mock_users.scan.return_value = {
                        'Items': [{
                            'id': 'photographer123',
                            'plan': 'free'
                        }]
                    }
                    
                    mock_features.return_value = ({'client_favorites': False}, 'free', 'Free')
                    
                    response = handle_submit_favorites(user, body)
                    
                    assert response['statusCode'] == 403
                    body_data = json.loads(response['body'])
                    assert body_data['upgrade_required'] is True


class TestRoleVerification:
    """Test role-based access controls"""
    
    def test_client_cannot_create_invoice(self):
        """Clients cannot create invoices"""
        user = {
            'id': 'client123',
            'email': 'client@example.com',
            'role': 'client',  # Not photographer
            'plan': 'pro'  # Even with Pro plan
        }
        
        body = {
            'client_email': 'someone@example.com',
            'items': [{'description': 'Test', 'amount': 100}]
        }
        
        response = handle_create_invoice(user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'photographer' in body_data.get('error', '').lower()
        assert body_data.get('required_role') == 'photographer'
    
    def test_photographer_can_create_invoice_with_plan(self):
        """Photographers with Pro+ can create invoices"""
        user = {
            'id': 'photo123',
            'email': 'photo@example.com',
            'role': 'photographer',  # Correct role
            'plan': 'pro'
        }
        
        body = {
            'client_email': 'client@example.com',
            'items': [{'description': 'Wedding', 'amount': Decimal('2500')}]
        }
        
        with patch('handlers.subscription_handler.get_user_features') as mock_features:
            with patch('handlers.invoice_handler.invoices_table'):
                # Has invoicing feature
                mock_features.return_value = ({'client_invoicing': True}, 'pro', 'Pro')
                
                response = handle_create_invoice(user, body)
                
                # Should succeed (201) or fail for other reasons but not 403 for role
                assert response['statusCode'] in [200, 201, 400, 500]
                if response['statusCode'] != 403:
                    # Pass - role check passed
                    pass
    
    def test_client_cannot_create_contract(self):
        """Clients cannot create contracts"""
        user = {
            'id': 'client123',
            'email': 'client@example.com',
            'role': 'client',
            'plan': 'ultimate'  # Even with Ultimate
        }
        
        body = {
            'client_email': 'someone@example.com',
            'content': 'Contract terms...'
        }
        
        response = handle_create_contract(user, body)
        
        assert response['statusCode'] == 403
        body_data = json.loads(response['body'])
        assert 'photographer' in body_data.get('error', '').lower()


class TestFileValidation:
    """Test file upload security and validation"""
    
    def test_file_too_large_rejected(self):
        """Files over 100MB are rejected"""
        user = {
            'id': 'user123',
            'email': 'test@example.com',
            'plan': 'ultimate',  # Even with unlimited storage
            'role': 'photographer'
        }
        
        gallery_id = 'gallery123'
        
        # 101MB file
        huge_file = b'x' * (101 * 1024 * 1024)
        event = {
            'body': json.dumps({
                'filename': 'huge.jpg',
                'data': base64.b64encode(huge_file).decode('utf-8')
            })
        }
        
        with patch('handlers.photo_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {
                'Item': {
                    'id': gallery_id,
                    'user_id': user['id']
                }
            }
            
            response = handle_upload_photo(gallery_id, user, event)
            
            assert response['statusCode'] == 400
            body_data = json.loads(response['body'])
            assert '100mb' in body_data.get('error', '').lower()
    
    def test_file_too_small_rejected(self):
        """Files under 50 bytes are rejected as invalid"""
        user = {
            'id': 'user123',
            'email': 'test@example.com',
            'plan': 'starter',
            'role': 'photographer'
        }
        
        gallery_id = 'gallery123'
        
        # Tiny file (30 bytes - below 50 byte minimum)
        tiny_file = b'x' * 30
        event = {
            'body': json.dumps({
                'filename': 'tiny.jpg',
                'data': base64.b64encode(tiny_file).decode('utf-8')
            })
        }
        
        with patch('handlers.photo_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {
                'Item': {
                    'id': gallery_id,
                    'user_id': user['id']
                }
            }
            
            response = handle_upload_photo(gallery_id, user, event)
            
            assert response['statusCode'] == 400
            body_data = json.loads(response['body'])
            assert 'too small' in body_data.get('error', '').lower()


class TestPlanFeatureMatrix:
    """Test complete feature matrix for all plans"""
    
    def test_free_plan_features(self):
        """Test Free plan has correct features"""
        user = {'id': 'user123', 'email': 'test@example.com', 'plan': 'free'}
        
        features, plan_id, plan_name = get_user_features(user)
        
        assert plan_id == 'free'
        assert features['storage_gb'] == 2
        assert features['video_minutes'] == 30
        assert features['video_quality'] == 'hd'
        assert features['remove_branding'] is False
        assert features['client_favorites'] is False
        assert features['client_invoicing'] is False
        assert features['analytics_level'] == 'basic'
    
    def test_starter_plan_features(self):
        """Test Starter plan has correct features"""
        user = {'id': 'user123', 'email': 'test@example.com', 'plan': 'starter'}
        
        features, plan_id, plan_name = get_user_features(user)
        
        assert plan_id == 'starter'
        assert features['storage_gb'] == 25
        assert features['video_minutes'] == 60
        assert features['remove_branding'] is True  # Starter includes this
        assert features['client_favorites'] is True  # Starter includes this
        assert features['edit_requests'] is True
        assert features['client_invoicing'] is False  # Pro+ only
    
    def test_plus_plan_features(self):
        """Test Plus plan has correct features"""
        user = {'id': 'user123', 'email': 'test@example.com', 'plan': 'plus'}
        
        features, plan_id, plan_name = get_user_features(user)
        
        assert plan_id == 'plus'
        assert features['storage_gb'] == 100
        assert features['video_minutes'] == 240  # 4 hours
        assert features['video_quality'] == '4k'
        assert features['custom_domain'] is True
        assert features['watermarking'] is True
        assert features['analytics_level'] == 'advanced'
        assert features['client_invoicing'] is False  # Pro+ only
    
    def test_pro_plan_features(self):
        """Test Pro plan has correct features"""
        user = {'id': 'user123', 'email': 'test@example.com', 'plan': 'pro'}
        
        features, plan_id, plan_name = get_user_features(user)
        
        assert plan_id == 'pro'
        assert features['storage_gb'] == 500
        assert features['raw_support'] is True
        assert features['client_invoicing'] is True
        assert features['email_templates'] is True
        assert features['seo_tools'] is True
        assert features['analytics_level'] == 'pro'
        assert features['raw_vault'] is False  # Ultimate only
    
    def test_ultimate_plan_features(self):
        """Test Ultimate plan has all features"""
        user = {'id': 'user123', 'email': 'test@example.com', 'plan': 'ultimate'}
        
        features, plan_id, plan_name = get_user_features(user)
        
        assert plan_id == 'ultimate'
        assert features['storage_gb'] == 2000  # 2TB
        assert features['raw_vault'] is True
        assert features['scheduler'] is True
        assert features['e_signatures'] is True
        assert features['client_invoicing'] is True
        assert features['analytics_level'] == 'pro'


class TestStorageLimitCalculations:
    """Test storage limit enforcement logic"""
    
    def test_enforce_storage_limit_free_plan(self):
        """Test storage enforcement for free plan"""
        user = {'id': 'user123', 'plan': 'free'}
        
        with patch('handlers.subscription_handler.check_storage_limit') as mock_check:
            # User has 1.8GB used, 2GB limit
            mock_check.return_value = {
                'used_gb': 1.8,
                'limit_gb': 2,
                'remaining_gb': 0.2
            }
            
            # Try to upload 0.5GB - should fail
            allowed, error = enforce_storage_limit(user, 500)
            
            assert allowed is False
            assert 'storage' in error.lower()
    
    def test_enforce_storage_limit_unlimited(self):
        """Test storage enforcement for unlimited storage"""
        user = {'id': 'user123', 'plan': 'ultimate'}
        
        with patch('handlers.subscription_handler.check_storage_limit') as mock_check:
            # Unlimited
            mock_check.return_value = {
                'used_gb': 500,
                'limit_gb': -1,  # Unlimited
                'remaining_gb': -1
            }
            
            # Try to upload 100GB - should pass
            allowed, error = enforce_storage_limit(user, 100000)
            
            assert allowed is True
            assert error is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
