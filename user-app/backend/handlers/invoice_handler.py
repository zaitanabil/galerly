"""
Invoice management handlers
"""
import uuid
import os
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from utils.config import invoices_table, users_table
from utils.response import create_response
from utils.email import send_email

def handle_list_invoices(user, query_params=None):
    """List all invoices for this user"""
    try:
        response = invoices_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        invoices = response.get('Items', [])
        
        # Sort by created_at desc
        invoices.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return create_response(200, {'invoices': invoices})
    except Exception as e:
        print(f"Error listing invoices: {str(e)}")
        return create_response(500, {'error': 'Failed to list invoices'})

def handle_create_invoice(user, body):
    """Create a new invoice"""
    try:
        # Check Plan Limits
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('client_invoicing'):
             return create_response(403, {
                 'error': 'Client Invoicing is available on Pro and Ultimate plans.',
                 'upgrade_required': True
             })

        # Validate required fields
        if 'client_email' not in body or 'items' not in body:
            return create_response(400, {'error': 'Missing required fields'})
            
        invoice_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Calculate total
        total = Decimal('0.00')
        items = body.get('items', [])
        for item in items:
            price = Decimal(str(item.get('price', os.environ.get('DEFAULT_ITEM_PRICE'))))
            quantity = Decimal(str(item.get('quantity', os.environ.get('DEFAULT_ITEM_QUANTITY'))))
            total += price * quantity
            # Ensure decimals are stored as numbers or strings that DynamoDB likes, but Decimal is fine with boto3
            item['price'] = price
            item['quantity'] = quantity
            
        invoice = {
            'id': invoice_id,
            'user_id': user['id'],
            'client_name': body.get('client_name', ''),
            'client_email': body['client_email'],
            'status': 'draft',
            'due_date': body.get('due_date'),
            'currency': body.get('currency', os.environ.get('DEFAULT_INVOICE_CURRENCY')),
            'items': items,
            'total_amount': total,
            'notes': body.get('notes', ''),
            'created_at': current_time,
            'updated_at': current_time
        }
        
        invoices_table.put_item(Item=invoice)
        
        return create_response(201, invoice)
    except Exception as e:
        print(f"Error creating invoice: {str(e)}")
        return create_response(500, {'error': 'Failed to create invoice'})

def handle_get_invoice(invoice_id, user):
    """Get single invoice"""
    try:
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        invoice = response['Item']
        
        # Verify ownership
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        return create_response(200, invoice)
    except Exception as e:
        print(f"Error getting invoice: {str(e)}")
        return create_response(500, {'error': 'Failed to get invoice'})

