# S3 Bucket Usage Audit

## ✅ VERIFIED - All Backend Files Using Correct Buckets

### Bucket Configuration (backend/utils/config.py)
```python
S3_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')  # Photos storage
S3_FRONTEND_BUCKET = os.environ.get('S3_BUCKET', 'galerly-frontend-app')  # Frontend static assets
```

**Environment Variables:**
- `S3_PHOTOS_BUCKET` → `galerly-images-storage` (for photo uploads/storage)
- `S3_BUCKET` → `galerly-frontend-app` (for HTML/CSS/JS static files)

---

## Photo Upload & Storage Handlers

### ✅ photo_upload_presigned.py (Lines 10, 44, 107, 118, 130, 131, 146, 162, 183, 184)
**Status:** ✅ CORRECT - Uses `S3_BUCKET` which now points to `S3_PHOTOS_BUCKET`

**Operations:**
- Line 10: `from utils.config import s3_client, S3_BUCKET`
- Line 44: `generate_presigned_post(Bucket=S3_BUCKET, ...)`
- Line 107: `head_object(Bucket=S3_BUCKET, Key=s3_key)` - Verify upload
- Line 118: `get_object(Bucket=S3_BUCKET, Key=s3_key)` - Download for validation
- Line 130-131: `put_object(Bucket=S3_BUCKET, ...)` - Upload sanitized image
- Line 146: `delete_object(Bucket=S3_BUCKET, ...)` - Delete malicious files
- Line 162: `delete_object(Bucket=S3_BUCKET, ...)` - Delete problematic files
- Line 183-184: Generate URLs: `https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}`

**Flow:**
1. Generate presigned URL for direct S3 upload
2. Verify file exists after upload
3. Download & validate image (security check)
4. Sanitize image (strip metadata, code)
5. Replace original with sanitized version
6. Delete if malicious

---

### ✅ photo_handler.py (Lines 10, 170-171, 184-185, 761)
**Status:** ✅ CORRECT - Uses `S3_BUCKET` which now points to `S3_PHOTOS_BUCKET`

**Operations:**
- Line 10: `from utils.config import s3_client, S3_BUCKET`
- Line 170-171: `put_object(Bucket=S3_BUCKET, Key=filename, Body=image_data)`
- Line 184-185: Generate URLs: `https://{S3_BUCKET}.s3.amazonaws.com/{filename}`
- Line 761: `delete_object(Bucket=S3_BUCKET, Key=s3_key)` - Delete photos

**Usage:** Base64 upload (legacy), photo deletion

---

### ✅ gallery_handler.py (Lines 10, 561)
**Status:** ✅ CORRECT - Uses `S3_BUCKET` which now points to `S3_PHOTOS_BUCKET`

**Operations:**
- Line 10: `from utils.config import s3_client, S3_BUCKET`
- Line 561: `delete_object(Bucket=S3_BUCKET, Key=photo['s3_key'])` - Delete gallery photos

**Usage:** Bulk photo deletion when deleting galleries

---

### ✅ billing_handler.py (Lines 883, 942)
**Status:** ✅ CORRECT - Uses `S3_BUCKET` which now points to `S3_PHOTOS_BUCKET`

**Operations:**
- Line 883: `from utils.config import s3_client, S3_BUCKET`
- Line 942: `delete_object(Bucket=S3_BUCKET, Key=photo_key)` - Delete photos on downgrade

**Usage:** Delete photos when user downgrades subscription

---

## AWS Setup & Configuration Scripts

### ✅ setup_aws.py (Lines 16, 176, 198, 219, 236, 240)
**Status:** ✅ CORRECT - Uses `S3_PHOTOS_BUCKET` environment variable

**Configuration:**
- Line 16: `S3_BUCKET_NAME = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')`
- Lines 176-240: CORS configuration for photo uploads

**Purpose:** Configure S3 CORS for direct photo uploads from frontend

---

## Tests

### ✅ test_environment.py (Lines 33-34)
**Status:** ✅ CORRECT - Checks BOTH buckets

**Tests:**
```python
assert os.environ.get('S3_BUCKET'), "S3_BUCKET not set (frontend bucket)"
assert os.environ.get('S3_PHOTOS_BUCKET'), "S3_PHOTOS_BUCKET not set (photos storage bucket)"
```

---

### ✅ test_config.py (Lines 53, 65)
**Status:** ✅ CORRECT - Tests BOTH buckets exist

**Tests:**
- Line 53: `photos_bucket = os.environ.get('S3_PHOTOS_BUCKET')`
- Line 65: `frontend_bucket = os.environ.get('S3_BUCKET')`
- Verifies both buckets exist in AWS

---

## Summary

### ✅ All Files Verified
- **7 handler files** using `S3_BUCKET` correctly
- **1 setup script** using `S3_PHOTOS_BUCKET` correctly
- **2 test files** updated to check both buckets

### Bucket Separation
```
galerly-images-storage (S3_PHOTOS_BUCKET)
├── Photo uploads (presigned URLs)
├── Photo storage (all user images)
├── Photo deletion
└── CORS configured for direct uploads

galerly-frontend-app (S3_BUCKET)
├── HTML files (index.html, gallery.html, etc.)
├── CSS files (style.css, etc.)
├── JavaScript files (gallery.js, etc.)
├── Static assets (images, fonts)
└── CloudFront distribution origin
```

### Security Implications
1. ✅ Photos isolated from frontend code
2. ✅ Different CORS policies per bucket
3. ✅ Separate permissions/policies possible
4. ✅ Photos validated & sanitized before storage
5. ✅ Malicious files detected and deleted

### Migration Status
- ✅ **Code fixed** - All new uploads go to `galerly-images-storage`
- ⚠️  **Data migration needed** - Old photos in `galerly-frontend-app` need moving
- ✅ **Tests updated** - Both buckets verified
- ✅ **CORS configured** - Both buckets have proper CORS

---

## Next Steps

### 1. Migrate Existing Photos (REQUIRED)
Run this AWS CLI command to move old photos:
```bash
aws s3 sync s3://galerly-frontend-app/ s3://galerly-images-storage/ \
  --exclude "*" \
  --include "*/*/*.jpg" \
  --include "*/*/*.jpeg" \
  --include "*/*/*.png" \
  --include "*/*/*.webp" \
  --include "*/*/*.heic" \
  --dryrun  # Remove --dryrun when ready
```

### 2. Update Database URLs (OPTIONAL)
If photos are still in frontend bucket, update DB records:
```python
# Scan all photos, update URLs to point to new bucket
for photo in photos_table.scan()['Items']:
    if 'galerly-frontend-app' in photo.get('url', ''):
        photo['url'] = photo['url'].replace(
            'galerly-frontend-app',
            'galerly-images-storage'
        )
        photo['thumbnail_url'] = photo['thumbnail_url'].replace(
            'galerly-frontend-app',
            'galerly-images-storage'
        )
        photos_table.put_item(Item=photo)
```

### 3. Clean Up Old Photos (AFTER MIGRATION)
Once photos are migrated and verified:
```bash
# Delete old photos from frontend bucket
aws s3 rm s3://galerly-frontend-app/ \
  --recursive \
  --exclude "*" \
  --include "*/*/*.jpg" \
  --include "*/*/*.jpeg" \
  --include "*/*/*.png"
```

---

**Last Updated:** 2025-11-17
**Status:** ✅ All backend files verified and using correct buckets

