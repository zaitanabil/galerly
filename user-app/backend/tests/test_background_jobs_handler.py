import json
import pytest
from unittest.mock import MagicMock, patch, call
from handlers.background_jobs_handler import (
    create_background_job,
    update_job_status,
    delete_s3_objects_by_prefix,
    process_account_deletion,
    handle_get_job_status,
    handle_process_background_job
)


@pytest.fixture
def mock_dynamodb_tables():
    """Mock all DynamoDB tables"""
    with patch('handlers.background_jobs_handler.background_jobs_table') as mock_jobs, \
         patch('handlers.background_jobs_handler.users_table') as mock_users, \
         patch('handlers.background_jobs_handler.galleries_table') as mock_galleries, \
         patch('handlers.background_jobs_handler.photos_table') as mock_photos, \
         patch('handlers.background_jobs_handler.sessions_table') as mock_sessions, \
         patch('handlers.background_jobs_handler.contracts_table') as mock_contracts, \
         patch('handlers.background_jobs_handler.invoices_table') as mock_invoices, \
         patch('handlers.background_jobs_handler.appointments_table') as mock_appointments, \
         patch('handlers.background_jobs_handler.video_analytics_table') as mock_video, \
         patch('handlers.background_jobs_handler.visitor_tracking_table') as mock_visitor:
        
        yield {
            'jobs': mock_jobs,
            'users': mock_users,
            'galleries': mock_galleries,
            'photos': mock_photos,
            'sessions': mock_sessions,
            'contracts': mock_contracts,
            'invoices': mock_invoices,
            'appointments': mock_appointments,
            'video': mock_video,
            'visitor': mock_visitor
        }


@pytest.fixture
def mock_s3():
    """Mock S3 client"""
    with patch('handlers.background_jobs_handler.s3_client') as mock_client:
        yield mock_client


def test_create_background_job(mock_dynamodb_tables):
    """Test creating a background job"""
    mock_dynamodb_tables['jobs'].put_item.return_value = {}
    
    job_id = create_background_job(
        job_type='account_deletion',
        user_id='user123',
        user_email='test@example.com',
        metadata={'test': 'data'}
    )
    
    assert job_id is not None
    assert len(job_id) == 36  # UUID format
    mock_dynamodb_tables['jobs'].put_item.assert_called_once()
    
    # Verify the item structure
    call_args = mock_dynamodb_tables['jobs'].put_item.call_args
    item = call_args[1]['Item']
    assert item['job_type'] == 'account_deletion'
    assert item['user_id'] == 'user123'
    assert item['user_email'] == 'test@example.com'
    assert item['status'] == 'pending'


def test_update_job_status(mock_dynamodb_tables):
    """Test updating job status"""
    mock_dynamodb_tables['jobs'].update_item.return_value = {}
    
    update_job_status('job123', 'completed', progress=100)
    
    mock_dynamodb_tables['jobs'].update_item.assert_called_once()
    call_args = mock_dynamodb_tables['jobs'].update_item.call_args[1]
    assert call_args['Key']['job_id'] == 'job123'
    assert ':status' in call_args['ExpressionAttributeValues']
    assert call_args['ExpressionAttributeValues'][':status'] == 'completed'


def test_delete_s3_objects_by_prefix(mock_s3):
    """Test S3 object deletion by prefix"""
    # Mock paginator
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    
    # Mock pages with objects
    mock_paginator.paginate.return_value = [
        {
            'Contents': [
                {'Key': 'galleries/g1/photo1.jpg'},
                {'Key': 'galleries/g1/photo2.jpg'}
            ]
        }
    ]
    
    deleted_count = delete_s3_objects_by_prefix('galleries/g1/')
    
    assert deleted_count == 2
    mock_s3.delete_objects.assert_called_once()


def test_process_account_deletion_success(mock_dynamodb_tables, mock_s3):
    """Test successful account deletion processing"""
    # Mock gallery query
    mock_dynamodb_tables['galleries'].query.return_value = {
        'Items': [
            {'id': 'gallery1', 'photographer_id': 'user123'},
            {'id': 'gallery2', 'photographer_id': 'user123'}
        ]
    }
    
    # Mock photos query
    mock_dynamodb_tables['photos'].query.return_value = {
        'Items': [
            {'id': 'photo1', 'gallery_id': 'gallery1'},
            {'id': 'photo2', 'gallery_id': 'gallery1'}
        ]
    }
    
    # Mock other scans
    mock_dynamodb_tables['contracts'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['invoices'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['appointments'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['video'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['visitor'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['sessions'].scan.return_value = {'Items': []}
    
    # Mock S3 operations
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = []
    
    # Mock update_item for job status updates
    mock_dynamodb_tables['jobs'].update_item.return_value = {}
    
    success = process_account_deletion('job123', 'user123', 'test@example.com')
    
    assert success is True
    # Verify user was deleted
    mock_dynamodb_tables['users'].delete_item.assert_called_once_with(
        Key={'email': 'test@example.com'}
    )
    # Verify galleries were deleted
    assert mock_dynamodb_tables['galleries'].delete_item.call_count == 2


def test_process_account_deletion_failure(mock_dynamodb_tables, mock_s3):
    """Test account deletion processing with error"""
    # Simulate error during gallery query
    mock_dynamodb_tables['galleries'].query.side_effect = Exception("DynamoDB error")
    mock_dynamodb_tables['jobs'].update_item.return_value = {}
    
    success = process_account_deletion('job123', 'user123', 'test@example.com')
    
    assert success is False
    # Verify job status was updated to failed
    update_calls = mock_dynamodb_tables['jobs'].update_item.call_args_list
    assert any(':status' in str(call) and 'failed' in str(call) for call in update_calls)


def test_handle_get_job_status_success(mock_dynamodb_tables):
    """Test getting job status"""
    mock_user = {'email': 'test@example.com', 'id': 'user123'}
    
    mock_dynamodb_tables['jobs'].get_item.return_value = {
        'Item': {
            'job_id': 'job123',
            'job_type': 'account_deletion',
            'user_email': 'test@example.com',
            'status': 'completed',
            'progress': 100
        }
    }
    
    response = handle_get_job_status(mock_user, 'job123')
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['job']['job_id'] == 'job123'
    assert body['job']['status'] == 'completed'


def test_handle_get_job_status_unauthorized(mock_dynamodb_tables):
    """Test getting job status for another user's job"""
    mock_user = {'email': 'test@example.com', 'id': 'user123'}
    
    mock_dynamodb_tables['jobs'].get_item.return_value = {
        'Item': {
            'job_id': 'job123',
            'user_email': 'other@example.com',  # Different user
            'status': 'pending'
        }
    }
    
    response = handle_get_job_status(mock_user, 'job123')
    
    assert response['statusCode'] == 403
    body = json.loads(response['body'])
    assert 'Unauthorized' in body['error']


def test_handle_process_background_job(mock_dynamodb_tables, mock_s3):
    """Test processing a background job via handler"""
    mock_dynamodb_tables['jobs'].get_item.return_value = {
        'Item': {
            'job_id': 'job123',
            'job_type': 'account_deletion',
            'user_id': 'user123',
            'user_email': 'test@example.com',
            'status': 'pending'
        }
    }
    
    # Mock all required operations for account deletion
    mock_dynamodb_tables['galleries'].query.return_value = {'Items': []}
    mock_dynamodb_tables['photos'].query.return_value = {'Items': []}
    mock_dynamodb_tables['contracts'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['invoices'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['appointments'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['video'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['visitor'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['sessions'].scan.return_value = {'Items': []}
    mock_dynamodb_tables['jobs'].update_item.return_value = {}
    
    mock_paginator = MagicMock()
    mock_s3.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = []
    
    response = handle_process_background_job('job123')
    
    assert response['statusCode'] == 200

