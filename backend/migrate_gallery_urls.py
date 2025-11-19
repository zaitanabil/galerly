#!/usr/bin/env python3
"""
Migration Script: Update Gallery URLs from .app to .com
Fixes all existing galleries that have galerly.app URLs in their share_url field
"""

import boto3
import os
from decimal import Decimal
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

# Get table name - check multiple possible env var names
table_name = os.environ.get('DYNAMODB_GALLERIES_TABLE') or \
             os.environ.get('GALLERIES_TABLE') or \
             'galerly-galleries'

print(f"📊 Using DynamoDB table: {table_name}")
print(f"📍 Region: {os.environ.get('AWS_REGION', 'us-east-1')}\n")

galleries_table = dynamodb.Table(table_name)

def migrate_gallery_urls():
    """Migrate all gallery URLs from .app to .com and fix URL format"""
    
    print("🔄 Starting Gallery URL Migration")
    print("=" * 60)
    
    galleries_updated = 0
    galleries_scanned = 0
    galleries_already_correct = 0
    galleries_missing_url = 0
    format_fixed = 0
    
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
            share_url = gallery.get('share_url', '')
            share_token = gallery.get('share_token', '')
            
            needs_update = False
            new_share_url = share_url
            
            # Check if gallery has a share_url
            if not share_url:
                galleries_missing_url += 1
                
                # If there's a share_token but no share_url, create one with new format
                if share_token:
                    new_share_url = f"https://galerly.com/client-gallery?token={share_token}"
                    needs_update = True
            
            # Check if URL needs domain update (contains .app)
            elif 'galerly.app' in share_url:
                new_share_url = share_url.replace('galerly.app', 'galerly.com')
                needs_update = True
            
            # Check if URL needs format update (/view/ → /client-gallery?token=)
            if '/view/' in new_share_url and share_token:
                new_share_url = f"https://galerly.com/client-gallery?token={share_token}"
                needs_update = True
                format_fixed += 1
            
            # Update if needed
            if needs_update:
                try:
                    from datetime import datetime
                    galleries_table.update_item(
                        Key={
                            'user_id': user_id,
                            'id': gallery_id
                        },
                        UpdateExpression='SET share_url = :url, updated_at = :updated',
                        ExpressionAttributeValues={
                            ':url': new_share_url,
                            ':updated': datetime.utcnow().isoformat() + 'Z'
                        }
                    )
                    
                    galleries_updated += 1
                    print(f"✅ Updated: {gallery_name}")
                    print(f"   Old URL: {share_url or '(missing)'}")
                    print(f"   New URL: {new_share_url}\n")
                    
                except Exception as e:
                    print(f"❌ Failed to update {gallery_name}: {str(e)}\n")
            
            else:
                galleries_already_correct += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary:")
        print(f"   Galleries Scanned: {galleries_scanned}")
        print(f"   Galleries Updated: {galleries_updated}")
        print(f"   Already Correct: {galleries_already_correct}")
        print(f"   Missing URL (fixed): {galleries_missing_url}")
        print(f"   Format Fixed (/view/ → /client-gallery?token=): {format_fixed}")
        print("=" * 60)
        
        if galleries_updated > 0:
            print(f"\n✅ Successfully migrated {galleries_updated} galleries")
            print("   - Fixed domain (.app → .com)")
            print("   - Fixed URL format (/view/ → /client-gallery?token=)")
        else:
            print("\n✅ No galleries needed migration. All URLs are correct!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n🚀 GALERLY GALLERY URL MIGRATION\n")
    print("This script will update all gallery URLs from galerly.app to galerly.com\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = migrate_gallery_urls()
        exit(0 if success else 1)
    else:
        print("\n❌ Migration cancelled by user")
        exit(1)

