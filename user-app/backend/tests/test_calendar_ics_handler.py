"""
Tests for Calendar ICS Handler
"""
import pytest
from unittest.mock import patch, MagicMock
from handlers.calendar_ics_handler import (
    handle_export_appointment_ics,
    handle_export_calendar_feed,
    handle_generate_calendar_token
)


class TestCalendarICSHandler:
    """Test calendar ICS export functionality"""
    
    @patch('handlers.calendar_ics_handler.dynamodb')
    def test_export_appointment_ics(self, mock_dynamodb):
        """Test exporting single appointment as ICS"""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'appt1',
                'title': 'Photo Session',
                'start_time': '2025-01-15T10:00:00Z',
                'end_time': '2025-01-15T12:00:00Z'
            }
        }
        
        event = {'pathParameters': {'appointment_id': 'appt1'}}
        response = handle_export_appointment_ics(event)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/calendar'
    
    @patch('handlers.calendar_ics_handler.dynamodb')
    def test_export_calendar_feed(self, mock_dynamodb):
        """Test exporting calendar feed"""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {'id': 'photo1', 'calendar_feed_token': 'token123'}
        }
        mock_table.query.return_value = {'Items': []}
        
        event = {
            'queryStringParameters': {
                'photographer_id': 'photo1',
                'token': 'token123'
            }
        }
        response = handle_export_calendar_feed(event)
        
        assert response['statusCode'] == 200
        assert 'text/calendar' in response['headers']['Content-Type']
    
    @patch('handlers.calendar_ics_handler.get_user_from_token')
    @patch('handlers.calendar_ics_handler.dynamodb')
    def test_generate_calendar_token(self, mock_dynamodb, mock_get_user):
        """Test generating calendar token"""
        mock_get_user.return_value = {'user_id': 'photo1', 'role': 'photographer'}
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        event = {}
        response = handle_generate_calendar_token(event)
        
        assert response['statusCode'] == 200
        assert 'token' in response['body']
        assert 'feed_url' in response['body']
