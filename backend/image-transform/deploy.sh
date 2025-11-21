#!/bin/bash
# Deploy Image Transformation Lambda
# This Lambda handles on-demand image resizing for all formats

set -e

echo "🚀 Deploying Image Transformation Lambda..."
echo ""

# Configuration
FUNCTION_NAME="galerly-image-transform"
REGION="us-east-1"

# Get AWS Account ID dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# IAM Role ARN (must exist - create manually or via CloudFormation)
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-image-transform-role"
echo "📋 IAM Role: $ROLE_ARN"
echo ""

# Check if IAM role exists
if ! aws iam get-role --role-name lambda-image-transform-role >/dev/null 2>&1; then
    echo "⚠️  IAM role 'lambda-image-transform-role' not found!"
    echo "   Creating IAM role with basic Lambda execution permissions..."
    echo ""
    
    # Create trust policy
    cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create role
    aws iam create-role \
        --role-name lambda-image-transform-role \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Execution role for Galerly image transformation Lambda"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name lambda-image-transform-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to propagate..."
    sleep 10
    
    echo "✅ IAM role created"
    echo ""
fi

# Build Lambda Layer with image processing libraries
LAYER_NAME="galerly-image-transform-layer"
echo "📚 Building Lambda Layer: $LAYER_NAME..."
echo ""

# Create layer package directory
rm -rf layer-package
mkdir -p layer-package/python

# Install image processing dependencies for Lambda runtime
# Use manylinux platform to ensure compatibility with Lambda execution environment
echo "   Installing Pillow, rawpy, pillow-heif, numpy..."
pip install \
    Pillow>=10.0.0 \
    rawpy>=0.18.0 \
    pillow-heif>=0.13.0 \
    numpy \
    -t layer-package/python/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --upgrade \
    --quiet

# Create layer zip
cd layer-package
zip -r ../image-transform-layer.zip . -q
cd ..

echo "✅ Layer package created"
echo "📊 Layer size: $(du -h image-transform-layer.zip | cut -f1)"
echo ""

# Publish or update layer
echo "📤 Publishing Lambda Layer..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --description "Image processing libraries: Pillow, rawpy, pillow-heif, numpy for galerly-image-transform" \
    --zip-file fileb://image-transform-layer.zip \
    --compatible-runtimes python3.11 python3.12 \
    --region $REGION \
    --query 'Version' \
    --output text)

LAYER_ARN="arn:aws:lambda:${REGION}:${AWS_ACCOUNT_ID}:layer:${LAYER_NAME}:${LAYER_VERSION}"
echo "✅ Layer published: $LAYER_ARN"
echo ""

# Create deployment package with Lambda function code only
echo "📦 Creating Lambda function package..."
rm -rf package
mkdir -p package

# Copy Lambda function
cp lambda_function.py package/

# Create zip
cd package
zip -r ../image-transform-lambda.zip . -q
cd ..

echo "✅ Function package created: image-transform-lambda.zip"
echo "📊 Package size: $(du -h image-transform-lambda.zip | cut -f1)"
echo ""

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://image-transform-lambda.zip \
        --region $REGION \
        --no-cli-pager
    
    # Wait for code update to complete
    printf "⏳ Waiting for code update to complete"
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
    
    # Attach layer to function
    echo "🔗 Attaching layer to function..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers "$LAYER_ARN" \
        --region $REGION \
        --no-cli-pager
    
    # Wait for configuration update
    printf "⏳ Waiting for layer attachment"
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
        --environment "Variables={SOURCE_BUCKET=galerly-uploads,CACHE_BUCKET=galerly-image-cache}" \
        --layers "$LAYER_ARN" \
        --no-cli-pager
    
    # Wait for function creation
    printf "⏳ Waiting for function to become active"
    MAX_WAIT=90
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        STATE=$(aws lambda get-function \
            --function-name $FUNCTION_NAME \
            --region $REGION \
            --query 'Configuration.State' \
            --output text 2>/dev/null)
        
        if [ "$STATE" = "Active" ]; then
            printf "\n"
            break
        fi
        
        printf "."
        sleep 2
        WAITED=$((WAITED + 2))
    done
fi

echo ""
echo "✅ Deployment complete!"
echo ""

# Verify layer attachment
ATTACHED_LAYERS=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Layers | length' \
    --output text)

if [ "$ATTACHED_LAYERS" -gt 0 ]; then
    echo "✅ Layer attached successfully!"
    echo "📚 Layers: $ATTACHED_LAYERS"
else
    echo "⚠️  Warning: No layers attached to function"
fi

echo ""
echo "📋 Function ARN: arn:aws:lambda:${REGION}:${AWS_ACCOUNT_ID}:function:${FUNCTION_NAME}"
echo "📚 Layer ARN: $LAYER_ARN"
echo ""

