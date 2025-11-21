"""
S3 Lifecycle Policy Configuration - Step 30
Manages storage tiers and archival for cost optimization
"""
import boto3
import json
import os

s3_client = boto3.client('s3')

# Configuration
PHOTOS_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')


def configure_lifecycle_policies():
    """
    Step 30: Configure S3 lifecycle policies
    
    Strategy:
    - Original files: Keep in Standard for 90 days, then move to Intelligent-Tiering
    - Renditions: Keep in Standard (frequently accessed via CDN)
    - Deleted photos: Move to Glacier for 30 days before permanent deletion
    - Temporary files: Auto-delete after 7 days
    """
    
    lifecycle_config = {
        'Rules': [
            {
                'Id': 'ArchiveOriginals',
                'Status': 'Enabled',
                'Filter': {
                    'And': {
                        'Prefix': '',
                        'Tags': [
                            {'Key': 'type', 'Value': 'original'}
                        ]
                    }
                },
                'Transitions': [
                    {
                        'Days': 90,
                        'StorageClass': 'INTELLIGENT_TIERING'
                    },
                    {
                        'Days': 365,
                        'StorageClass': 'GLACIER_IR'
                    }
                ]
            },
            {
                'Id': 'DeleteTempFiles',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': 'temp/'
                },
                'Expiration': {
                    'Days': 7
                }
            },
            {
                'Id': 'DeleteOldMultipartUploads',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': ''
                },
                'AbortIncompleteMultipartUpload': {
                    'DaysAfterInitiation': 7
                }
            },
            {
                'Id': 'MoveRenditionsToIA',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': 'renditions/'
                },
                'Transitions': [
                    {
                        'Days': 180,
                        'StorageClass': 'STANDARD_IA'  # Infrequent Access for old renditions
                    }
                ]
            },
            {
                'Id': 'ArchiveDeletedPhotos',
                'Status': 'Enabled',
                'Filter': {
                    'And': {
                        'Prefix': '',
                        'Tags': [
                            {'Key': 'status', 'Value': 'deleted'}
                        ]
                    }
                },
                'Transitions': [
                    {
                        'Days': 1,
                        'StorageClass': 'GLACIER_FLEXIBLE_RETRIEVAL'
                    }
                ],
                'Expiration': {
                    'Days': 30  # Permanent delete after 30 days
                }
            }
        ]
    }
    
    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=PHOTOS_BUCKET,
            LifecycleConfiguration=lifecycle_config
        )
        print(f"✅ Lifecycle policies configured for {PHOTOS_BUCKET}")
        return True
    except Exception as e:
        print(f"❌ Failed to configure lifecycle policies: {str(e)}")
        return False


def configure_intelligent_tiering():
    """
    Configure S3 Intelligent-Tiering for automatic cost optimization
    """
    
    intelligent_tiering_config = {
        'Id': 'GalerlyAutoTiering',
        'Status': 'Enabled',
        'Tierings': [
            {
                'Days': 90,
                'AccessTier': 'ARCHIVE_ACCESS'
            },
            {
                'Days': 180,
                'AccessTier': 'DEEP_ARCHIVE_ACCESS'
            }
        ]
    }
    
    try:
        s3_client.put_bucket_intelligent_tiering_configuration(
            Bucket=PHOTOS_BUCKET,
            Id='GalerlyAutoTiering',
            IntelligentTieringConfiguration=intelligent_tiering_config
        )
        print(f"✅ Intelligent-Tiering configured for {PHOTOS_BUCKET}")
        return True
    except Exception as e:
        print(f"❌ Failed to configure Intelligent-Tiering: {str(e)}")
        return False


if __name__ == '__main__':
    print("Configuring S3 lifecycle policies...")
    configure_lifecycle_policies()
    configure_intelligent_tiering()
    print("Done!")

