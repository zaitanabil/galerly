#!/bin/bash
# Check if AWS CLI is configured and ready

echo "Checking AWS CLI Setup..."
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "✗ AWS CLI not installed"
    echo ""
    echo "Install with:"
    echo "  brew install awscli"
    echo ""
    echo "Or download from: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✓ AWS CLI installed ($(aws --version 2>&1 | head -1))"

# Check if credentials are configured
if [ ! -f ~/.aws/credentials ]; then
    echo "✗ AWS credentials not configured"
    echo ""
    echo "Run: aws configure"
    echo ""
    echo "If you don't have access keys yet:"
    echo "  1. Sign in to AWS Console: https://console.aws.amazon.com/"
    echo "  2. Create an admin IAM user"
    echo "  3. Generate access keys"
    echo "  4. Then run: aws configure"
    echo ""
    echo "Guide: .github/CREATE_INITIAL_ADMIN.md"
    exit 1
fi

echo "✓ Credentials file exists"

# Test credentials
echo ""
echo "Testing AWS credentials..."
if ! IDENTITY=$(aws sts get-caller-identity 2>&1); then
    echo "✗ AWS credentials are invalid or expired"
    echo ""
    echo "Error: $IDENTITY"
    echo ""
    echo "Fix with: aws configure"
    exit 1
fi

echo "✓ Credentials are valid"
echo ""

# Show identity
ACCOUNT=$(echo "$IDENTITY" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
USER_ARN=$(echo "$IDENTITY" | grep -o '"Arn": "[^"]*"' | cut -d'"' -f4)

echo "AWS Account: $ACCOUNT"
echo "User ARN: $USER_ARN"
echo ""

# Check if root user
if echo "$USER_ARN" | grep -q ":root"; then
    echo "⚠️  WARNING: You are using ROOT credentials"
    echo ""
    echo "For security, create an admin IAM user instead:"
    echo "  Guide: .github/CREATE_INITIAL_ADMIN.md"
    echo ""
    echo "Continue anyway? (not recommended)"
    read -p "Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Setup cancelled"
        exit 1
    fi
    echo ""
fi

# Check permissions
echo "Checking IAM permissions..."
if aws iam list-users --max-items 1 &> /dev/null; then
    echo "✓ IAM permissions confirmed"
else
    echo "✗ No IAM permissions"
    echo ""
    echo "Your user needs IAM admin permissions to create users/policies"
    echo ""
    echo "Options:"
    echo "  1. Use different credentials with IAM admin access"
    echo "  2. Have AWS admin grant you IAM permissions"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Ready to create Galerly IAM setup"
echo "=========================================="
echo ""
echo "Run: .github/scripts/create-iam-setup.sh"
