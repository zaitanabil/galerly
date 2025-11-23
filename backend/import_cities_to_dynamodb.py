"""
Import cities from worldcities.csv to DynamoDB
Processes ~48,000 cities with prefix indexing for fast autocomplete
"""

import csv
import boto3
import os
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration
IS_LOCAL = os.getenv('AWS_ENDPOINT_URL', '').startswith('http://localhost')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')  # Read endpoint URL
CSV_PATH = '/Users/nz-dev/Desktop/business/galerly.com/worldcities.csv'

# DynamoDB client
if IS_LOCAL:
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=AWS_ENDPOINT_URL,  # Use environment variable
        region_name=AWS_REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

TABLE_NAME = 'galerly-cities-local' if IS_LOCAL else 'galerly-cities'


def generate_prefixes(city_ascii):
    """
    Generate prefix strings for indexing
    Returns: (prefix1, prefix2, prefix3)
    """
    city_lower = city_ascii.lower().strip()
    
    # Generate prefixes (1, 2, 3 characters)
    prefix1 = city_lower[0] if len(city_lower) >= 1 else ''
    prefix2 = city_lower[:2] if len(city_lower) >= 2 else city_lower
    prefix3 = city_lower[:3] if len(city_lower) >= 3 else city_lower
    
    return prefix1, prefix2, prefix3


def import_cities():
    """Import cities from CSV with batch writing for efficiency"""
    table = dynamodb.Table(TABLE_NAME)
    
    print(f"📂 Reading cities from: {CSV_PATH}")
    print(f"📊 Target table: {TABLE_NAME}")
    print(f"📍 Environment: {'LocalStack' if IS_LOCAL else 'AWS'}\n")
    
    batch_size = 25  # DynamoDB batch_writer limit
    total_imported = 0
    total_skipped = 0
    
    try:
        with table.batch_writer() as batch:
            with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Extract and clean data
                        city_id = row['id']
                        city = row['city'].strip()
                        city_ascii = row['city_ascii'].strip()
                        country = row['country'].strip()
                        iso2 = row['iso2'].strip()
                        iso3 = row['iso3'].strip()
                        admin_name = row['admin_name'].strip() if row['admin_name'] else ''
                        
                        # Parse coordinates and population
                        try:
                            lat = Decimal(str(row['lat']))
                            lng = Decimal(str(row['lng']))
                            population = int(row['population']) if row['population'] else 0
                        except (ValueError, TypeError):
                            # Skip cities with invalid data
                            total_skipped += 1
                            continue
                        
                        # Generate prefixes for search
                        prefix1, prefix2, prefix3 = generate_prefixes(city_ascii)
                        
                        # Prepare item
                        item = {
                            'city_id': city_id,
                            'city': city,
                            'city_ascii': city_ascii,
                            'city_lower': city_ascii.lower(),  # For exact matching
                            'country': country,
                            'iso2': iso2,
                            'iso3': iso3,
                            'admin_name': admin_name,
                            'lat': lat,
                            'lng': lng,
                            'population': population,
                            'prefix1': prefix1,
                            'prefix2': prefix2,
                            'prefix3': prefix3,
                            'display_name': f"{city}, {admin_name}, {country}" if admin_name else f"{city}, {country}"
                        }
                        
                        # Write to DynamoDB
                        batch.put_item(Item=item)
                        total_imported += 1
                        
                        # Progress indicator
                        if total_imported % 1000 == 0:
                            print(f"✅ Imported {total_imported} cities...")
                            
                    except Exception as e:
                        print(f"⚠️  Error importing {row.get('city', 'unknown')}: {e}")
                        total_skipped += 1
                        continue
        
        print(f"\n✅ Import complete!")
        print(f"📊 Total imported: {total_imported}")
        print(f"⚠️  Total skipped: {total_skipped}")
        
        # Print some example cities
        print(f"\n📍 Example cities imported:")
        response = table.scan(Limit=5)
        for item in response.get('Items', []):
            print(f"   • {item['display_name']} (pop: {item['population']:,})")
        
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        print(f"💡 Make sure worldcities.csv is in the correct location")
    except ClientError as e:
        print(f"❌ DynamoDB error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise


def verify_indexes():
    """Verify that prefix indexes are working"""
    table = dynamodb.Table(TABLE_NAME)
    
    print(f"\n🔍 Verifying prefix indexes...")
    
    # Test prefix1 index (cities starting with 'n')
    response = table.query(
        IndexName='prefix1-population-index',
        KeyConditionExpression='prefix1 = :prefix',
        ExpressionAttributeValues={':prefix': 'n'},
        ScanIndexForward=False,  # Sort by population DESC
        Limit=5
    )
    
    print(f"\n✅ Top 5 cities starting with 'N':")
    for item in response.get('Items', []):
        print(f"   • {item['display_name']} (pop: {item['population']:,})")
    
    # Test prefix2 index (cities starting with 'ne')
    response = table.query(
        IndexName='prefix2-population-index',
        KeyConditionExpression='prefix2 = :prefix',
        ExpressionAttributeValues={':prefix': 'ne'},
        ScanIndexForward=False,
        Limit=5
    )
    
    print(f"\n✅ Top 5 cities starting with 'NE':")
    for item in response.get('Items', []):
        print(f"   • {item['display_name']} (pop: {item['population']:,})")


if __name__ == '__main__':
    print("🌍 Galerly Cities Import")
    print("=" * 50)
    
    import_cities()
    verify_indexes()
    
    print("\n" + "=" * 50)
    print("✅ Cities import and verification complete!")
    print("📝 Next step: Test the city search API endpoint")
