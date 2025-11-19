#!/usr/bin/env python3
"""
Fix Storage and Photo Count
Recalculates accurate storage and photo counts for all galleries
"""

import boto3
import os
from decimal import Decimal
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key

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

def fix_gallery_stats():
    """Recalculate accurate storage and photo counts"""
    
    print("🔄 Starting Gallery Stats Fix")
    print("=" * 60)
    
    try:
        # Get all galleries
        galleries_response = galleries_table.scan()
        galleries = galleries_response.get('Items', [])
        
        print(f"📁 Found {len(galleries)} galleries to fix\n")
        
        for gallery in galleries:
            gallery_id = gallery.get('id')
            gallery_name = gallery.get('name', 'Unnamed')
            user_id = gallery.get('user_id')
            
            print(f"\n🔍 Processing: {gallery_name} (ID: {gallery_id[:12]}...)")
            
            # Query photos for this gallery using GalleryIdIndex
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery_id)
            )
            photos = photos_response.get('Items', [])
            
            # Calculate accurate stats
            actual_photo_count = len(photos)
            actual_storage_mb = sum(float(photo.get('size_mb', 0)) for photo in photos)
            
            # Get current (incorrect) values
            current_photo_count = gallery.get('photo_count', 0)
            current_storage_mb = float(gallery.get('storage_used', 0))
            
            print(f"   Current in DB: {current_photo_count} photos, {current_storage_mb} MB")
            print(f"   Actual count:  {actual_photo_count} photos, {round(actual_storage_mb, 2)} MB")
            
            # Update if different
            if actual_photo_count != current_photo_count or abs(actual_storage_mb - current_storage_mb) > 0.01:
                galleries_table.update_item(
                    Key={
                        'user_id': user_id,
                        'id': gallery_id
                    },
                    UpdateExpression='SET photo_count = :count, storage_used = :storage',
                    ExpressionAttributeValues={
                        ':count': actual_photo_count,
                        ':storage': Decimal(str(round(actual_storage_mb, 2)))  # Convert to Decimal
                    }
                )
                print(f"   ✅ Updated to: {actual_photo_count} photos, {round(actual_storage_mb, 2)} MB")
            else:
                print(f"   ✓ Already accurate")
        
        print("\n" + "=" * 60)
        print("✅ Gallery stats fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 GALERLY STORAGE FIX\n")
    print("This script will:")
    print("1. Count actual photos per gallery")
    print("2. Calculate actual storage per gallery")
    print("3. Update gallery records with accurate data\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = fix_gallery_stats()
        exit(0 if success else 1)
    else:
        print("\n❌ Fix cancelled by user")
        exit(1)

