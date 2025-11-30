"""
Gallery Expiration & Cleanup Handler
Automatically archives expired galleries and deletes galleries archived for 30+ days
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Attr, Key
from utils.config import galleries_table, photos_table, s3_client, S3_BUCKET, S3_RENDITIONS_BUCKET
from utils.response import create_response
from utils.email import send_gallery_expiration_notice, send_gallery_deletion_notice


def check_and_archive_expired_galleries(event=None, context=None):
    """
    Check all galleries and archive those that have expired
    This should run daily via CloudWatch Events (cron)
    """
    try:
        print("🕐 Starting gallery expiration check...")
        today = datetime.utcnow().date()
        archived_count = 0
        
        # Scan all galleries (across all users) with pagination
        all_galleries = []
        last_key = None
        
        while True:
            if last_key:
                response = galleries_table.scan(ExclusiveStartKey=last_key)
            else:
                response = galleries_table.scan()
            
            all_galleries.extend(response.get('Items', []))
            
            # Check if there are more pages
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        for gallery in all_galleries:
            # Skip if already archived
            if gallery.get('archived', False):
                continue
            
            # Skip if expiry is "never"
            expiry_days = gallery.get('expiry_days')
            if not expiry_days or expiry_days == 'never':
                continue
            
            # Calculate expiration date
            created_at = gallery.get('created_at')
            if not created_at:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                expiry_days_int = int(expiry_days)
                expiration_date = created_date + timedelta(days=expiry_days_int)
                
                # Check if expired
                if today > expiration_date:
                    print(f"📦 Archiving expired gallery: {gallery.get('name')} (ID: {gallery.get('id')})")
                    
                    # Archive the gallery
                    galleries_table.update_item(
                        Key={
                            'user_id': gallery['user_id'],
                            'id': gallery['id']
                        },
                        UpdateExpression='SET archived = :archived, archived_at = :archived_at, archived_reason = :reason',
                        ExpressionAttributeValues={
                            ':archived': True,
                            ':archived_at': datetime.utcnow().isoformat() + 'Z',
                            ':reason': 'expired'
                        }
                    )
                    
                    # Send expiration notice to photographer
                    try:
                        send_gallery_expiration_notice(
                            photographer_email=gallery.get('photographer_email'),
                            gallery_name=gallery.get('name'),
                            gallery_id=gallery.get('id')
                        )
                    except Exception as email_error:
                        print(f"⚠️ Failed to send expiration notice: {email_error}")
                    
                    archived_count += 1
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error processing gallery {gallery.get('id')}: {e}")
                continue
        
        print(f"✅ Archived {archived_count} expired galleries")
        
        return create_response(200, {
            'message': f'Successfully archived {archived_count} expired galleries',
            'archived_count': archived_count
        })
        
    except Exception as e:
        print(f"❌ Error checking expired galleries: {str(e)}")
        return create_response(500, {'error': f'Failed to check expired galleries: {str(e)}'})


def delete_old_archived_galleries(event=None, context=None):
    """
    Permanently delete galleries that have been archived for 30+ days
    This should run daily via CloudWatch Events (cron)
    """
    try:
        print("🗑️ Starting old archived gallery cleanup...")
        today = datetime.utcnow().date()
        deleted_count = 0
        
        # Scan all galleries with pagination
        all_galleries = []
        last_key = None
        
        while True:
            if last_key:
                response = galleries_table.scan(ExclusiveStartKey=last_key)
            else:
                response = galleries_table.scan()
            
            all_galleries.extend(response.get('Items', []))
            
            # Check if there are more pages
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        for gallery in all_galleries:
            # Only process archived galleries
            if not gallery.get('archived', False):
                continue
            
            archived_at = gallery.get('archived_at')
            if not archived_at:
                continue
            
            try:
                archived_date = datetime.fromisoformat(archived_at.replace('Z', '+00:00')).date()
                days_archived = (today - archived_date).days
                
                # Delete if archived for 30+ days
                if days_archived >= 30:
                    gallery_id = gallery['id']
                    user_id = gallery['user_id']
                    gallery_name = gallery.get('name', 'Untitled')
                    
                    print(f"🗑️ Deleting gallery archived for {days_archived} days: {gallery_name} (ID: {gallery_id})")
                    
                    # 1. Delete all photos in S3 (originals and renditions)
                    try:
                        # Query all photos for this gallery
                        photos_response = photos_table.query(
                            IndexName='GalleryIdIndex',
                            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
                        )
                        
                        photos = photos_response.get('Items', [])
                        
                        for photo in photos:
                            # Delete from S3 photos bucket
                            s3_key = photo.get('s3_key')
                            if s3_key:
                                try:
                                    s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                                    print(f"  ✓ Deleted S3 object: {s3_key}")
                                except Exception as s3_error:
                                    print(f"  ⚠️ Failed to delete S3 object {s3_key}: {s3_error}")
                            
                            # Delete original file if it exists
                            original_s3_key = photo.get('original_s3_key')
                            if original_s3_key:
                                try:
                                    s3_client.delete_object(Bucket=S3_BUCKET, Key=original_s3_key)
                                    print(f"  ✓ Deleted original S3 object: {original_s3_key}")
                                except Exception as s3_error:
                                    print(f"  ⚠️ Failed to delete original S3 object {original_s3_key}: {s3_error}")
                            
                            # Delete renditions from S3 renditions bucket
                            rendition_keys = [
                                photo.get('thumbnail_key'),
                                photo.get('small_key'),
                                photo.get('medium_key'),
                                photo.get('large_key')
                            ]
                            
                            for rendition_key in rendition_keys:
                                if rendition_key:
                                    try:
                                        s3_client.delete_object(Bucket=S3_RENDITIONS_BUCKET, Key=rendition_key)
                                        print(f"  ✓ Deleted rendition: {rendition_key}")
                                    except Exception as s3_error:
                                        print(f"  ⚠️ Failed to delete rendition {rendition_key}: {s3_error}")
                            
                            # Delete photo from DynamoDB
                            try:
                                photos_table.delete_item(
                                    Key={
                                        'user_id': user_id,
                                        'id': photo['id']
                                    }
                                )
                                print(f"  ✓ Deleted photo record: {photo['id']}")
                            except Exception as db_error:
                                print(f"  ⚠️ Failed to delete photo record {photo['id']}: {db_error}")
                        
                        print(f"  ✓ Deleted {len(photos)} photos")
                        
                    except Exception as photos_error:
                        print(f"  ⚠️ Error deleting photos: {photos_error}")
                    
                    # 2. Delete the gallery from DynamoDB
                    try:
                        galleries_table.delete_item(
                            Key={
                                'user_id': user_id,
                                'id': gallery_id
                            }
                        )
                        print(f"  ✓ Deleted gallery record: {gallery_id}")
                    except Exception as db_error:
                        print(f"  ⚠️ Failed to delete gallery record: {db_error}")
                    
                    # 3. Send deletion notice to photographer
                    try:
                        send_gallery_deletion_notice(
                            photographer_email=gallery.get('photographer_email'),
                            gallery_name=gallery_name,
                            archived_days=days_archived
                        )
                    except Exception as email_error:
                        print(f"  ⚠️ Failed to send deletion notice: {email_error}")
                    
                    deleted_count += 1
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error processing archived gallery {gallery.get('id')}: {e}")
                continue
        
        print(f"✅ Permanently deleted {deleted_count} old archived galleries")
        
        return create_response(200, {
            'message': f'Successfully deleted {deleted_count} old archived galleries',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"❌ Error deleting old archived galleries: {str(e)}")
        return create_response(500, {'error': f'Failed to delete old archived galleries: {str(e)}'})


from handlers.notification_handler import notify_gallery_expiring

def send_expiry_reminders(event=None, context=None):
    """
    Send reminders to clients for galleries expiring in 7 days or 1 day.
    This should run daily via CloudWatch Events (cron).
    """
    try:
        print("📧 Sending gallery expiration reminders...")
        today = datetime.utcnow().date()
        reminders_sent = 0
        
        # Scan all galleries
        all_galleries = []
        last_key = None
        
        while True:
            if last_key:
                response = galleries_table.scan(ExclusiveStartKey=last_key)
            else:
                response = galleries_table.scan()
            
            all_galleries.extend(response.get('Items', []))
            
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        for gallery in all_galleries:
            # Skip if archived or never expires
            if gallery.get('archived', False):
                continue
            
            expiry_days = gallery.get('expiry_days')
            if not expiry_days or expiry_days == 'never':
                continue
                
            created_at = gallery.get('created_at')
            if not created_at:
                continue
                
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                expiry_days_int = int(expiry_days)
                expiration_date = created_date + timedelta(days=expiry_days_int)
                
                days_until = (expiration_date - today).days
                
                # Send reminder at 7 days and 1 day
                if days_until == 7 or days_until == 1:
                    print(f"  🔔 Gallery '{gallery.get('name')}' expires in {days_until} days")
                    
                    user_id = gallery.get('user_id')
                    gallery_id = gallery.get('id')
                    client_email = gallery.get('client_email')
                    
                    if not client_email:
                        continue
                        
                    # Get photographer name
                    photographer_name = "Photographer" # Default
                    # In a real app, we might fetch user to get name, or store it in gallery
                    # optimizing by not fetching user if possible, or fetch batch.
                    # For now, let's try to get it from gallery if stored, or fetch user
                    from utils.config import users_table
                    user_resp = users_table.get_item(Key={'id': user_id})
                    if 'Item' in user_resp:
                        user = user_resp['Item']
                        photographer_name = user.get('name') or user.get('username') or "Photographer"
                    
                    client_name = gallery.get('client_name', 'Client')
                    
                    # Build URL
                    import os
                    frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
                    share_token = gallery.get('share_token')
                    gallery_url = f"{frontend_url}/client-gallery?token={share_token}" if share_token else f"{frontend_url}/gallery/{gallery_id}"
                    
                    # Send notification
                    success = notify_gallery_expiring(
                        user_id, gallery_id, client_email, client_name,
                        photographer_name, gallery_url, days_until
                    )
                    
                    if success:
                        reminders_sent += 1
                        
            except Exception as e:
                print(f"⚠️ Error processing reminder for gallery {gallery.get('id')}: {e}")
                continue
                
        print(f"✅ Sent {reminders_sent} expiration reminders")
        return reminders_sent
        
    except Exception as e:
        print(f"❌ Error sending expiry reminders: {str(e)}")
        return 0

def run_daily_cleanup(event=None, context=None):
    """
    Combined daily cleanup job:
    1. Send expiry reminders (7 days / 1 day before)
    2. Archive expired galleries
    3. Delete galleries archived for 30+ days
    """
    try:
        print("🔄 Running daily gallery cleanup...")
        
        # Step 0: Send expiry reminders
        reminders_count = send_expiry_reminders()
        
        # Step 1: Archive expired galleries
        archive_result = check_and_archive_expired_galleries()
        
        # Step 2: Delete old archived galleries
        delete_result = delete_old_archived_galleries()
        
        # Extract counts from results
        import json
        archived_count = 0
        deleted_count = 0
        
        if isinstance(archive_result, dict) and 'body' in archive_result:
            body_str = archive_result['body']
            if isinstance(body_str, str):
                archive_data = json.loads(body_str)
                archived_count = archive_data.get('archived_count', 0)
            elif isinstance(body_str, dict):
                archived_count = body_str.get('archived_count', 0)
        
        if isinstance(delete_result, dict) and 'body' in delete_result:
            body_str = delete_result['body']
            if isinstance(body_str, str):
                delete_data = json.loads(body_str)
                deleted_count = delete_data.get('deleted_count', 0)
            elif isinstance(body_str, dict):
                deleted_count = body_str.get('deleted_count', 0)
        
        return create_response(200, {
            'message': 'Daily cleanup completed successfully',
            'reminders_sent': reminders_count,
            'archived': archived_count,
            'deleted': deleted_count
        })
        
    except Exception as e:
        print(f"❌ Error running daily cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': f'Failed to run daily cleanup: {str(e)}'})


def handle_check_expiring_galleries(event=None, context=None):
    """
    Check for galleries that are expiring soon (within 7 days)
    Returns a list of expiring galleries for notification purposes
    """
    try:
        print("🔔 Checking for expiring galleries...")
        today = datetime.utcnow().date()
        seven_days_from_now = today + timedelta(days=7)
        expiring_galleries = []
        
        # Scan all galleries
        response = galleries_table.scan()
        all_galleries = response.get('Items', [])
        
        for gallery in all_galleries:
            # Skip archived galleries
            if gallery.get('archived', False):
                continue
            
            # Skip galleries that never expire
            expiry_days = gallery.get('expiry_days')
            if not expiry_days or expiry_days == 'never':
                continue
            
            # Calculate expiration date
            created_at = gallery.get('created_at')
            if not created_at:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                expiry_days_int = int(expiry_days)
                expiration_date = created_date + timedelta(days=expiry_days_int)
                
                # Check if expiring within 7 days (include galleries expiring today)
                if today <= expiration_date <= seven_days_from_now:
                    days_until_expiry = (expiration_date - today).days
                    expiring_galleries.append({
                        'gallery_id': gallery.get('id'),
                        'gallery_name': gallery.get('name'),
                        'user_id': gallery.get('user_id'),
                        'photographer_email': gallery.get('photographer_email'),
                        'expiration_date': expiration_date.isoformat(),
                        'days_until_expiry': days_until_expiry
                    })
                    print(f"⚠️ Gallery expiring in {days_until_expiry} days: {gallery.get('name')}")
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error processing gallery {gallery.get('id')}: {e}")
                continue
        
        print(f"✅ Found {len(expiring_galleries)} galleries expiring within 7 days")
        
        return create_response(200, {
            'message': f'Found {len(expiring_galleries)} expiring galleries',
            'expiring_galleries': expiring_galleries,
            'count': len(expiring_galleries)
        })
        
    except Exception as e:
        print(f"❌ Error checking expiring galleries: {str(e)}")
        return create_response(500, {'error': f'Failed to check expiring galleries: {str(e)}'})


def handle_manual_expiry_check(user):
    """
    Manual expiry check for a photographer's galleries
    Returns galleries that will expire soon
    """
    try:
        user_id = user.get('id')
        print(f"🔍 Manual expiry check for user: {user_id}")
        
        today = datetime.utcnow().date()
        seven_days_from_now = today + timedelta(days=7)
        expiring_galleries = []
        
        # Query this user's galleries
        from boto3.dynamodb.conditions import Key
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        user_galleries = response.get('Items', [])
        
        for gallery in user_galleries:
            # Skip archived galleries
            if gallery.get('archived', False):
                continue
            
            # Skip galleries that never expire
            expiry_days = gallery.get('expiry_days')
            if not expiry_days or expiry_days == 'never':
                continue
            
            # Calculate expiration date
            created_at = gallery.get('created_at')
            if not created_at:
                continue
            
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                expiry_days_int = int(expiry_days)
                expiration_date = created_date + timedelta(days=expiry_days_int)
                
                # Check if expiring within 7 days or already expired
                if expiration_date <= seven_days_from_now:
                    days_until_expiry = (expiration_date - today).days
                    status = 'expired' if days_until_expiry < 0 else 'expiring_soon'
                    
                    expiring_galleries.append({
                        'gallery_id': gallery.get('id'),
                        'gallery_name': gallery.get('name'),
                        'expiration_date': expiration_date.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'status': status
                    })
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error processing gallery {gallery.get('id')}: {e}")
                continue
        
        return create_response(200, {
            'message': f'Found {len(expiring_galleries)} galleries expiring within 7 days',
            'expiring_galleries': expiring_galleries,
            'count': len(expiring_galleries)
        })
        
    except Exception as e:
        print(f"❌ Error checking user galleries: {str(e)}")
        return create_response(500, {'error': f'Failed to check galleries: {str(e)}'})
