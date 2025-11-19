#!/usr/bin/env python3
"""
Migrate Photos from Frontend Bucket to Photos Bucket
Moves all photos from galerly-frontend-app to galerly-images-storage
and updates database URLs
"""
import boto3
import os
from decimal import Decimal

# AWS Setup
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# Buckets
SOURCE_BUCKET = os.environ.get('S3_BUCKET', 'galerly-frontend-app')
TARGET_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')

# Tables
photos_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PHOTOS', 'galerly-photos'))

print("=" * 80)
print("📸 PHOTO MIGRATION SCRIPT")
print("=" * 80)
print(f"Source Bucket: {SOURCE_BUCKET}")
print(f"Target Bucket: {TARGET_BUCKET}")
print("")

def list_photo_objects():
    """List all photo objects in source bucket"""
    print("🔍 Scanning source bucket for photos...")
    
    photo_objects = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    # List all objects in source bucket
    for page in paginator.paginate(Bucket=SOURCE_BUCKET):
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            # Check if it's a photo (has gallery_id/photo_id.ext structure)
            if '/' in key and any(key.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.gif']):
                photo_objects.append({
                    'Key': key,
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified']
                })
    
    print(f"   Found {len(photo_objects)} photo objects")
    return photo_objects

def copy_photo_to_target(source_key):
    """Copy photo from source to target bucket"""
    try:
        # Copy object
        copy_source = {
            'Bucket': SOURCE_BUCKET,
            'Key': source_key
        }
        
        s3_client.copy_object(
            CopySource=copy_source,
            Bucket=TARGET_BUCKET,
            Key=source_key,
            MetadataDirective='COPY'
        )
        
        return True
    except Exception as e:
        print(f"   ❌ Error copying {source_key}: {e}")
        return False

def update_photo_urls():
    """Update all photo URLs in database"""
    print("\n🔄 Updating photo URLs in database...")
    
    updated_count = 0
    skipped_count = 0
    
    # Scan all photos
    response = photos_table.scan()
    photos = response.get('Items', [])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = photos_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        photos.extend(response.get('Items', []))
    
    print(f"   Found {len(photos)} photo records in database")
    
    for photo in photos:
        url = photo.get('url', '')
        thumbnail_url = photo.get('thumbnail_url', '')
        
        # Check if URL needs updating
        if SOURCE_BUCKET in url:
            # Update URLs
            new_url = url.replace(SOURCE_BUCKET, TARGET_BUCKET)
            new_thumbnail = thumbnail_url.replace(SOURCE_BUCKET, TARGET_BUCKET)
            
            # Update database
            try:
                photos_table.update_item(
                    Key={'id': photo['id']},
                    UpdateExpression='SET #url = :url, thumbnail_url = :thumb',
                    ExpressionAttributeNames={'#url': 'url'},
                    ExpressionAttributeValues={
                        ':url': new_url,
                        ':thumb': new_thumbnail
                    }
                )
                updated_count += 1
                print(f"   ✅ Updated photo {photo['id'][:8]}...")
            except Exception as e:
                print(f"   ❌ Failed to update {photo['id']}: {e}")
        else:
            skipped_count += 1
    
    print(f"\n   Updated: {updated_count} photos")
    print(f"   Skipped: {skipped_count} photos (already correct)")
    return updated_count

def verify_migration():
    """Verify photos exist in target bucket"""
    print("\n🧪 Verifying migration...")
    
    # Get sample of photos from database
    response = photos_table.scan(Limit=10)
    photos = response.get('Items', [])
    
    verified = 0
    failed = 0
    
    for photo in photos:
        s3_key = photo.get('s3_key', '')
        if not s3_key:
            continue
            
        try:
            s3_client.head_object(Bucket=TARGET_BUCKET, Key=s3_key)
            verified += 1
            print(f"   ✅ Verified: {s3_key[:30]}...")
        except:
            failed += 1
            print(f"   ❌ Not found: {s3_key[:30]}...")
    
    print(f"\n   Verified: {verified}/{verified + failed} photos exist in target bucket")
    return failed == 0

def main():
    """Main migration flow"""
    print("\n⚠️  MIGRATION STEPS:")
    print("1. Copy photos from source bucket to target bucket")
    print("2. Update database URLs to point to target bucket")
    print("3. Verify migration")
    print("4. (Manual) Delete old photos from source bucket")
    print("")
    
    # Step 1: List photos
    photo_objects = list_photo_objects()
    
    if not photo_objects:
        print("\n✅ No photos found in source bucket. Migration not needed!")
        return
    
    # Confirm before proceeding
    print(f"\n⚠️  This will copy {len(photo_objects)} photos to {TARGET_BUCKET}")
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    # Step 2: Copy photos
    print("\n📤 Copying photos to target bucket...")
    copied = 0
    failed = 0
    
    for i, obj in enumerate(photo_objects, 1):
        key = obj['Key']
        print(f"   [{i}/{len(photo_objects)}] Copying {key}...")
        
        if copy_photo_to_target(key):
            copied += 1
        else:
            failed += 1
    
    print(f"\n   ✅ Copied: {copied} photos")
    print(f"   ❌ Failed: {failed} photos")
    
    # Step 3: Update database
    updated = update_photo_urls()
    
    # Step 4: Verify
    verification_passed = verify_migration()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Photos Copied:     {copied}")
    print(f"Photos Failed:     {failed}")
    print(f"URLs Updated:      {updated}")
    print(f"Verification:      {'✅ PASSED' if verification_passed else '❌ FAILED'}")
    print("")
    
    if verification_passed:
        print("✅ MIGRATION COMPLETE!")
        print("\n⚠️  NEXT STEP: Manually delete old photos from source bucket:")
        print(f"aws s3 rm s3://{SOURCE_BUCKET}/ --recursive --exclude '*' --include '*/*/*.jpg' --include '*/*/*.jpeg' --include '*/*/*.png'")
    else:
        print("⚠️  MIGRATION INCOMPLETE - Please verify manually")
    
    print("=" * 80)

if __name__ == '__main__':
    main()

