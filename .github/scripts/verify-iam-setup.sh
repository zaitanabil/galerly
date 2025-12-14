#!/bin/bash
# Verify IAM setup is correct

set -e

echo "Verifying Galerly IAM Setup..."
echo ""

# Check users exist
echo "Checking IAM Users..."
for user in galerly-cicd galerly-app-runtime galerly-admin; do
    if aws iam get-user --user-name "$user" &>/dev/null; then
        echo "  ✓ $user"
    else
        echo "  ✗ $user (not found)"
    fi
done
echo ""

# Check groups exist
echo "Checking IAM Groups..."
for group in galerly-cicd-group galerly-app-runtime-group galerly-admin-group; do
    if aws iam get-group --group-name "$group" &>/dev/null; then
        echo "  ✓ $group"
    else
        echo "  ✗ $group (not found)"
    fi
done
echo ""

# Check policies exist
echo "Checking IAM Policies..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

policies=(
    "GalerlyCICDDeploymentPolicy"
    "GalerlyDynamoDBFullAccessPolicy"
    "GalerlyS3StoragePolicy"
    "GalerlySESEmailPolicy"
    "GalerlyCloudWatchLogsPolicy"
    "GalerlyAdminPolicy"
)

for policy in "${policies[@]}"; do
    policy_arn="arn:aws:iam::${ACCOUNT_ID}:policy/galerly/$policy"
    if aws iam get-policy --policy-arn "$policy_arn" &>/dev/null; then
        echo "  ✓ $policy"
    else
        echo "  ✗ $policy (not found)"
    fi
done
echo ""

# Check group memberships
echo "Checking Group Memberships..."
echo "  galerly-cicd-group:"
aws iam get-group --group-name galerly-cicd-group --query 'Users[*].UserName' --output text | sed 's/^/    /'
echo "  galerly-app-runtime-group:"
aws iam get-group --group-name galerly-app-runtime-group --query 'Users[*].UserName' --output text | sed 's/^/    /'
echo "  galerly-admin-group:"
aws iam get-group --group-name galerly-admin-group --query 'Users[*].UserName' --output text | sed 's/^/    /'
echo ""

# Check access keys
echo "Checking Access Keys..."
for user in galerly-cicd galerly-app-runtime galerly-admin; do
    key_count=$(aws iam list-access-keys --user-name "$user" --query 'length(AccessKeyMetadata)' --output text 2>/dev/null || echo "0")
    if [ "$key_count" -gt 0 ]; then
        echo "  ✓ $user ($key_count key(s))"
    else
        echo "  ⚠ $user (no access keys)"
    fi
done
echo ""

echo "Verification complete!"
