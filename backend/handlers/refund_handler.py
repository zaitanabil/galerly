"""
Refund policy enforcement and request handling
Refund rules:
- 14 days from initial purchase
- Free plan: N/A (no refunds needed)
- Starter → Plus: No refund if used > 5GB OR > 5 galleries
- Starter → Pro (direct): No refund if used > 5GB OR > 5 galleries
- Plus → Pro: No refund if used > 50GB
- Service considered "consumed" if limits exceeded
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, subscriptions_table, users_table, dynamodb, get_required_env
from utils.response import create_response

# Initialize refunds table
refunds_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_REFUNDS'))


def get_upgrade_path(user_id, subscription_created_at):
    """
    Determine the user's upgrade path by checking audit log
    Returns: 'starter_to_plus', 'starter_to_pro', 'plus_to_pro', or 'unknown'
    """
    try:
        from utils.audit_log import get_user_subscription_history
        
        # Get subscription history
        history = get_user_subscription_history(user_id, limit=50)
        
        if not history:
            # No history found, check current plan to make best guess
            return 'unknown'
        
        # Filter history to only entries after subscription created
        try:
            sub_date = datetime.fromisoformat(subscription_created_at.replace('Z', '+00:00'))
            relevant_history = [
                h for h in history 
                if datetime.fromisoformat(h.get('timestamp', '').replace('Z', '+00:00')) >= sub_date
            ]
        except:
            relevant_history = history
        
        # Look for upgrade actions
        upgrades = [h for h in relevant_history if h.get('action') in ['upgrade', 'checkout_completed']]
        
        if not upgrades:
            return 'unknown'
        
        # Get first upgrade (most recent due to sort order)
        first_upgrade = upgrades[-1] if upgrades else None
        
        if not first_upgrade:
            return 'unknown'
        
        from_plan = first_upgrade.get('from_plan', 'none').lower()
        to_plan = first_upgrade.get('to_plan', '').lower()
        
        # Normalize plan names
        if from_plan in ['none', 'free', 'starter']:
            from_plan = 'starter'
        if to_plan in ['professional']:
            to_plan = 'plus'
        if to_plan in ['business']:
            to_plan = 'pro'
        
        # Determine path
        if from_plan == 'starter' and to_plan == 'plus':
            return 'starter_to_plus'
        elif from_plan == 'starter' and to_plan == 'pro':
            return 'starter_to_pro'
        elif from_plan == 'plus' and to_plan == 'pro':
            return 'plus_to_pro'
        
        # Check if user had plus before going to pro
        has_plus_history = any(
            h.get('to_plan', '').lower() in ['plus', 'professional'] 
            for h in relevant_history
        )
        
        if to_plan == 'pro' and has_plus_history:
            return 'plus_to_pro'
        elif to_plan == 'pro' and not has_plus_history:
            return 'starter_to_pro'
        elif to_plan == 'plus':
            return 'starter_to_plus'
        
        return 'unknown'
        
    except Exception as e:
        print(f"⚠️  Error determining upgrade path: {str(e)}")
        return 'unknown'


def check_refund_eligibility(user):
    """
    Check if user is eligible for refund based on:
    1. No existing pending or approved refund
    2. Time since initial purchase (14 days)
    3. Usage limits based on upgrade path
    """
    try:
        # Check if user already has a pending or approved refund
        existing_refunds = refunds_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='#status IN (:pending, :approved)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':uid': user['id'],
                ':pending': 'pending',
                ':approved': 'approved'
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        if existing_refunds.get('Items'):
            existing_refund = existing_refunds['Items'][0]
            return {
                'eligible': False,
                'reason': f'You already have a {existing_refund.get("status", "pending")} refund request',
                'details': {
                    'refund_id': existing_refund.get('id'),
                    'status': existing_refund.get('status'),
                    'created_at': existing_refund.get('created_at')
                }
            }
        
        # Get current subscription
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response.get('Items'):
            return {
                'eligible': False,
                'reason': 'No active subscription found',
                'details': {}
            }
        
        subscription = response['Items'][0]
        
        # Check if already on free plan
        user_email = user.get('email')
        if user_email:
            user_response = users_table.get_item(Key={'email': user_email})
            if 'Item' in user_response:
                current_plan = user_response['Item'].get('subscription', 'free')
            else:
                current_plan = user.get('subscription', 'free')
        else:
            current_plan = user.get('subscription', 'free')
        
        if current_plan == 'free':
            return {
                'eligible': False,
                'reason': 'Already on Starter plan (no refund needed)',
                'details': {}
            }
        
        # Check if subscription was created within 14 days
        created_at = subscription.get('created_at', '')
        if not created_at:
            return {
                'eligible': False,
                'reason': 'Unable to determine subscription creation date',
                'details': {}
            }
        
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_since_purchase = (datetime.utcnow() - created_date.replace(tzinfo=None)).days
        except Exception as e:
            print(f"⚠️  Error parsing created_at: {str(e)}")
            return {
                'eligible': False,
                'reason': 'Unable to determine subscription age',
                'details': {}
            }
        
        if days_since_purchase > 14:
            return {
                'eligible': False,
                'reason': f'Subscription is {days_since_purchase} days old (refund window is 14 days)',
                'details': {
                    'days_since_purchase': days_since_purchase,
                    'purchase_date': created_at
                }
            }
        
        # Get usage statistics
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        all_galleries = galleries_response.get('Items', [])
        
        # Calculate storage usage
        total_storage_mb = sum(float(g.get('storage_used', 0)) for g in all_galleries)
        total_storage_gb = total_storage_mb / 1024
        
        # Count galleries created since subscription
        galleries_since_purchase = sum(
            1 for g in all_galleries 
            if g.get('created_at', '') >= created_at
        )
        
        # Determine eligibility based on plan and usage
        # Refund rules:
        # - Starter → Plus: No refund if used > 5GB OR > 5 galleries
        # - Starter → Pro (direct): No refund if used > 5GB OR > 5 galleries
        # - Plus → Pro: No refund if used > 50GB
        
        # Get upgrade path to determine correct limits
        upgrade_path = get_upgrade_path(user['id'], created_at)
        
        details = {
            'days_since_purchase': days_since_purchase,
            'purchase_date': created_at,
            'current_plan': current_plan,
            'total_storage_gb': Decimal(str(round(total_storage_gb, 2))),
            'galleries_since_purchase': galleries_since_purchase,
            'total_galleries': len(all_galleries),
            'upgrade_path': upgrade_path
        }
        
        print(f"🔍 Refund check: User {user['id']} | Plan: {current_plan} | Path: {upgrade_path} | Usage: {total_storage_gb:.2f}GB, {galleries_since_purchase} galleries")
        
        # Apply refund rules based on current plan and upgrade path
        if current_plan in ['plus', 'professional']:
            # Plus plan: Always check Starter limits (5GB, 5 galleries)
            # Since Plus can only come from Starter
            if total_storage_gb > 5 or galleries_since_purchase > 5:
                return {
                    'eligible': False,
                    'reason': f'Service consumed: Used {total_storage_gb:.2f} GB and created {galleries_since_purchase} galleries (Starter limit: 5 GB, 5 galleries)',
                    'details': details
                }
        
        elif current_plan in ['pro', 'business']:
            # Pro plan: Check based on upgrade path
            
            if upgrade_path == 'plus_to_pro':
                # Plus → Pro: Check Plus limits (50GB)
                # User already paid for Plus, so don't check Starter limits
                if total_storage_gb > 50:
                    return {
                        'eligible': False,
                        'reason': f'Service consumed: Used {total_storage_gb:.2f} GB (Plus limit: 50 GB)',
                        'details': details
                    }
            
            elif upgrade_path == 'starter_to_pro':
                # Starter → Pro (direct): Check Starter limits (5GB, 5 galleries)
                # User went straight from free to Pro, never paid for Plus
                if total_storage_gb > 5 or galleries_since_purchase > 5:
                    return {
                        'eligible': False,
                        'reason': f'Service consumed: Used {total_storage_gb:.2f} GB and created {galleries_since_purchase} galleries (Starter limit: 5 GB, 5 galleries for direct Starter→Pro upgrade)',
                        'details': details
                    }
            
            else:
                # Unknown path: Apply most restrictive rules for safety
                # Check both Starter limits (for direct upgrade) and Plus limits (for Plus→Pro)
                # This ensures we don't give refunds incorrectly
                
                if total_storage_gb > 50:
                    # Definitely exceeded Plus limits
                    return {
                        'eligible': False,
                        'reason': f'Service consumed: Used {total_storage_gb:.2f} GB (Plus limit: 50 GB)',
                        'details': details
                    }
                elif total_storage_gb > 5 or galleries_since_purchase > 5:
                    # Exceeded Starter limits but under Plus limits
                    # Could be direct Starter→Pro or Plus→Pro with usage under 50GB
                    # Since we can't determine path, note this in the reason for admin review
                    return {
                        'eligible': False,
                        'reason': f'Service consumed: Used {total_storage_gb:.2f} GB and created {galleries_since_purchase} galleries (Starter limit: 5 GB, 5 galleries). Note: Unable to determine upgrade path, admin review recommended.',
                        'details': details
                    }
        
        # Eligible for refund
        return {
            'eligible': True,
            'reason': 'Eligible for refund (within 14 days, usage within limits)',
            'details': details
        }
        
    except Exception as e:
        print(f"❌ Error checking refund eligibility: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'eligible': False,
            'reason': f'Error checking eligibility: {str(e)}',
            'details': {}
        }


def handle_check_refund_eligibility(user):
    """API handler to check refund eligibility"""
    result = check_refund_eligibility(user)
    return create_response(200, result)


def cancel_pending_refunds(user_id):
    """
    Cancel any pending refund requests for a user (called during reactivation)
    
    Args:
        user_id: User ID
    
    Returns:
        Number of refunds cancelled
    """
    try:
        # Find all pending refunds for user
        response = refunds_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='#status = :pending',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':pending': 'pending'
            }
        )
        
        refunds = response.get('Items', [])
        cancelled_count = 0
        
        for refund in refunds:
            try:
                # Update refund status to cancelled
                refunds_table.update_item(
                    Key={'id': refund['id']},
                    UpdateExpression='SET #status = :cancelled, updated_at = :now, cancellation_reason = :reason',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':cancelled': 'cancelled',
                        ':now': datetime.utcnow().isoformat() + 'Z',
                        ':reason': 'User reactivated subscription'
                    }
                )
                print(f"✅ Cancelled refund {refund['id']} due to subscription reactivation")
                cancelled_count += 1
                
                # Log the cancellation
                try:
                    from utils.audit_log import log_audit
                    log_audit(
                        user_id=user_id,
                        action='refund_cancelled',
                        details={
                            'refund_id': refund['id'],
                            'reason': 'User reactivated subscription',
                            'original_amount': str(refund.get('amount', 0))
                        }
                    )
                except Exception as e:
                    print(f"⚠️  Error logging refund cancellation: {str(e)}")
                    
            except Exception as e:
                print(f"⚠️  Error cancelling refund {refund.get('id')}: {str(e)}")
        
        return cancelled_count
        
    except Exception as e:
        print(f"❌ Error in cancel_pending_refunds: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def has_pending_or_approved_refund(user_id):
    """
    Check if user has a pending or approved refund request (internal helper)
    
    Args:
        user_id: User ID to check
    
    Returns:
        Boolean indicating if user has pending/approved refund
    """
    try:
        response = refunds_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='#status IN (:pending, :approved)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':pending': 'pending',
                ':approved': 'approved'
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        refunds = response.get('Items', [])
        return len(refunds) > 0
    except Exception as e:
        print(f"⚠️  Error checking refund status for user {user_id}: {str(e)}")
        return False


def handle_get_refund_status(user):
    """
    Check if user has a pending or approved refund request
    """
    try:
        print(f"🔍 Checking refund status for user: {user['id']}")
        response = refunds_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='#status IN (:pending, :approved)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':uid': user['id'],
                ':pending': 'pending',
                ':approved': 'approved'
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        refunds = response.get('Items', [])
        print(f"📋 Found {len(refunds)} pending/approved refunds")
        
        if refunds:
            refund = refunds[0]
            print(f"✅ Refund found: {refund.get('id')} - Status: {refund.get('status')}")
            return create_response(200, {
                'has_pending_refund': True,
                'refund_id': refund.get('id'),
                'status': refund.get('status'),
                'created_at': refund.get('created_at'),
                'reason': refund.get('reason')
            })
        
        print(f"ℹ️  No pending/approved refunds found for user {user['id']}")
        return create_response(200, {
            'has_pending_refund': False
        })
    except Exception as e:
        print(f"❌ Error getting refund status: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get refund status'})


def handle_request_refund(user, body):
    """
    Submit a refund request
    Admin will review and process manually
    """
    try:
        reason = body.get('reason', '')
        
        if not reason or len(reason) < 10:
            return create_response(400, {
                'error': 'Please provide a detailed reason for the refund request (minimum 10 characters)'
            })
        
        # Check eligibility
        eligibility = check_refund_eligibility(user)
        
        if not eligibility['eligible']:
            return create_response(400, {
                'error': 'Not eligible for refund',
                'reason': eligibility['reason'],
                'details': eligibility['details']
            })
        
        # Get subscription details
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response.get('Items'):
            return create_response(400, {'error': 'No active subscription found'})
        
        subscription = response['Items'][0]
        
        # Check if refund already requested
        existing_refunds = refunds_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='#status IN (:pending, :approved)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':uid': user['id'],
                ':pending': 'pending',
                ':approved': 'approved'
            }
        )
        
        if existing_refunds.get('Items'):
            return create_response(400, {
                'error': 'Refund request already exists',
                'status': existing_refunds['Items'][0]['status']
            })
        
        # Create refund request
        import uuid
        refund_id = str(uuid.uuid4())
        
        refund_request = {
            'id': refund_id,
            'user_id': user['id'],
            'user_email': user.get('email', ''),
            'subscription_id': subscription.get('id'),
            'stripe_subscription_id': subscription.get('stripe_subscription_id'),
            'plan': subscription.get('plan', 'unknown'),
            'reason': reason,
            'status': 'pending',  # pending, approved, rejected, processed
            'eligibility_details': eligibility['details'],
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        refunds_table.put_item(Item=refund_request)
        
        print(f"✅ Created refund request {refund_id} for user {user['id']}")
        
        # Send notification email to admin
        try:
            from utils.email import send_admin_refund_request_notification
            send_admin_refund_request_notification(
                refund_id,
                user.get('email', ''),
                user.get('username', ''),
                subscription.get('plan', 'unknown'),
                reason,
                eligibility['details']
            )
        except Exception as e:
            print(f"⚠️  Error sending admin notification: {str(e)}")
        
        # Send confirmation email to user
        try:
            from utils.email import send_refund_request_confirmation_email
            send_refund_request_confirmation_email(
                user.get('email', ''),
                user.get('username', ''),
                refund_id
            )
        except Exception as e:
            print(f"⚠️  Error sending user confirmation: {str(e)}")
        
        return create_response(200, {
            'message': 'Refund request submitted successfully. Our team will review and respond within 2-3 business days.',
            'refund_id': refund_id,
            'status': 'pending'
        })
        
    except Exception as e:
        print(f"❌ Error requesting refund: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to submit refund request'})

