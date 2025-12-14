#!/bin/bash
# Complete AWS Infrastructure Setup for Galerly
# Run this script BEFORE any GitHub Actions deployment

set -e

REGION="eu-central-1"
ACCOUNT_ID="278584440715"
PROJECT_NAME="galerly"

echo "=========================================="
echo "Galerly AWS Infrastructure Setup"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo "=========================================="
echo ""

# Check AWS credentials
echo "Step 1: Verifying AWS credentials..."
aws sts get-caller-identity || { echo "Error: AWS credentials not configured"; exit 1; }
echo "✓ AWS credentials verified"
echo ""

# S3 Buckets (already created)
echo "Step 2: Verifying S3 buckets..."
for bucket in "${PROJECT_NAME}-frontend" "${PROJECT_NAME}-images-storage" "${PROJECT_NAME}-renditions"; do
    if aws s3 ls "s3://$bucket" --region $REGION >/dev/null 2>&1; then
        echo "✓ Bucket exists: $bucket"
    else
        echo "Creating bucket: $bucket"
        aws s3 mb "s3://$bucket" --region $REGION
    fi
done
echo ""

# Configure S3 bucket for static website hosting
echo "Step 3: Configuring S3 static website hosting..."
aws s3 website "s3://${PROJECT_NAME}-frontend" \
    --index-document index.html \
    --error-document index.html \
    --region $REGION
echo "✓ S3 website hosting configured"
echo ""

# Create Lambda execution role (already done)
echo "Step 4: Verifying Lambda execution role..."
if aws iam get-role --role-name ${PROJECT_NAME}-lambda-execution-role >/dev/null 2>&1; then
    echo "✓ Lambda execution role exists"
else
    echo "Creating Lambda execution role..."
    aws iam create-role \
        --role-name ${PROJECT_NAME}-lambda-execution-role \
        --assume-role-policy-document '{
          "Version": "2012-10-17",
          "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
          }]
        }'
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name ${PROJECT_NAME}-lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy \
        --role-name ${PROJECT_NAME}-lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
    
    aws iam attach-role-policy \
        --role-name ${PROJECT_NAME}-lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    
    echo "✓ Lambda execution role created"
    echo "⏳ Waiting 10 seconds for IAM role propagation..."
    sleep 10
fi
echo ""

# Create initial Lambda function (if doesn't exist)
echo "Step 5: Setting up Lambda function..."
if aws lambda get-function --function-name ${PROJECT_NAME}-api --region $REGION >/dev/null 2>&1; then
    echo "✓ Lambda function exists: ${PROJECT_NAME}-api"
else
    echo "Creating initial Lambda function..."
    
    # Create minimal Lambda deployment package
    mkdir -p /tmp/${PROJECT_NAME}-lambda
    cat > /tmp/${PROJECT_NAME}-lambda/lambda_function.py <<'EOF'
def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': '{"status":"ok","message":"Lambda function initialized"}'
    }
EOF
    
    cd /tmp/${PROJECT_NAME}-lambda
    zip -q lambda.zip lambda_function.py
    
    aws lambda create-function \
        --function-name ${PROJECT_NAME}-api \
        --runtime python3.11 \
        --role arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-lambda-execution-role \
        --handler lambda_function.handler \
        --zip-file fileb://lambda.zip \
        --timeout 30 \
        --memory-size 512 \
        --region $REGION
    
    rm -rf /tmp/${PROJECT_NAME}-lambda
    echo "✓ Lambda function created"
fi

LAMBDA_ARN=$(aws lambda get-function --function-name ${PROJECT_NAME}-api --region $REGION --query 'Configuration.FunctionArn' --output text)
echo "Lambda ARN: $LAMBDA_ARN"
echo ""

# Create API Gateway
echo "Step 6: Setting up API Gateway..."
API_ID=$(aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='${PROJECT_NAME}-api'].ApiId" --output text)

