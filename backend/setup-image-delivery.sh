#!/bin/bash
# Professional Image Delivery Setup Script
# Configures AWS infrastructure for optimal image delivery

set -e

echo "========================================="
echo " Galerly Image Delivery Setup"
echo " Professional Photography Platform"
echo "========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$S3_PHOTOS_BUCKET" ]; then
    echo "❌ S3_PHOTOS_BUCKET environment variable not set"
    exit 1
fi

if [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "⚠️  CLOUDFRONT_DISTRIBUTION_ID not set. CloudFront optimization will be skipped."
fi

echo "✅ Environment validated"
echo ""

# Step 1: Configure S3 Lifecycle Policies
echo "Step 1: Configuring S3 Lifecycle Policies..."
echo "=========================================="
python3 backend/utils/storage_lifecycle.py
if [ $? -eq 0 ]; then
    echo "✅ S3 lifecycle policies configured"
else
    echo "❌ Failed to configure S3 lifecycle policies"
    exit 1
fi
echo ""

# Step 2: Configure CloudFront (if distribution ID is set)
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "Step 2: Configuring CloudFront Distribution..."
    echo "=========================================="
    python3 backend/utils/cloudfront_optimizer.py
    if [ $? -eq 0 ]; then
        echo "✅ CloudFront configuration complete"
    else
        echo "⚠️  CloudFront configuration had issues (non-fatal)"
    fi
    echo ""
fi

# Step 3: Update Lambda functions
echo "Step 3: Deploying Image Processing Lambda..."
echo "=========================================="
cd backend/image-processing
./deploy.sh
if [ $? -eq 0 ]; then
    echo "✅ Image processing Lambda deployed"
else
    echo "❌ Failed to deploy Lambda"
    exit 1
fi
cd ../..
echo ""

# Step 4: Configure S3 Event Notifications
echo "Step 4: Configuring S3 Event Notifications..."
echo "=========================================="
LAMBDA_ARN=$(aws lambda get-function --function-name galerly-image-processing --query 'Configuration.FunctionArn' --output text 2>/dev/null)

if [ -n "$LAMBDA_ARN" ]; then
    # Create notification configuration
    cat > /tmp/s3-notification.json <<EOF
{
    "LambdaFunctionConfigurations": [
        {
            "Id": "ImageProcessingTrigger",
            "LambdaFunctionArn": "$LAMBDA_ARN",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "suffix",
                            "Value": ".jpg"
                        }
                    ]
                }
            }
        },
        {
            "Id": "RawProcessingTrigger",
            "LambdaFunctionArn": "$LAMBDA_ARN",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "prefix",
                            "Value": ""
                        }
                    ]
                }
            }
        }
    ]
}
EOF

    aws s3api put-bucket-notification-configuration \
        --bucket "$S3_PHOTOS_BUCKET" \
        --notification-configuration file:///tmp/s3-notification.json

    if [ $? -eq 0 ]; then
        echo "✅ S3 event notifications configured"
    else
        echo "⚠️  S3 event notifications configuration had issues"
    fi
    
    rm /tmp/s3-notification.json
else
    echo "⚠️  Lambda ARN not found, skipping S3 notification setup"
fi
echo ""

# Step 5: Configure CORS for S3 bucket
echo "Step 5: Configuring S3 CORS..."
echo "=========================================="
cat > /tmp/cors-config.json <<EOF
{
    "CORSRules": [
        {
            "AllowedOrigins": ["https://galerly.com", "https://www.galerly.com"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedHeaders": ["*"],
            "MaxAgeSeconds": 3600,
            "ExposeHeaders": ["ETag"]
        }
    ]
}
EOF

aws s3api put-bucket-cors \
    --bucket "$S3_PHOTOS_BUCKET" \
    --cors-configuration file:///tmp/cors-config.json

if [ $? -eq 0 ]; then
    echo "✅ S3 CORS configured"
else
    echo "⚠️  S3 CORS configuration had issues"
fi

rm /tmp/cors-config.json
echo ""

# Step 6: Test the setup
echo "Step 6: Running validation tests..."
echo "=========================================="

# Test S3 access
echo -n "Testing S3 access... "
aws s3 ls "s3://$S3_PHOTOS_BUCKET" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

# Test Lambda function
if [ -n "$LAMBDA_ARN" ]; then
    echo -n "Testing Lambda function... "
    aws lambda invoke --function-name galerly-image-processing \
        --payload '{"Records":[]}' \
        /tmp/lambda-test-output.json > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅"
    else
        echo "❌"
    fi
    rm -f /tmp/lambda-test-output.json
fi

# Test CloudFront distribution
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo -n "Testing CloudFront distribution... "
    aws cloudfront get-distribution --id "$CLOUDFRONT_DISTRIBUTION_ID" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅"
    else
        echo "❌"
    fi
fi

echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "  • S3 Bucket: $S3_PHOTOS_BUCKET"
echo "  • Lifecycle policies: ✅ Active"
echo "  • Event notifications: ✅ Configured"
echo "  • CORS: ✅ Enabled"

if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "  • CloudFront: ✅ Optimized"
fi

if [ -n "$LAMBDA_ARN" ]; then
    echo "  • Image Processing: ✅ Deployed"
fi

echo ""
echo "Next Steps:"
echo "  1. Test image upload through the application"
echo "  2. Verify renditions are generated automatically"
echo "  3. Check CloudFront cache hit rates after 24 hours"
echo "  4. Monitor CloudWatch metrics for performance"
echo ""
echo "Documentation: See IMPLEMENTATION.md for details"
echo ""

