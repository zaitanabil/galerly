# Galerly Image Transformation System

## 📸 Overview

High-performance image transformation system with cache-first architecture.

**Key Features:**
- ✅ **Cache-First** - Check S3 cache before transforming
- ✅ **Async Processing** - Non-blocking transformations
- ✅ **All Formats** - RAW (DNG, CR2, NEF), HEIC, TIFF, JPEG, PNG
- ✅ **Fast Delivery** - CloudFront edge caching
- ✅ **Cost Efficient** - Transform once, cache forever

## ☁️ CloudFront Distributions

Galerly uses TWO CloudFront distributions:

### 1. Frontend Distribution (EEUAF5M39R2Z5)
- **Domain**: galerly.com, www.galerly.com
- **Origin**: galerly-frontend-app S3 bucket
- **Purpose**: Serves frontend HTML/CSS/JS files
- **Lambda@Edge**: None

### 2. Image CDN Distribution (E3P0EU1X4VGR58) ⭐
- **Domain**: cdn.galerly.com
- **Origin**: galerly-images-storage S3 bucket
- **Purpose**: Serves and transforms images
- **Lambda@Edge**: galerly-cloudfront-router (origin-request event)
- **Used by**: Image transformation system

**Important**: The image transformation system uses the **Image CDN Distribution** (E3P0EU1X4VGR58).

GitHub secret `CLOUDFRONT_DISTRIBUTION_ID` must be set to `E3P0EU1X4VGR58`.

## 🏗️ Architecture

```
Browser Request: cdn.galerly.com/photo.dng?format=jpeg&width=800
       ↓
CloudFront (Edge Cache)
    ↓ (Cache miss)
Lambda@Edge (Origin Request)
    ├─ No ?format= or ?width= → Pass through to S3 (instant)
    ├─ Check S3 cache → Found? → Serve from cache (instant)
    └─ Not cached? → Invoke Transform Lambda (async) + Serve original
                     Next request will hit cache
```

## 🚀 Quick Start

### Automated Deployment (Recommended)

```bash
git push origin main  # GitHub Actions deploys everything
```

### Manual Deployment

```bash
cd backend/image-transform

# 1. Deploy Transform Lambda with Layer
./deploy.sh

# 2. Deploy CloudFront Router
./deploy-cloudfront-router.sh
```

## 📁 Files

- `lambda_function.py` - Transform Lambda (processes images)
- `cloudfront-router.py` - Lambda@Edge (cache-first routing)
- `deploy.sh` - Deploys Transform Lambda + Layer
- `deploy-cloudfront-router.sh` - Deploys CloudFront Router
- `test-local.sh` - Local testing with HEIC images

## 🔧 How It Works

### Display Flow (Optimized)

```
Request: thumbnail_url (?format=jpeg&width=800)
    ↓
Lambda@Edge: Check S3 cache
    ├─ CACHED? → Redirect to cache (50ms)
    └─ NOT CACHED? → Trigger async transform + Return original
                     (Transform completes in background)
                     (Next request hits cache)
```

### First vs Subsequent Loads

| Load | Time | What Happens |
|------|------|--------------|
| **First** | ~30s for 20 images | Async transforms, show originals |
| **Second** | 2-3s for 20 images | All from S3 cache |
| **Third+** | <1s for 20 images | CloudFront edge cache |

## 💾 Storage

Store originals only. Transformations cached on-demand.

**Example: 1000 photos**
- Originals: 50GB
- Cached transforms: 2-3GB (only what's requested)
- Total: 52-53GB (vs 85GB with duplicates)
- **Savings: 38%**

## ⚡ Performance

| Scenario | Time |
|----------|------|
| Regular JPEG (no transform) | 50-100ms |
| Cached transform | 50-200ms |
| First RAW transform | 2-5s |
| ZIP download (originals) | Varies by size |

## 🎯 Supported Formats

**Input:** RAW (DNG, CR2, NEF, ARW), HEIC, TIFF, JPEG, PNG  
**Output:** JPEG (default), PNG, WebP

## 🧪 Local Testing

```bash
cd backend/image-transform

# Install dependencies in venv
python3 -m venv venv
source venv/bin/activate
pip install Pillow rawpy pillow-heif boto3

# Run tests with your images
./test-local.sh /path/to/images
```

## 📋 GitHub Secrets Required

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
CLOUDFRONT_DISTRIBUTION_ID
LAMBDA_IMAGE_TRANSFORM_FUNCTION_NAME
LAMBDA_CLOUDFRONT_ROUTER_FUNCTION_NAME
S3_IMAGE_CACHE_BUCKET
S3_PHOTOS_BUCKET
```

## 🔐 IAM Permissions

**Transform Lambda:**
- S3: Read from uploads bucket
- S3: Read/Write to cache bucket

**CloudFront Router:**
- Lambda: Invoke transform function
- S3: Head/Get from cache bucket

## 💰 Cost (10k views/day)

- Lambda: ~$10/month
- S3 cache: ~$1/month
- CloudFront: ~$8/month
- **Total: ~$19/month**

