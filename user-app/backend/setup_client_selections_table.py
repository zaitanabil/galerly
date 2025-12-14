"""
Setup Client Selections Table for DynamoDB
Creates the table required for the client selection workflow feature
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError

# Environment detection
LOCALSTACK_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-central-1')

# Check if running in LocalStack or AWS
IS_LOCALSTACK = os.environ.get('USE_LOCALSTACK', 'false').lower() == 'true'

# DynamoDB client
if IS_LOCALSTACK:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        endpoint_url=LOCALSTACK_ENDPOINT
    )
    print(f"Using LocalStack at {LOCALSTACK_ENDPOINT}")
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    print(f"Using AWS DynamoDB in region {AWS_REGION}")

# Table configuration
TABLE_NAME = os.environ.get('DYNAMODB_CLIENT_SELECTIONS_TABLE', 'client_selections')


def create_client_selections_table():
    """
    Create the client_selections table with proper schema and indexes
    
    Table Schema:
    - Partition Key: id (session ID)
    - GSI: PhotographerSelectionSessionsIndex on photographer_id
    
    Attributes:
    - id: Session ID (UUID)
    - gallery_id: Gallery ID
    - photographer_id: Photographer user ID
    - client_email: Client email address
    - client_name: Client name (optional)
    - max_selections: Maximum number of photos client can select (optional)
    - deadline: Selection deadline (ISO date, optional)
    - status: Session status (active, submitted, cancelled)
    - selections: List of selected photos with notes
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - submitted_at: Submission timestamp (optional)
    - client_message: Message from client on submission (optional)
    """
    
    try:
        print(f"\nCreating table: {TABLE_NAME}")
        
        # Check if table already exists
        try:
            existing_table = dynamodb.Table(TABLE_NAME)
            existing_table.load()
            print(f"✓ Table '{TABLE_NAME}' already exists")
            print(f"  Status: {existing_table.table_status}")
            print(f"  Item Count: {existing_table.item_count}")
            return existing_table
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create table
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'  # String
                },
                {
                    'AttributeName': 'photographer_id',
                    'AttributeType': 'S'  # String
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'PhotographerSelectionSessionsIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'photographer_id',
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
        
        print(f"✓ Table '{TABLE_NAME}' created successfully")
        
        # Wait for table to be active
        print("  Waiting for table to become active...")
        table.wait_until_exists()
        
        print(f"✓ Table '{TABLE_NAME}' is now active")
        print(f"  Table ARN: {table.table_arn}")
        
        return table
        
    except ClientError as e:
        print(f"✗ Error creating table: {e.response['Error']['Message']}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_table_setup():
    """
    Verify that the table is properly configured
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.load()
        
        print(f"\n{'='*60}")
        print(f"Table Verification: {TABLE_NAME}")
        print(f"{'='*60}")
        
        print(f"\n✓ Table Status: {table.table_status}")
        print(f"✓ Item Count: {table.item_count}")
        print(f"✓ Table Size: {table.table_size_bytes} bytes")
        print(f"✓ Creation Time: {table.creation_date_time}")
        
        # Verify key schema
        print(f"\nKey Schema:")
        for key in table.key_schema:
            print(f"  - {key['AttributeName']} ({key['KeyType']})")
        
        # Verify GSI
        print(f"\nGlobal Secondary Indexes:")
        if table.global_secondary_indexes:
            for gsi in table.global_secondary_indexes:
                print(f"  - {gsi['IndexName']}")
                print(f"    Keys: {[k['AttributeName'] for k in gsi['KeySchema']]}")
                print(f"    Projection: {gsi['Projection']['ProjectionType']}")
                print(f"    Status: {gsi.get('IndexStatus', 'N/A')}")
        else:
            print("  No GSIs configured")
        
        # Verify provisioned throughput
        print(f"\nProvisioned Throughput:")
        print(f"  Read Capacity: {table.provisioned_throughput['ReadCapacityUnits']}")
        print(f"  Write Capacity: {table.provisioned_throughput['WriteCapacityUnits']}")
        
        print(f"\n{'='*60}")
        print(f"✓ Table verification complete")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed: {str(e)}")
        return False


def add_sample_data():
    """
    Add sample selection session for testing (optional)
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        from datetime import datetime, timezone, timedelta
        import uuid
        
        # Sample session
        sample_session = {
            'id': str(uuid.uuid4()),
            'gallery_id': 'sample_gallery_123',
            'photographer_id': 'sample_photographer_123',
            'client_email': 'client@example.com',
            'client_name': 'John Doe',
            'max_selections': 20,
            'deadline': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            'status': 'active',
            'selections': [],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=sample_session)
        
        print(f"✓ Added sample session: {sample_session['id']}")
        return sample_session['id']
        
    except Exception as e:
        print(f"✗ Error adding sample data: {str(e)}")
        return None


def cleanup_sample_data(session_id):
    """
    Remove sample data (optional)
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.delete_item(Key={'id': session_id})
        print(f"✓ Removed sample session: {session_id}")
    except Exception as e:
        print(f"✗ Error removing sample data: {str(e)}")


def main():
    """
    Main setup function
    """
    print("\n" + "="*60)
    print("Client Selections Table Setup")
    print("="*60)
    
    # Create table
    table = create_client_selections_table()
    
    # Verify setup
    if verify_table_setup():
        print("\n✓ Setup completed successfully!")
        
        # Ask about sample data
        if IS_LOCALSTACK:
            response = input("\nAdd sample data for testing? (y/n): ")
            if response.lower() == 'y':
                session_id = add_sample_data()
                if session_id:
                    response = input(f"\nRemove sample data now? (y/n): ")
                    if response.lower() == 'y':
                        cleanup_sample_data(session_id)
        
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("\n1. Add to utils/config.py:")
        print(f"   CLIENT_SELECTIONS_TABLE = '{TABLE_NAME}'")
        print(f"   client_selections_table = dynamodb.Table(CLIENT_SELECTIONS_TABLE)")
        print("\n2. Add to .env files:")
        print(f"   DYNAMODB_CLIENT_SELECTIONS_TABLE={TABLE_NAME}")
        print("\n3. Restart backend services:")
        print("   ./dev_tools/restart-backend.sh")
        print("\n4. Test selection endpoints:")
        print("   pytest tests/test_client_selection_workflow.py -v")
        print("\n" + "="*60 + "\n")
    else:
        print("\n✗ Setup failed. Please check errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

