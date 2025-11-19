# Galerly Test Suite

Comprehensive test coverage for the entire Galerly application integrated into the CI/CD pipeline.

## 📋 Test Structure

```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_environment.py      # Environment variable validation
├── test_imports.py          # Handler and utility import tests
├── test_response.py         # Response utility tests
├── test_image_security.py   # Image security tests
├── test_config.py           # Configuration tests
├── test_cdn.py              # CDN URL generation & CloudFront integration
├── test_endpoints.py        # API endpoint tests
├── test_frontend.py         # Frontend JS validation tests
└── test_smoke.py            # End-to-end smoke tests
```

## 🚀 Quick Start

### Run All Tests Locally
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

# Integration tests (hits live AWS)
pytest tests/ -v -m "integration"

# End-to-end smoke tests
pytest tests/test_smoke.py -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=handlers --cov=utils --cov=api --cov-report=html
# Open htmlcov/index.html to see coverage report
```

## 🧪 Test Categories

### 1. **Environment Tests** (`test_environment.py`)
- ✅ AWS credentials configured
- ✅ DynamoDB table names set
- ✅ S3 bucket names set
- ✅ CloudFront CDN domain configured
- ✅ Stripe keys configured
- ✅ SMTP configuration

### 2. **Import Tests** (`test_imports.py`)
- ✅ All handlers import successfully
- ✅ All utility modules import successfully
- ✅ Required functions exist in handlers

### 3. **Response Tests** (`test_response.py`)
- ✅ Response structure correct
- ✅ CORS headers properly set
- ✅ Security headers included
- ✅ Error responses formatted correctly

### 4. **Image Security Tests** (`test_image_security.py`)
- ✅ Invalid file formats rejected
- ✅ Empty images rejected
- ✅ Magic bytes validated
- ✅ Executable extensions blocked

### 5. **Configuration Tests** (`test_config.py`)
- ✅ DynamoDB tables configured
- ✅ S3 buckets configured
- ✅ Environment variables used correctly

### 6. **CDN Tests** (`test_cdn.py`) ⭐ NEW
- ✅ CDN URL generation
- ✅ Photo URL variants (thumbnail, medium, small)
- ✅ CloudFront domain resolution (integration)
- ✅ CloudFront headers present (integration)
- ✅ Lambda@Edge error detection (502/503)
- ✅ No hardcoded S3 URLs

### 7. **API Endpoint Tests** (`test_endpoints.py`) ⭐ NEW
- ✅ Authentication endpoints (register, login)
- ✅ Gallery endpoints (create, list, get, update, delete)
- ✅ Photo endpoints (upload URL generation)
- ✅ Subscription endpoints (usage tracking)
- ✅ Dashboard endpoints (stats)
- ✅ API routing logic
- ✅ CORS preflight handling

### 8. **Frontend Validation Tests** (`test_frontend.py`) ⭐ NEW
- ✅ Required HTML files exist
- ✅ Required JS files exist
- ✅ CSS files exist
- ✅ `config.js` has CDN_URL configured
- ✅ `config.js` has API_URL configured
- ✅ `getImageUrl` function exists and uses CDN
- ✅ No duplicate `getImageUrl` functions in other files
- ✅ JS files have no syntax errors
- ✅ No hardcoded S3 URLs in JS files

### 9. **End-to-End Smoke Tests** (`test_smoke.py`) ⭐ NEW
- ✅ API health check
- ✅ API CORS headers
- ✅ CDN domain accessible
- ✅ CloudFront headers present
- ✅ Complete user journey (register → create gallery → upload → list)
- ✅ Image URL consistency
- ✅ AWS resources configured

## 🔄 CI/CD Integration

Tests run automatically in the GitHub Actions pipeline on every push and pull request.

### Pipeline Stage 4: Comprehensive Test Suite

The tests are integrated into `.github/workflows/deploy.yml` as Stage 4:

```yaml
test-backend:
  name: 🧪 Comprehensive Test Suite
  needs: [setup-aws-infrastructure]
  steps:
    - Run Unit Tests
    - Run CDN Tests
    - Run Endpoint Tests
    - Run Frontend Validation Tests
    - Test Lambda Handler Imports
    - Run Integration Tests (Optional, non-blocking)
    - Generate Test Report
    - Upload Test Results & Coverage
```

### Test Execution Flow

```
┌─────────────────────────────────────┐
│  Stage 1: Validate Secrets          │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Stage 2: Lint & Validate           │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Stage 3: Setup AWS Infrastructure  │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Stage 4: COMPREHENSIVE TEST SUITE  │  ← Tests run here!
│  ├─ Unit Tests                      │
│  ├─ CDN Tests                       │
│  ├─ Endpoint Tests                  │
│  ├─ Frontend Validation             │
│  ├─ Handler Import Tests            │
│  └─ Integration Tests (optional)    │
└──────────┬──────────────────────────┘
           │
           ▼ (Only if tests pass)