def handle_update_invoice(invoice_id, user, body):
    """Update invoice"""
    try:
        # Get existing first
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        invoice = response['Item']
        
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        # Update fields
        updatable_fields = ['client_name', 'client_email', 'due_date', 'currency', 'items', 'notes', 'status']
        for field in updatable_fields:
            if field in body:
                invoice[field] = body[field]
                
        # Recalculate total if items changed
        if 'items' in body:
            total = Decimal('0.00')
            new_items = []
            for item in body['items']:
                price = Decimal(str(item.get('price', os.environ.get('DEFAULT_ITEM_PRICE'))))
                quantity = Decimal(str(item.get('quantity', os.environ.get('DEFAULT_ITEM_QUANTITY'))))
                total += price * quantity
                item['price'] = price
                item['quantity'] = quantity
                new_items.append(item)
            invoice['items'] = new_items
            invoice['total_amount'] = total
            
        invoice['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        invoices_table.put_item(Item=invoice)
        
        return create_response(200, invoice)
    except Exception as e:
        print(f"Error updating invoice: {str(e)}")
        return create_response(500, {'error': 'Failed to update invoice'})

def handle_delete_invoice(invoice_id, user):
    """Delete invoice"""
    try:
        # Get existing first to check owner
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        if response['Item']['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        invoices_table.delete_item(Key={'id': invoice_id})
        
        return create_response(200, {'message': 'Invoice deleted'})
    except Exception as e:
        print(f"Error deleting invoice: {str(e)}")
        return create_response(500, {'error': 'Failed to delete invoice'})


def handle_mark_invoice_paid(invoice_id, user, body):
    """Mark invoice as paid manually or via webhook"""
    try:
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        invoice = response['Item']
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Update invoice status
        invoice['status'] = 'paid'
        invoice['paid_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        invoice['payment_method'] = body.get('payment_method', os.environ.get('DEFAULT_INVOICE_PAYMENT_METHOD'))
        invoice['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Store transaction ID if provided
        if 'transaction_id' in body:
            invoice['transaction_id'] = body['transaction_id']
        
        invoices_table.put_item(Item=invoice)
        
        return create_response(200, {
            'message': 'Invoice marked as paid',
            'invoice': invoice
        })
    except Exception as e:
        print(f"Error marking invoice as paid: {str(e)}")
        return create_response(500, {'error': 'Failed to update invoice'})

def handle_send_invoice(invoice_id, user):
    """Send invoice to client via email with Stripe payment link"""
    try:
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        invoice = response['Item']
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Generate Stripe Payment Link if Stripe is available
        payment_link = None
        try:
            import stripe
            stripe_secret = os.environ.get('STRIPE_SECRET_KEY')
            disable_integration = os.environ.get('DISABLE_STRIPE_INVOICE_INTEGRATION', 'false')
            # Skip Stripe integration if no key or if explicitly disabled for testing
            if stripe_secret and disable_integration.lower() != 'true':
                stripe.api_key = stripe_secret
                
                # Use Stripe Checkout Session instead of Payment Links
                # This creates one-time prices that don't pollute the product catalog
                line_items = []
                for item in invoice.get('items', []):
                    line_items.append({
                        'price_data': {
                            'currency': invoice.get('currency', os.environ.get('DEFAULT_INVOICE_CURRENCY')).lower(),
                            'unit_amount': int(float(item.get('price', os.environ.get('DEFAULT_ITEM_PRICE'))) * 100),  # Convert to cents
                            'product_data': {
                                'name': item.get('description', os.environ.get('DEFAULT_SERVICE_NAME')),
                            },
                        },
                        'quantity': int(item.get('quantity', os.environ.get('DEFAULT_ITEM_QUANTITY'))),
                    })
                
                # Get URLs from environment variables
                frontend_url = os.environ.get('FRONTEND_URL')
                if not frontend_url:
                    raise ValueError("FRONTEND_URL environment variable is required for Stripe integration")
                
                # Create Checkout Session (doesn't create persistent prices)
                checkout_session = stripe.checkout.Session.create(
                    mode='payment',
                    line_items=line_items,
                    success_url=f"{frontend_url}/invoice/{invoice_id}/success",
                    cancel_url=f"{frontend_url}/invoice/{invoice_id}",
                    metadata={
                        'invoice_id': invoice_id,
                        'photographer_id': user['id'],
                        'client_email': invoice['client_email']
                    },
                    invoice_creation={
                        'enabled': True,
                        'invoice_data': {
                            'description': f"Invoice from {user.get('name', os.environ.get('DEFAULT_PHOTOGRAPHER_NAME', 'Your Photographer').replace('_', ' '))}",
                            'metadata': {
                                'invoice_id': invoice_id
                            }
                        }
                    }
                )
                payment_link = checkout_session.url
                
                # Store payment link in invoice
                invoice['stripe_payment_link'] = payment_link
                
        except Exception as stripe_err:
            print(f"Could not create Stripe payment link: {str(stripe_err)}")
            # Continue without payment link
            
        # Update status to sent
        invoice['status'] = 'sent'
        invoice['sent_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        invoice['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        invoices_table.put_item(Item=invoice)
        
        # Send email with payment link
        try:
            photographer_name = user.get('name', os.environ.get('DEFAULT_PHOTOGRAPHER_NAME', 'Your Photographer').replace('_', ' '))
            frontend_url = os.environ.get('FRONTEND_URL')
            
            subject = f"Invoice #{invoice_id[:8]} from {photographer_name}"
            
            # Format items
            items_html = ""
            for item in invoice.get('items', []):
                items_html += f"<li>{item.get('description', os.environ.get('DEFAULT_SERVICE_NAME'))}: {item.get('quantity', os.environ.get('DEFAULT_ITEM_QUANTITY'))} x ${item.get('price', os.environ.get('DEFAULT_ITEM_PRICE'))}</li>"
            
            # Add payment button if link exists
            payment_button = ""
            if payment_link:
                payment_button = f"""
                <div style="margin: 30px 0;">
                    <a href="{payment_link}" 
                       style="display: inline-block; padding: 12px 24px; background-color: #0066CC; 
                              color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                        Pay Invoice Online
                    </a>
                </div>
                """
                
            body_html = f"""
            <h2>Invoice from {photographer_name}</h2>
            <p>Hi {invoice.get('client_name', '')},</p>
            <p>Please find details for your invoice below:</p>
            <ul>
                {items_html}
            </ul>
            <p><strong>Total: ${invoice['total_amount']} {invoice['currency']}</strong></p>
            <p>Due Date: {invoice.get('due_date', os.environ.get('DEFAULT_INVOICE_DUE_DATE', 'Upon Receipt').replace('_', ' '))}</p>
            {payment_button}
            <p>Notes: {invoice.get('notes', '')}</p>
            """
            
            body_text = f"Invoice from {photographer_name}. Total: ${invoice['total_amount']} {invoice['currency']}. "
            if payment_link:
                body_text += f"Pay online: {payment_link}"
            
            send_email(
                to_addresses=[invoice['client_email']],
                subject=subject,
                body_html=body_html,
                body_text=body_text
            )
        except Exception as email_err:
            print(f"Failed to send email: {email_err}")
            return create_response(500, {'error': 'Invoice updated but failed to send email'})
            
        return create_response(200, {
            'message': 'Invoice sent successfully',
            'invoice': invoice,
            'payment_link': payment_link
        })
    except Exception as e:
        print(f"Error sending invoice: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to send invoice'})

