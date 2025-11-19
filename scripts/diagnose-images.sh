#!/bin/bash

# Image Not Found Diagnostic Script
# This script helps diagnose why images are not displaying

echo "🔍 GALERLY IMAGE DIAGNOSTIC"
echo "============================"
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    exit 1
fi

echo "✅ AWS CLI installed"
echo ""

# Get Lambda environment variables
echo "📋 Step 1: Checking Lambda environment variables..."
LAMBDA_FUNCTION=$(aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `galerly`)].FunctionName' --output text | head -1)

if [ -z "$LAMBDA_FUNCTION" ]; then
    echo "❌ No Lambda function found starting with 'galerly'"
    echo "   Please provide the Lambda function name manually."
    exit 1
fi

echo "   Lambda function: $LAMBDA_FUNCTION"

CDN_DOMAIN=$(aws lambda get-function-configuration \
    --function-name "$LAMBDA_FUNCTION" \
    --query 'Environment.Variables.CDN_DOMAIN' \
    --output text)

S3_PHOTOS_BUCKET=$(aws lambda get-function-configuration \
    --function-name "$LAMBDA_FUNCTION" \
    --query 'Environment.Variables.S3_BUCKET' \
    --output text)

if [ "$CDN_DOMAIN" == "None" ] || [ -z "$CDN_DOMAIN" ]; then
    echo "❌ CDN_DOMAIN not set in Lambda"
    echo "   This is why images are not loading!"
else
    echo "✅ CDN_DOMAIN: $CDN_DOMAIN"
fi

if [ "$S3_PHOTOS_BUCKET" == "None" ] || [ -z "$S3_PHOTOS_BUCKET" ]; then
    echo "⚠️  S3_BUCKET not found in Lambda environment"
else
    echo "✅ S3_PHOTOS_BUCKET: $S3_PHOTOS_BUCKET"
fi

echo ""

# Check S3 photos
echo "📋 Step 2: Checking S3 photos bucket..."
if [ -n "$S3_PHOTOS_BUCKET" ] && [ "$S3_PHOTOS_BUCKET" != "None" ]; then
    PHOTO_COUNT=$(aws s3 ls s3://$S3_PHOTOS_BUCKET --recursive | grep -E '\.(jpg|jpeg|png|JPG|JPEG|PNG)$' | wc -l | tr -d ' ')
    echo "   Photos in S3: $PHOTO_COUNT"
    
    if [ "$PHOTO_COUNT" -gt 0 ]; then
        echo ""
        echo "   📸 Sample photos (first 5):"
        aws s3 ls s3://$S3_PHOTOS_BUCKET --recursive | grep -E '\.(jpg|jpeg|png|JPG|JPEG|PNG)$' | head -5 | awk '{print "      " $4}'
    fi
else
    echo "⚠️  Cannot check S3 (bucket name not found)"
fi

echo ""

# Check CloudFront distribution
echo "📋 Step 3: Checking CloudFront distribution for images..."
CF_DIST_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='Galerly Image CDN'].Id" \
    --output text 2>/dev/null)

if [ -z "$CF_DIST_ID" ]; then
    echo "❌ No CloudFront distribution found with comment 'Galerly Image CDN'"
    echo "   Images cannot load without CloudFront!"
else
    echo "✅ CloudFront Distribution: $CF_DIST_ID"
    
    CF_STATUS=$(aws cloudfront get-distribution --id "$CF_DIST_ID" \
        --query 'Distribution.Status' \
        --output text)
    
    echo "   Status: $CF_STATUS"
    
    if [ "$CF_STATUS" != "Deployed" ]; then
        echo "   ⚠️  WARNING: Distribution not fully deployed yet!"
        echo "   Images will not work until status is 'Deployed'"
    fi
    
    CF_DOMAIN=$(aws cloudfront get-distribution --id "$CF_DIST_ID" \
        --query 'Distribution.DomainName' \
        --output text)
    
    echo "   Domain: $CF_DOMAIN"
