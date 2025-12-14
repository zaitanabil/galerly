#!/usr/bin/env python3
"""
Galerly - DynamoDB Setup & Management (LocalStack Compatible)
Works with both AWS and LocalStack based on environment configuration
"""
import boto3
import time
import sys
import os
from typing import List, Dict
from botocore.exceptions import ClientError

# LocalStack detection
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', None)
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients with LocalStack support
def create_dynamodb_clients():
    """Create DynamoDB clients with LocalStack support if configured"""
    client_args = {
        'service_name': 'dynamodb',
        'region_name': AWS_REGION
    }
    
    resource_args = {
        'service_name': 'dynamodb',
        'region_name': AWS_REGION
    }
    
    # LocalStack configuration
    if AWS_ENDPOINT_URL:
        print(f"🔧 Using LocalStack endpoint: {AWS_ENDPOINT_URL}")
        client_args['endpoint_url'] = AWS_ENDPOINT_URL
        client_args['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
        client_args['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
        
        resource_args['endpoint_url'] = AWS_ENDPOINT_URL
        resource_args['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
        resource_args['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
    
    return boto3.client(**client_args), boto3.resource(**resource_args)

dynamodb, dynamodb_resource = create_dynamodb_clients()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE DEFINITIONS (using environment variables for table names)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Get table names from environment (supports local suffixes)
def get_table_name(base_name):
    """
    Get table name from environment or use base name
    Converts 'galerly-users' to DYNAMODB_TABLE_USERS env var
    """
    # Remove 'galerly-' prefix and convert to env var format
    # galerly-users -> users -> USERS -> DYNAMODB_TABLE_USERS
    table_suffix = base_name.replace('galerly-', '', 1)
    env_var = f"DYNAMODB_TABLE_{table_suffix.upper().replace('-', '_')}"
    return os.environ.get(env_var, base_name)

TABLES = {
    get_table_name('galerly-users'): {
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
    get_table_name('galerly-galleries'): {
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
    get_table_name('galerly-photos'): {
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
    get_table_name('galerly-sessions'): {
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
    get_table_name('galerly-background-jobs'): {
        'AttributeDefinitions': [
            {'AttributeName': 'job_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_email', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'job_id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserEmailIndex',
                'KeySchema': [
                    {'AttributeName': 'user_email', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-newsletters'): {
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
    get_table_name('galerly-contact'): {
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
    get_table_name('galerly-billing'): {
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
    get_table_name('galerly-invoices'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'client_email', 'AttributeType': 'S'}
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
                'IndexName': 'ClientEmailIndex',
                'KeySchema': [{'AttributeName': 'client_email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-appointments'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'client_email', 'AttributeType': 'S'}
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
                'IndexName': 'ClientEmailIndex',
                'KeySchema': [{'AttributeName': 'client_email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-contracts'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'client_email', 'AttributeType': 'S'}
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
                'IndexName': 'ClientEmailIndex',
                'KeySchema': [{'AttributeName': 'client_email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-subscriptions'): {
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
    get_table_name('galerly-analytics'): {
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
    get_table_name('galerly-client-favorites'): {
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
    get_table_name('galerly-client-feedback'): {
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
    get_table_name('galerly-video-analytics'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'gallery_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
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
            }
        ]
    },
    
    get_table_name('galerly-visitor-tracking'): {
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
    get_table_name('galerly-notification-preferences'): {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': []
    },
    get_table_name('galerly-refunds'): {
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
    get_table_name('galerly-audit-log'): {
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
    },
    get_table_name('galerly-features'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': []
    },
    get_table_name('galerly-user-features'): {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'feature_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'feature_id', 'KeyType': 'RANGE'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'FeatureIdIndex',
                'KeySchema': [{'AttributeName': 'feature_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-email-templates'): {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'template_type', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'template_type', 'KeyType': 'RANGE'}
        ],
        'GlobalSecondaryIndexes': []
    },
    get_table_name('galerly-raw-vault'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'photo_id', 'AttributeType': 'S'}
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
                'IndexName': 'PhotoIdIndex',
                'KeySchema': [{'AttributeName': 'photo_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-seo-settings'): {
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': []
    },
    get_table_name('galerly-leads'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
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
    get_table_name('galerly-followup-sequences'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'lead_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'LeadIdIndex',
                'KeySchema': [
                    {'AttributeName': 'lead_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-testimonials'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
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
    get_table_name('galerly-services'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'display_order', 'AttributeType': 'N'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'display_order', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-sales'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'customer_email', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'CustomerEmailIndex',
                'KeySchema': [
                    {'AttributeName': 'customer_email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-packages'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'display_order', 'AttributeType': 'N'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'display_order', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-downloads'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'customer_email', 'AttributeType': 'S'},
            {'AttributeName': 'sale_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'CustomerEmailIndex',
                'KeySchema': [
                    {'AttributeName': 'customer_email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'SaleIdIndex',
                'KeySchema': [
                    {'AttributeName': 'sale_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-payment-reminders'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
            {'AttributeName': 'invoice_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'InvoiceIdIndex',
                'KeySchema': [
                    {'AttributeName': 'invoice_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-onboarding-workflows'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'photographer_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'PhotographerIdIndex',
                'KeySchema': [
                    {'AttributeName': 'photographer_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    
    # Feature Requests table
    get_table_name('galerly-feature-requests'): {
        'AttributeDefinitions': [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'StatusCreatedIndex',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    get_table_name('galerly-custom-domains'): {
        'AttributeDefinitions': [
            {'AttributeName': 'domain', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'domain', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCTIONS (rest of the file remains the same)
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
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        # LocalStack doesn't support KMS encryption, skip for local
        if not AWS_ENDPOINT_URL:
            params['SSESpecification'] = {
                'Enabled': True,
                'SSEType': 'KMS'
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
    """Enable Point-in-Time Recovery for backups (AWS only, not LocalStack)"""
    # Skip for LocalStack
    if AWS_ENDPOINT_URL:
        print(f"  ⏭️  Skipping PITR for {table_name} (LocalStack)")
        return
    
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
    if AWS_ENDPOINT_URL:
        print(f"   Using LocalStack: {AWS_ENDPOINT_URL}")
    print("")
    
    created_tables = []
    
    for table_name, config in TABLES.items():
        if create_table(table_name, config):
            created_tables.append(table_name)
    
    if created_tables:
        wait_for_tables(created_tables)
    
    print("\n✅ All tables processed!")


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
    if AWS_ENDPOINT_URL:
        print(f"   LocalStack Mode: {AWS_ENDPOINT_URL}")
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
        # Note: S3 bucket setup is handled by init scripts in LocalStack
        # The init-resources.sh script already creates and configures S3 buckets
        if AWS_ENDPOINT_URL:
            print("")
            print("ℹ️  S3 bucket setup is handled by LocalStack init scripts")
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
