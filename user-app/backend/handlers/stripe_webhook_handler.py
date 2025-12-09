"""
Stripe Webhook Handler
Processes Stripe webhook events for subscription and payment updates
"""
import json
import os
from datetime import datetime, timezone
from utils.response import create_response
from utils.config import users_table

# Stripe configuration
try:
    import stripe
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    print(" Stripe not installed")


def handle_stripe_webhook(event, context):
    """
    Handle incoming Stripe webhook events
    Verifies signature and processes events
    """
    try:
        # Get the webhook payload
        payload = event.get('body', '')
        sig_header = event.get('headers', {}).get('stripe-signature', '') or event.get('headers', {}).get('Stripe-Signature', '')
        
        print(f"📥 Stripe webhook received")
        print(f"   Signature: {sig_header[:20]}..." if sig_header else "   No signature")
        
        # ENFORCE webhook signature verification (required for security)
        if not STRIPE_WEBHOOK_SECRET:
            print(f"❌ STRIPE_WEBHOOK_SECRET not configured")
            return create_response(500, {'error': 'Webhook secret not configured'})
        
        if not sig_header:
            print(f"❌ No Stripe signature in request")
            return create_response(400, {'error': 'Missing Stripe signature'})
        
        # Verify webhook signature
        try:
            stripe_event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            print(f"✅ Webhook signature verified")
        except ValueError as e:
            print(f"❌ Invalid payload: {e}")
            return create_response(400, {'error': 'Invalid payload'})
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Invalid signature: {e}")
            return create_response(401, {'error': 'Invalid signature'})
        
        # Get event type and data
        event_type = stripe_event.get('type')
        event_data = stripe_event.get('data', {}).get('object', {})
        
        print(f"📌 Event type: {event_type}")
        print(f"📌 Event ID: {stripe_event.get('id')}")
        
        # Route to appropriate handler
        if event_type.startswith('customer.subscription.'):
            return handle_subscription_event(event_type, event_data)
        elif event_type.startswith('invoice.'):
            return handle_invoice_event(event_type, event_data)
        elif event_type.startswith('customer.'):
            return handle_customer_event(event_type, event_data)
        elif event_type.startswith('checkout.session.'):
            return handle_checkout_event(event_type, event_data)
        else:
            print(f"Unhandled event type: {event_type}")
            return create_response(200, {
                'received': True,
                'message': f'Event {event_type} received but not processed'
            })
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': str(e)})


