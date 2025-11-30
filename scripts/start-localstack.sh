#!/bin/bash
# Galerly LocalStack - Complete Local Development Setup
# Starts all services for local development with LocalStack
# Works with React frontend and Python backend

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

# Check for backend .env.local file
if [ ! -f backend/.env.local ]; then
    echo "❌ backend/.env.local not found"
    echo "   Copy backend/.env.local.template to backend/.env.local and configure"
    exit 1
fi

echo "✅ Backend environment configuration found"

# Check for React frontend .env file
if [ ! -f "frontend react/.env" ]; then
    echo "⚠️  React frontend .env not found, creating default..."
    cat > "frontend react/.env" << 'EOF'
VITE_ENVIRONMENT=local
VITE_IS_LOCALSTACK=true

VITE_BACKEND_HOST=localhost
VITE_BACKEND_PORT=5001
VITE_BACKEND_PROTOCOL=http

VITE_LOCALSTACK_HOST=localhost
VITE_LOCALSTACK_PORT=4566
VITE_S3_RENDITIONS_BUCKET=galerly-renditions-local

VITE_CHUNK_SIZE=5242880
VITE_MAX_CONCURRENT_UPLOADS=3

VITE_DEFAULT_PAGE_SIZE=20
VITE_MAX_PAGE_SIZE=100

VITE_API_TIMEOUT=30000
VITE_UPLOAD_TIMEOUT=300000

VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=false
EOF
    echo "✅ React frontend .env created"
else
    echo "✅ React frontend environment configuration found"
fi

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

# Install all requirements
if pip install --quiet -r backend/requirements.txt; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Failed to install Python dependencies"
    echo "   Try manually:"
    echo "   source backend/venv/bin/activate"
    echo "   pip install -r backend/requirements.txt"
    exit 1
fi

# Verify Flask is installed (critical dependency)
if python -c "import flask" 2>/dev/null; then
    echo "✅ Flask verified"
else
    echo "⚠️  Flask not found, installing explicitly..."
    pip install flask
fi
echo ""

# Install React frontend dependencies
echo "📦 Installing React frontend dependencies..."
cd "frontend react"
if [ ! -d "node_modules" ]; then
    echo "   Installing npm packages..."
    npm install --silent || {
        echo "❌ Failed to install React frontend dependencies"
        echo "   Try manually:"
        echo "   cd 'frontend react' && npm install"
        exit 1
    }
    echo "✅ React frontend dependencies installed"
else
    echo "✅ React frontend dependencies already installed"
fi
cd ..
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

#!/bin/bash
# Galerly LocalStack - Complete Local Development Setup
# Starts all services for local development with LocalStack
# Works with React frontend and Python backend in Docker containers

set -e

echo "🚀 Starting Galerly LocalStack Development Environment (Docker)"
echo "================================================================"
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

# Check for backend .env.local file
if [ ! -f backend/.env.local ]; then
    echo "❌ backend/.env.local not found"
    echo "   Copy backend/.env.local.template to backend/.env.local and configure"
    exit 1
fi

echo "✅ Backend environment configuration found"

# Check for React frontend .env file
if [ ! -f "frontend react/.env" ]; then
    echo "⚠️  React frontend .env not found, creating default..."
    cat > "frontend react/.env" << 'EOF'
VITE_ENVIRONMENT=local
VITE_IS_LOCALSTACK=true

VITE_BACKEND_HOST=localhost
VITE_BACKEND_PORT=5001
VITE_BACKEND_PROTOCOL=http

VITE_LOCALSTACK_HOST=localhost
VITE_LOCALSTACK_PORT=4566
VITE_S3_RENDITIONS_BUCKET=galerly-renditions-local

VITE_CHUNK_SIZE=5242880
VITE_MAX_CONCURRENT_UPLOADS=3

VITE_DEFAULT_PAGE_SIZE=20
VITE_MAX_PAGE_SIZE=100

VITE_API_TIMEOUT=30000
VITE_UPLOAD_TIMEOUT=300000

VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=false
EOF
    echo "✅ React frontend .env created"
else
    echo "✅ React frontend environment configuration found"
fi

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
    "S3_PHOTOS_BUCKET"
    "S3_BUCKET"
    "S3_RENDITIONS_BUCKET"
    "DYNAMODB_TABLE_USERS"
    "JWT_SECRET"
    "PORT"
    "FLASK_HOST"
    "FLASK_DEBUG"
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
cd backend

