# 🧪 Galerly Test Suite - Quick Reference

## ✅ What You Got

A complete testing framework with **comprehensive test coverage** integrated into CI/CD:

### Test Organization

```
backend/tests/
├── test_cdn.py            # CDN URL generation & CloudFront integration
├── test_endpoints.py      # API endpoint tests (auth, galleries, photos, etc.)
├── test_frontend.py       # Frontend JS validation
├── test_smoke.py          # End-to-end smoke tests
├── test_environment.py    # Environment variable tests
├── test_imports.py        # Handler import tests
├── test_response.py       # Response utility tests
├── test_image_security.py # Image security tests
└── test_config.py         # Configuration tests
```

## 🚀 How to Run

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only (fast)
pytest tests/ -v -m "not integration and not slow"

# CDN tests
pytest tests/test_cdn.py -v

# API endpoint tests
pytest tests/test_endpoints.py -v

# Frontend validation
pytest tests/test_frontend.py -v

# Integration tests (live AWS)
pytest tests/ -v -m "integration"
```

### Run with Coverage
```bash
pytest tests/ -v --cov=handlers --cov=utils --cov=api --cov-report=html
# Open htmlcov/index.html
```

## 📊 What Gets Tested

| Component | Tests | Status |
|-----------|-------|--------|
| **CDN URLs** | CloudFront URL generation | ✅ |
| **CloudFront** | Distribution, caching, headers | ✅ |
| **Lambda@Edge** | Pass-through (no 502/503) | ✅ |
| **Authentication** | Register, login, logout | ✅ |
| **Galleries** | Create, update, delete, list | ✅ |
| **Photos** | Upload via pre-signed URLs | ✅ |
| **Dashboard** | Statistics endpoints | ✅ |
| **Subscriptions** | Usage tracking | ✅ |
| **Frontend Config** | CDN_URL, API_URL configured | ✅ |
| **Frontend Structure** | All required files exist | ✅ |
| **Image URLs** | No hardcoded S3 URLs | ✅ |
| **JS Syntax** | No syntax errors | ✅ |
| **API Health** | Health check endpoint | ✅ |
| **User Journey** | Register → Gallery → Upload | ✅ |

## 🔄 CI/CD Integration

Tests run automatically on every push and pull request:

```
GitHub Actions Pipeline
├─ Stage 1: Validate Secrets
├─ Stage 2: Lint & Validate
├─ Stage 3: Setup AWS Infrastructure
├─ Stage 4: 🧪 COMPREHENSIVE TEST SUITE  ← Tests here!
│  ├─ Run Unit Tests
│  ├─ Run CDN Tests
│  ├─ Run Endpoint Tests
│  ├─ Run Frontend Validation Tests
│  ├─ Test Lambda Handler Imports
│  ├─ Run Integration Tests (optional)
│  └─ Generate Test Report & Coverage
├─ Stage 5: Deploy Frontend (only if tests pass)
├─ Stage 6: Deploy Backend (only if tests pass)
└─ Stage 7: Post-Deployment Tests
```

**Deployment is blocked if tests fail!**

## 🔍 Quick Diagnostics

### If Images Show "Not Found"
```bash
# Run CDN integration tests
cd backend
pytest tests/test_cdn.py -v

# Check these specific tests:
# ✅ test_cdn_url_basic - Are URLs formatted correctly?
# ✅ test_photo_urls_use_cdn - Do all URLs use CloudFront?
# ✅ test_cloudfront_domain_resolves - Is CDN active?
# ✅ test_lambda_edge_no_errors - Any 502/503 errors?
```

### If API Fails
```bash
# Run endpoint tests
cd backend
pytest tests/test_endpoints.py -v

# Check these specific tests:
# ✅ test_api_health - Is API responding?
# ✅ test_register_creates_user - Can register users?
# ✅ test_create_gallery - Can create galleries?
```

### If Frontend Has Issues
```bash
# Run frontend validation
cd backend
pytest tests/test_frontend.py -v

# Check these specific tests:
# ✅ test_config_has_cdn_url - CDN configured?
# ✅ test_no_duplicate_get_image_url - No duplicate functions?
# ✅ test_no_hardcoded_s3_urls - No S3 URLs in JS?
```

## 🎯 Test Coverage Map

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND                            │
│  • gallery.js          ✅ Validated                 │
│  • gallery-loader.js   ✅ No duplicate getImageUrl  │
│  • config.js           ✅ CDN URL configured         │
│  • All JS files        ✅ Syntax checked            │
└─────────────────┬───────────────────────────────────┘
                  │ HTTPS Requests
                  ▼
┌─────────────────────────────────────────────────────┐
│           CloudFront CDN (cdn.galerly.com)          │
│  ✅ Distribution status tested                      │
│  ✅ Caching behavior tested                         │
│  ✅ Lambda@Edge error detection                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              BACKEND API                             │
│  • utils/cdn_urls.py → ✅ URL generation tested     │
│  • handlers/*.py → ✅ All endpoints tested          │
│  • api.py routing → ✅ CORS & health tested         │
└─────────────────────────────────────────────────────┘
```

