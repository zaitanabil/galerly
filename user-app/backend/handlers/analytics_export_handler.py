"""
Analytics Export Handler
Export analytics data in CSV/PDF formats
"""

import json
import csv
import io
from datetime import datetime, timedelta
import boto3
from utils.auth import get_user_from_token
from utils.response import create_response
from utils.config import get_dynamodb, get_s3_client

dynamodb = get_dynamodb()
s3 = get_s3_client()

def handle_export_analytics_csv(event):
    """
    Export analytics data to CSV format
    GET /analytics/export/csv?start_date=...&end_date=...&type=...
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user or user.get('role') != 'photographer':
            return create_response(403, {'error': 'Unauthorized'})
        
        photographer_id = user['user_id']
        params = event.get('queryStringParameters') or {}
        
        # Parse parameters
        export_type = params.get('type', 'summary')  # summary, galleries, photos, clients
        start_date = params.get('start_date')
        end_date = params.get('end_date', datetime.now().isoformat())
        
        # Default to last 30 days if no start date
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Fetch data based on type
        csv_data = []
        
        if export_type == 'summary':
            csv_data = generate_summary_csv(photographer_id, start_date, end_date)
        elif export_type == 'galleries':
            csv_data = generate_galleries_csv(photographer_id, start_date, end_date)
        elif export_type == 'photos':
            csv_data = generate_photos_csv(photographer_id, start_date, end_date)
        elif export_type == 'clients':
            csv_data = generate_clients_csv(photographer_id, start_date, end_date)
        elif export_type == 'revenue':
            csv_data = generate_revenue_csv(photographer_id, start_date, end_date)
        else:
            return create_response(400, {'error': 'Invalid export type'})
        
        # Generate CSV
        output = io.StringIO()
        if csv_data:
            writer = csv.DictWriter(output, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
        
        csv_content = output.getvalue()
        
        # Return CSV with proper headers
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename="analytics_{export_type}_{start_date[:10]}_to_{end_date[:10]}.csv"',
                'Access-Control-Allow-Origin': '*'
            },
            'body': csv_content
        }
        
    except Exception as e:
        print(f"Error exporting CSV: {str(e)}")
        return create_response(500, {'error': f'Failed to export CSV: {str(e)}'})


def handle_export_analytics_pdf(event):
    """
    Export analytics data to PDF format
    POST /analytics/export/pdf
    """
    try:
        # Verify authentication
        user = get_user_from_token(event)
        if not user or user.get('role') != 'photographer':
            return create_response(403, {'error': 'Unauthorized'})
        
        photographer_id = user['user_id']
        
        body = json.loads(event.get('body', '{}'))
        report_type = body.get('type', 'summary')
        start_date = body.get('start_date')
        end_date = body.get('end_date', datetime.now().isoformat())
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Generate PDF (simplified - in production use reportlab or weasyprint)
        pdf_url = generate_pdf_report(photographer_id, report_type, start_date, end_date)
        
        return create_response(200, {
            'pdf_url': pdf_url,
            'expires_in': 3600
        })
        
    except Exception as e:
        print(f"Error exporting PDF: {str(e)}")
        return create_response(500, {'error': f'Failed to export PDF: {str(e)}'})


def generate_summary_csv(photographer_id, start_date, end_date):
    """Generate summary statistics CSV"""
    analytics_table = dynamodb.Table('galerly-analytics')
    
    try:
        response = analytics_table.query(
            KeyConditionExpression='photographer_id = :pid AND date BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':pid': photographer_id,
                ':start': start_date[:10],
                ':end': end_date[:10]
            }
        )
        
        rows = []
        for item in response.get('Items', []):
            rows.append({
                'Date': item.get('date'),
                'Gallery Views': item.get('gallery_views', 0),
                'Photo Views': item.get('photo_views', 0),
                'Downloads': item.get('downloads', 0),
                'Favorites': item.get('favorites', 0),
                'Shares': item.get('shares', 0),
                'New Clients': item.get('new_clients', 0),
                'Revenue': f"${item.get('revenue', 0):.2f}"
            })
        
        return rows
    except Exception as e:
        print(f"Error generating summary CSV: {str(e)}")
        return []


def generate_galleries_csv(photographer_id, start_date, end_date):
    """Generate galleries CSV"""
    galleries_table = dynamodb.Table('galerly-galleries')
    
    try:
        response = galleries_table.query(
            IndexName='photographer_created_index',
            KeyConditionExpression='photographer_id = :pid',
            ExpressionAttributeValues={
                ':pid': photographer_id
            }
        )
        
        rows = []
        for gallery in response.get('Items', []):
            created = gallery.get('created_at', '')
            if start_date <= created <= end_date:
                rows.append({
                    'Gallery ID': gallery.get('id'),
                    'Name': gallery.get('name'),
                    'Client': gallery.get('client_email', 'N/A'),
                    'Photos': gallery.get('photo_count', 0),
                    'Views': gallery.get('views', 0),
                    'Downloads': gallery.get('downloads', 0),
                    'Status': 'Public' if gallery.get('is_public') else 'Private',
                    'Created': created[:10]
                })
        
        return rows
    except Exception as e:
        print(f"Error generating galleries CSV: {str(e)}")
        return []


def generate_photos_csv(photographer_id, start_date, end_date):
    """Generate photos CSV"""
    photos_table = dynamodb.Table('galerly-photos')
    
    try:
        response = photos_table.query(
            IndexName='photographer_upload_index',
            KeyConditionExpression='photographer_id = :pid',
            ExpressionAttributeValues={
                ':pid': photographer_id
            }
        )
        
        rows = []
        for photo in response.get('Items', []):
            uploaded = photo.get('uploaded_at', '')
            if start_date <= uploaded <= end_date:
                rows.append({
                    'Photo ID': photo.get('id'),
                    'Gallery': photo.get('gallery_name', 'N/A'),
                    'Filename': photo.get('filename'),
                    'Size (MB)': f"{photo.get('file_size', 0) / (1024*1024):.2f}",
                    'Views': photo.get('views', 0),
                    'Downloads': photo.get('downloads', 0),
                    'Favorited': 'Yes' if photo.get('is_favorite') else 'No',
                    'Uploaded': uploaded[:10]
                })
        
        return rows
    except Exception as e:
        print(f"Error generating photos CSV: {str(e)}")
        return []


def generate_clients_csv(photographer_id, start_date, end_date):
    """Generate clients CSV"""
    leads_table = dynamodb.Table('galerly-leads')
    
    try:
        response = leads_table.query(
            KeyConditionExpression='photographer_id = :pid',
            ExpressionAttributeValues={
                ':pid': photographer_id
            }
        )
        
        rows = []
        for lead in response.get('Items', []):
            created = lead.get('created_at', '')
            if start_date <= created <= end_date:
                rows.append({
                    'Name': lead.get('name'),
                    'Email': lead.get('email'),
                    'Phone': lead.get('phone', 'N/A'),
                    'Status': lead.get('status'),
                    'Quality': lead.get('quality'),
                    'Score': lead.get('score', 0),
                    'Source': lead.get('source'),
                    'Created': created[:10]
                })
        
        return rows
    except Exception as e:
        print(f"Error generating clients CSV: {str(e)}")
        return []


def generate_revenue_csv(photographer_id, start_date, end_date):
    """Generate revenue CSV"""
    sales_table = dynamodb.Table('galerly-sales')
    
    try:
        response = sales_table.query(
            IndexName='photographer_date_index',
            KeyConditionExpression='photographer_id = :pid',
            ExpressionAttributeValues={
                ':pid': photographer_id
            }
        )
        
        rows = []
        for sale in response.get('Items', []):
            created = sale.get('created_at', '')
            if start_date <= created <= end_date:
                rows.append({
                    'Transaction ID': sale.get('id'),
                    'Client': sale.get('client_email'),
                    'Type': sale.get('purchase_type'),
                    'Item': sale.get('item_name', 'N/A'),
                    'Amount': f"${sale.get('amount', 0) / 100:.2f}",
                    'Status': sale.get('status'),
                    'Date': created[:10]
                })
        
        return rows
    except Exception as e:
        print(f"Error generating revenue CSV: {str(e)}")
        return []


def generate_pdf_report(photographer_id, report_type, start_date, end_date):
    """
    Generate PDF report (simplified implementation)
    In production, use reportlab or weasyprint for proper PDF generation
    """
    # For now, return a placeholder URL
    # In production, generate actual PDF and upload to S3
    
    filename = f"analytics_{report_type}_{photographer_id}_{datetime.now().timestamp()}.pdf"
    
    # Generate simple HTML that can be converted to PDF
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; }}
            h1 {{ color: #0066CC; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #0066CC; color: white; }}
        </style>
    </head>
    <body>
        <h1>Analytics Report - {report_type.title()}</h1>
        <p>Period: {start_date[:10]} to {end_date[:10]}</p>
        <p>Photographer ID: {photographer_id}</p>
        <p><em>Full PDF generation will be implemented with reportlab/weasyprint</em></p>
    </body>
    </html>
    """
    
    # Return presigned URL (placeholder)
    return f"/api/v1/analytics/reports/{filename}"
