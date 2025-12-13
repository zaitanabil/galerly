#!/bin/bash
# Galerly - Development Environment Startup
# Starts LocalStack and User App
#
# TESTS ARE MANDATORY - All tests must pass before services start
# No exceptions, no optional flags

set -e

echo "🚀 Starting Galerly Development Environment"
echo "============================================"
echo ""

# ALWAYS run tests - mandatory, no exceptions
echo "🧪 Running pre-deployment validation (MANDATORY)..."
echo "====================================================="
./dev_tools/pre-deployment-check.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Pre-deployment validation FAILED!"
    echo "   All tests MUST pass before starting services."
    echo "   Fix all issues and try again."
    echo ""
    exit 1
fi

echo ""
echo "✅ All tests passed! Starting services..."
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

# Check for root .env.development file
if [ ! -f .env.development ]; then
    echo "❌ .env.development not found in root directory"
    echo "   This file is required for local development"
    exit 1
fi

echo "✅ Root .env.development found (all apps use this file)"


# Load environment variables from root .env.development
echo "📋 Loading environment variables from .env.development..."
export $(cat .env.development | grep -v '^#' | xargs)
echo "✅ Environment variables loaded"
echo ""

# Create LocalStack data directory if it doesn't exist
LOCALSTACK_DATA_DIR="${LOCALSTACK_DATA_DIR:-./localstack_data}"
if [ ! -d "$LOCALSTACK_DATA_DIR" ]; then
    echo "📁 Creating LocalStack data directory: $LOCALSTACK_DATA_DIR"
    mkdir -p "$LOCALSTACK_DATA_DIR"
    echo "✅ LocalStack data directory created"
else
    echo "✅ LocalStack data directory exists: $LOCALSTACK_DATA_DIR"
fi
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

# Setup AWS resources in LocalStack
echo "⚙️  Setting up AWS resources in LocalStack..."
cd user-app/backend

# Setup Python venv for setup script
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Use venv pip directly to ensure installation
venv/bin/pip install --quiet boto3 python-dotenv

# Run setup with environment variables using venv python
venv/bin/python3 setup_localstack.py || {
    echo "❌ Failed to setup AWS resources"
    echo "   Check logs above for details"
    exit 1
}
cd ../..
echo ""

# Build and start user app backend container
echo "🐍 Building and starting user app backend container..."
docker-compose -f docker/docker-compose.localstack.yml up -d --build backend
echo ""

# Wait for user app backend to be ready
echo "⏳ Waiting for user app backend API to be ready..."
BACKEND_PORT="${BACKEND_PORT:-5001}"
retry_count=0
backend_ready=false

while [ $retry_count -lt 20 ]; do
    # Check if container is running
    if ! docker ps | grep -q galerly-backend-local; then
        echo "   ❌ Backend container not running! Check logs:"
        docker-compose -f docker/docker-compose.localstack.yml logs backend | tail -20
        exit 1
    fi
    
    # Try to connect to health endpoint
    if curl -s -f "http://localhost:${BACKEND_PORT}/health" > /dev/null 2>&1; then
        echo "✅ User app backend API is ready"
        backend_ready=true
        break
    fi
    
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/20: Backend not ready yet..."
    sleep 3
done

if [ "$backend_ready" = false ]; then
    echo "   ⚠️  Backend health check timeout. Checking logs..."
    echo ""
    docker-compose -f docker/docker-compose.localstack.yml logs backend | tail -30
    echo ""
    echo "   Full logs: docker-compose -f docker/docker-compose.localstack.yml logs backend"
    exit 1
fi
echo ""

# Build and start user app frontend container
echo "⚛️  Building and starting user app frontend container..."
docker-compose -f docker/docker-compose.localstack.yml up -d --build frontend
echo ""

# Wait for user app frontend to be ready
echo "⏳ Waiting for user app frontend to be ready..."
FRONTEND_PORT="${FRONTEND_PORT:-8000}"
retry_count=0
frontend_ready=false

while [ $retry_count -lt 30 ]; do
    # Check if container is running
    if ! docker ps | grep -qE "(galerly-frontend-local)"; then
        echo "   ❌ Frontend container not running! Check logs:"
        docker-compose -f docker/docker-compose.localstack.yml logs frontend | tail -20
        exit 1
    fi
    
    # Try to connect to frontend
    if curl -s -f "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1; then
        echo "✅ User app frontend is ready"
        frontend_ready=true
        break
    fi
    
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/30: Frontend not ready yet..."
    sleep 3
done

if [ "$frontend_ready" = true ]; then
    echo "✅ User app frontend is ready on http://localhost:${FRONTEND_PORT}"
else
    echo "   ⚠️  Frontend not responding. Check logs:"
    docker-compose -f docker/docker-compose.localstack.yml logs frontend | tail -30
fi
echo ""

echo "============================================"
echo "✅ Galerly Development Environment Running"
echo "============================================"
echo ""
echo "GALERLY USER APP:"
echo "  • Frontend:         http://localhost:${FRONTEND_PORT:-8000}"
echo "  • Backend API:      http://localhost:${BACKEND_PORT:-5001}"
echo ""
echo "INFRASTRUCTURE:"
echo "  • LocalStack:       ${AWS_ENDPOINT_URL}"
echo "  • S3:               ${AWS_ENDPOINT_URL}"
echo "  • DynamoDB:         ${AWS_ENDPOINT_URL}"
echo ""
echo "DOCKER CONTAINERS:"
echo "  • LocalStack:       galerly-localstack"
echo "  • User Backend:     galerly-backend-local"
echo "  • User Frontend:    galerly-frontend-local"
echo ""
echo "LOGS:"
echo "  • Backend:          docker-compose -f docker/docker-compose.localstack.yml logs -f backend"
echo "  • Frontend:         docker-compose -f docker/docker-compose.localstack.yml logs -f frontend"
echo ""
echo "TO STOP:"
echo "  • All services:     ./dev_tools/stop-all.sh"
echo "  • Docker only:      docker-compose -f docker/docker-compose.localstack.yml down"
echo ""

echo "Next Steps:"
echo "  1. Open App:        http://localhost:${FRONTEND_PORT:-8000}"
echo ""
echo "✅ All tests passed before startup - system validated and ready!"
echo ""
echo "Press Ctrl+C to stop showing logs, services will continue running..."
echo ""

# Follow all logs
docker-compose -f docker/docker-compose.localstack.yml logs -f

