#!/bin/bash
# Production Deployment Checklist Script
# Ensures all production requirements are met before deployment

set -e

echo "🚀 Galerly Production Deployment Checklist"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track status
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

# Helper function
check_status() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check 1: Environment file exists
echo "📋 Checking configuration files..."
echo "===================================="
if [ -f "user-app/backend/.env" ]; then
    check_status 0 "Production .env file exists"
else
    check_status 1 "Production .env file missing"
fi

# Check 2: Load environment
if [ -f "user-app/backend/.env" ]; then
    set -a
    source user-app/backend/.env
    set +a
fi

echo ""

# Check 3: Required environment variables
echo "🔧 Checking environment variables..."
echo "======================================"

REQUIRED_VARS=(
    "AWS_REGION"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "S3_BUCKET"
    "S3_PHOTOS_BUCKET"
    "S3_RENDITIONS_BUCKET"
    "DYNAMODB_TABLE_USERS"
    "DYNAMODB_TABLE_GALLERIES"
    "DYNAMODB_TABLE_PHOTOS"
    "DYNAMODB_TABLE_RAW_VAULT"
    "DYNAMODB_TABLE_SEO_SETTINGS"
    "STRIPE_SECRET_KEY"
    "JWT_SECRET"
    "FROM_EMAIL"
    "SMTP_HOST"
    "SMTP_USER"
    "SMTP_PASSWORD"
)

MISSING_VARS=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        check_status 1 "$var is not set"
        MISSING_VARS=$((MISSING_VARS + 1))
    fi
done

if [ $MISSING_VARS -eq 0 ]; then
    check_status 0 "All required environment variables are set"
fi

echo ""

# Check 4: AWS credentials are valid
echo "🔐 Validating AWS credentials..."
echo "=================================="
if command -v aws &> /dev/null; then
    aws sts get-caller-identity &> /dev/null
    if [ $? -eq 0 ]; then
        check_status 0 "AWS credentials are valid"
    else
        check_status 1 "AWS credentials are invalid"
    fi
else
    warning "AWS CLI not installed, skipping credential check"
fi

echo ""

# Check 5: DynamoDB tables exist
echo "🗄️  Checking DynamoDB tables..."
echo "================================"
if command -v aws &> /dev/null && [ ! -z "$DYNAMODB_TABLE_USERS" ]; then
    TABLES_TO_CHECK=(
        "$DYNAMODB_TABLE_USERS"
        "$DYNAMODB_TABLE_GALLERIES"
        "$DYNAMODB_TABLE_PHOTOS"
        "$DYNAMODB_TABLE_RAW_VAULT"
        "$DYNAMODB_TABLE_SEO_SETTINGS"
    )
    
    TABLES_MISSING=0
    for table in "${TABLES_TO_CHECK[@]}"; do
        aws dynamodb describe-table --table-name "$table" &> /dev/null
        if [ $? -eq 0 ]; then
            check_status 0 "Table $table exists"
        else
            check_status 1 "Table $table does not exist"
            TABLES_MISSING=$((TABLES_MISSING + 1))
        fi
    done
    
    if [ $TABLES_MISSING -gt 0 ]; then
        warning "Run: cd user-app/backend && python setup_dynamodb.py create"
    fi
else
    warning "Skipping table check (AWS CLI not installed or table names not set)"
fi

echo ""

# Check 6: S3 buckets exist
echo "📦 Checking S3 buckets..."
echo "=========================="
if command -v aws &> /dev/null && [ ! -z "$S3_BUCKET" ]; then
    BUCKETS_TO_CHECK=(
        "$S3_BUCKET"
        "$S3_PHOTOS_BUCKET"
        "$S3_RENDITIONS_BUCKET"
    )
    
    BUCKETS_MISSING=0
    for bucket in "${BUCKETS_TO_CHECK[@]}"; do
        aws s3 ls "s3://$bucket" &> /dev/null
        if [ $? -eq 0 ]; then
            check_status 0 "Bucket $bucket exists"
        else
            check_status 1 "Bucket $bucket does not exist"
            BUCKETS_MISSING=$((BUCKETS_MISSING + 1))
        fi
    done
    
    if [ $BUCKETS_MISSING -gt 0 ]; then
        warning "Create buckets manually or via infrastructure as code"
    fi
else
    warning "Skipping bucket check (AWS CLI not installed or bucket names not set)"
fi

echo ""

# Check 7: All tests pass
echo "🧪 Running test suite..."
echo "========================="
cd user-app/backend

if [ -d "venv" ]; then
    source venv/bin/activate
fi

if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short &> /tmp/galerly-test-output.txt
    if [ $? -eq 0 ]; then
        check_status 0 "All backend tests pass"
    else
        check_status 1 "Backend tests failed"
        warning "See /tmp/galerly-test-output.txt for details"
    fi
else
    check_status 1 "pytest not installed"
fi

cd ../..

echo ""

# Check 8: Dependencies installed
echo "📚 Checking dependencies..."
echo "============================"
cd user-app/backend
if [ -f "requirements.txt" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip freeze | grep -q "Flask"
        check_status $? "Backend dependencies installed"
    else
        warning "Virtual environment not found"
    fi
fi
cd ../..

cd user-app/frontend
if [ -f "package.json" ]; then
    if [ -d "node_modules" ]; then
        check_status 0 "Frontend dependencies installed"
    else
        check_status 1 "Frontend node_modules missing"
        warning "Run: npm install"
    fi
fi
cd ../..

echo ""

# Check 9: Security checks
echo "🔒 Running security checks..."
echo "=============================="
cd user-app/backend
SECURITY_ISSUES=0

# Check for exposed secrets in .env
if [ -f ".env" ]; then
    if grep -q "AKIA" .env; then
        warning ".env contains AWS access key - ensure .gitignore is configured"
    fi
    if grep -q "sk_live_" .env; then
        warning ".env contains Stripe live key - ensure .gitignore is configured"
    fi
fi

# Check .gitignore
if [ ! -f "../../.gitignore" ]; then
    check_status 1 ".gitignore missing"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
else
    if grep -q ".env" ../../.gitignore; then
        check_status 0 ".env is in .gitignore"
    else
        check_status 1 ".env is NOT in .gitignore"
        SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
    fi
fi

cd ../..

echo ""

# Final summary
echo "================================================"
echo "DEPLOYMENT READINESS SUMMARY"
echo "================================================"
echo ""
echo "Total checks: $CHECKS_TOTAL"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ System is ready for production deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review DEPLOYMENT_READY.md for deployment guide"
    echo "2. Set up CI/CD pipeline with GitHub Actions"
    echo "3. Configure production monitoring and alerts"
    echo "4. Set up backup and disaster recovery"
    echo "5. Deploy to production environment"
    echo ""
    exit 0
else
    echo -e "${RED}❌ System is NOT ready for production deployment${NC}"
    echo ""
    echo "Please fix the issues above before deploying."
    echo ""
    exit 1
fi
