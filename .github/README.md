# Galerly - GitHub Actions & AWS Setup

Complete automation for GitHub Actions, AWS IAM, and Infrastructure.

---

## Quick Start

### 1. AWS Setup (First Time)

```bash
# Configure AWS CLI with your credentials
aws configure

# Create IAM users and policies
bash .github/scripts/create-iam-setup.sh

# Verify setup
bash .github/scripts/verify-iam-setup.sh
```

### 2. Update GitHub Secrets

```bash
# Push IAM credentials to GitHub Actions
bash .github/scripts/update-github-with-cicd-keys.sh
```

### 3. Create AWS Resources

```bash
# S3 Buckets
aws s3 mb s3://galerly-frontend --region eu-central-1
aws s3 mb s3://galerly-images-storage --region eu-central-1
aws s3 mb s3://galerly-renditions --region eu-central-1

# DynamoDB Tables
cd user-app/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python setup_dynamodb.py create
```

### 4. Deploy

```bash
git push origin main
gh run watch
```

---

## Documentation

- **[IAM_SETUP.md](IAM_SETUP.md)** - Complete IAM configuration guide
- **[IAM_QUICKSTART.md](IAM_QUICKSTART.md)** - Quick IAM setup
- **[INFRASTRUCTURE_COMPLETE.md](INFRASTRUCTURE_COMPLETE.md)** - AWS resources status
- **[scripts/README.md](scripts/README.md)** - Scripts documentation

---

## AWS Configuration

**Account:** 278584440715  
**Region:** eu-central-1 (Frankfurt, Germany)  
**Environment Variables:** 125 (7 secrets + 118 variables)

### Resources Created

✅ **IAM Users:** 3 (galerly-cicd, galerly-app-runtime, galerly-admin)  
✅ **IAM Policies:** 6 (least-privilege access)  
✅ **S3 Buckets:** 3 (frontend, images, renditions)  
✅ **DynamoDB Tables:** 36 (all application tables)  
✅ **GitHub Actions:** Fully configured with CI/CD pipeline

---

## Directory Structure

```
.github/
├── scripts/              # Automation scripts
│   ├── create-iam-setup.sh
│   ├── update-github-with-cicd-keys.sh
│   ├── verify-iam-setup.sh
│   └── ...
├── workflows/            # GitHub Actions workflows
│   ├── ci-cd.yml
│   └── sync-env-secrets.yml
├── credentials/          # IAM access keys (gitignored)
├── generated/            # Auto-generated configs (some gitignored)
├── aws-iam-policies.tf   # Terraform IAM config
└── README.md            # This file
```

---

## Workflows

### CI/CD Pipeline (ci-cd.yml)
- Runs on: push to main, pull requests
- Jobs: test → build-frontend → build-docker → deploy
- Deploys to: eu-central-1
- Environment: All 125 variables configured

### Sync Environment (sync-env-secrets.yml)
- Manual trigger only
- Updates GitHub secrets/variables from .env.production

---

## Scripts

| Script | Purpose |
|--------|---------|
| `create-iam-setup.sh` | Create IAM users, groups, policies |
| `update-github-with-cicd-keys.sh` | Push CI/CD credentials to GitHub |
| `verify-iam-setup.sh` | Verify IAM configuration |
| `verify-github-env.sh` | Verify GitHub Actions config |
| `update-env.sh` | Sync .env.production to GitHub |
| `generate-env-config.py` | Generate environment config |
| `validate-env.sh` | Validate environment variables |
| `check-aws-ready.sh` | Check AWS CLI readiness |

---

## Maintenance

### Update Environment Variables

When `.env.production` changes:

```bash
bash .github/scripts/update-env.sh
```

### Rotate IAM Keys (Every 90 Days)

```bash
# Delete old keys
aws iam delete-access-key --user-name galerly-cicd --access-key-id AKIA...

# Re-run setup to create new keys
bash .github/scripts/create-iam-setup.sh

# Update GitHub
bash .github/scripts/update-github-with-cicd-keys.sh
```

### Monitor Deployments

```bash
gh run list --limit 10
gh run watch
gh run view [RUN_ID] --log-failed
```

---

## Security

✅ IAM least-privilege policies  
✅ Credentials gitignored  
✅ GitHub secrets encrypted  
✅ Point-in-Time Recovery on DynamoDB  
✅ eu-central-1 for GDPR compliance  

⚠️ **Remember:** Rotate access keys every 90 days

---

## Status

✅ GitHub Actions: Configured  
✅ IAM: Users and policies created  
✅ S3: Buckets created  
✅ DynamoDB: 36 tables created  
✅ Region: eu-central-1  
🟡 Lambda: Pending deployment  
🟡 API Gateway: Pending creation  
🟡 CloudFront: Pending creation  

---

## Support

- Check logs: `gh run view [RUN_ID] --log-failed`
- Verify AWS: `aws sts get-caller-identity`
- List resources: `aws s3 ls`, `aws dynamodb list-tables`
- Documentation: See individual .md files in this directory

---

**Region:** eu-central-1 (Frankfurt)  
**Account:** 278584440715  
**Setup:** Complete  
**Status:** Ready for deployment
