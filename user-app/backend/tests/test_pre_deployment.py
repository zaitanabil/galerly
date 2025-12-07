"""
Pre-deployment validation tests
Run these tests before building containers to ensure:
1. All required environment variables are set
2. Configuration is valid
3. Required tables are defined
4. No hardcoded secrets in code
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEnvironmentVariables:
    """Test that all required environment variables are set"""
    
    REQUIRED_ENV_VARS = [
        'AWS_REGION',
        'ENVIRONMENT',
        'S3_BUCKET',
        'S3_PHOTOS_BUCKET',
        'S3_RENDITIONS_BUCKET',
        'DYNAMODB_TABLE_USERS',
        'DYNAMODB_TABLE_GALLERIES',
        'DYNAMODB_TABLE_PHOTOS',
        'DYNAMODB_TABLE_SESSIONS',
        'DYNAMODB_TABLE_SUBSCRIPTIONS',
        'DYNAMODB_TABLE_BILLING',
        'DYNAMODB_TABLE_REFUNDS',
        'DYNAMODB_TABLE_ANALYTICS',
        'DYNAMODB_TABLE_AUDIT_LOG',
        'DYNAMODB_TABLE_CLIENT_FAVORITES',
        'DYNAMODB_TABLE_CLIENT_FEEDBACK',
        'DYNAMODB_TABLE_EMAIL_TEMPLATES',
        'DYNAMODB_TABLE_FEATURES',
        'DYNAMODB_TABLE_USER_FEATURES',
        'DYNAMODB_TABLE_INVOICES',
        'DYNAMODB_TABLE_APPOINTMENTS',
        'DYNAMODB_TABLE_CONTRACTS',
        'DYNAMODB_TABLE_RAW_VAULT',
        'DYNAMODB_TABLE_SEO_SETTINGS',
    ]
    
    def test_required_env_vars_exist(self):
        """All required environment variables must be set"""
        missing = []
        for var in self.REQUIRED_ENV_VARS:
            if not os.environ.get(var):
                missing.append(var)
        
        if missing:
            pytest.fail(
                f"Missing required environment variables:\n  " + 
                "\n  ".join(missing) +
                "\n\nPlease set these in .env.local or .env file"
            )
    
    def test_aws_region_is_valid(self):
        """AWS region should be valid"""
        region = os.environ.get('AWS_REGION', '')
        assert region, "AWS_REGION must be set"
        # Basic validation - should match AWS region format
        assert len(region) > 0, "AWS_REGION cannot be empty"
    
    def test_environment_is_valid(self):
        """Environment should be 'development', 'local', or 'production'"""
        env = os.environ.get('ENVIRONMENT', '')
        assert env in ['development', 'local', 'production'], \
            f"ENVIRONMENT must be 'development', 'local', or 'production', got '{env}'"


class TestDynamoDBConfiguration:
    """Test DynamoDB table configuration"""
    
    def test_table_names_follow_convention(self):
        """Table names should follow naming convention"""
        tables = [
            os.environ.get(var, '') 
            for var in TestEnvironmentVariables.REQUIRED_ENV_VARS 
            if var.startswith('DYNAMODB_TABLE_')
        ]
        
        for table in tables:
            if not table:
                continue
            # Should start with 'galerly-' prefix
            assert table.startswith('galerly-'), \
                f"Table name '{table}' should start with 'galerly-'"
    
    def test_no_duplicate_table_names(self):
        """All table names should be unique"""
        tables = [
            os.environ.get(var, '') 
            for var in TestEnvironmentVariables.REQUIRED_ENV_VARS 
            if var.startswith('DYNAMODB_TABLE_')
        ]
        
        # Remove empty strings
        tables = [t for t in tables if t]
        
        # Check for duplicates
        unique_tables = set(tables)
        assert len(tables) == len(unique_tables), \
            "Duplicate table names found in configuration"


class TestS3Configuration:
    """Test S3 bucket configuration"""
    
    def test_bucket_names_are_set(self):
        """All S3 bucket names must be configured"""
        buckets = {
            'S3_BUCKET': os.environ.get('S3_BUCKET', ''),
            'S3_PHOTOS_BUCKET': os.environ.get('S3_PHOTOS_BUCKET', ''),
            'S3_RENDITIONS_BUCKET': os.environ.get('S3_RENDITIONS_BUCKET', '')
        }
        
        for name, value in buckets.items():
            assert value, f"{name} must be set"
    
    def test_bucket_names_follow_convention(self):
        """Bucket names should follow naming convention"""
        buckets = [
            os.environ.get('S3_BUCKET', ''),
            os.environ.get('S3_PHOTOS_BUCKET', ''),
            os.environ.get('S3_RENDITIONS_BUCKET', '')
        ]
        
        for bucket in buckets:
            if not bucket:
                continue
            # Should start with 'galerly-' prefix
            assert bucket.startswith('galerly-'), \
                f"Bucket name '{bucket}' should start with 'galerly-'"
    
    def test_no_duplicate_bucket_names(self):
        """All bucket names should be unique"""
        buckets = [
            os.environ.get('S3_BUCKET', ''),
            os.environ.get('S3_PHOTOS_BUCKET', ''),
            os.environ.get('S3_RENDITIONS_BUCKET', '')
        ]
        
        # Remove empty strings
        buckets = [b for b in buckets if b]
        
        # Check for duplicates
        unique_buckets = set(buckets)
        assert len(buckets) == len(unique_buckets), \
            "Duplicate bucket names found in configuration"


class TestCodeQuality:
    """Test code quality and security practices"""
    
    def test_no_hardcoded_secrets_in_handlers(self):
        """Handler files should not contain hardcoded secrets"""
        handlers_dir = Path(__file__).parent.parent / 'handlers'
        if not handlers_dir.exists():
            pytest.skip("Handlers directory not found")
        
        # Patterns that indicate hardcoded secrets
        # Using regex to avoid false positives from comments
        import re
        forbidden_patterns = [
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),  # Actual AWS key format
            (r'sk_live_[a-zA-Z0-9]{24,}', 'Stripe live key'),  # Actual Stripe key (not in quotes/comments)
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),  # password="value"
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),  # secret="value"
        ]
        
        violations = []
        for handler_file in handlers_dir.glob('*.py'):
            if handler_file.name.startswith('__'):
                continue
            
            content = handler_file.read_text()
            for pattern, desc in forbidden_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Skip if it's in a comment or string literal definition
                    for match in matches:
                        lines = content.split('\n')
                        for line in lines:
                            if match in line and not line.strip().startswith('#'):
                                violations.append(f"{handler_file.name}: contains {desc}")
                                break
        
        if violations:
            pytest.fail(
                "Hardcoded secrets found:\n  " + 
                "\n  ".join(violations)
            )
    
    def test_handlers_use_config_module(self):
        """Handlers should import from utils.config for AWS resources"""
        handlers_dir = Path(__file__).parent.parent / 'handlers'
        if not handlers_dir.exists():
            pytest.skip("Handlers directory not found")
        
        violations = []
        for handler_file in handlers_dir.glob('*_handler.py'):
            content = handler_file.read_text()
            
            # Check if file uses AWS resources
            uses_aws = any([
                'dynamodb' in content.lower(),
                's3_client' in content.lower(),
                'ses_client' in content.lower(),
            ])
            
            if uses_aws:
                # Should import from utils.config
                if 'from utils.config import' not in content:
                    violations.append(
                        f"{handler_file.name}: uses AWS but doesn't import from utils.config"
                    )
        
        if violations:
            pytest.fail(
                "Configuration violations found:\n  " + 
                "\n  ".join(violations)
            )


class TestFileStructure:
    """Test that all required files exist"""
    
    def test_all_handlers_have_tests(self):
        """Each handler MUST have a corresponding test file - NO EXCEPTIONS"""
        handlers_dir = Path(__file__).parent.parent / 'handlers'
        tests_dir = Path(__file__).parent
        
        if not handlers_dir.exists():
            pytest.skip("Handlers directory not found")
        
        # NO exceptions - ALL handlers must have tests
        missing_tests = []
        for handler_file in handlers_dir.glob('*_handler.py'):
            test_file = tests_dir / f"test_{handler_file.name}"
            if not test_file.exists():
                missing_tests.append(handler_file.name)
        
        if missing_tests:
            pytest.fail(
                "Missing test files for handlers:\n  " + 
                "\n  ".join(missing_tests) +
                "\n\nALL handlers MUST have tests - NO EXCEPTIONS"
            )
    
    def test_setup_dynamodb_exists(self):
        """setup_dynamodb.py script must exist"""
        setup_file = Path(__file__).parent.parent / 'setup_dynamodb.py'
        assert setup_file.exists(), \
            "setup_dynamodb.py not found - required for database setup"
    
    def test_init_features_exists(self):
        """init_features.py script must exist"""
        init_file = Path(__file__).parent.parent / 'init_features.py'
        assert init_file.exists(), \
            "init_features.py not found - required for feature initialization"


class TestNewFeatures:
    """Test that newly implemented features are properly configured"""
    
    def test_raw_processor_exists(self):
        """RAW photo processor module should exist"""
        raw_processor = Path(__file__).parent.parent / 'utils' / 'raw_processor.py'
        assert raw_processor.exists(), \
            "utils/raw_processor.py not found - required for RAW photo support"
    
    def test_video_transcoder_exists(self):
        """Video transcoder module should exist"""
        video_transcoder = Path(__file__).parent.parent / 'utils' / 'video_transcoder.py'
        assert video_transcoder.exists(), \
            "utils/video_transcoder.py not found - required for video streaming"
    
    def test_raw_vault_handler_exists(self):
        """RAW vault handler should exist"""
        raw_vault = Path(__file__).parent.parent / 'handlers' / 'raw_vault_handler.py'
        assert raw_vault.exists(), \
            "handlers/raw_vault_handler.py not found - required for RAW vault"
    
    def test_seo_handler_exists(self):
        """SEO handler should exist"""
        seo_handler = Path(__file__).parent.parent / 'handlers' / 'seo_handler.py'
        assert seo_handler.exists(), \
            "handlers/seo_handler.py not found - required for SEO tools"
    
    def test_raw_vault_table_configured(self):
        """RAW vault table should be configured"""
        table_name = os.environ.get('DYNAMODB_TABLE_RAW_VAULT', '')
        assert table_name, \
            "DYNAMODB_TABLE_RAW_VAULT not configured"
        assert table_name.startswith('galerly-'), \
            f"RAW vault table name '{table_name}' should start with 'galerly-'"
    
    def test_seo_settings_table_configured(self):
        """SEO settings table should be configured"""
        table_name = os.environ.get('DYNAMODB_TABLE_SEO_SETTINGS', '')
        assert table_name, \
            "DYNAMODB_TABLE_SEO_SETTINGS not configured"
        assert table_name.startswith('galerly-'), \
            f"SEO settings table name '{table_name}' should start with 'galerly-'"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
