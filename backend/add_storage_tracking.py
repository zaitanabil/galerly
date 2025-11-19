#!/usr/bin/env python3
"""
Migration Script: Add size_mb to photos and recalculate gallery storage
Calculates photo sizes from file_size field and updates gallery storage_used
"""

import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize DynamoDB with credentials from .env
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Get table names
galleries_table_name = os.environ.get('DYNAMODB_GALLERIES_TABLE') or 'galerly-galleries'
photos_table_name = os.environ.get('DYNAMODB_PHOTOS_TABLE') or 'galerly-photos'

print(f"📊 Using DynamoDB tables:")
print(f"   Galleries: {galleries_table_name}")
print(f"   Photos: {photos_table_name}")
print(f"📍 Region: {os.environ.get('AWS_REGION', 'us-east-1')}\n")

galleries_table = dynamodb.Table(galleries_table_name)
photos_table = dynamodb.Table(photos_table_name)

def add_storage_tracking():
    """Add size_mb to photos and recalculate gallery storage"""
    
    print("🔄 Starting Storage Tracking Migration")
    print("=" * 60)
    
    photos_updated = 0
    photos_scanned = 0
    photos_already_have_size = 0
    galleries_updated = 0
    
    gallery_storage = {}  # {gallery_id: total_mb}
    
    try:
        # Step 1: Scan all photos and add size_mb
        print("📸 Step 1: Processing photos...")
        response = photos_table.scan()
        photos = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = photos_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            photos.extend(response.get('Items', []))
        
        print(f"   Found {len(photos)} photos to check\n")
        
        for photo in photos:
            photos_scanned += 1
            
            photo_id = photo.get('id')
            gallery_id = photo.get('gallery_id')
            file_size = photo.get('file_size', 0)
            
            # Skip if already has size_mb
            if 'size_mb' in photo:
                size_mb = float(photo.get('size_mb', 0))
                photos_already_have_size += 1
            else:
                # Calculate size_mb from file_size
                size_mb = file_size / (1024 * 1024) if file_size else 0
                size_mb = round(size_mb, 2)
                
                # Update photo
                try:
                    photos_table.update_item(
                        Key={'id': photo_id},
                        UpdateExpression='SET size_mb = :size',
                        ExpressionAttributeValues={
                            ':size': size_mb
                        }
                    )
                    photos_updated += 1
                    if photos_updated % 10 == 0:
                        print(f"   Updated {photos_updated} photos...")
                except Exception as e:
                    print(f"   ❌ Failed to update photo {photo_id}: {str(e)}")
                    continue
            
            # Accumulate storage per gallery
            if gallery_id:
                if gallery_id not in gallery_storage:
                    gallery_storage[gallery_id] = 0
                gallery_storage[gallery_id] += size_mb
        
        print(f"\n✅ Photos processed:")
        print(f"   Scanned: {photos_scanned}")
        print(f"   Updated: {photos_updated}")
        print(f"   Already had size_mb: {photos_already_have_size}\n")
        
        # Step 2: Update gallery storage_used
        print("📁 Step 2: Updating gallery storage...")
        for gallery_id, total_mb in gallery_storage.items():
            try:
                # Get gallery to get user_id (needed for key)
                response = galleries_table.scan(
                    FilterExpression='id = :gid',
                    ExpressionAttributeValues={':gid': gallery_id}
                )
                
                if response.get('Items'):
                    gallery = response['Items'][0]
                    user_id = gallery.get('user_id')
                    gallery_name = gallery.get('name', 'Unnamed')
                    
                    # Update storage
                    galleries_table.update_item(
                        Key={
                            'user_id': user_id,
                            'id': gallery_id
                        },
                        UpdateExpression='SET storage_used = :storage',
                        ExpressionAttributeValues={
                            ':storage': round(total_mb, 2)
                        }
                    )
                    
                    galleries_updated += 1
                    storage_display = f"{total_mb:.2f} MB" if total_mb < 1024 else f"{total_mb/1024:.2f} GB"
                    print(f"   ✅ {gallery_name}: {storage_display}")
                    
            except Exception as e:
                print(f"   ❌ Failed to update gallery {gallery_id}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary:")
        print(f"   Photos Scanned: {photos_scanned}")
        print(f"   Photos Updated: {photos_updated}")
        print(f"   Galleries Updated: {galleries_updated}")
        print(f"   Total Galleries: {len(gallery_storage)}")
        print("=" * 60)
        
        # Storage breakdown
        if gallery_storage:
            total_storage_mb = sum(gallery_storage.values())
            total_storage_gb = total_storage_mb / 1024
            print(f"\n📦 Total Storage Across All Galleries:")
            print(f"   {total_storage_mb:.2f} MB ({total_storage_gb:.2f} GB)")
        
        print(f"\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 GALERLY STORAGE TRACKING MIGRATION\n")
    print("This script will:")
    print("1. Add size_mb field to all photos (from file_size)")
    print("2. Calculate and update storage_used for all galleries\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = add_storage_tracking()
        exit(0 if success else 1)
    else:
        print("\n❌ Migration cancelled by user")
        exit(1)

