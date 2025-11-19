#!/usr/bin/env python3
"""
Migration Script: Remove duplicate allow_download field
Standardizes to use only allow_downloads (plural) across all galleries
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

# Get table name
table_name = os.environ.get('DYNAMODB_GALLERIES_TABLE') or \
             os.environ.get('GALLERIES_TABLE') or \
             'galerly-galleries'

print(f"📊 Using DynamoDB table: {table_name}")
print(f"📍 Region: {os.environ.get('AWS_REGION', 'us-east-1')}\n")

galleries_table = dynamodb.Table(table_name)

def remove_allow_download_field():
    """Remove duplicate allow_download field and keep only allow_downloads"""
    
    print("🔄 Starting Field Cleanup Migration")
    print("=" * 60)
    
    galleries_updated = 0
    galleries_scanned = 0
    galleries_already_clean = 0
    galleries_no_field = 0
    
    try:
        # Scan all galleries
        response = galleries_table.scan()
        galleries = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = galleries_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            galleries.extend(response.get('Items', []))
        
        print(f"📊 Found {len(galleries)} galleries to check\n")
        
        for gallery in galleries:
            galleries_scanned += 1
            
            gallery_id = gallery.get('id')
            gallery_name = gallery.get('name', 'Unnamed')
            user_id = gallery.get('user_id')
            
            # Check if gallery has the duplicate field
            has_allow_download = 'allow_download' in gallery
            has_allow_downloads = 'allow_downloads' in gallery
            
            if not has_allow_download and not has_allow_downloads:
                galleries_no_field += 1
                continue
            
            if not has_allow_download:
                galleries_already_clean += 1
                continue
            
            # Need to migrate
            try:
                # Get the value from either field (prefer allow_downloads)
                downloads_value = gallery.get('allow_downloads', gallery.get('allow_download', True))
                
                # Update gallery: set allow_downloads and remove allow_download
                galleries_table.update_item(
                    Key={
                        'user_id': user_id,
                        'id': gallery_id
                    },
                    UpdateExpression='SET allow_downloads = :val REMOVE allow_download',
                    ExpressionAttributeValues={
                        ':val': downloads_value
                    }
                )
                
                galleries_updated += 1
                print(f"✅ Cleaned: {gallery_name}")
                print(f"   Gallery ID: {gallery_id}")
                print(f"   Set allow_downloads = {downloads_value}")
                print(f"   Removed allow_download field\n")
                
            except Exception as e:
                print(f"❌ Failed to update {gallery_name}: {str(e)}\n")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary:")
        print(f"   Galleries Scanned: {galleries_scanned}")
        print(f"   Galleries Updated: {galleries_updated}")
        print(f"   Already Clean: {galleries_already_clean}")
        print(f"   No Permission Field: {galleries_no_field}")
        print("=" * 60)
        
        if galleries_updated > 0:
            print(f"\n✅ Successfully removed allow_download field from {galleries_updated} galleries")
            print(f"   All galleries now use allow_downloads (plural) only")
        else:
            print("\n✅ All galleries already clean!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n🚀 GALERLY FIELD CLEANUP MIGRATION\n")
    print("This script will remove duplicate allow_download field")
    print("and standardize to use only allow_downloads (plural)\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = remove_allow_download_field()
        exit(0 if success else 1)
    else:
        print("\n❌ Migration cancelled by user")
        exit(1)

