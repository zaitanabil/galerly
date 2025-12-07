"""
DynamoDB Cities Table Setup
Creates galerly-cities table with prefix indexing for fast autocomplete
"""

import boto3
import os
from botocore.exceptions import ClientError

# Configuration
IS_LOCAL = os.getenv('AWS_ENDPOINT_URL', '').startswith('http://localhost')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# DynamoDB client
if IS_LOCAL:
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:4566',
        region_name=AWS_REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
else:
    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

TABLE_NAME = 'galerly-cities-local' if IS_LOCAL else 'galerly-cities'


def create_cities_table():
    """
    Create cities table with GSIs for prefix-based searching
    
    Schema:
    - PK: city_id (unique ID from CSV)
    - city: Full city name
    - city_ascii: ASCII version for searching
    - country: Country name
    - iso2: 2-letter country code
    - iso3: 3-letter country code
    - admin_name: State/province
    - population: Population (number)
    - lat, lng: Coordinates
    
    GSIs for fast prefix search:
    - prefix1-index: First 1 letter (26 partitions)
    - prefix2-index: First 2 letters (~676 partitions)
    - prefix3-index: First 3 letters (~17k partitions)
    """
    
    try:
        response = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'city_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_id', 'AttributeType': 'S'},
                {'AttributeName': 'prefix1', 'AttributeType': 'S'},
                {'AttributeName': 'prefix2', 'AttributeType': 'S'},
                {'AttributeName': 'prefix3', 'AttributeType': 'S'},
                {'AttributeName': 'population', 'AttributeType': 'N'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'prefix1-population-index',
                    'KeySchema': [
                        {'AttributeName': 'prefix1', 'KeyType': 'HASH'},
                        {'AttributeName': 'population', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'prefix2-population-index',
                    'KeySchema': [
                        {'AttributeName': 'prefix2', 'KeyType': 'HASH'},
                        {'AttributeName': 'population', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'prefix3-population-index',
                    'KeySchema': [
                        {'AttributeName': 'prefix3', 'KeyType': 'HASH'},
                        {'AttributeName': 'population', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        print(f"✅ Created table: {TABLE_NAME}")
        print(f"📊 Table ARN: {response['TableDescription']['TableArn']}")
        print(f"🔍 GSIs: prefix1-population-index, prefix2-population-index, prefix3-population-index")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {TABLE_NAME} already exists")
            return False
        else:
            print(f"❌ Error creating table: {e}")
            raise


def wait_for_table():
    """Wait for table to become active"""
    print(f"⏳ Waiting for table {TABLE_NAME} to become active...")
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=TABLE_NAME)
    print(f"✅ Table {TABLE_NAME} is active")


if __name__ == '__main__':
    print(f"🚀 Creating cities table: {TABLE_NAME}")
    print(f"📍 Environment: {'LocalStack' if IS_LOCAL else 'AWS'}")
    
    created = create_cities_table()
    
    if created:
        wait_for_table()
        print("\n✅ Cities table setup complete!")
        print("\n📝 Next step: Run import_cities_to_dynamodb.py to populate the table")
    else:
        print("\n✅ Table already exists. Ready to import cities.")

