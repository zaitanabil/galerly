"""
Tests for availability_handler.py
Real-time availability and booking calendar functionality
"""
import pytest
import os
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
        'id': 'test-user-123',
        'email': 'photographer@test.com',
        'name': 'Test Photographer',
        'plan': 'ultimate'
    }


@pytest.fixture
def mock_availability_settings():
    return {
        'user_id': 'test-user-123',
        'timezone': 'America/New_York',
        'working_hours': {
            'monday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
            'tuesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
            'wednesday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
            'thursday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
            'friday': {'enabled': True, 'start': '09:00', 'end': '17:00'},
            'saturday': {'enabled': False, 'start': '10:00', 'end': '15:00'},
            'sunday': {'enabled': False, 'start': '10:00', 'end': '15:00'}
        },
        'slot_duration': 60,
        'buffer_time': 15,
        'booking_window': {
            'min_hours_ahead': 24,
            'max_days_ahead': 60
        },
        'auto_approve': False
    }


class TestGetAvailabilitySettings:
    """Test availability settings retrieval"""
    
    @patch('handlers.availability_handler.availability_settings_table')
    def test_get_settings_returns_existing(self, mock_table, mock_user, mock_availability_settings):
        """Test retrieving existing availability settings"""
        mock_table.get_item.return_value = {'Item': mock_availability_settings}
        
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['user_id'] == mock_user['id']
        assert body['timezone'] == 'America/New_York'
        assert body['slot_duration'] == 60
    
    @patch('handlers.availability_handler.availability_settings_table')
    def test_get_settings_returns_defaults_when_not_exist(self, mock_table, mock_user):
        """Test returning default settings when none exist"""
        mock_table.get_item.return_value = {}
        
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'working_hours' in body
        assert 'slot_duration' in body
        assert body['slot_duration'] == 60


