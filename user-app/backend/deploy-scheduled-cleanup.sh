#!/bin/bash
# Deploy scheduled account cleanup Lambda to AWS

set -e

ENVIRONMENT=${1:-production}
LAMBDA_FUNCTION_NAME="galerly-scheduled-account-cleanup-${ENVIRONMENT}"
S3_BUCKET="galerly-lambda-deployments-${ENVIRONMENT}"
CLOUDFORMATION_STACK="galerly-scheduled-cleanup-${ENVIRONMENT}"

echo "📦 Building Lambda deployment package..."

# Create temporary build directory
BUILD_DIR="build_scheduled_cleanup"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy Lambda function
cp scheduled_account_cleanup.py $BUILD_DIR/

# Copy dependencies
cp -r handlers $BUILD_DIR/
cp -r utils $BUILD_DIR/

# Install Python dependencies in build directory
pip install -r requirements.txt --target $BUILD_DIR/

# Package everything
cd $BUILD_DIR
zip -r ../scheduled-account-cleanup.zip . -x "*.pyc" -x "*__pycache__*"
cd ..

echo "✅ Package built: scheduled-account-cleanup.zip"

# Upload to S3
echo "☁️  Uploading to S3 bucket: ${S3_BUCKET}..."
aws s3 cp scheduled-account-cleanup.zip s3://${S3_BUCKET}/scheduled-account-cleanup.zip

echo "✅ Uploaded to S3"

# Deploy CloudFormation stack
echo "🚀 Deploying CloudFormation stack: ${CLOUDFORMATION_STACK}..."
aws cloudformation deploy \
  --template-file ../cloudformation/scheduled-account-cleanup.yaml \
  --stack-name ${CLOUDFORMATION_STACK} \
  --parameter-overrides Environment=${ENVIRONMENT} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ${AWS_REGION:-us-east-1}

echo "✅ CloudFormation stack deployed"

# Clean up
rm -rf $BUILD_DIR
rm scheduled-account-cleanup.zip

echo "🎉 Scheduled account cleanup Lambda deployed successfully!"
echo "📋 Function name: ${LAMBDA_FUNCTION_NAME}"
echo "📅 Schedule: Daily at 2 AM UTC"
echo ""
echo "To test manually:"
echo "  aws lambda invoke --function-name ${LAMBDA_FUNCTION_NAME} response.json"

