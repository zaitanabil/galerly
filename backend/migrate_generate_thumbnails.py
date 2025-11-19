#!/usr/bin/env python3
"""
Migration Script: Generate Thumbnails for Existing Photos

This script:
1. Scans all photos in the database
2. For photos without thumbnails (thumbnail_url == url), generates thumbnails
3. Uploads thumbnails to S3 with _thumb suffix
4. Updates database with new thumbnail_url

Run this ONCE to migrate existing photos. New uploads automatically get thumbnails.
"""

import boto3
import os
import sys
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.image_security import generate_thumbnail, ImageSecurityError

# Initialize AWS clients
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Get configuration
S3_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
photos_table_name = os.environ.get('DYNAMODB_PHOTOS_TABLE', 'galerly-photos')
photos_table = dynamodb.Table(photos_table_name)

print("=" * 80)
print("🖼️  THUMBNAIL GENERATION MIGRATION")
print("=" * 80)
print(f"S3 Bucket: {S3_BUCKET}")
print(f"DynamoDB Table: {photos_table_name}")
print(f"Region: {AWS_REGION}")
print("")


def scan_all_photos():
    """Scan all photos from DynamoDB"""
    print("📊 Scanning all photos from database...")
    photos = []
    
    try:
        response = photos_table.scan()
        photos.extend(response.get('Items', []))
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = photos_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            photos.extend(response.get('Items', []))
        
        print(f"   ✅ Found {len(photos)} photos in database")
        return photos
    except Exception as e:
        print(f"   ❌ Error scanning photos: {e}")
        return []


def needs_thumbnail(photo):
    """Check if photo needs thumbnail generation"""
    url = photo.get('url', '')
    thumbnail_url = photo.get('thumbnail_url', '')
    
    # If thumbnail_url is same as url, or thumbnail doesn't have _thumb suffix, needs migration
    if thumbnail_url == url or '_thumb' not in thumbnail_url:
        return True
    
    # Check if thumbnail exists in S3
    s3_key = thumbnail_url.replace(f"https://{S3_BUCKET}.s3.amazonaws.com/", "")
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return False  # Thumbnail exists
    except:
        return True  # Thumbnail doesn't exist


def generate_and_upload_thumbnail(photo):
    """Generate thumbnail for a photo and upload to S3"""
    photo_id = photo.get('id')
    url = photo.get('url', '')
    s3_key = photo.get('s3_key', '')
    filename = photo.get('filename', 'photo.jpg')
    
    print(f"📸 {filename[:40]} (ID: {photo_id[:8]}...)", end=" ")
    
    try:
        # 1. Download original image from S3
        s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        image_data = s3_object['Body'].read()
        image_size_mb = len(image_data) / (1024 * 1024)
        
        # 2. Generate thumbnail
        # IMPORTANT: Files in S3 are already sanitized JPEGs (even if original was RAW/DNG)
        # So we always treat them as JPEG to avoid RAW processing errors
        thumbnail_data = generate_thumbnail(
            image_data,
            max_width=800,
            max_height=600,
            quality=85,
            filename='photo.jpg'  # Always treat as JPEG (files already converted in S3)
        )
        thumbnail_size_kb = len(thumbnail_data) / 1024
        
        # 3. Upload thumbnail to S3
        s3_key_thumb = s3_key.replace('.jpg', '_thumb.jpg')
        if not s3_key_thumb.endswith('_thumb.jpg'):
            # Handle other extensions
            base, ext = os.path.splitext(s3_key)
            s3_key_thumb = f"{base}_thumb.jpg"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key_thumb,
            Body=thumbnail_data,
            ContentType='image/jpeg'
        )
        
        # 4. Update database
        thumbnail_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key_thumb}"
        photos_table.update_item(
            Key={'id': photo_id},
            UpdateExpression='SET thumbnail_url = :thumb',
            ExpressionAttributeValues={
                ':thumb': thumbnail_url
            }
        )
        
        print(f"✅ {thumbnail_size_kb:.0f}KB ({image_size_mb:.1f}MB → {thumbnail_size_kb/1024:.2f}MB)")
        return True
        
    except ImageSecurityError as e:
        print(f"❌ Security error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:60]}")
        return False


def migrate_thumbnails(dry_run=False, limit=None):
    """
    Main migration function
    
    Args:
        dry_run: If True, only scan and report what would be done
        limit: Maximum number of photos to process (None = all)
    """
    print(f"🚀 Starting migration (dry_run={dry_run}, limit={limit or 'all'})")
    print("")
    
    # Scan all photos
    photos = scan_all_photos()
    
    if not photos:
        print("❌ No photos found in database")
        return
    
    # Filter photos that need thumbnails
    photos_needing_thumbnails = []
    print("\n🔍 Checking which photos need thumbnails...")
    for photo in photos:
        if needs_thumbnail(photo):
            photos_needing_thumbnails.append(photo)
    
    total_photos = len(photos)
    need_migration = len(photos_needing_thumbnails)
    already_have = total_photos - need_migration
    
    print("")
    print("=" * 80)
    print("📊 MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Total photos in database: {total_photos}")
    print(f"Photos already have thumbnails: {already_have} ✅")
    print(f"Photos need thumbnails: {need_migration} 🔄")
    print("")
    
    if need_migration == 0:
        print("🎉 All photos already have thumbnails! Nothing to migrate.")
        return
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print(f"\nPhotos that would be migrated ({min(limit or need_migration, need_migration)}):")
        for i, photo in enumerate(photos_needing_thumbnails[:limit or need_migration]):
            print(f"   {i+1}. {photo.get('filename', 'unknown')} (ID: {photo.get('id', 'unknown')[:8]}...)")
        print(f"\nTo perform actual migration, run: python migrate_generate_thumbnails.py --migrate")
        return
    
    # Perform migration
    print(f"🔄 Migrating {min(limit or need_migration, need_migration)} photos...")
    print(f"⚡ Using parallel processing (10 workers) for faster migration")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    
    photos_to_process = photos_needing_thumbnails[:limit] if limit else photos_needing_thumbnails
    
    # Use ThreadPoolExecutor for parallel processing
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_photo = {
            executor.submit(generate_and_upload_thumbnail, photo): (i+1, photo) 
            for i, photo in enumerate(photos_to_process)
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_photo):
            idx, photo = future_to_photo[future]
            print(f"[{idx}/{len(photos_to_process)}] ", end="")
            
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"❌ Exception: {str(e)[:60]}")
                fail_count += 1
    
    # Final summary
    print("")
    print("=" * 80)
    print("🎉 MIGRATION COMPLETE")
    print("=" * 80)
    print(f"✅ Successfully migrated: {success_count} photos")
    print(f"❌ Failed: {fail_count} photos")
    print(f"📊 Total processed: {success_count + fail_count}")
    print("")
    
    if fail_count > 0:
        print("⚠️  Some photos failed. Check the logs above for details.")
        print("   You can re-run this script to retry failed photos.")
    else:
        print("🎉 All photos successfully migrated!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate thumbnails for existing photos')
    parser.add_argument('--migrate', action='store_true', help='Perform actual migration (default is dry-run)')
    parser.add_argument('--limit', type=int, help='Limit number of photos to process (for testing)')
    
    args = parser.parse_args()
    
    # Run migration
    migrate_thumbnails(dry_run=not args.migrate, limit=args.limit)

