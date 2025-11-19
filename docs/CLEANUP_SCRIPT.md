# Gallery Cleanup Script Documentation

## Overview

The `cleanup_galleries.py` script safely removes all gallery data while preserving user accounts. This allows users to continue logging in, but they'll start with a clean slate (no galleries).

---

## 🏗️ Architecture Review

### What Gets DELETED ❌

**DynamoDB Tables (Required Cleanup):**
- `galerly-galleries` - All photo galleries
- `galerly-photos` - Photo metadata
- `galerly-analytics` - Gallery analytics/tracking
- `galerly-client-favorites` - Client photo selections
- `galerly-client-feedback` - Client gallery feedback

**DynamoDB Tables (Optional Cleanup):**
- `galerly-billing` - Payment/billing history
- `galerly-subscriptions` - Stripe subscription data
- `galerly-refunds` - Refund requests
- `galerly-audit-log` - Change audit trail

**S3 Storage:**
- `galerly-images-storage` - ALL photos deleted
  - Structure: `{user_id}/{gallery_id}/{photo_id}.ext`
  - This includes original photos, thumbnails, and medium-res versions

### What Gets PRESERVED ✅

**User Data:**
- `galerly-users` - User accounts (can still login)
- `galerly-sessions` - Active login sessions
- `galerly-notification-preferences` - Email preferences

**System Data:**
- `galerly-newsletters` - Newsletter subscribers
- `galerly-contact` - Support tickets
- `galerly-visitor-tracking` - Website analytics

---

## 🚀 Usage

### 1. Preview Mode (Safe - Read Only)
Shows what data exists and what will be deleted:

```bash
cd backend
python cleanup_galleries.py preview
```

**Output:**
```
✅ TABLES THAT WILL BE PRESERVED:
   • galerly-users                          1,234 items
   • galerly-sessions                          56 items
   
❌ TABLES THAT WILL BE CLEANED:
   • galerly-galleries                      5,678 items
   • galerly-photos                        45,234 items + S3 files
   • galerly-analytics                     12,345 items
   
📊 Total items: 63,257
🗑️  S3 files: 2.5 GB
```

### 2. Dry Run Mode (Safe - Simulates Deletion)
Performs a complete simulation without actually deleting anything:

```bash
python cleanup_galleries.py dry-run
```

**With billing data:**
```bash
python cleanup_galleries.py dry-run --include-billing
```

### 3. Execute Mode (⚠️ DANGER - Actual Deletion)
Permanently deletes all gallery data:

```bash
python cleanup_galleries.py execute
```

**With billing data:**
```bash
python cleanup_galleries.py execute --include-billing
```

**Safety Confirmations Required:**
1. Type: `YES DELETE ALL GALLERIES`
2. Type: `CONFIRM DELETE`

---

## 🔒 Safety Features

### Multi-Step Confirmation
- Preview shows exact counts before deletion
- Two separate confirmation prompts
- Clear warnings about data loss

### Dry Run Mode
- Test the entire process without deleting
- See exactly what would be deleted
- Verify script behavior before execution

### Batch Processing
- Uses DynamoDB batch operations
- Handles large datasets efficiently
- Rate limiting to avoid throttling

### Error Handling
- Continues processing even if individual items fail
- Reports all errors at the end
- Maintains operation log

---

## 📊 Process Flow

### 1. Preview Phase
```
1. Connect to AWS
2. Scan all tables to get item counts
3. Check S3 bucket for photo count/size
4. Display summary report
```

### 2. Cleanup Phase
```
1. Scan galerly-galleries → Delete all items
2. Scan galerly-photos → Delete all items
3. Delete all S3 photos (batch 1000 at a time)
4. Scan galerly-analytics → Delete all items
5. Scan galerly-client-favorites → Delete all items
6. Scan galerly-client-feedback → Delete all items
7. [Optional] Clean billing tables
8. Generate summary report
```

### 3. Verification Phase
```
1. Count remaining items in each table
2. Verify S3 bucket is empty (or only has non-gallery files)
3. Confirm users can still login
4. Display final status
```

---

## ⚠️ Important Warnings

### Data Loss
- **ALL galleries will be permanently deleted**
- **ALL photos will be permanently deleted from S3**
- **This operation CANNOT be undone**
- **No backups are created by this script**

### Backup First!
Before running execute mode, consider:

1. **DynamoDB Point-in-Time Recovery:**
```bash
# Verify PITR is enabled
aws dynamodb describe-continuous-backups \
  --table-name galerly-galleries

# If needed, restore to before cleanup:
aws dynamodb restore-table-to-point-in-time \
  --source-table-name galerly-galleries \
  --target-table-name galerly-galleries-restored \
  --restore-date-time 2025-01-15T10:00:00Z
```

2. **S3 Versioning:**
```bash
# Enable versioning (if not already)
aws s3api put-bucket-versioning \
  --bucket galerly-images-storage \
  --versioning-configuration Status=Enabled

# Photos can be restored from versions after deletion
```

### User Impact
After cleanup:
- ✅ Users can still login
- ✅ Sessions remain active
- ✅ Email preferences preserved
- ❌ No galleries visible
- ❌ No photos accessible
- ❌ No analytics data
- ❌ Client favorites lost

---

## 🔧 Technical Details

### DynamoDB Operations
- **Scan & Delete:** Processes all items in batches
- **Batch Size:** Up to 25 items per batch (DynamoDB limit)
- **Rate Limiting:** 0.5s delay between batches
- **Key Extraction:** Automatically detects partition/sort keys

