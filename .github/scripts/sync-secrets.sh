#!/bin/bash
# Automated GitHub Actions Secrets and Variables Sync
# Reads .env.production and syncs to GitHub repository

set -e

REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-nz-dev}"
REPO_NAME="${GITHUB_REPOSITORY_NAME:-galerly.com}"
ENV_FILE=".env.production"

if [ ! -f "$ENV_FILE" ]; then
    exit 1
fi

if ! command -v gh &> /dev/null; then
    exit 1
fi

# GitHub CLI must be authenticated
if ! gh auth status &> /dev/null; then
    exit 1
fi

# Read .env.production and extract key-value pairs
while IFS='=' read -r key value; do
    # Skip comments, empty lines, and section headers
    if [[ -z "$key" ]] || [[ "$key" =~ ^[[:space:]]*# ]] || [[ "$key" =~ ^[[:space:]]*$ ]]; then
        continue
    fi
    
    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Skip if key or value is empty
    if [[ -z "$key" ]] || [[ -z "$value" ]]; then
        continue
    fi
    
    # Determine if this should be a secret or variable based on sensitivity
    if [[ "$key" =~ (SECRET|KEY|PASSWORD|TOKEN|CREDENTIALS) ]]; then
        # Secrets: sensitive data
        gh secret set "$key" --body "$value" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
    else
        # Variables: non-sensitive configuration
        gh variable set "$key" --body "$value" --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null || true
    fi
done < "$ENV_FILE"
