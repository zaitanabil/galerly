"""
GDPR Compliance Handler
Implements GDPR data export (Article 20 - Right to Data Portability)
"""
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import (
    users_table, galleries_table, photos_table, sessions_table,
    billing_table, subscriptions_table, analytics_table,
    client_favorites_table, client_feedback_table, invoices_table,
    appointments_table, contracts_table, seo_settings_table,
    s3_client, S3_BUCKET
)
from utils.response import create_response


def decimal_to_float(obj):
    """Convert Decimal objects to JSON-serializable format"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def handle_export_user_data(user):
    """
    Export all user data in machine-readable format (GDPR Article 20)
    Returns comprehensive JSON with all personal data
    """
    try:
        user_id = user['id']
        user_email = user['email']
        
        print(f"📦 Starting GDPR data export for user: {user_email}")
        
        # Initialize export data structure
        export_data = {
            'export_date': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'user_id': user_id,
            'format_version': '1.0',
            'export_type': 'GDPR Article 20 - Data Portability',
            'data': {}
        }
        
        # 1. User Profile Data
        print(f"  Exporting profile data...")
        user_response = users_table.get_item(Key={'email': user_email})
        if 'Item' in user_response:
            user_data = user_response['Item']
            # Remove sensitive internal fields
            safe_user_data = {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'username': user_data.get('username'),
                'bio': user_data.get('bio'),
                'city': user_data.get('city'),
                'role': user_data.get('role'),
                'plan': user_data.get('plan'),
                'created_at': user_data.get('created_at'),
                'email_verified': user_data.get('email_verified'),
                'watermark_enabled': user_data.get('watermark_enabled'),
                'watermark_text': user_data.get('watermark_text'),
                'watermark_position': user_data.get('watermark_position'),
                'watermark_opacity': user_data.get('watermark_opacity'),
                # NOTE: password_hash, api_key, stripe IDs intentionally excluded
            }
            export_data['data']['profile'] = decimal_to_float(safe_user_data)
        
        # 2. Galleries Data
        print(f"  Exporting galleries...")
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        galleries = galleries_response.get('Items', [])
        export_data['data']['galleries'] = {
            'count': len(galleries),
            'items': decimal_to_float(galleries)
        }
        
        # 3. Photos Data
        print(f"  Exporting photos...")
        all_photos = []
        for gallery in galleries:
            try:
                photos_response = photos_table.query(
                    IndexName='GalleryIdIndex',
                    KeyConditionExpression=Key('gallery_id').eq(gallery['id'])
                )
                all_photos.extend(photos_response.get('Items', []))
            except Exception as e:
                print(f"  Warning: Could not fetch photos for gallery {gallery['id']}: {str(e)}")
        
        export_data['data']['photos'] = {
            'count': len(all_photos),
            'items': decimal_to_float(all_photos)
        }
        
        # 4. Billing History
        print(f"  Exporting billing history...")
        try:
            billing_response = billing_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            billing_records = billing_response.get('Items', [])
            # Mask any payment method details (PCI DSS compliance)
            for record in billing_records:
                if 'payment_method_details' in record:
                    # Mask card numbers if present
                    if isinstance(record['payment_method_details'], dict):
                        if 'last4' in record['payment_method_details']:
                            record['payment_method_details']['card_number'] = f"****{record['payment_method_details']['last4']}"
            
            export_data['data']['billing_history'] = {
                'count': len(billing_records),
                'items': decimal_to_float(billing_records)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch billing history: {str(e)}")
            export_data['data']['billing_history'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 5. Subscription Data
        print(f"  Exporting subscription...")
        try:
            subscription_response = subscriptions_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            subscriptions = subscription_response.get('Items', [])
            export_data['data']['subscriptions'] = {
                'count': len(subscriptions),
                'items': decimal_to_float(subscriptions)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch subscriptions: {str(e)}")
            export_data['data']['subscriptions'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 6. Analytics Data
        print(f"  Exporting analytics...")
        try:
            analytics_response = analytics_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            analytics = analytics_response.get('Items', [])
            export_data['data']['analytics'] = {
                'count': len(analytics),
                'items': decimal_to_float(analytics)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch analytics: {str(e)}")
            export_data['data']['analytics'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 7. Client Favorites (as photographer)
        print(f"  Exporting client favorites...")
        try:
            favorites_response = client_favorites_table.scan(
                FilterExpression=Attr('photographer_id').eq(user_id)
            )
            favorites = favorites_response.get('Items', [])
            export_data['data']['client_favorites'] = {
                'count': len(favorites),
                'items': decimal_to_float(favorites)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch favorites: {str(e)}")
            export_data['data']['client_favorites'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 8. Client Feedback
        print(f"  Exporting client feedback...")
        try:
            feedback_response = client_feedback_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            feedback = feedback_response.get('Items', [])
            export_data['data']['client_feedback'] = {
                'count': len(feedback),
                'items': decimal_to_float(feedback)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch feedback: {str(e)}")
            export_data['data']['client_feedback'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 9. Invoices
        print(f"  Exporting invoices...")
        try:
            invoices_response = invoices_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            invoices = invoices_response.get('Items', [])
            export_data['data']['invoices'] = {
                'count': len(invoices),
                'items': decimal_to_float(invoices)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch invoices: {str(e)}")
            export_data['data']['invoices'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 10. Appointments
        print(f"  Exporting appointments...")
        try:
            appointments_response = appointments_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            appointments = appointments_response.get('Items', [])
            export_data['data']['appointments'] = {
                'count': len(appointments),
                'items': decimal_to_float(appointments)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch appointments: {str(e)}")
            export_data['data']['appointments'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 11. Contracts
        print(f"  Exporting contracts...")
        try:
            contracts_response = contracts_table.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )
            contracts = contracts_response.get('Items', [])
            export_data['data']['contracts'] = {
                'count': len(contracts),
                'items': decimal_to_float(contracts)
            }
        except Exception as e:
            print(f"  Warning: Could not fetch contracts: {str(e)}")
            export_data['data']['contracts'] = {'count': 0, 'items': [], 'error': str(e)}
        
        # 12. SEO Settings
        print(f"  Exporting SEO settings...")
        try:
            seo_response = seo_settings_table.get_item(Key={'user_id': user_id})
            if 'Item' in seo_response:
                export_data['data']['seo_settings'] = decimal_to_float(seo_response['Item'])
        except Exception as e:
            print(f"  Warning: Could not fetch SEO settings: {str(e)}")
        
        # Generate export filename
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"gdpr_export_{user_id}_{timestamp}.json"
        s3_key = f"gdpr-exports/{user_id}/{filename}"
        
        # Upload to S3
        print(f"  Uploading export to S3: {s3_key}")
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(export_data, indent=2, default=str),
            ContentType='application/json',
            ContentDisposition=f'attachment; filename="{filename}"'
        )
        
        # Generate presigned download URL (valid for 1 hour)
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        # Summary statistics
        summary = {
            'total_galleries': len(galleries),
            'total_photos': len(all_photos),
            'total_billing_records': len(billing_records) if 'billing_records' in locals() else 0,
            'export_size_mb': round(len(json.dumps(export_data)) / (1024 * 1024), 2)
        }
        
        print(f"✅ GDPR export completed: {summary['export_size_mb']} MB")
        
        return create_response(200, {
            'message': 'Data export completed successfully',
            'download_url': download_url,
            'filename': filename,
            'expires_in_seconds': 3600,
            'summary': summary,
            'export_date': export_data['export_date']
        })
        
    except Exception as e:
        print(f"❌ Error exporting user data: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Failed to export user data',
            'message': 'An error occurred while preparing your data export. Please try again or contact support.'
        })


def handle_get_data_retention_info(user):
    """
    Get information about data retention policies (GDPR Article 13)
    """
    retention_info = {
        'user_profile': {
            'retention_period': 'Until account deletion',
            'legal_basis': 'Contract performance',
            'can_be_deleted': True
        },
        'photos_and_galleries': {
            'retention_period': 'Until deleted by user or account deletion',
            'legal_basis': 'Contract performance',
            'can_be_deleted': True
        },
        'billing_records': {
            'retention_period': '7 years (tax law requirement)',
            'legal_basis': 'Legal obligation',
            'can_be_deleted': False,
            'note': 'Financial records must be retained for tax compliance'
        },
        'analytics_data': {
            'retention_period': '2 years or until account deletion',
            'legal_basis': 'Legitimate interest',
            'can_be_deleted': True
        },
        'sessions': {
            'retention_period': '7 days (auto-expire)',
            'legal_basis': 'Contract performance',
            'can_be_deleted': True
        },
        'backup_data': {
            'retention_period': '30 days in backups after deletion',
            'legal_basis': 'Legitimate interest (disaster recovery)',
            'can_be_deleted': False,
            'note': 'Deleted data removed from backups after 30 days'
        }
    }
    
    return create_response(200, {
        'data_retention_policy': retention_info,
        'last_updated': '2025-12-09',
        'jurisdiction': 'Switzerland (FADP) and EU (GDPR)',
        'contact': {
            'data_protection_officer': 'privacy@galerly.com',
            'support': 'support@galerly.com'
        }
    })

