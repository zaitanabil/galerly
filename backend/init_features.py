#!/usr/bin/env python3
"""
Initialize Galerly Features
Populates the features table with default feature definitions
"""
import os
import boto3
import time
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:4566') # Default to LocalStack
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_FEATURES', 'galerly-features-local')

def get_dynamodb_resource():
    """Get DynamoDB resource"""
    return boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'test'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
    )

FEATURES = [
    # Visual Asset Management (Storage)
    {"id": "storage_2gb", "name": "Smart Cloud Storage (2 GB)", "category": "storage", "value": 2147483648, "unit": "bytes", "display": "2 GB Storage"},
    {"id": "storage_25gb", "name": "Smart Cloud Storage (25 GB)", "category": "storage", "value": 26843545600, "unit": "bytes", "display": "25 GB Storage"},
    {"id": "storage_100gb", "name": "Smart Cloud Storage (100 GB)", "category": "storage", "value": 107374182400, "unit": "bytes", "display": "100 GB Storage"},
    {"id": "storage_500gb", "name": "Smart Cloud Storage (500 GB)", "category": "storage", "value": 536870912000, "unit": "bytes", "display": "500 GB Storage"},
    {"id": "storage_2tb", "name": "Smart Cloud Storage (2 TB)", "category": "storage", "value": 2199023255552, "unit": "bytes", "display": "2 TB Storage"},
    {"id": "storage_unlimited", "name": "Smart Cloud Storage (Unlimited)", "category": "storage", "value": -1, "unit": "bytes", "display": "Unlimited Storage"},

    # Visual Asset Management (Video)
    {"id": "video_none", "name": "No Video Streaming", "category": "video", "value": 0, "unit": "minutes", "resolution": "None", "display": "No Video"},
    {"id": "video_30min_hd", "name": "HD Video Streaming (30 min)", "category": "video", "value": 30, "unit": "minutes", "resolution": "HD", "display": "30 Min HD Video"},
    {"id": "video_60min_hd", "name": "HD Video Streaming (1 Hour)", "category": "video", "value": 60, "unit": "minutes", "resolution": "HD", "display": "1 Hour HD Video"},
    {"id": "video_4hr_4k", "name": "4K Video Streaming (4 Hours)", "category": "video", "value": 240, "unit": "minutes", "resolution": "4K", "display": "4 Hours 4K Video"},
    {"id": "video_10hr_4k", "name": "4K Video Streaming (10 Hours)", "category": "video", "value": 600, "unit": "minutes", "resolution": "4K", "display": "10 Hours 4K Video"},

    # Brand Identity Suite
    {"id": "branding_on", "name": "Galerly Branding", "category": "branding", "enabled": True, "display": "Galerly Branding"},
    {"id": "no_branding", "name": "White-Label Experience", "category": "branding", "enabled": True, "display": "Remove Galerly Branding"},
    {"id": "custom_domain", "name": "Custom Domain Integration", "category": "branding", "enabled": True, "display": "Custom Domain"},
    {"id": "watermarking", "name": "Automated Watermarking", "category": "branding", "enabled": True, "display": "Watermarking"},
    
    # Client Experience & Workflow
    {"id": "client_proofing", "name": "Client Proofing & Favorites", "category": "workflow", "enabled": True, "display": "Client Favorites"},
    {"id": "unlimited_galleries", "name": "Unlimited Active Galleries", "category": "workflow", "enabled": True, "display": "Unlimited Galleries"},
    {"id": "raw_support", "name": "RAW Photo Support", "category": "workflow", "enabled": True, "display": "RAW Support"},
    {"id": "raw_vault", "name": "RAW Archival Vault (Glacier)", "category": "workflow", "enabled": True, "display": "RAW Vault"},
    {"id": "lightroom_workflow", "name": "Lightroom Integration Workflow", "category": "workflow", "enabled": True, "display": "Lightroom Workflow"},
    
    # Studio Command Center
    {"id": "email_templates", "name": "Email Templates", "category": "studio", "enabled": True, "display": "Email Templates"},
    {"id": "smart_invoicing", "name": "Smart Invoicing & Payments", "category": "studio", "enabled": True, "display": "Invoicing"},
    {"id": "esignatures", "name": "eSignatures & Audit Trails", "category": "studio", "enabled": True, "display": "eSignatures"},
    {"id": "scheduler", "name": "Intelligent Scheduler", "category": "studio", "enabled": True, "display": "Scheduler"},
    {"id": "seo_tools", "name": "SEO Optimization Tools", "category": "studio", "enabled": True, "display": "SEO Tools"},

    # Analytics & Support
    {"id": "analytics_basic", "name": "Basic Analytics", "category": "analytics", "enabled": True, "display": "Basic Analytics"},
    {"id": "analytics_advanced", "name": "Advanced Analytics", "category": "analytics", "enabled": True, "display": "Advanced Analytics"},
    {"id": "analytics_pro", "name": "Pro Analytics & Insights", "category": "analytics", "enabled": True, "display": "Pro Analytics"}
]

def init_features():
    print(f"🔧 Initializing Features in {TABLE_NAME}...")
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)

    # Wait for table to exist
    try:
        table.load()
    except ClientError:
        print(f"❌ Table {TABLE_NAME} does not exist. Please run setup_dynamodb.py first.")
        return

    count = 0
    with table.batch_writer() as batch:
        for feature in FEATURES:
            # Add timestamps
            item = feature.copy()
            item['created_at'] = int(time.time())
            item['updated_at'] = int(time.time())
            
            batch.put_item(Item=item)
            count += 1
            print(f"  ✅ Added: {feature['name']} ({feature['id']})")

    print(f"\n🎉 Successfully initialized {count} features!")

if __name__ == '__main__':
    init_features()
