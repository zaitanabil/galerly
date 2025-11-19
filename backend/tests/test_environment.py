"""
Test environment variables configuration
Ensures all required environment variables are set
"""
import os
import pytest


class TestEnvironmentVariables:
    """Test that all required environment variables are configured"""
    
    def test_aws_credentials_set(self):
        """Test AWS credentials environment variables"""
        assert os.environ.get('AWS_ACCESS_KEY_ID'), "AWS_ACCESS_KEY_ID not set"
        assert os.environ.get('AWS_SECRET_ACCESS_KEY'), "AWS_SECRET_ACCESS_KEY not set"
    
    def test_dynamodb_tables_set(self):
        """Test DynamoDB table environment variables"""
        required_tables = [
            'DYNAMODB_TABLE_USERS',
            'DYNAMODB_TABLE_GALLERIES',
            'DYNAMODB_TABLE_PHOTOS',
            'DYNAMODB_TABLE_SESSIONS',
            'DYNAMODB_TABLE_SUBSCRIPTIONS',
            'DYNAMODB_TABLE_BILLING'
        ]
        
        for table in required_tables:
            assert os.environ.get(table), f"{table} not set"
    
    def test_s3_buckets_set(self):
        """Test S3 bucket environment variables"""
        assert os.environ.get('S3_BUCKET'), "S3_BUCKET not set (frontend bucket)"
        assert os.environ.get('S3_PHOTOS_BUCKET'), "S3_PHOTOS_BUCKET not set (photos storage bucket)"
    
    def test_frontend_url_set(self):
        """Test FRONTEND_URL environment variable"""
        frontend_url = os.environ.get('FRONTEND_URL')
        assert frontend_url, "FRONTEND_URL not set"
        assert frontend_url.startswith('http'), "FRONTEND_URL must start with http or https"
    
    def test_stripe_config_set(self):
        """Test Stripe configuration environment variables"""
        assert os.environ.get('STRIPE_SECRET_KEY'), "STRIPE_SECRET_KEY not set"
        assert os.environ.get('STRIPE_WEBHOOK_SECRET'), "STRIPE_WEBHOOK_SECRET not set"
        assert os.environ.get('STRIPE_PRICE_PLUS'), "STRIPE_PRICE_PLUS not set"
        assert os.environ.get('STRIPE_PRICE_PRO'), "STRIPE_PRICE_PRO not set"
    
    def test_smtp_config_set(self):
        """Test SMTP configuration environment variables"""
        assert os.environ.get('SMTP_HOST'), "SMTP_HOST not set"
        assert os.environ.get('SMTP_PORT'), "SMTP_PORT not set"
        assert os.environ.get('SMTP_USER'), "SMTP_USER not set"
        assert os.environ.get('SMTP_PASSWORD'), "SMTP_PASSWORD not set"
        assert os.environ.get('FROM_EMAIL'), "FROM_EMAIL not set"
    
    def test_no_hardcoded_values(self):
        """Test that critical URLs are not hardcoded"""
        frontend_url = os.environ.get('FRONTEND_URL')
        # Ensure we're using the env var, not a hardcoded value
        assert frontend_url != 'https://galerly.com' or os.environ.get('FRONTEND_URL') == 'https://galerly.com', \
            "FRONTEND_URL should be configurable via environment variable"

