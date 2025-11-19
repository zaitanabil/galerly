# AWS Infrastructure Auto-Setup

## Overview

The CI/CD pipeline now automatically creates missing AWS resources before deployment. This enables a **fresh AWS start** anytime tables or buckets are deleted.

---

## What Gets Created Automatically

### 1. DynamoDB Tables (14 Tables)

All tables are created with:
- **Encryption at rest** (AWS KMS)
- **Pay-per-request billing** (cost-efficient)
- **Point-in-Time Recovery** (automatic backups)
- **Global Secondary Indexes** (for fast queries)

**Tables:**
```
galerly-users                    # Photographers/users
galerly-galleries                # Photo galleries
galerly-photos                   # Individual photos
galerly-sessions                 # Authentication sessions
galerly-newsletters              # Newsletter subscribers
galerly-contact                  # Support tickets
galerly-billing                  # Billing records
galerly-subscriptions            # Stripe subscriptions
galerly-analytics                # Usage analytics
galerly-client-favorites         # Client photo selections
galerly-client-feedback          # Client gallery feedback
galerly-visitor-tracking         # Website analytics
galerly-notification-preferences # Email preferences
```

### 2. S3 Buckets (2 Buckets)

**Frontend Bucket** (`galerly-frontend-app`):
- Static website hosting enabled
- Public read access for HTML/CSS/JS
- Cache control headers configured
- CloudFront distribution origin

**Photos Bucket** (`galerly-images-storage`):
- Private by default (photos are protected)
- CORS enabled for direct uploads from frontend
- Presigned URL access only
- Organized by gallery: `gallery-id/photo-id.jpg`

---

## CI/CD Pipeline Flow

### Before (Old Flow):
```
1. Validate secrets
2. Lint & validate code
3. ❌ Test AWS (FAILS if tables missing)
4. Test backend
5. Deploy
```

### After (New Flow):
```
1. Validate secrets
2. Lint & validate code
3. ✅ Setup AWS (creates missing resources)
4. ✅ Test AWS (passes)
5. Test backend
6. Deploy frontend
7. Deploy backend
```

---

## How It Works

### Step 1: Check & Create DynamoDB Tables

```bash
python backend/setup_dynamodb.py create
```

**What it does:**
- Checks if each table exists
- Creates missing tables with proper schema
- Sets up Global Secondary Indexes
- Enables encryption and backups
- Skips tables that already exist

**Output:**
```
🗄️  Creating DynamoDB tables for Galerly...

📝 Creating galerly-users...
  ✅ galerly-users created

  ℹ️  galerly-galleries already exists

⏳ Waiting for tables to become active...
  ✅ galerly-users is active

✅ All tables processed!
```

### Step 2: Check & Create S3 Buckets

**Frontend Bucket:**
```bash
# Check if exists
aws s3 ls s3://galerly-frontend-app

# Create if missing
aws s3 mb s3://galerly-frontend-app --region us-east-1

# Configure static website
aws s3 website s3://galerly-frontend-app \
  --index-document index.html \
  --error-document 404.html

# Set public read policy
aws s3api put-bucket-policy \
  --bucket galerly-frontend-app \
  --policy file://bucket-policy.json
```

**Photos Bucket:**
```bash
# Create if missing
aws s3 mb s3://galerly-images-storage --region us-east-1

# Block public access (photos are private)
aws s3api put-public-access-block \
  --bucket galerly-images-storage \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true"

# Configure CORS for uploads
aws s3api put-bucket-cors \
  --bucket galerly-images-storage \
  --cors-configuration file://photos-cors.json
```

---

## Manual Setup (Local Development)

### Create All Tables

```bash
cd backend
python setup_dynamodb.py create
```

### List All Tables

```bash
python setup_dynamodb.py list
```

**Output:**
```
📊 Current Galerly Tables:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 galerly-users
   Status: ACTIVE
   Items: 25
   Billing: PAY_PER_REQUEST
   Encryption: ✅
   Indexes: 1
      • UserIdIndex (ACTIVE)
```