if [ -z "$API_ID" ]; then
    echo "Creating HTTP API Gateway..."
    
    API_ID=$(aws apigatewayv2 create-api \
        --name ${PROJECT_NAME}-api \
        --protocol-type HTTP \
        --target $LAMBDA_ARN \
        --region $REGION \
        --query 'ApiId' \
        --output text)
    
    echo "✓ API Gateway created: $API_ID"
    
    # Grant API Gateway permission to invoke Lambda
    aws lambda add-permission \
        --function-name ${PROJECT_NAME}-api \
        --statement-id apigateway-invoke \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" \
        --region $REGION 2>/dev/null || echo "Lambda permission already exists"
    
    # Create default stage
    aws apigatewayv2 create-stage \
        --api-id $API_ID \
        --stage-name '$default' \
        --auto-deploy \
        --region $REGION >/dev/null 2>&1 || echo "Default stage already exists"
else
    echo "✓ API Gateway exists: $API_ID"
fi

API_ENDPOINT=$(aws apigatewayv2 get-api --api-id $API_ID --region $REGION --query 'ApiEndpoint' --output text)
echo "API Endpoint: $API_ENDPOINT"
echo ""

# Create CloudFront distribution
echo "Step 7: Setting up CloudFront distribution..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='${PROJECT_NAME}-frontend'].Id" --output text)

if [ -z "$DISTRIBUTION_ID" ]; then
    echo "Creating CloudFront distribution..."
    
    # Create CloudFront distribution config
    cat > /tmp/cloudfront-config.json <<EOF
{
  "CallerReference": "${PROJECT_NAME}-$(date +%s)",
  "Comment": "${PROJECT_NAME}-frontend",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "S3-${PROJECT_NAME}-frontend",
      "DomainName": "${PROJECT_NAME}-frontend.s3-website.${REGION}.amazonaws.com",
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${PROJECT_NAME}-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [{
      "ErrorCode": 404,
      "ResponsePagePath": "/index.html",
      "ResponseCode": "200",
      "ErrorCachingMinTTL": 300
    }]
  },
  "PriceClass": "PriceClass_100"
}
EOF
    
    DISTRIBUTION_ID=$(aws cloudfront create-distribution \
        --distribution-config file:///tmp/cloudfront-config.json \
        --query 'Distribution.Id' \
        --output text)
    
    rm /tmp/cloudfront-config.json
    
    echo "✓ CloudFront distribution created: $DISTRIBUTION_ID"
    echo "⏳ CloudFront distribution is deploying (this takes 15-20 minutes)..."
else
    echo "✓ CloudFront distribution exists: $DISTRIBUTION_ID"
fi

CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DomainName' --output text)
echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo ""

# Update GitHub variables
echo "Step 8: Updating GitHub Actions variables..."
gh variable set API_GATEWAY_ID --body "$API_ID" 2>/dev/null || echo "Using existing API_GATEWAY_ID"
gh variable set CLOUDFRONT_DISTRIBUTION_ID --body "$DISTRIBUTION_ID" 2>/dev/null || echo "Using existing CLOUDFRONT_DISTRIBUTION_ID"
gh variable set CDN_DOMAIN --body "$CLOUDFRONT_DOMAIN" 2>/dev/null || echo "Using existing CDN_DOMAIN"
gh variable set API_BASE_URL --body "$API_ENDPOINT" 2>/dev/null || echo "Using existing API_BASE_URL"
echo "✓ GitHub variables updated"
echo ""

# Summary
echo "=========================================="
echo "✅ AWS Infrastructure Setup Complete!"
echo "=========================================="
echo ""
echo "Resources Created:"
echo "  S3 Buckets:"
echo "    - ${PROJECT_NAME}-frontend"
echo "    - ${PROJECT_NAME}-images-storage"
echo "    - ${PROJECT_NAME}-renditions"
echo ""
echo "  Lambda Function:"
echo "    - Name: ${PROJECT_NAME}-api"
echo "    - ARN: $LAMBDA_ARN"
echo ""
echo "  API Gateway:"
echo "    - ID: $API_ID"
echo "    - Endpoint: $API_ENDPOINT"
echo ""
echo "  CloudFront:"
echo "    - Distribution ID: $DISTRIBUTION_ID"
echo "    - Domain: $CLOUDFRONT_DOMAIN"
echo ""
echo "  DynamoDB Tables: 36 tables (already created)"
echo ""
echo "Next Steps:"
echo "  1. Wait for CloudFront distribution to deploy (15-20 min)"
echo "  2. Run: gh workflow run ci-cd.yml"
echo "  3. Monitor: gh run watch"
echo ""
echo "Verify CloudFront status:"
echo "  aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.Status'"
echo ""