# Setup Python venv for setup script
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --quiet boto3 python-dotenv

# Run setup with environment variables
python setup_localstack.py || {
    echo "❌ Failed to setup AWS resources"
    echo "   Check logs above for details"
    exit 1
}
cd ..
echo ""

# Build and start backend container
echo "🐍 Building and starting backend container..."
docker-compose -f docker/docker-compose.localstack.yml up -d --build backend
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend API to be ready..."
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
        echo "✅ Backend API is ready"
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

# Build and start React frontend container
echo "⚛️  Building and starting React frontend container..."
docker-compose -f docker/docker-compose.localstack.yml up -d --build frontend_react
echo ""

# Wait for frontend to be ready
echo "⏳ Waiting for React frontend to be ready..."
FRONTEND_PORT="${FRONTEND_PORT:-8000}"
retry_count=0
frontend_ready=false

while [ $retry_count -lt 30 ]; do
    # Check if container is running (use grep -E to match either name variant)
    if ! docker ps | grep -qE "(galerly-frontend-react-local|galerly-frontend-local)"; then
        echo "   ❌ Frontend container not running! Check logs:"
        docker-compose -f docker/docker-compose.localstack.yml logs frontend_react | tail -20
        exit 1
    fi
    
    # Try to connect to frontend
    if curl -s -f "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1; then
        echo "✅ React frontend is ready"
        frontend_ready=true
        break
    fi
    
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/30: Frontend not ready yet..."
    sleep 3
done

if [ "$frontend_ready" = true ]; then
    echo "✅ React frontend is ready on http://localhost:${FRONTEND_PORT}"
else
    echo "   ⚠️  Frontend not responding. Check logs:"
    docker-compose -f docker/docker-compose.localstack.yml logs frontend_react | tail -30
fi
echo ""

echo "======================================================"
echo "✅ Galerly LocalStack Development Environment Running (Docker)"
echo "======================================================"
echo ""
echo "Services:"
echo "  • LocalStack:       ${AWS_ENDPOINT_URL}"
echo "  • Backend API:      http://localhost:${BACKEND_PORT:-5001}"
echo "  • React Frontend:   http://localhost:${FRONTEND_PORT:-8000}"
echo ""
echo "LocalStack Services:"
echo "  • S3:               ${AWS_ENDPOINT_URL}"
echo "  • DynamoDB:         ${AWS_ENDPOINT_URL}"
echo "  • SES:              ${AWS_ENDPOINT_URL}"
echo ""
echo "Docker Containers:"
echo "  • LocalStack:       galerly-localstack"
echo "  • Backend:          galerly-backend-local"
echo "  • Frontend:         galerly-frontend-react-local"
echo ""
echo "Container Logs:"
echo "  • View all:         docker-compose -f docker/docker-compose.localstack.yml logs -f"
echo "  • Backend:          docker-compose -f docker/docker-compose.localstack.yml logs -f backend"
echo "  • Frontend:         docker-compose -f docker/docker-compose.localstack.yml logs -f frontend_react"
echo "  • LocalStack:       docker logs -f galerly-localstack"
echo ""
echo "Useful Commands:"
echo "  • Stop services:    docker-compose -f docker/docker-compose.localstack.yml down"
echo "  • List S3 buckets:  aws --endpoint-url=${AWS_ENDPOINT_URL} s3 ls"
echo "  • List DynamoDB:    aws --endpoint-url=${AWS_ENDPOINT_URL} dynamodb list-tables"
echo "  • Test API:         curl http://localhost:${BACKEND_PORT:-5001}/health"
echo "  • Restart backend:  docker-compose -f docker/docker-compose.localstack.yml restart backend"
echo "  • Restart frontend: docker-compose -f docker/docker-compose.localstack.yml restart frontend_react"
echo ""
echo "Next Steps:"
echo "  1. Open browser:    http://localhost:${FRONTEND_PORT:-5173}"
echo "  2. Test API:        http://localhost:${FRONTEND_PORT:-5173}/api-test"
echo "  3. Register account and start using Galerly!"
echo ""
echo "Press Ctrl+C to stop, or run: docker-compose -f docker/docker-compose.localstack.yml down"
echo ""

# Keep script running and show live logs
echo "📊 Showing live logs from all services (Ctrl+C to stop):"
echo ""

# Follow all container logs
docker-compose -f docker/docker-compose.localstack.yml logs -f