## 📈 Expected Results

### ✅ All Tests Passing
```
🧪 COMPREHENSIVE TEST SUITE
========================================
🌐 TESTING CDN & IMAGE URLS
✅ test_cdn_url_basic PASSED
✅ test_photo_urls_use_cdn PASSED
✅ CDN tests passed

📡 TESTING API ENDPOINTS
✅ test_register_creates_user PASSED
✅ test_create_gallery PASSED
✅ Endpoint tests passed

🎨 VALIDATING FRONTEND FILES
✅ test_config_has_cdn_url PASSED
✅ test_no_duplicate_get_image_url PASSED
✅ Frontend validation passed

========================================
✅ ALL TESTS COMPLETE!
========================================
```

### ❌ Some Tests Failing
The test output will show exactly which component failed:
```
❌ test_cdn_url_basic FAILED
   AssertionError: URL contains '.s3.amazonaws.com'
   
   → Fix: Check backend/utils/cdn_urls.py
   → Expected: https://cdn.galerly.com/...
   → Got: https://galerly-images-storage.s3.amazonaws.com/...
```

## 🛠️ Common Fixes

### Fix 1: Images Not Loading
**Tests Failed:** `test_cdn_url_*`, `test_photo_urls_use_cdn`

**Fix:**
```bash
# Check backend CDN URL generation
cat backend/utils/cdn_urls.py | grep "cdn.galerly.com"

# Check frontend config
cat frontend/js/config.js | grep "CDN_URL"

# Ensure no duplicate getImageUrl functions
grep -r "function getImageUrl" frontend/js/*.js
```

### Fix 2: Lambda@Edge 502 Errors
**Tests Failed:** `test_lambda_edge_no_errors`

**Fix:**
```bash
# Check Lambda@Edge logs
aws logs tail /aws/lambda/us-east-1.galerly-image-resize-edge --follow

# Verify Lambda is simple pass-through
cat lambda-edge/resize.js
```

### Fix 3: Endpoint Tests Fail
**Tests Failed:** `test_create_gallery`, `test_register_creates_user`

**Fix:**
```bash
# Check handler imports
cd backend
pytest tests/test_imports.py -v

# Verify environment variables
pytest tests/test_environment.py -v
```

## 📝 Viewing Test Results in CI/CD

1. Go to GitHub Actions
2. Click on the latest workflow run
3. Click on "🧪 Comprehensive Test Suite" job
4. Scroll through test output
5. Download artifacts (test-results, coverage-report) at bottom

## 🎓 Next Steps After Adding Features

When you add new features:

1. **Write tests first** (TDD approach)
2. **Run tests locally**:
   ```bash
   cd backend
   pytest tests/ -v
   ```
3. **Commit and push** - tests run automatically in CI/CD
4. **Check GitHub Actions** for test results
5. **Deployment happens automatically** if all tests pass

## 📚 Full Documentation

- **Comprehensive Guide**: `backend/tests/README.md`
- **CI/CD Pipeline**: `.github/workflows/deploy.yml` (Stage 4)
- **Test Files**: `backend/tests/`

## 🔑 Key Benefits

1. **Early Bug Detection** - Catches issues before deployment
2. **Confidence in Changes** - Know immediately if something breaks
3. **Documentation** - Tests serve as executable documentation
4. **Regression Prevention** - Old bugs can't come back
5. **Automated** - No manual testing needed
6. **Fast Feedback** - Results in minutes, not hours

## 🆘 Getting Help

If tests fail:

1. Read the error message carefully
2. Look at the test file to see what's being tested
3. Run the specific test locally: `pytest tests/test_cdn.py::test_cdn_url_basic -vv`
4. Check the logs in GitHub Actions
5. Review the documentation in `backend/tests/README.md`

**Your application now has enterprise-grade testing!** 🎉


## 📊 What Gets Tested

