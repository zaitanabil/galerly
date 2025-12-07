"""
Tests for Backend Utility Functions
Tests critical utility modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal


class TestAuthUtils:
    """Test authentication utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        from utils.auth import hash_password
        
        result = hash_password('password123')
        
        # SHA-256 produces a 64-character hex string
        assert result is not None
        assert len(result) == 64
        assert isinstance(result, str)
        
        # Same password should produce same hash
        assert hash_password('password123') == result
    
    def test_hash_password_different_inputs(self):
        """Test that different passwords produce different hashes"""
        from utils.auth import hash_password
        
        hash1 = hash_password('password123')
        hash2 = hash_password('password456')
        
        assert hash1 != hash2


class TestResponseUtils:
    """Test response utilities"""
    
    def test_create_response_success(self):
        """Test successful response creation"""
        from utils.response import create_response
        
        response = create_response(200, {'message': 'Success'})
        
        assert response['statusCode'] == 200
        assert 'body' in response
        assert 'message' in eval(response['body'])
    
    def test_create_response_with_headers(self):
        """Test response with custom headers"""
        from utils.response import create_response
        
        headers = {'X-Custom-Header': 'value'}
        response = create_response(200, {'data': 'test'}, headers)
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['X-Custom-Header'] == 'value'
    
    def test_create_response_cors_headers(self):
        """Test response includes CORS headers"""
        from utils.response import create_response
        
        response = create_response(200, {})
        
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']


class TestMimeTypes:
    """Test MIME type utilities"""
    
    def test_get_mime_type_for_common_extensions(self):
        """Test MIME type detection for common file types"""
        from utils.mime_types import get_mime_type
        
        assert get_mime_type('photo.jpg') == 'image/jpeg'
        assert get_mime_type('video.mp4') == 'video/mp4'
        assert get_mime_type('document.pdf') == 'application/pdf'
    
    def test_get_mime_type_case_insensitive(self):
        """Test MIME type detection is case insensitive"""
        from utils.mime_types import get_mime_type
        
        assert get_mime_type('PHOTO.JPG') == 'image/jpeg'
        assert get_mime_type('Video.MP4') == 'video/mp4'
    
    def test_get_mime_type_unknown(self):
        """Test MIME type for unknown extension"""
        from utils.mime_types import get_mime_type
        
        result = get_mime_type('file.unknown')
        assert result == 'application/octet-stream'


class TestCDNUrls:
    """Test CDN URL generation"""
    
    def test_get_photo_urls(self):
        """Test photo URL generation"""
        from utils.cdn_urls import get_photo_urls
        
        # Test with a sample S3 key
        urls = get_photo_urls('galleries/gallery-123/photo-456.jpg')
        
        # Should return a dict with different size URLs
        assert isinstance(urls, dict)
        assert 'original' in urls or 'large' in urls or len(urls) > 0
    
    def test_get_rendition_url(self):
        """Test rendition URL generation"""
        from utils.cdn_urls import get_rendition_url
        
        url = get_rendition_url('galleries/gallery-123/photo-456.jpg', 'large')
        
        # Should contain some part of the path
        assert 'gallery-123' in url or 'photo-456' in url or 'large' in url


class TestDuplicateDetector:
    """Test duplicate detection utilities"""
    
    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        from utils.duplicate_detector import calculate_file_hash
        
        # Test hash calculation
        data1 = b'test data'
        data2 = b'test data'
        data3 = b'different data'
        
        hash1 = calculate_file_hash(data1)
        hash2 = calculate_file_hash(data2)
        hash3 = calculate_file_hash(data3)
        
        # Same data should produce same hash
        assert hash1 == hash2
        # Different data should produce different hash
        assert hash1 != hash3
    
    def test_normalize_filename(self):
        """Test filename normalization"""
        from utils.duplicate_detector import normalize_filename
        
        # Test normalization
        assert normalize_filename('Photo.JPG') == normalize_filename('photo.jpg')
        assert normalize_filename('My Photo 123.png') == normalize_filename('my photo 123.png')


class TestSubscriptionValidator:
    """Test subscription validation utilities"""
    
    def test_normalize_plan_name(self):
        """Test plan name normalization"""
        from utils.subscription_validator import SubscriptionValidator
        
        # Normalize_plan returns the input as-is (identity function)
        assert SubscriptionValidator.normalize_plan('FREE') == 'FREE'
        assert SubscriptionValidator.normalize_plan('Starter') == 'Starter'
        assert SubscriptionValidator.normalize_plan('pro') == 'pro'
    
    def test_validate_plan_exists(self):
        """Test plan validation"""
        from utils.subscription_validator import SubscriptionValidator
        
        # Test plan level retrieval (valid plans return levels >= 0)
        assert SubscriptionValidator.get_plan_level('free') >= 0
        assert SubscriptionValidator.get_plan_level('starter') >= 0
        assert SubscriptionValidator.get_plan_level('pro') >= 0
    
    def test_validate_upgrade_path(self):
        """Test upgrade path validation"""
        from utils.subscription_validator import SubscriptionValidator, SubscriptionState
        
        # Test simple upgrade validation by checking plan levels
        free_level = SubscriptionValidator.get_plan_level('free')
        starter_level = SubscriptionValidator.get_plan_level('starter')
        pro_level = SubscriptionValidator.get_plan_level('pro')
        
        # Verify plan hierarchy
        assert free_level < starter_level < pro_level
        
        # Test plan validation
        result = SubscriptionValidator.validate_plan_exists('free')
        assert result.valid is True
        
        result = SubscriptionValidator.validate_plan_exists('invalid_plan')
        assert result.valid is False


class TestAuditLog:
    """Test audit logging utilities"""
    
    @patch('utils.audit_log.audit_table')
    def test_log_action(self, mock_table):
        """Test action logging"""
        from utils.audit_log import log_subscription_change
        
        mock_table.put_item.return_value = {}
        
        log_subscription_change(
            user_id='user-123',
            action='upgrade',
            from_plan='starter',
            to_plan='pro'
        )
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        assert call_args['user_id'] == 'user-123'
        assert call_args['action'] == 'upgrade'
    
    @patch('utils.audit_log.audit_table')
    def test_log_action_with_ip(self, mock_table):
        """Test action logging with metadata"""
        from utils.audit_log import log_subscription_change
        
        mock_table.put_item.return_value = {}
        
        log_subscription_change(
            user_id='user-123',
            action='upgrade',
            from_plan='starter',
            to_plan='pro',
            metadata={'ip': '192.168.1.1'}
        )
        
        call_args = mock_table.put_item.call_args[1]['Item']
        assert 'metadata' in call_args
        assert call_args['metadata'].get('ip') == '192.168.1.1'


