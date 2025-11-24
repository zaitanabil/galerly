#!/bin/bash
# Galerly LocalStack - Complete Local Development Setup
# Starts all services for local development with LocalStack
# All values from .env.local

set -e

echo "🚀 Starting Galerly LocalStack Development Environment"
echo "======================================================"
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose."
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Check for .env.local file
if [ ! -f backend/.env.local ]; then
    echo "❌ backend/.env.local not found"
    echo "   Copy backend/.env.local.template to backend/.env.local and configure"
    exit 1
fi

echo "✅ Environment configuration found"
echo ""

# Load environment variables
echo "📋 Loading environment variables..."
export $(cat backend/.env.local | grep -v '^#' | xargs)
echo "✅ Environment variables loaded"
echo ""

# Validate required variables
REQUIRED_VARS=(
    "AWS_ENDPOINT_URL"
    "AWS_REGION"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "FRONTEND_URL"
    "S3_PHOTOS_BUCKET"
    "S3_BUCKET"
    "S3_RENDITIONS_BUCKET"
    "DYNAMODB_TABLE_USERS"
    "JWT_SECRET"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "   Please configure them in backend/.env.local"
    exit 1
fi

echo "✅ All required environment variables set"
echo ""

# Setup Python virtual environment
VENV_DIR="backend/venv"
echo "🐍 Setting up Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "   Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || {
        echo "❌ Failed to create virtual environment"
        echo "   Ensure Python 3 is installed: brew install python@3.11"
        exit 1
    }
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source "$VENV_DIR/bin/activate" || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}
echo "✅ Virtual environment activated"

# Install Python dependencies in virtual environment
echo "📦 Installing Python dependencies in virtual environment..."
pip install --quiet --upgrade pip
pip install --quiet boto3 python-dotenv || {
    echo "❌ Failed to install Python dependencies"
    echo "   Try manually:"
    echo "   source backend/venv/bin/activate"
    echo "   pip install boto3 python-dotenv"
    exit 1
}
echo "✅ Dependencies installed"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers (if any)..."
docker-compose -f docker/docker-compose.localstack.yml down 2>/dev/null || true
echo ""

# Start LocalStack
echo "🐳 Starting LocalStack..."
docker-compose -f docker/docker-compose.localstack.yml up -d localstack
echo ""

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
sleep 10

MAX_RETRIES="${LOCALSTACK_MAX_RETRIES:-30}"
RETRY_DELAY="${LOCALSTACK_RETRY_DELAY:-2}"
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    if curl -s "${AWS_ENDPOINT_URL}/_localstack/health" > /dev/null 2>&1; then
        echo "✅ LocalStack is ready"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/$MAX_RETRIES: LocalStack not ready yet..."
    sleep $RETRY_DELAY
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "❌ LocalStack failed to start after $MAX_RETRIES attempts"
    exit 1
fi
echo ""

# Setup AWS resources in LocalStack (using virtual environment)
echo "⚙️  Setting up AWS resources in LocalStack..."
cd backend
# Use virtual environment's Python
../backend/venv/bin/python setup_localstack.py || {
    echo "❌ Failed to setup AWS resources"
    echo "   Check logs above for details"
    exit 1
}
cd ..
echo ""

# Start backend and frontend services
echo "🌐 Starting backend and frontend services..."
docker-compose -f docker/docker-compose.localstack.yml up -d backend frontend
echo ""

# Restore S3 from backup
echo "📦 Restoring S3 data from backup..."
./scripts/restore-localstack-s3.sh
echo ""

# Start automatic S3 backup service
echo "🔄 Starting automatic S3 backup service..."
./scripts/auto-backup-s3.sh > ./localstack_data/auto-backup.log 2>&1 &
BACKUP_PID=$!
echo "   ✅ Auto-backup PID: $BACKUP_PID"
echo "   📦 Backing up S3 every 30 seconds"
echo "   📄 Backup log: ./localstack_data/auto-backup.log"
echo ""

echo "======================================================"
echo "✅ Galerly LocalStack Development Environment Running"
echo "======================================================"
echo ""
echo "Services:"
echo "  • LocalStack:       ${AWS_ENDPOINT_URL}"
echo "  • LocalStack UI:    http://localhost:${LOCALSTACK_UI_PORT:-8080}"
echo "  • Backend API:      http://localhost:${BACKEND_PORT:-5000}"
echo "  • Frontend:         ${FRONTEND_URL}"
echo ""
echo "LocalStack Services:"
echo "  • S3:               ${AWS_ENDPOINT_URL}"
echo "  • DynamoDB:         ${AWS_ENDPOINT_URL}"
echo "  • Lambda:           ${AWS_ENDPOINT_URL}"
echo "  • API Gateway:      ${AWS_ENDPOINT_URL}"
echo "  • SES:              ${AWS_ENDPOINT_URL}"
echo ""
echo "💾 S3 Auto-Backup:"
echo "  • Status:           ENABLED"
echo "  • Interval:         Every 30 seconds"
echo "  • Backup location:  ./localstack_data/s3_backup/"
echo "  • View logs:        tail -f ./localstack_data/auto-backup.log"
echo ""
echo "Useful Commands:"
echo "  • View logs:        docker-compose -f docker/docker-compose.localstack.yml logs -f"
echo "  • Stop services:    ./scripts/stop-localstack.sh"
echo "  • Restart services: docker-compose -f docker/docker-compose.localstack.yml restart"
echo "  • List S3 buckets:  aws --endpoint-url=${AWS_ENDPOINT_URL} s3 ls"
echo "  • List DynamoDB:    aws --endpoint-url=${AWS_ENDPOINT_URL} dynamodb list-tables"
echo ""
echo "Next Steps:"
echo "  1. Open browser: ${FRONTEND_URL}"
echo "  2. Register a new account"
echo "  3. Create a gallery and upload photos"
echo ""
echo "⚠️  IMPORTANT: Your images are now backed up automatically every 30 seconds!"
echo "   Even if you restart Docker without ./scripts/stop-localstack.sh, they're safe!"
echo ""
echo "Press Ctrl+C to stop, or run: ./scripts/stop-localstack.sh"
echo ""

# Follow logs
docker-compose -f docker/docker-compose.localstack.yml logs -f
