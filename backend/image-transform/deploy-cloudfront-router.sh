#!/bin/bash
# Deploy CloudFront Router Lambda@Edge

set -e

echo "🚀 Deploying CloudFront Router (Lambda@Edge)..."
echo ""

FUNCTION_NAME="galerly-cloudfront-router"
REGION="us-east-1"  # Lambda@Edge must be in us-east-1

# Get AWS Account ID dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# IAM Role ARN
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-edge-role"
echo "📋 IAM Role: $ROLE_ARN"
echo ""

# Check if IAM role exists
if ! aws iam get-role --role-name lambda-edge-role >/dev/null 2>&1; then
    echo "⚠️  IAM role 'lambda-edge-role' not found!"
    echo "   Creating IAM role for Lambda@Edge..."
    echo ""
    
    # Create trust policy for Lambda@Edge
    cat > /tmp/edge-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "edgelambda.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create role
    aws iam create-role \
        --role-name lambda-edge-role \
        --assume-role-policy-document file:///tmp/edge-trust-policy.json \
        --description "Execution role for Galerly Lambda@Edge functions"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name lambda-edge-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to propagate..."
    sleep 10
    
    echo "✅ IAM role created"
    echo ""
fi

# Create deployment package
echo "📦 Creating Lambda@Edge package..."
rm -f cloudfront-router.zip
zip cloudfront-router.zip cloudfront-router.py

echo "📊 Package size: $(du -h cloudfront-router.zip | cut -f1)"
echo ""

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing Lambda@Edge function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://cloudfront-router.zip \
        --region $REGION
    
    # Wait for function update to complete
    # Function enters "Pending" during update and must return to "Active"
    printf "⏳ Waiting for function update to complete"
    MAX_WAIT=90
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        STATE=$(aws lambda get-function \
            --function-name $FUNCTION_NAME \
            --region $REGION \
            --query 'Configuration.State' \
            --output text)
        
        LAST_UPDATE_STATUS=$(aws lambda get-function \
            --function-name $FUNCTION_NAME \
            --region $REGION \
            --query 'Configuration.LastUpdateStatus' \
            --output text)
        
        if [ "$STATE" = "Active" ] && [ "$LAST_UPDATE_STATUS" = "Successful" ]; then
            printf "\n"
            break
        fi
        
        printf "."
        sleep 2
        WAITED=$((WAITED + 2))
    done
    
    if [ "$STATE" != "Active" ] || [ "$LAST_UPDATE_STATUS" != "Successful" ]; then
        printf "\n"
        echo "⚠️  Warning: Update did not complete within ${MAX_WAIT}s"
        echo "   State: $STATE, LastUpdateStatus: $LAST_UPDATE_STATUS"
        echo "   Attempting to publish version anyway..."
    fi
    
    # Publish new version
    VERSION=$(aws lambda publish-version \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'Version' \
        --output text)
    
    echo "✅ Published version: $VERSION"
else
    echo "🆕 Creating new Lambda@Edge function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler cloudfront-router.lambda_handler \
        --zip-file fileb://cloudfront-router.zip \
        --timeout 5 \
        --memory-size 128 \
        --region $REGION
    
    # Wait for function to become active
    # Lambda functions start in "Pending" state and must reach "Active" before publishing
    printf "⏳ Waiting for Lambda function to become active"
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        STATE=$(aws lambda get-function \
            --function-name $FUNCTION_NAME \
            --region $REGION \
            --query 'Configuration.State' \
            --output text)
        
        if [ "$STATE" = "Active" ]; then
            printf "\n"
            break
        fi
        
        printf "."
        sleep 2
        WAITED=$((WAITED + 2))
    done
    
    if [ "$STATE" != "Active" ]; then
        printf "\n"
        echo "⚠️  Warning: Function did not become active within ${MAX_WAIT}s (current state: $STATE)"
        echo "   Attempting to publish version anyway..."
    fi
    
    # Publish version
    VERSION=$(aws lambda publish-version \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'Version' \
        --output text)
    
    echo "✅ Published version: $VERSION"
fi

# Get function ARN
FUNCTION_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo ""
echo "✅ Lambda@Edge deployed!"
echo ""
echo "📋 Next steps:"
echo "   1. Update cloudfront-router.py with your transform Lambda ARN"
echo "   2. Associate with CloudFront distribution:"
echo "      - Event type: Origin Request"
echo "      - ARN: ${FUNCTION_ARN}:${VERSION}"
echo "   3. Test transformation requests"
echo ""

