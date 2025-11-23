"""
Billing and payment handlers - Stripe integration
"""
import os
import uuid
from datetime import datetime
from decimal import Decimal
from utils.config import users_table, billing_table, subscriptions_table
from utils.response import create_response

# Initialize Stripe
stripe = None
STRIPE_SECRET_KEY = ''
STRIPE_WEBHOOK_SECRET = ''

try:
    import stripe
    print("✅ Stripe module imported successfully")
    
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    print(f"🔍 STRIPE_SECRET_KEY present: {bool(STRIPE_SECRET_KEY)}")
    print(f"🔍 STRIPE_SECRET_KEY length: {len(STRIPE_SECRET_KEY) if STRIPE_SECRET_KEY else 0}")
    print(f"🔍 STRIPE_WEBHOOK_SECRET present: {bool(STRIPE_WEBHOOK_SECRET)}")
    
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        print("✅ Stripe API key configured")
    else:
        print("⚠️  STRIPE_SECRET_KEY not set in environment variables")
        stripe = None
except ImportError as e:
    stripe = None
    print(f"❌ Stripe import error: {str(e)}")
    print("⚠️  Stripe not installed. Install with: pip install stripe")
except Exception as e:
    stripe = None
    print(f"❌ Error initializing Stripe: {str(e)}")
    import traceback
    print(traceback.format_exc())

