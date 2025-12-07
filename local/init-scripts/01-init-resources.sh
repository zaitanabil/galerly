#!/bin/bash
# LocalStack Initialization Script
# Runs after LocalStack is ready to create initial resources
# All values from environment variables

set -e

echo "🔧 LocalStack Init: Creating initial resources..."

# Load environment variables from .env.local if available
if [ -f /etc/localstack/init/.env.local ]; then
    export $(cat /etc/localstack/init/.env.local | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_REGION" ]; then
    echo "❌ AWS credentials not set in environment"
    exit 1
fi

if [ -z "$AWS_ENDPOINT_URL" ]; then
    echo "❌ AWS_ENDPOINT_URL not set in environment"
    exit 1
fi

if [ -z "$S3_PHOTOS_BUCKET" ] || [ -z "$S3_BUCKET" ] || [ -z "$S3_RENDITIONS_BUCKET" ]; then
    echo "❌ S3 bucket names not set in environment"
    exit 1
fi

# Create S3 buckets from environment variables
echo "📦 Creating S3 buckets..."
aws --endpoint-url="$AWS_ENDPOINT_URL" s3 mb "s3://$S3_PHOTOS_BUCKET" || true
aws --endpoint-url="$AWS_ENDPOINT_URL" s3 mb "s3://$S3_BUCKET" || true
aws --endpoint-url="$AWS_ENDPOINT_URL" s3 mb "s3://$S3_RENDITIONS_BUCKET" || true

# Enable CORS on S3 buckets (allow all origins for LocalStack development)
echo "🔧 Configuring S3 CORS..."
for bucket in "$S3_PHOTOS_BUCKET" "$S3_BUCKET" "$S3_RENDITIONS_BUCKET"; do
    aws --endpoint-url="$AWS_ENDPOINT_URL" s3api put-bucket-cors \
        --bucket "$bucket" \
        --cors-configuration '{
            "CORSRules": [{
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET", "HEAD", "POST", "PUT", "DELETE"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag", "Content-Length"],
                "MaxAgeSeconds": 3600
            }]
        }' || true
done

# Create DynamoDB tables
echo "🗄️  Creating DynamoDB tables..."

# Run Python setup script to create all tables
if [ -f /app/setup_dynamodb.py ]; then
    echo "Running setup_dynamodb.py create..."
    python3 /app/setup_dynamodb.py create || echo "⚠️  setup_dynamodb.py failed, falling back to manual table creation"
fi

# If setup_dynamodb.py didn't work or doesn't exist, create essential tables manually
if [ -z "$(aws --endpoint-url="$AWS_ENDPOINT_URL" dynamodb list-tables --query 'TableNames[0]' --output text 2>/dev/null)" ]; then
    echo "⚠️  No tables found, creating essential tables manually..."
    
    # Create essential tables if setup script is not available
    TABLES=(
        "users_table:$DYNAMODB_TABLE_USERS"
        "galleries_table:$DYNAMODB_TABLE_GALLERIES"
        "photos_table:$DYNAMODB_TABLE_PHOTOS"
        "sessions_table:$DYNAMODB_TABLE_SESSIONS"
        "visitor_table:$DYNAMODB_TABLE_VISITOR_TRACKING"
    )
    
    for table_def in "${TABLES[@]}"; do
        table_name="${table_def#*:}"
        if [ -n "$table_name" ]; then
            echo "Creating table: $table_name"
            aws --endpoint-url="$AWS_ENDPOINT_URL" dynamodb create-table \
                --table-name "$table_name" \
                --attribute-definitions \
                    AttributeName=id,AttributeType=S \
                --key-schema \
                    AttributeName=id,KeyType=HASH \
                --billing-mode PAY_PER_REQUEST || echo "Table $table_name may already exist"
        fi
    done
fi

echo "✅ LocalStack initialization complete"
