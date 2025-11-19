# Galerly Testing Suite

Comprehensive test suite for Galerly application covering backend APIs, CDN integration, and end-to-end user flows.

## 📋 Test Coverage

### 1. **Backend Unit Tests** (`backend/tests/test_api.py`)
Tests individual API handlers and utilities in isolation.

**Coverage:**
- ✅ CDN URL generation (`utils/cdn_urls.py`)
- ✅ Authentication (register, login, logout)
- ✅ Gallery management (create, update, delete, list)
- ✅ Photo uploads (pre-signed URLs)
- ✅ Email utilities
- ✅ Subscription limits and usage tracking

**Run:**
```bash
cd backend
python3 tests/test_api.py
```

### 2. **Image CDN Integration Tests** (`tests/test_cdn_integration.py`)
Tests CloudFront, S3, and Lambda@Edge integration.

**Coverage:**
- ✅ CloudFront distribution status
- ✅ Lambda@Edge pass-through functionality
- ✅ S3 origin access (OAI verification)
- ✅ CDN URL structure validation
- ✅ Caching behavior
- ✅ Performance (response times)
- ✅ Image format support
- ✅ CORS headers

**Run:**
```bash
python3 tests/test_cdn_integration.py
```

### 3. **End-to-End Smoke Tests** (`tests/smoke_tests.py`)
Tests critical user flows through actual API endpoints.

**Coverage:**
- ✅ API health check
- ✅ CDN connectivity
- ✅ User registration flow
- ✅ Gallery creation and retrieval
- ✅ Photo upload (pre-signed URLs)
- ✅ CDN URL generation
- ✅ Subscription limits
- ✅ Image URL consistency (backend vs frontend)
- ✅ Resource cleanup

**Run:**
```bash
python3 tests/smoke_tests.py
```

## 🚀 Quick Start

### Run All Tests
```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

### Run Individual Test Suites
```bash
# Backend unit tests
cd backend && python3 tests/test_api.py

# CDN integration tests
python3 tests/test_cdn_integration.py

# Smoke tests
python3 tests/smoke_tests.py
```

## 🔧 Configuration

### Environment Variables
```bash
# For testing
export AWS_REGION=us-east-1
export S3_PHOTOS_BUCKET=galerly-images-storage-test
export CDN_DOMAIN=cdn.galerly.com
export JWT_SECRET=test-secret-key
```

### API Endpoints
Update in `tests/smoke_tests.py`:
```python
API_BASE_URL = "https://api.galerly.com/v1"  # Your API Gateway URL
CDN_BASE_URL = "https://cdn.galerly.com"     # Your CloudFront domain
```

## 📊 Test Output

### Example Output
```
🧪 GALERLY TEST SUITE
==================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Running: Backend Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CDN URL Generation: PASS
✅ Photo URLs Generation: PASS
✅ User Registration: PASS
✅ Gallery Creation: PASS
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 FINAL TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test Suites Run: 3
Passed: 3
Failed: 0
==================================

🎉 All test suites passed!
```

## 🐛 Debugging Failed Tests

### Common Issues

#### 1. **Image Not Found (404)**
**Symptom:** CDN tests fail with 404 errors

**Fix:**
```bash
# Verify CloudFront distribution
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='Galerly Image CDN']"

# Check S3 bucket
aws s3 ls s3://galerly-images-storage/

# Test direct S3 access (should be 403 for OAI)
curl -I https://galerly-images-storage.s3.amazonaws.com/test.jpg
```

#### 2. **Lambda@Edge 502/503 Errors**
**Symptom:** CDN tests fail with server errors

**Fix:**
```bash
# Check Lambda@Edge logs (logs appear in region where executed)
aws logs tail /aws/lambda/us-east-1.galerly-image-resize-edge --follow

# Verify Lambda@Edge is attached
aws cloudfront get-distribution-config --id YOUR_DIST_ID \
  --query 'DistributionConfig.DefaultCacheBehavior.LambdaFunctionAssociations'
```

#### 3. **Authentication Failures**
**Symptom:** API tests fail with 401 errors

**Fix:**
```bash
# Verify JWT_SECRET environment variable
echo $JWT_SECRET

# Check user exists in DynamoDB
aws dynamodb scan --table-name galerly-users --limit 5
```

#### 4. **CDN URL Mismatch**
**Symptom:** Images load from S3 instead of CloudFront

**Fix:**
- Check `backend/utils/cdn_urls.py` - should return `https://cdn.galerly.com/...`
- Check `frontend/js/config.js` - `CDN_URL` should be `https://cdn.galerly.com`
- Verify no duplicate `getImageUrl()` functions in frontend

## 📈 CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install requests unittest-xml-reporting
      
      - name: Run tests
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: ./scripts/run_tests.sh
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-reports/
```

## 🔍 Test Checklist

Use this checklist to verify all systems are working:

### Backend API
- [ ] API responds to health check
- [ ] User can register
- [ ] User can login
- [ ] Gallery can be created
- [ ] Photos can be uploaded
- [ ] CDN URLs are generated correctly

### Image CDN
- [ ] CloudFront distribution is active
- [ ] Lambda@Edge is functioning (no 502/503)
- [ ] S3 access is via OAI only (403 on direct access)
- [ ] Images load from `cdn.galerly.com`
- [ ] Caching is working (X-Cache: Hit)

### Frontend Integration
- [ ] Images load in gallery view
- [ ] Thumbnails display correctly
- [ ] Lightbox shows full images
- [ ] Download works
- [ ] All images use CloudFront URLs

## 📚 Additional Resources

- [Backend API Documentation](../backend/README.md)
- [CloudFront Setup Guide](CLOUDFRONT_QUICKSTART.md)
- [Image CDN Architecture](IMAGE_CDN_ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## 🆘 Support

If tests fail and you can't resolve the issue:

1. Check the test output for specific error messages
2. Review CloudWatch logs for Lambda functions
3. Verify AWS resources are deployed correctly
4. Check GitHub Actions logs if running in CI/CD

## 📝 Contributing

When adding new features, please add corresponding tests:

1. **Unit tests** for new handlers/utilities
2. **Integration tests** for CDN changes
3. **Smoke tests** for new user flows

Run all tests before committing:
```bash
./scripts/run_tests.sh
```

