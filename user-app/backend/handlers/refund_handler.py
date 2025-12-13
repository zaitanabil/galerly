"""
Refund management handlers
Handles 14-day money-back guarantee
"""
import os
from datetime import datetime, timedelta, timezone
from utils.config import users_table, subscriptions_table, billing_table
from utils.response import create_response
from utils.plan_enforcement import require_role
from boto3.dynamodb.conditions import Key

# Configuration from environment
REFUND_WINDOW_DAYS = int(os.environ.get('REFUND_WINDOW_DAYS', '14'))  # Default 14-day money-back guarantee

# Initialize Stripe
try:
    import stripe
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None


def has_pending_or_approved_refund(user_id):
    """
    Check if user has any pending or approved refunds.
    
    Args:
        user_id (str): User ID to check
        
    Returns:
        bool: True if user has pending/approved refunds, False otherwise
    """
    try:
        # Query billing records for refund status
        response = billing_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        # Check if any transactions are refunded or pending refund
        for record in response.get('Items', []):
            refund_status = record.get('refund_status', '').lower()
            if refund_status in ['pending', 'approved', 'processing']:
                return True
        
        # Check subscriptions for refund flags
        sub_response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        for subscription in sub_response.get('Items', []):
            refund_status = subscription.get('refund_status', '').lower()
            if refund_status in ['pending', 'approved', 'processing', 'refunded']:
                return True
        
        return False
    except Exception as e:
        print(f"Error checking refund status for user {user_id}: {str(e)}")
        return False


@require_role('photographer')
def handle_check_refund_eligibility(user):
    """
    Check if user is eligible for a refund
    Eligible if:
    - Subscribed less than 14 days ago
    - Has an active subscription
    - Hasn't already requested a refund
    """
    try:
        # Get user's subscription
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id']),
            Limit=1
        )
        
        subscriptions = response.get('Items', [])
        if not subscriptions:
            return create_response(200, {
                'eligible': False,
                'reason': 'No active subscription found'
            })
        
        subscription = subscriptions[0]
        
        # Check if already refunded
        if subscription.get('refund_status') == 'refunded':
            return create_response(200, {
                'eligible': False,
                'reason': 'Refund already processed'
            })
        
        if subscription.get('refund_status') == 'requested':
            return create_response(200, {
                'eligible': False,
                'reason': 'Refund already requested'
            })
        
        # Check subscription date
        created_at = subscription.get('created_at')
        if not created_at:
            return create_response(200, {
                'eligible': False,
                'reason': 'Subscription date not found'
            })
        
        # Parse date
        sub_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        # FIX: Use timezone-aware datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        days_since = (now - sub_date).days
        
        if days_since > REFUND_WINDOW_DAYS:
            return create_response(200, {
                'eligible': False,
                'reason': f'Refund window expired. Refunds are available within {REFUND_WINDOW_DAYS} days of subscription.',
                'days_since_subscription': days_since
            })
        
        # Eligible!
        remaining_days = REFUND_WINDOW_DAYS - days_since
        return create_response(200, {
            'eligible': True,
            'days_since_subscription': days_since,
            'remaining_days': remaining_days,
            'subscription_id': subscription.get('id')
        })
        
    except Exception as e:
        print(f"Error checking refund eligibility: {str(e)}")
        return create_response(500, {'error': 'Failed to check refund eligibility'})


@require_role('photographer')
def handle_request_refund(user, body):
    """
    Request a refund
    Processes immediately via Stripe and cancels subscription
    """
    try:
        if not stripe:
            return create_response(500, {'error': 'Payment system unavailable'})
        
        reason = body.get('reason', 'Customer requested refund')
        
        # Check eligibility first
        eligibility_response = handle_check_refund_eligibility(user)
        eligibility_data = eligibility_response.get('body', {})
        
        if isinstance(eligibility_data, str):
            import json
            eligibility_data = json.loads(eligibility_data)
        
        if not eligibility_data.get('eligible'):
            return create_response(403, {
                'error': 'Not eligible for refund',
                'reason': eligibility_data.get('reason')
            })
        
        # Get subscription
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id']),
            Limit=1
        )
        
        subscriptions = response.get('Items', [])
        if not subscriptions:
            return create_response(404, {'error': 'Subscription not found'})
        
        subscription = subscriptions[0]
        stripe_sub_id = subscription.get('stripe_subscription_id')
        stripe_customer_id = subscription.get('stripe_customer_id')
        
        if not stripe_sub_id or not stripe_customer_id:
            return create_response(400, {'error': 'Stripe subscription not found'})
        
        # Get latest payment intent to refund
        try:
            # Get recent invoices for this customer
            invoices = stripe.Invoice.list(
                customer=stripe_customer_id,
                limit=int(os.environ.get('REFUND_LIST_LIMIT'))
            )
            
            # Find the latest paid invoice
            latest_payment_intent_id = None
            for invoice in invoices.data:
                if invoice.status == 'paid' and invoice.payment_intent:
                    latest_payment_intent_id = invoice.payment_intent
                    break
            
            if not latest_payment_intent_id:
                return create_response(400, {'error': 'No recent payment found to refund'})
            
            # Create refund
            refund = stripe.Refund.create(
                payment_intent=latest_payment_intent_id,
                reason='requested_by_customer',
                metadata={
                    'user_id': user['id'],
                    'reason': reason
                }
            )
            
            # Cancel subscription
            stripe.Subscription.cancel(stripe_sub_id)
            
            # Update subscription record
            subscription['refund_status'] = 'refunded'
            subscription['refund_amount'] = refund.amount / 100  # Convert cents to dollars
            subscription['refund_date'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            subscription['refund_reason'] = reason
            subscription['refund_id'] = refund.id
            subscription['status'] = 'canceled'
            subscription['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            
            subscriptions_table.put_item(Item=subscription)
            
            # Update user plan to free
            user_response = users_table.get_item(Key={'email': user['email']})
            if 'Item' in user_response:
                user_data = user_response['Item']
                user_data['plan'] = 'free'
                user_data['subscription'] = 'free'
                user_data['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                users_table.put_item(Item=user_data)
            
            return create_response(200, {
                'success': True,
                'refund_amount': refund.amount / 100,
                'refund_id': refund.id,
                'message': f'Refund of ${refund.amount / 100:.2f} processed successfully. Your subscription has been canceled.'
            })
            
        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            return create_response(400, {'error': f'Payment error: {str(e)}'})
        
    except Exception as e:
        print(f"Error processing refund: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to process refund'})


@require_role('photographer')
def handle_get_refund_status(user):
    """Get refund status for user"""
    try:
        response = subscriptions_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id']),
            Limit=1
        )
        
        subscriptions = response.get('Items', [])
        if not subscriptions:
            return create_response(200, {'status': 'no_subscription'})
        
        subscription = subscriptions[0]
        refund_status = subscription.get('refund_status', 'none')
        
        result = {
            'status': refund_status
        }
        
        if refund_status == 'refunded':
            result['refund_amount'] = subscription.get('refund_amount')
            result['refund_date'] = subscription.get('refund_date')
            result['refund_id'] = subscription.get('refund_id')
        
        return create_response(200, result)
        
    except Exception as e:
        print(f"Error getting refund status: {str(e)}")
        return create_response(500, {'error': 'Failed to get refund status'})
