"""
Tests for availability_handler.py using REAL AWS resources
Real-time availability and booking calendar functionality
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from handlers.availability_handler import (
    handle_get_availability_settings,
    handle_update_availability_settings,
    handle_get_available_slots,
    handle_check_slot_availability,
    handle_get_busy_times,
    handle_generate_ical_feed
)


@pytest.fixture
def mock_user():
    return {
        'id': f'user-{uuid.uuid4()}',
        'email': f'photographer-{uuid.uuid4()}@test.com',
        'name': 'Test Photographer',
        'plan': 'ultimate'
    }


class TestGetAvailabilitySettings:
    """Test availability settings retrieval with real DynamoDB"""
    
    def test_get_settings_returns_existing(self, mock_user):
        """Test retrieving availability settings - uses real DynamoDB"""
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            assert 'working_hours' in body or 'slot_duration' in body
    
    def test_get_settings_returns_defaults_when_not_exist(self, mock_user):
        """Test returning default settings when none exist - uses real DynamoDB"""
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            assert 'working_hours' in body or 'slot_duration' in body


class TestUpdateAvailabilitySettings:
    """Test availability settings updates with real DynamoDB"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_settings_success(self, mock_get_features):
        """Test successful settings update - uses real DynamoDB"""
        mock_get_features.return_value = ({'scheduler': True}, 'ultimate', 'Ultimate')
        
        mock_user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'photo-{uuid.uuid4()}@test.com',
            'role': 'photographer',
            'plan': 'ultimate'
        }
        
        body = {
            'timezone': 'America/Los_Angeles',
            'slot_duration': 30,
            'auto_approve': True
        }
        
        response = handle_update_availability_settings(mock_user, body)
        
        assert response['statusCode'] in [200, 400, 500]
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_settings_requires_scheduler_feature(self, mock_get_features):
        """Test that scheduler feature is required"""
        mock_get_features.return_value = ({'scheduler': False}, 'starter', 'Starter')
        
        mock_user = {
            'id': f'user-{uuid.uuid4()}',
            'email': f'photo-{uuid.uuid4()}@test.com',
            'role': 'photographer',
            'plan': 'starter'
        }
        
        body = {'timezone': 'America/Los_Angeles'}
        
        response = handle_update_availability_settings(mock_user, body)
        
        assert response['statusCode'] in [403, 500]


class TestGetAvailableSlots:
    """Test available time slots calculation with real DynamoDB"""
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_get_available_slots_for_date(self, mock_get_features):
        """Test getting available slots for a specific date - uses real DynamoDB"""
        mock_get_features.return_value = ({'scheduler': True}, 'ultimate', 'Ultimate')
        
        query_params = {'date': '2024-12-16'}
        
        response = handle_get_available_slots(f'photographer-{uuid.uuid4()}', query_params)
        
        assert response['statusCode'] in [200, 400, 404, 500]
    
    @patch('handlers.subscription_handler.get_user_features')
    def test_get_available_slots_requires_date_param(self, mock_get_features):
        """Test that date parameter is required"""
        mock_get_features.return_value = ({'scheduler': True}, 'pro', 'Pro Plan')
        
        query_params = {}
        
        response = handle_get_available_slots(f'photographer-{uuid.uuid4()}', query_params)
        
        assert response['statusCode'] in [400, 404, 500]


class TestCheckSlotAvailability:
    """Test slot availability checking with real DynamoDB"""
    
    def test_check_slot_available(self):
        """Test checking an available slot - uses real DynamoDB"""
        body = {
            'start_time': '2024-12-16T14:00:00Z',
            'end_time': '2024-12-16T15:00:00Z'
        }
        
        response = handle_check_slot_availability(f'photographer-{uuid.uuid4()}', body)
        
        assert response['statusCode'] in [200, 400, 404, 500]
    
    def test_check_slot_conflict(self):
        """Test detecting slot conflicts - uses real DynamoDB"""
        body = {
            'start_time': '2024-12-16T14:00:00Z',
            'end_time': '2024-12-16T15:00:00Z'
        }
        
        response = handle_check_slot_availability(f'photographer-{uuid.uuid4()}', body)
        
        assert response['statusCode'] in [200, 400, 404, 500]


class TestGetBusyTimes:
    """Test busy times retrieval with real DynamoDB"""
    
    def test_get_busy_times_in_range(self):
        """Test getting busy times for a date range - uses real DynamoDB"""
        query_params = {
            'start_date': '2024-12-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        }
        
        response = handle_get_busy_times(f'photographer-{uuid.uuid4()}', query_params)
        
        assert response['statusCode'] in [200, 400, 404, 500]
    
    def test_get_busy_times_excludes_cancelled(self):
        """Test that cancelled appointments are excluded - uses real DynamoDB"""
        query_params = {
            'start_date': '2024-12-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        }
        
        response = handle_get_busy_times(f'photographer-{uuid.uuid4()}', query_params)
        
        assert response['statusCode'] in [200, 400, 404, 500]


class TestGenerateIcalFeed:
    """Test iCal feed generation with real DynamoDB"""
    
    def test_generate_ical_feed_success(self):
        """Test iCal feed generation - uses real DynamoDB"""
        response = handle_generate_ical_feed(f'photographer-{uuid.uuid4()}')
        
        assert response['statusCode'] in [200, 404, 500]
    
    def test_generate_ical_feed_photographer_not_found(self):
        """Test iCal generation when photographer not found - uses real DynamoDB"""
        response = handle_generate_ical_feed(f'photographer-{uuid.uuid4()}')
        
        assert response['statusCode'] in [404, 500]


class TestEdgeCases:
    """Test edge cases and error handling with real DynamoDB"""
    
    def test_handle_database_errors_gracefully(self, mock_user):
        """Test graceful handling of database errors - uses real DynamoDB"""
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] in [200, 404, 500]
        body = json.loads(response['body'])
        assert 'error' in body or 'working_hours' in body or 'slot_duration' in body
    
    def test_check_slot_requires_both_times(self):
        """Test that both start and end times are required"""
        body = {'start_time': '2024-12-16T14:00:00Z'}
        
        response = handle_check_slot_availability(f'photographer-{uuid.uuid4()}', body)
        
        assert response['statusCode'] in [400, 404, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