def handle_subscription_event(event_type, subscription):
    """Handle subscription-related events"""
    print(f"🔄 Processing subscription event: {event_type}")
    
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    status = subscription.get('status')
    current_period_end = subscription.get('current_period_end')
    
    print(f"   Customer: {customer_id}")
    print(f"   Subscription: {subscription_id}")
    print(f"   Status: {status}")
    
    # Find user by Stripe customer ID
    try:
        response = users_table.scan(
            FilterExpression='stripe_customer_id = :customer_id',
            ExpressionAttributeValues={':customer_id': customer_id}
        )
        
        if not response.get('Items'):
            print(f" No user found for customer {customer_id}")
            return create_response(200, {
                'received': True,
                'warning': 'User not found'
            })
        
        user = response['Items'][0]
        user_id = user['id']
        
        print(f"   Found user: {user.get('email')}")
        
        # Update user subscription status
        update_expression_parts = []
        expression_values = {}
        
        if event_type == 'customer.subscription.created':
            print(f"Subscription created")
            update_expression_parts.append('stripe_subscription_id = :sub_id')
            update_expression_parts.append('subscription_status = :status')
            update_expression_parts.append('updated_at = :now')
            expression_values[':sub_id'] = subscription_id
            expression_values[':status'] = status
            expression_values[':now'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        elif event_type == 'customer.subscription.updated':
            print(f"🔄 Subscription updated")
            # Get plan from subscription items
            items = subscription.get('items', {}).get('data', [])
            if items:
                price_id = items[0].get('price', {}).get('id')
                # Map price ID to plan
                plan = map_price_to_plan(price_id)
                print(f"   Plan: {plan}")
                
                update_expression_parts.append('plan = :plan')
                expression_values[':plan'] = plan
            
            update_expression_parts.append('subscription_status = :status')
            update_expression_parts.append('updated_at = :now')
            expression_values[':status'] = status
            expression_values[':now'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            
            if current_period_end:
                update_expression_parts.append('subscription_period_end = :period_end')
                expression_values[':period_end'] = current_period_end
        
        elif event_type == 'customer.subscription.deleted':
            print(f"Subscription deleted/canceled")
            update_expression_parts.append('subscription_status = :status')
            update_expression_parts.append('plan = :plan')
            update_expression_parts.append('updated_at = :now')
            expression_values[':status'] = 'canceled'
            expression_values[':plan'] = 'free'
            expression_values[':now'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        elif event_type == 'customer.subscription.trial_will_end':
            print(f"Trial ending soon")
            # Send email notification (implement later)
            pass
        
        # Update user in DynamoDB
        if update_expression_parts:
            users_table.update_item(
                Key={'id': user_id},
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_values
            )
            print(f"User updated: {user.get('email')}")
        
        return create_response(200, {
            'received': True,
            'processed': True,
            'event_type': event_type
        })
    
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': str(e)})


def handle_invoice_event(event_type, invoice):
    """Handle invoice-related events"""
    print(f"🧾 Processing invoice event: {event_type}")
    
    customer_id = invoice.get('customer')
    invoice_id = invoice.get('id')
    amount_paid = invoice.get('amount_paid', 0)
    status = invoice.get('status')
    currency = invoice.get('currency', 'usd')
    invoice_pdf = invoice.get('invoice_pdf')  # PDF URL from Stripe
    invoice_number = invoice.get('number')  # Human-readable invoice number
    
    print(f"   Customer: {customer_id}")
    print(f"   Invoice: {invoice_id}")
    print(f"   Amount: ${amount_paid / 100}")
    print(f"   Status: {status}")
    print(f"   PDF URL: {invoice_pdf}")
    
    if event_type == 'invoice.paid':
        print(f"Invoice paid successfully")
        
        # Store invoice in billing table
        try:
            from utils.config import dynamodb
            from boto3.dynamodb.conditions import Key, Attr
            import uuid
            from datetime import datetime
            
            billing_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_BILLING'))
            
            # Find user by Stripe customer ID
            users_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_USERS'))
            user_response = users_table.scan(
                FilterExpression=Attr('stripe_customer_id').eq(customer_id)
            )
            
            if user_response.get('Items'):
                user = user_response['Items'][0]
                user_id = user.get('id')
                
                # Get subscription to determine plan
                subscription_id = invoice.get('subscription')
                plan = 'free'  # Default to free if no subscription found
                if subscription_id:
                    subscriptions_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SUBSCRIPTIONS'))
                    # Use scan with filter since we don't know if GSI exists or its key schema
                    sub_response = subscriptions_table.scan(
                        FilterExpression=Attr('stripe_subscription_id').eq(subscription_id)
                    )
                    if sub_response.get('Items'):
                        plan = sub_response['Items'][0].get('plan') or 'free'
                        print(f"   Found subscription plan: {plan}")
                    else:
                        print(f"   No subscription found for ID: {subscription_id}")
                
                # Store billing record
                billing_id = str(uuid.uuid4())
                billing_table.put_item(Item={
                    'id': billing_id,
                    'user_id': user_id,
                    'stripe_invoice_id': invoice_id,
                    'stripe_customer_id': customer_id,
                    'amount': amount_paid / 100,  # Convert from cents to dollars
                    'currency': currency,
                    'status': status,
                    'plan': plan,
                    'invoice_pdf': invoice_pdf,  # Store PDF URL
                    'invoice_number': invoice_number,  # Store invoice number
                    'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
                    'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                })
                
                print(f"Billing record created: {billing_id} for plan: {plan}")
            else:
                print(f" User not found for customer {customer_id}")
                
        except Exception as e:
            print(f"Error storing invoice: {str(e)}")
            import traceback
            traceback.print_exc()
    
    elif event_type == 'invoice.payment_failed':
        print(f"Invoice payment failed")
        # Send payment failure notification
        # User's subscription will be updated by subscription.updated
    
    elif event_type == 'invoice.payment_action_required':
        print(f" Payment action required")
        # Send action required notification
    
    return create_response(200, {
        'received': True,
        'processed': True,
        'event_type': event_type
    })


def handle_customer_event(event_type, customer):
    """Handle customer-related events"""
    print(f"Processing customer event: {event_type}")
    
    customer_id = customer.get('id')
    email = customer.get('email')
    
    print(f"   Customer: {customer_id}")
    print(f"   Email: {email}")
    
    # Most customer events are informational
    # User updates should come from your own API
    
    return create_response(200, {
        'received': True,
        'event_type': event_type
    })


def handle_checkout_event(event_type, session):
    """Handle checkout session events"""
    print(f"🛒 Processing checkout event: {event_type}")
    
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    print(f"   Customer: {customer_id}")
    print(f"   Subscription: {subscription_id}")
    
    if event_type == 'checkout.session.completed':
        print(f"Checkout completed")
        # Subscription will be handled by subscription.created event
        # Just log for tracking
    
    elif event_type == 'checkout.session.expired':
        print(f"Checkout expired")
        # User abandoned checkout
    
    return create_response(200, {
        'received': True,
        'processed': True,
        'event_type': event_type
    })


def map_price_to_plan(price_id):
    """Map Stripe price ID to internal plan name"""
    stripe_price_plus = os.environ.get('STRIPE_PRICE_PLUS')
    stripe_price_pro = os.environ.get('STRIPE_PRICE_PRO')
    
    if price_id == stripe_price_plus:
        return 'plus'
    elif price_id == stripe_price_pro:
        return 'pro'
    else:
        return 'free'