| Component | What's Tested | Pass/Fail |
|-----------|---------------|-----------|
| **CDN URLs** | CloudFront URL generation | ✅/❌ |
| **Authentication** | User register/login | ✅/❌ |
| **Galleries** | Create, update, delete, list | ✅/❌ |
| **Photos** | Upload via pre-signed URLs | ✅/❌ |
| **CloudFront** | Distribution status, caching | ✅/❌ |
| **Lambda@Edge** | Pass-through (no 502/503) | ✅/❌ |
| **S3 Access** | OAI security (403 on direct) | ✅/❌ |
| **Image URLs** | Consistency across stack | ✅/❌ |

## 🔍 Quick Diagnostics

### If Images Show "Not Found"
```bash
# Run CDN integration tests
python3 tests/test_cdn_integration.py

# Check these specific tests:
# ✅ CloudFront Distribution - Is CDN active?
# ✅ Lambda@Edge Pass-through - Any 502/503 errors?
# ✅ CDN URL Structure - Are URLs formatted correctly?
```

### If API Fails
```bash
# Run backend unit tests
cd backend && python3 tests/test_api.py

# Check these specific tests:
# ✅ CDN URL Generation - Backend generating CloudFront URLs?
# ✅ Photo Upload - Pre-signed URLs working?
# ✅ Gallery Creation - Can create galleries?
```

### If Authentication Fails
```bash
# Run smoke tests
python3 tests/smoke_tests.py

# Check these specific tests:
# ✅ User Registration - Can register new users?
# ✅ User Login - Can login with credentials?
# ✅ API Health - Is API responding?
```

## 🎯 Test Coverage Map

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND                            │
│  • gallery.js                                        │
│  • gallery-loader.js    → Uses getImageUrl()        │
│  • config.js           → CDN URL generation          │
└─────────────────┬───────────────────────────────────┘
                  │ HTTPS Requests
                  ▼
┌─────────────────────────────────────────────────────┐
│           CloudFront CDN (cdn.galerly.com)          │
│  ✅ Tested: Distribution status                     │
│  ✅ Tested: Caching behavior                        │
│  ✅ Tested: Performance                             │
└─────────────────┬───────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌─────────────────┐   ┌──────────────────┐
│ Lambda@Edge     │   │   S3 Origin      │
│ ✅ Pass-through │   │ ✅ OAI access    │
│ ✅ No errors    │   │ ✅ Security      │
└─────────────────┘   └──────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              BACKEND API                             │
│  • utils/cdn_urls.py → ✅ URL generation            │
│  • handlers/*.py → ✅ All endpoints                 │
└─────────────────────────────────────────────────────┘
```

## 📈 Expected Results

### ✅ All Tests Passing
```
🎉 All test suites passed!

Test Suites Run: 3
Passed: 3
Failed: 0
Success Rate: 100%
```

### ❌ Some Tests Failing
The test output will show exactly which component failed:
```
❌ CDN URL Structure: FAIL
   Expected: https://cdn.galerly.com/...
   Got: https://galerly-images-storage.s3.amazonaws.com/...
   
   → Fix: Check frontend/js/config.js getImageUrl()
```

## 🛠️ Common Fixes

### Fix 1: Images Not Loading
**Test Failed:** `CDN URL Structure`, `Image URL Consistency`

**Fix:**
```bash
# Check frontend uses CloudFront
grep -r "getImageUrl" frontend/js/*.js

# Should all use the global function from config.js
# Remove any duplicate getImageUrl() functions
```

### Fix 2: Lambda@Edge 502 Errors
**Test Failed:** `Lambda@Edge Pass-through`

**Fix:**
```bash
# Check Lambda@Edge logs
aws logs tail /aws/lambda/us-east-1.galerly-image-resize-edge --follow

# Verify Lambda is simple pass-through (no Sharp)
cat lambda-edge/resize.js
```

### Fix 3: S3 Access Issues
**Test Failed:** `S3 Origin Access`

**Fix:**
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket galerly-images-storage

# Should allow CloudFront OAI only
```

## 📝 Adding New Tests

When you add features, add tests:

```python
# backend/tests/test_api.py
def test_new_feature(self):
    """Test new feature description"""
    # Your test code here
    self.assertEqual(expected, actual)
```

Run tests to verify:
```bash
cd backend && python3 tests/test_api.py
```

## 🎓 Next Steps

1. **Run tests now** to establish baseline
2. **Fix any failures** using the diagnostic guides above
3. **Run tests after changes** to catch regressions
4. **Add to CI/CD** to automate testing on every push

## 📚 Full Documentation

See `docs/TESTING.md` for complete documentation including:
- Detailed test descriptions
- CI/CD integration
- Debugging guides
- Contributing guidelines