┌─────────────────────────────────────┐
│  Stage 5: Deploy Frontend           │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Stage 6: Deploy Backend            │
└─────────────────────────────────────┘
```

**Deployment is blocked if tests fail!**

## 📊 Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.integration` - Tests that hit live AWS resources
- `@pytest.mark.slow` - Tests that take a long time to run

### Running Specific Markers
```bash
# Skip integration tests (fast, unit tests only)
pytest tests/ -v -m "not integration"

# Run only integration tests
pytest tests/ -v -m "integration"

# Skip slow tests
pytest tests/ -v -m "not slow"
```

## 🎯 Test Coverage

Current test coverage includes:

| Component | Coverage | Test File |
|-----------|----------|-----------|
| CDN URL Generation | ✅ 100% | `test_cdn.py` |
| CloudFront Integration | ✅ Integration | `test_cdn.py` |
| Auth Endpoints | ✅ Unit | `test_endpoints.py` |
| Gallery Endpoints | ✅ Unit | `test_endpoints.py` |
| Photo Endpoints | ✅ Unit | `test_endpoints.py` |
| Frontend Config | ✅ Validation | `test_frontend.py` |
| Frontend Structure | ✅ Validation | `test_frontend.py` |
| Image URLs | ✅ Consistency | `test_smoke.py` |
| API Health | ✅ Integration | `test_smoke.py` |
| User Journey | ✅ E2E | `test_smoke.py` |

## 🐛 Debugging Failed Tests

### Common Issues

#### 1. Import Errors
**Symptom:** `ModuleNotFoundError` or import failures

**Fix:**
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock requests
```

#### 2. Environment Variables Missing
**Symptom:** Tests fail with "environment variable not set"

**Fix:** Ensure all required environment variables are set (in CI/CD, these come from GitHub Secrets)
```bash
export CDN_DOMAIN="cdn.galerly.com"
export AWS_REGION="us-east-1"
# ... etc
```

#### 3. Integration Tests Fail
**Symptom:** Tests marked with `@pytest.mark.integration` fail

**Reason:** Integration tests require live AWS resources

**Fix:** 
- Ensure AWS credentials are configured
- Run integration tests separately: `pytest -m integration`
- Skip integration tests locally: `pytest -m "not integration"`

#### 4. Frontend Tests Fail
**Symptom:** `test_frontend.py` fails with "file not found"

**Fix:** Run tests from `backend/` directory:
```bash
cd backend
pytest tests/test_frontend.py -v
```

## 📈 Adding New Tests

### 1. Create New Test File
```python
# backend/tests/test_myfeature.py
import pytest

class TestMyFeature:
    """Test my new feature"""
    
    def test_feature_works(self):
        """Test that feature works correctly"""
        # Your test code here
        assert True
```

### 2. Use Fixtures from conftest.py
```python
def test_with_fixtures(mock_user, mock_gallery):
    """Test using fixtures"""
    assert mock_user['id'] == 'test-user-123'
    assert mock_gallery['user_id'] == 'test-user-123'
```

### 3. Mark Tests Appropriately
```python
@pytest.mark.integration
def test_live_aws():
    """Test that hits live AWS"""
    pass

@pytest.mark.slow
def test_takes_long_time():
    """Test that is slow"""
    pass
```

### 4. Run Your New Tests
```bash
pytest tests/test_myfeature.py -v
```

## 🔍 Test Reports

After each CI/CD run, test results are uploaded as artifacts:

- **Test Results** (`junit.xml`) - 30 day retention
- **Coverage Report** (`htmlcov/`) - 30 day retention

View these in GitHub Actions → Workflow Run → Artifacts

## ✅ Best Practices

1. **Write Tests First** - TDD approach catches issues early
2. **Keep Tests Fast** - Mark slow tests with `@pytest.mark.slow`
3. **Mock External Services** - Use `unittest.mock` for AWS services in unit tests
4. **Test Real Integration** - Use `@pytest.mark.integration` for live AWS tests
5. **Descriptive Names** - Test names should describe what they test
6. **One Assert Per Test** - Each test should verify one thing
7. **Use Fixtures** - Reuse test data via `conftest.py` fixtures

## 🆘 Getting Help

If tests fail and you can't figure out why:

1. Check the test output for specific error messages
2. Run tests locally with `-vv` for verbose output
3. Check GitHub Actions logs for the failed test
4. Review the test file to understand what's being tested
5. Ensure all dependencies are installed

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [GitHub Actions - Testing](https://docs.github.com/en/actions/automating-builds-and-tests)