### S3 Operations
- **Batch Delete:** Up to 1000 objects per request
- **Pagination:** Handles buckets with millions of files
- **Size Calculation:** Tracks total storage freed
- **Error Tracking:** Reports failed deletions

### Performance
- **Small Dataset (<10K items):** ~1-2 minutes
- **Medium Dataset (10K-100K items):** ~5-10 minutes  
- **Large Dataset (>100K items):** ~20-30 minutes
- **S3 Photos:** ~1-5 minutes per GB

---

## 🐛 Troubleshooting

### Script Won't Run
```bash
# Install dependencies
cd backend
source venv/bin/activate
pip install boto3

# Or use system Python
python3 cleanup_galleries.py preview
```

### Permission Errors
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check DynamoDB permissions
aws dynamodb list-tables

# Check S3 permissions
aws s3 ls s3://galerly-images-storage
```

### Throttling Errors
The script includes rate limiting, but if you see throttling:
1. Increase delay in code: `time.sleep(0.5)` → `time.sleep(1.0)`
2. Reduce batch size
3. Run during off-peak hours

### Partial Deletion
If script stops mid-execution:
1. Run `preview` again to see what remains
2. Run `dry-run` to verify safe to continue
3. Run `execute` again (idempotent - safe to re-run)

---

## 📝 Example Output

### Preview Mode
```
================================================================================
📊 CLEANUP PREVIEW
================================================================================

✅ TABLES THAT WILL BE PRESERVED:
   • galerly-users                          1,234 items
   • galerly-sessions                          56 items
   • galerly-notification-preferences          234 items
   • galerly-newsletters                       567 items
   • galerly-contact                            89 items
   • galerly-visitor-tracking                2,345 items

❌ TABLES THAT WILL BE CLEANED:
   • galerly-galleries                      5,678 items
   • galerly-photos                        45,234 items + S3 files
   • galerly-analytics                     12,345 items
   • galerly-client-favorites               3,456 items
   • galerly-client-feedback                  789 items

⚠️  OPTIONAL CLEANUP:
   • galerly-billing                        1,234 items - Billing records
   • galerly-subscriptions                    123 items - Stripe subscriptions
   • galerly-refunds                           45 items - Refunds
   • galerly-audit-log                        678 items - Audit trail

📊 Total: 67,502 items (required) + 2,080 items (optional)

🗑️  S3 STORAGE:
   • Bucket: galerly-images-storage
   • Action: ALL PHOTOS WILL BE DELETED

================================================================================
```

### Execution Mode
```
🔥 LIVE MODE - DELETING DATA
================================================================================

🗑️  Cleaning galerly-galleries (Photo galleries)...
📋 Scanning galerly-galleries...
   Processing batch of 25 items...
   Processing batch of 25 items...
   ...
   ✅ Deleted 5,678 items

🗑️  Cleaning galerly-photos (Photo metadata)...
📋 Scanning galerly-photos...
   Processing batch of 25 items...
   ...
   ✅ Deleted 45,234 items

🗑️  Deleting photos from S3 bucket: galerly-images-storage
   Found 45,234 objects...
   ✅ Deleted 45,234 files (2.5 GB)

================================================================================
📊 CLEANUP SUMMARY
================================================================================

✅ Deleted:
   • DynamoDB items: 67,502
   • S3 files: 45,234 (2.5 GB)

================================================================================

✅ Cleanup complete!
   Users can still login, but all galleries have been removed.
```

---

## 🎯 Use Cases

### 1. Testing Environment Reset
Clean up test data between development cycles:
```bash
python cleanup_galleries.py execute
```

### 2. User Data Migration
Remove old data before importing new structure:
```bash
# Backup users first
python cleanup_galleries.py execute --include-billing
```

### 3. Privacy Compliance
Delete user galleries while keeping account (GDPR "right to erasure" for content only):
```bash
python cleanup_galleries.py execute
# Users remain, but all their content is removed
```

### 4. Storage Cost Reduction
Remove galleries to reduce S3 storage costs:
```bash
# Preview first to see storage savings
python cleanup_galleries.py preview
# Then execute
python cleanup_galleries.py execute
```

---

## ✅ Post-Cleanup Verification

After running the script:

### 1. Verify Tables Are Clean
```bash
cd backend
python setup_dynamodb.py list
```

Expected:
- `galerly-galleries`: 0 items
- `galerly-photos`: 0 items
- `galerly-users`: Still has items ✅

### 2. Verify S3 Is Clean
```bash
aws s3 ls s3://galerly-images-storage/ --recursive | wc -l
```

Expected: `0` (or only non-gallery files)

### 3. Test User Login
1. Go to frontend
2. Login with existing user
3. Should see empty dashboard (no galleries)
4. Should be able to create new gallery

---

## 🔐 Security Considerations

### AWS Credentials
Script requires permissions for:
- `dynamodb:Scan`
- `dynamodb:DeleteItem`
- `dynamodb:BatchWriteItem`
- `dynamodb:DescribeTable`
- `s3:ListBucket`
- `s3:DeleteObject`

### Audit Trail
All deletions are logged in:
- CloudWatch Logs (DynamoDB operations)
- S3 Access Logs (if enabled)
- CloudTrail (AWS API calls)

### Compliance
Consider regulatory requirements:
- Data retention policies
- User consent for deletion
- Backup requirements
- Audit trail retention

---

## 📞 Support

If you encounter issues:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify table access: `aws dynamodb list-tables`
3. Run in dry-run mode first: `python cleanup_galleries.py dry-run`
4. Check CloudWatch logs for errors
5. Review DynamoDB throttling metrics

---

**Created:** 2025-01-19  
**Version:** 1.0  
**Status:** Production-ready with safety checks

