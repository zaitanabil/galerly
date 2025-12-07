"""
Tests for video utilities - duration tracking and enforcement
"""
import pytest
from utils.video_utils import (
    get_user_video_usage,
    enforce_video_duration_limit,
    format_duration
)
from decimal import Decimal


def test_format_duration():
    """Test duration formatting"""
    assert format_duration(90) == "1:30"
    assert format_duration(3665) == "1:01:05"
    assert format_duration(45) == "0:45"
    assert format_duration(3600) == "1:00:00"
    assert format_duration(0) == "0:00"
    assert format_duration(None) == "0:00"


def test_get_user_video_usage_empty(mock_dynamodb):
    """Test video usage with no videos"""
    from utils.config import photos_table
    
    usage = get_user_video_usage('user-123', photos_table)
    
    assert usage['total_minutes'] == 0
    assert usage['total_seconds'] == 0
    assert usage['video_count'] == 0


def test_get_user_video_usage_with_videos(mock_dynamodb):
    """Test video usage with multiple videos"""
    from utils.config import photos_table
    from unittest.mock import patch
    from decimal import Decimal
    
    user_id = 'user-video-test'
    
    # FIX: Conftest global mocking intercepts query, so mock the return directly
    mock_videos = [
        {
            'id': 'video-1',
            'user_id': user_id,
            'gallery_id': 'gallery-1',
            'type': 'video',
            'duration_seconds': Decimal('120'),  # 2 minutes
            's3_key': 'test/video1.mp4'
        },
        {
            'id': 'video-2',
            'user_id': user_id,
            'gallery_id': 'gallery-1',
            'type': 'video',
            'duration_seconds': Decimal('180'),  # 3 minutes
            's3_key': 'test/video2.mp4'
        }
    ]
    
    with patch.object(photos_table, 'query', return_value={'Items': mock_videos}):
        usage = get_user_video_usage(user_id, photos_table)
    
    assert usage['total_minutes'] == 5.0  # 2 + 3 minutes
    assert usage['total_seconds'] == 300.0
    assert usage['video_count'] == 2


def test_enforce_video_duration_limit_unlimited():
    """Test video limit enforcement with unlimited plan"""
    user = {'id': 'user-123'}
    features = {'video_minutes': -1, 'video_quality': '4k'}
    
    allowed, error = enforce_video_duration_limit(user, 100, features)
    
    assert allowed is True
    assert error is None


def test_enforce_video_duration_limit_no_video():
    """Test video limit enforcement when video not allowed"""
    user = {'id': 'user-123'}
    features = {'video_minutes': 0, 'video_quality': 'none'}
    
    allowed, error = enforce_video_duration_limit(user, 10, features)
    
    assert allowed is False
    assert 'not available' in error.lower()


def test_enforce_video_duration_limit_within_limit(mock_dynamodb):
    """Test video upload within limit"""
    from utils.config import photos_table
    
    user = {'id': 'user-limit-test'}
    features = {'video_minutes': 60, 'video_quality': 'hd'}  # 60 minute limit
    
    # Add existing video (30 minutes)
    photos_table.put_item(Item={
        'id': 'existing-video',
        'user_id': user['id'],
        'gallery_id': 'gallery-1',
        'type': 'video',
        'duration_seconds': Decimal('1800'),  # 30 minutes
        's3_key': 'test/existing.mp4'
    })
    
    # Try to add 20 more minutes (should be allowed)
    allowed, error = enforce_video_duration_limit(user, 20, features)
    
    assert allowed is True
    assert error is None


def test_enforce_video_duration_limit_exceeds_limit(mock_dynamodb):
    """Test video upload exceeding limit"""
    from utils.config import photos_table
    from unittest.mock import patch
    
    user = {'id': 'user-exceed-test'}
    features = {'video_minutes': 60, 'video_quality': 'hd'}  # 60 minute limit
    
    # FIX: Mock existing video (50 minutes) in query response
    mock_existing_video = [{
        'id': 'existing-video',
        'user_id': user['id'],
        'gallery_id': 'gallery-1',
        'type': 'video',
        'duration_seconds': Decimal('3000'),  # 50 minutes
        's3_key': 'test/existing.mp4'
    }]
    
    with patch.object(photos_table, 'query', return_value={'Items': mock_existing_video}):
        # Try to add 20 more minutes (should fail - would total 70)
        allowed, error = enforce_video_duration_limit(user, 20, features)
    
    assert allowed is False
    assert 'limit reached' in error.lower()
    assert '10.0 minutes remaining' in error

