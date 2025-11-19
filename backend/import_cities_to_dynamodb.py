#!/usr/bin/env python3
"""
Import /Users/nz-dev/Desktop/business/galerly.com/worldcities.csv to DynamoDB
with optimized indexes for fast city search
"""
import csv
import boto3
from decimal import Decimal
import time

# Initialize DynamoDB
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_optimized_table():
    """Create DynamoDB table with GSI for fast city prefix search"""
    print("🗄️  Creating optimized galerly-cities table with search indexes...")
    
    try:
        # Delete existing table if it exists
        try:
            dynamodb_client.describe_table(TableName='galerly-cities')
            print("⚠️  Existing table found, deleting...")
            dynamodb_client.delete_table(TableName='galerly-cities')
            
            # Wait for deletion
            waiter = dynamodb_client.get_waiter('table_not_exists')
            waiter.wait(TableName='galerly-cities')
            print("✅ Old table deleted")
        except dynamodb_client.exceptions.ResourceNotFoundException:
            print("✓ No existing table found")
        
        # Create new table with GSI for city search
        response = dynamodb_client.create_table(
            TableName='galerly-cities',
            KeySchema=[
                {'AttributeName': 'city_ascii', 'KeyType': 'HASH'},
                {'AttributeName': 'country', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_ascii', 'AttributeType': 'S'},
                {'AttributeName': 'country', 'AttributeType': 'S'},
                {'AttributeName': 'search_key', 'AttributeType': 'S'},  # For prefix search
                {'AttributeName': 'population', 'AttributeType': 'N'}   # For sorting
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'search_key-index',
                    'KeySchema': [
                        {'AttributeName': 'search_key', 'KeyType': 'HASH'},
                        {'AttributeName': 'population', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print("✅ Table created with optimized search index!")
        print("⏳ Waiting for table to become active...")
        
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName='galerly-cities')
        
        print("✅ Table is now active!")
        return True
        
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print("✅ Table already exists with correct structure")
            return True
        else:
            print(f"❌ Error creating table: {e}")
            raise

def import_cities():
    """Import cities from CSV to DynamoDB with search optimization"""
    print("\n📊 Starting import of /Users/nz-dev/Desktop/business/galerly.com/worldcities.csv to DynamoDB...")
    
    table = dynamodb.Table('galerly-cities')
    batch_size = 25  # DynamoDB batch limit
    batch = []
    total_imported = 0
    seen_keys = set()  # Track seen city+country combinations
    
    with open('/Users/nz-dev/Desktop/business/galerly.com/worldcities.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Create unique key
            key = (row['city_ascii'], row['country'])
            
            # Skip duplicates (keep only first occurrence)
            if key in seen_keys:
                continue
            
            # Skip empty city names
            if not row['city_ascii'] or not row['country']:
                continue
            
            seen_keys.add(key)
            
            # Create search key for prefix matching (first 3 chars, lowercase)
            # This allows fast queries like "Par" -> Paris, "Lon" -> London
            city_lower = row['city_ascii'].lower()
            search_prefix = city_lower[:3] if len(city_lower) >= 3 else city_lower
            
            # Prepare item for DynamoDB with search optimization
            item = {
                'city_ascii': row['city_ascii'],
                'country': row['country'],
                'city': row['city'],
                'lat': Decimal(str(row['lat'])),
                'lng': Decimal(str(row['lng'])),
                'population': int(float(row.get('population', 0) or 0)),
                'search_key': search_prefix,  # For fast prefix search
                'city_lower': city_lower  # For case-insensitive search
            }
            
            batch.append({
                'PutRequest': {
                    'Item': item
                }
            })
            
            # Write batch when it reaches 25 items
            if len(batch) >= batch_size:
                table.meta.client.batch_write_item(
                    RequestItems={
                        'galerly-cities': batch
                    }
                )
                total_imported += len(batch)
                print(f"✓ Imported {total_imported} cities...")
                batch = []
        
        # Write remaining items
        if batch:
            table.meta.client.batch_write_item(
                RequestItems={
                    'galerly-cities': batch
                }
            )
            total_imported += len(batch)
    
    print(f"\n✅ Successfully imported {total_imported} cities to DynamoDB!")
    print(f"📊 Search optimization: Cities indexed by 3-char prefix for instant suggestions")

if __name__ == '__main__':
    # Step 1: Create optimized table structure
    create_optimized_table()
    
    # Step 2: Import cities data
    import_cities()
    
    print("\n" + "="*70)
    print("🎉 IMPORT COMPLETE!")
    print("="*70)
    print("\n✅ Fast city search is now enabled!")
    print("   - Cities indexed by first 3 characters")
    print("   - Results sorted by population (largest cities first)")
    print("   - Case-insensitive search support")
    print("\n💡 Search examples:")
    print("   - 'Par' → Paris, Parma, Parnu...")
    print("   - 'Lon' → London, Long Beach...")
    print("   - 'Fri' → Fribourg, Friedrichshafen...")
    print()


