# Automated IAM Setup for AWS

## Quick Start

### 1. Configure AWS CLI

```bash
aws configure
```

Enter your **current AWS credentials** (root or admin user):
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

**Verify configuration:**
```bash
aws sts get-caller-identity
```

Should show your Account ID and User ARN.

---

### 2. Run Automated Setup

```bash
cd /Users/nz-dev/Desktop/business/galerly.com
.github/scripts/create-iam-setup.sh
```

This script will:
1. ✓ Create 6 IAM policies
2. ✓ Create 3 IAM groups
3. ✓ Attach policies to groups
4. ✓ Create 3 IAM users
5. ✓ Add users to groups
6. ✓ Generate access keys
7. ✓ Save credentials to `.github/credentials/`

**Time:** ~30 seconds

---

### 3. Update GitHub Actions

```bash
.github/scripts/update-github-with-cicd-keys.sh
```

This will update GitHub secrets with the new `galerly-cicd` credentials.

---

### 4. Verify Setup

```bash
.github/scripts/verify-iam-setup.sh
```

---

## Manual Steps (if needed)

### Configure AWS CLI

```bash
# Check if configured
aws sts get-caller-identity

# If not configured:
aws configure

# Or use specific profile:
aws configure --profile galerly
```

### Run Individual Steps

```bash
# 1. Create IAM setup
.github/scripts/create-iam-setup.sh

# 2. Update GitHub secrets
.github/scripts/update-github-with-cicd-keys.sh

# 3. Verify everything
.github/scripts/verify-iam-setup.sh
```

---

## What Gets Created

### IAM Users (3)
1. **galerly-cicd** - GitHub Actions deployments
2. **galerly-app-runtime** - Application backend
3. **galerly-admin** - Manual administration

### IAM Groups (3)
1. **galerly-cicd-group**
2. **galerly-app-runtime-group**
3. **galerly-admin-group**

### IAM Policies (6)
1. **GalerlyCICDDeploymentPolicy** - Lambda, S3, CloudFront deployment
2. **GalerlyDynamoDBFullAccessPolicy** - All 38 DynamoDB tables
3. **GalerlyS3StoragePolicy** - Photo storage buckets
4. **GalerlySESEmailPolicy** - Email sending
5. **GalerlyCloudWatchLogsPolicy** - Application logging
6. **GalerlyAdminPolicy** - Full administrative access

---

## Credentials Files

After running `create-iam-setup.sh`, credentials are saved to:

```
.github/credentials/
├── galerly-cicd.txt          # GitHub Actions (use this!)
├── galerly-app-runtime.txt   # Lambda execution
└── galerly-admin.txt         # Manual operations
```

**⚠️ These files contain secrets - they are gitignored**

---

## Update GitHub Actions

### Automatic (Recommended)

```bash
.github/scripts/update-github-with-cicd-keys.sh
```

### Manual

```bash
# Get credentials
cat .github/credentials/galerly-cicd.txt

# Set GitHub secrets
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..." --repo zaitanabil/galerly
gh secret set AWS_SECRET_ACCESS_KEY --body "..." --repo zaitanabil/galerly
```

---

## Update .env.production

Replace the current AWS credentials with `galerly-app-runtime`:

```bash
# View runtime credentials
cat .github/credentials/galerly-app-runtime.txt

# Update .env.production manually
# Then sync to GitHub
.github/scripts/update-env.sh
```

---

## Troubleshooting

### "InvalidClientTokenId" Error

Your AWS CLI is not configured or has invalid credentials.

**Fix:**
```bash
aws configure
# Enter your admin AWS credentials
```

### "User already exists" Error

IAM resources already exist. The script will skip creation and continue.

### "EntityAlreadyExists" Error

Policy or group already exists. The script handles this gracefully.

### "Access key limit exceeded"

Each user can have maximum 2 access keys.

**Fix:**
```bash
# List existing keys
aws iam list-access-keys --user-name galerly-cicd

# Delete old key
aws iam delete-access-key --user-name galerly-cicd --access-key-id AKIA...

# Re-run setup script
```

---

## Security

1. **Never commit credentials** - `.github/credentials/` is gitignored
2. **Rotate keys every 90 days** - Set calendar reminder
3. **Use MFA for admin user** - Enable in AWS Console
4. **Monitor CloudTrail** - Track IAM activity
5. **Least privilege** - Users only have required permissions

---

## Next Steps

After setup:

1. ✓ Verify with `.github/scripts/verify-iam-setup.sh`
2. ✓ Update GitHub secrets (done by update script)
3. ✓ Update `.env.production` with runtime credentials
4. ✓ Test deployment: `git push origin main`
5. ✓ Monitor: `gh run watch`

---

## Files Created

```
.github/
├── scripts/
│   ├── create-iam-setup.sh              # Main setup script
│   ├── update-github-with-cicd-keys.sh  # Update GitHub secrets
│   └── verify-iam-setup.sh              # Verification script
├── credentials/
│   ├── .gitignore                       # Ignore credentials
│   ├── galerly-cicd.txt                 # CI/CD keys
│   ├── galerly-app-runtime.txt          # Runtime keys
│   └── galerly-admin.txt                # Admin keys
├── aws-iam-policies.tf                  # Terraform config
├── aws-iam-setup.json                   # JSON spec
├── IAM_SETUP.md                         # Documentation
└── IAM_QUICKSTART.md                    # This file
```

---

## Commands Reference

```bash
# Setup
.github/scripts/create-iam-setup.sh

# Update GitHub
.github/scripts/update-github-with-cicd-keys.sh

# Verify
.github/scripts/verify-iam-setup.sh

# View credentials
cat .github/credentials/galerly-cicd.txt

# Test AWS access
aws sts get-caller-identity

# List IAM users
aws iam list-users --path-prefix /galerly/

# List policies
aws iam list-policies --scope Local --path-prefix /galerly/
```
