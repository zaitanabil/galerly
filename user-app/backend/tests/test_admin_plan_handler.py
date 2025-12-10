"""
Tests for Admin Plan Management Handler
Tests administrative functions for managing user plans and features
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.admin_plan_handler import (
    handle_grant_feature,
    handle_revoke_feature,
    handle_list_user_overrides,
    handle_upgrade_user_plan,
    handle_get_plan_violations,
    handle_get_user_violations
)


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user"""
    return {
        'id': 'admin-123',
        'email': 'admin@galerly.com',
        'role': 'admin'
    }


@pytest.fixture
def mock_regular_user():
    """Create a mock regular user"""
    return {
        'id': 'user-456',
        'email': 'user@galerly.com',
        'role': 'photographer'
    }


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables"""
    with patch('handlers.admin_plan_handler.users_table') as users_table, \
         patch('handlers.admin_plan_handler.user_features_table') as features_table:
        
        yield {
            'users_table': users_table,
            'user_features_table': features_table
        }


class TestAdminAuthentication:
    """Test admin role verification"""
    
    def test_grant_feature_requires_admin(self, mock_regular_user, mock_dynamodb_tables):
        """Test that non-admin users cannot grant features"""
        body = {
            'user_id': 'user-789',
            'feature_id': 'client_invoicing',
            'reason': 'Trial'
        }
        
        response = handle_grant_feature(mock_regular_user, body)
        
        assert response['statusCode'] == 403
        assert 'admin' in response['body'].lower()
    
    def test_revoke_feature_requires_admin(self, mock_regular_user, mock_dynamodb_tables):
        """Test that non-admin users cannot revoke features"""
        response = handle_revoke_feature(mock_regular_user, 'user-789', 'client_invoicing')
        
        assert response['statusCode'] == 403
        assert 'admin' in response['body'].lower()


class TestFeatureManagement:
    """Test feature grant and revoke operations"""
    
    def test_grant_feature_success(self, mock_admin_user, mock_dynamodb_tables):
        """Test successful feature grant"""
        body = {
            'user_id': 'user-789',
            'feature_id': 'client_invoicing',
            'reason': 'Trial access',
            'expires_at': '2024-12-31T23:59:59Z'
        }
        
        mock_dynamodb_tables['users_table'].get_item.return_value = {
            'Item': {
                'id': 'user-789',
                'email': 'user@test.com',
                'subscription_id': 'free'
            }
        }
        
        mock_dynamodb_tables['user_features_table'].put_item.return_value = {}
        
        response = handle_grant_feature(mock_admin_user, body)
        
        assert response['statusCode'] == 200
        body_data = eval(response['body'])
        assert 'message' in body_data
        assert 'granted' in body_data['message'].lower()
    
    def test_grant_feature_validates_required_fields(self, mock_admin_user, mock_dynamodb_tables):
        """Test that required fields are validated"""
        body = {
            'user_id': 'user-789'
            # Missing feature_id
        }
        
        response = handle_grant_feature(mock_admin_user, body)
        
        assert response['statusCode'] == 400
    
    def test_revoke_feature_success(self, mock_admin_user, mock_dynamodb_tables):
        """Test successful feature revocation"""
        # Mock query to return override that will be deleted
        mock_dynamodb_tables['user_features_table'].query.return_value = {
            'Items': [
                {
                    'user_id': 'user-789',
                    'id': 'override-123',
                    'feature_id': 'client_invoicing'
                }
            ]
        }
        mock_dynamodb_tables['user_features_table'].delete_item.return_value = {}
        
        response = handle_revoke_feature(mock_admin_user, 'user-789', 'client_invoicing')
        
        assert response['statusCode'] == 200
        body_data = eval(response['body'])
        assert 'revoked' in body_data['message'].lower()
    
    def test_list_user_overrides(self, mock_admin_user, mock_dynamodb_tables):
        """Test listing user feature overrides"""
        mock_dynamodb_tables['user_features_table'].query.return_value = {
            'Items': [
                {
                    'user_id': 'user-789',
                    'feature_id': 'client_invoicing',
                    'granted_by': 'admin-123',
                    'reason': 'Trial',
                    'granted_at': '2024-01-01T00:00:00Z'
                }
            ]
        }
        
        response = handle_list_user_overrides(mock_admin_user, 'user-789')
        
        assert response['statusCode'] == 200
        body_data = eval(response['body'])
        assert 'overrides' in body_data
        assert len(body_data['overrides']) == 1


class TestPlanManagement:
    """Test plan upgrade operations"""
    
    def test_upgrade_user_plan_success(self, mock_admin_user, mock_dynamodb_tables):
        """Test successful plan upgrade"""
        body = {
            'user_id': 'user-789',
            'plan': 'starter',
            'reason': 'Customer support upgrade'
        }
        
        mock_dynamodb_tables['users_table'].scan.return_value = {  # Changed from get_item to scan
            'Items': [{
                'id': 'user-789',
                'email': 'user@test.com',
                'subscription_id': 'free',
                'plan': 'free'
            }]
        }
        
        mock_dynamodb_tables['users_table'].update_item.return_value = {}
        
        response = handle_upgrade_user_plan(mock_admin_user, body)
        
        assert response['statusCode'] == 200
        body_data = eval(response['body'])
        assert 'message' in body_data
    
    def test_upgrade_validates_plan_exists(self, mock_admin_user, mock_dynamodb_tables):
        """Test that invalid plans are rejected"""
        body = {
            'user_id': 'user-789',
            'plan': 'invalid_plan',  # Changed from new_plan to plan
            'reason': 'Test'
        }
        
        mock_dynamodb_tables['users_table'].scan.return_value = {  # Changed from get_item to scan
            'Items': [{
                'id': 'user-789',
                'email': 'user@test.com'
            }]
        }
        
        response = handle_upgrade_user_plan(mock_admin_user, body)
        
        assert response['statusCode'] == 400


class TestViolationMonitoring:
    """Test violation monitoring endpoints"""
    
    def test_get_platform_violations(self, mock_admin_user, mock_dynamodb_tables):
        """Test retrieving platform-wide violations"""
        with patch('utils.plan_monitoring.get_violation_summary') as mock_summary:
            mock_summary.return_value = {
                'total_violations': 2,
                'violations_by_type': {
                    'storage_exceeded': 1,
                    'feature_not_available': 1
                },
                'violations': [
                    {
                        'id': 'violation-1',
                        'user_id': 'user-123',
                        'violation_type': 'storage_exceeded',
                        'timestamp': '2024-01-01T00:00:00Z'
                    },
                    {
                        'id': 'violation-2',
                        'user_id': 'user-456',
                        'violation_type': 'feature_not_available',
                        'timestamp': '2024-01-02T00:00:00Z'
                    }
                ]
            }
            
            response = handle_get_plan_violations(mock_admin_user)
            
            assert response['statusCode'] == 200
            body_data = eval(response['body'])
            assert 'total_violations' in body_data
            assert body_data['total_violations'] == 2
    
    def test_get_user_violations(self, mock_admin_user, mock_dynamodb_tables):
        """Test retrieving user-specific violations"""
        with patch('utils.plan_monitoring.get_user_violations') as mock_history:
            mock_history.return_value = {
                'user_id': 'user-789',
                'total_violations': 1,
                'violations': [
                    {
                        'id': 'violation-1',
                        'user_id': 'user-789',
                        'violation_type': 'storage_exceeded',
                        'timestamp': '2024-01-01T00:00:00Z'
                    }
                ]
            }
            
            response = handle_get_user_violations(mock_admin_user, 'user-789')
            
            assert response['statusCode'] == 200
            body_data = eval(response['body'])
            assert 'user_id' in body_data
            assert body_data['user_id'] == 'user-789'
    
    def test_violations_require_admin(self, mock_regular_user, mock_dynamodb_tables):
        """Test that violation endpoints require admin role"""
        response = handle_get_plan_violations(mock_regular_user)
        
        assert response['statusCode'] == 403


class TestErrorHandling:
    """Test error handling in admin operations"""
    
    def test_grant_feature_handles_db_errors(self, mock_admin_user, mock_dynamodb_tables):
        """Test that database errors are handled gracefully"""
        body = {
            'user_id': 'user-789',
            'feature_id': 'client_invoicing',
            'reason': 'Trial'
        }
        
        mock_dynamodb_tables['users_table'].scan.side_effect = Exception("Database error")
        
        response = handle_grant_feature(mock_admin_user, body)
        
        assert response['statusCode'] == 500
    
    def test_user_not_found(self, mock_admin_user, mock_dynamodb_tables):
        """Test handling when target user doesn't exist"""
        body = {
            'user_id': 'nonexistent-user',
            'feature_id': 'client_invoicing',
            'reason': 'Trial'
        }
        
        mock_dynamodb_tables['users_table'].scan.return_value = {'Items': []}  # Empty list
        
        response = handle_grant_feature(mock_admin_user, body)
        
        assert response['statusCode'] == 404


