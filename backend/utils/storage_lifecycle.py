"""
Storage Lifecycle Manager - Step 30
Manages S3 storage tiers, lifecycle policies, and archival for cost optimization

Architecture:
- Original files: Standard -> Intelligent-Tiering -> Glacier (archival path)
- Renditions: Standard -> Standard-IA (frequently accessed via CDN)
- Temporary files: Auto-delete after configurable period
- Deleted content: Graceful archival before permanent deletion
"""
import os
import boto3
from datetime import datetime, timedelta


class StorageLifecycleManager:
    """
    Manages S3 lifecycle policies for cost optimization
    Follows AWS best practices for photography storage
    """
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.bucket = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
        
        # Lifecycle policy configuration from environment
        # Days to keep originals in Standard before moving to Intelligent-Tiering
        self.original_standard_days = int(os.environ.get('LIFECYCLE_ORIGINAL_STANDARD_DAYS', '90'))
        
        # Days to keep originals before archiving to Glacier
        self.original_glacier_days = int(os.environ.get('LIFECYCLE_ORIGINAL_GLACIER_DAYS', '365'))
        
        # Days to keep renditions before moving to Infrequent Access
        self.rendition_ia_days = int(os.environ.get('LIFECYCLE_RENDITION_IA_DAYS', '180'))
        
        # Days to keep temporary files before deletion
        self.temp_expiry_days = int(os.environ.get('LIFECYCLE_TEMP_EXPIRY_DAYS', '7'))
        
        # Days to keep deleted content in Glacier before permanent deletion
        self.deleted_retention_days = int(os.environ.get('LIFECYCLE_DELETED_RETENTION_DAYS', '30'))


    def configure_all_policies(self):
        """
        Configure all lifecycle policies
        Returns True if successful
        """
        try:
            lifecycle_config = {
                'Rules': [
                    self._get_original_archive_rule(),
                    self._get_rendition_optimization_rule(),
                    self._get_temp_cleanup_rule(),
                    self._get_multipart_cleanup_rule(),
                    self._get_deleted_content_rule(),
                    self._get_zip_refresh_rule()
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket,
                LifecycleConfiguration=lifecycle_config
            )
            
            print(f"✅ Lifecycle policies configured for {self.bucket}")
            print(f"   - Originals: Standard ({self.original_standard_days}d) → Intelligent-Tiering → Glacier ({self.original_glacier_days}d)")
            print(f"   - Renditions: Standard → Standard-IA ({self.rendition_ia_days}d)")
            print(f"   - Temp files: Auto-delete ({self.temp_expiry_days}d)")
            print(f"   - Deleted content: Glacier → Permanent delete ({self.deleted_retention_days}d)")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure lifecycle policies: {str(e)}")
            return False


    def _get_original_archive_rule(self):
        """
        Rule: Archive original files progressively
        Standard -> Intelligent-Tiering -> Glacier IR
        
        Strategy:
        - Keep in Standard for fast access during active period
        - Move to Intelligent-Tiering for automatic cost optimization
        - Eventually archive to Glacier for long-term storage
        """
        return {
            'Id': 'ArchiveOriginalFiles',
            'Status': 'Enabled',
            'Filter': {
                'And': {
                    'Prefix': '',  # All files except those with specific prefixes
                    'Tags': []  # Apply to all non-tagged files (originals)
                }
            },
            'Transitions': [
                {
                    'Days': self.original_standard_days,
                    'StorageClass': 'INTELLIGENT_TIERING'
                },
                {
                    'Days': self.original_glacier_days,
                    'StorageClass': 'GLACIER_IR'  # Instant Retrieval for occasional downloads
                }
            ],
            'NoncurrentVersionTransitions': [
                {
                    'NoncurrentDays': 30,
                    'StorageClass': 'GLACIER_DEEP_ARCHIVE'
                }
            ]
        }


    def _get_rendition_optimization_rule(self):
        """
        Rule: Optimize rendition storage
        Renditions are accessed frequently via CDN, but old renditions can move to IA
        
        Strategy:
        - Keep recent renditions in Standard for fast CDN access
        - Move older renditions to Standard-IA
        - Don't archive renditions (can be regenerated if needed)
        """
        return {
            'Id': 'OptimizeRenditions',
            'Status': 'Enabled',
            'Filter': {
                'Prefix': 'renditions/'
            },
            'Transitions': [
                {
                    'Days': self.rendition_ia_days,
                    'StorageClass': 'STANDARD_IA'
                }
            ]
        }


    def _get_temp_cleanup_rule(self):
        """
        Rule: Auto-delete temporary files
        Temporary uploads, processing files, etc. should be cleaned up automatically
        """
        return {
            'Id': 'CleanupTempFiles',
            'Status': 'Enabled',
            'Filter': {
                'Prefix': 'temp/'
            },
            'Expiration': {
                'Days': self.temp_expiry_days
            }
        }


    def _get_multipart_cleanup_rule(self):
        """
        Rule: Clean up incomplete multipart uploads
        Failed or abandoned multipart uploads should be removed to save costs
        """
        return {
            'Id': 'CleanupIncompleteMultipart',
            'Status': 'Enabled',
            'Filter': {
                'Prefix': ''
            },
            'AbortIncompleteMultipartUpload': {
                'DaysAfterInitiation': self.temp_expiry_days
            }
        }


    def _get_deleted_content_rule(self):
        """
        Rule: Graceful archival of deleted content
        Content marked as deleted is archived before permanent removal
        
        Strategy:
        - Immediately move to Glacier on deletion
        - Keep for retention period (30 days default)
        - Permanent delete after retention period
        """
        return {
            'Id': 'ArchiveDeletedContent',
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
                'Days': self.deleted_retention_days
            }
        }


    def _get_zip_refresh_rule(self):
        """
        Rule: Manage ZIP archive lifecycle
        ZIP files should be refreshed periodically or when gallery changes
        
        Strategy:
        - Keep ZIPs in Standard for immediate download
        - Don't cache forever (regenerate on demand if expired)
        """
        return {
            'Id': 'ManageZipArchives',
            'Status': 'Enabled',
            'Filter': {
                'And': {
                    'Prefix': '',
                    'Tags': [
                        {'Key': 'type', 'Value': 'zip'}
                    ]
                }
            },
            'Transitions': [
                {
                    'Days': 90,
                    'StorageClass': 'STANDARD_IA'
                }
            ]
        }


    def configure_intelligent_tiering(self):
        """
        Configure S3 Intelligent-Tiering for automatic cost optimization
        Intelligent-Tiering automatically moves objects between access tiers
        based on changing access patterns
        """
        config = {
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
            self.s3_client.put_bucket_intelligent_tiering_configuration(
                Bucket=self.bucket,
                Id='GalerlyAutoTiering',
                IntelligentTieringConfiguration=config
            )
            print(f"✅ Intelligent-Tiering configured for {self.bucket}")
            return True
        except Exception as e:
            print(f"❌ Failed to configure Intelligent-Tiering: {str(e)}")
            return False


    def tag_file_for_deletion(self, s3_key):
        """
        Tag a file for deletion to trigger lifecycle archival
        
        Args:
            s3_key: S3 object key
        """
        try:
            self.s3_client.put_object_tagging(
                Bucket=self.bucket,
                Key=s3_key,
                Tagging={
                    'TagSet': [
                        {'Key': 'status', 'Value': 'deleted'},
                        {'Key': 'deleted_at', 'Value': datetime.utcnow().isoformat()}
                    ]
                }
            )
            print(f"✅ Tagged {s3_key} for deletion")
            return True
        except Exception as e:
            print(f"❌ Failed to tag {s3_key}: {str(e)}")
            return False


    def get_storage_analytics(self):
        """
        Get storage usage analytics
        Helps understand cost distribution across storage classes
        """
        try:
            # Get storage metrics from CloudWatch
            cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            
            metrics = {
                'total_size_bytes': 0,
                'object_count': 0,
                'storage_classes': {}
            }
            
            # Get bucket metrics
            for storage_class in ['StandardStorage', 'IntelligentTieringStorage', 
                                'StandardIAStorage', 'GlacierInstantRetrievalStorage',
                                'GlacierStorage', 'DeepArchiveStorage']:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': self.bucket},
                            {'Name': 'StorageType', 'Value': storage_class}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1 day
                        Statistics=['Average']
                    )
                    
                    if response['Datapoints']:
                        size = response['Datapoints'][0]['Average']
                        metrics['storage_classes'][storage_class] = size
                        metrics['total_size_bytes'] += size
                        
                except Exception as e:
                    print(f"⚠️  Could not get metrics for {storage_class}: {str(e)}")
            
            return metrics
            
        except Exception as e:
            print(f"❌ Failed to get storage analytics: {str(e)}")
            return None


def configure_lifecycle():
    """
    Main function to configure all lifecycle policies
    Can be called from setup scripts or Lambda
    """
    manager = StorageLifecycleManager()
    
    print("Configuring S3 lifecycle policies...")
    success = manager.configure_all_policies()
    
    if success:
        print("Configuring Intelligent-Tiering...")
        manager.configure_intelligent_tiering()
    
    print("Done!")
    return success


if __name__ == '__main__':
    configure_lifecycle()