# Plan configurations
PLANS = {
    'free': {
        'name': 'Starter',
        'price': 0,
        'stripe_price_id': None,
        'galleries_per_month': 5,
        'storage_gb': 5,
        'features': [
            '5 galleries per month',
            '5 GB storage',
            'Client downloads',
            'Photo approval',
            'Comments & feedback',
            'Email notifications',
            'Public profile',
            'Basic analytics'
        ]
    },
    'plus': {
        'name': 'Plus',
        'price': 12,
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PLUS', ''),
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 50,
        'features': [
            'Unlimited galleries',
            '50 GB storage',
            'Video support (30 min, up to HD)',
            'Priority email support',
            'All Starter features',
            'Batch photo uploads',
            'Advanced analytics',
            'Custom notifications'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 24,
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PRO', ''),
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 200,
        'features': [
            'Unlimited galleries',
            '200 GB storage',
            'Video support (2 hours, up to 4K)',
            'Priority support (12-24h)',
            'Phone/video support',
            'All Plus features',
            'Custom email branding',
            'Analytics exports',
            'Gallery templates'
        ]
    },
    # Legacy plan names for backward compatibility
    'professional': {
        'name': 'Plus',
        'price': 12,
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PLUS', ''),
        'galleries_per_month': -1,
        'storage_gb': 50,
        'features': [
            'Unlimited galleries',
            '50 GB storage',
            'Priority email support',
            'All Starter features'
        ]
    },
    'business': {
        'name': 'Pro',
        'price': 24,
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PRO', ''),
        'galleries_per_month': -1,
        'storage_gb': 200,
        'features': [
            'Unlimited galleries',
            '200 GB storage',
            'Priority support',
            'All Plus features'
        ]
    }
}

def handle_change_plan(user, body):
    """Change subscription plan between paid plans (Plus <-> Pro)"""
    plan_id = body.get('plan', 'plus')
    
    if plan_id not in PLANS:
        return create_response(400, {'error': 'Invalid plan'})
    
    plan = PLANS[plan_id]
    
    if plan_id == 'free':
        return create_response(400, {'error': 'Use downgrade endpoint for free plan'})
    
    if not plan['stripe_price_id']:
        return create_response(500, {
            'error': 'Plan not configured',
            'message': f'Stripe Price ID for {plan_id} plan is not configured.'
        })
    
    if not stripe:
        return create_response(500, {'error': 'Stripe not configured'})
    
    try:
        # Get current subscription with lock to prevent race conditions
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
        stripe_subscription_id = subscription.get('stripe_subscription_id')
        
        if not stripe_subscription_id:
            return create_response(400, {'error': 'No Stripe subscription found'})
        
        # Check if subscription is processing a change (race condition prevention)
        if subscription.get('processing_change', False):
            return create_response(409, {
                'error': 'Subscription change in progress',
                'message': 'Please wait a moment and try again. Your subscription is currently being updated.'
            })
        
        # Set processing flag to prevent concurrent modifications
        try:
            subscriptions_table.update_item(
                Key={'id': subscription['id']},
                UpdateExpression='SET processing_change = :true, updated_at = :now',
                ConditionExpression='attribute_not_exists(processing_change) OR processing_change = :false',
                ExpressionAttributeValues={
                    ':true': True,
                    ':false': False,
                    ':now': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except Exception as e:
            # Condition failed - another change is in progress
            if 'ConditionalCheckFailedException' in str(type(e)):
                return create_response(409, {
                    'error': 'Subscription change in progress',
                    'message': 'Please wait a moment and try again.'
                })
            raise
        
        try:
            # Get current plan from user
            user_email = user.get('email')
            if user_email:
                user_response = users_table.get_item(Key={'email': user_email})
                if 'Item' in user_response:
                    # Use 'plan' field (new), fallback to 'subscription' (legacy)
                    current_plan = user_response['Item'].get('plan', user_response['Item'].get('subscription', 'free'))
                else:
                    current_plan = user.get('plan', user.get('subscription', 'free'))
            else:
                current_plan = user.get('plan', user.get('subscription', 'free'))
            
            # Check for pending plan change
            pending_plan = subscription.get('pending_plan')
            
            # Special case: If user has pending_plan='free' (canceled) but wants to return to their current plan
            # This is a "reactivation" - allow it even if current_plan == plan_id
            is_reactivation = (
                pending_plan == 'free' and 
                current_plan == plan_id and 
                current_plan in ['professional', 'business', 'plus', 'pro']  # Support both legacy and new plan names
            )
            
            # Check if it's actually a change (not same plan)
            # If there's a pending_plan, check against that instead of current_plan
            # This allows users to change from a scheduled downgrade to another plan
            effective_plan = pending_plan if pending_plan else current_plan
            
            # Allow reactivation (returning to current plan after cancellation)
            if effective_plan == plan_id and not is_reactivation:
                # Release processing lock
                subscriptions_table.update_item(
                    Key={'id': subscription['id']},
                    UpdateExpression='SET processing_change = :false',
                    ExpressionAttributeValues={':false': False}
                )
                return create_response(400, {'error': 'Already on this plan or scheduled for this plan'})
            
            # If user has a pending plan change, allow them to change to a different plan
            # This will replace the pending plan change
            
            # Check if downgrading to free (should use downgrade endpoint)
            if plan_id == 'free':
                # Release processing lock
                subscriptions_table.update_item(
                    Key={'id': subscription['id']},
                    UpdateExpression='SET processing_change = :false',
                    ExpressionAttributeValues={':false': False}
                )
                return create_response(400, {'error': 'Use downgrade endpoint for free plan'})
            
            # Retrieve current Stripe subscription
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Get current price ID from subscription
            current_price_id = stripe_sub['items']['data'][0]['price']['id']
            new_price_id = plan['stripe_price_id']
            
            # Determine what price ID should match the current plan
            current_plan_price_id = PLANS.get(current_plan, {}).get('stripe_price_id')
            
            # Check if Stripe price matches the requested plan
            # But also check if Stripe price matches current plan - if not, allow change
            # This handles cases where Stripe was modified but user plan wasn't updated yet
            if current_price_id == new_price_id:
                # Price matches requested plan, but check if it also matches current plan
                # If current plan price doesn't match Stripe price, allow change (Stripe was modified)
                if current_plan_price_id and current_price_id == current_plan_price_id:
                    # Both match - user is already on this plan
                    # Release processing lock
                    subscriptions_table.update_item(
                        Key={'id': subscription['id']},
                        UpdateExpression='SET processing_change = :false',
                        ExpressionAttributeValues={':false': False}
                    )
                    return create_response(400, {'error': 'Already on this plan'})
                # Stripe price matches requested plan but not current plan - this is a valid change
                print(f"🔄 Stripe price ({current_price_id}) matches requested plan but not current plan ({current_plan}), allowing change")
            
            # Determine if this is an upgrade or downgrade
            # Compare against current plan (not pending plan) for pricing logic
            current_price = PLANS.get(current_plan, {}).get('price', 0)
            new_price = plan.get('price', 0)
            is_downgrade = new_price < current_price
            
            # If this is a reactivation (returning to current plan after cancellation), handle it separately
            # This avoids currency mismatch errors by not changing the price
            if is_reactivation:
                print(f"🔄 Reactivating subscription: returning to {plan_id} plan (canceling scheduled downgrade to Starter)")
                
                # Clear pending plan change
                subscription['pending_plan'] = None
                subscription['pending_plan_change_at'] = None
                
                # Reactivate subscription by removing cancel_at_period_end (without changing price)
                try:
                    # Retrieve fresh subscription data
                    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    
                    # For reactivation, just remove cancel_at_period_end without changing the price
                    # This preserves the existing currency and price, avoiding currency mismatch errors
                    stripe.Subscription.modify(
                        stripe_subscription_id,
                        cancel_at_period_end=False
                    )
                    subscription['cancel_at_period_end'] = False
                    subscription['status'] = 'active'  # Update status to active
                    subscription['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                    subscription['processing_change'] = False  # Release lock
                    subscriptions_table.put_item(Item=subscription)
                    print(f"✅ Reactivated subscription {stripe_subscription_id} (removed cancel_at_period_end)")
                    
                    # Update user plan immediately for reactivation
                    try:
                        if user_email:
                            users_table.update_item(
                                Key={'email': user_email},
                                UpdateExpression='SET #plan = :plan_val, subscription = :plan_val, updated_at = :now',
                                ExpressionAttributeNames={'#plan': 'plan'},
                                ExpressionAttributeValues={
                                    ':plan_val': plan_id,
                                    ':now': datetime.utcnow().isoformat() + 'Z'
                                }
                            )
                            print(f"✅ Updated user {user_email} to plan {plan_id} (reactivation)")
                    except Exception as e:
                        print(f"⚠️  Error updating user plan: {str(e)}")
                    
                    # Log the reactivation
                    try:
                        from utils.audit_log import log_subscription_change
                        log_subscription_change(
                            user_id=user['id'],
                            action='reactivation',
                            from_plan=pending_plan or 'free',
                            to_plan=plan_id,
                            metadata={'stripe_subscription_id': stripe_subscription_id}
                        )
                    except Exception as e:
                        print(f"⚠️  Error logging reactivation: {str(e)}")
                    
                    # Return success response for reactivation
                    return create_response(200, {
                        'message': f'Subscription reactivated successfully. Your {plan_id} plan is now active again.',
                        'plan': plan_id,
                        'subscription_id': stripe_subscription_id,
                        'reactivated': True
                    })
                except Exception as e:
                    # Release processing lock on error
                    subscriptions_table.update_item(
                        Key={'id': subscription['id']},
                        UpdateExpression='SET processing_change = :false',
                        ExpressionAttributeValues={':false': False}
                    )
                    print(f"⚠️  Error reactivating subscription: {str(e)}")
                    error_type = type(e).__name__
                    error_msg = str(e) if e else 'Unknown error'
                    if hasattr(e, 'user_message'):
                        error_msg = e.user_message
                    elif hasattr(e, 'message'):
                        error_msg = e.message
                    return create_response(500, {
                        'error': 'Failed to reactivate subscription',
                        'message': error_msg,
                        'type': error_type
                    })
            
            # If there was a pending plan change, clear it since we're changing to a new plan
            # Also cancel any scheduled cancellation in Stripe if user is changing to a paid plan
            if pending_plan:
                print(f"🔄 Clearing pending plan change from {pending_plan} to {plan_id}")
                subscription['pending_plan'] = None
                subscription['pending_plan_change_at'] = None
                
                # If user had canceled (pending_plan was 'free'), reactivate subscription
                if pending_plan == 'free' and stripe:
                    try:
                        # Retrieve fresh subscription data
                        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                        if stripe_sub.get('cancel_at_period_end', False):
                            # Remove cancel_at_period_end
                            stripe.Subscription.modify(
                                stripe_subscription_id,
                                cancel_at_period_end=False
                            )
                            subscription['cancel_at_period_end'] = False
                            subscription['status'] = 'active'
                            print(f"✅ Removed cancel_at_period_end from subscription {stripe_subscription_id}")
                    except Exception as e:
                        print(f"⚠️  Error removing cancel_at_period_end: {str(e)}")
            
            if is_downgrade:
                # Check downgrade limits before proceeding
                print(f"🔍 Checking downgrade limits for {current_plan} → {plan_id}")
                limit_check = handle_check_downgrade_limits(user, plan_id)
                
                if limit_check['statusCode'] == 200:
                    limit_data = limit_check['body'] if isinstance(limit_check['body'], dict) else {}
                    can_downgrade = limit_data.get('can_downgrade', True)
                    issues = limit_data.get('issues', [])
                    
                    if not can_downgrade:
                        # User exceeds target plan limits
                        # Release processing lock
                        subscriptions_table.update_item(
                            Key={'id': subscription['id']},
                            UpdateExpression='SET processing_change = :false',
                            ExpressionAttributeValues={':false': False}
                        )
                        
                        target_plan_name = limit_data.get('target_plan_name', plan_id)
                        issues_text = '\n'.join([issue['message'] for issue in issues])
                        
                        return create_response(400, {
                            'error': 'Cannot downgrade',
                            'message': f'You cannot downgrade to {target_plan_name} plan because you exceed its limits.\n\n{issues_text}\n\nPlease delete some galleries or photos to free up resources, then try again.',
                            'issues': issues,
                            'current_usage': limit_data.get('current_usage', {}),
                            'target_limits': limit_data.get('target_limits', {})
                        })
                
                # For downgrades, schedule change at period end
                # Store pending plan change in subscription record
                subscription['pending_plan'] = plan_id
                subscription['pending_plan_change_at'] = stripe_sub.get('current_period_end')
                subscription['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                subscription['processing_change'] = False  # Release lock
                subscriptions_table.put_item(Item=subscription)
                
                # Schedule subscription modification at period end
                # Modify subscription to change plan, but use proration_behavior='none'
                # This will schedule the change for the next billing cycle
                updated_subscription = stripe.Subscription.modify(
                    stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0]['id'],
                        'price': new_price_id,
                    }],
                    proration_behavior='none',  # No immediate proration, change at period end
                    metadata={
                        'user_id': user['id'],
                        'plan': plan_id,
                        'previous_plan': current_plan,
                        'pending_change': 'true'
                    }
                )
                
                print(f"✅ Scheduled subscription {stripe_subscription_id} change from {current_plan} to {plan_id} at period end")
                
                # Log the downgrade
                try:
                    from utils.audit_log import log_subscription_change
                    log_subscription_change(
                        user_id=user['id'],
                        action='downgrade_scheduled',
                        from_plan=current_plan,
                        to_plan=plan_id,
                        effective_at=stripe_sub.get('current_period_end'),
                        metadata={'stripe_subscription_id': stripe_subscription_id}
                    )
                except Exception as e:
                    print(f"⚠️  Error logging downgrade: {str(e)}")
                
                # Send downgrade confirmation email
                try:
                    from utils.email import send_subscription_downgraded_email
                    plan_details = PLANS.get(plan_id, {})
                    plan_name = plan_details.get('name', plan_id.capitalize())
                    period_end_timestamp = stripe_sub.get('current_period_end', 0)
                    if period_end_timestamp:
                        period_end_date = datetime.fromtimestamp(period_end_timestamp).strftime('%B %d, %Y')
                    else:
                        period_end_date = 'the end of your billing period'
                    
                    user_email = user.get('email', '')
                    user_name = user.get('username') or user.get('name') or ''
                    if user_email:
                        send_subscription_downgraded_email(user_email, user_name, plan_name, period_end_date)
                except Exception as e:
                    print(f"⚠️  Error sending downgrade email: {str(e)}")
                
                # DO NOT update user plan immediately - keep current plan active
                # The plan will change automatically at period end via webhook
                
                return create_response(200, {
                    'message': f'Plan change scheduled. You will be downgraded to {plan_id} at the end of your current billing period.',
                    'current_plan': current_plan,
                    'pending_plan': plan_id,
                    'effective_at': datetime.fromtimestamp(stripe_sub.get('current_period_end', 0)).isoformat() + 'Z' if stripe_sub.get('current_period_end') else None,
                    'scheduled': True
                })
            else:
                # For upgrades, apply immediately with proration
                updated_subscription = stripe.Subscription.modify(
                    stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0]['id'],
                        'price': new_price_id,
                    }],
                    proration_behavior='always_invoice',  # Immediate proration for upgrades
                    metadata={
                        'user_id': user['id'],
                        'plan': plan_id,
                        'previous_plan': current_plan
                    }
                )
                
                print(f"✅ Modified subscription {stripe_subscription_id} from {current_plan} to {plan_id} (upgrade)")
                
                # Update user plan immediately for upgrades
                try:
                    if user_email:
                        users_table.update_item(
                            Key={'email': user_email},
                            UpdateExpression='SET #plan = :plan_val, subscription = :plan_val, updated_at = :now',
                            ExpressionAttributeNames={'#plan': 'plan'},
                            ExpressionAttributeValues={
                                ':plan_val': plan_id,
                                ':now': datetime.utcnow().isoformat() + 'Z'
                            }
                        )
                        print(f"✅ Updated user {user_email} to plan {plan_id} (immediate upgrade)")
                except Exception as e:
                    print(f"⚠️  Error updating user plan: {str(e)}")
                
                # Update subscription record
                try:
                    subscription['plan'] = plan_id
                    subscription['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                    subscription['processing_change'] = False  # Release lock
                    subscriptions_table.put_item(Item=subscription)
                    print(f"✅ Updated subscription record to plan {plan_id}")
                except Exception as e:
                    print(f"⚠️  Error updating subscription record: {str(e)}")
                
                # Log the upgrade
                try:
                    from utils.audit_log import log_subscription_change
                    log_subscription_change(
                        user_id=user['id'],
                        action='upgrade',
                        from_plan=current_plan,
                        to_plan=plan_id,
                        metadata={'stripe_subscription_id': stripe_subscription_id, 'prorated': True}
                    )
                except Exception as e:
                    print(f"⚠️  Error logging upgrade: {str(e)}")
                
                # Customize message for reactivation
                if is_reactivation:
                    message = f'Subscription reactivated successfully. Your {plan_id} plan is now active again.'
                else:
                    message = f'Plan upgraded successfully from {current_plan} to {plan_id}'
                
                return create_response(200, {
                    'message': message,
                    'plan': plan_id,
                    'subscription_id': stripe_subscription_id,
                    'prorated': True,
                    'reactivated': is_reactivation
                })
        
        except Exception as inner_e:
            # Release processing lock on any error within the try block
            try:
                subscriptions_table.update_item(
                    Key={'id': subscription['id']},
                    UpdateExpression='SET processing_change = :false',
                    ExpressionAttributeValues={':false': False}
                )
            except:
                pass
            raise inner_e
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e) if e else 'Unknown error'
        
        if hasattr(e, 'user_message'):
            error_msg = e.user_message
        elif hasattr(e, 'message'):
            error_msg = e.message
        
        print(f"❌ Error changing plan ({error_type}): {error_msg}")
        import traceback
        traceback.print_exc()
        
        return create_response(500, {
            'error': 'Failed to change plan',
            'message': error_msg,
            'type': error_type
        })


