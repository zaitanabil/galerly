import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime

@pytest.fixture
def mock_appointment_dependencies():
    with patch('handlers.appointment_handler.appointments_table') as mock_table, \
         patch('handlers.appointment_handler.send_email') as mock_email:
        yield {
            'table': mock_table,
            'email': mock_email
        }

class TestAppointmentHandler:
    def test_create_appointment_success(self, sample_user, mock_appointment_dependencies):
        from handlers.appointment_handler import handle_create_appointment
        
        # Mock conflict check (query returns empty)
        mock_appointment_dependencies['table'].query.return_value = {'Items': []}
        
        body = {
            'client_name': 'John Doe',
            'client_email': 'john@example.com',
            'start_time': '2023-12-25T10:00:00Z',
            'duration_minutes': 60,
            'service_type': 'Portrait'
        }
        
        result = handle_create_appointment(sample_user, body)
        
        assert result['statusCode'] == 201
        response = json.loads(result['body'])
        assert response['client_name'] == 'John Doe'
        mock_appointment_dependencies['table'].put_item.assert_called_once()
        mock_appointment_dependencies['email'].assert_called()

    def test_list_appointments(self, sample_user, mock_appointment_dependencies):
        from handlers.appointment_handler import handle_list_appointments
        
        mock_appointment_dependencies['table'].query.return_value = {
            'Items': [{'id': 'app1', 'user_id': sample_user['id'], 'client_name': 'Jane'}]
        }
        
        result = handle_list_appointments(sample_user)
        
        assert result['statusCode'] == 200
        response = json.loads(result['body'])
        assert len(response['appointments']) == 1

