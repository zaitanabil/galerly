# 🚀 Quick Start: Automated Deployment

## ⚡ TL;DR

Your repository now auto-deploys to AWS on every push to `main`. Here's what you need to do:

### 1️⃣ Add GitHub Secrets (One-time setup)

Go to: **GitHub Repository → Settings → Secrets and variables → Actions**

Click **"New repository secret"** and add these **28 secrets**:

#### AWS (2 secrets)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### Frontend (3 secrets)
- `S3_BUCKET` (e.g., `galerly-frontend`)
- `CLOUDFRONT_DISTRIBUTION_ID` (e.g., `E1234567890ABC`)
- `FRONTEND_URL` (e.g., `https://galerly.com`)

#### Backend (1 secret)
- `LAMBDA_FUNCTION_NAME` (e.g., `galerly-api`)

#### DynamoDB (6 secrets)
- `DYNAMODB_TABLE_USERS`
- `DYNAMODB_TABLE_GALLERIES`
- `DYNAMODB_TABLE_PHOTOS`
- `DYNAMODB_TABLE_SESSIONS`
- `DYNAMODB_TABLE_SUBSCRIPTIONS`
- `DYNAMODB_TABLE_BILLING`

#### S3 Storage (1 secret)
- `S3_PHOTOS_BUCKET`

#### Stripe (4 secrets)
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PLUS`
- `STRIPE_PRICE_PRO`

#### Email (5 secrets)
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`

💡 **Helper script**: Run `./scripts/setup-github-secrets.sh` for a guided setup.

### 2️⃣ Deploy

```bash
git add .
git commit -m "your changes"
git push origin main
```

✨ **That's it!** GitHub Actions will automatically deploy everything.

### 3️⃣ Monitor

Watch deployment progress at:
```
https://github.com/YOUR_USERNAME/galerly/actions
```

---

## 🎯 What Happens Automatically

Every time you push to `main`:

✅ **Frontend** → Synced to S3, CloudFront updated & cache cleared  
✅ **Backend** → Lambda function updated with new code  
✅ **Clean deployment** → Old files removed, new files deployed  
✅ **3-5 minutes** → Fully automated, zero manual steps  

---

## 🆘 Need Help?

- **Detailed guide**: See `docs/DEPLOYMENT.md`
- **Implementation details**: See `docs/AUTOMATED_DEPLOYMENT_COMPLETE.md`
- **Setup helper**: Run `./scripts/setup-github-secrets.sh`

---

## 📊 Deployment Status

Check if everything is configured:
- [ ] All 28 GitHub Secrets added
- [ ] AWS IAM permissions granted
- [ ] CloudFront distribution ID verified
- [ ] Lambda function name correct
- [ ] S3 buckets exist

Once all checked, you're ready to deploy! 🚀

---

**Just push to main and watch the magic happen!** ✨

