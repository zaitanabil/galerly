#!/usr/bin/env python3
"""
Galerly - Gallery Data Cleanup Script
Removes all galleries, photos, and related data while preserving users

⚠️  WARNING: This script will permanently delete:
   - All galleries
   - All photos (metadata AND S3 files)
   - All analytics data
   - All client favorites
   - All client feedback
   
✅ This script PRESERVES:
   - Users accounts (can still login)
   - Sessions (active logins remain)
   - Notification preferences
   - Newsletters
   - Contact/support tickets
   - Website visitor tracking

🤔 Optional cleanup (you choose):
   - Billing records
   - Subscriptions
   - Refunds
   - Audit logs
"""
import boto3
import sys
from typing import Dict, List
from botocore.exceptions import ClientError
import time

# Initialize AWS clients
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')

# Configuration
S3_PHOTOS_BUCKET = 'galerly-images-storage'

# Tables to clean
TABLES_TO_CLEAN = {
    'galerly-galleries': {
        'description': 'Photo galleries',
        'required': True,
        'has_s3_data': False
    },
    'galerly-photos': {
        'description': 'Photo metadata',
        'required': True,
        'has_s3_data': True  # Also delete S3 files
    },
    'galerly-analytics': {
        'description': 'Gallery analytics/tracking',
        'required': True,
        'has_s3_data': False
    },
    'galerly-client-favorites': {
        'description': 'Client photo selections',
        'required': True,
        'has_s3_data': False
    },
    'galerly-client-feedback': {
        'description': 'Client gallery feedback',
        'required': True,
        'has_s3_data': False
    },
    'galerly-billing': {
        'description': 'Billing records (payment history)',
        'required': False,
        'has_s3_data': False
    },
    'galerly-subscriptions': {
        'description': 'Stripe subscription data',
        'required': False,
        'has_s3_data': False
    },
    'galerly-refunds': {
        'description': 'Refund requests/history',
        'required': False,
        'has_s3_data': False
    },
    'galerly-audit-log': {
        'description': 'Audit trail/change logs',
        'required': False,
        'has_s3_data': False
    }
}

# Tables that will be PRESERVED
PRESERVED_TABLES = [
    'galerly-users',
    'galerly-sessions',
    'galerly-notification-preferences',
    'galerly-newsletters',
    'galerly-contact',
    'galerly-visitor-tracking'
]


def get_table_item_count(table_name: str) -> int:
    """Get approximate item count from a table"""
    try:
        response = dynamodb.describe_table(TableName=table_name)
        return response['Table'].get('ItemCount', 0)
    except ClientError:
        return 0


def scan_and_delete_table(table_name: str, dry_run: bool = False) -> Dict:
    """Scan and delete all items from a DynamoDB table"""
    table = dynamodb_resource.Table(table_name)
    deleted_count = 0
    errors = 0
    
    print(f"\n📋 Scanning {table_name}...")
    
    try:
        # Get table key schema
        response = dynamodb.describe_table(TableName=table_name)
        key_schema = response['Table']['KeySchema']
        key_names = [key['AttributeName'] for key in key_schema]
        
        # Scan and delete in batches
        scan_kwargs = {}
        
        while True:
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            if not items:
                break
            
            print(f"   Processing batch of {len(items)} items...")
            
            # Delete items in batch
            with table.batch_writer() as batch:
                for item in items:
                    # Extract key attributes
                    key = {k: item[k] for k in key_names}
                    
                    if not dry_run:
                        try:
                            batch.delete_item(Key=key)
                            deleted_count += 1
                        except Exception as e:
                            print(f"   ⚠️  Error deleting item: {str(e)}")
                            errors += 1
                    else:
                        deleted_count += 1
            
            # Check for more items
            if 'LastEvaluatedKey' not in response:
                break
            
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            
            # Rate limiting to avoid throttling
            time.sleep(0.5)
        
        return {
            'deleted': deleted_count,
            'errors': errors,
            'success': True
        }
        
    except Exception as e:
        print(f"   ❌ Error processing {table_name}: {str(e)}")
        return {
            'deleted': 0,
            'errors': 1,
            'success': False,
            'error': str(e)
        }


