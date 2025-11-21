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
    
    # Create inline policy for Lambda invocation
    # Lambda@Edge needs to invoke the image-transform Lambda
    cat > /tmp/lambda-invoke-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:galerly-image-transform"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name lambda-edge-role \
        --policy-name LambdaInvokePolicy \
        --policy-document file:///tmp/lambda-invoke-policy.json
    
    echo "✅ IAM policies attached (CloudWatch Logs + Lambda Invoke)"
    
    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to propagate..."
    sleep 10
    
    echo "✅ IAM role created"
    echo ""
else
    # Role exists - verify it has Lambda invoke permission
    echo "✅ IAM role exists"
    
    # Update inline policy to ensure correct permissions
    cat > /tmp/lambda-invoke-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:galerly-image-transform"
    }
  ]
}
EOF
    
    aws iam put-role-policy \
        --role-name lambda-edge-role \
        --policy-name LambdaInvokePolicy \
        --policy-document file:///tmp/lambda-invoke-policy.json \
        2>/dev/null || true
    
    echo "✅ Lambda invoke permission verified"
    echo ""
fi

# Create deployment package
echo "📦 Creating Lambda@Edge package..."

# Get the image transform Lambda ARN
TRANSFORM_LAMBDA_ARN="arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:galerly-image-transform"
echo "📋 Transform Lambda ARN: $TRANSFORM_LAMBDA_ARN"
echo ""

# Lambda@Edge does not support environment variables
# Inject ARN into source code at build time
echo "🔧 Injecting ARN into source code..."
cp cloudfront-router.py cloudfront-router-build.py
sed -i.bak "s|__TRANSFORM_LAMBDA_ARN_PLACEHOLDER__|${TRANSFORM_LAMBDA_ARN}|g" cloudfront-router-build.py
rm -f cloudfront-router-build.py.bak

# Create deployment package from modified source
rm -f cloudfront-router.zip
zip -q cloudfront-router.zip cloudfront-router-build.py

# Rename inside zip to expected filename
printf "@ cloudfront-router-build.py\n@=cloudfront-router.py\n" | zipnote -w cloudfront-router.zip

# Clean up build file
rm -f cloudfront-router-build.py

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
        echo "   Continuing anyway..."
    fi
    
    # Lambda@Edge cannot have environment variables
    # Remove any existing environment variables
    echo "🧹 Removing environment variables (Lambda@Edge requirement)..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "Variables={}" \
        --region $REGION \
        --no-cli-pager > /dev/null
    
    # Wait for environment removal to complete
    printf "⏳ Waiting for configuration update"
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
    
    # Publish new version
    # ARN is already injected into code during build
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
    # Lambda@Edge does not support environment variables
    # ARN is already injected into code during build
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
echo "✅ Lambda@Edge deployed successfully!"
echo ""
echo "📋 Function Details:"
echo "   Function ARN: ${FUNCTION_ARN}:${VERSION}"
echo "   Transform Lambda: $TRANSFORM_LAMBDA_ARN"
echo ""
echo "🔧 CloudFront Configuration:"
echo "   To enable image transformation, attach this Lambda@Edge to your CloudFront distribution:"
echo ""
echo "   1. Open CloudFront console"
echo "   2. Select distribution (cdn.galerly.com)"
echo "   3. Go to: Behaviors → Edit default behavior"
echo "   4. Scroll to: Function associations → Lambda@Edge"
echo "   5. Add association:"
echo "      Event Type: Origin Request"
echo "      ARN: ${FUNCTION_ARN}:${VERSION}"
echo "   6. Save and deploy (takes 5-10 minutes)"
echo ""
echo "   Or via AWS CLI:"
echo "   aws cloudfront get-distribution-config --id YOUR_DISTRIBUTION_ID > dist-config.json"
echo "   # Edit dist-config.json to add Lambda@Edge association"
echo "   aws cloudfront update-distribution --id YOUR_DISTRIBUTION_ID --if-match ETAG --distribution-config file://dist-config.json"
echo ""
echo "✅ After CloudFront deployment completes:"
echo "   - HEIC images will be converted to JPEG server-side"
echo "   - RAW images (DNG, CR2, NEF) will be converted to JPEG server-side"
echo "   - Image transformations (?format=jpeg&width=800) will work"
echo "   - Client-side HEIC conversion will no longer be needed"
echo ""

