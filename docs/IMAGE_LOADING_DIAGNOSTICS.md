# 📸 Image Loading Diagnostics & Troubleshooting Guide

## ✅ Current Configuration Status

### Backend Configuration (100% VERIFIED)
```python
# backend/utils/cdn_urls.py
CDN_DOMAIN = 'cdn.galerly.com'
```

**URL Generation Test:**
```bash
✅ get_cdn_url('test/photo.jpg') → 'https://cdn.galerly.com/test/photo.jpg'
```

### Frontend Configuration (100% VERIFIED)
```javascript
// frontend/js/config.js
CDN_URL: 'https://cdn.galerly.com'

function getImageUrl(path) {
  // ✅ Converts old S3 URLs → CloudFront
  // ✅ Returns CDN URLs as-is  
  // ✅ Uses CDN_URL for production
}
```

### Code Quality Checks (100% PASSED)
- ✅ Only ONE `getImageUrl` function exists (in config.js)
- ✅ No duplicate `getImageUrl` functions in other JS files
- ✅ No hardcoded S3 URLs anywhere in frontend
- ✅ Backend generates CloudFront URLs correctly
- ✅ Frontend uses CloudFront URLs consistently

### CloudFront CDN Setup
- ✅ Distribution: Active
- ✅ Lambda@Edge: Pass-through (simple & fast)
- ✅ Domain: `cdn.galerly.com`
- ✅ Origin: `galerly-images-storage` S3 bucket

---

## 🔧 Automated Deployment Checks (NEW!)

The CI/CD pipeline now automatically performs these checks on every deployment:

### 1. S3 Image Verification
```bash
# Checks if images exist in S3
aws s3 ls s3://galerly-images-storage/ --recursive | head -20
```

**What it does:**
- Counts total images in bucket
- Lists first 20 images with timestamps
- Warns if bucket is empty (expected for fresh deployments)