def delete_s3_photos(dry_run: bool = False) -> Dict:
    """Delete all photos from S3 bucket"""
    print(f"\n🗑️  Deleting photos from S3 bucket: {S3_PHOTOS_BUCKET}")
    
    deleted_count = 0
    errors = 0
    total_size = 0
    
    try:
        # List all objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_PHOTOS_BUCKET)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            objects = page['Contents']
            print(f"   Found {len(objects)} objects in this batch...")
            
            if not dry_run:
                # Delete in batches of 1000 (S3 limit)
                for i in range(0, len(objects), 1000):
                    batch = objects[i:i + 1000]
                    delete_keys = [{'Key': obj['Key']} for obj in batch]
                    
                    try:
                        response = s3_client.delete_objects(
                            Bucket=S3_PHOTOS_BUCKET,
                            Delete={'Objects': delete_keys}
                        )
                        deleted_count += len(response.get('Deleted', []))
                        errors += len(response.get('Errors', []))
                    except Exception as e:
                        print(f"   ⚠️  Error deleting batch: {str(e)}")
                        errors += len(batch)
            else:
                deleted_count += len(objects)
            
            # Calculate total size
            for obj in objects:
                total_size += obj.get('Size', 0)
        
        size_mb = total_size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        return {
            'deleted': deleted_count,
            'errors': errors,
            'size_mb': size_mb,
            'size_gb': size_gb,
            'success': errors == 0
        }
        
    except Exception as e:
        print(f"   ❌ Error accessing S3: {str(e)}")
        return {
            'deleted': 0,
            'errors': 1,
            'success': False,
            'error': str(e)
        }


def show_preview():
    """Show what will be deleted"""
    print("\n" + "=" * 80)
    print("📊 CLEANUP PREVIEW")
    print("=" * 80)
    
    print("\n✅ TABLES THAT WILL BE PRESERVED:")
    for table in PRESERVED_TABLES:
        count = get_table_item_count(table)
        print(f"   • {table:40} {count:>8} items")
    
    print("\n❌ TABLES THAT WILL BE CLEANED (all data deleted):")
    total_to_delete = 0
    for table_name, info in TABLES_TO_CLEAN.items():
        if info['required']:
            count = get_table_item_count(table_name)
            total_to_delete += count
            s3_marker = " + S3 files" if info['has_s3_data'] else ""
            print(f"   • {table_name:40} {count:>8} items{s3_marker}")
    
    print("\n⚠️  OPTIONAL CLEANUP (you can choose):")
    optional_count = 0
    for table_name, info in TABLES_TO_CLEAN.items():
        if not info['required']:
            count = get_table_item_count(table_name)
            optional_count += count
            print(f"   • {table_name:40} {count:>8} items - {info['description']}")
    
    print(f"\n📊 Total items to delete: {total_to_delete:,} (required) + {optional_count:,} (optional)")
    
    # S3 Preview
    print("\n🗑️  S3 STORAGE:")
    try:
        response = s3_client.list_objects_v2(Bucket=S3_PHOTOS_BUCKET, MaxKeys=1)
        if 'Contents' in response:
            print(f"   • Bucket: {S3_PHOTOS_BUCKET}")
            print(f"   • Action: ALL PHOTOS WILL BE DELETED")
        else:
            print(f"   • Bucket: {S3_PHOTOS_BUCKET} (empty)")
    except Exception as e:
        print(f"   ⚠️  Cannot access S3 bucket: {str(e)}")
    
    print("\n" + "=" * 80)


