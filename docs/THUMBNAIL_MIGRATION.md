# Thumbnail Migration Script

## Purpose
Generate thumbnails for all existing photos in the database. New uploads automatically get thumbnails, but this script is needed to migrate existing photos.

## What It Does
1. Scans all photos in DynamoDB
2. Identifies photos without thumbnails (where `thumbnail_url == url`)
3. Downloads full-resolution images from S3
4. Generates 800x600 thumbnails (~100KB each)
5. Uploads thumbnails to S3 with `_thumb` suffix
6. Updates database with new `thumbnail_url`

## Performance Impact
- **500MB gallery** → **20MB thumbnails** (96% reduction)
- **Page load time**: 30+ seconds → 2-3 seconds
- **Memory usage**: 500MB → 20MB

## Usage

### 1. Dry Run (Check what will be migrated)
```bash
cd backend
python migrate_generate_thumbnails.py
```

This will:
- ✅ Scan all photos
- ✅ Show how many need thumbnails
- ✅ List photos that would be migrated
- ❌ NOT make any changes

### 2. Test Migration (5 photos)
```bash
python migrate_generate_thumbnails.py --migrate --limit 5
```

Good for testing before full migration.

### 3. Full Migration (all photos)
```bash
python migrate_generate_thumbnails.py --migrate
```

This will:
- ✅ Generate thumbnails for ALL photos
- ✅ Upload to S3
- ✅ Update database
- ✅ Show progress for each photo

## Example Output

```
🖼️  THUMBNAIL GENERATION MIGRATION
================================================================================
S3 Bucket: galerly-images-storage
DynamoDB Table: galerly-photos
Region: us-east-1

📊 Scanning all photos from database...
   ✅ Found 247 photos in database

🔍 Checking which photos need thumbnails...

================================================================================
📊 MIGRATION SUMMARY
================================================================================
Total photos in database: 247
Photos already have thumbnails: 0 ✅
Photos need thumbnails: 247 🔄

🔄 Migrating 247 photos...
================================================================================

[1/247] 📸 Processing: IMG_6198.jpg (ID: a1b2c3d4...)
   ⬇️  Downloading from S3: gallery123/a1b2c3d4.jpg
   📦 Downloaded 3.45 MB
   🖼️  Generating thumbnail...
   ✅ Thumbnail generated: 127.3KB (96.4% smaller)
   ⬆️  Uploading thumbnail: gallery123/a1b2c3d4_thumb.jpg
   💾 Updating database...
   ✅ SUCCESS: Thumbnail created and database updated

[2/247] 📸 Processing: IMG_6199.jpg (ID: e5f6g7h8...)
   ...

================================================================================
🎉 MIGRATION COMPLETE
================================================================================
✅ Successfully migrated: 247 photos
❌ Failed: 0 photos
📊 Total processed: 247

🎉 All photos successfully migrated!
```

## Safety Features

1. **Dry run by default**: Won't make changes unless you use `--migrate`
2. **Idempotent**: Can run multiple times safely (skips photos that already have thumbnails)
3. **Error handling**: Failed photos are logged, but migration continues
4. **Progress tracking**: Shows exactly what's happening for each photo

## Requirements

- Python 3.8+
- AWS credentials configured in `.env`
- Access to S3 bucket (`galerly-images-storage`)
- Access to DynamoDB table (`galerly-photos`)

## Troubleshooting

### "Error scanning photos"
- Check AWS credentials in `.env`
- Verify DynamoDB table name

### "Failed to download from S3"
- Check S3 bucket name
- Verify photos exist in S3

### "Thumbnail generation failed"
- Check if `rawpy` is installed for RAW formats
- Verify image is valid (not corrupted)

### Some photos failed
- Just re-run the script
- It will skip successfully migrated photos
- Only retry failed ones

## After Migration

Once complete:
1. ✅ Gallery pages will load 96% faster
2. ✅ Browser memory usage reduced by 96%
3. ✅ No more freezing on large galleries
4. ✅ New uploads automatically get thumbnails

## Notes

- **Original quality preserved**: Full-resolution images remain at quality=98
- **No data loss**: Original images are never modified
- **Thumbnails only for grid view**: Full-res loaded on click
- **Progressive JPEG**: Thumbnails load smoothly/gradually

