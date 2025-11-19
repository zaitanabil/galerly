#!/usr/bin/env python3
"""
Migration Script: Add share_token_created_at to existing galleries
Sets the creation date to 7 days ago so existing tokens remain valid initially
"""

import boto3
import os
from datetime import datetime, timedelta
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

def add_token_created_at():
    """Add share_token_created_at field to galleries that don't have it"""
    
    print("🔄 Starting Token Creation Date Migration")
    print("=" * 60)
    
    galleries_updated = 0
    galleries_scanned = 0
    galleries_already_have_field = 0
    galleries_no_token = 0
    
    try:
        # Scan all galleries
        response = galleries_table.scan()
        galleries = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = galleries_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            galleries.extend(response.get('Items', []))
        
        print(f"📊 Found {len(galleries)} galleries to check\n")
        
        # Use current time as default (tokens created now are valid for 7 days)
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        for gallery in galleries:
            galleries_scanned += 1
            
            gallery_id = gallery.get('id')
            gallery_name = gallery.get('name', 'Unnamed')
            user_id = gallery.get('user_id')
            share_token = gallery.get('share_token')
            token_created_at = gallery.get('share_token_created_at')
            
            # Skip if no share_token
            if not share_token:
                galleries_no_token += 1
                continue
            
            # Skip if already has share_token_created_at
            if token_created_at:
                galleries_already_have_field += 1
                continue
            
            # Add share_token_created_at field
            try:
                galleries_table.update_item(
                    Key={
                        'user_id': user_id,
                        'id': gallery_id
                    },
                    UpdateExpression='SET share_token_created_at = :created, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':created': current_time,
                        ':updated': current_time
                    }
                )
                
                galleries_updated += 1
                print(f"✅ Updated: {gallery_name}")
                print(f"   Gallery ID: {gallery_id}")
                print(f"   Token Created: {current_time}\n")
                
            except Exception as e:
                print(f"❌ Failed to update {gallery_name}: {str(e)}\n")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary:")
        print(f"   Galleries Scanned: {galleries_scanned}")
        print(f"   Galleries Updated: {galleries_updated}")
        print(f"   Already Have Field: {galleries_already_have_field}")
        print(f"   No Share Token: {galleries_no_token}")
        print("=" * 60)
        
        if galleries_updated > 0:
            print(f"\n✅ Successfully added share_token_created_at to {galleries_updated} galleries")
            print(f"   All updated galleries now have valid tokens for 7 days")
        else:
            print("\n✅ All galleries already have share_token_created_at field!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n🚀 GALERLY TOKEN EXPIRATION MIGRATION\n")
    print("This script will add share_token_created_at field to existing galleries")
    print("Tokens will be marked as created NOW, valid for 7 days\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = add_token_created_at()
        exit(0 if success else 1)
    else:
        print("\n❌ Migration cancelled by user")
        exit(1)

