# GitHub Actions Environment Variables Configuration

## Summary

Total environment variables: **125**
- Secrets (sensitive): **7**
- Variables (non-sensitive): **118**

## Quick Start

### 1. Generate Configuration

```bash
python3 .github/scripts/generate-env-config.py
```

### 2. Push to GitHub

```bash
gh auth login
.github/generated/gh-commands.sh
```

### 3. Verify

```bash
gh secret list
gh variable list
```

## Secrets

| Variable | Type | Description |
|----------|------|-------------|
| AWS_ACCESS_KEY_ID | Secret | AWS access credentials |
| AWS_SECRET_ACCESS_KEY | Secret | AWS secret credentials |
| JWT_SECRET | Secret | JWT signing key |
| SMTP_PASSWORD | Secret | Email SMTP password |
| STRIPE_SECRET_KEY | Secret | Stripe API secret key |
| STRIPE_WEBHOOK_SECRET | Secret | Stripe webhook signing secret |
| STRIPE_PUBLISHABLE_KEY | Secret | Stripe API publishable key |

## Variables (Non-Sensitive)

All DynamoDB table names, S3 buckets, URLs, IDs, timeouts, and configuration values.

Full list: `.github/generated/summary.txt`

## Workflow Integration

Copy environment variables from `.github/generated/workflow-env.yml` into workflow files.

Example workflow: `.github/workflows/ci-cd.yml`

## Automation

- **Manual sync**: `.github/generated/gh-commands.sh`
- **Workflow sync**: `.github/workflows/sync-env-secrets.yml`
- **Validation**: `.github/scripts/validate-env.sh`

## Files Generated

- `.github/generated/gh-commands.sh` - GitHub CLI commands to push secrets/variables
- `.github/generated/workflow-env.yml` - Environment section for workflows
- `.github/generated/summary.txt` - Detailed categorization report

## Maintenance

Re-run `generate-env-config.py` whenever `.env.production` changes.
