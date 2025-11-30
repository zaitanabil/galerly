#!/bin/bash

# Galerly React Frontend - Development Startup Script
# This script sets up and starts the React development environment

set -e

echo "🎨 Galerly React Frontend Setup"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the 'frontend react' directory."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed!"
    echo ""
else
    echo "✅ Dependencies already installed"
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cat > .env << 'EOF'
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
    echo "✅ .env file created!"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Display environment info
echo "📋 Environment Configuration:"
echo "   - Backend: http://localhost:5001"
echo "   - LocalStack: http://localhost:4566"
echo "   - Frontend Dev Server: http://localhost:5173"
echo ""

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s -f -o /dev/null http://localhost:5001/health 2>/dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not running on localhost:5001"
    echo "   Please start the backend first: cd ../backend && python api.py"
fi
echo ""

# Start the dev server
echo "🚀 Starting React development server..."
echo ""
echo "📖 Available at: http://localhost:5173"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev

