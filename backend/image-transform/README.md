# Galerly Image Transformation System

## 📸 Overview

Instagram-style image transformation system with on-demand processing and intelligent caching.

**Key Benefits:**
- ✅ **No duplicate storage** - store only originals
- ✅ **Supports ALL formats** - RAW (DNG, CR2, NEF), HEIC, TIFF, JPEG, PNG
- ✅ **Fast delivery** - CloudFront edge caching
- ✅ **Cost efficient** - only pay for transformations once
- ✅ **Scalable** - handles any image size or format

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ Request: cdn.galerly.com/photo.dng?format=jpeg&width=800
       ↓
┌─────────────────┐
│   CloudFront    │ ← Global CDN with edge caching
└────────┬────────┘
         │ (Cache miss)
         ↓
┌──────────────────┐
│ Lambda@Edge      │ ← Routes transformation requests
│ (Origin Request) │
└────────┬─────────┘
         │
         ↓
┌─────────────────────────┐
│ Image Transform Lambda  │ ← Does the heavy lifting
│                         │
│ 1. Check cache bucket   │
│ 2. Fetch original       │
│ 3. Process (RAW→JPEG)   │
│ 4. Resize               │
│ 5. Store in cache       │
│ 6. Return image         │
└────────┬────────────────┘
         │
         ↓
┌─────────────────┐
│  Cache Bucket   │ ← Stores transformed versions
└─────────────────┘
```

## 📁 File Structure

```
backend/
├── image-transform/
│   ├── lambda_function.py           # Main transformation logic
│   ├── cloudfront-router.py         # Lambda@Edge router
│   ├── requirements.txt             # Python dependencies
│   ├── deploy.sh                    # Deploy transform Lambda
│   ├── deploy-cloudfront-router.sh  # Deploy router
│   ├── cache-lifecycle.json         # S3 cache lifecycle policy
│   └── SETUP.md                     # Detailed setup instructions
│
├── handlers/
│   ├── photo_upload_presigned.py    # Stores originals only
│   └── photo_handler.py             # Stores originals only
│
└── utils/
    └── cdn_urls.py                  # Generates transformation URLs
```

## 🚀 Deployment

### 1. Deploy Image Transform Lambda

```bash
cd backend/image-transform
./deploy.sh
```

### 2. Create Lambda Layer for Image Processing

```bash
# Create layer with heavy dependencies (Pillow, rawpy, etc.)
mkdir -p layer/python
pip install Pillow rawpy pillow-heif numpy -t layer/python
cd layer && zip -r ../image-processing-layer.zip . && cd ..

# Upload to AWS
aws lambda publish-layer-version \
    --layer-name image-processing \
    --zip-file fileb://image-processing-layer.zip \
    --compatible-runtimes python3.11

# Attach to Lambda
aws lambda update-function-configuration \
    --function-name galerly-image-transform \
    --layers arn:aws:lambda:REGION:ACCOUNT:layer:image-processing:1
```

### 3. Deploy CloudFront Router

```bash
./deploy-cloudfront-router.sh
```

### 4. Configure CloudFront

Update your CloudFront distribution:

```yaml
Behaviors:
  - PathPattern: "*.dng?*"
    EventType: origin-request
    LambdaFunctionARN: arn:aws:lambda:us-east-1:ACCOUNT:function:galerly-cloudfront-router:VERSION
  
  - PathPattern: "*.cr2?*"
    EventType: origin-request
    LambdaFunctionARN: arn:aws:lambda:us-east-1:ACCOUNT:function:galerly-cloudfront-router:VERSION
  
  # ... add for .nef, .heic, .tiff, etc.
```

### 5. Create Cache Bucket

```bash
aws s3 mb s3://galerly-image-cache
aws s3api put-bucket-lifecycle-configuration \
    --bucket galerly-image-cache \
    --lifecycle-configuration file://cache-lifecycle.json
```

## 🔧 How It Works

### Upload Flow

```
User uploads photo.dng (50MB)
    ↓
Backend stores to S3: gallery123/photo456.dng
    ↓
Database stores:
  - url: cdn.galerly.com/gallery123/photo456.dng (original)
  - thumbnail_url: cdn.galerly.com/gallery123/photo456.dng?format=jpeg&width=800&height=600
  - medium_url: cdn.galerly.com/gallery123/photo456.dng?format=jpeg&width=2000&height=2000
```

### Display Flow

```
Browser requests thumbnail_url
    ↓
CloudFront receives: cdn.galerly.com/gallery123/photo456.dng?format=jpeg&width=800
    ↓
Cache miss → Lambda@Edge triggered
    ↓
Lambda@Edge invokes transform Lambda with params:
  {s3_key: "gallery123/photo456.dng", format: "jpeg", width: 800, height: 600}
    ↓
Transform Lambda:
  1. Checks cache: gallery123/photo456.dng/w800h600fjpeg
  2. Not found → Fetches original from S3
  3. Processes RAW → RGB array using rawpy
  4. Resizes to 800x600 using Pillow
  5. Converts to JPEG (quality=85)
  6. Stores in cache bucket
  7. Returns JPEG (200KB) to CloudFront
    ↓
CloudFront caches at edge
    ↓
Browser receives JPEG thumbnail (200KB, not 50MB!)
```

### Subsequent Requests

```
Browser requests same thumbnail_url
    ↓
CloudFront hits edge cache
    ↓
Returns cached JPEG instantly (50-200ms)
```

## 💾 Storage Comparison

### Example: 1000 photos

| Approach | Original | Thumbnails | Medium | Total | Savings |
|----------|----------|------------|--------|-------|---------|
| **Old (Duplicates)** | 50GB | 5GB | 30GB | **85GB** | - |
| **New (On-Demand)** | 50GB | 0.2GB | 2GB | **52.2GB** | **38%** |

The savings increase with more images since cached versions are tiny!

## ⚡ Performance

| Scenario | Time | Notes |
|----------|------|-------|
| First request (RAW) | 2-5s | Processing + caching |
| First request (JPEG) | 200-500ms | Resize + cache |
| Cached request | 50-200ms | CloudFront edge |
| Download original | Varies | Full quality file |

## 🧪 Testing

### Test Lambda Directly

```bash
aws lambda invoke \
    --function-name galerly-image-transform \
    --payload '{
        "s3_key": "test/photo.dng",
        "width": 800,
        "height": 600,
        "format": "jpeg"
    }' \
    response.json
```

### Test via CloudFront

```bash
# RAW image
curl "https://cdn.galerly.com/gallery/photo.dng?format=jpeg&width=800" -o test.jpg

# HEIC image
curl "https://cdn.galerly.com/gallery/photo.heic?format=jpeg&width=800" -o test.jpg

# Check cache header
curl -I "https://cdn.galerly.com/gallery/photo.dng?format=jpeg&width=800"
# Should see: X-Cache: Hit (after first request)
```

## 🎯 Supported Formats

### Input Formats
- **RAW**: DNG, CR2, CR3, NEF, ARW, RAF, ORF, RW2, PEF, 3FR
- **HEIC/HEIF**: iPhone photos
- **Standard**: JPEG, PNG, GIF, WebP, TIFF, BMP

### Output Formats
- JPEG (default, best compatibility)
- PNG (lossless)
- WebP (modern browsers)

## 🔐 Security

- Lambda has read-only access to source bucket
- Lambda has read-write access to cache bucket only
- CloudFront requires signed URLs (optional)
- No public S3 access - all via CloudFront

## 💰 Cost Estimate

For 10,000 photo views/day:

| Service | Cost/Month | Notes |
|---------|-----------|-------|
| Lambda invocations | ~$5 | Only on cache miss |
| Lambda compute | ~$10 | RAW processing |
| S3 storage (cache) | ~$1 | Cached thumbnails |
| CloudFront | ~$8 | Data transfer |
| **Total** | **~$24/month** | vs ~$40 with duplicates |

## 📚 References

- [AWS Serverless Image Handler](https://aws.amazon.com/solutions/implementations/serverless-image-handler/)
- [Lambda@Edge Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)
- [CloudFront Caching](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ConfiguringCaching.html)

