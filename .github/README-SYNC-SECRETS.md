# Syncing Environment Variables to GitHub

## Overview

The `sync-env-secrets.yml` workflow and `generate-env-config.py` script are designed to help you sync environment variables from `.env.production` to GitHub Actions secrets and variables.

## Important Notes

⚠️ **This process should be run LOCALLY, not in CI/CD**

The `.env.production` file contains sensitive credentials and is intentionally excluded from the repository via `.gitignore`.

## How to Sync Secrets

### Step 1: Generate Configuration

Run the Python script locally:

```bash
cd /Users/nz-dev/Desktop/business/galerly.com
python .github/scripts/generate-env-config.py
```

This will generate three files in `.github/generated/`:
- `gh-commands.sh` - Shell script with GitHub CLI commands
- `workflow-env.yml` - Example workflow env section
- `summary.txt` - Summary of what will be synced

### Step 2: Review Generated Commands

Check what will be synced:

```bash
cat .github/generated/summary.txt
```

Review the actual commands (sensitive values will be visible):

```bash
cat .github/generated/gh-commands.sh
```

### Step 3: Execute Sync

If everything looks correct, execute the sync:

```bash
bash .github/generated/gh-commands.sh
```

This will:
- Set all secrets using `gh secret set`
- Set all variables using `gh variable set`

## What Gets Synced

### Secrets (sensitive)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `JWT_SECRET`
- `SMTP_PASSWORD`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PUBLISHABLE_KEY`

### Variables (non-sensitive)
- All `DYNAMODB_TABLE_*` names
- All `S3_BUCKET_*` names
- Configuration values (URLs, ports, etc.)
- Feature flags
- Non-sensitive environment settings

## Current State

✅ **Secrets and variables are already configured** via the initial setup.

You only need to run this sync process if:
1. You've added new environment variables to `.env.production`
2. You've changed values that need to be updated in GitHub
3. You're setting up a new repository

## GitHub Workflow

The `sync-env-secrets.yml` workflow is kept in the repository for documentation, but it will exit gracefully when run in CI/CD (since `.env.production` is not available there).

## Security

- `.env.production` is in `.gitignore` and never committed
- The generated `gh-commands.sh` is also in `.gitignore`
- Secrets are only visible when you run the script locally
- GitHub CLI uses your authenticated session to set secrets