### Optimize Tables (Enable Backups)

```bash
python setup_dynamodb.py optimize
```

### Delete All Tables (⚠️ Dangerous!)

```bash
python setup_dynamodb.py delete
# You must type: DELETE ALL TABLES
```

---

## Configuration

### Table Schemas

All table schemas are defined in `backend/setup_dynamodb.py`:

```python
TABLES = {
    'galerly-users': {
        'AttributeDefinitions': [
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ],
        'KeySchema': [
            {'AttributeName': 'email', 'KeyType': 'HASH'}
        ],
        'GlobalSecondaryIndexes': [...]
    },
    ...
}
```

### Bucket Policies

**Frontend (Public Read):**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::galerly-frontend-app/*"
  }]
}
```

**Photos (Private + CORS):**
```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://galerly.com"],
    "AllowedMethods": ["GET", "HEAD", "POST", "PUT"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}
```

---

## Cost Implications

### DynamoDB
- **Billing Mode:** PAY_PER_REQUEST
- **Cost:** $1.25 per million write requests, $0.25 per million read requests
- **Free Tier:** 25 GB storage, 2.5M reads/month, 1M writes/month
- **Typical Monthly Cost:** $1-5 (low usage) to $10-50 (high usage)

### S3
- **Frontend Bucket:** ~$0.01/month (static files, served via CloudFront)
- **Photos Bucket:** ~$0.023/GB/month storage + transfer costs
- **Free Tier:** 5 GB storage, 20,000 GET requests, 2,000 PUT requests
- **Typical Monthly Cost:** $0.50-5 (depends on photo count)

### Total Estimated Cost
- **Development:** < $1/month (free tier)
- **Production:** $5-20/month (100 users, 1000 photos)
- **Enterprise:** $50-200/month (1000+ users, 10,000+ photos)

---

## Troubleshooting

### Tables Not Creating

**Symptom:** `ClientError: User is not authorized to perform: dynamodb:CreateTable`

**Solution:** Ensure AWS credentials have DynamoDB permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:CreateTable",
      "dynamodb:DescribeTable",
      "dynamodb:UpdateTable",
      "dynamodb:DeleteTable",
      "dynamodb:UpdateContinuousBackups"
    ],
    "Resource": "*"
  }]
}
```

### S3 Buckets Already Exist

**Symptom:** `BucketAlreadyExists` error

**Solution:** S3 bucket names are globally unique. Either:
1. Update GitHub Secrets to use different bucket names
2. Delete existing buckets if you own them
3. Restore deleted buckets from AWS Recycle Bin

### Pipeline Fails on Setup

**Check logs:**
```bash
# View GitHub Actions logs
https://github.com/<your-username>/galerly/actions

# Or check locally
cd backend
python setup_dynamodb.py list
```

---

## Security

### Data Isolation
- Each user's galleries isolated via partition key (`user_id`)
- Photos linked to galleries, preventing cross-user access
- Sessions use unique tokens, no password storage

### Encryption
- **At Rest:** All tables encrypted with AWS KMS
- **In Transit:** HTTPS/TLS for all API calls
- **Backups:** Point-in-Time Recovery enabled

### Access Control
- **Lambda:** Only Lambda function can access DynamoDB
- **Frontend Bucket:** Public read for static assets only
- **Photos Bucket:** Private, presigned URLs for temporary access

---

## Next Steps

1. **Push to main** → Pipeline automatically sets up AWS
2. **Monitor logs** → Check GitHub Actions for setup status
3. **Verify tables** → Run `python setup_dynamodb.py list`
4. **Deploy app** → Frontend and backend deploy automatically

---

## References

- **DynamoDB Setup:** `backend/setup_dynamodb.py`
- **S3 Setup:** `.github/workflows/deploy.yml` (lines 212-280)
- **AWS Config:** `backend/setup_aws.py`
- **Table Schemas:** See `backend/setup_dynamodb.py` for full schemas

---

**Last Updated:** 2025-11-17  
**Status:** ✅ Active and tested in production

