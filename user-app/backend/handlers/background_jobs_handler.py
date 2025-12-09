"""
Background job processing for long-running tasks
Handles account deletion, bulk operations, etc.
"""
import json
from datetime import datetime
from decimal import Decimal
from utils.config import (
    s3_client, S3_BUCKET,
    users_table, galleries_table, photos_table, sessions_table,
    contracts_table, invoices_table, appointments_table,
    visitor_tracking_table, background_jobs_table, analytics_table,
    video_analytics_table
)
from utils.response import create_response
from boto3.dynamodb.conditions import Key, Attr


def create_background_job(job_type, user_id, user_email, metadata=None):
    """
    Create a background job entry
    Returns job_id
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    job_item = {
        'job_id': job_id,
        'job_type': job_type,  # e.g., 'account_deletion', 'bulk_photo_delete'
        'user_id': user_id,
        'user_email': user_email,
        'status': 'pending',  # pending, in_progress, completed, failed
        'progress': Decimal('0'),  # 0-100
        'metadata': json.dumps(metadata) if metadata else '{}',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    background_jobs_table.put_item(Item=job_item)
    return job_id


def update_job_status(job_id, status, progress=None, error_message=None):
    """Update background job status"""
    update_expression = 'SET #status = :status, updated_at = :now'
    expression_values = {
        ':status': status,
        ':now': datetime.utcnow().isoformat() + 'Z'
    }
    expression_names = {'#status': 'status'}
    
    if progress is not None:
        update_expression += ', progress = :progress'
        expression_values[':progress'] = Decimal(str(progress))
    
    if error_message:
        update_expression += ', error_message = :error'
        expression_values[':error'] = error_message
    
    background_jobs_table.update_item(
        Key={'job_id': job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )


def delete_s3_objects_by_prefix(prefix):
    """Delete all S3 objects with a given prefix"""
    try:
        # List objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
        
        objects_deleted = 0
        for page in pages:
            if 'Contents' not in page:
                continue
            
            # Delete in batches of 1000 (S3 limit)
            objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
            
            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket=S3_BUCKET,
                    Delete={'Objects': objects_to_delete}
                )
                objects_deleted += len(objects_to_delete)
        
        return objects_deleted
    except Exception as e:
        print(f"Error deleting S3 objects with prefix {prefix}: {str(e)}")
        return 0


def process_account_deletion(job_id, user_id, user_email):
    """
    Process complete account deletion
    This runs as a background job to avoid Lambda timeouts
    """
    try:
        update_job_status(job_id, 'in_progress', progress=0)
        
        total_steps = 10
        current_step = 0
        
        # Step 1: Get all user galleries
        # Galleries table uses user_id as partition key
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        galleries = galleries_response.get('Items', [])
        gallery_ids = [g['id'] for g in galleries]
        
        # Step 2: Delete all photos and their S3 objects
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        for gallery_id in gallery_ids:
            # Get all photos in gallery
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            photos = photos_response.get('Items', [])
            
            # Delete photo records
            for photo in photos:
                photos_table.delete_item(Key={'id': photo['id']})
            
            # Delete S3 objects for this gallery
            delete_s3_objects_by_prefix(f"galleries/{gallery_id}/")
        
        # Step 3: Delete galleries
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        # Galleries table has composite key: user_id (HASH) + id (RANGE)
        for gallery_id in gallery_ids:
            galleries_table.delete_item(Key={
                'user_id': user_id,
                'id': gallery_id
            })
        
        # Step 4: Delete contracts
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        contracts_response = contracts_table.scan(
            FilterExpression=Attr('photographer_id').eq(user_id)
        )
        for contract in contracts_response.get('Items', []):
            contracts_table.delete_item(Key={'id': contract['id']})
        
        # Step 5: Delete invoices
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        invoices_response = invoices_table.scan(
            FilterExpression=Attr('photographer_id').eq(user_id)
        )
        for invoice in invoices_response.get('Items', []):
            invoices_table.delete_item(Key={'id': invoice['id']})
        
        # Step 6: Delete appointments
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        appointments_response = appointments_table.scan(
            FilterExpression=Attr('photographer_id').eq(user_id)
        )
        for appointment in appointments_response.get('Items', []):
            appointments_table.delete_item(Key={'id': appointment['id']})
        
        # Step 7: Delete analytics data
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        # Delete video analytics
        for gallery_id in gallery_ids:
            video_analytics_response = video_analytics_table.scan(
                FilterExpression=Attr('gallery_id').eq(gallery_id)
            )
            for analytics in video_analytics_response.get('Items', []):
                video_analytics_table.delete_item(Key={'id': analytics['id']})
        
        # Delete visitor tracking
        for gallery_id in gallery_ids:
            visitor_response = visitor_tracking_table.scan(
                FilterExpression=Attr('gallery_id').eq(gallery_id)
            )
            for visitor in visitor_response.get('Items', []):
                visitor_tracking_table.delete_item(Key={'id': visitor['id']})
        
        # Step 8: Delete user's watermark logo if exists
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        delete_s3_objects_by_prefix(f"watermarks/{user_id}/")
        
        # Step 9: Delete all user sessions
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        sessions_response = sessions_table.scan(
            FilterExpression=Attr('user.email').eq(user_email)
        )
        for session in sessions_response.get('Items', []):
            sessions_table.delete_item(Key={'token': session['token']})
        
        # Step 10: Delete user record
        current_step += 1
        update_job_status(job_id, 'in_progress', progress=(current_step / total_steps) * 100)
        
        users_table.delete_item(Key={'email': user_email})
        
        # Mark job as completed
        update_job_status(job_id, 'completed', progress=100)
        
        return True
        
    except Exception as e:
        print(f"Error processing account deletion job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        update_job_status(job_id, 'failed', error_message=str(e))
        return False


def handle_process_background_job(job_id):
    """
    Process a background job
    This would typically be called by a separate Lambda or worker process
    """
    try:
        # Get job details
        response = background_jobs_table.get_item(Key={'job_id': job_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Job not found'})
        
        job = response['Item']
        
        # Route to appropriate processor
        if job['job_type'] == 'account_deletion':
            success = process_account_deletion(
                job_id=job_id,
                user_id=job['user_id'],
                user_email=job['user_email']
            )
            
            if success:
                return create_response(200, {'message': 'Account deletion completed'})
            else:
                return create_response(500, {'error': 'Account deletion failed'})
        
        else:
            return create_response(400, {'error': f"Unknown job type: {job['job_type']}"})
    
    except Exception as e:
        print(f"Error processing background job: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to process job'})


def handle_get_job_status(user, job_id):
    """Get status of a background job"""
    try:
        response = background_jobs_table.get_item(Key={'job_id': job_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Job not found'})
        
        job = response['Item']
        
        # Verify the job belongs to the user
        if job['user_email'] != user['email']:
            return create_response(403, {'error': 'Unauthorized'})
        
        # Convert Decimal to float for JSON serialization
        if 'progress' in job:
            job['progress'] = float(job['progress'])
        
        return create_response(200, {'job': job})
    
    except Exception as e:
        print(f"Error getting job status: {str(e)}")
        return create_response(500, {'error': 'Failed to get job status'})

