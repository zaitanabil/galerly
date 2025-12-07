"""
RAW Vault Archival Handler
Manages long-term cold storage of RAW files in AWS Glacier
Ultimate plan feature for cost-effective RAW file archival
"""
import uuid
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import s3_client, S3_BUCKET, users_table, photos_table, raw_vault_table
from utils.response import create_response
from utils.email import send_email


def handle_archive_to_vault(user, body):
    """
    Archive RAW file to Glacier Deep Archive
    Ultimate plan feature
    
    Request body:
    {
        "photo_id": "uuid",
        "gallery_id": "uuid"
    }
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('raw_vault'):
            return create_response(403, {
                'error': 'RAW Vault Archival is available on the Ultimate plan only.',
                'upgrade_required': True,
                'required_feature': 'raw_vault'
            })
        
        photo_id = body.get('photo_id')
        gallery_id = body.get('gallery_id')
        
        if not photo_id:
            return create_response(400, {'error': 'photo_id required'})
        
        # Get photo details
        photo_response = photos_table.get_item(Key={'id': photo_id})
        
        if 'Item' not in photo_response:
            return create_response(404, {'error': 'Photo not found'})
        
        photo = photo_response['Item']
        
        # Verify ownership
        if photo['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Check if it's a RAW file
        if not photo.get('is_raw'):
            return create_response(400, {
                'error': 'Only RAW files can be archived to vault',
                'is_raw': False
            })
        
        # Check if already archived
        vault_response = raw_vault_table.query(
            IndexName='PhotoIdIndex',
            KeyConditionExpression=Key('photo_id').eq(photo_id)
        )
        
        if vault_response.get('Items'):
            return create_response(400, {
                'error': 'File is already archived in vault',
                'vault_entry': vault_response['Items'][0]
            })
        
        # Tag the S3 object for Glacier transition
        s3_key = photo['s3_key']
        
        try:
            # Apply tag that triggers lifecycle policy to Glacier
            s3_client.put_object_tagging(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Tagging={
                    'TagSet': [
                        {'Key': 'storage-class', 'Value': 'glacier'},
                        {'Key': 'archived-by', 'Value': user['id']},
                        {'Key': 'archived-at', 'Value': datetime.utcnow().isoformat()}
                    ]
                }
            )
        except Exception as tag_error:
            print(f"Warning: Could not tag S3 object: {str(tag_error)}")
        
        # Create vault entry
        vault_id = str(uuid.uuid4())
        vault_entry = {
            'id': vault_id,
            'user_id': user['id'],
            'photo_id': photo_id,
            'gallery_id': gallery_id or photo.get('gallery_id'),
            's3_key': s3_key,
            'original_filename': photo.get('filename'),
            'file_size_mb': float(photo.get('size_mb', 0)),
            'camera_make': photo.get('camera_make'),
            'camera_model': photo.get('camera_model'),
            'status': 'archiving',  # archiving -> archived
            'storage_class': 'GLACIER_DEEP_ARCHIVE',
            'archived_at': datetime.utcnow().isoformat() + 'Z',
            'retrieval_tier': 'bulk',  # bulk (12-48h, cheapest), standard (3-5h), expedited (1-5min, expensive)
        }
        
        raw_vault_table.put_item(Item=vault_entry)
        
        print(f"? RAW file archived to vault: {s3_key}")
        
        return create_response(201, {
            'message': 'RAW file queued for Glacier archival',
            'vault_id': vault_id,
            'vault_entry': vault_entry,
            'note': 'File will transition to Glacier Deep Archive within 24 hours'
        })
        
    except Exception as e:
        print(f"Error archiving to vault: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to archive file'})


def handle_list_vault_files(user, query_params=None):
    """
    List all RAW files in user's vault
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('raw_vault'):
            return create_response(403, {
                'error': 'RAW Vault is an Ultimate plan feature',
                'upgrade_required': True
            })
        
        response = raw_vault_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        
        vault_files = response.get('Items', [])
        
        # Sort by archived_at desc
        vault_files.sort(key=lambda x: x.get('archived_at', ''), reverse=True)
        
        # Calculate total storage
        total_storage_mb = sum(float(f.get('file_size_mb', 0)) for f in vault_files)
        
        return create_response(200, {
            'vault_files': vault_files,
            'count': len(vault_files),
            'total_storage_mb': round(total_storage_mb, 2),
            'total_storage_gb': round(total_storage_mb / 1024, 2)
        })
        
    except Exception as e:
        print(f"Error listing vault files: {str(e)}")
        return create_response(500, {'error': 'Failed to list vault files'})