fi

echo ""

# Check Lambda@Edge
echo "📋 Step 4: Checking Lambda@Edge function..."
EDGE_FUNCTION=$(aws lambda list-functions \
    --region us-east-1 \
    --query 'Functions[?FunctionName==`galerly-image-resize-edge`].FunctionName' \
    --output text)

if [ -z "$EDGE_FUNCTION" ]; then
    echo "❌ Lambda@Edge function 'galerly-image-resize-edge' not found"
    echo "   Image resizing will not work!"
else
    echo "✅ Lambda@Edge function exists"
    
    # Check if it's attached to CloudFront
    if [ -n "$CF_DIST_ID" ]; then
        ATTACHED=$(aws cloudfront get-distribution-config --id "$CF_DIST_ID" \
            --query 'DistributionConfig.DefaultCacheBehavior.LambdaFunctionAssociations.Items[*].LambdaFunctionARN' \
            --output text)
        
        if echo "$ATTACHED" | grep -q "galerly-image-resize-edge"; then
            echo "✅ Lambda@Edge attached to CloudFront"
        else
            echo "❌ Lambda@Edge NOT attached to CloudFront"
        fi
    fi
fi

echo ""
echo "============================"
echo "📊 DIAGNOSIS SUMMARY"
echo "============================"
echo ""

# Determine the issue
ISSUES=()

if [ "$CDN_DOMAIN" == "None" ] || [ -z "$CDN_DOMAIN" ]; then
    ISSUES+=("CDN_DOMAIN not set in Lambda environment")
fi

if [ -z "$CF_DIST_ID" ]; then
    ISSUES+=("CloudFront distribution for images not found")
fi

if [ -n "$CF_DIST_ID" ] && [ "$CF_STATUS" != "Deployed" ]; then
    ISSUES+=("CloudFront distribution not fully deployed yet")
fi

if [ -z "$EDGE_FUNCTION" ]; then
    ISSUES+=("Lambda@Edge function missing")
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo "✅ Infrastructure looks good!"
    echo ""
    echo "If images still don't load, check:"
    echo "1. Browser console for errors (F12 → Console)"
    echo "2. Network tab for failed requests (F12 → Network)"
    echo "3. Photo URLs in DynamoDB (should use cdn.galerly.com)"
else
    echo "❌ Found ${#ISSUES[@]} issue(s):"
    echo ""
    for issue in "${ISSUES[@]}"; do
        echo "   ❌ $issue"
    done
    echo ""
    echo "🔧 RECOMMENDED FIXES:"
    echo ""
    
    if [[ " ${ISSUES[@]} " =~ "CDN_DOMAIN not set" ]]; then
        echo "1. CDN_DOMAIN is missing from Lambda environment"
        echo "   Fix: Trigger a new deployment (git push)"
        echo "   The CI/CD pipeline will sync CDN_DOMAIN to Lambda"
        echo ""
    fi
    
    if [[ " ${ISSUES[@]} " =~ "CloudFront distribution" ]] || [[ " ${ISSUES[@]} " =~ "Lambda@Edge" ]]; then
        echo "2. CloudFront infrastructure is incomplete"
        echo "   Fix: Trigger a new deployment (git push)"
        echo "   The CI/CD pipeline will create missing resources"
        echo ""
    fi
    
    if [[ " ${ISSUES[@]} " =~ "not fully deployed" ]]; then
        echo "3. CloudFront is still deploying (15-20 minutes)"
        echo "   Fix: Wait for deployment to complete"
        echo "   Check status: aws cloudfront get-distribution --id $CF_DIST_ID"
        echo ""
    fi
fi

echo "============================"
echo ""
echo "Need help? Check the documentation:"
echo "  - CI_CD_INFRASTRUCTURE_AUTOMATION.md"
echo "  - CLOUDFRONT_IMAGE_OPTIMIZATION.md"
echo ""

