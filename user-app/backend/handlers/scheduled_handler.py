"""
Scheduled Lambda handlers for periodic tasks
"""
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table
from utils.response import create_response
from handlers.notification_handler import should_send_notification

def handle_gallery_expiration_reminders(event, context):
    """
    DEPRECATED: Galleries no longer expire
    This function is kept for backwards compatibility but does nothing
    """
    print("ℹ️  Gallery expiration reminders are disabled - galleries never expire")
    return create_response(200, {
        'message': 'Gallery expiration feature is disabled',
        'reminders_sent': 0
    })

def _handle_gallery_expiration_reminders_DEPRECATED(event, context):
    """
    Scheduled Lambda function to send expiration reminders for galleries
    Runs daily via EventBridge/CloudWatch Events
    
    Checks for galleries expiring within 7 days and sends reminder emails
    """
    try:
        print("🔄 Starting gallery expiration reminder check...")
        
        # Calculate date range (galleries expiring within 7 days)
        today = datetime.utcnow()
        reminder_window = today + timedelta(days=7)
        
        # Format dates for comparison (ISO format strings)
        today_str = today.isoformat() + 'Z'
        reminder_window_str = reminder_window.isoformat() + 'Z'
        
        print(f"Checking galleries expiring between {today_str} and {reminder_window_str}")
        
        # Scan all galleries (we need to check expiration dates)
        # Note: This is expensive but necessary since expiration is not indexed
        # In production, consider adding a GSI on expiration_date
        all_galleries = []
        last_evaluated_key = None
        
        while True:
            if last_evaluated_key:
                response = galleries_table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = galleries_table.scan()
            
            all_galleries.extend(response.get('Items', []))
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        print(f"Found {len(all_galleries)} total galleries")
        
        # Filter galleries that are expiring soon
        expiring_galleries = []
        for gallery in all_galleries:
            expiration = gallery.get('expiration') or gallery.get('expiry_days')
            
            # Skip if no expiration set
            if not expiration:
                continue
            
            # Handle expiry_days (number of days from creation)
            if isinstance(expiration, (int, float)) or (isinstance(expiration, str) and expiration.isdigit()):
                # Calculate expiration date from creation date
                created_at = gallery.get('created_at', '')
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        expiry_days = int(float(expiration))
                        expiration_date = created_date + timedelta(days=expiry_days)
                        
                        # Check if expiring within reminder window
                        if today <= expiration_date <= reminder_window:
                            expiring_galleries.append({
                                'gallery': gallery,
                                'expiration_date': expiration_date
                            })
                    except Exception as e:
                        print(f" Error parsing expiration for gallery {gallery.get('id')}: {str(e)}")
                        continue
            
            # Handle expiration as ISO date string
            elif isinstance(expiration, str) and 'T' in expiration:
                try:
                    expiration_date = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
                    
                    # Check if expiring within reminder window
                    if today <= expiration_date <= reminder_window:
                        expiring_galleries.append({
                            'gallery': gallery,
                            'expiration_date': expiration_date
                        })
                except Exception as e:
                    print(f" Error parsing expiration date for gallery {gallery.get('id')}: {str(e)}")
                    continue
        
        print(f"Found {len(expiring_galleries)} galleries expiring soon")
        
        # Send reminder emails
        emails_sent = 0
        emails_failed = 0
        
        for item in expiring_galleries:
            gallery = item['gallery']
            expiration_date = item['expiration_date']
            
            try:
                # Get photographer user info
                user_id = gallery.get('user_id')
                if not user_id:
                    print(f" Gallery {gallery.get('id')} missing user_id")
                    continue
                
                # Get user email and name
                user_response = users_table.scan(
                    FilterExpression='id = :id',
                    ExpressionAttributeValues={':id': user_id}
                )
                
                users = user_response.get('Items', [])
                if not users:
                    print(f" User {user_id} not found for gallery {gallery.get('id')}")
                    continue
                
                user = users[0]
                user_email = user.get('email')
                user_name = user.get('name') or user.get('username', 'there')
                
                if not user_email:
                    print(f" User {user_id} has no email")
                    continue
                
                # Prepare gallery URL
                frontend_url = os.environ.get('FRONTEND_URL')
                gallery_url = gallery.get('share_url') or f"{frontend_url}/gallery?id={gallery.get('id')}"
                
                # Format expiration date
                expiration_date_str = expiration_date.strftime('%B %d, %Y')
                
                # Check if photographer has gallery_expiring notifications enabled
                if should_send_notification(user_id, 'gallery_expiring'):
                    # Send reminder email
                    success = send_gallery_expiration_reminder_email(
                        user_email,
                        user_name,
                        gallery.get('name', 'Your gallery'),
                        gallery_url,
                        expiration_date_str
                    )
                    
                    if success:
                        emails_sent += 1
                        print(f"Sent reminder for gallery {gallery.get('id')} to {user_email}")
                    else:
                        emails_failed += 1
                        print(f"Failed to send reminder for gallery {gallery.get('id')}")
                else:
                    print(f"Skipping reminder for gallery {gallery.get('id')} - notifications disabled for photographer {user_id}")
                    
            except Exception as e:
                emails_failed += 1
                print(f"Error processing gallery {gallery.get('id')}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        result = {
            'status': 'completed',
            'galleries_checked': len(all_galleries),
            'galleries_expiring_soon': len(expiring_galleries),
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        print(f"Reminder check completed: {emails_sent} emails sent, {emails_failed} failed")
        return result
        
    except Exception as e:
        print(f"Error in gallery expiration reminder check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

def handle_expire_galleries(event, context):
    """
    DEPRECATED: Galleries no longer expire
    This function is kept for backwards compatibility but does nothing
    """
    print("ℹ️  Gallery expiration is disabled - galleries never expire")
    return create_response(200, {
        'message': 'Gallery expiration feature is disabled',
        'archived_count': 0
    })

def _handle_expire_galleries_DEPRECATED(event, context):
    """
    Scheduled Lambda function to auto-archive expired galleries
    Runs daily via EventBridge/CloudWatch Events
    
    Archives galleries that have passed their expiration date
    """
    try:
        print("🔄 Starting gallery expiration check...")
        
        today = datetime.utcnow()
        today_str = today.isoformat() + 'Z'
        
        # Scan all galleries
        all_galleries = []
        last_evaluated_key = None
        
        while True:
            if last_evaluated_key:
                response = galleries_table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = galleries_table.scan()
            
            all_galleries.extend(response.get('Items', []))
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        expired_galleries = []
        
        for gallery in all_galleries:
            # Skip already archived galleries
            if gallery.get('archived', False):
                continue
            
            expiration = gallery.get('expiration') or gallery.get('expiry_days')
            
            if not expiration:
                continue
            
            expiration_date = None
            
            # Handle expiry_days
            if isinstance(expiration, (int, float)) or (isinstance(expiration, str) and expiration.isdigit()):
                created_at = gallery.get('created_at', '')
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        expiry_days = int(float(expiration))
                        expiration_date = created_date + timedelta(days=expiry_days)
                    except:
                        continue
            
            # Handle expiration as ISO date string
            elif isinstance(expiration, str) and 'T' in expiration:
                try:
                    expiration_date = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
                except:
                    continue
            
            # Check if expired
            if expiration_date and expiration_date < today:
                expired_galleries.append(gallery)
        
        # Archive expired galleries
        archived_count = 0
        for gallery in expired_galleries:
            try:
                gallery['archived'] = True
                gallery['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                galleries_table.put_item(Item=gallery)
                archived_count += 1
                print(f"Archived expired gallery {gallery.get('id')}")
            except Exception as e:
                print(f"Error archiving gallery {gallery.get('id')}: {str(e)}")
        
        result = {
            'status': 'completed',
            'galleries_checked': len(all_galleries),
            'expired_galleries': len(expired_galleries),
            'archived_count': archived_count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        print(f"Expiration check completed: {archived_count} galleries archived")
        return result
        
    except Exception as e:
        print(f"Error in gallery expiration check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

