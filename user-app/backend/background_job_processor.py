"""
Background Job Processor Lambda
Triggered by DynamoDB Streams when new jobs are created
Processes long-running tasks asynchronously
"""
import json
import os
from handlers.background_jobs_handler import handle_process_background_job


def lambda_handler(event, context):
    """
    Process background jobs triggered by DynamoDB Streams
    """
    print(f"Processing {len(event['Records'])} job(s)")
    
    results = []
    
    for record in event['Records']:
        # Only process INSERT events with status=pending
        if record['eventName'] != 'INSERT':
            continue
        
        new_image = record['dynamodb'].get('NewImage', {})
        job_id = new_image.get('job_id', {}).get('S')
        status = new_image.get('status', {}).get('S')
        
        if not job_id or status != 'pending':
            continue
        
        print(f"Processing job: {job_id}")
        
        try:
            # Process the job
            response = handle_process_background_job(job_id)
            results.append({
                'job_id': job_id,
                'status': 'processed',
                'response': response
            })
            print(f"Job {job_id} processed successfully")
            
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'job_id': job_id,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(results),
            'results': results
        })
    }

