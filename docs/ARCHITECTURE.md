# Architecture

## Stack

```
Browser → CloudFront → S3 (Frontend)
                     ↓
                API Gateway → Lambda (Python 3.11) → DynamoDB
                                                   → S3 (Images)
```

## Components

### Frontend
- **Host:** S3 static website
- **CDN:** CloudFront (optional)
- **Tech:** Vanilla JS, HTML, CSS
- **Bucket:** `galerly-frontend-app`

### Backend
- **Runtime:** AWS Lambda Python 3.11
- **Function:** `galerly-api`
- **Memory:** 512MB
- **Timeout:** 30s
- **Architecture:** Modular handlers

### Database
- **Service:** DynamoDB
- **Tables:** 6 (users, galleries, photos, sessions, cities, newsletters)
- **Billing:** Pay-per-request
- **Indexes:** 10 GSIs
- **Encryption:** KMS
- **Backup:** Point-in-Time Recovery

### Storage
- **Service:** S3
- **Bucket:** `galerly-images-storage`
- **Structure:** `{user_id}/{gallery_id}/{photo_id}.{ext}`
- **Access:** Pre-signed URLs (15min expiry)
- **CORS:** Enabled for downloads

### API Gateway
- **Type:** REST API
- **ID:** `ow085upbvb`
- **Region:** us-east-1
- **Stage:** prod
- **CORS:** Enabled
- **Throttle:** 10K req/sec

## Data Flow

### Photo Upload
```
1. Client → API Gateway → Lambda
2. Lambda → Generate pre-signed S3 URL
3. Lambda → Return URL to client
4. Client → Upload directly to S3 (bypasses Lambda)
5. Client → POST photo metadata to Lambda
6. Lambda → Save metadata to DynamoDB
```

### Authentication
```
1. POST /auth/login → Lambda
2. Lambda → Verify credentials (DynamoDB)
3. Lambda → Generate session token
4. Lambda → Store session (DynamoDB, 24h TTL)
5. Return token to client
6. Client → Store in localStorage
7. All requests → Authorization: Bearer {token}
```

### Gallery Access
```
Photographer:
- Query by user_id (partition key)
- Automatic data isolation

Client:
- Query by client_email (GSI)
- Or share_token (GSI)
- No user_id needed
```

## Security

### User Isolation
- Galleries: `user_id` partition key
- Photos: `user_id` field + ownership check
- Sessions: Token-based, user-specific

### Encryption
- At rest: KMS encryption (DynamoDB + S3)
- In transit: TLS 1.2+ (API Gateway)
- Passwords: bcrypt hash

### Access Control
- All endpoints: Session token validation
- Mutations: Ownership verification
- S3: Pre-signed URLs only

## Scalability

### Lambda
- Auto-scales: 0 → 1000 concurrent
- Cold start: ~500ms (with city cache)
- Warm latency: ~50-200ms

### DynamoDB
- Pay-per-request: Unlimited throughput
- Global tables: Not needed (single region)
- Indexes: Eventually consistent reads OK

### S3
- Unlimited storage
- Parallel uploads: No limit
- CloudFront: Optional CDN

## Monitoring

### CloudWatch Logs
```bash
/aws/lambda/galerly-api
```

### Metrics
- Lambda invocations
- API Gateway 4xx/5xx
- DynamoDB throttles
- S3 4xx/5xx

### Alarms
- Lambda errors > 5%
- API Gateway 5xx > 1%
- DynamoDB throttles > 0

## Cost Estimate

### Monthly (1K active users, 10K photos)
- Lambda: $5-10
- DynamoDB: $1-3
- S3 storage: $10-20 (1TB)
- S3 requests: $1-2
- API Gateway: $3-5
- **Total:** ~$20-40/month

### At Scale (100K users, 1M photos)
- Lambda: $200-300
- DynamoDB: $50-100
- S3 storage: $500-1000 (50TB)
- S3 requests: $50-100
- API Gateway: $100-200
- CloudFront: $100-200
- **Total:** ~$1000-1900/month

## Deployment

### Backend
```bash
cd backend
zip -r galerly-modular.zip api.py handlers/ utils/
aws lambda update-function-code \
  --function-name galerly-api \
  --zip-file fileb://galerly-modular.zip
```

### Frontend
```bash
aws s3 sync frontend/ s3://galerly-frontend-app/ --delete
```

### Infrastructure
```bash
cd backend
python setup_dynamodb.py create
python setup_aws.py all
```

## Regions

**Primary:** us-east-1

**Why:**
- Lowest Lambda pricing
- Most AWS services available
- Fastest new feature adoption
- No data sovereignty requirements

## Disaster Recovery

### Backups
- DynamoDB: Point-in-Time Recovery (35 days)
- S3: Versioning enabled
- Lambda: Code in Git + deployment package

### Recovery
```bash
# Restore DynamoDB to specific time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name galerly-photos \
  --target-table-name galerly-photos-restored \
  --restore-date-time 2025-01-01T00:00:00Z

# Restore S3 object version
aws s3api get-object \
  --bucket galerly-images-storage \
  --key photo.jpg \
  --version-id <version-id> \
  restored-photo.jpg
```

### RTO/RPO
- RTO (Recovery Time): ~1 hour
- RPO (Point Recovery): ~5 minutes (PITR)