@pytest.mark.integration
class TestAdminWorkflow:
    """Integration tests for complete admin workflows"""
    
    def test_complete_feature_grant_workflow(self, mock_admin_user, mock_dynamodb_tables):
        """Test complete workflow: grant feature, verify, then revoke"""
        # Step 1: Grant feature
        grant_body = {
            'user_id': 'user-789',
            'feature_id': 'client_invoicing',
            'reason': 'Trial access'
        }
        
        mock_dynamodb_tables['users_table'].scan.return_value = {  # Changed from get_item to scan
            'Items': [{'id': 'user-789', 'email': 'user@test.com'}]
        }
        mock_dynamodb_tables['user_features_table'].put_item.return_value = {}
        
        grant_response = handle_grant_feature(mock_admin_user, grant_body)
        assert grant_response['statusCode'] == 200
        
        # Step 2: List overrides
        mock_dynamodb_tables['user_features_table'].query.return_value = {
            'Items': [
                {
                    'user_id': 'user-789',
                    'id': 'override-123',  # Add id field
                    'feature_id': 'client_invoicing',
                    'granted_by': 'admin-123'
                }
            ]
        }
        
        list_response = handle_list_user_overrides(mock_admin_user, 'user-789')
        assert list_response['statusCode'] == 200
        
        # Step 3: Revoke feature - reuse the same query mock with id field
        mock_dynamodb_tables['user_features_table'].delete_item.return_value = {}
        
        revoke_response = handle_revoke_feature(mock_admin_user, 'user-789', 'client_invoicing')
        assert revoke_response['statusCode'] == 200
