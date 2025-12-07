#!/bin/bash
# Pre-deployment validation script
# Ensures all requirements are met before containerization

set -e

echo "🔍 Galerly Pre-Deployment Validation"
echo "====================================="
echo ""

# Track overall status
VALIDATION_FAILED=0

# Step 1: Environment validation
echo "📋 Step 1: Checking environment configuration..."
echo "================================================"

# Check if root .env.development exists
if [ ! -f ".env.development" ]; then
    echo "❌ .env.development not found in project root"
    VALIDATION_FAILED=1
else
    echo "✅ .env.development exists"
fi

# Load environment variables from root
if [ -f ".env.development" ]; then
    set -a
    source .env.development
    set +a
fi

cd user-app/backend

# Check critical environment variables
REQUIRED_VARS=(
    "AWS_REGION"
    "ENVIRONMENT"
    "S3_BUCKET"
    "S3_PHOTOS_BUCKET"
    "S3_RENDITIONS_BUCKET"
    "DYNAMODB_TABLE_USERS"
    "DYNAMODB_TABLE_GALLERIES"
    "DYNAMODB_TABLE_PHOTOS"
    "DYNAMODB_TABLE_RAW_VAULT"
    "DYNAMODB_TABLE_SEO_SETTINGS"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Missing environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    VALIDATION_FAILED=1
else
    echo "✅ All required environment variables are set"
fi

echo ""

# Step 2: Run pre-deployment tests
echo "🧪 Step 2: Running pre-deployment validation tests..."
echo "======================================================"
if [ -d "venv" ]; then
    source venv/bin/activate
fi

if command -v pytest &> /dev/null; then
    pytest tests/test_pre_deployment.py -v
    if [ $? -ne 0 ]; then
        echo "❌ Pre-deployment tests failed"
        VALIDATION_FAILED=1
    else
        echo "✅ Pre-deployment tests passed"
    fi
else
    echo "⚠️  pytest not installed, skipping validation tests"
    echo "   Install: pip install pytest"
fi

cd ../..
echo ""

# Step 3: Run all backend unit tests
echo "🧪 Step 3: Running backend unit tests..."
echo "========================================="
cd user-app/backend

if [ -d "venv" ]; then
    source venv/bin/activate
fi

if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short
    if [ $? -ne 0 ]; then
        echo "❌ Backend tests failed"
        VALIDATION_FAILED=1
    else
        echo "✅ Backend tests passed"
    fi
else
    echo "⚠️  pytest not installed, skipping backend tests"
    VALIDATION_FAILED=1
fi

cd ../..
echo ""

# Step 4: Run frontend tests
echo "🧪 Step 4: Running frontend tests..."
echo "====================================="
cd user-app/frontend

if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found, installing dependencies..."
    npm install
fi

npm test -- --run
if [ $? -ne 0 ]; then
    echo "❌ Frontend tests failed"
    VALIDATION_FAILED=1
else
    echo "✅ Frontend tests passed"
fi

cd ../..
echo ""

# Step 5: Validate file structure
echo "📁 Step 5: Validating file structure..."
echo "========================================"

REQUIRED_FILES=(
    "user-app/backend/setup_dynamodb.py"
    "user-app/backend/init_features.py"
    "user-app/backend/utils/raw_processor.py"
    "user-app/backend/utils/video_transcoder.py"
    "user-app/backend/handlers/raw_vault_handler.py"
    "user-app/backend/handlers/seo_handler.py"
    "user-app/backend/tests/test_raw_processor.py"
    "user-app/backend/tests/test_raw_vault_handler.py"
    "user-app/backend/tests/test_video_transcoder.py"
    "user-app/backend/tests/test_seo_handler.py"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "❌ Missing required files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    VALIDATION_FAILED=1
else
    echo "✅ All required files exist"
fi

echo ""

# Step 6: Check Docker configuration
echo "🐳 Step 6: Validating Docker configuration..."
echo "=============================================="

if [ ! -f "docker/docker-compose.localstack.yml" ]; then
    echo "❌ docker-compose.localstack.yml not found"
    VALIDATION_FAILED=1
else
    echo "✅ docker-compose.localstack.yml exists"
fi

if [ ! -f "user-app/backend/Dockerfile.local" ]; then
    echo "❌ Backend Dockerfile.local not found"
    VALIDATION_FAILED=1
else
    echo "✅ Backend Dockerfile.local exists"
fi

if [ ! -f "user-app/frontend/Dockerfile.local" ]; then
    echo "❌ Frontend Dockerfile.local not found"
    VALIDATION_FAILED=1
else
    echo "✅ Frontend Dockerfile.local exists"
fi

echo ""

# Final summary
echo "================================================"
echo "VALIDATION SUMMARY"
echo "================================================"

if [ $VALIDATION_FAILED -eq 0 ]; then
    echo "✅ All validation checks passed!"
    echo ""
    echo "System is ready for containerization."
    echo "You can now run: ./dev_tools/dev-rebuild.sh"
    echo ""
    exit 0
else
    echo "❌ Validation failed!"
    echo ""
    echo "Please fix the issues above before proceeding."
    echo "Do not build containers until all tests pass."
    echo ""
    exit 1
fi
