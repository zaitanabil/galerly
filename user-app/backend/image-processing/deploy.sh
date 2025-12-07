#!/bin/bash
set -e

# Deploy Image Processing Lambda
# This Lambda is triggered by S3 uploads to automatically generate renditions

echo "=========================================="
echo "🚀 DEPLOYING IMAGE PROCESSING LAMBDA"
echo "=========================================="

# Configuration
FUNCTION_NAME="galerly-image-processing"
ROLE_NAME="lambda-image-processing-role"
LAYER_NAME="galerly-image-processing-layer"
SOURCE_BUCKET="galerly-images-storage"
RENDITIONS_BUCKET="galerly-renditions"
CDN_DOMAIN="cdn.galerly.com"
REGION="us-east-1"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "📋 AWS Account ID: $ACCOUNT_ID"

# Create IAM role if it doesn't exist
if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo "⚠️  IAM role '$ROLE_NAME' not found!"
    echo "Creating IAM role..."
    
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }'
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Add S3 and DynamoDB permissions
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name ImageProcessingPolicy \
        --policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Effect\": \"Allow\",
                    \"Action\": [
                        \"s3:GetObject\",
                        \"s3:HeadObject\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${SOURCE_BUCKET}/*\"
                },
                {
                    \"Effect\": \"Allow\",
                    \"Action\": [
                        \"s3:PutObject\",
                        \"s3:PutObjectAcl\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${RENDITIONS_BUCKET}/*\"
                },
                {
                    \"Effect\": \"Allow\",
                    \"Action\": [
                        \"dynamodb:UpdateItem\",
                        \"dynamodb:GetItem\"
                    ],
                    \"Resource\": \"arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/galerly-photos\"
                }
            ]
        }"
    
    echo "⏳ Waiting for IAM role to propagate..."
    sleep 10
    echo "✅ IAM role created"
fi

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "📋 IAM Role: $ROLE_ARN"

# Create Lambda Layer with image processing libraries
echo ""
echo "📦 Creating Lambda Layer with dependencies..."

# Create layer directory
mkdir -p layer/python
cd layer/python

# Install dependencies
pip install \
    Pillow \
    rawpy \
    pillow-heif \
    numpy \
    -t . \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.11

cd ../..

# Package layer
cd layer
zip -r ../layer.zip . -q
cd ..

echo "📊 Layer size: $(du -h layer.zip | cut -f1)"

# Create or update layer
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --description "Image processing libraries (Pillow, rawpy, pillow-heif, numpy)" \
    --zip-file fileb://layer.zip \
    --compatible-runtimes python3.11 \
    --region $REGION \
    --query 'Version' \
    --output text)

LAYER_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:layer:${LAYER_NAME}:${LAYER_VERSION}"
echo "✅ Lambda Layer created: Version $LAYER_VERSION"

# Clean up layer files
rm -rf layer layer.zip

# Package Lambda function
echo ""
echo "📦 Packaging Lambda function..."
zip -j function.zip lambda_function.py

echo "📊 Function size: $(du -h function.zip | cut -f1)"

# Create or update Lambda function
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text
    
    # Wait for update to complete
    aws lambda wait function-updated \
        --function-name $FUNCTION_NAME \
        --region $REGION
    
    # Update configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout 300 \
        --memory-size 3008 \
        --layers $LAYER_ARN \
        --environment "Variables={SOURCE_BUCKET=${SOURCE_BUCKET},RENDITIONS_BUCKET=${RENDITIONS_BUCKET},CDN_DOMAIN=${CDN_DOMAIN}}" \
        --region $REGION \
        --query 'FunctionArn' \
        --output text
    
    echo "✅ Lambda function updated"
else
    echo "🆕 Creating new Lambda function..."
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 300 \
        --memory-size 3008 \
        --layers $LAYER_ARN \
        --environment "Variables={SOURCE_BUCKET=${SOURCE_BUCKET},RENDITIONS_BUCKET=${RENDITIONS_BUCKET},CDN_DOMAIN=${CDN_DOMAIN}}" \
        --region $REGION \
        --query 'FunctionArn' \
        --output text
    
    echo "✅ Lambda function created"
fi

# Clean up
rm -f function.zip

# Configure S3 trigger
echo ""
echo "🔗 Configuring S3 trigger..."

# Add Lambda permission for S3 to invoke
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id S3InvokePermission \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::${SOURCE_BUCKET} \
    --region $REGION \
    2>/dev/null || echo "⏭️  Permission already exists"

# Wait for permission to propagate
echo "⏳ Waiting for Lambda permission to propagate..."
sleep 30

# Create S3 notification configuration
aws s3api put-bucket-notification-configuration \
    --bucket $SOURCE_BUCKET \
    --notification-configuration "{
        \"LambdaFunctionConfigurations\": [{
            \"LambdaFunctionArn\": \"arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}\",
            \"Events\": [\"s3:ObjectCreated:*\"]
        }]
    }" \
    --region $REGION

echo "✅ S3 trigger configured"

# Create renditions bucket if it doesn't exist
echo ""
echo "📦 Checking renditions bucket..."
if ! aws s3api head-bucket --bucket $RENDITIONS_BUCKET 2>/dev/null; then
    echo "Creating renditions bucket..."
    aws s3api create-bucket --bucket $RENDITIONS_BUCKET --region $REGION
    
    # Configure bucket for public read (CDN access)
    aws s3api put-bucket-policy --bucket $RENDITIONS_BUCKET --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Sid\": \"PublicReadGetObject\",
            \"Effect\": \"Allow\",
            \"Principal\": \"*\",
            \"Action\": \"s3:GetObject\",
            \"Resource\": \"arn:aws:s3:::${RENDITIONS_BUCKET}/*\"
        }]
    }"
    
    echo "✅ Renditions bucket created"
else
    echo "✅ Renditions bucket exists"
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "📋 Function: $FUNCTION_NAME"
echo "📦 Source Bucket: $SOURCE_BUCKET"
echo "📦 Renditions Bucket: $RENDITIONS_BUCKET"
echo "🌐 CDN Domain: $CDN_DOMAIN"
echo ""
echo "Next steps:"
echo "1. Upload a test image to $SOURCE_BUCKET"
echo "2. Check CloudWatch Logs for processing status"
echo "3. Verify renditions in $RENDITIONS_BUCKET"
echo ""

