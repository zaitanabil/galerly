#!/bin/bash
# Deploy Image Transformation Lambda
# This Lambda handles on-demand image resizing for all formats

set -e

echo "🚀 Deploying Image Transformation Lambda..."
echo ""

# Configuration
FUNCTION_NAME="galerly-image-transform"
REGION="us-east-1"

# Get AWS Account ID dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# IAM Role ARN (must exist - create manually or via CloudFormation)
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-image-transform-role"
echo "📋 IAM Role: $ROLE_ARN"
echo ""

# Check if IAM role exists
if ! aws iam get-role --role-name lambda-image-transform-role >/dev/null 2>&1; then
    echo "⚠️  IAM role 'lambda-image-transform-role' not found!"
    echo "   Creating IAM role with basic Lambda execution permissions..."
    echo ""
    
    # Create trust policy
    cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create role
    aws iam create-role \
        --role-name lambda-image-transform-role \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Execution role for Galerly image transformation Lambda"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name lambda-image-transform-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to propagate..."
    sleep 10
    
    echo "✅ IAM role created"
    echo ""
fi

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf package
mkdir -p package

# Copy Lambda function
cp lambda_function.py package/

# Create zip
cd package
zip -r ../image-transform-lambda.zip . -q
cd ..

echo ""
echo "✅ Deployment package created: image-transform-lambda.zip"
echo "📊 Package size: $(du -h image-transform-lambda.zip | cut -f1)"
echo ""

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://image-transform-lambda.zip \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://image-transform-lambda.zip \
        --timeout 60 \
        --memory-size 2048 \
        --region $REGION \
        --environment "Variables={SOURCE_BUCKET=galerly-uploads,CACHE_BUCKET=galerly-image-cache}"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Create/update Lambda Layer with image processing libraries (Pillow, rawpy, etc.)"
echo "   2. Attach layer to function: aws lambda update-function-configuration --function-name $FUNCTION_NAME --layers arn:aws:lambda:REGION:ACCOUNT:layer:image-processing:VERSION"
echo "   3. Configure API Gateway or Lambda@Edge to trigger this function"
echo "   4. Set up S3 cache bucket: galerly-image-cache"
echo ""

