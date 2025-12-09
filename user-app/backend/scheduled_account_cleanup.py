"""
Scheduled Account Cleanup Job
Permanently deletes accounts that have been marked for deletion for > 30 days

This script should be run daily via:
- AWS Lambda scheduled event (CloudWatch Events)
- Cron job
- Manual execution for testing

Usage:
    python scheduled_account_cleanup.py

Environment Variables Required:
    - All DynamoDB table names
    - S3 bucket names
    - AWS credentials
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Attr

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import (
    users_table, galleries_table, photos_table, sessions_table,
    billing_table, subscriptions_table, analytics_table,
    client_favorites_table, client_feedback_table, invoices_table,
    appointments_table, contracts_table, seo_settings_table,
    raw_vault_table, email_templates_table, background_jobs_table,
    visitor_tracking_table, video_analytics_table,
    s3_client, S3_BUCKET
)
from utils.email import send_account_deleted_confirmation_email


def permanently_delete_account(user_id, user_email):
    """
    Permanently delete account and all associated data
    (except billing records - retained for 7 years for tax compliance)
    
    Returns: (success: bool, error: str or None)
    """
    try:
        print(f"  🗑️  Permanently deleting account: {user_email}")
        
        # 1. Delete galleries
        try:
            galleries_response = galleries_table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            galleries = galleries_response.get('Items', [])
            print(f"    Found {len(galleries)} galleries")
            
            for gallery in galleries:
                # Delete gallery photos from DynamoDB
                try:
                    photos_response = photos_table.query(
                        IndexName='GalleryIdIndex',
                        KeyConditionExpression='gallery_id = :gid',
                        ExpressionAttributeValues={':gid': gallery['id']}
                    )
                    photos = photos_response.get('Items', [])
                    
                    for photo in photos:
                        # Delete photo files from S3
                        try:
                            s3_key = photo.get('s3_key')
                            if s3_key:
                                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                        except Exception as s3_error:
                            print(f"    ⚠️  Failed to delete S3 object: {str(s3_error)}")
                        
                        # Delete photo record
                        photos_table.delete_item(Key={'id': photo['id']})
                    
                    print(f"      Deleted {len(photos)} photos from gallery {gallery['id']}")
                except Exception as photo_error:
                    print(f"    ⚠️  Error deleting photos: {str(photo_error)}")
                
                # Delete gallery record
                galleries_table.delete_item(
                    Key={'user_id': user_id, 'id': gallery['id']}
                )
            
            print(f"    ✅ Deleted {len(galleries)} galleries")
        except Exception as gallery_error:
            print(f"    ⚠️  Error deleting galleries: {str(gallery_error)}")
        
        # 2. Delete sessions
        try:
            sessions_response = sessions_table.scan(
                FilterExpression=Attr('user').id.eq(user_id)
            )
            sessions = sessions_response.get('Items', [])
            for session in sessions:
                sessions_table.delete_item(Key={'token': session['token']})
            print(f"    ✅ Deleted {len(sessions)} sessions")
        except Exception as session_error:
            print(f"    ⚠️  Error deleting sessions: {str(session_error)}")
        
        # 3. Anonymize billing records (CANNOT DELETE - 7 year retention)
        try:
            billing_response = billing_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            billing_records = billing_response.get('Items', [])
            for record in billing_records:
                # Anonymize but keep for tax compliance
                billing_table.update_item(
                    Key={'id': record['id']},
                    UpdateExpression='SET user_email = :anon, anonymized_at = :now REMOVE user_id',
                    ExpressionAttributeValues={
                        ':anon': '[DELETED USER]',
                        ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                    }
                )
            print(f"    ✅ Anonymized {len(billing_records)} billing records (retained for tax)")
        except Exception as billing_error:
            print(f"    ⚠️  Error anonymizing billing: {str(billing_error)}")
        
        # 4. Delete subscriptions
        try:
            subscriptions_response = subscriptions_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            subscriptions = subscriptions_response.get('Items', [])
            for subscription in subscriptions:
                subscriptions_table.delete_item(Key={'id': subscription['id']})
            print(f"    ✅ Deleted {len(subscriptions)} subscriptions")
        except Exception as sub_error:
            print(f"    ⚠️  Error deleting subscriptions: {str(sub_error)}")
        
        # 5. Delete analytics data
        try:
            analytics_response = analytics_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            analytics = analytics_response.get('Items', [])
            for record in analytics:
                analytics_table.delete_item(Key={'id': record['id']})
            print(f"    ✅ Deleted {len(analytics)} analytics records")
        except Exception as analytics_error:
            print(f"    ⚠️  Error deleting analytics: {str(analytics_error)}")
        
        # 6-12. Delete other user data (favorites, feedback, invoices, etc.)
        tables_to_clean = [
            (client_favorites_table, 'photographer_id', 'client favorites'),
            (client_feedback_table, 'user_id', 'feedback'),
            (invoices_table, 'user_id', 'invoices'),
            (appointments_table, 'user_id', 'appointments'),
            (contracts_table, 'user_id', 'contracts'),
            (email_templates_table, 'user_id', 'email templates'),
            (background_jobs_table, 'user_id', 'background jobs'),
            (visitor_tracking_table, 'user_id', 'visitor tracking'),
            (video_analytics_table, 'user_id', 'video analytics')
        ]
        
        for table, key_field, name in tables_to_clean:
            try:
                response = table.scan(
                    FilterExpression=Attr(key_field).eq(user_id)
                )
                items = response.get('Items', [])
                for item in items:
                    table.delete_item(Key={'id': item['id']})
                if items:
                    print(f"    ✅ Deleted {len(items)} {name}")
            except Exception as e:
                print(f"    ⚠️  Error deleting {name}: {str(e)}")
        
        # 13. Delete SEO settings (different key structure)
        try:
            seo_settings_table.delete_item(Key={'user_id': user_id})
            print(f"    ✅ Deleted SEO settings")
        except Exception as seo_error:
            print(f"    ⚠️  Error deleting SEO settings: {str(seo_error)}")
        
        # 14. Delete RAW vault files from S3
        try:
            vault_response = raw_vault_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            vault_files = vault_response.get('Items', [])
            for vault_file in vault_files:
                # Delete from S3
                try:
                    s3_key = vault_file.get('s3_key')
                    if s3_key:
                        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                except Exception as s3_error:
                    print(f"    ⚠️  Failed to delete vault file from S3: {str(s3_error)}")
                
                # Delete record
                raw_vault_table.delete_item(Key={'id': vault_file['id']})
            
            if vault_files:
                print(f"    ✅ Deleted {len(vault_files)} vault files")
        except Exception as vault_error:
            print(f"    ⚠️  Error deleting vault files: {str(vault_error)}")
        
        # 15. Finally, delete user profile
        try:
            users_table.delete_item(Key={'email': user_email})
            print(f"    ✅ Deleted user profile")
        except Exception as user_error:
            print(f"    ⚠️  Error deleting user profile: {str(user_error)}")
        
        print(f"  ✅ Account permanently deleted: {user_email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Failed to delete account: {str(e)}"
        print(f"  ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg


def cleanup_expired_deletions():
    """
    Find and permanently delete accounts marked for deletion > 30 days ago
    
    Returns: dict with statistics
    """
    print("=" * 80)
    print("🧹 SCHEDULED ACCOUNT CLEANUP")
    print(f"   Time: {datetime.now(timezone.utc).isoformat()}Z")
    print("=" * 80)
    
    stats = {
        'checked': 0,
        'deleted': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # Find all accounts with status = 'pending_deletion'
        response = users_table.scan(
            FilterExpression=Attr('account_status').eq('pending_deletion')
        )
        
        pending_accounts = response.get('Items', [])
        stats['checked'] = len(pending_accounts)
        
        print(f"\n📊 Found {len(pending_accounts)} accounts pending deletion")
        
        if not pending_accounts:
            print("   No accounts to delete")
            return stats
        
        # Check each account
        now = datetime.now(timezone.utc)
        
        for user in pending_accounts:
            user_id = user.get('id')
            user_email = user.get('email')
            deletion_scheduled_for = user.get('deletion_scheduled_for')
            
            if not deletion_scheduled_for:
                print(f"\n⚠️  Account {user_email} has no deletion_scheduled_for date - skipping")
                continue
            
            # Parse deletion date
            try:
                deletion_date = datetime.fromisoformat(deletion_scheduled_for.replace('Z', ''))
            except:
                print(f"\n⚠️  Invalid deletion date for {user_email}: {deletion_scheduled_for}")
                continue
            
            # Check if grace period expired
            days_remaining = (deletion_date - now).days
            
            if now >= deletion_date:
                # Grace period expired - delete now
                print(f"\n🗑️  Deleting account (grace period expired): {user_email}")
                print(f"   Deletion was scheduled for: {deletion_scheduled_for}")
                
                success, error = permanently_delete_account(user_id, user_email)
                
                if success:
                    stats['deleted'] += 1
                    
                    # Send final confirmation email (if email service available)
                    try:
                        send_account_deleted_confirmation_email(user_email)
                    except Exception as email_error:
                        print(f"    ⚠️  Failed to send confirmation email: {str(email_error)}")
                else:
                    stats['failed'] += 1
                    stats['errors'].append({
                        'email': user_email,
                        'error': error
                    })
            else:
                print(f"\n⏳ Account {user_email} still in grace period ({days_remaining} days remaining)")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 CLEANUP SUMMARY")
        print(f"   Accounts checked: {stats['checked']}")
        print(f"   Successfully deleted: {stats['deleted']}")
        print(f"   Failed: {stats['failed']}")
        
        if stats['errors']:
            print(f"\n❌ ERRORS:")
            for error in stats['errors']:
                print(f"   - {error['email']}: {error['error']}")
        
        print("=" * 80)
        
        return stats
        
    except Exception as e:
        print(f"\n❌ Fatal error in cleanup job: {str(e)}")
        import traceback
        traceback.print_exc()
        stats['errors'].append({'error': str(e)})
        return stats


def lambda_handler(event, context):
    """
    AWS Lambda handler for scheduled execution
    Triggered by CloudWatch Events (daily schedule)
    """
    print("🚀 Lambda function started")
    stats = cleanup_expired_deletions()
    
    return {
        'statusCode': 200,
        'body': stats
    }


if __name__ == '__main__':
    # For local testing and cron execution
    print("🔧 Running in standalone mode")
    stats = cleanup_expired_deletions()
    
    # Exit with error code if any deletions failed
    if stats['failed'] > 0:
        sys.exit(1)
    
    sys.exit(0)

