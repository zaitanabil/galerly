import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_contract_dependencies():
    with patch('handlers.contract_handler.contracts_table') as mock_table, \
         patch('handlers.contract_handler.s3_client') as mock_s3, \
         patch('handlers.contract_handler.send_email') as mock_email:
        yield {
            'table': mock_table,
            's3': mock_s3,
            'email': mock_email
        }

class TestContractHandler:
    def test_create_contract(self, sample_user, mock_contract_dependencies):
        from handlers.contract_handler import handle_create_contract
        
        body = {
            'client_name': 'Client A',
            'client_email': 'client@example.com',
            'title': 'Wedding Contract',
            'content': 'Terms and conditions...'
        }
        
        result = handle_create_contract(sample_user, body)
        
        assert result['statusCode'] == 201
        response = json.loads(result['body'])
        assert response['status'] == 'draft'
        mock_contract_dependencies['table'].put_item.assert_called_once()

    def test_sign_contract(self, mock_contract_dependencies):
        from handlers.contract_handler import handle_sign_contract
        
        contract_id = 'cont123'
        contract = {
            'id': contract_id,
            'status': 'sent',
            'user_id': 'photographer1',
            'client_email': 'client@example.com'
        }
        
        # Mock get contract
        mock_contract_dependencies['table'].get_item.return_value = {'Item': contract}
        
        body = {
            'signature_data': 'base64sigdata'
        }
        
        result = handle_sign_contract(contract_id, body, '127.0.0.1')
        
        assert result['statusCode'] == 200
        # Verify S3 upload
        mock_contract_dependencies['s3'].put_object.assert_called_once()
        # Verify status update
        mock_contract_dependencies['table'].put_item.assert_called()
        # Verify email notifications (one to client, one to photographer - simplified check)
        assert mock_contract_dependencies['email'].call_count >= 1

