# Galerly CI/CD & Automation Documentation

## 📁 File Organization

### Docker Configuration (`docker/`)
```
docker/
├── Dockerfile.test              # Test container definition
├── docker-compose.test.yml      # Test orchestration
└── docker-compose.localstack.yml # Local AWS environment
```

### CI/CD Workflows (`.github/workflows/`)
```
.github/workflows/
├── backend-tests.yml            # Backend test automation
└── full-test-suite.yml          # Complete test suite
```

### Operational Scripts (`scripts/`)
```
scripts/
├── run-tests.sh                 # Automated test runner
├── start-localstack.sh          # Start local AWS
├── stop-localstack.sh           # Stop local AWS
├── auto-backup-s3.sh            # S3 backup automation
├── backup-localstack-s3.sh      # LocalStack backup
├── restore-localstack-s3.sh     # LocalStack restore
├── run-gallery-cleanup.sh       # Scheduled cleanup
├── generate-frontend-config.sh  # Config generation
└── cleanup-background-processes.sh # Process cleanup
```

## 🚀 Quick Start

### Run All Tests
```bash
./scripts/run-tests.sh
```

### Run Specific Test Suites
```bash
# Backend tests only
docker-compose -f docker/docker-compose.test.yml run --rm backend-tests

# Integration tests only
docker-compose -f docker/docker-compose.test.yml run --rm integration-tests

# Complete suite
docker-compose -f docker/docker-compose.test.yml run --rm all-tests
```

### Local Development
```bash
# Start LocalStack (local AWS)
./scripts/start-localstack.sh

# Stop LocalStack
./scripts/stop-localstack.sh

# Backup LocalStack S3 data
./scripts/backup-localstack-s3.sh

# Restore LocalStack S3 data
./scripts/restore-localstack-s3.sh
```

## 🐳 Docker Configuration

### Test Container (`docker/Dockerfile.test`)
- Python 3.11 slim base
- All test dependencies
- Pytest with coverage
- Parallel execution support

### Test Orchestration (`docker/docker-compose.test.yml`)
**Services:**
- `backend-tests` - 478 backend tests
- `integration-tests` - 20 workflow tests
- `all-tests` - Complete suite with runner

**Features:**
- Volume mounts for live code
- Test result artifacts
- Coverage HTML reports
- Parallel execution

### LocalStack (`docker/docker-compose.localstack.yml`)
- Local AWS services
- DynamoDB, S3, Lambda, etc.
- Persistent data storage
- Network isolation

## 🔄 GitHub Actions

### Backend Tests Workflow

**File**: `.github/workflows/backend-tests.yml`

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Changes in `backend/**` or `docker/**`

**Matrix Testing:**
- Python 3.9, 3.10, 3.11

**Steps:**
1. Checkout code
2. Setup Python
3. Cache dependencies
4. Install dependencies
5. Run tests with coverage
6. Upload to Codecov
7. Check 80% threshold

### Full Test Suite Workflow

**File**: `.github/workflows/full-test-suite.yml`

**Triggers:**
- Push to `main`
- Pull requests to `main`
- Daily at 2 AM UTC (cron)

**Jobs:**
1. Backend tests (478 tests)
2. Integration tests (20 workflows)
3. Test summary generation

## 📊 Test Organization

### Backend Tests (`backend/tests/`)
18 test files with specific names:

| File | Tests | Coverage |
|------|-------|----------|
| `test_auth_handler.py` | 42 | Authentication |
| `test_gallery_handler.py` | 49 | Gallery CRUD |
| `test_client_handler.py` | 28 | Client access |
| `test_photo_handler.py` | 76 | Photo operations |
| `test_billing_handler.py` | 54 | Billing & subscriptions |
| `test_analytics_handler.py` | 41 | Analytics tracking |
| `test_cache.py` | 30 | Cache utility |
| `test_dashboard_handler.py` | 3 | Dashboard stats |
| `test_profile_handler.py` | 5 | Profile management |
| `test_newsletter_handler.py` | 7 | Newsletter |
| `test_contact_handler.py` | 6 | Contact form |
| `test_notification_handler.py` | 10 | Notifications |
| `test_client_favorites_handler.py` | 12 | Favorites |
| `test_client_feedback_handler.py` | 11 | Feedback |
| `test_visitor_tracking_handler.py` | 17 | Visitor analytics |
| `test_refund_handler.py` | 15 | Refunds |
| `test_upload_portfolio_handlers.py` | 52 | Uploads/Portfolio |
| `test_integration_workflows.py` | 20 | End-to-end |

**Total: 478 tests**

## 🛠️ Scripts Reference

### `run-tests.sh`
Automated test runner with colored output

**Usage:**
```bash
./scripts/run-tests.sh
```

**Features:**
- Builds Docker containers
- Runs backend tests
- Runs integration tests
- Generates coverage reports
- Colored output
- Exit codes for CI

### `start-localstack.sh`
Start local AWS environment

**Usage:**
```bash
./scripts/start-localstack.sh
```

**Services Started:**
- DynamoDB
- S3
- Lambda
- API Gateway
- CloudWatch

### `stop-localstack.sh`
Stop LocalStack gracefully

**Usage:**
```bash
./scripts/stop-localstack.sh
```

### `auto-backup-s3.sh`
Automated S3 backup with rotation

**Usage:**
```bash
./scripts/auto-backup-s3.sh
```

**Features:**
- Backs up to `localstack_data/s3_backup/`
- Timestamp-based naming
- Automatic cleanup of old backups

## 📈 Test Results

### Locations
- **JUnit XML**: `test-results/junit.xml`
- **Coverage XML**: `backend/coverage.xml`
- **Coverage HTML**: `backend/htmlcov/index.html`

### Viewing Coverage
```bash
# Generate and open coverage report
cd backend
pytest tests/ --cov=handlers --cov=utils --cov-report=html
open htmlcov/index.html
```

## 🎯 Best Practices

### Running Tests Locally
1. Always run `./scripts/run-tests.sh` before pushing
2. Check coverage reports for gaps
3. Ensure 80%+ coverage maintained
4. Fix failing tests immediately

### CI/CD Integration
1. Tests run automatically on push/PR
2. Merge blocked if tests fail
3. Coverage threshold enforced
4. Daily scheduled runs catch regressions

### Docker Usage
1. Use `docker-compose` for test consistency
2. Volume mount for live development
3. Results captured in `test-results/`
4. Clean containers regularly

## 🔧 Troubleshooting

### Tests Fail Locally
```bash
# Clean Docker cache
docker-compose -f docker/docker-compose.test.yml down -v
docker system prune -f

# Rebuild containers
docker-compose -f docker/docker-compose.test.yml build --no-cache

# Run tests again
./scripts/run-tests.sh
```

### GitHub Actions Fail
1. Check workflow logs in Actions tab
2. Verify Python version compatibility
3. Check for missing dependencies
4. Test locally with same Python version

### LocalStack Issues
```bash
# Stop LocalStack
./scripts/stop-localstack.sh

# Clean data
rm -rf localstack_data/state/*

# Restart
./scripts/start-localstack.sh
```

## 📝 Summary

✅ **Organized Structure**
- Docker files in `docker/`
- Scripts in `scripts/`
- Workflows in `.github/workflows/`
- Tests in `backend/tests/`

✅ **Automated Testing**
- 478 backend tests
- 20 integration tests
- 100% endpoint coverage
- CI/CD integrated

✅ **Easy to Use**
- Single command: `./scripts/run-tests.sh`
- Clear documentation
- Troubleshooting guides
- Professional organization

All automation files are now properly organized and easy to maintain! 🎉

