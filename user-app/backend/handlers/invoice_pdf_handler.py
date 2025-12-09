"""
Invoice PDF Generation Handler
Generate PDF invoices for clients
"""

import json
import boto3
from datetime import datetime
from utils.auth import get_user_from_token
from utils.response import create_response
from utils.secure_url_generator import SecureURLGenerator
from utils.config import get_dynamodb, get_s3_client

dynamodb = get_dynamodb()
s3 = get_s3_client()

def handle_generate_invoice_pdf(event):
    """
    Generate PDF for an invoice
    POST /invoices/{invoice_id}/pdf
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        invoice_id = event['pathParameters']['invoice_id']
        
        # Get invoice
        invoices_table = dynamodb.Table('galerly-invoices')
        response = invoices_table.get_item(Key={'id': invoice_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
        
        invoice = response['Item']
        
        # Verify ownership
        if invoice['photographer_id'] != user['user_id'] and invoice.get('client_id') != user.get('user_id'):
            return create_response(403, {'error': 'Unauthorized'})
        
        # Generate PDF
        pdf_url = generate_invoice_pdf(invoice)
        
        # Update invoice with PDF URL
        invoices_table.update_item(
            Key={'id': invoice_id},
            UpdateExpression='SET pdf_url = :url, pdf_generated_at = :time',
            ExpressionAttributeValues={
                ':url': pdf_url,
                ':time': datetime.now().isoformat()
            }
        )
        
        return create_response(200, {
            'invoice_id': invoice_id,
            'pdf_url': pdf_url,
            'expires_in': 3600
        })
        
    except Exception as e:
        print(f"Error generating invoice PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to generate PDF: {str(e)}'})


def handle_download_invoice_pdf(event):
    """
    Download invoice PDF
    GET /invoices/{invoice_id}/pdf/download
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        invoice_id = event['pathParameters']['invoice_id']
        
        # Get invoice
        invoices_table = dynamodb.Table('galerly-invoices')
        response = invoices_table.get_item(Key={'id': invoice_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Invoice not found'})
        
        invoice = response['Item']
        
        # Verify ownership
        if invoice['photographer_id'] != user['user_id'] and invoice.get('client_id') != user.get('user_id'):
            return create_response(403, {'error': 'Unauthorized'})
        
        # Check if PDF exists
        if not invoice.get('pdf_url'):
            # Generate if doesn't exist
            pdf_url = generate_invoice_pdf(invoice)
            invoices_table.update_item(
                Key={'id': invoice_id},
                UpdateExpression='SET pdf_url = :url',
                ExpressionAttributeValues={':url': pdf_url}
            )
        else:
            pdf_url = invoice['pdf_url']
        
        # Generate presigned download URL for PDF
        if pdf_url.startswith('s3://'):
            url_generator = SecureURLGenerator()
            # Extract S3 key from URL
            pdf_key = '/'.join(pdf_url.split('/')[3:])
            download_url = url_generator.generate_download_url(
                s3_key=pdf_key,
                filename=f"invoice_{invoice_id}.pdf",  # Binary PDF format
                expiry_minutes=60
            )
        else:
            download_url = pdf_url
        
        return create_response(200, {
            'download_url': download_url,
            'expires_in': 3600
        })
        
    except Exception as e:
        print(f"Error downloading invoice PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to download PDF: {str(e)}'})


def generate_invoice_pdf(invoice):
    """
    Generate binary PDF invoice using reportlab
    Returns S3 URL of generated PDF
    """
    import os
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from datetime import datetime
    
    invoice_id = invoice['id']
    photographer_id = invoice['photographer_id']
    filename = f"invoices/{photographer_id}/{invoice_id}.pdf"
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'galerly-files')
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0066CC'),
        spaceAfter=30,
    )
    
    right_align = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
    )
    
    # Header - Invoice Title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 12))
    
    # Invoice details in two columns
    invoice_info = [
        [Paragraph(f"<b>Invoice #{invoice.get('invoice_number', invoice_id)}</b>", styles['Normal']), 
         Paragraph(f"<b>Date:</b> {datetime.fromisoformat(invoice.get('created_at', datetime.now().isoformat())).strftime('%B %d, %Y')}", right_align)],
        [Paragraph(f"<b>Status:</b> {invoice.get('status', 'pending').upper()}", styles['Normal']),
         Paragraph(f"<b>Due Date:</b> {datetime.fromisoformat(invoice.get('due_date', datetime.now().isoformat())).strftime('%B %d, %Y')}", right_align)]
    ]
    
    info_table = Table(invoice_info, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 24))
    
    # From/To section
    from_to_data = [
        [Paragraph("<b>From:</b>", styles['Normal']), Paragraph("<b>To:</b>", styles['Normal'])],
        [Paragraph(invoice.get('photographer_name', 'Photographer'), styles['Normal']),
         Paragraph(invoice.get('client_name', 'Client'), styles['Normal'])],
        [Paragraph(invoice.get('photographer_email', ''), styles['Normal']),
         Paragraph(invoice.get('client_email', ''), styles['Normal'])],
    ]
    
    from_to_table = Table(from_to_data, colWidths=[3.25*inch, 3.25*inch])
    from_to_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(from_to_table)
    elements.append(Spacer(1, 24))
    
    # Line items table
    items_data = [['Description', 'Quantity', 'Price', 'Amount']]
    
    for item in invoice.get('items', []):
        qty = item.get('quantity', 1)
        price = float(item.get('price', 0))
        amount = qty * price
        items_data.append([
            item.get('description', ''),
            str(qty),
            f"${price:.2f}",
            f"${amount:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 24))
    
    # Totals
    subtotal = sum(item.get('quantity', 1) * float(item.get('price', 0)) for item in invoice.get('items', []))
    tax = float(invoice.get('tax', 0))
    total = float(invoice.get('total', subtotal + tax))
    
    totals_data = [
        ['', '', 'Subtotal:', f"${subtotal:.2f}"],
        ['', '', 'Tax:', f"${tax:.2f}"],
        ['', '', 'Total:', f"${total:.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[3*inch, 1*inch, 1*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, -1), (-1, -1), 14),
        ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
    ]))
    elements.append(totals_table)
    
    # Notes section
    if invoice.get('notes'):
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(invoice.get('notes', ''), styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Upload to S3
    pdf_content = buffer.getvalue()
    buffer.close()
    
    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=pdf_content,
        ContentType='application/pdf',
        ContentDisposition=f'inline; filename="invoice-{invoice_id}.pdf"',
        Metadata={
            'invoice_id': invoice_id,
            'photographer_id': photographer_id,
            'content_type': 'invoice',
            'generated_at': datetime.now().isoformat()
        }
    )
    
    return f"s3://{bucket_name}/{filename}"


def generate_invoice_html(invoice):
    """Generate HTML for invoice"""
    
    # Get photographer details
    users_table = dynamodb.Table('galerly-users')
    photographer = users_table.get_item(Key={'id': invoice['photographer_id']}).get('Item', {})
    
    # Calculate totals
    line_items = invoice.get('line_items', [])
    subtotal = sum(item.get('amount', 0) for item in line_items)
    tax = invoice.get('tax_amount', 0)
    total = subtotal + tax
    
    # Format items HTML
    items_html = ''
    for item in line_items:
        items_html += f"""
        <tr>
            <td>{item.get('description', '')}</td>
            <td style="text-align: center;">{item.get('quantity', 1)}</td>
            <td style="text-align: right;">${item.get('unit_price', 0):.2f}</td>
            <td style="text-align: right;">${item.get('amount', 0):.2f}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #1D1D1F;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: start;
                margin-bottom: 40px;
                border-bottom: 2px solid #0066CC;
                padding-bottom: 20px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: bold;
                color: #0066CC;
            }}
            .invoice-info {{
                text-align: right;
            }}
            .invoice-number {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .addresses {{
                display: flex;
                justify-content: space-between;
                margin: 30px 0;
            }}
            .address-block {{
                flex: 1;
            }}
            .address-block h3 {{
                font-size: 12px;
                text-transform: uppercase;
                color: #86868b;
                margin-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 30px 0;
            }}
            th {{
                background-color: #f5f5f7;
                padding: 12px;
                text-align: left;
                font-size: 12px;
                text-transform: uppercase;
                color: #86868b;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #f5f5f7;
            }}
            .totals {{
                margin-left: auto;
                width: 300px;
                margin-top: 20px;
            }}
            .totals tr td {{
                border: none;
                padding: 8px 12px;
            }}
            .totals .total-row {{
                font-size: 18px;
                font-weight: bold;
                border-top: 2px solid #0066CC;
            }}
            .payment-info {{
                background: #f5f5f7;
                padding: 20px;
                border-radius: 8px;
                margin-top: 40px;
            }}
            .footer {{
                text-align: center;
                margin-top: 60px;
                padding-top: 20px;
                border-top: 1px solid #f5f5f7;
                color: #86868b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">{photographer.get('business_name', photographer.get('name', 'Galerly'))}</div>
            <div class="invoice-info">
                <div class="invoice-number">INVOICE</div>
                <div>#{invoice.get('invoice_number', invoice['id'][:8])}</div>
                <div style="color: #86868b; margin-top: 10px;">
                    Date: {invoice.get('issue_date', datetime.now().strftime('%B %d, %Y'))}
                </div>
                <div style="color: #86868b;">
                    Due: {invoice.get('due_date', 'Upon receipt')}
                </div>
            </div>
        </div>

        <div class="addresses">
            <div class="address-block">
                <h3>From</h3>
                <div><strong>{photographer.get('business_name', photographer.get('name'))}</strong></div>
                <div>{photographer.get('email')}</div>
                <div>{photographer.get('phone', '')}</div>
                <div>{photographer.get('address', '')}</div>
            </div>
            <div class="address-block">
                <h3>Bill To</h3>
                <div><strong>{invoice.get('client_name')}</strong></div>
                <div>{invoice.get('client_email')}</div>
                <div>{invoice.get('client_phone', '')}</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: center;">Quantity</th>
                    <th style="text-align: right;">Unit Price</th>
                    <th style="text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <table class="totals">
            <tr>
                <td>Subtotal:</td>
                <td style="text-align: right;">${subtotal:.2f}</td>
            </tr>
            <tr>
                <td>Tax:</td>
                <td style="text-align: right;">${tax:.2f}</td>
            </tr>
            <tr class="total-row">
                <td>Total:</td>
                <td style="text-align: right;">${total:.2f}</td>
            </tr>
        </table>

        <div class="payment-info">
            <h3 style="margin-top: 0;">Payment Information</h3>
            <p>Status: <strong style="color: {'#34c759' if invoice.get('status') == 'paid' else '#ff9500'};">{invoice.get('status', 'pending').upper()}</strong></p>
            {f'<p>Paid on: {invoice.get("paid_at", "")[:10]}</p>' if invoice.get('status') == 'paid' else '<p>Please submit payment via the link provided in your email.</p>'}
        </div>

        <div class="footer">
            <p>Thank you for your business!</p>
            <p>{photographer.get('business_name', photographer.get('name'))} | {photographer.get('email')}</p>
        </div>
    </body>
    </html>
    """
    
    return html
