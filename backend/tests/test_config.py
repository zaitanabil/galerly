"""
Test configuration and AWS resource connectivity
"""
import pytest
import boto3
import os
from botocore.exceptions import ClientError


class TestAWSResources:
    """Test AWS resource connectivity (runs against actual production AWS)"""
    
    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not configured"
    )
    def test_dynamodb_tables_exist(self):
        """Test that all required DynamoDB tables exist"""
        dynamodb = boto3.client('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        required_tables = [
            os.environ.get('DYNAMODB_TABLE_USERS'),
            os.environ.get('DYNAMODB_TABLE_GALLERIES'),
            os.environ.get('DYNAMODB_TABLE_PHOTOS'),
            os.environ.get('DYNAMODB_TABLE_SESSIONS'),
            os.environ.get('DYNAMODB_TABLE_SUBSCRIPTIONS'),
            os.environ.get('DYNAMODB_TABLE_BILLING')
        ]
        
        for table_name in required_tables:
            if not table_name:
                pytest.skip(f"Table environment variable not set")
                
            try:
                # Check if table exists
                response = dynamodb.describe_table(TableName=table_name)
                assert response['Table']['TableStatus'] in ['ACTIVE', 'UPDATING']
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    pytest.fail(f"Production table {table_name} does not exist")
                else:
                    raise
    
    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not configured"
    )
    def test_s3_bucket_exists(self):
        """Test that S3 buckets exist"""
        s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        # Test photos bucket (primary bucket for image storage)
        photos_bucket = os.environ.get('S3_PHOTOS_BUCKET')
        if photos_bucket:
            try:
                s3.head_bucket(Bucket=photos_bucket)
                print(f"✅ Photos bucket exists: {photos_bucket}")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    pytest.fail(f"Production photos bucket {photos_bucket} does not exist")
                else:
                    raise
        
        # Test frontend bucket (optional check)
        frontend_bucket = os.environ.get('S3_BUCKET')
        if frontend_bucket:
            try:
                s3.head_bucket(Bucket=frontend_bucket)
                print(f"✅ Frontend bucket exists: {frontend_bucket}")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    pytest.fail(f"Production frontend bucket {frontend_bucket} does not exist")
                else:
                    raise
        
        if not photos_bucket and not frontend_bucket:
            pytest.skip("No S3 bucket environment variables set")


class TestConfiguration:
    """Test configuration module"""
    
    def test_config_imports(self):
        """Test that config module imports correctly"""
        from utils import config
        assert hasattr(config, 'galleries_table')
        assert hasattr(config, 'photos_table')
        assert hasattr(config, 'users_table')
        assert hasattr(config, 'sessions_table')
    
    def test_config_dynamodb_tables(self):
        """Test that DynamoDB tables are configured"""
        from utils import config
        
        # Check that tables are DynamoDB Table resources
        assert config.galleries_table is not None
        assert config.photos_table is not None
        assert config.users_table is not None
        assert config.sessions_table is not None
    
    def test_config_uses_environment_variables(self):
        """Test that config uses environment variables"""
        import os
        from utils import config
        
        # Verify that environment variables are being used
        assert os.environ.get('DYNAMODB_TABLE_USERS') is not None
        assert os.environ.get('DYNAMODB_TABLE_GALLERIES') is not None

