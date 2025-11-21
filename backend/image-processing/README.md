# Image Processing Pipeline - Deployment Guide

## Overview

This is the **proper** image processing architecture following industry best practices (Instagram, Airbnb, Booking.com, Flickr).

### Key Principles
1. **Process ONCE during upload** (not on every view)
2. **Generate ALL renditions immediately**
3. **Store renditions in optimized structure**
4. **Serve pre-generated files** (instant loading, no delays)
5. **Simple CloudFront** (no Lambda@Edge complexity)

## Architecture

```
Upload Flow:
1. Client uploads original → S3 (galerly-images-storage)
2. S3 triggers Lambda (galerly-image-processing)
3. Lambda generates renditions:
   - thumbnail (400x400)
   - small (800x600)
   - medium (2000x2000)
   - large (4000x4000)
4. Lambda stores renditions → S3 (galerly-renditions)
5. Lambda updates DynamoDB with rendition URLs

View Flow:
1. Client requests gallery
2. Backend returns pre-generated rendition URLs
3. CloudFront serves renditions (instant, no processing)
4. Original file available for download
```

## Components

### 1. Processing Lambda (`galerly-image-processing`)
- **Trigger**: S3 ObjectCreated events on `galerly-images-storage`
- **Function**: Generate all renditions from original
- **Libraries**: Pillow, rawpy, pillow-heif (via Lambda Layer)
- **Timeout**: 300 seconds (5 minutes)
- **Memory**: 3008 MB (max for image processing)

### 2. S3 Buckets
- **galerly-images-storage**: Original files (RAW, HEIC, JPEG)
- **galerly-renditions**: Pre-generated renditions (JPEG only)

### 3. CloudFront Distribution
- **Simple static file serving** (no Lambda@Edge)
- **Origins**: Both S3 buckets
- **Caching**: Aggressive (renditions never change)
- **Domain**: cdn.galerly.com

### 4. DynamoDB Updates
- **Table**: galerly-photos
- **Fields**: thumbnail_url, small_url, medium_url, large_url, status, processed_at

## Deployment Steps

### Step 1: Deploy Processing Lambda

```bash
cd backend/image-processing
chmod +x deploy.sh
./deploy.sh
```

This will:
- Create IAM role with S3 and DynamoDB permissions
- Create Lambda Layer with image processing libraries
- Deploy Lambda function
- Configure S3 trigger
- Create renditions bucket

### Step 2: Configure CloudFront

```bash
# Update CloudFront distribution to add renditions bucket as origin
aws cloudfront get-distribution-config --id E3P0EU1X4VGR58 > /tmp/cf-config.json

# Edit config to add second origin:
# {
#   "Id": "renditions-bucket",
#   "DomainName": "galerly-renditions.s3.amazonaws.com",
#   "S3OriginConfig": {
#     "OriginAccessIdentity": ""
#   }
# }

# Add path pattern for renditions:
# {
#   "PathPattern": "renditions/*",
#   "TargetOriginId": "renditions-bucket",
#   "ViewerProtocolPolicy": "redirect-to-https",
#   "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"  # CachingOptimized
# }

# Update distribution
aws cloudfront update-distribution \
  --id E3P0EU1X4VGR58 \
  --distribution-config file:///tmp/cf-config-updated.json \
  --if-match <ETAG>
```

### Step 3: Remove Lambda@Edge (Old System)

```bash
# Remove Lambda@Edge from CloudFront
aws cloudfront get-distribution-config --id E3P0EU1X4VGR58 > /tmp/cf-config.json

# Edit config to remove LambdaFunctionAssociations
# Set: "LambdaFunctionAssociations": {"Quantity": 0, "Items": []}

# Update distribution
aws cloudfront update-distribution \
  --id E3P0EU1X4VGR58 \
  --distribution-config file:///tmp/cf-config-no-lambda.json \
  --if-match <ETAG>

# Delete old Lambda@Edge function (after CloudFront update)
aws lambda delete-function \
  --function-name galerly-cloudfront-router \
  --region us-east-1

# Delete old image-transform Lambda
aws lambda delete-function \
  --function-name galerly-image-transform \
  --region us-east-1

# Delete old cache bucket (optional)
aws s3 rm s3://galerly-image-cache --recursive
aws s3 rb s3://galerly-image-cache
```

### Step 4: Test End-to-End

```bash
# 1. Upload a test image
aws s3 cp test.HEIC s3://galerly-images-storage/test-gallery/test-photo.HEIC

# 2. Check Lambda logs
aws logs tail /aws/lambda/galerly-image-processing --follow

# 3. Verify renditions were created
aws s3 ls s3://galerly-renditions/renditions/test-gallery/

# Expected output:
# test-photo_thumbnail.jpg
# test-photo_small.jpg
# test-photo_medium.jpg
# test-photo_large.jpg

# 4. Test CloudFront delivery
curl -I https://cdn.galerly.com/renditions/test-gallery/test-photo_small.jpg

# Expected: HTTP 200, Content-Type: image/jpeg
```

