#!/bin/bash

# CloudFront + Lambda@Edge Setup Script
# Automates the entire deployment process

set -e  # Exit on error

echo "🚀 CloudFront Image Optimization Setup"
echo "======================================="
echo ""

# Configuration
BUCKET_NAME="galerly-images-storage"
FUNCTION_NAME="galerly-image-resize-edge"
CDN_DOMAIN="cdn.galerly.com"
REGION="us-east-1"  # Lambda@Edge MUST be in us-east-1

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Package Lambda@Edge Function${NC}"
echo "--------------------------------------"

# Create deployment package
cd "$(dirname "$0")/.."
mkdir -p lambda-edge-package
cd lambda-edge-package

# Copy function code from new location
cp ../lambda-edge/resize.js index.js

# Install dependencies (Sharp for image processing)
echo "Installing Sharp (image processing library)..."
npm init -y
npm install sharp --platform=linux --arch=x64

# Create ZIP package
zip -r ../lambda-edge-resize.zip .
cd ..
rm -rf lambda-edge-package

echo -e "${GREEN}✅ Lambda package created: lambda-edge-resize.zip${NC}"
echo ""

echo -e "${YELLOW}Step 2: Create Lambda@Edge Function${NC}"
echo "---------------------------------------"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null; then
    echo "Function already exists, updating code..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-edge-resize.zip \
        --region "$REGION" \
        --no-cli-pager
else
    echo "Creating new Lambda function..."
    
    # Create IAM role for Lambda@Edge
    ROLE_NAME="galerly-lambda-edge-role"
    
    # Check if role exists
    if ! aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
        echo "Creating IAM role..."
        
        cat > trust-policy.json <<EOF
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
        
        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        
        rm trust-policy.json
        
        echo "Waiting for IAM role to propagate..."
        sleep 10
    fi
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    
    # Create Lambda function
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime nodejs18.x \
        --role "$ROLE_ARN" \
        --handler index.handler \
        --zip-file fileb://lambda-edge-resize.zip \
        --timeout 30 \
        --memory-size 1024 \
        --region "$REGION" \
        --no-cli-pager
fi

echo -e "${GREEN}✅ Lambda@Edge function deployed${NC}"
echo ""

# Get Lambda function version ARN
echo "Publishing Lambda version..."
VERSION_ARN=$(aws lambda publish-version \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query 'FunctionArn' \
    --output text)

echo -e "${GREEN}✅ Lambda version published: $VERSION_ARN${NC}"
echo ""

echo -e "${YELLOW}Step 3: Create CloudFront Distribution${NC}"
echo "----------------------------------------"

# Check if distribution exists
DIST_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='Galerly Image CDN'].Id" \
    --output text 2>/dev/null || echo "")

if [ -z "$DIST_ID" ]; then
    echo "Creating CloudFront distribution..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Create Origin Access Identity (OAI)
    OAI_ID=$(aws cloudfront list-cloud-front-origin-access-identities \
        --query "CloudFrontOriginAccessIdentityList.Items[?Comment=='Galerly S3 Access'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$OAI_ID" ]; then
        echo "Creating Origin Access Identity..."
        OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
            --cloud-front-origin-access-identity-config \
            "CallerReference=$(date +%s),Comment='Galerly S3 Access'" \
            --query 'CloudFrontOriginAccessIdentity.Id' \
            --output text)
        
        echo -e "${GREEN}✅ OAI created: $OAI_ID${NC}"
        echo "⏳ Waiting for OAI to propagate globally (30 seconds)..."
        sleep 30
    fi
    
    # Create distribution config
    cat > cloudfront-config.json <<EOF
{
  "CallerReference": "$(date +%s)",
  "Comment": "Galerly Image CDN",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-$BUCKET_NAME",
        "DomainName": "$BUCKET_NAME.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-$BUCKET_NAME",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "LambdaFunctionAssociations": {
      "Quantity": 1,
      "Items": [
        {
          "LambdaFunctionARN": "$VERSION_ARN",
          "EventType": "origin-request",
          "IncludeBody": false
        }
      ]
    }
  }
}
EOF
    
    # Create distribution
    DIST_ID=$(aws cloudfront create-distribution \
        --distribution-config file://cloudfront-config.json \
        --query 'Distribution.Id' \
        --output text)
    
    rm cloudfront-config.json
    
    echo -e "${GREEN}✅ CloudFront distribution created: $DIST_ID${NC}"
    echo ""
    echo -e "${YELLOW}⏳ Distribution is deploying... This takes 15-20 minutes${NC}"
    echo ""
else
    echo -e "${GREEN}✅ CloudFront distribution already exists: $DIST_ID${NC}"
    echo ""
fi

# Get CloudFront domain
CF_DOMAIN=$(aws cloudfront get-distribution --id "$DIST_ID" \
    --query 'Distribution.DomainName' \
    --output text)

echo -e "${YELLOW}Step 4: Update S3 Bucket Policy${NC}"
echo "----------------------------------"

# Update S3 bucket policy to allow CloudFront OAI access
cat > s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAI",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity $OAI_ID"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy file://s3-policy.json

rm s3-policy.json

echo -e "${GREEN}✅ S3 bucket policy updated${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration Summary:${NC}"
echo "-------------------------"
echo "Lambda Function: $FUNCTION_NAME"
echo "Lambda ARN: $VERSION_ARN"
echo "CloudFront Distribution: $DIST_ID"
echo "CloudFront Domain: $CF_DOMAIN"
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "1. Add DNS record: $CDN_DOMAIN → $CF_DOMAIN (CNAME)"
echo "2. Request SSL certificate for $CDN_DOMAIN in ACM (us-east-1)"
echo "3. Update CloudFront distribution to use custom domain + SSL"
echo "4. Update environment variable: CDN_DOMAIN=$CDN_DOMAIN"
echo "5. Deploy backend changes (use cdn_urls.py helper)"
echo ""
echo -e "${YELLOW}🧪 Test URL:${NC}"
echo "Original: https://$CF_DOMAIN/[your-s3-key].jpg"
echo "Thumbnail: https://$CF_DOMAIN/resize/800x600/[your-s3-key].jpg"
echo ""
echo -e "${GREEN}Done!${NC}"