def handle_create_checkout_session(user, body):
    """Create Stripe checkout session for subscription"""
    plan_id = body.get('plan', 'plus')
    
    if plan_id not in PLANS:
        return create_response(400, {'error': 'Invalid plan'})
    
    plan = PLANS[plan_id]
    
    if plan_id == 'free':
        return create_response(400, {'error': 'Free plan does not require payment'})
    
    # Check if user already has a paid subscription - if so, use plan change instead
    try:
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=1
        )
        
        if response.get('Items'):
            subscription = response['Items'][0]
            stripe_subscription_id = subscription.get('stripe_subscription_id')
            
            # Get current plan
            user_email = user.get('email')
            if user_email:
                user_response = users_table.get_item(Key={'email': user_email})
                if 'Item' in user_response:
                    # Use 'plan' field (new), fallback to 'subscription' (legacy)
                    current_plan = user_response['Item'].get('plan', user_response['Item'].get('subscription', 'free'))
                else:
                    current_plan = user.get('plan', user.get('subscription', 'free'))
            else:
                current_plan = user.get('plan', user.get('subscription', 'free'))
            
            # If user has a paid plan and wants to change to another paid plan, use plan change
            # Support both legacy (professional/business) and new (plus/pro) plan names
            if current_plan in ['professional', 'business', 'plus', 'pro'] and plan_id in ['professional', 'business', 'plus', 'pro']:
                if current_plan != plan_id:
                    print(f"🔄 User has {current_plan} plan, changing to {plan_id} via subscription modification")
                    return handle_change_plan(user, body)
    except Exception as e:
        print(f"⚠️  Error checking existing subscription: {str(e)}")
        # Continue with checkout creation if check fails
    
    # Debug: Log environment variables
    professional_price = os.environ.get('STRIPE_PRICE_PROFESSIONAL', '')
    business_price = os.environ.get('STRIPE_PRICE_BUSINESS', '')
    print(f"🔍 Debug - STRIPE_PRICE_PROFESSIONAL: {professional_price[:20] if professional_price else 'NOT SET'}...")
    print(f"🔍 Debug - STRIPE_PRICE_BUSINESS: {business_price[:20] if business_price else 'NOT SET'}...")
    print(f"🔍 Debug - Plan ID: {plan_id}, Price ID: {plan.get('stripe_price_id', 'NOT SET')}")
    
    if not plan['stripe_price_id']:
        error_msg = f'Plan "{plan_id}" not configured. Missing STRIPE_PRICE_{plan_id.upper()} environment variable.'
        print(f"❌ {error_msg}")
        return create_response(500, {
            'error': 'Plan not configured',
            'message': f'Stripe Price ID for {plan_id} plan is not configured. Please set STRIPE_PRICE_{plan_id.upper()} in Lambda environment variables.',
            'plan': plan_id
        })
    
    # Detailed diagnostics
    print(f"🔍 Debug - stripe object: {stripe}")
    print(f"🔍 Debug - stripe type: {type(stripe)}")
    
    if not stripe:
        error_detail = 'Stripe Python package not installed or STRIPE_SECRET_KEY not configured'
        print(f"❌ {error_detail}")
        print(f"🔍 Available environment variables: {list(os.environ.keys())}")
        return create_response(500, {
            'error': 'Stripe not configured',
            'message': error_detail,
            'details': 'Please ensure stripe package is installed and STRIPE_SECRET_KEY is set in Lambda environment variables',
            'debug': {
                'stripe_module': 'not_imported' if stripe is None else 'imported',
                'stripe_secret_key_set': bool(STRIPE_SECRET_KEY),
                'stripe_secret_key_length': len(STRIPE_SECRET_KEY) if STRIPE_SECRET_KEY else 0
            }
        })
    
    if not stripe.api_key or not stripe.api_key.strip():
        error_detail = 'STRIPE_SECRET_KEY is empty or not set'
        print(f"❌ {error_detail}")
        print(f"🔍 stripe.api_key: {stripe.api_key[:20] if stripe.api_key else 'None'}...")
        return create_response(500, {
            'error': 'Stripe not configured',
            'message': error_detail,
            'details': 'Please set STRIPE_SECRET_KEY in Lambda environment variables',
            'debug': {
                'stripe_module': 'imported',
                'stripe_secret_key_set': bool(STRIPE_SECRET_KEY),
                'stripe_api_key_set': bool(stripe.api_key) if stripe else False
            }
        })
    
    try:
        # Create Stripe checkout session
        frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
        # Use billing instead of /billing for S3 static hosting compatibility
        success_url = f"{frontend_url}/billing?success=true"
        cancel_url = f"{frontend_url}/billing?canceled=true"
        
        print(f"🔍 Creating checkout session:")
        print(f"   Plan: {plan_id}")
        print(f"   Price ID: {plan['stripe_price_id']}")
        print(f"   Customer email: {user['email']}")
        print(f"   Success URL: {success_url}")
        print(f"   Cancel URL: {cancel_url}")
        
        checkout_session = stripe.checkout.Session.create(
            customer_email=user['email'],
            payment_method_types=['card'],
            line_items=[{
                'price': plan['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user['id'],
                'plan': plan_id
            }
        )
        
        print(f"✅ Checkout session created: {checkout_session.id}")
        
        return create_response(200, {
            'session_id': checkout_session.id,
            'url': checkout_session.url
        })
    except Exception as e:
        # Check if it's a Stripe error
        error_type = type(e).__name__
        error_msg = str(e) if e else 'Unknown error'
        
        # Try to get Stripe-specific error details
        if hasattr(e, 'user_message'):
            error_msg = e.user_message
        elif hasattr(e, 'message'):
            error_msg = e.message
        
        print(f"❌ Error creating checkout session ({error_type}): {error_msg}")
        import traceback
        print(traceback.format_exc())
        
        # Detect mode mismatch error
        is_mode_mismatch = (
            'live mode' in error_msg.lower() and 'test mode' in error_msg.lower()
        ) or (
            'test mode' in error_msg.lower() and 'live mode' in error_msg.lower()
        )
        
        # Check if it's a Stripe error
        if 'stripe' in error_type.lower() or 'Stripe' in str(type(e)) or hasattr(e, 'code'):
            if is_mode_mismatch:
                # Detect which mode the API key is in
                api_key_mode = 'test' if STRIPE_SECRET_KEY.startswith('sk_test_') else 'live'
                return create_response(500, {
                    'error': 'Stripe mode mismatch',
                    'message': error_msg,
                    'type': error_type,
                    'details': f'Your Stripe API key is in {api_key_mode} mode, but the Price ID is in {"live" if api_key_mode == "test" else "test"} mode. You need to create Price IDs in {api_key_mode} mode in your Stripe Dashboard.',
                    'solution': f'Go to Stripe Dashboard → Products → Create/Edit Product → Add Price in {api_key_mode.upper()} mode, then update STRIPE_PRICE_PROFESSIONAL and STRIPE_PRICE_BUSINESS environment variables'
                })
            else:
                return create_response(500, {
                    'error': 'Failed to create checkout session',
                    'message': error_msg,
                    'type': error_type,
                    'details': 'Check Stripe dashboard and verify Price ID is correct'
                })
        else:
            return create_response(500, {
                'error': 'Failed to create checkout session',
                'message': error_msg,
                'type': error_type,
                'details': 'An unexpected error occurred while creating the checkout session'
            })


def handle_get_billing_history(user):
    """Get billing history for user"""
    try:
        print(f"📋 Fetching billing history for user {user['id']}")
        
        response = billing_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=50
        )
        
        invoices = response.get('Items', [])
        print(f"✅ Found {len(invoices)} billing records for user {user['id']}")
        
        # Sort by created_at descending (most recent first)
        invoices.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Format invoices for frontend
        formatted_invoices = []
        for invoice in invoices:
            formatted_invoices.append({
                'id': invoice.get('id'),
                'stripe_invoice_id': invoice.get('stripe_invoice_id'),
                'amount': float(invoice.get('amount', 0)),
                'currency': invoice.get('currency', 'usd'),
                'status': invoice.get('status', 'paid'),
                'plan': invoice.get('plan'),
                'created_at': invoice.get('created_at'),
                'invoice_pdf': invoice.get('invoice_pdf'),  # Stripe-generated PDF URL
                'invoice_number': invoice.get('invoice_number')  # Human-readable invoice number
            })
        
        return create_response(200, {'invoices': formatted_invoices})
    except Exception as e:
        print(f"❌ Error getting billing history: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(200, {'invoices': []})


def handle_get_invoice_pdf(user, invoice_id):
    """
    Get invoice PDF URL - either from stored DynamoDB record or fetch from Stripe.
    For testing/LocalStack, we can use the invoice_pdf field stored in DynamoDB.
    For production, we fetch from Stripe.
    """
    try:
        print(f"📄 Fetching invoice PDF for stripe_invoice_id {invoice_id}, user {user['id']}")
        
        # Query billing table by user_id and filter by stripe_invoice_id
        # Using UserIdIndex GSI
        response = billing_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            FilterExpression='stripe_invoice_id = :sid',
            ExpressionAttributeValues={
                ':uid': user['id'],
                ':sid': invoice_id
            },
            Limit=1
        )
        
        if not response.get('Items'):
            print(f"❌ Invoice {invoice_id} not found for user {user['id']}")
            return create_response(404, {'error': 'Invoice not found'})
        
        invoice = response['Items'][0]
        print(f"✅ Found invoice: {invoice.get('id')}")
        
        # Check if we have a stored PDF URL in DynamoDB (for test invoices or cached URLs)
        stored_pdf_url = invoice.get('invoice_pdf')
        if stored_pdf_url:
            print(f"✅ Using stored PDF URL from DynamoDB")
            # For test/demo invoices, return a mock PDF URL or the stored one
            return create_response(200, {
                'pdf_url': stored_pdf_url,
                'invoice_number': invoice.get('invoice_number', invoice.get('stripe_invoice_id')),
                'amount': float(invoice.get('amount', 0)),
                'currency': invoice.get('currency', 'usd').upper(),
                'created': invoice.get('created_at'),
                'status': invoice.get('status', 'paid')
            })
        
        # If no stored PDF URL, fetch from Stripe
        stripe_invoice_id = invoice.get('stripe_invoice_id')
        if not stripe_invoice_id:
            return create_response(404, {'error': 'Stripe invoice ID not found'})
        
        # Fetch invoice from Stripe to get PDF URL
        if stripe:
            try:
                stripe_invoice = stripe.Invoice.retrieve(stripe_invoice_id)
                pdf_url = stripe_invoice.get('invoice_pdf')
                
                if pdf_url:
                    # Cache the PDF URL in DynamoDB for future requests
                    try:
                        billing_table.update_item(
                            Key={'id': invoice['id']},
                            UpdateExpression='SET invoice_pdf = :pdf, invoice_number = :num',
                            ExpressionAttributeValues={
                                ':pdf': pdf_url,
                                ':num': stripe_invoice.get('number')
                            }
                        )
                        print(f"✅ Cached PDF URL in DynamoDB for invoice {invoice_id}")
                    except Exception as cache_error:
                        print(f"⚠️  Error caching PDF URL: {str(cache_error)}")
                    
                    return create_response(200, {
                        'pdf_url': pdf_url,
                        'invoice_number': stripe_invoice.get('number'),
                        'amount': stripe_invoice.get('amount_paid') / 100,  # Convert from cents
                        'currency': stripe_invoice.get('currency', 'usd').upper(),
                        'created': stripe_invoice.get('created'),
                        'status': stripe_invoice.get('status')
                    })
                else:
                    return create_response(404, {'error': 'PDF URL not available'})
            except stripe.error.StripeError as e:
                print(f"❌ Stripe error retrieving invoice: {str(e)}")
                return create_response(500, {'error': 'Failed to retrieve invoice from Stripe'})
        else:
            return create_response(500, {'error': 'Stripe not configured'})
            
    except Exception as e:
        print(f"❌ Error getting invoice PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to retrieve invoice PDF'})


def handle_get_subscription(user):
    """Get current subscription details"""
    try:
        # Get subscription from subscriptions table
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=1
        )
        
        subscription = None
        if response.get('Items'):
            subscription = response['Items'][0]
        
        # Get user's current plan directly from DynamoDB (not from session cache)
        # This ensures we have the latest subscription status after webhook updates
        try:
            user_email = user.get('email')
            if user_email:
                user_response = users_table.get_item(Key={'email': user_email})
                if 'Item' in user_response:
                    db_user = user_response['Item']
                    # Use 'plan' field (new), fallback to 'subscription' (legacy)
                    current_plan = db_user.get('plan', db_user.get('subscription', 'free'))
                    print(f"📋 User {user_email} plan from DB: {current_plan}")
                else:
                    current_plan = user.get('plan', user.get('subscription', 'free'))
                    print(f"⚠️  User not found in DB, using session plan: {current_plan}")
            else:
                current_plan = user.get('plan', user.get('subscription', 'free'))
                print(f"⚠️  No email in user object, using session plan: {current_plan}")
        except Exception as e:
            print(f"⚠️  Error fetching user from DB: {str(e)}, using session plan")
            current_plan = user.get('plan', user.get('subscription', 'free'))
        
        plan_details = PLANS.get(current_plan, PLANS['free'])
        
        # Check for pending plan change first
        pending_plan = None
        pending_plan_change_at = None
        if subscription:
            pending_plan = subscription.get('pending_plan')
            pending_plan_change_at = subscription.get('pending_plan_change_at')
        
        # Determine status based on actual user plan and cancellation status
        if current_plan == 'free':
            status = 'free'
        elif current_plan in ['professional', 'business']:
            # If there's a pending plan change to another paid plan, status is 'active' (plan change, not cancellation)
            if pending_plan and pending_plan in ['professional', 'business']:
                status = 'active'  # Plan change scheduled, not cancellation
            else:
                # Check if subscription is scheduled to cancel at period end
                # First check our database record
                cancel_at_period_end = False
                if subscription:
                    cancel_at_period_end = subscription.get('cancel_at_period_end', False)
                
                # If not in DB, check Stripe directly
                if not cancel_at_period_end and subscription and stripe:
                    stripe_subscription_id = subscription.get('stripe_subscription_id')
                    if stripe_subscription_id:
                        try:
                            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                            cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
                            # Update our database record
                            if cancel_at_period_end:
                                subscription['cancel_at_period_end'] = True
                                subscriptions_table.put_item(Item=subscription)
                        except Exception as e:
                            print(f"⚠️  Error retrieving Stripe subscription: {str(e)}")
                
                # If subscription is scheduled to cancel (and no pending plan change to paid plan), show 'canceled' status
                # User still has access until period end, but status reflects cancellation
                if cancel_at_period_end:
                    status = 'canceled'
                else:
                    status = 'active'
        else:
            # Fallback: unknown plan, default to active
            status = 'active'
        
        return create_response(200, {
            'subscription': subscription,
            'plan': current_plan,
            'plan_details': plan_details,
            'status': status,
            'pending_plan': pending_plan,
            'pending_plan_change_at': pending_plan_change_at
        })
    except Exception as e:
        print(f"Error getting subscription: {str(e)}")
        import traceback
        traceback.print_exc()
        # Use 'plan' field (new), fallback to 'subscription' (legacy)
        current_plan = user.get('plan', user.get('subscription', 'free'))
        return create_response(200, {
            'subscription': None,
            'plan': current_plan,
            'plan_details': PLANS.get(current_plan, PLANS['free']),
            'status': 'free'
        })


def handle_check_downgrade_limits(user, target_plan='free'):
    """Check if user can downgrade to target plan and return what needs to be deleted"""
    from boto3.dynamodb.conditions import Key
    from utils.config import galleries_table, photos_table
    from handlers.subscription_handler import get_user_plan_limits
    
    try:
        # Validate target plan
        if target_plan not in PLANS:
            return create_response(400, {'error': 'Invalid target plan'})
        
        # Get current and target plan limits
        current_plan_limits = get_user_plan_limits(user)
        target_plan_config = PLANS.get(target_plan, PLANS['free'])
        
        # Get all galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        all_galleries = galleries_response.get('Items', [])
        
        # Calculate current usage
        total_storage_mb = sum(float(g.get('storage_used', 0)) for g in all_galleries)
        total_storage_gb = total_storage_mb / 1024
        
        current_month = datetime.utcnow().strftime('%Y-%m')
        monthly_galleries = sum(
            1 for g in all_galleries 
            if g.get('created_at', '').startswith(current_month)
        )
        
        # Get photo counts per gallery
        galleries_with_photos = []
        for gallery in all_galleries:
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery['id'])
            )
            photo_count = len(photos_response.get('Items', []))
            galleries_with_photos.append({
                'id': gallery['id'],
                'name': gallery.get('name', 'Unnamed Gallery'),
                'created_at': gallery.get('created_at', ''),
                'photo_count': photo_count,
                'storage_mb': float(gallery.get('storage_used', 0)),
                'storage_gb': float(gallery.get('storage_used', 0)) / 1024
            })
        
        # Check limits based on target plan
        target_galleries_limit = target_plan_config['galleries_per_month']
        target_storage_gb = target_plan_config['storage_gb']
        
        issues = []
        needs_deletion = False
        
        # Check gallery limit (only for free/starter plan)
        if target_galleries_limit != -1 and monthly_galleries > target_galleries_limit:
            excess_galleries = monthly_galleries - target_galleries_limit
            issues.append({
                'type': 'galleries',
                'current': monthly_galleries,
                'limit': target_galleries_limit,
                'excess': excess_galleries,
                'message': f'You have {monthly_galleries} galleries this month, but {target_plan_config["name"]} plan allows only {target_galleries_limit}. You need to delete {excess_galleries} gallery(ies).'
            })
            needs_deletion = True
        
        # Check storage limit (for all plans)
        if target_storage_gb != -1 and total_storage_gb > target_storage_gb:
            excess_storage_gb = total_storage_gb - target_storage_gb
            issues.append({
                'type': 'storage',
                'current': round(total_storage_gb, 2),
                'limit': target_storage_gb,
                'excess': round(excess_storage_gb, 2),
                'message': f'You are using {total_storage_gb:.2f} GB, but {target_plan_config["name"]} plan allows only {target_storage_gb} GB. You need to free up {excess_storage_gb:.2f} GB.'
            })
            needs_deletion = True
        
        return create_response(200, {
            'can_downgrade': not needs_deletion,
            'issues': issues,
            'current_usage': {
                'galleries_this_month': monthly_galleries,
                'total_storage_gb': round(total_storage_gb, 2)
            },
            'target_limits': {
                'galleries_per_month': target_galleries_limit,
                'storage_gb': target_storage_gb
            },
            'target_plan': target_plan,
            'target_plan_name': target_plan_config['name'],
            'galleries': galleries_with_photos
        })
    except Exception as e:
        print(f"Error checking downgrade limits: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to check downgrade limits'})


def handle_downgrade_subscription(user, body):
    """Downgrade subscription to free plan with selective deletion"""
    from boto3.dynamodb.conditions import Key
    from utils.config import galleries_table, photos_table, s3_client, S3_BUCKET
    
    try:
        galleries_to_delete = body.get('galleries_to_delete', [])
        
        # Get subscription
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user['id']},
            ScanIndexForward=False,
            Limit=1
        )
        
        subscription = None
        if response.get('Items'):
            subscription = response['Items'][0]
            stripe_subscription_id = subscription.get('stripe_subscription_id')
            
            # Cancel Stripe subscription
            if stripe_subscription_id and stripe:
                try:
                    stripe.Subscription.modify(
                        stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    print(f"✅ Stripe subscription {stripe_subscription_id} set to cancel at period end")
                except Exception as e:
                    print(f"⚠️  Error canceling Stripe subscription: {str(e)}")
        
        # Delete selected galleries and their photos
        deleted_galleries = []
        deleted_photos = 0
        freed_storage_mb = 0
        
        for gallery_id in galleries_to_delete:
            try:
                # Get gallery
                gallery_response = galleries_table.get_item(Key={
                    'user_id': user['id'],
                    'id': gallery_id
                })
                
                if 'Item' in gallery_response:
                    gallery = gallery_response['Item']
                    
                    # Get all photos in gallery
                    photos_response = photos_table.query(
                        IndexName='GalleryIdIndex',
                        KeyConditionExpression=Key('gallery_id').eq(gallery_id)
                    )
                    photos = photos_response.get('Items', [])
                    
                    # Delete photos from S3 and database
                    for photo in photos:
                        try:
                            # Delete from S3
                            photo_key = photo.get('s3_key') or photo.get('url', '').split('/')[-1]
                            if photo_key:
                                s3_client.delete_object(Bucket=S3_BUCKET, Key=photo_key)
                            
                            # Delete from database
                            photos_table.delete_item(Key={'id': photo['id']})
                            deleted_photos += 1
                            freed_storage_mb += float(photo.get('size_mb', 0))
                        except Exception as e:
                            print(f"⚠️  Error deleting photo {photo.get('id')}: {str(e)}")
                    
                    # Delete gallery
                    galleries_table.delete_item(Key={
                        'user_id': user['id'],
                        'id': gallery_id
                    })
                    deleted_galleries.append(gallery_id)
                    freed_storage_mb += float(gallery.get('storage_used', 0))
            except Exception as e:
                print(f"⚠️  Error deleting gallery {gallery_id}: {str(e)}")
        
        # Update subscription status and cancel_at_period_end flag
        if subscription:
            subscription['status'] = 'canceled'
            subscription['cancel_at_period_end'] = True
            subscription['pending_plan'] = 'free'  # Will change to free at period end
            subscription['canceled_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Get period end from Stripe
            if stripe_subscription_id and stripe:
                try:
                    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    subscription['pending_plan_change_at'] = stripe_sub.get('current_period_end')
                except Exception as e:
                    print(f"⚠️  Error retrieving Stripe subscription: {str(e)}")
            
            subscriptions_table.put_item(Item=subscription)
            
            # Send downgrade confirmation email
            try:
                from utils.email import send_subscription_downgraded_email
                period_end_timestamp = subscription.get('pending_plan_change_at')
                if period_end_timestamp:
                    period_end_date = datetime.fromtimestamp(period_end_timestamp).strftime('%B %d, %Y')
                else:
                    period_end_date = 'the end of your billing period'
                
                user_email = subscription.get('user_email') or user.get('email', '')
                user_name = user.get('username') or user.get('name') or ''
                if user_email:
                    send_subscription_downgraded_email(user_email, user_name, 'Starter', period_end_date)
            except Exception as e:
                print(f"⚠️  Error sending downgrade email: {str(e)}")
        
        # DO NOT update user plan immediately - keep current plan active until period end
        # The plan will change automatically at period end via webhook
        
        return create_response(200, {
            'message': 'Subscription downgrade scheduled. You will be downgraded to Starter plan at the end of your current billing period.',
            'deleted_galleries': len(deleted_galleries),
            'deleted_photos': deleted_photos,
            'freed_storage_gb': round(freed_storage_mb / 1024, 2),
            'scheduled': True
        })
    except Exception as e:
        print(f"Error downgrading subscription: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to downgrade subscription'})


def handle_cancel_subscription(user):
    """Cancel subscription - now redirects to downgrade check"""
    # This is kept for backward compatibility, but should use handle_downgrade_subscription
    return handle_downgrade_subscription(user, {'galleries_to_delete': []})


def handle_stripe_webhook(event_data, stripe_signature='', raw_body=''):
    """Handle Stripe webhook events with signature verification"""
    try:
        # Verify webhook signature if secret is configured
        if STRIPE_WEBHOOK_SECRET and stripe and stripe_signature and raw_body:
            try:
                # Verify the webhook signature
                event_obj = stripe.Webhook.construct_event(
                    raw_body,
                    stripe_signature,
                    STRIPE_WEBHOOK_SECRET
                )
                event_data = event_obj
            except ValueError as e:
                print(f"⚠️  Invalid webhook payload: {str(e)}")
                return create_response(400, {'error': 'Invalid payload'})
            except stripe.error.SignatureVerificationError as e:
                print(f"⚠️  Invalid webhook signature: {str(e)}")
                return create_response(400, {'error': 'Invalid signature'})
        
        # Extract event type and data
        event_type = event_data.get('type')
        data = event_data.get('data', {}).get('object', {})
        
        if event_type == 'checkout.session.completed':
            # Subscription created
            user_id = data.get('metadata', {}).get('user_id')
            plan = data.get('metadata', {}).get('plan')
            subscription_id = data.get('subscription')
            customer_email = data.get('customer_email', '').lower()
            customer_id = data.get('customer')
            
            if user_id and plan and customer_email:
                # Update user subscription
                try:
                    users_table.update_item(
                        Key={'email': customer_email},
                        UpdateExpression='SET subscription = :plan, updated_at = :now',
                        ExpressionAttributeValues={
                            ':plan': plan,
                            ':now': datetime.utcnow().isoformat() + 'Z'
                        }
                    )
                    print(f"✅ Updated user {customer_email} to plan {plan}")
                except Exception as e:
                    print(f"⚠️  Error updating user subscription: {str(e)}")
                
                # Create subscription record
                try:
                    subscriptions_table.put_item(Item={
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'stripe_subscription_id': subscription_id,
                        'stripe_customer_id': customer_id,
                        'user_email': customer_email,
                        'plan': plan,
                        'status': 'active',
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'updated_at': datetime.utcnow().isoformat() + 'Z'
                    })
                    print(f"✅ Created subscription record for user {user_id}")
                except Exception as e:
                    print(f"⚠️  Error creating subscription record: {str(e)}")
                
                # Create invoice record if invoice exists
                # Note: For subscriptions, Stripe creates the invoice after checkout.session.completed
                # The invoice.paid webhook will handle creating the billing record
                invoice_id = data.get('invoice')
                if invoice_id:
                    print(f"📄 Checkout session has invoice {invoice_id}, will be processed by invoice.paid webhook")
                    # Optionally fetch invoice details and create record immediately
                    if stripe:
                        try:
                            invoice = stripe.Invoice.retrieve(invoice_id)
                            amount_paid = invoice.get('amount_paid', 0) or invoice.get('total', 0) or 0
                            if amount_paid > 0:
                                billing_table.put_item(Item={
                                    'id': str(uuid.uuid4()),
                                    'user_id': user_id,
                                    'stripe_invoice_id': invoice_id,
                                    'amount': amount_paid / 100,  # Convert cents to dollars
                                    'currency': invoice.get('currency', 'usd'),
                                    'status': 'paid',
                                    'plan': plan,
                                    'created_at': datetime.utcnow().isoformat() + 'Z'
                                })
                                print(f"✅ Created billing record for invoice {invoice_id} from checkout session")
                        except Exception as e:
                            print(f"⚠️  Error fetching invoice details: {str(e)}")
                            # Don't fail, invoice.paid webhook will handle it
                
                # Send subscription upgrade email
                try:
                    from utils.email import send_subscription_upgraded_email
                    plan_details = PLANS.get(plan, {})
                    send_subscription_upgraded_email(
                        customer_email,
                        '',  # Name not available in checkout session
                        plan_details.get('name', plan),
                        plan_details.get('features', [])
                    )
                except Exception as e:
                    print(f"⚠️  Error sending upgrade email: {str(e)}")
        
        elif event_type == 'customer.subscription.updated':
            # Subscription updated (e.g., cancel_at_period_end changed, plan changed)
            subscription_id = data.get('id')
            customer_id = data.get('customer')
            cancel_at_period_end = data.get('cancel_at_period_end', False)
            current_period_end = data.get('current_period_end')
            
            # Get plan from metadata or items
            plan = None
            if data.get('metadata', {}).get('plan'):
                plan = data['metadata']['plan']
            elif data.get('items', {}).get('data'):
                # Try to determine plan from price ID
                price_id = data['items']['data'][0].get('price', {}).get('id', '')
                if price_id == os.environ.get('STRIPE_PRICE_PROFESSIONAL', ''):
                    plan = 'professional'
                elif price_id == os.environ.get('STRIPE_PRICE_BUSINESS', ''):
                    plan = 'business'
            
            print(f"📋 Processing customer.subscription.updated: subscription={subscription_id}, cancel_at_period_end={cancel_at_period_end}, plan={plan}")
            
            # Find subscription by Stripe subscription ID
            response = subscriptions_table.scan(
                FilterExpression='stripe_subscription_id = :sid',
                ExpressionAttributeValues={':sid': subscription_id}
            )
            
            if response.get('Items'):
                subscription = response['Items'][0]
                user_id = subscription['user_id']
                pending_plan = subscription.get('pending_plan')
                pending_plan_change_at = subscription.get('pending_plan_change_at')
                
                # Update cancel_at_period_end flag
                subscription['cancel_at_period_end'] = cancel_at_period_end
                subscription['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                
                # Check if this is a period end and pending plan change should take effect
                if pending_plan and pending_plan_change_at:
                    # Check if current period end has passed (or is very close to) the scheduled change time
                    # pending_plan_change_at is a Unix timestamp, current_period_end is also Unix timestamp
                    current_time = datetime.utcnow().timestamp()
                    # Apply change if we're past the scheduled time (with 1 hour buffer for webhook delays)
                    if current_time >= (pending_plan_change_at - 3600):
                        # Period has ended (or is ending), apply pending plan change
                        print(f"🔄 Applying pending plan change: {pending_plan} (scheduled for {pending_plan_change_at}, current time: {current_time})")
                        subscription['plan'] = pending_plan
                        subscription['pending_plan'] = None
                        subscription['pending_plan_change_at'] = None
                        
                        # Update user plan in users table
                        try:
                            user_email = subscription.get('user_email')
                            if user_email:
                                users_table.update_item(
                                    Key={'email': user_email},
                                    UpdateExpression='SET #plan = :plan_val, subscription = :plan_val, updated_at = :now',
                                    ExpressionAttributeNames={'#plan': 'plan'},
                                    ExpressionAttributeValues={
                                        ':plan_val': pending_plan,
                                        ':now': datetime.utcnow().isoformat() + 'Z'
                                    }
                                )
                                print(f"✅ Updated user {user_email} to plan {pending_plan} at period end (downgrade applied)")
                        except Exception as e:
                            print(f"⚠️  Error updating user plan via webhook: {str(e)}")
                
                # Update plan if changed (for immediate upgrades)
                elif plan and plan in ['professional', 'business']:
                    # Only update immediately if no pending plan change
                    if not pending_plan:
                        subscription['plan'] = plan
                        # Update user plan in users table
                        try:
                            user_email = subscription.get('user_email')
                            if user_email:
                                users_table.update_item(
                                    Key={'email': user_email},
                                    UpdateExpression='SET #plan = :plan_val, subscription = :plan_val, updated_at = :now',
                                    ExpressionAttributeNames={'#plan': 'plan'},
                                    ExpressionAttributeValues={
                                        ':plan_val': plan,
                                        ':now': datetime.utcnow().isoformat() + 'Z'
                                    }
                                )
                                print(f"✅ Updated user {user_email} to plan {plan} via webhook (immediate upgrade)")
                        except Exception as e:
                            print(f"⚠️  Error updating user plan via webhook: {str(e)}")
                
                subscriptions_table.put_item(Item=subscription)
                print(f"✅ Updated subscription {subscription_id} cancel_at_period_end={cancel_at_period_end}, plan={plan}")
        
        elif event_type == 'customer.subscription.deleted':
            # Subscription canceled - this webhook is called when subscription is actually deleted
            # If cancel_at_period_end=True, this happens at period end
            subscription_id = data.get('id')
            customer_id = data.get('customer')
            
            print(f"📋 Processing customer.subscription.deleted: subscription={subscription_id}, customer={customer_id}")
            
            # Find subscription by Stripe subscription ID
            response = subscriptions_table.scan(
                FilterExpression='stripe_subscription_id = :sid',
                ExpressionAttributeValues={':sid': subscription_id}
            )
            
            if response.get('Items'):
                subscription = response['Items'][0]
                user_id = subscription['user_id']
                pending_plan = subscription.get('pending_plan')
                
                # Get user email from subscription record or users table
                user_email = subscription.get('user_email')
                if not user_email:
                    user_response = users_table.query(
                        IndexName='UserIdIndex',
                        KeyConditionExpression='id = :uid',
                        ExpressionAttributeValues={':uid': user_id}
                    )
                    if user_response.get('Items'):
                        user_email = user_response['Items'][0]['email']
                
                if user_email:
                    # If there's a pending plan change, use that (should be 'free' for cancellations)
                    # Otherwise, default to 'free' since subscription is deleted
                    plan_to_set = pending_plan if pending_plan else 'free'
                    
                    # Update user to free plan (or pending plan if set)
                    try:
                        users_table.update_item(
                            Key={'email': user_email},
                            UpdateExpression='SET #plan = :plan_val, subscription = :plan_val, updated_at = :now',
                            ExpressionAttributeNames={'#plan': 'plan'},
                            ExpressionAttributeValues={
                                ':plan_val': plan_to_set,
                                ':now': datetime.utcnow().isoformat() + 'Z'
                            }
                        )
                        print(f"✅ Updated user {user_email} to plan {plan_to_set} after subscription deletion")
                    except Exception as e:
                        print(f"⚠️  Error updating user plan: {str(e)}")
                
                # Update subscription status
                subscription['status'] = 'canceled'
                subscription['canceled_at'] = datetime.utcnow().isoformat() + 'Z'
                # Clear pending plan since it's been applied
                if pending_plan:
                    subscription['pending_plan'] = None
                    subscription['pending_plan_change_at'] = None
                subscriptions_table.put_item(Item=subscription)
                print(f"✅ Updated subscription {subscription_id} status to canceled")
        
        elif event_type == 'invoice.paid':
            # Invoice paid - create billing record
            user_id = None
            customer_id = data.get('customer')
            invoice_id = data.get('id')
            
            print(f"📄 Processing invoice.paid event: invoice={invoice_id}, customer={customer_id}")
            
            # Try to find user by customer ID from subscriptions table
            if customer_id:
                response = subscriptions_table.scan(
                    FilterExpression='stripe_customer_id = :cid',
                    ExpressionAttributeValues={':cid': customer_id}
                )
                if response.get('Items'):
                    user_id = response['Items'][0]['user_id']
                    print(f"✅ Found user_id {user_id} for customer {customer_id}")
            
            # If not found via subscription, try to get from invoice metadata or checkout session
            if not user_id:
                # Try to get customer email from invoice
                customer_email = None
                if stripe and customer_id:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        customer_email = customer.get('email', '').lower() if customer else None
                        if customer_email:
                            # Find user by email
                            user_response = users_table.get_item(Key={'email': customer_email})
                            if 'Item' in user_response:
                                user_id = user_response['Item'].get('id')
                                print(f"✅ Found user_id {user_id} via customer email {customer_email}")
                    except Exception as e:
                        print(f"⚠️  Error retrieving customer: {str(e)}")
            
            if user_id:
                # Check if billing record already exists
                try:
                    existing_response = billing_table.scan(
                        FilterExpression='stripe_invoice_id = :inv_id',
                        ExpressionAttributeValues={':inv_id': invoice_id}
                    )
                    if existing_response.get('Items'):
                        print(f"ℹ️  Billing record already exists for invoice {invoice_id}")
                    else:
                        # Create new billing record
                        amount_paid = data.get('amount_paid', 0) or data.get('total', 0) or 0
                        billing_table.put_item(Item={
                            'id': str(uuid.uuid4()),
                            'user_id': user_id,
                            'stripe_invoice_id': invoice_id,
                            'amount': Decimal(str(amount_paid / 100)),  # Convert cents to dollars, then to Decimal
                            'currency': data.get('currency', 'usd'),
                            'status': 'paid',
                            'plan': data.get('subscription_details', {}).get('metadata', {}).get('plan') or 'professional',
                            'created_at': datetime.utcnow().isoformat() + 'Z'
                        })
                        print(f"✅ Created billing record for invoice {invoice_id}, user {user_id}, amount ${amount_paid / 100}")
                        
                        # Send payment receipt email
                        try:
                            from utils.email import send_payment_receipt_email
                            plan_name = data.get('subscription_details', {}).get('metadata', {}).get('plan') or 'professional'
                            plan_details = PLANS.get(plan_name, {})
                            plan_display_name = plan_details.get('name', plan_name)
                            
                            # Get user email
                            user_email = None
                            if customer_id and stripe:
                                try:
                                    customer = stripe.Customer.retrieve(customer_id)
                                    user_email = customer.get('email', '').lower() if customer else None
                                except:
                                    pass
                            
                            if not user_email:
                                # Try to get from subscriptions table
                                try:
                                    sub_response = subscriptions_table.scan(
                                        FilterExpression='user_id = :uid',
                                        ExpressionAttributeValues={':uid': user_id}
                                    )
                                    if sub_response.get('Items'):
                                        user_email = sub_response['Items'][0].get('user_email', '').lower()
                                except:
                                    pass
                            
                            if user_email:
                                # Get user name
                                user_name = None
                                try:
                                    user_response = users_table.get_item(Key={'email': user_email})
                                    if 'Item' in user_response:
                                        user_name = user_response['Item'].get('username') or user_response['Item'].get('name')
                                except:
                                    pass
                                
                                send_payment_receipt_email(
                                    user_email,
                                    user_name or '',
                                    amount_paid / 100,
                                    data.get('currency', 'usd'),
                                    plan_display_name
                                )
                                print(f"✅ Sent payment receipt email to {user_email}")
                        except Exception as e:
                            print(f"⚠️  Error sending payment receipt email: {str(e)}")
                except Exception as e:
                    print(f"⚠️  Error creating billing record: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️  Could not find user_id for invoice {invoice_id}, customer {customer_id}")
        
        return create_response(200, {'status': 'success'})
    except Exception as e:
        print(f"Error handling webhook: {str(e)}")
        return create_response(500, {'error': 'Webhook processing failed'})

