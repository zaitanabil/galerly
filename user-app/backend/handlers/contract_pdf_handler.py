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
        
        # Generate presigned download URL
        if pdf_url.startswith('s3://'):
            url_generator = SecureURLGenerator()
            # Extract S3 key from URL
            pdf_key = '/'.join(pdf_url.split('/')[3:])
            download_url = url_generator.generate_download_url(
                s3_key=pdf_key,
                filename=f"contract_{contract_id}.pdf",
                expiry_minutes=60
            )
        else:
            download_url = pdf_url
        
        return create_response(200, {
            'download_url': download_url,
            'expires_in': 3600,
            'filename': f"contract_{contract_id}.pdf"
        })
        
    except Exception as e:
        print(f"Error downloading contract PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to download PDF: {str(e)}'})


def generate_contract_pdf(contract):
    """
    Generate PDF contract with signatures
    Returns S3 URL of generated PDF
    """
    import os
    
    # Generate HTML for contract
    html = generate_contract_html(contract)
    
    contract_id = contract['id']
    photographer_id = contract['photographer_id']
    filename = f"contracts/{photographer_id}/{contract_id}.pdf"
    
    bucket_name = os.environ.get('S3_BUCKET_NAME', 'galerly-files')
    
    # Placeholder: In production, convert HTML to actual PDF using weasyprint
    # pdf_content = weasyprint.HTML(string=html).write_pdf()
    
    # For now, save HTML (in production, save PDF)
    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=html.encode('utf-8'),
        ContentType='text/html',  # In production: 'application/pdf'
        Metadata={
            'contract_id': contract_id,
            'photographer_id': photographer_id,
            'signed': 'true' if contract.get('signed_at') else 'false'
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
