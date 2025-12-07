"""
Configuration and AWS clients
"""
import os
import boto3

# AWS Region (default to us-east-1)
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# AWS clients with region
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# Configuration
S3_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')  # Photos storage bucket
S3_FRONTEND_BUCKET = os.environ.get('S3_BUCKET', 'galerly-frontend-app')  # Frontend bucket (separate)

# DynamoDB Tables from environment variables
users_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_USERS', 'galerly-users'))
galleries_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_GALLERIES', 'galerly-galleries'))
photos_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PHOTOS', 'galerly-photos'))
sessions_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SESSIONS', 'galerly-sessions'))
billing_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_BILLING', 'galerly-billing'))
subscriptions_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SUBSCRIPTIONS', 'galerly-subscriptions'))
analytics_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_ANALYTICS', 'galerly-analytics'))
client_favorites_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_CLIENT_FAVORITES', 'galerly-client-favorites'))
client_feedback_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_CLIENT_FEEDBACK', 'galerly-client-feedback'))