class TestUpdateAvailabilitySettings:
    """Test availability settings updates"""
    
    @patch('handlers.availability_handler.availability_settings_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_settings_success(self, mock_get_features, mock_table):
        """Test successful settings update"""
        # Mock get_user_features to allow access
        mock_get_features.return_value = (
            {'scheduler': True},  # features
            'ultimate',  # plan_id
            'Ultimate'  # plan_name
        )
        
        # Mock table
        mock_table.put_item.return_value = {}
        
        # Mock user with all required fields
        mock_user = {
            'id': 'test-user-123',
            'email': 'photographer@test.com',
            'role': 'photographer',
            'plan': 'ultimate'
        }
        
        body = {
            'timezone': 'America/Los_Angeles',
            'slot_duration': 30,
            'auto_approve': True
        }
        
        response = handle_update_availability_settings(mock_user, body)
        
        assert response['statusCode'] == 200
        mock_table.put_item.assert_called_once()
    
    @patch('handlers.availability_handler.availability_settings_table')
    @patch('handlers.subscription_handler.get_user_features')
    def test_update_settings_requires_scheduler_feature(self, mock_get_features, mock_table):
        """Test that scheduler feature is required"""
        # Mock get_user_features to deny access
        mock_get_features.return_value = (
            {'scheduler': False},  # No scheduler feature
            'starter',  # plan_id
            'Starter'  # plan_name
        )
        
        # Mock user
        mock_user = {
            'id': 'test-user-123',
            'email': 'photographer@test.com',
            'role': 'photographer',
            'plan': 'starter'
        }
        
        body = {'timezone': 'America/Los_Angeles'}
        
        response = handle_update_availability_settings(mock_user, body)
        
        # Decorator should block this with 403
        assert response['statusCode'] == 403


class TestGetAvailableSlots:
    """Test available time slots calculation"""
    
    @patch('handlers.availability_handler.appointments_table')
    @patch('handlers.availability_handler.dynamodb')
    @patch('handlers.availability_handler.users_table')
    def test_get_available_slots_for_date(self, mock_users, mock_dynamodb, mock_appointments):
        """Test getting available slots for a specific date"""
        mock_users.query.return_value = {'Items': [{'id': 'photographer-123', 'plan': 'ultimate'}]}
        
        # Mock settings table
        mock_settings = MagicMock()
        mock_dynamodb.Table.return_value = mock_settings
        mock_settings.get_item.return_value = {
            'Item': {
                'working_hours': {
                    'monday': {'enabled': True, 'start': '09:00', 'end': '12:00'}
                },
                'slot_duration': 60,
                'buffer_time': 0
            }
        }
        mock_appointments.query.return_value = {'Items': []}
        
        query_params = {'date': '2024-12-16'}  # A Monday
        
        response = handle_get_available_slots('photographer-123', query_params)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'available_slots' in body
        assert isinstance(body['available_slots'], list)
    
    @patch('handlers.availability_handler.users_table')
    def test_get_available_slots_requires_date_param(self, mock_users):
        """Test that date parameter is required"""
        mock_users.query.return_value = {'Items': [{'id': 'photographer-123'}]}
        
        query_params = {}
        
        response = handle_get_available_slots('photographer-123', query_params)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'date parameter required' in body['error']


class TestCheckSlotAvailability:
    """Test slot availability checking"""
    
    @patch('handlers.availability_handler.appointments_table')
    def test_check_slot_available(self, mock_table):
        """Test checking an available slot"""
        mock_table.query.return_value = {'Items': []}
        
        body = {
            'start_time': '2024-12-16T14:00:00Z',
            'end_time': '2024-12-16T15:00:00Z'
        }
        
        response = handle_check_slot_availability('photographer-123', body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['available'] is True
        assert body_data['conflict'] is False
    
    @patch('handlers.availability_handler.appointments_table')
    def test_check_slot_conflict(self, mock_table):
        """Test detecting slot conflicts"""
        mock_table.query.return_value = {
            'Items': [{
                'id': 'appt-123',
                'start_time': '2024-12-16T14:30:00Z',
                'end_time': '2024-12-16T15:30:00Z',
                'status': 'confirmed'
            }]
        }
        
        body = {
            'start_time': '2024-12-16T14:00:00Z',
            'end_time': '2024-12-16T15:00:00Z'
        }
        
        response = handle_check_slot_availability('photographer-123', body)
        
        assert response['statusCode'] == 200
        body_data = json.loads(response['body'])
        assert body_data['available'] is False
        assert body_data['conflict'] is True


class TestGetBusyTimes:
    """Test busy times retrieval"""
    
    @patch('handlers.availability_handler.appointments_table')
    def test_get_busy_times_in_range(self, mock_table):
        """Test getting busy times for a date range"""
        mock_table.query.return_value = {
            'Items': [
                {
                    'id': 'appt-1',
                    'start_time': '2024-12-16T10:00:00Z',
                    'end_time': '2024-12-16T11:00:00Z',
                    'service_type': 'Portrait Session',
                    'status': 'confirmed'
                }
            ]
        }
        
        query_params = {
            'start_date': '2024-12-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        }
        
        response = handle_get_busy_times('photographer-123', query_params)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'busy_times' in body
        assert len(body['busy_times']) == 1
        assert body['count'] == 1
    
    @patch('handlers.availability_handler.appointments_table')
    def test_get_busy_times_excludes_cancelled(self, mock_table):
        """Test that cancelled appointments are excluded"""
        mock_table.query.return_value = {
            'Items': [
                {
                    'id': 'appt-1',
                    'start_time': '2024-12-16T10:00:00Z',
                    'end_time': '2024-12-16T11:00:00Z',
                    'status': 'cancelled'
                }
            ]
        }
        
        query_params = {
            'start_date': '2024-12-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        }
        
        response = handle_get_busy_times('photographer-123', query_params)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['busy_times']) == 0


class TestGenerateIcalFeed:
    """Test iCal feed generation"""
    
    @patch('handlers.availability_handler.appointments_table')
    @patch('handlers.availability_handler.users_table')
    def test_generate_ical_feed_success(self, mock_users, mock_appointments):
        """Test successful iCal feed generation"""
        mock_users.query.return_value = {
            'Items': [{'id': 'photographer-123', 'name': 'Test Photographer'}]
        }
        mock_appointments.query.return_value = {
            'Items': [
                {
                    'id': 'appt-1',
                    'start_time': '2024-12-16T10:00:00Z',
                    'end_time': '2024-12-16T11:00:00Z',
                    'service_type': 'Portrait Session',
                    'client_name': 'John Doe',
                    'client_email': 'john@example.com',
                    'status': 'confirmed',
                    'created_at': '2024-12-01T10:00:00Z'
                }
            ]
        }
        
        response = handle_generate_ical_feed('photographer-123')
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/calendar; charset=utf-8'
        assert 'BEGIN:VCALENDAR' in response['body']
        assert 'BEGIN:VEVENT' in response['body']
        assert 'Portrait Session' in response['body']
    
    @patch('handlers.availability_handler.users_table')
    def test_generate_ical_feed_photographer_not_found(self, mock_users):
        """Test iCal generation when photographer not found"""
        mock_users.query.return_value = {'Items': []}
        
        response = handle_generate_ical_feed('photographer-123')
        
        assert response['statusCode'] == 404


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.availability_handler.availability_settings_table')
    def test_handle_database_errors_gracefully(self, mock_table, mock_user):
        """Test graceful handling of database errors"""
        mock_table.get_item.side_effect = Exception('Database error')
        
        response = handle_get_availability_settings(mock_user)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_check_slot_requires_both_times(self):
        """Test that both start and end times are required"""
        body = {'start_time': '2024-12-16T14:00:00Z'}
        
        response = handle_check_slot_availability('photographer-123', body)
        
        assert response['statusCode'] == 400
        body_data = json.loads(response['body'])
        assert 'required' in body_data['error'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
