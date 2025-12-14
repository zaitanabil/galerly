#!/bin/bash
# Automated IAM Setup for Galerly
# Creates users, groups, policies, and generates access keys

set -e

echo "=========================================="
echo "Galerly IAM Setup - Automated"
echo "=========================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not installed"
    echo "Install: brew install awscli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

echo "✓ AWS CLI configured"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ Account ID: $ACCOUNT_ID"
echo ""

# Store policy ARNs
declare -A POLICY_ARNS

# ============================================
# CREATE POLICIES
# ============================================

echo "Creating IAM policies..."

# Policy 1: CI/CD Deployment
echo "  Creating GalerlyCICDDeploymentPolicy..."
POLICY_ARNS[cicd]=$(aws iam create-policy \
    --policy-name GalerlyCICDDeploymentPolicy \
    --path /galerly/ \
    --description "CI/CD deployment permissions for GitHub Actions" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "LambdaDeployment",
                "Effect": "Allow",
                "Action": [
                    "lambda:GetFunction",
                    "lambda:UpdateFunctionCode",
                    "lambda:UpdateFunctionConfiguration",
                    "lambda:PublishVersion",
                    "lambda:CreateAlias",
                    "lambda:UpdateAlias",
                    "lambda:GetFunctionConfiguration"
                ],
                "Resource": "arn:aws:lambda:eu-central-1:*:function:galerly-*"
            },
            {
                "Sid": "S3FrontendDeployment",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:PutObjectAcl"
                ],
                "Resource": [
                    "arn:aws:s3:::galerly-frontend",
                    "arn:aws:s3:::galerly-frontend/*"
                ]
            },
            {
                "Sid": "CloudFrontInvalidation",
                "Effect": "Allow",
                "Action": [
                    "cloudfront:CreateInvalidation",
                    "cloudfront:GetInvalidation",
                    "cloudfront:ListInvalidations",
                    "cloudfront:GetDistribution"
                ],
                "Resource": "arn:aws:cloudfront::*:distribution/*"
            },
            {
                "Sid": "APIGatewayDeployment",
                "Effect": "Allow",
                "Action": [
                    "apigateway:GET",
                    "apigateway:POST",
                    "apigateway:PUT",
                    "apigateway:PATCH"
                ],
                "Resource": "arn:aws:apigateway:eu-central-1::/restapis/*"
            },
            {
                "Sid": "IAMPassRole",
                "Effect": "Allow",
                "Action": [
                    "iam:GetRole",
                    "iam:PassRole"
                ],
                "Resource": "arn:aws:iam::*:role/galerly-*"
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlyCICDDeploymentPolicy")

# Policy 2: DynamoDB Access
echo "  Creating GalerlyDynamoDBFullAccessPolicy..."
POLICY_ARNS[dynamodb]=$(aws iam create-policy \
    --policy-name GalerlyDynamoDBFullAccessPolicy \
    --path /galerly/ \
    --description "Full access to all Galerly DynamoDB tables" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DynamoDBTableAccess",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:BatchGetItem",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:DescribeTable",
                    "dynamodb:ConditionCheckItem"
                ],
                "Resource": "arn:aws:dynamodb:eu-central-1:*:table/galerly-*"
            },
            {
                "Sid": "DynamoDBIndexAccess",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": "arn:aws:dynamodb:eu-central-1:*:table/galerly-*/index/*"
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlyDynamoDBFullAccessPolicy")

# Policy 3: S3 Storage
echo "  Creating GalerlyS3StoragePolicy..."
POLICY_ARNS[s3]=$(aws iam create-policy \
    --policy-name GalerlyS3StoragePolicy \
    --path /galerly/ \
    --description "S3 storage permissions for photos and renditions" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "S3BucketAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:GetBucketVersioning"
                ],
                "Resource": [
                    "arn:aws:s3:::galerly-images-storage",
                    "arn:aws:s3:::galerly-renditions",
                    "arn:aws:s3:::galerly-frontend"
                ]
            },
            {
                "Sid": "S3ObjectAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:PutObjectAcl",
                    "s3:GetObjectAcl",
                    "s3:AbortMultipartUpload",
                    "s3:ListMultipartUploadParts"
                ],
                "Resource": [
                    "arn:aws:s3:::galerly-images-storage/*",
                    "arn:aws:s3:::galerly-renditions/*"
                ]
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlyS3StoragePolicy")

# Policy 4: SES Email
echo "  Creating GalerlySESEmailPolicy..."
POLICY_ARNS[ses]=$(aws iam create-policy \
    --policy-name GalerlySESEmailPolicy \
    --path /galerly/ \
    --description "SES email sending permissions" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "SESEmailSending",
                "Effect": "Allow",
                "Action": [
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                    "ses:SendTemplatedEmail"
                ],
                "Resource": "*"
            },
            {
                "Sid": "SESQuotaChecking",
                "Effect": "Allow",
                "Action": [
                    "ses:GetSendQuota",
                    "ses:GetSendStatistics"
                ],
                "Resource": "*"
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlySESEmailPolicy")

# Policy 5: CloudWatch Logs
echo "  Creating GalerlyCloudWatchLogsPolicy..."
POLICY_ARNS[logs]=$(aws iam create-policy \
    --policy-name GalerlyCloudWatchLogsPolicy \
    --path /galerly/ \
    --description "CloudWatch Logs write permissions" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudWatchLogsAccess",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                "Resource": [
                    "arn:aws:logs:eu-central-1:*:log-group:/aws/lambda/galerly-*",
                    "arn:aws:logs:eu-central-1:*:log-group:/aws/lambda/galerly-*:*"
                ]
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlyCloudWatchLogsPolicy")

# Policy 6: Admin
echo "  Creating GalerlyAdminPolicy..."
POLICY_ARNS[admin]=$(aws iam create-policy \
    --policy-name GalerlyAdminPolicy \
    --path /galerly/ \
    --description "Administrative permissions for manual operations" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "FullGalerlyAccess",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:*",
                    "s3:*",
                    "lambda:*",
                    "cloudfront:*",
                    "apigateway:*",
                    "ses:*",
                    "logs:*",
                    "cloudwatch:*",
                    "acm:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "IAMLimitedAccess",
                "Effect": "Allow",
                "Action": [
                    "iam:GetRole",
                    "iam:PassRole",
                    "iam:ListRoles"
                ],
                "Resource": "arn:aws:iam::*:role/galerly-*"
            }
        ]
    }' \
    --query 'Policy.Arn' --output text 2>/dev/null || echo "arn:aws:iam::${ACCOUNT_ID}:policy/galerly/GalerlyAdminPolicy")

echo "✓ Policies created"
echo ""

# ============================================
# CREATE GROUPS
# ============================================

echo "Creating IAM groups..."

aws iam create-group --group-name galerly-cicd-group --path /galerly/ 2>/dev/null || echo "  Group galerly-cicd-group already exists"
aws iam create-group --group-name galerly-app-runtime-group --path /galerly/ 2>/dev/null || echo "  Group galerly-app-runtime-group already exists"
aws iam create-group --group-name galerly-admin-group --path /galerly/ 2>/dev/null || echo "  Group galerly-admin-group already exists"

echo "✓ Groups created"
echo ""

# ============================================
# ATTACH POLICIES TO GROUPS
# ============================================

echo "Attaching policies to groups..."

# CI/CD group
aws iam attach-group-policy --group-name galerly-cicd-group --policy-arn "${POLICY_ARNS[cicd]}" 2>/dev/null || true

# Runtime group
aws iam attach-group-policy --group-name galerly-app-runtime-group --policy-arn "${POLICY_ARNS[dynamodb]}" 2>/dev/null || true
aws iam attach-group-policy --group-name galerly-app-runtime-group --policy-arn "${POLICY_ARNS[s3]}" 2>/dev/null || true
aws iam attach-group-policy --group-name galerly-app-runtime-group --policy-arn "${POLICY_ARNS[ses]}" 2>/dev/null || true
aws iam attach-group-policy --group-name galerly-app-runtime-group --policy-arn "${POLICY_ARNS[logs]}" 2>/dev/null || true

# Admin group
aws iam attach-group-policy --group-name galerly-admin-group --policy-arn "${POLICY_ARNS[admin]}" 2>/dev/null || true

echo "✓ Policies attached to groups"
echo ""

# ============================================
# CREATE USERS
# ============================================

echo "Creating IAM users..."

aws iam create-user --user-name galerly-cicd --path /galerly/ --tags Key=Application,Value=Galerly Key=Purpose,Value=CI/CD 2>/dev/null || echo "  User galerly-cicd already exists"
aws iam create-user --user-name galerly-app-runtime --path /galerly/ --tags Key=Application,Value=Galerly Key=Purpose,Value=Runtime 2>/dev/null || echo "  User galerly-app-runtime already exists"
aws iam create-user --user-name galerly-admin --path /galerly/ --tags Key=Application,Value=Galerly Key=Purpose,Value=Admin 2>/dev/null || echo "  User galerly-admin already exists"

echo "✓ Users created"
echo ""

# ============================================
# ADD USERS TO GROUPS
# ============================================

echo "Adding users to groups..."

aws iam add-user-to-group --user-name galerly-cicd --group-name galerly-cicd-group 2>/dev/null || true
aws iam add-user-to-group --user-name galerly-app-runtime --group-name galerly-app-runtime-group 2>/dev/null || true
aws iam add-user-to-group --user-name galerly-admin --group-name galerly-admin-group 2>/dev/null || true

echo "✓ Users added to groups"
echo ""

# ============================================
# GENERATE ACCESS KEYS
# ============================================

echo "=========================================="
echo "Generating Access Keys"
echo "=========================================="
echo ""

# Create output directory
mkdir -p .github/credentials

echo "1. galerly-cicd (GitHub Actions)"
echo "   Generating access key..."
CICD_KEY=$(aws iam create-access-key --user-name galerly-cicd --output json 2>/dev/null || echo "{}")

if [ "$CICD_KEY" != "{}" ]; then
    CICD_ACCESS_KEY=$(echo "$CICD_KEY" | grep -o '"AccessKeyId": "[^"]*"' | cut -d'"' -f4)
    CICD_SECRET_KEY=$(echo "$CICD_KEY" | grep -o '"SecretAccessKey": "[^"]*"' | cut -d'"' -f4)
    
    echo "   Access Key ID: $CICD_ACCESS_KEY"
    echo "   Secret Access Key: $CICD_SECRET_KEY"
    echo ""
    
    # Save to file
    cat > .github/credentials/galerly-cicd.txt <<EOF
# galerly-cicd credentials
# Use for GitHub Actions CI/CD

AWS_ACCESS_KEY_ID=$CICD_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$CICD_SECRET_KEY
AWS_REGION=eu-central-1

# Update GitHub Secrets:
gh secret set AWS_ACCESS_KEY_ID --body "$CICD_ACCESS_KEY" --repo zaitanabil/galerly
gh secret set AWS_SECRET_ACCESS_KEY --body "$CICD_SECRET_KEY" --repo zaitanabil/galerly
EOF
    echo "   ✓ Saved to .github/credentials/galerly-cicd.txt"
else
    echo "   ⚠ Access key already exists or creation failed"
    echo "   List existing keys: aws iam list-access-keys --user-name galerly-cicd"
fi
echo ""

echo "2. galerly-app-runtime (Lambda Execution)"
echo "   Generating access key..."
RUNTIME_KEY=$(aws iam create-access-key --user-name galerly-app-runtime --output json 2>/dev/null || echo "{}")

if [ "$RUNTIME_KEY" != "{}" ]; then
    RUNTIME_ACCESS_KEY=$(echo "$RUNTIME_KEY" | grep -o '"AccessKeyId": "[^"]*"' | cut -d'"' -f4)
    RUNTIME_SECRET_KEY=$(echo "$RUNTIME_KEY" | grep -o '"SecretAccessKey": "[^"]*"' | cut -d'"' -f4)
    
    echo "   Access Key ID: $RUNTIME_ACCESS_KEY"
    echo "   Secret Access Key: $RUNTIME_SECRET_KEY"
    echo ""
    
    # Save to file
    cat > .github/credentials/galerly-app-runtime.txt <<EOF
# galerly-app-runtime credentials
# Use for Lambda execution role

AWS_ACCESS_KEY_ID=$RUNTIME_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$RUNTIME_SECRET_KEY
AWS_REGION=eu-central-1

# Add to .env.production (DO NOT COMMIT):
AWS_ACCESS_KEY_ID=$RUNTIME_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$RUNTIME_SECRET_KEY
EOF
    echo "   ✓ Saved to .github/credentials/galerly-app-runtime.txt"
else
    echo "   ⚠ Access key already exists or creation failed"
fi
echo ""

echo "3. galerly-admin (Manual Operations)"
echo "   Generating access key..."
ADMIN_KEY=$(aws iam create-access-key --user-name galerly-admin --output json 2>/dev/null || echo "{}")

if [ "$ADMIN_KEY" != "{}" ]; then
    ADMIN_ACCESS_KEY=$(echo "$ADMIN_KEY" | grep -o '"AccessKeyId": "[^"]*"' | cut -d'"' -f4)
    ADMIN_SECRET_KEY=$(echo "$ADMIN_KEY" | grep -o '"SecretAccessKey": "[^"]*"' | cut -d'"' -f4)
    
    echo "   Access Key ID: $ADMIN_ACCESS_KEY"
    echo "   Secret Access Key: $ADMIN_SECRET_KEY"
    echo ""
    
    # Save to file
    cat > .github/credentials/galerly-admin.txt <<EOF
# galerly-admin credentials
# Use for administrative operations

AWS_ACCESS_KEY_ID=$ADMIN_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$ADMIN_SECRET_KEY
AWS_REGION=eu-central-1

# Configure AWS CLI profile:
aws configure set aws_access_key_id $ADMIN_ACCESS_KEY --profile galerly-admin
aws configure set aws_secret_access_key $ADMIN_SECRET_KEY --profile galerly-admin
aws configure set region eu-central-1 --profile galerly-admin

# Use profile:
aws s3 ls --profile galerly-admin
EOF
    echo "   ✓ Saved to .github/credentials/galerly-admin.txt"
else
    echo "   ⚠ Access key already exists or creation failed"
fi
echo ""

# ============================================
# SUMMARY
# ============================================

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Created:"
echo "  ✓ 3 IAM Users"
echo "  ✓ 3 IAM Groups"
echo "  ✓ 6 IAM Policies"
echo "  ✓ Access keys generated"
echo ""
echo "Users:"
echo "  • galerly-cicd → galerly-cicd-group"
echo "  • galerly-app-runtime → galerly-app-runtime-group"
echo "  • galerly-admin → galerly-admin-group"
echo ""
echo "Credentials saved to:"
echo "  • .github/credentials/galerly-cicd.txt"
echo "  • .github/credentials/galerly-app-runtime.txt"
echo "  • .github/credentials/galerly-admin.txt"
echo ""
echo "⚠ IMPORTANT: Keep credentials secure!"
echo "   Add .github/credentials/ to .gitignore"
echo ""
echo "Next steps:"
echo "  1. Update GitHub Secrets (commands in galerly-cicd.txt)"
echo "  2. Update .env.production with galerly-app-runtime credentials"
echo "  3. Run: .github/scripts/update-env.sh to sync to GitHub"
echo "  4. Test deployment"
echo ""
