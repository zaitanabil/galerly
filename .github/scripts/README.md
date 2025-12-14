# GitHub Actions Environment Configuration

This directory contains automated tools for managing GitHub Actions secrets and variables from `.env.production`.

## Files

- `generate-env-config.py` - Python script that categorizes and generates GitHub CLI commands
- `sync-secrets.sh` - Bash script for automated secret/variable syncing
- `generated/gh-commands.sh` - Auto-generated GitHub CLI commands
- `generated/workflow-env.yml` - Auto-generated workflow environment section
- `generated/summary.txt` - Summary of secrets and variables

## Usage

### 1. Generate Configuration

```bash
python3 .github/scripts/generate-env-config.py
```

This reads `.env.production` and generates:
- GitHub CLI commands
- Workflow environment YAML
- Summary report

### 2. Push Secrets and Variables to GitHub

```bash
# Ensure GitHub CLI is authenticated
gh auth login

# Run generated commands
.github/generated/gh-commands.sh
```

Or use the workflow:

```bash
gh workflow run sync-env-secrets.yml
```

### 3. Update Workflows

Copy the environment section from `.github/generated/workflow-env.yml` into your workflow files.

## Categorization

**Secrets (7):**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- JWT_SECRET
- SMTP_PASSWORD
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- STRIPE_PUBLISHABLE_KEY

**Variables (118):**
All other environment variables (tables, buckets, URLs, IDs, etc.)

## Automation

Secrets sync workflow: `.github/workflows/sync-env-secrets.yml`

Trigger manually with:
```bash
gh workflow run sync-env-secrets.yml
```
