#!/bin/bash
# Complete AWS cleanup and fresh setup script

set -e

echo "========================================="
echo " Complete AWS Reset & Fresh Setup"
echo "========================================="
echo ""

# Step 1: Clean up existing resources
echo "Step 1: Cleaning up existing AWS resources..."
echo "-----------------------------------------"
python3 cleanup-aws.py

echo ""
echo "Step 2: Waiting for CloudFront distributions..."
echo "-----------------------------------------"
echo "CloudFront distributions need to be fully disabled before deletion."
echo "This typically takes 15-20 minutes."
echo ""
read -p "Have CloudFront distributions finished disabling? (yes/no): " cloudfront_ready

if [ "$cloudfront_ready" = "yes" ]; then
    echo "Running cleanup again to remove CloudFront distributions..."
    python3 cleanup-aws.py
fi

echo ""
echo "Step 3: Creating fresh DynamoDB tables..."
echo "-----------------------------------------"
python3 setup_dynamodb.py create

echo ""
echo "Step 4: Configuring S3 buckets..."
echo "-----------------------------------------"
python3 setup_aws.py s3-cors

echo ""
echo "Step 5: Verifying setup..."
echo "-----------------------------------------"
python3 setup_aws.py verify

echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Deploy Lambda functions via GitHub Actions"
echo "  2. Configure API Gateway ID in .env"
echo "  3. Run: python3 setup_aws.py api-cors"
echo "  4. Configure CloudFront distribution"
echo ""

