#!/bin/bash

# Galerly React Frontend - Installation and Setup Script
# This script installs dependencies and verifies the frontend-backend connection

set -e

echo "🚀 Galerly React Frontend - Setup Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the 'frontend' directory."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Warning: Node.js 18 or higher is recommended. Current version: $(node -v)"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
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
    echo "✅ .env file created with local development settings"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Start the backend (if not already running):"
echo "   cd ../backend && python api.py"
echo ""
echo "2. Start the React frontend:"
echo "   npm run dev"
echo ""
echo "3. Test the API connection:"
echo "   Open http://localhost:5173/api-test"
echo "   Click 'Run All Tests' to verify backend connection"
echo ""
echo "4. View the main app:"
echo "   Open http://localhost:5173"
echo ""
echo "📚 Documentation:"
echo "   - SETUP_GUIDE.md - Complete setup and usage guide"
echo "   - src/services/README.md - API services documentation"
echo "   - INTEGRATION_COMPLETE.md - Integration overview"
echo ""
echo "🎉 Happy coding!"

