"""
Setup DynamoDB table for Custom Domain configurations
"""
import boto3
import os
from dotenv import load_dotenv

# Load environment variables from root-level .env files
env = os.environ.get('ENVIRONMENT', 'development')
if env == 'production':
    load_dotenv('../../.env.production')
else:
    load_dotenv('../../.env.development')
load_dotenv()

# DynamoDB setup
endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
dynamodb_config = {
    'service_name': 'dynamodb',
    'region_name': os.environ.get('AWS_REGION', 'eu-central-1')
}

if endpoint_url:
    dynamodb_config['endpoint_url'] = endpoint_url
    dynamodb_config['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
    dynamodb_config['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')

dynamodb = boto3.resource(**dynamodb_config)
dynamodb_client = boto3.client(**dynamodb_config)

def setup_custom_domains_table():
    """
    Create custom domains table if it doesn't exist
    
    Table Schema:
        - user_id (HASH) - User ID
        - domain (RANGE) - Custom domain name
        - certificate_arn - ACM certificate ARN
        - distribution_id - CloudFront distribution ID
        - distribution_domain - CloudFront domain name (e.g., d123abc.cloudfront.net)
        - status - pending_validation, active, error
        - validation_records - DNS records needed for SSL validation
        - created_at - Timestamp
        - updated_at - Timestamp
    """
    table_name = os.environ.get('DYNAMODB_TABLE_CUSTOM_DOMAINS', 'galerly-custom-domains-local')
    
    try:
        # Check if table exists
        existing_tables = dynamodb_client.list_tables()['TableNames']
        
        if table_name in existing_tables:
            print(f"✓ Table {table_name} already exists")
            return
        
        # Create table
        print(f"Creating table: {table_name}")
        
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'domain',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'domain',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        print(f"Waiting for table {table_name} to be active...")
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        
        print(f"✓ Table {table_name} created successfully")
        
    except Exception as e:
        print(f"Error creating custom domains table: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Setting up Custom Domains table...")
    setup_custom_domains_table()
    print("✓ Setup complete!")

