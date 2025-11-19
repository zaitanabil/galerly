#!/usr/bin/env python3
"""
Galerly - DynamoDB Setup & Management
Unified script for creating tables, indexes, and optimizing DynamoDB
Replaces: create-dynamodb-tables.sh, create-newsletter-table.sh, optimize_dynamodb.sh
"""
import boto3
import time
import sys
from typing import List, Dict
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE DEFINITIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TABLES = {
    'galerly-users': {
        'AttributeDefinitions': [
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'email', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-galleries': {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'client_email', 'AttributeType': 'S'},
            {'AttributeName': 'share_token', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'id', 'KeyType': 'RANGE'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'ClientEmailIndex',
                'KeySchema': [{'AttributeName': 'client_email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'ShareTokenIndex',
                'KeySchema': [{'AttributeName': 'share_token', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'GalleryIdIndex',
                'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-photos': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'gallery_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'GalleryIdIndex',
                'KeySchema': [{'AttributeName': 'gallery_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-sessions': {
        'AttributeDefinitions': [
            {'AttributeName': 'token', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'token', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-newsletters': {
        'AttributeDefinitions': [
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'subscribed_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'email', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'SubscribedAtIndex',
                'KeySchema': [{'AttributeName': 'subscribed_at', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-contact': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'CreatedAtIndex',
                'KeySchema': [{'AttributeName': 'created_at', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'StatusIndex',
                'KeySchema': [{'AttributeName': 'status', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-billing': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'CreatedAtIndex',
                'KeySchema': [{'AttributeName': 'created_at', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-subscriptions': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'stripe_subscription_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'StripeSubscriptionIndex',
                'KeySchema': [{'AttributeName': 'stripe_subscription_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-analytics': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'gallery_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            {'AttributeName': 'event_type', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'GalleryIdIndex',
                'KeySchema': [
                    {'AttributeName': 'gallery_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'EventTypeIndex',
                'KeySchema': [
                    {'AttributeName': 'event_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-client-favorites': {
        'AttributeDefinitions': [
            {'AttributeName': 'client_email', 'AttributeType': 'S'},
            {'AttributeName': 'photo_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'client_email', 'KeyType': 'HASH'},
            {'AttributeName': 'photo_id', 'KeyType': 'RANGE'}
        ],
        'GlobalSecondaryIndexes': []
    },
    'galerly-client-feedback': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'gallery_id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'GalleryIdIndex',
                'KeySchema': [
                    {'AttributeName': 'gallery_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-visitor-tracking': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'session_id', 'AttributeType': 'S'},
            {'AttributeName': 'event_type', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            {'AttributeName': 'page_url', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'SessionIdIndex',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'EventTypeIndex',
                'KeySchema': [
                    {'AttributeName': 'event_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'PageUrlIndex',
                'KeySchema': [
                    {'AttributeName': 'page_url', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-notification-preferences': {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': []
    },
    'galerly-refunds': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'StatusCreatedAtIndex',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    'galerly-audit-log': {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdTimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def table_exists(table_name: str) -> bool:
    """Check if table exists"""
    try:
        dynamodb.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise


def create_table(table_name: str, config: Dict) -> bool:
    """Create a DynamoDB table with indexes"""
    try:
        if table_exists(table_name):
            print(f"  ℹ️  {table_name} already exists")
            return True
        
        print(f"📝 Creating {table_name}...")
        
        # Prepare table parameters
        params = {
            'TableName': table_name,
            'AttributeDefinitions': config['AttributeDefinitions'],
            'KeySchema': config['KeySchema'],
            'BillingMode': 'PAY_PER_REQUEST',  # On-demand billing
            'SSESpecification': {
                'Enabled': True,
                'SSEType': 'KMS'  # Encryption at rest
            }
        }
        
        # Add GSIs if present and not empty
        if 'GlobalSecondaryIndexes' in config and config['GlobalSecondaryIndexes']:
            params['GlobalSecondaryIndexes'] = config['GlobalSecondaryIndexes']
        
        dynamodb.create_table(**params)
        print(f"  ✅ {table_name} created")
        return True
        
    except ClientError as e:
        print(f"  ❌ Error creating {table_name}: {str(e)}")
        return False


def wait_for_tables(table_names: List[str]):
    """Wait for all tables to become active"""
    print("\n⏳ Waiting for tables to become active...")
    
    for table_name in table_names:
        try:
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            print(f"  ✅ {table_name} is active")
        except Exception as e:
            print(f"  ⚠️  {table_name}: {str(e)}")


def enable_point_in_time_recovery(table_name: str):
    """Enable Point-in-Time Recovery for backups"""
    try:
        dynamodb.update_continuous_backups(
            TableName=table_name,
            PointInTimeRecoverySpecification={'PointInTimeRecoveryEnabled': True}
        )
        print(f"  ✅ Point-in-Time Recovery enabled for {table_name}")
    except ClientError as e:
        if 'already enabled' in str(e).lower():
            print(f"  ℹ️  PITR already enabled for {table_name}")
        else:
            print(f"  ⚠️  Could not enable PITR for {table_name}: {str(e)}")


def optimize_tables():
    """Enable security and optimization features on all tables"""
    print("\n🔧 Optimizing tables (security & performance)...")
    
    for table_name in TABLES.keys():
        if not table_exists(table_name):
            print(f"  ⚠️  {table_name} does not exist, skipping")
            continue
        
        print(f"\n🔐 Optimizing {table_name}...")
        enable_point_in_time_recovery(table_name)


def list_tables():
    """List all Galerly tables with their status"""
    print("\n📊 Current Galerly Tables:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for table_name in TABLES.keys():
        if table_exists(table_name):
            try:
                response = dynamodb.describe_table(TableName=table_name)
                table = response['Table']
                status = table['TableStatus']
                item_count = table.get('ItemCount', 0)
                billing = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
                
                print(f"\n📦 {table_name}")
                print(f"   Status: {status}")
                print(f"   Items: {item_count}")
                print(f"   Billing: {billing}")
                print(f"   Encryption: {'✅' if table.get('SSEDescription') else '❌'}")
                
                # List indexes
                gsi = table.get('GlobalSecondaryIndexes', [])
                if gsi:
                    print(f"   Indexes: {len(gsi)}")
                    for idx in gsi:
                        print(f"      • {idx['IndexName']} ({idx['IndexStatus']})")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        else:
            print(f"\n📦 {table_name}")
            print(f"   Status: ❌ Does not exist")


def create_all_tables():
    """Create all Galerly tables"""
    print("🗄️  Creating DynamoDB tables for Galerly...")
    print("")
    
    created_tables = []
    
    for table_name, config in TABLES.items():
        if create_table(table_name, config):
            created_tables.append(table_name)
    
    if created_tables:
        wait_for_tables(created_tables)
    
    print("\n✅ All tables processed!")
    print("\n📊 Table Structure:")
    print("  • galerly-users                    → Photographers/users")
    print("  • galerly-galleries                → Photo galleries (isolated per user)")
    print("  • galerly-photos                   → Photos (linked to galleries)")
    print("  • galerly-sessions                 → Auth sessions")
    print("  • galerly-newsletters              → Newsletter subscribers")
    print("  • galerly-contact                  → Support tickets")
    print("  • galerly-billing                  → Billing records")
    print("  • galerly-subscriptions            → Subscription management")
    print("  • galerly-refunds                  → Refund requests & status")
    print("  • galerly-audit-log                → Subscription change audit trail")
    print("  • galerly-analytics                → Analytics tracking")
    print("  • galerly-client-favorites         → Client photo favorites")
    print("  • galerly-client-feedback          → Client gallery feedback")
    print("  • galerly-visitor-tracking         → Website visitor tracking (UX analytics)")
    print("  • galerly-notification-preferences → Email notification settings")
    print("")
    print("🔒 Security Features:")
    print("  • Encryption at rest (KMS)")
    print("  • Pay-per-request billing (cost-efficient)")
    print("  • User data isolation via partition keys")
    print("  • Point-in-Time Recovery (backups)")


def delete_all_tables():
    """Delete all Galerly tables (use with caution!)"""
    print("⚠️  WARNING: This will delete ALL Galerly tables and data!")
    response = input("Type 'DELETE ALL TABLES' to confirm: ")
    
    if response != 'DELETE ALL TABLES':
        print("❌ Cancelled")
        return
    
    print("\n🗑️  Deleting tables...")
    
    for table_name in TABLES.keys():
        if table_exists(table_name):
            try:
                dynamodb.delete_table(TableName=table_name)
                print(f"  ✅ {table_name} deleted")
            except Exception as e:
                print(f"  ❌ Error deleting {table_name}: {str(e)}")
        else:
            print(f"  ℹ️  {table_name} does not exist")
    
    print("\n✅ All tables deleted")


def main():
    """Main function"""
    print("=" * 70)
    print("🔧 GALERLY - DynamoDB Setup & Management")
    print("=" * 70)
    print("")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_dynamodb.py create    # Create all tables")
        print("  python setup_dynamodb.py optimize  # Optimize existing tables")
        print("  python setup_dynamodb.py list      # List all tables")
        print("  python setup_dynamodb.py delete    # Delete all tables (⚠️  dangerous!)")
        print("")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        create_all_tables()
        optimize_tables()
    elif command == 'optimize':
        optimize_tables()
    elif command == 'list':
        list_tables()
    elif command == 'delete':
        delete_all_tables()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: create, optimize, list, delete")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()

