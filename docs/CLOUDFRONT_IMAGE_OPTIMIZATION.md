# CloudFront Image Optimization - Implementation Guide

## 🎯 Architecture Overview

```
User Request → CloudFront (CDN) → Lambda@Edge (resize) → S3 (original)
                    ↓
              Cache resized image
                    ↓
        Serve instantly next time
```

## 💰 Cost Comparison

### Current (3 versions stored):
- **Storage**: 3x cost (original + medium + thumb)
- **Lambda**: High processing during upload
- **Total**: ~$3-5/month for 1000 photos

### CloudFront (1 version + on-demand):
- **Storage**: 1x cost (original only) ✅
- **CloudFront**: $0.085/GB transfer (first 10TB)
- **Lambda@Edge**: $0.00000625 per resize (first time only)
- **Caching**: 99% of requests served from cache
- **Total**: ~$1-2/month for 1000 photos ✅

**SAVINGS: 50-60% cheaper!**

## 🚀 Implementation Steps

### Step 1: Create CloudFront Distribution

1. Go to AWS Console → CloudFront
2. Create Distribution:
   - **Origin Domain**: `galerly-images-storage.s3.amazonaws.com`
   - **Origin Path**: Leave empty
   - **Cache Policy**: CacheOptimized
   - **Viewer Protocol**: Redirect HTTP to HTTPS
   - **Alternate Domain Names**: `cdn.galerly.com`
   - **SSL Certificate**: Request ACM certificate for `cdn.galerly.com`

### Step 2: Create Lambda@Edge Function

This function intercepts requests and resizes images on-the-fly:

**Function**: `galerly-image-resize-edge`
**Runtime**: Node.js 18.x
**Region**: us-east-1 (Lambda@Edge must be in us-east-1)

```javascript
// See: lambda-edge/resize.js
```

### Step 3: Update Frontend URLs

Change image URLs from direct S3 to CloudFront:

**Before**:
```javascript
thumbnail_url: https://galerly-images-storage.s3.amazonaws.com/gallery123/photo456.jpg
```

**After**:
```javascript
thumbnail_url: https://cdn.galerly.com/resize/800x600/gallery123/photo456.jpg
medium_url: https://cdn.galerly.com/resize/2000x2000/gallery123/photo456.jpg
url: https://cdn.galerly.com/gallery123/photo456.jpg  // Original
```

### Step 4: URL Format

```
Format: https://cdn.galerly.com/resize/{width}x{height}/{s3_key}

Examples:
- Thumbnail (800x600): /resize/800x600/gallery123/photo456.jpg
- Medium (2000x2000): /resize/2000x2000/gallery123/photo456.jpg
- Original: /gallery123/photo456.jpg (no resize prefix)
```

## 📊 Performance Benefits

1. **First Request** (cold):
   - CloudFront → Lambda@Edge → Resize → Cache → Serve
   - Time: ~500ms (one-time cost)

2. **Subsequent Requests** (warm):
   - CloudFront → Serve from cache
   - Time: ~50ms (instant!)

3. **Global CDN**:
   - Images served from nearest edge location
   - Faster for users worldwide

## 🔧 Technical Details

### Lambda@Edge Function (Origin Request)

- Triggered on **origin-request** (before fetching from S3)
- Checks if resized version exists in CloudFront cache
- If not: downloads original, resizes, returns resized image
- CloudFront caches the resized image automatically

### Caching Strategy

- **Original images**: Cache for 1 year (immutable)
- **Resized images**: Cache for 1 year (immutable)
- **Cache key**: Full URL (including size parameters)

### Cost Optimization

- Lambda@Edge only runs on **cache miss** (first request)
- 99% of requests = cache hit = $0 Lambda cost
- Storage reduced by 66% (no medium/thumb stored)

## 🎨 Smart Optimizations

1. **WebP Support** (optional):
   ```
   /resize/800x600/webp/gallery123/photo456.jpg
   ```
   - 30% smaller file size
   - Automatic format conversion

2. **Quality Parameter** (optional):
   ```
   /resize/800x600/q85/gallery123/photo456.jpg
   ```
   - Adjustable JPEG quality

3. **Lazy Resizing**:
   - Thumbnails generated only when viewed
   - Old galleries with no views = no cost

## 📝 Migration Plan

1. ✅ Set up CloudFront distribution
2. ✅ Deploy Lambda@Edge function
3. ✅ Update backend to use CloudFront URLs
4. ✅ Update frontend to use CloudFront URLs
5. ✅ Test with new uploads
6. ⚠️  Existing photos: Keep 3 versions OR regenerate on-demand
7. 🗑️  Optional: Delete medium/thumb versions after migration

## ⚠️ Important Notes

- **Lambda@Edge must be in us-east-1** (CloudFront requirement)
- **Max response size**: 1 MB for Lambda@Edge (use S3 redirect for larger)
- **Timeout**: 30 seconds max
- **Cold start**: First request per size may be slower

## 🔒 Security

- CloudFront uses S3 Origin Access Identity (OAI)
- Direct S3 access blocked (only via CloudFront)
- Prevents bandwidth theft
- DDoS protection included

## 📈 Monitoring

- CloudWatch metrics for Lambda@Edge
- CloudFront access logs
- Cache hit ratio (should be >95%)

## 🚀 Next Steps

See implementation files:
- `lambda-edge/resize.js` - Lambda@Edge function
- `scripts/cloudfront-setup.sh` - Automated setup script
- `backend/utils/cdn_urls.py` - URL helper functions