def handle_request_retrieval(vault_id, user, body):
    """
    Request retrieval of archived RAW file from Glacier
    
    Request body:
    {
        "tier": "bulk" | "standard" | "expedited"
    }
    
    Retrieval times:
    - bulk: 12-48 hours (cheapest)
    - standard: 3-5 hours (moderate cost)
    - expedited: 1-5 minutes (expensive)
    """
    try:
        # Get vault entry
        vault_response = raw_vault_table.get_item(Key={'id': vault_id})
        
        if 'Item' not in vault_response:
            return create_response(404, {'error': 'Vault entry not found'})
        
        vault_entry = vault_response['Item']
        
        # Verify ownership
        if vault_entry['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        tier = body.get('tier', 'bulk')
        
        if tier not in ['bulk', 'standard', 'expedited']:
            return create_response(400, {'error': 'Invalid tier. Must be bulk, standard, or expedited'})
        
        # Check if already retrieving
        if vault_entry.get('status') == 'retrieving':
            return create_response(400, {
                'error': 'File is already being retrieved',
                'estimated_completion': vault_entry.get('retrieval_completion_time')
            })
        
        # Initiate Glacier restore
        s3_key = vault_entry['s3_key']
        
        # Calculate retrieval completion time
        if tier == 'bulk':
            hours = 48
        elif tier == 'standard':
            hours = 5
        else:  # expedited
            hours = 0.1  # ~5 minutes
        
        completion_time = (datetime.utcnow() + timedelta(hours=hours)).isoformat() + 'Z'
        
        try:
            # Initiate S3 Glacier restore
            s3_client.restore_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                RestoreRequest={
                    'Days': 7,  # Keep restored copy available for 7 days
                    'GlacierJobParameters': {
                        'Tier': tier.capitalize()
                    }
                }
            )
            
            print(f"? Glacier restore initiated: {s3_key} ({tier} tier)")
            
        except Exception as restore_error:
            # Check if already restored
            if 'RestoreAlreadyInProgress' in str(restore_error):
                print(f"?? Restore already in progress for {s3_key}")
            elif 'ObjectAlreadyInActiveTierError' in str(restore_error):
                # File is already restored
                vault_entry['status'] = 'available'
                vault_entry['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                raw_vault_table.put_item(Item=vault_entry)
                
                return create_response(200, {
                    'message': 'File is already restored and available for download',
                    'vault_entry': vault_entry
                })
            else:
                raise restore_error
        
        # Update vault entry
        vault_entry['status'] = 'retrieving'
        vault_entry['retrieval_tier'] = tier
        vault_entry['retrieval_requested_at'] = datetime.utcnow().isoformat() + 'Z'
        vault_entry['retrieval_completion_time'] = completion_time
        vault_entry['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        raw_vault_table.put_item(Item=vault_entry)
        
        # Send email notification
        try:
            send_email(
                to_addresses=[user['email']],
                subject='RAW File Retrieval Requested',
                body_html=f"""
                <p>Hi {user.get('name', 'there')},</p>
                <p>Your RAW file retrieval request has been initiated.</p>
                <p><strong>File:</strong> {vault_entry.get('original_filename')}</p>
                <p><strong>Tier:</strong> {tier.capitalize()}</p>
                <p><strong>Estimated completion:</strong> {completion_time}</p>
                <p>You will receive another email when the file is ready for download.</p>
                """,
                body_text=f"RAW file retrieval initiated. Estimated completion: {completion_time}"
            )
        except Exception as email_error:
            print(f"Warning: Could not send notification email: {str(email_error)}")
        
        return create_response(200, {
            'message': f'Retrieval initiated ({tier} tier)',
            'vault_entry': vault_entry,
            'estimated_completion': completion_time
        })
        
    except Exception as e:
        print(f"Error requesting retrieval: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to request retrieval'})


def handle_check_retrieval_status(vault_id, user):
    """
    Check status of Glacier retrieval
    """
    try:
        vault_response = raw_vault_table.get_item(Key={'id': vault_id})
        
        if 'Item' not in vault_response:
            return create_response(404, {'error': 'Vault entry not found'})
        
        vault_entry = vault_response['Item']
        
        # Verify ownership
        if vault_entry['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Check S3 restore status
        s3_key = vault_entry['s3_key']
        
        try:
            response = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
            restore_status = response.get('Restore')
            
            if restore_status:
                if 'ongoing-request="false"' in restore_status:
                    # Restore complete
                    vault_entry['status'] = 'available'
                    vault_entry['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                    raw_vault_table.put_item(Item=vault_entry)
                    
                    # Send completion email
                    try:
                        download_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                            ExpiresIn=int(os.environ.get('PRESIGNED_URL_EXPIRY'))
                        )
                        
                        send_email(
                            to_addresses=[user['email']],
                            subject='RAW File Ready for Download',
                            body_html=f"""
                            <p>Hi {user.get('name', 'there')},</p>
                            <p>Your RAW file has been retrieved and is ready for download.</p>
                            <p><strong>File:</strong> {vault_entry.get('original_filename')}</p>
                            <p><strong>Available until:</strong> 7 days from now</p>
                            <p><a href="{download_url}">Download Now</a></p>
                            """,
                            body_text=f"Your RAW file is ready for download: {download_url}"
                        )
                    except Exception as email_error:
                        print(f"Warning: Could not send completion email: {str(email_error)}")
                    
                    return create_response(200, {
                        'status': 'available',
                        'message': 'File is ready for download',
                        'vault_entry': vault_entry
                    })
                else:
                    # Still retrieving
                    return create_response(200, {
                        'status': 'retrieving',
                        'message': 'Retrieval in progress',
                        'estimated_completion': vault_entry.get('retrieval_completion_time'),
                        'vault_entry': vault_entry
                    })
            else:
                # Not yet initiated or archived
                return create_response(200, {
                    'status': vault_entry.get('status', 'archived'),
                    'vault_entry': vault_entry
                })
                
        except Exception as s3_error:
            print(f"Error checking S3 restore status: {str(s3_error)}")
            return create_response(200, {
                'status': vault_entry.get('status', 'unknown'),
                'vault_entry': vault_entry
            })
        
    except Exception as e:
        print(f"Error checking retrieval status: {str(e)}")
        return create_response(500, {'error': 'Failed to check status'})


def handle_download_vault_file(vault_id, user):
    """
    Generate presigned URL for downloading restored RAW file
    """
    try:
        vault_response = raw_vault_table.get_item(Key={'id': vault_id})
        
        if 'Item' not in vault_response:
            return create_response(404, {'error': 'Vault entry not found'})
        
        vault_entry = vault_response['Item']
        
        # Verify ownership
        if vault_entry['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Check if file is available
        if vault_entry.get('status') != 'available':
            return create_response(400, {
                'error': 'File is not available for download yet',
                'status': vault_entry.get('status'),
                'message': 'Please request retrieval first'
            })
        
        # Generate presigned URL
        s3_key = vault_entry['s3_key']
        
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600  # 1 hour
        )
        
        return create_response(200, {
            'download_url': download_url,
            'filename': vault_entry.get('original_filename'),
            'file_size_mb': vault_entry.get('file_size_mb'),
            'expires_in': 3600
        })
        
    except Exception as e:
        print(f"Error generating download URL: {str(e)}")
        return create_response(500, {'error': 'Failed to generate download URL'})


def handle_delete_vault_file(vault_id, user):
    """
    Permanently delete RAW file from vault
    """
    try:
        vault_response = raw_vault_table.get_item(Key={'id': vault_id})
        
        if 'Item' not in vault_response:
            return create_response(404, {'error': 'Vault entry not found'})
        
        vault_entry = vault_response['Item']
        
        # Verify ownership
        if vault_entry['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Delete from S3
        s3_key = vault_entry['s3_key']
        
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
            print(f"? Deleted from S3: {s3_key}")
        except Exception as s3_error:
            print(f"Warning: Could not delete from S3: {str(s3_error)}")
        
        # Delete vault entry
        raw_vault_table.delete_item(Key={'id': vault_id})
        
        return create_response(200, {
            'message': 'Vault file permanently deleted'
        })
        
    except Exception as e:
        print(f"Error deleting vault file: {str(e)}")
        return create_response(500, {'error': 'Failed to delete file'})