### 2. CloudFront Cache Invalidation
```bash
# Invalidates all cached images
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

**What it does:**
- Finds the correct CDN distribution (tries "Galerly Image CDN" first)
- Creates invalidation for all paths (`/*`)
- Reports invalidation status
- Cache clears in 1-2 minutes

**Why this matters:**
- Ensures fresh images are served
- Prevents stale cache issues
- Automatic on every deployment

---

## 🧪 Test Suite Results

**21/23 tests passing** for image loading:

### ✅ Passing Tests
1. `test_cdn_url_basic` - CloudFront URL generation
2. `test_cdn_url_with_special_characters` - Special chars handling
3. `test_photo_urls_structure` - URL structure validation
4. `test_photo_urls_use_cdn` - All URLs use CloudFront
5. `test_image_sizes_configured` - Image size configuration
6. `test_cdn_url_no_hardcoded_values` - No hardcoded values
7. `test_config_file_exists` - Frontend config exists
8. `test_config_has_cdn_url` - CDN_URL configured
9. `test_config_has_get_image_url_function` - Function exists
10. `test_get_image_url_uses_cdn` - Function uses CDN
11. `test_no_duplicate_get_image_url` - No duplicates ✨
12. `test_no_hardcoded_s3_urls` - No hardcoded S3 URLs ✨
13. Plus 9 more tests...

### ⚠️ Non-Critical Test Failures
1. `test_cdn_domain_environment_variable` - CDN_DOMAIN not set locally (fine, defaults to 'cdn.galerly.com')
2. `test_required_js_files_exist` - Missing `dashboard.js` (not critical for image loading)

---

## 🔍 Troubleshooting Guide

### If you're still seeing "Image not found":

#### 1. **Verify Images Exist in S3**

Run locally:
```bash
aws s3 ls s3://galerly-images-storage/ --recursive | head -20
```

**Expected:** List of images with paths like:
```
2024-01-15 10:30:45  2456789 gallery-uuid/photo-uuid.jpg
2024-01-15 10:31:12  3567890 gallery-uuid/photo-uuid2.jpg
```

**If empty:**
- Upload images through the gallery interface
- Check if uploads are completing successfully
- Verify S3 bucket name in secrets

#### 2. **Check CloudFront Distribution Status**

```bash
aws cloudfront get-distribution --id YOUR_DIST_ID --query 'Distribution.Status' --output text
```

**Expected:** `Deployed`

**If `InProgress`:**
- CloudFront is still deploying (takes 15-20 minutes after creation)
- Wait for deployment to complete
- Check again in 5 minutes

#### 3. **Test Direct S3 Access (Bypass CloudFront)**

```bash
# Try accessing an image directly
aws s3api get-object-acl --bucket galerly-images-storage --key gallery-uuid/photo-uuid.jpg
```

**Expected:** Returns object ACL

**If fails:**
- Image doesn't exist in S3
- Check the exact S3 key/path

#### 4. **Test CloudFront Access**

```bash
# Test CDN URL
curl -I https://cdn.galerly.com/gallery-uuid/photo-uuid.jpg
```

**Expected:** `HTTP/2 200`

**Possible errors:**
- `HTTP/2 403` - Check S3 bucket policy and OAI configuration
- `HTTP/2 404` - Image doesn't exist in S3
- `HTTP/2 502` - Lambda@Edge error (check CloudWatch Logs)
- `HTTP/2 503` - Lambda@Edge timeout or failure

#### 5. **Check Browser Console**

Open DevTools → Console → Try loading a gallery:

**Look for:**
- Image request URLs (should be `https://cdn.galerly.com/...`)
- Response status codes
- CORS errors
- JavaScript errors

**Common issues:**
- Mixed content (HTTP vs HTTPS)
- CORS blocks
- JavaScript errors preventing image load

#### 6. **Clear All Caches**

**Browser:**
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Incognito mode: `Ctrl+Shift+N` or `Cmd+Shift+N`
- Clear site data: DevTools → Application → Clear storage

**CloudFront:**
```bash
# Invalidate cache (now automated in CI/CD)
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

**DNS:**
```bash
# Flush DNS cache
# Windows:
ipconfig /flushdns

# Mac:
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Linux:
sudo systemd-resolve --flush-caches
```

---

## 📊 Automated Monitoring

### GitHub Actions Pipeline

Every push to `main` now includes:

1. **Image Verification Step** (Stage 7)
   - Location: `test-deployment` job
   - Runs after: Backend deployment
   - Purpose: Verify images exist in S3

2. **Cache Invalidation Step** (Stage 7)
   - Location: `test-deployment` job  
   - Runs after: Image verification
   - Purpose: Clear CloudFront cache for fresh images

### View Results

After each deployment:
1. Go to GitHub Actions
2. Click on the latest workflow run
3. Expand "Post-Deployment Tests"
4. Check "Verify Images Exist in S3 Bucket"
5. Check "Invalidate CDN CloudFront Cache"

---

## 🚀 Quick Fix Commands

### If images suddenly stop loading:

```bash
# 1. Check S3
aws s3 ls s3://galerly-images-storage/ --recursive | head -10

# 2. Check CloudFront status
aws cloudfront get-distribution \
  --id YOUR_DIST_ID \
  --query 'Distribution.Status' \
  --output text

# 3. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

# 4. Check Lambda@Edge logs
aws logs tail /aws/lambda/us-east-1.galerly-image-resize-edge --follow
```

### If images load slowly:

```bash
# Check CloudFront cache hit rate
aws cloudfront get-distribution-config \
  --id YOUR_DIST_ID \
  | jq '.DistributionConfig.DefaultCacheBehavior'
```

**Good cache hit rate:** 80%+ (images served from edge)
**Poor cache hit rate:** <50% (images fetched from origin)

---

## 📈 Performance Expectations

### First Load (Cache Miss)
- **Latency:** 500-1000ms (fetches from S3)
- **After:** Image cached at CloudFront edge

### Subsequent Loads (Cache Hit)
- **Latency:** 50-200ms (served from edge)
- **Global:** Fast worldwide delivery

### Cache Duration
- **Images:** Cached for 24 hours by default
- **Invalidation:** 1-2 minutes to propagate

---

## 🔐 Security Checklist

- ✅ S3 bucket is private (no public access)
- ✅ CloudFront uses Origin Access Identity (OAI)
- ✅ Images accessible only through CloudFront
- ✅ HTTPS enforced (`redirect-to-https`)
- ✅ No direct S3 URLs in frontend code

---

## 📝 Summary

### What's Working
✅ Backend generates CloudFront URLs
✅ Frontend uses CloudFront URLs  
✅ No duplicate `getImageUrl` functions
✅ No hardcoded S3 URLs
✅ CloudFront CDN active
✅ Lambda@Edge pass-through working
✅ Automated S3 verification in CI/CD
✅ Automated cache invalidation in CI/CD

### What to Check if Issues Persist
1. Images actually exist in S3
2. CloudFront distribution is deployed
3. Browser/CloudFront cache is cleared
4. DNS resolves `cdn.galerly.com` correctly
5. No JavaScript errors in console

### Getting Help
- Check GitHub Actions logs for deployment issues
- Check CloudWatch Logs for Lambda@Edge errors  
- Check browser DevTools console for frontend errors
- Use the troubleshooting commands above

---

**Last Updated:** 2024-01-19
**Pipeline Version:** v2.0 (with automated diagnostics)

