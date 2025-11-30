"""
Invoice management handlers
"""
import uuid
import os
from datetime import datetime
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
        # Check Plan Limits (Pro Feature)
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        # Invoicing is typically a Pro feature (check feature 'client_invoicing' or plan level)
        # Using explicit plan check or feature flag if defined. 
        # Based on pricing: "Client Invoicing" is in Pro.
        if not features.get('client_invoicing') and 'pro' not in str(user.get('plan', '')).lower() and 'ultimate' not in str(user.get('plan', '')).lower():
             return create_response(403, {
                 'error': 'Client Invoicing is available on Pro and Ultimate plans.',
                 'upgrade_required': True
             })

        # Validate required fields
        if 'client_email' not in body or 'items' not in body:
            return create_response(400, {'error': 'Missing required fields'})
            
        invoice_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Calculate total
        total = Decimal('0.00')
        items = body.get('items', [])
        for item in items:
            price = Decimal(str(item.get('price', 0)))
            quantity = Decimal(str(item.get('quantity', 1)))
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
            'currency': body.get('currency', 'USD'),
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
                price = Decimal(str(item.get('price', 0)))
                quantity = Decimal(str(item.get('quantity', 1)))
                total += price * quantity
                item['price'] = price
                item['quantity'] = quantity
                new_items.append(item)
            invoice['items'] = new_items
            invoice['total_amount'] = total
            
        invoice['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
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

def handle_send_invoice(invoice_id, user):
    """Send invoice to client via email"""
    try:
        response = invoices_table.get_item(Key={'id': invoice_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
            
        invoice = response['Item']
        if invoice['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        # Update status to sent
        invoice['status'] = 'sent'
        invoice['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        invoices_table.put_item(Item=invoice)
        
        # Send Email Logic here
        try:
            photographer_name = user.get('name', 'Your Photographer')
            frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
            
            # Simple text email for now
            subject = f"Invoice #{invoice_id[:8]} from {photographer_name}"
            
            # Format items
            items_html = ""
            for item in invoice.get('items', []):
                items_html += f"<li>{item.get('description', 'Item')}: {item.get('quantity',1)} x {item.get('price',0)}</li>"
                
            body_html = f"""
            <h2>Invoice from {photographer_name}</h2>
            <p>Hi {invoice.get('client_name','')},</p>
            <p>Please find details for your invoice below:</p>
            <ul>
                {items_html}
            </ul>
            <p><strong>Total: {invoice['total_amount']} {invoice['currency']}</strong></p>
            <p>Due Date: {invoice.get('due_date', 'Upon Receipt')}</p>
            <p>Notes: {invoice.get('notes', '')}</p>
            """
            
            send_email(
                to_addresses=[invoice['client_email']],
                subject=subject,
                body_html=body_html,
                body_text=f"Invoice from {photographer_name}. Total: {invoice['total_amount']} {invoice['currency']}"
            )
        except Exception as email_err:
            print(f"Failed to send email: {email_err}")
            return create_response(500, {'error': 'Invoice updated but failed to send email'})
            
        return create_response(200, {'message': 'Invoice sent successfully', 'invoice': invoice})
    except Exception as e:
        print(f"Error sending invoice: {str(e)}")
        return create_response(500, {'error': 'Failed to send invoice'})