def run_cleanup(include_optional: bool = False, dry_run: bool = False):
    """Execute the cleanup operation"""
    mode = "🔍 DRY RUN MODE" if dry_run else "🔥 LIVE MODE - DELETING DATA"
    print(f"\n{mode}")
    print("=" * 80)
    
    results = {}
    
    # Delete DynamoDB data
    for table_name, info in TABLES_TO_CLEAN.items():
        # Skip optional tables if not included
        if not info['required'] and not include_optional:
            continue
        
        print(f"\n🗑️  Cleaning {table_name} ({info['description']})...")
        result = scan_and_delete_table(table_name, dry_run)
        results[table_name] = result
        
        if result['success']:
            action = "Would delete" if dry_run else "Deleted"
            print(f"   ✅ {action} {result['deleted']:,} items")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Delete S3 photos
    if not dry_run or True:  # Always show S3 info
        s3_result = delete_s3_photos(dry_run)
        results['s3_photos'] = s3_result
        
        if s3_result['success']:
            action = "Would delete" if dry_run else "Deleted"
            print(f"\n   ✅ {action} {s3_result['deleted']:,} files ({s3_result['size_gb']:.2f} GB)")
        else:
            print(f"   ❌ Failed: {s3_result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 CLEANUP SUMMARY")
    print("=" * 80)
    
    total_items = sum(r['deleted'] for r in results.values() if 'deleted' in r)
    total_errors = sum(r['errors'] for r in results.values() if 'errors' in r)
    
    action = "Would be deleted" if dry_run else "Deleted"
    print(f"\n✅ {action}:")
    print(f"   • DynamoDB items: {total_items:,}")
    if 's3_photos' in results:
        print(f"   • S3 files: {results['s3_photos']['deleted']:,} ({results['s3_photos']['size_gb']:.2f} GB)")
    
    if total_errors > 0:
        print(f"\n⚠️  Errors encountered: {total_errors}")
    
    print("\n" + "=" * 80)


def main():
    """Main function"""
    print("=" * 80)
    print("🧹 GALERLY - GALLERY DATA CLEANUP")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python cleanup_galleries.py preview                   # Show what will be deleted")
        print("  python cleanup_galleries.py dry-run                   # Simulate deletion (safe)")
        print("  python cleanup_galleries.py dry-run --include-billing # Include billing data")
        print("  python cleanup_galleries.py execute                   # ⚠️  ACTUALLY DELETE DATA")
        print("  python cleanup_galleries.py execute --include-billing # ⚠️  DELETE + billing data")
        print("")
        return
    
    command = sys.argv[1].lower()
    include_billing = '--include-billing' in sys.argv
    
    if command == 'preview':
        show_preview()
    
    elif command == 'dry-run':
        show_preview()
        print("\n⏳ Running dry-run (no data will be deleted)...")
        time.sleep(2)
        run_cleanup(include_optional=include_billing, dry_run=True)
    
    elif command == 'execute':
        show_preview()
        print("\n⚠️  WARNING: THIS WILL PERMANENTLY DELETE DATA!")
        print("   • All galleries will be deleted")
        print("   • All photos will be deleted (DynamoDB + S3)")
        print("   • All analytics data will be deleted")
        print("   • Users can still login but will have NO galleries")
        
        if include_billing:
            print("   • Billing/subscription data will also be deleted")
        
        print("\n❓ Are you absolutely sure you want to continue?")
        confirm1 = input("   Type 'YES DELETE ALL GALLERIES' to confirm: ")
        
        if confirm1 != 'YES DELETE ALL GALLERIES':
            print("\n❌ Cancelled - No data was deleted")
            return
        
        print("\n❓ Final confirmation - This cannot be undone!")
        confirm2 = input("   Type 'CONFIRM DELETE' to proceed: ")
        
        if confirm2 != 'CONFIRM DELETE':
            print("\n❌ Cancelled - No data was deleted")
            return
        
        print("\n🔥 Starting deletion process...")
        time.sleep(2)
        run_cleanup(include_optional=include_billing, dry_run=False)
        
        print("\n✅ Cleanup complete!")
        print("   Users can still login, but all galleries have been removed.")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: preview, dry-run, execute")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

