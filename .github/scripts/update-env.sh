#!/bin/bash
# Update GitHub Actions secrets and variables from .env.production

set -e

# Auto-detect repository
if [ -z "$GITHUB_REPOSITORY" ]; then
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
    if [ -z "$REPO" ]; then
        exit 1
    fi
    export GITHUB_REPOSITORY="$REPO"
fi

ENV_FILE=".env.production"

if [ ! -f "$ENV_FILE" ]; then
    exit 1
fi

if ! command -v gh &> /dev/null; then
    exit 1
fi

if ! gh auth status &> /dev/null; then
    exit 1
fi

# Generate configuration
python3 .github/scripts/generate-env-config.py

# Execute commands
bash .github/generated/gh-commands.sh
