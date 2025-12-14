# IAM Users and Policies for Galerly

## Overview

Three IAM users with specific roles and least-privilege access.

## IAM Users

### 1. **galerly-cicd**
**Purpose:** GitHub Actions CI/CD deployments

**Policy Group:** `galerly-cicd-group`

**Policies Attached:**
- `GalerlyCICDDeploymentPolicy` - Lambda deployment
- `GalerlyS3DeploymentPolicy` - Frontend deployment to S3
- `GalerlyCloudFrontInvalidationPolicy` - Cache invalidation

**Permissions:**
- Lambda: Update function code/config, publish versions
- S3: Upload frontend to `galerly-frontend` bucket
- CloudFront: Invalidate distribution cache
- API Gateway: Deploy API updates
- IAM: Pass role to Lambda

**Use:** Replace current AWS credentials in GitHub Actions secrets

---

### 2. **galerly-app-runtime**
**Purpose:** Application backend runtime operations

**Policy Group:** `galerly-app-runtime-group`

**Policies Attached:**
- `GalerlyDynamoDBFullAccessPolicy` - All 38 DynamoDB tables
- `GalerlyS3StoragePolicy` - Photo storage buckets
- `GalerlySESEmailPolicy` - Email sending
- `GalerlyCloudWatchLogsPolicy` - Application logging

**Permissions:**
- DynamoDB: Full CRUD on all `galerly-*` tables
- S3: Read/write `galerly-images-storage` and `galerly-renditions`
- SES: Send emails from `noreply@galerly.com` and `support@galerly.com`
- CloudWatch: Write Lambda logs

**Use:** Application Lambda function execution (attach to Lambda role)

---

### 3. **galerly-admin**
**Purpose:** Manual administrative operations

**Policy Group:** `galerly-admin-group`

**Policies Attached:**
- `GalerlyAdminPolicy` - Full access to Galerly resources

**Permissions:**
- Full access to DynamoDB, S3, Lambda, CloudFront, API Gateway
- Full access to SES, CloudWatch, ACM
- Limited IAM access (get/pass roles)

**Use:** Manual maintenance, debugging, emergency operations

---

## DynamoDB Tables (38 total)

All users/policies reference these tables:
```
galerly-users
galerly-galleries
galerly-photos
galerly-sessions
galerly-subscriptions
galerly-billing
galerly-refunds
galerly-analytics
galerly-audit-log
galerly-client-favorites
galerly-client-feedback
galerly-email-templates
galerly-features
galerly-user-features
galerly-invoices
galerly-appointments
galerly-contracts
galerly-raw-vault
galerly-seo-settings
galerly-cities
galerly-notification-preferences
galerly-newsletters
galerly-contact
galerly-video-analytics
galerly-visitor-tracking
galerly-background-jobs
galerly-leads
galerly-followup-sequences
galerly-testimonials
galerly-services
galerly-sales
galerly-packages
galerly-downloads
galerly-payment-reminders
galerly-onboarding-workflows
galerly-feature-requests
galerly-custom-domains
galerly-rate-limits
galerly-plan-violations
```

## S3 Buckets (3 total)

- `galerly-frontend` - Static website hosting
- `galerly-images-storage` - Original photo uploads
- `galerly-renditions` - Processed images/videos

## Setup Instructions

### Option 1: Terraform (Recommended)

```bash
# Navigate to project
cd /Users/nz-dev/Desktop/business/galerly.com/.github

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply configuration
terraform apply

# Get access keys (create separately via AWS Console or CLI)
```

### Option 2: AWS CLI

```bash
# Create users
aws iam create-user --user-name galerly-cicd --path /galerly/
aws iam create-user --user-name galerly-app-runtime --path /galerly/
aws iam create-user --user-name galerly-admin --path /galerly/

# Create groups
aws iam create-group --group-name galerly-cicd-group --path /galerly/
aws iam create-group --group-name galerly-app-runtime-group --path /galerly/
aws iam create-group --group-name galerly-admin-group --path /galerly/

# Add users to groups
aws iam add-user-to-group --user-name galerly-cicd --group-name galerly-cicd-group
aws iam add-user-to-group --user-name galerly-app-runtime --group-name galerly-app-runtime-group
aws iam add-user-to-group --user-name galerly-admin --group-name galerly-admin-group

# Create policies (use JSON from aws-iam-setup.json)
# Then attach to groups...
```

### Option 3: AWS Console

1. Go to IAM > Users > Create user
2. Create each user from list above
3. Create groups from list above
4. Create policies using Terraform file as reference
5. Attach policies to groups
6. Add users to groups

## Generate Access Keys

After creating users:

```bash
# CI/CD user
aws iam create-access-key --user-name galerly-cicd

# Runtime user
aws iam create-access-key --user-name galerly-app-runtime

# Admin user
aws iam create-access-key --user-name galerly-admin
```

**Update GitHub Secrets:**
```bash
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..." --repo zaitanabil/galerly
gh secret set AWS_SECRET_ACCESS_KEY --body "..." --repo zaitanabil/galerly
```

## Security Best Practices

1. **Rotate access keys** every 90 days
2. **Enable MFA** for admin user
3. **Use CloudTrail** to monitor IAM activity
4. **Least privilege** - users only have required permissions
5. **Never commit credentials** - use GitHub Secrets only

## Files Created

- `.github/aws-iam-setup.json` - JSON specification
- `.github/aws-iam-policies.tf` - Terraform configuration
- `.github/IAM_SETUP.md` - This documentation

## Summary Table

| User | Group | Primary Purpose | S3 | DynamoDB | Lambda | CloudFront | SES |
|------|-------|-----------------|-----|----------|--------|------------|-----|
| galerly-cicd | galerly-cicd-group | Deploy code | Frontend only | No | Update code | Invalidate | No |
| galerly-app-runtime | galerly-app-runtime-group | Run application | Photos/Renditions | Full access | No | No | Send emails |
| galerly-admin | galerly-admin-group | Manual ops | Full | Full | Full | Full | Full |

## Next Steps

1. **Create users** using Terraform or AWS CLI
2. **Generate access keys** for each user
3. **Update GitHub Actions** with `galerly-cicd` credentials
4. **Update Lambda role** to use `galerly-app-runtime` permissions
5. **Store admin keys** securely (1Password, AWS Secrets Manager)
6. **Test deployment** to verify permissions
