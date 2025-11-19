# 🎯 URGENT: Image Upload Fix Implementation

## 📋 Summary

**Problem**: HTTP 413 errors when uploading images > 7.5MB due to API Gateway's 10MB limit.

**Solution**: Direct S3 uploads using presigned URLs (bypassing API Gateway limit).

**Status**: 
- ✅ Backend deployed (presigned URL handlers)
- ❌ Frontend needs update (this document)
- 🎯 ETA: 10 minutes to implement

---

## 🔧 Frontend Changes Required

### File: `frontend/js/gallery-loader.js`

**Current Flow (Broken)**:
```javascript
// Line 852-859: Sends full base64 through API Gateway (10MB limit!)
const response = await apiRequest(`galleries/${galleryId}/photos`, {
    method: 'POST',
    body: JSON.stringify({
        filename: file.name,
        data: base64,  // ❌ FAILS for images > 7.5MB
        skip_duplicate_check: true
    })
});
```

**New Flow (Works)**:
```javascript
// Step 1: Get presigned URL from Lambda
const urlResponse = await apiRequest(`galleries/${galleryId}/photos/upload-url`, {
    method: 'POST',
    body: JSON.stringify({
        filename: file.name,
        content_type: file.type,
        file_size: file.size
    })
});

const { photo_id, s3_key, upload_url, upload_fields } = urlResponse;

// Step 2: Upload directly to S3 (NO API Gateway!)
const formData = new FormData();
Object.entries(upload_fields).forEach(([key, value]) => {
    formData.append(key, value);
});
formData.append('file', file);  // ✅ Direct file upload (no base64!)

await fetch(upload_url, {
    method: 'POST',
    body: formData  // ⚠️  NO Content-Type header! FormData sets it automatically
});

// Step 3: Confirm upload with Lambda
const confirmResponse = await apiRequest(`galleries/${galleryId}/photos/confirm-upload`, {
    method: 'POST',
    body: JSON.stringify({
        photo_id,
        s3_key,
        filename: file.name,
        file_size: file.size,
        file_hash: '' // TODO: Calculate client-side if needed for duplicates
    })
});
```

---

## 📝 Implementation Steps

### 1. **Backup Current Implementation**
```bash
cp frontend/js/gallery-loader.js frontend/js/gallery-loader.js.backup
```

### 2. **Update Upload Function**

Find the upload section (around line 852) and replace with the new 3-step flow above.

**Key Changes**:
- Line ~752-860: Replace entire upload logic
- Remove base64 encoding for upload (keep for duplicate check)
- Add progress tracking for S3 upload
- Handle S3 upload errors separately

### 3. **Handle Duplicate Detection**

Duplicate detection still needs base64 for hash calculation:
```javascript
// Keep base64 for duplicate check (Step 1)
const checkResponse = await apiRequest(`galleries/${galleryId}/photos/check-duplicates`, {
    method: 'POST',
    body: JSON.stringify({
        filename: file.name,
        data: base64  // ✅ Still needed for duplicate detection
    })
});

// Then use NEW upload flow (Steps 2-4 above)
```

### 4. **Update Progress Tracking**

S3 upload progress:
```javascript
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        progressBar.style.width = `${Math.round(percentComplete)}%`;
        statusText.textContent = `Uploading... ${Math.round(percentComplete)}%`;
    }
});

xhr.open('POST', upload_url);
xhr.onload = () => {
    if (xhr.status === 204 || xhr.status === 200) {
        // Success! Proceed to confirm
    }
};
xhr.send(formData);
```

---

## ⚠️  Important Notes

### CORS Considerations
- S3 direct upload uses **S3's CORS**, not API Gateway CORS
- Already configured in `backend/setup_aws.py` (s3-cors command)
- If S3 upload fails with CORS, run: `python3 backend/setup_aws.py s3-cors`

### Duplicate Detection Flow
```
1. Read file as base64 (for hash calculation)
2. Check duplicates via API Gateway ✅ (small payload, < 10MB)
3. Get presigned URL via API Gateway ✅
4. Upload to S3 directly ✅ (bypasses API Gateway!)
5. Confirm via API Gateway ✅
```

### Error Handling
```javascript
try {
    // Step 1: Get URL
    const urlResponse = await apiRequest(...);
    
    // Step 2: Upload to S3
    const s3Response = await fetch(upload_url, { method: 'POST', body: formData });
    if (!s3Response.ok) {
        throw new Error(`S3 upload failed: ${s3Response.status}`);
    }
    
    // Step 3: Confirm
    const confirmResponse = await apiRequest(...);
    
} catch (error) {
    console.error('Upload failed:', error);
    statusText.textContent = `Failed: ${error.message}`;
    progressBar.style.background = '#f44336';
}
```

---

## 🧪 Testing Checklist

After implementing:

1. ✅ Test small image (< 1MB) - should work
2. ✅ Test medium image (5MB) - should work
3. ✅ Test large image (15MB) - **should now work!**
4. ✅ Test very large image (50MB) - should work
5. ✅ Test duplicate detection - should still work
6. ✅ Test progress bar - should show real progress
7. ✅ Test upload multiple files - should work in batch

---

## 🚀 Deployment

```bash
# 1. Test locally (if possible)
# 2. Commit changes
git add frontend/js/gallery-loader.js
git commit -m "fix: implement presigned S3 URLs for large image uploads"
git push origin main

# 3. GitHub Actions will deploy automatically
# 4. Wait ~5 minutes for deployment
# 5. Hard refresh browser (Ctrl+Shift+R)
# 6. Test with large image!
```

---

## 📊 Expected Results

**Before** (Current):
- ❌ 7.5MB image → HTTP 413
- ❌ 10MB+ image → Instant failure
- ❌ CORS error (side effect of 413)

**After** (Fixed):
- ✅ 7.5MB image → Success
- ✅ 10MB+ image → Success
- ✅ 50MB+ image → Success
- ✅ No CORS errors
- ✅ Real progress tracking
- ✅ Faster uploads

---

## 🆘 Troubleshooting

### Issue: S3 Upload Fails with CORS
**Solution**: Configure S3 CORS
```bash
cd backend
python3 setup_aws.py s3-cors
```

### Issue: "Photo not found in S3" after upload
**Cause**: S3 upload succeeded but confirmation failed
**Solution**: Check S3 bucket directly, photo should be there

### Issue: Duplicate detection not working
**Cause**: Still using base64 for hash calculation (this is correct!)
**Solution**: This is expected - duplicate detection needs base64

### Issue: Progress bar not working
**Cause**: Using `fetch()` API (doesn't support progress)
**Solution**: Use `XMLHttpRequest` as shown above

---

## 💡 Benefits of This Approach

1. **No Size Limit**: S3 supports up to 5GB per object
2. **Faster**: Direct upload, no Lambda processing
3. **Cheaper**: No data transfer through API Gateway/Lambda
4. **Scalable**: S3 handles concurrent uploads efficiently
5. **Better UX**: Real upload progress tracking
6. **Secure**: Presigned URLs expire after 1 hour

---

## 📞 Need Help?

If you encounter issues:
1. Check browser console for errors
2. Check CloudWatch logs for Lambda errors
3. Verify S3 CORS configuration
4. Test with direct API Gateway endpoint (bypassing CloudFront)

---

**STATUS**: Ready to implement! Backend is deployed and waiting for frontend update.

