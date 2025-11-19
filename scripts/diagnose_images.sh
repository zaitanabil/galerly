#!/bin/bash

echo "=========================================="
echo "🔍 GALERLY IMAGE DIAGNOSTICS"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    exit 1
fi

echo "1️⃣ Checking S3 Bucket..."
echo "=========================================="
BUCKET="galerly-images-storage"

# List images
IMAGE_COUNT=$(aws s3 ls s3://$BUCKET --recursive 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "⚠️  NO IMAGES FOUND in S3 bucket: $BUCKET"
    echo "   You need to upload images first!"
else
    echo "✅ Found $IMAGE_COUNT files in S3 bucket"
    echo ""
    echo "📋 Sample images:"
    aws s3 ls s3://$BUCKET --recursive --human-readable | head -5
fi

echo ""
echo "2️⃣ Checking CloudFront Distribution..."
echo "=========================================="

# Find CDN distribution
CDN_DIST_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='Galerly Image CDN'].Id" \
    --output text 2>/dev/null || echo "")

if [ -z "$CDN_DIST_ID" ]; then
    echo "❌ No CloudFront distribution found for 'Galerly Image CDN'"
else
    echo "✅ Found CloudFront distribution: $CDN_DIST_ID"
    
    # Get distribution status
    STATUS=$(aws cloudfront get-distribution \
        --id "$CDN_DIST_ID" \
        --query 'Distribution.Status' \
        --output text)
    echo "   Status: $STATUS"
    
    # Get CloudFront domain
    CF_DOMAIN=$(aws cloudfront get-distribution \
        --id "$CDN_DIST_ID" \
        --query 'Distribution.DomainName' \
        --output text)
    echo "   Domain: $CF_DOMAIN"
fi

echo ""
echo "3️⃣ Testing DNS Resolution..."
echo "=========================================="

if command -v dig &> /dev/null; then
    echo "🔍 Checking cdn.galerly.com DNS..."
    dig +short cdn.galerly.com
    echo ""
elif command -v nslookup &> /dev/null; then
    echo "🔍 Checking cdn.galerly.com DNS..."
    nslookup cdn.galerly.com
    echo ""
else
    echo "⚠️  dig/nslookup not available - skipping DNS check"
fi

echo "4️⃣ Testing Image Access..."
echo "=========================================="

if [ "$IMAGE_COUNT" -gt 0 ]; then
    # Get first image key
    FIRST_IMAGE=$(aws s3 ls s3://$BUCKET --recursive | head -1 | awk '{print $4}')
    
    if [ -n "$FIRST_IMAGE" ]; then
        echo "Testing image: $FIRST_IMAGE"
        echo ""
        
        # Test direct S3 access
        echo "📍 Testing direct S3 access..."
        S3_URL="https://$BUCKET.s3.amazonaws.com/$FIRST_IMAGE"
        S3_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$S3_URL")
        echo "   S3 URL: $S3_URL"
        echo "   Status: $S3_STATUS"
        
        # Test CloudFront access
        if [ -n "$CF_DOMAIN" ]; then
            echo ""
            echo "📍 Testing CloudFront access..."
            CF_URL="https://$CF_DOMAIN/$FIRST_IMAGE"
            CF_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CF_URL")
            echo "   CloudFront URL: $CF_URL"
            echo "   Status: $CF_STATUS"
        fi
        
        # Test CDN custom domain
        echo ""
        echo "📍 Testing CDN custom domain..."
        CDN_URL="https://cdn.galerly.com/$FIRST_IMAGE"
        CDN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CDN_URL")
        echo "   CDN URL: $CDN_URL"
        echo "   Status: $CDN_STATUS"
        
        echo ""
        if [ "$CDN_STATUS" = "200" ]; then
            echo "✅ Images are accessible via CDN!"
        elif [ "$CF_STATUS" = "200" ]; then
            echo "⚠️  CloudFront works but CDN domain (cdn.galerly.com) doesn't"
            echo "   → Check DNS: cdn.galerly.com should CNAME to $CF_DOMAIN"
        elif [ "$S3_STATUS" = "200" ]; then
            echo "⚠️  S3 works but CloudFront doesn't"
            echo "   → Check CloudFront configuration and OAI permissions"
        else
            echo "❌ Images not accessible"
            echo "   → Check S3 bucket policy and permissions"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "✅ DIAGNOSIS COMPLETE"
echo "=========================================="
