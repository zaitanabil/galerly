# Region Migration to eu-central-1 - COMPLETE ✓

## Summary

All references to `us-east-1` have been updated to `eu-central-1` (Frankfurt, Germany) for optimal performance in Switzerland.

---

## Files Updated

### Environment Configuration
- ✓ `.env.production` - AWS_REGION=eu-central-1
- ✓ `.env.development` - AWS_REGION=eu-central-1

### IAM Configuration
- ✓ `.github/aws-iam-policies.tf` - Provider region + all ARNs
- ✓ `.github/scripts/create-iam-setup.sh` - All regions and ARNs
- ✓ `.github/credentials/*.txt` - AWS_REGION=eu-central-1

### Backend Python Files
- ✓ `user-app/backend/setup_monitoring.py`
- ✓ `user-app/backend/setup_client_selections_table.py`
- ✓ `user-app/backend/utils/acm_manager.py`
- ✓ `user-app/backend/utils/cloudfront_manager.py`
- ✓ `user-app/backend/utils/security_monitoring.py`
- ✓ `user-app/backend/setup_custom_domains_table.py`
- ✓ `user-app/backend/utils/env_validation.py`

### GitHub Actions
- ✓ GitHub variable `AWS_REGION` → eu-central-1
- ✓ All workflow files reference vars.AWS_REGION

---

## Important Exception

**ACM (Certificate Manager)** remains in `us-east-1`:
- CloudFront requires SSL certificates in us-east-1
- This is an AWS requirement, not changeable
- Only affects certificate management
- File: `user-app/backend/utils/acm_manager.py`

---

## Updated ARN Patterns

All AWS ARNs now use `eu-central-1`:

```
arn:aws:lambda:eu-central-1:*:function:galerly-*
arn:aws:dynamodb:eu-central-1:*:table/galerly-*
arn:aws:logs:eu-central-1:*:log-group:/aws/lambda/galerly-*
arn:aws:apigateway:eu-central-1::/restapis/*
```

---

## Default Fallbacks

All Python code with region defaults now use `eu-central-1`:

```python
# Before
os.environ.get('AWS_REGION', 'us-east-1')

# After  
os.environ.get('AWS_REGION', 'eu-central-1')
```

---

## Verification

```bash
# Check environment files
grep AWS_REGION .env.production .env.development

# Check Python defaults
grep -r "us-east-1" user-app/backend/ --include="*.py" | grep -v test | grep -v "# CloudFront"

# Check IAM configs
grep -r "us-east-1" .github/*.tf .github/scripts/*.sh

# GitHub variable
gh variable list --repo zaitanabil/galerly | grep AWS_REGION
```

---

## Next Steps

### 1. Create AWS Resources in eu-central-1

You'll need to create all AWS resources in the new region:

**S3 Buckets:**
```bash
aws s3 mb s3://galerly-frontend --region eu-central-1
aws s3 mb s3://galerly-images-storage --region eu-central-1
aws s3 mb s3://galerly-renditions --region eu-central-1
```

**DynamoDB Tables:**
```bash
cd user-app/backend
# Update setup scripts to use eu-central-1
python setup_dynamodb.py
```

**Lambda Functions:**
```bash
# Deploy via GitHub Actions
git push origin main
```

### 2. Update DNS/CloudFront

- CloudFront distributions can be global
- Point to new eu-central-1 resources
- Update API Gateway in eu-central-1

### 3. Test Deployment

```bash
# Commit changes
git add .
git commit -m "Migrate all services to eu-central-1 region"
git push origin main

# Watch deployment
gh run watch
```

---

## Benefits of eu-central-1

✓ **Latency:** ~10-20ms from Switzerland (vs ~120ms from us-east-1)
✓ **GDPR Compliance:** Data stays in EU
✓ **Cost:** Similar to us-east-1
✓ **Availability:** All services available (Lambda, DynamoDB, S3, SES)
✓ **Proximity:** Frankfurt is closest AWS region to Switzerland

---

## Important Notes

### Migration Required

Since you're changing regions, you need to:
1. Create all resources in eu-central-1
2. Migrate data if you had any in us-east-1
3. Update DNS/endpoints
4. Test thoroughly

### No Automatic Migration

AWS resources don't automatically migrate between regions. You must:
- Create new S3 buckets in eu-central-1
- Create new DynamoDB tables in eu-central-1
- Deploy Lambda functions to eu-central-1
- Set up new API Gateway in eu-central-1

### CloudFront Exception

- CloudFront is global (not region-specific)
- Can point to resources in any region
- SSL certificates MUST be in us-east-1 (AWS requirement)
- This is handled automatically in code

---

## Rollback

If you need to revert to us-east-1:

```bash
# Update environment files
sed -i '' 's/eu-central-1/us-east-1/g' .env.production .env.development

# Update GitHub
gh variable set AWS_REGION --body "us-east-1" --repo zaitanabil/galerly

# Regenerate config
python3 .github/scripts/generate-env-config.py
```

---

## Status: READY

✓ All code updated to eu-central-1
✓ Environment files updated
✓ IAM policies updated with correct ARNs
✓ GitHub Actions configured
✓ Default fallbacks updated

**Next:** Create AWS resources in eu-central-1 region
