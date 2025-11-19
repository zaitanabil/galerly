# Infrastructure Automation

## Overview

GitHub Actions automatically checks and creates all AWS infrastructure before each deployment.

## DynamoDB Tables (7)

1. `galerly-users` - User accounts
2. `galerly-galleries` - Photo galleries
3. `galerly-photos` - Individual photos
4. `galerly-sessions` - User sessions
5. `galerly-cities` - City search data
6. `galerly-newsletters` - Newsletter subscribers
7. `galerly-contact` - Support tickets

## Indexes (12)

- `galerly-users`: UserIdIndex
- `galerly-galleries`: ClientEmailIndex, ShareTokenIndex, GalleryIdIndex
- `galerly-photos`: GalleryIdIndex, UserIdIndex
- `galerly-sessions`: UserIdIndex
- `galerly-cities`: country-population-index
- `galerly-newsletters`: SubscribedAtIndex
- `galerly-contact`: CreatedAtIndex, StatusIndex

See: `DATABASE_INDEXES.md` for details

## AWS Configuration

- S3 CORS (galerly-images-storage)
- API Gateway CORS

## Automation Process

### First Deployment

```
1. Check tables exist → MISSING
2. Create 7 tables (~2-3 min)
3. Create 12 indexes (~1-2 min)
4. Configure S3 CORS (~10 sec)
5. Verify infrastructure (~5 sec)
6. Deploy backend (~60 sec)
7. Deploy frontend (~30 sec)

Total: ~5-7 minutes
```

### Subsequent Deployments

```
1. Check tables exist → ALL_EXIST (~5 sec)
2. Skip table creation
3. Verify indexes exist (~5 sec)
4. Skip AWS config (already set)
5. Deploy backend (~60 sec)
6. Deploy frontend (~30 sec)

Total: ~2-3 minutes
```

## Workflow Steps

GitHub Actions (`.github/workflows/deploy.yml`):

```yaml
# 1. Check if tables exist
python3 -c "check all 7 tables"

# 2. Create if missing
if missing:
  python3 setup_dynamodb.py create

# 3. Verify indexes
python3 manage_indexes.py --create

# 4. Check S3 CORS
aws s3api get-bucket-cors || python3 setup_aws.py s3-cors

# 5. Verify ready
python3 setup_dynamodb.py list
```

## Features

✅ **Fully Autonomous** - No manual setup  
✅ **Idempotent** - Safe to run multiple times  
✅ **Self-Healing** - Creates missing resources  
✅ **Smart** - Only creates what's missing  
✅ **Fast** - ~17 sec overhead after first setup  

## Manual Setup (Optional)

If you want to set up before first push:

```bash
cd backend

# Create tables
python3 setup_dynamodb.py create

# Import cities (optional)
python3 import_cities_to_dynamodb.py

# Configure AWS
python3 setup_aws.py all

# Verify
python3 setup_dynamodb.py list
```

## Troubleshooting

### Tables Failed to Create

```bash
# Check error in Actions logs
# Verify IAM permissions
# Push again (idempotent)
```

### Indexes Failed

```bash
# Often timing (tables still creating)
# Push again or run manually:
cd backend && python3 manage_indexes.py --create
```

### AWS Config Failed

```bash
# Check S3 bucket exists
# Verify IAM permissions
# Fix manually:
cd backend && python3 setup_aws.py s3-cors
```

## Monitoring

### Check Tables

```bash
# List all tables
aws dynamodb list-tables --region us-east-1

# Check specific table
aws dynamodb describe-table --table-name galerly-users

# Check indexes
aws dynamodb describe-table --table-name galerly-photos \
  --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]'
```

### Check S3 CORS

```bash
aws s3api get-bucket-cors --bucket galerly-images-storage
```

## Cost

Infrastructure setup is one-time:

- DynamoDB: Pay-per-request (no upfront cost)
- Indexes: No extra cost with pay-per-request
- S3 CORS: Free (configuration only)

**Estimated:** $20-40/month for typical usage

## Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:*",
      "lambda:*",
      "s3:*"
    ],
    "Resource": "*"
  }]
}
```

Or use managed policies:
- `AWSLambda_FullAccess`
- `AmazonDynamoDBFullAccess`
- `AmazonS3FullAccess`

