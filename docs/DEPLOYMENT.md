# 🚀 Galerly Automated Deployment

This repository is configured with **GitHub Actions** for automatic deployment to AWS on every push to the `main` branch.

## 📋 Deployment Flow

When you push to `main`, GitHub Actions automatically:

### Frontend Deployment
1. ✅ **Syncs files to S3** - Uploads all frontend files with `--delete` flag (removes old files)
2. ✅ **Sets cache headers** - Long cache for assets, no cache for HTML
3. ✅ **Updates CloudFront Function** - Deploys URL rewrite function
4. ✅ **Invalidates CloudFront cache** - Forces fresh content delivery

### Backend Deployment
1. ✅ **Installs Python dependencies** - Packages all requirements
2. ✅ **Creates Lambda deployment zip** - Bundles code + dependencies
3. ✅ **Updates Lambda function** - Deploys new code
4. ✅ **Updates environment variables** - Syncs configuration
5. ✅ **Waits for deployment** - Ensures function is ready

---

## 🔐 Required GitHub Secrets

Go to **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

### AWS Credentials
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

### Frontend (S3 + CloudFront)
```
S3_BUCKET=galerly-frontend
CLOUDFRONT_DISTRIBUTION_ID=E...
FRONTEND_URL=https://galerly.com
```

### Backend (Lambda)
```
LAMBDA_FUNCTION_NAME=galerly-api
```

### DynamoDB Tables
```
DYNAMODB_TABLE_USERS=galerly-users
DYNAMODB_TABLE_GALLERIES=galerly-galleries
DYNAMODB_TABLE_PHOTOS=galerly-photos
DYNAMODB_TABLE_SESSIONS=galerly-sessions
DYNAMODB_TABLE_SUBSCRIPTIONS=galerly-subscriptions
DYNAMODB_TABLE_BILLING=galerly-billing
```

### S3 Photos Storage
```
S3_PHOTOS_BUCKET=galerly-photos
```

### Stripe
```
STRIPE_SECRET_KEY=sk_test_... or sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PLUS=price_...
STRIPE_PRICE_PRO=price_...
```

### Email (SMTP)
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@galerly.com
```

---

## 🛠️ How to Deploy

### Automatic Deployment (Recommended)
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

GitHub Actions will automatically deploy everything!

### Manual Deployment (Backup)
If you need to deploy manually:

#### Frontend Only
```bash
cd frontend
aws s3 sync . s3://galerly-frontend/ --delete
aws cloudfront create-invalidation --distribution-id E... --paths "/*"
```

#### Backend Only
```bash
cd backend
pip install -r requirements.txt -t package/
cp -r *.py handlers utils package/
cd package && zip -r ../lambda-deployment.zip . && cd ..
aws lambda update-function-code --function-name galerly-api --zip-file fileb://lambda-deployment.zip
```

---

## 📊 Monitoring Deployments

### View Deployment Status
1. Go to **GitHub Repository → Actions**
2. Click on the latest workflow run
3. View real-time logs for each step

### Troubleshooting Failed Deployments

If deployment fails:

1. **Check GitHub Actions logs** - Detailed error messages
2. **Verify AWS credentials** - Ensure secrets are correct
3. **Check AWS permissions** - IAM user needs:
   - S3: `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`
   - CloudFront: `cloudfront:CreateInvalidation`, `cloudfront:UpdateFunction`
   - Lambda: `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`
   - DynamoDB: Read/write permissions

4. **Manual rollback** if needed:
```bash
git revert HEAD
git push origin main
```

---

## 🔒 Security Best Practices

✅ **Never commit secrets** to the repository  
✅ **Use GitHub Secrets** for all sensitive data  
✅ **Rotate AWS credentials** periodically  
✅ **Use least privilege** IAM policies  
✅ **Enable CloudTrail** for audit logging  

---

## 📝 Deployment Checklist

Before pushing to production:

- [ ] All tests pass locally
- [ ] Environment variables are up to date in GitHub Secrets
- [ ] CloudFront distribution ID is correct
- [ ] Lambda function name matches
- [ ] S3 bucket names are correct
- [ ] Stripe keys are for the correct environment (test vs live)
- [ ] SMTP credentials are valid

---

## 🎯 Next Steps

After setting up automated deployment:

1. **Test the workflow** - Push a small change and verify it deploys
2. **Monitor CloudWatch** - Check Lambda logs for errors
3. **Set up alerts** - Configure SNS notifications for deployment failures
4. **Add staging environment** - Create a separate workflow for staging branch

---

## 🆘 Support

If you encounter issues:

1. Check GitHub Actions logs
2. Review AWS CloudWatch logs
3. Verify all secrets are set correctly
4. Ensure AWS IAM permissions are sufficient

---

## 📅 Deployment History

GitHub Actions automatically tracks:
- ✅ Who deployed
- ✅ What was deployed
- ✅ When it was deployed
- ✅ Deployment status (success/failure)

View history at: **Repository → Actions → Deploy Galerly to AWS**

---

**Last Updated**: November 2025  
**Maintained by**: Galerly Team
