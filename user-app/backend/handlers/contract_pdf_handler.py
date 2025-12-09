"""
Contract PDF Export Handler
Generate and export contract PDFs with signatures
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

def handle_generate_contract_pdf(event):
    """
    Generate PDF for a signed contract
    POST /contracts/{contract_id}/pdf
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        contract_id = event['pathParameters']['contract_id']
        
        # Get contract
        contracts_table = dynamodb.Table('galerly-contracts')
        response = contracts_table.get_item(Key={'id': contract_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
        
        contract = response['Item']
        
        # Verify ownership
        if contract['photographer_id'] != user['user_id'] and contract.get('client_id') != user.get('user_id'):
            return create_response(403, {'error': 'Unauthorized'})
        
        # Generate PDF
        pdf_url = generate_contract_pdf(contract)
        
        # Update contract with PDF URL
        contracts_table.update_item(
            Key={'id': contract_id},
            UpdateExpression='SET pdf_url = :url, pdf_generated_at = :time',
            ExpressionAttributeValues={
                ':url': pdf_url,
                ':time': datetime.now().isoformat()
            }
        )
        
        return create_response(200, {
            'contract_id': contract_id,
            'pdf_url': pdf_url,
            'expires_in': 3600
        })
        
    except Exception as e:
        print(f"Error generating contract PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to generate PDF: {str(e)}'})


def handle_download_contract_pdf(event):
    """
    Download contract PDF
    GET /contracts/{contract_id}/pdf/download
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user:
            return create_response(403, {'error': 'Unauthorized'})
        
        contract_id = event['pathParameters']['contract_id']
        
        # Get contract
        contracts_table = dynamodb.Table('galerly-contracts')
        response = contracts_table.get_item(Key={'id': contract_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
        
        contract = response['Item']
        
        # Verify ownership
        if contract['photographer_id'] != user['user_id'] and contract.get('client_id') != user.get('user_id'):
            return create_response(403, {'error': 'Unauthorized'})
        
        # Check if PDF exists
        if not contract.get('pdf_url'):
            # Generate if doesn't exist
            pdf_url = generate_contract_pdf(contract)
            contracts_table.update_item(
                Key={'id': contract_id},
                UpdateExpression='SET pdf_url = :url',
                ExpressionAttributeValues={':url': pdf_url}
            )
        else:
            pdf_url = contract['pdf_url']
        
        # Generate presigned download URL for PDF
        if pdf_url.startswith('s3://'):
            url_generator = SecureURLGenerator()
            # Extract S3 key from URL
            pdf_key = '/'.join(pdf_url.split('/')[3:])
            download_url = url_generator.generate_download_url(
                s3_key=pdf_key,
                filename=f"contract_{contract_id}.pdf",  # Binary PDF format
                expiry_minutes=60
            )
        else:
            download_url = pdf_url

        return create_response(200, {
            'download_url': download_url,
            'expires_in': 3600,
            'filename': f"contract_{contract_id}.pdf"  # Binary PDF format
        })
        
    except Exception as e:
        print(f"Error downloading contract PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to download PDF: {str(e)}'})


def generate_contract_pdf(contract):
    """
    Generate binary PDF contract with signatures using reportlab
    Returns S3 URL of generated PDF
    """
    import os
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER
    from datetime import datetime
    
    contract_id = contract['id']
    photographer_id = contract['photographer_id']
    filename = f"contracts/{photographer_id}/{contract_id}.pdf"
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'galerly-files')
    
    # Get photographer details
    users_table = dynamodb.Table('galerly-users')
    photographer = users_table.get_item(Key={'id': photographer_id}).get('Item', {})
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0066CC'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1D1D1F'),
        spaceBefore=12,
        spaceAfter=8,
    )
    
    # Title
    elements.append(Paragraph(f"<b>{contract.get('title', 'Photography Contract')}</b>", title_style))
    elements.append(Spacer(1, 12))
    
    # Parties section
    elements.append(Paragraph("<b>Contract Between:</b>", heading_style))
    
    parties_data = [
        ['Photographer:', photographer.get('business_name', photographer.get('name', ''))],
        ['Email:', photographer.get('email', '')],
        ['', ''],
        ['Client:', contract.get('client_name', '')],
        ['Email:', contract.get('client_email', '')],
    ]
    
    parties_table = Table(parties_data, colWidths=[1.5*inch, 5*inch])
    parties_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 20))
    
    # Contract details
    elements.append(Paragraph("<b>Contract Details:</b>", heading_style))
    
    details_data = [
        ['Contract Date:', datetime.fromisoformat(contract.get('created_at', datetime.now().isoformat())).strftime('%B %d, %Y')],
        ['Event Date:', contract.get('event_date', 'TBD')],
        ['Type:', contract.get('type', 'Photography Services')],
        ['Amount:', f"${float(contract.get('amount', 0)):.2f}"],
    ]
    
    details_table = Table(details_data, colWidths=[1.5*inch, 5*inch])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 20))
    
    # Contract content/terms
    elements.append(Paragraph("<b>Terms and Conditions:</b>", heading_style))
    content = contract.get('content', 'Standard photography contract terms apply.')
    
    # Replace template variables
    content = content.replace('{photographer_name}', photographer.get('business_name', photographer.get('name', '')))
    content = content.replace('{client_name}', contract.get('client_name', ''))
    content = content.replace('{date}', datetime.fromisoformat(contract.get('created_at', datetime.now().isoformat())).strftime('%B %d, %Y'))
    content = content.replace('{amount}', f"${float(contract.get('amount', 0)):.2f}")
    
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            elements.append(Paragraph(para, styles['Normal']))
            elements.append(Spacer(1, 6))
    
    elements.append(Spacer(1, 30))
    
    # Signatures section
    elements.append(Paragraph("<b>Signatures:</b>", heading_style))
    elements.append(Spacer(1, 12))
    
    signed_at = contract.get('signed_at')
    client_signature = contract.get('client_signature', '')
    
    signature_data = [
        ['Photographer:', 'Client:'],
        ['', ''],
        ['_' * 40, '_' * 40],
        [photographer.get('name', ''), contract.get('client_name', '')],
        [f"Date: {datetime.now().strftime('%B %d, %Y')}", 
         f"Date: {datetime.fromisoformat(signed_at).strftime('%B %d, %Y') if signed_at else '_______________'}"],
    ]
    
    if signed_at and client_signature:
        signature_data.insert(1, ['', f"Signed: {client_signature[:30]}..."])
    
    sig_table = Table(signature_data, colWidths=[3.25*inch, 3.25*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(sig_table)
    
    # Status indicator
    if signed_at:
        elements.append(Spacer(1, 20))
        status_para = Paragraph(
            f"<para align='center' color='green'><b>✓ SIGNED ON {datetime.fromisoformat(signed_at).strftime('%B %d, %Y at %I:%M %p')}</b></para>",
            styles['Normal']
        )
        elements.append(status_para)
    
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
        ContentDisposition=f'inline; filename="contract-{contract_id}.pdf"',
        Metadata={
            'contract_id': contract_id,
            'photographer_id': photographer_id,
            'signed': 'true' if signed_at else 'false',
            'content_type': 'contract',
            'generated_at': datetime.now().isoformat()
        }
    )
    
    return f"s3://{bucket_name}/{filename}"


def generate_contract_html(contract):
    """Generate HTML for contract with signatures"""
    
    # Get photographer details
    users_table = dynamodb.Table('galerly-users')
    photographer = users_table.get_item(Key={'id': contract['photographer_id']}).get('Item', {})
    
    # Format contract content (replace variables)
    content = contract.get('content', '')
    content = content.replace('{photographer_name}', photographer.get('business_name', photographer.get('name', '')))
    content = content.replace('{client_name}', contract.get('client_name', ''))
    content = content.replace('{date}', contract.get('created_at', '')[:10])
    
    # Signature section
    signature_html = ''
    if contract.get('signed_at'):
        signature_html = f"""
        <div class="signature-section">
            <h3>Signatures</h3>
            <div class="signature-row">
                <div class="signature-block">
                    <div class="signature-name">{contract.get('client_name')}</div>
                    {f'<img src="{contract.get("signature_url")}" class="signature-image" />' if contract.get('signature_url') else '<div class="signature-text">Digitally Signed</div>'}
                    <div class="signature-date">Signed on: {contract.get('signed_at', '')[:10]}</div>
                    <div class="signature-ip">IP: {contract.get('signature_ip', 'N/A')}</div>
                </div>
                <div class="signature-block">
                    <div class="signature-name">{photographer.get('business_name', photographer.get('name'))}</div>
                    <div class="signature-text">Photographer</div>
                    <div class="signature-date">{contract.get('created_at', '')[:10]}</div>
                </div>
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                margin: 1in;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #1D1D1F;
                line-height: 1.6;
                max-width: 8.5in;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 2px solid #0066CC;
            }}
            .title {{
                font-size: 32px;
                font-weight: bold;
                color: #0066CC;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 18px;
                color: #86868b;
            }}
            .parties {{
                display: flex;
                justify-content: space-between;
                margin: 30px 0;
                padding: 20px;
                background: #f5f5f7;
                border-radius: 8px;
            }}
            .party {{
                flex: 1;
            }}
            .party h3 {{
                font-size: 14px;
                text-transform: uppercase;
                color: #86868b;
                margin-bottom: 10px;
            }}
            .content {{
                margin: 40px 0;
                text-align: justify;
            }}
            .content h2 {{
                color: #0066CC;
                margin-top: 30px;
            }}
            .signature-section {{
                margin-top: 60px;
                page-break-inside: avoid;
            }}
            .signature-row {{
                display: flex;
                justify-content: space-around;
                margin-top: 40px;
            }}
            .signature-block {{
                text-align: center;
                flex: 1;
                max-width: 300px;
            }}
            .signature-name {{
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 20px;
            }}
            .signature-image {{
                max-width: 200px;
                border: 1px solid #d2d2d7;
                border-radius: 4px;
                padding: 10px;
            }}
            .signature-text {{
                padding: 20px;
                border-bottom: 2px solid #1D1D1F;
                margin: 20px 0;
            }}
            .signature-date {{
                color: #86868b;
                margin-top: 10px;
            }}
            .signature-ip {{
                font-size: 12px;
                color: #86868b;
                margin-top: 5px;
            }}
            .footer {{
                margin-top: 60px;
                padding-top: 20px;
                border-top: 1px solid #d2d2d7;
                text-align: center;
                color: #86868b;
                font-size: 12px;
            }}
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 120px;
                color: rgba(0, 102, 204, 0.05);
                pointer-events: none;
                z-index: -1;
            }}
        </style>
    </head>
    <body>
        {f'<div class="watermark">{"SIGNED" if contract.get("signed_at") else "UNSIGNED"}</div>'}
        
        <div class="header">
            <div class="title">{contract.get('title', 'Photography Contract')}</div>
            <div class="subtitle">Contract ID: {contract['id'][:8]}</div>
            <div class="subtitle">Date: {contract.get('created_at', datetime.now().isoformat())[:10]}</div>
        </div>

        <div class="parties">
            <div class="party">
                <h3>Photographer</h3>
                <div><strong>{photographer.get('business_name', photographer.get('name'))}</strong></div>
                <div>{photographer.get('email')}</div>
                <div>{photographer.get('phone', '')}</div>
            </div>
            <div class="party">
                <h3>Client</h3>
                <div><strong>{contract.get('client_name')}</strong></div>
                <div>{contract.get('client_email')}</div>
            </div>
        </div>

        <div class="content">
            {content}
        </div>

        {signature_html}

        <div class="footer">
            <p>This is a legally binding contract.</p>
            <p>Generated by Galerly on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            {f'<p><strong>Contract Status: {"SIGNED" if contract.get("signed_at") else "PENDING SIGNATURE"}</strong></p>'}
        </div>
    </body>
    </html>
    """
    
    return html
