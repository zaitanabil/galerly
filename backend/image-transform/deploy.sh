#!/bin/bash
# Deploy Image Transformation Lambda
# This Lambda handles on-demand image resizing for all formats

set -e

echo "🚀 Deploying Image Transformation Lambda..."
echo ""

# Configuration
FUNCTION_NAME="galerly-image-transform"
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-image-transform-role"

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

