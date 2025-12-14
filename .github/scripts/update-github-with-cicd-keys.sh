#!/bin/bash
# Quick command to update GitHub Actions with new CI/CD credentials

set -e

CREDS_FILE=".github/credentials/galerly-cicd.txt"

if [ ! -f "$CREDS_FILE" ]; then
    echo "ERROR: Credentials file not found"
    echo "Run: .github/scripts/create-iam-setup.sh first"
    exit 1
fi

# Extract credentials
ACCESS_KEY=$(grep "^AWS_ACCESS_KEY_ID=" "$CREDS_FILE" | cut -d'=' -f2)
SECRET_KEY=$(grep "^AWS_SECRET_ACCESS_KEY=" "$CREDS_FILE" | cut -d'=' -f2)

if [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
    echo "ERROR: Could not extract credentials from file"
    exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "zaitanabil/galerly")

echo "Updating GitHub Actions secrets for $REPO..."
echo ""

gh secret set AWS_ACCESS_KEY_ID --body "$ACCESS_KEY" --repo "$REPO"
echo "✓ AWS_ACCESS_KEY_ID updated"

gh secret set AWS_SECRET_ACCESS_KEY --body "$SECRET_KEY" --repo "$REPO"
echo "✓ AWS_SECRET_ACCESS_KEY updated"

echo ""
echo "✓ GitHub Actions secrets updated with galerly-cicd credentials"
echo ""
echo "Verify:"
echo "  gh secret list --repo $REPO | grep AWS"