## Database Schema Updates

The processing Lambda automatically updates DynamoDB with these fields:

```python
{
    'thumbnail_url': 'https://cdn.galerly.com/renditions/gallery/photo_thumbnail.jpg',
    'small_url': 'https://cdn.galerly.com/renditions/gallery/photo_small.jpg',
    'medium_url': 'https://cdn.galerly.com/renditions/gallery/photo_medium.jpg',
    'large_url': 'https://cdn.galerly.com/renditions/gallery/photo_large.jpg',
    'status': 'active',  # Changed from 'pending'
    'processed_at': '2025-11-21T15:30:00.000Z'
}
```

No manual database migration needed - records update as images are processed.

## Benefits of New System

### Performance
- ⚡ **Instant page loads**: No processing delay
- 🚀 **No cold starts**: No Lambda@Edge invocations
- 📦 **Simple CDN**: Just static file serving

### Reliability
- ✅ **No processing failures during view**: Already processed
- 🔄 **Retry logic**: S3 + Lambda handles retries automatically
- 📊 **Easy monitoring**: CloudWatch logs show all processing

### Cost
- 💰 **Process once, serve millions**: No repeated processing
- 📉 **No Lambda@Edge costs**: Simple CloudFront
- 💾 **Predictable storage**: Fixed rendition sizes

### Scalability
- 📈 **Handles traffic spikes**: Pre-generated files
- 🌍 **Global edge caching**: CloudFront serves instantly
- ⚙️ **Async processing**: Upload returns immediately

## Migration Strategy

### For Existing Photos

Run a one-time batch process to generate renditions for existing photos:

```python
# backend/scripts/migrate_existing_photos.py
import boto3

s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# List all existing photos
paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket='galerly-images-storage')

for page in pages:
    for obj in page.get('Contents', []):
        key = obj['Key']
        
        # Skip renditions
        if key.startswith('renditions/'):
            continue
        
        # Invoke processing Lambda
        lambda_client.invoke(
            FunctionName='galerly-image-processing',
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'Records': [{
                    's3': {
                        'bucket': {'name': 'galerly-images-storage'},
                        'object': {'key': key}
                    }
                }]
            })
        )
        
        print(f"Queued: {key}")
```

### Rollback Plan

If issues arise, the old system remains available:
1. Keep original files in `galerly-images-storage`
2. Re-enable Lambda@Edge if needed
3. Renditions are additive (don't break existing URLs)

## Monitoring

### CloudWatch Metrics
- Lambda invocations
- Lambda errors
- Lambda duration
- S3 PUT/GET requests

### CloudWatch Logs
```bash
# Monitor processing
aws logs tail /aws/lambda/galerly-image-processing --follow

# Check for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/galerly-image-processing \
  --filter-pattern "ERROR"
```

### Success Indicators
- ✅ Lambda duration < 60 seconds per image
- ✅ S3 renditions bucket growing
- ✅ DynamoDB status changing from 'pending' to 'active'
- ✅ CloudFront serving renditions with 200 status

## Troubleshooting

### Lambda Timeout
- Increase timeout (max 15 minutes)
- Increase memory (more memory = faster processing)
- Check for large RAW files

### S3 Permission Errors
- Verify IAM role has s3:GetObject on source bucket
- Verify IAM role has s3:PutObject on renditions bucket

### DynamoDB Update Failures
- Check IAM role has dynamodb:UpdateItem permission
- Verify table name matches

### CloudFront 403/404 Errors
- Verify renditions bucket policy allows public read
- Check CloudFront origin configuration
- Invalidate CloudFront cache

## Cost Estimates

### Processing (One-Time)
- Lambda executions: $0.20 per 1 million seconds
- Lambda requests: $0.20 per 1 million requests
- ~$0.10 per 1000 images processed

### Storage (Ongoing)
- S3 Standard: $0.023 per GB/month
- 4 renditions × 500KB average = 2MB per photo
- ~$0.05 per 1000 photos per month

### Delivery (Per View)
- CloudFront: $0.085 per GB (first 10 TB)
- 500KB per page view
- ~$0.04 per 1000 views

**Total**: ~$0.10 setup + $0.05/month + $0.04 per 1000 views

Compare to old system:
- Lambda@Edge: $0.60 per 1 million requests
- More expensive at scale due to repeated processing

## Next Steps

1. Deploy processing Lambda
2. Test with sample images
3. Configure CloudFront for renditions bucket
4. Update frontend to use new URL structure (optional - backward compatible)
5. Migrate existing photos (batch script)
6. Remove old Lambda@Edge system
7. Monitor and optimize

---

**Questions?** Check CloudWatch Logs or AWS Console for real-time status.

