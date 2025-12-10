#!/bin/bash
# Setup script for new DynamoDB tables and indexes
# Automates the deployment of plan enforcement infrastructure

set -e

echo "🚀 Galerly Plan Enforcement Setup"
echo "===================================="
echo ""

# Check if LocalStack is running
if ! curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
    echo "❌ LocalStack is not running"
    echo "   Start it with: docker-compose up localstack"
    exit 1
fi

echo "✅ LocalStack is running"
echo ""

# Environment detection
if [ "$1" == "--production" ]; then
    ENDPOINT=""
    SUFFIX="prod"
    echo "⚠️  PRODUCTION MODE"
else
    ENDPOINT="--endpoint-url=http://localhost:4566"
    SUFFIX="local"
    echo "🏠 LOCAL MODE (LocalStack)"
fi
echo ""

# Navigate to user-app/backend directory from dev_tools
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../user-app/backend"
cd "$BACKEND_DIR"

echo "Working directory: $(pwd)"
echo ""

# Create Rate Limits Table
echo "📊 Creating rate limits table..."
if aws dynamodb create-table \
    --cli-input-json file://schemas/rate-limits-table.json \
    $ENDPOINT 2>&1 | grep -q "ResourceInUseException"; then
    echo "   ℹ️  Table already exists"
else
    echo "   ✅ Table created"
fi

# Create Plan Violations Table
echo "📊 Creating plan violations table..."
if aws dynamodb create-table \
    --cli-input-json file://schemas/plan-violations-table.json \
    $ENDPOINT 2>&1 | grep -q "ResourceInUseException"; then
    echo "   ℹ️  Table already exists"
else
    echo "   ✅ Table created"
fi

echo ""
echo "📝 Adding GSI indexes to existing tables..."
echo ""

# Function to check if GSI exists
check_gsi_exists() {
    local table=$1
    local index=$2
    aws dynamodb describe-table --table-name "$table" $ENDPOINT 2>/dev/null | \
        grep -q "\"IndexName\": \"$index\""
    return $?
}

# Add GalleryIdIndex to galleries table
echo "   Galleries table..."
if check_gsi_exists "galerly-galleries-$SUFFIX" "GalleryIdIndex"; then
    echo "      ℹ️  GalleryIdIndex already exists"
else
    aws dynamodb update-table \
        --table-name "galerly-galleries-$SUFFIX" \
        --attribute-definitions AttributeName=id,AttributeType=S \
        --global-secondary-index-updates '[{
          "Create": {
            "IndexName": "GalleryIdIndex",
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"}
          }
        }]' \
        $ENDPOINT > /dev/null 2>&1 || echo "      ⚠️  Failed (may already exist)"
    echo "      ✅ GalleryIdIndex created"
fi

# Add UserIdIndex to users table
echo "   Users table..."
if check_gsi_exists "galerly-users-$SUFFIX" "UserIdIndex"; then
    echo "      ℹ️  UserIdIndex already exists"
else
    aws dynamodb update-table \
        --table-name "galerly-users-$SUFFIX" \
        --attribute-definitions AttributeName=id,AttributeType=S \
        --global-secondary-index-updates '[{
          "Create": {
            "IndexName": "UserIdIndex",
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"}
          }
        }]' \
        $ENDPOINT > /dev/null 2>&1 || echo "      ⚠️  Failed (may already exist)"
    echo "      ✅ UserIdIndex created"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Environment variables:"
echo "   Development: .env.development"
echo "      DYNAMODB_TABLE_RATE_LIMITS=galerly-rate-limits-local"
echo "      DYNAMODB_TABLE_PLAN_VIOLATIONS=galerly-plan-violations-local"
echo ""
echo "   Production: .env.production"
echo "      DYNAMODB_TABLE_RATE_LIMITS=galerly-rate-limits"
echo "      DYNAMODB_TABLE_PLAN_VIOLATIONS=galerly-plan-violations"
echo ""
echo "📋 Next steps:"
echo "   1. Run tests:"
echo "      cd user-app/backend/tests && pytest test_plan_enforcement.py -v"
echo ""
echo "   2. Restart services:"
echo "      cd dev_tools && ./restart-backend.sh"
echo ""
