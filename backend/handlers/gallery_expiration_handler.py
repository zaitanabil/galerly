"""
Gallery Expiration Check Handler
Run this via AWS EventBridge (daily scheduled Lambda)
Checks for galleries expiring soon and sends email notifications
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table
from utils.response import create_response
from handlers.notification_handler import notify_gallery_expiring

def handle_check_expiring_galleries(event, context):
    """
    Check all galleries for upcoming expiration
    Send notifications to clients for galleries expiring in 7 days or less
    
    This function should be triggered daily via AWS EventBridge
    
    Usage:
        - Set up EventBridge rule: rate(1 day)
        - Target: This Lambda function
        - No input needed
    """
    print("🔔 CHECKING EXPIRING GALLERIES")
    
    try:
        # Scan all galleries (consider using GSI if table is large)
        response = galleries_table.scan()
        all_galleries = response.get('Items', [])
        
        # Handle pagination if there are many galleries
        while 'LastEvaluatedKey' in response:
            response = galleries_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            all_galleries.extend(response.get('Items', []))
        
        print(f"Found {len(all_galleries)} total galleries")
        
        current_time = datetime.utcnow()
        notifications_sent = 0
        already_notified = 0
        no_expiry = 0
        
        for gallery in all_galleries:
            try:
                # Skip galleries without expiration
                expiry_days = gallery.get('expiry_days')
                if not expiry_days or expiry_days == 'never' or expiry_days == '':
                    no_expiry += 1
                    continue
                
                # Calculate expiration date
                created_at_str = gallery.get('created_at', '')
                if not created_at_str:
                    continue
                
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    # Try parsing without timezone
                    created_at = datetime.strptime(created_at_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                
                # Calculate expiry date
                expiry_date = created_at + timedelta(days=int(expiry_days))
                days_until_expiry = (expiry_date - current_time).days
                
                # Only notify if expiring in 7 days or less and not already notified
                if 0 <= days_until_expiry <= 7:
                    # Check if already notified (to avoid spam)
                    last_notified = gallery.get('expiry_notification_sent_at')
                    if last_notified:
                        # If already notified in the last 24 hours, skip
                        try:
                            last_notified_dt = datetime.fromisoformat(last_notified.replace('Z', '+00:00'))
                            if (current_time - last_notified_dt).days < 1:
                                already_notified += 1
                                continue
                        except:
                            pass  # If parsing fails, proceed with notification
                    
                    # Get photographer details
                    photographer_id = gallery.get('user_id')
                    client_emails = gallery.get('client_emails', [])
                    
                    if not photographer_id or not client_emails:
                        continue
                    
                    # Get photographer info
                    photographer_response = users_table.get_item(Key={'id': photographer_id})
                    if 'Item' not in photographer_response:
                        continue
                    
                    photographer = photographer_response['Item']
                    photographer_name = photographer.get('name') or photographer.get('username', 'Your photographer')
                    
                    # Send notification to ALL clients
                    gallery_name = gallery.get('name', 'Your gallery')
                    gallery_url = gallery.get('share_url', '')
                    client_name = gallery.get('client_name', 'Client')
                    
                    for client_email in client_emails:
                        try:
                            # Send notification (checks preferences internally)
                            notify_gallery_expiring(
                                user_id=photographer_id,
                                gallery_id=gallery['id'],
                                client_email=client_email,
                                client_name=client_name,
                                photographer_name=photographer_name,
                                gallery_url=gallery_url,
                                days_remaining=days_until_expiry
                            )
                            print(f"✅ Sent expiry notification to {client_email} (Gallery: {gallery_name}, Days: {days_until_expiry})")
                        except Exception as email_error:
                            print(f"❌ Failed to send to {client_email}: {str(email_error)}")
                    
                    # Mark as notified to avoid duplicate notifications
                    galleries_table.update_item(
                        Key={'user_id': photographer_id, 'id': gallery['id']},
                        UpdateExpression="SET expiry_notification_sent_at = :ts",
                        ExpressionAttributeValues={
                            ':ts': current_time.isoformat() + 'Z'
                        }
                    )
                    
                    notifications_sent += 1
                    
            except Exception as gallery_error:
                print(f"❌ Error processing gallery {gallery.get('id')}: {str(gallery_error)}")
                continue
        
        summary = {
            'success': True,
            'total_galleries': len(all_galleries),
            'notifications_sent': notifications_sent,
            'already_notified': already_notified,
            'no_expiry_set': no_expiry,
            'timestamp': current_time.isoformat() + 'Z'
        }
        
        print(f"✅ Expiry check complete: {summary}")
        return create_response(200, summary)
        
    except Exception as e:
        print(f"❌ Error checking expiring galleries: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': str(e)})


def handle_manual_expiry_check(user):
    """
    Manual trigger for testing (photographer can trigger this)
    Only checks galleries owned by the requesting photographer
    """
    print(f"🔔 MANUAL EXPIRY CHECK: user_id={user['id']}")
    
    try:
        # Get only this photographer's galleries
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        photographer_galleries = response.get('Items', [])
        
        print(f"Found {len(photographer_galleries)} galleries for photographer {user['id']}")
        
        current_time = datetime.utcnow()
        notifications_sent = 0
        
        for gallery in photographer_galleries:
            try:
                # Skip galleries without expiration
                expiry_days = gallery.get('expiry_days')
                if not expiry_days or expiry_days == 'never' or expiry_days == '':
                    continue
                
                # Calculate expiration date
                created_at_str = gallery.get('created_at', '')
                if not created_at_str:
                    continue
                
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    created_at = datetime.strptime(created_at_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                
                # Calculate expiry date
                expiry_date = created_at + timedelta(days=int(expiry_days))
                days_until_expiry = (expiry_date - current_time).days
                
                # Only notify if expiring in 7 days or less
                if 0 <= days_until_expiry <= 7:
                    # Send to all clients
                    client_emails = gallery.get('client_emails', [])
                    photographer_name = user.get('name') or user.get('username', 'Your photographer')
                    
                    for client_email in client_emails:
                        try:
                            notify_gallery_expiring(
                                user_id=user['id'],
                                gallery_id=gallery['id'],
                                client_email=client_email,
                                client_name=gallery.get('client_name', 'Client'),
                                photographer_name=photographer_name,
                                gallery_url=gallery.get('share_url', ''),
                                days_remaining=days_until_expiry
                            )
                            notifications_sent += 1
                        except Exception as email_error:
                            print(f"❌ Failed to send to {client_email}: {str(email_error)}")
                
            except Exception as gallery_error:
                print(f"❌ Error processing gallery: {str(gallery_error)}")
                continue
        
        return create_response(200, {
            'success': True,
            'notifications_sent': notifications_sent,
            'message': f'Sent {notifications_sent} expiry notification(s)'
        })
        
    except Exception as e:
        print(f"❌ Error in manual expiry check: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': str(e)})

