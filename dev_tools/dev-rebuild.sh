#!/bin/bash
# Development Rebuild Script
# Test-first approach: Validate and test before building containers
# Only builds and deploys if all validation checks and tests pass

set -e

echo "🔨 Galerly Development Rebuild"
echo "=============================="
echo ""

# Step 1: Run comprehensive pre-deployment validation
echo "🔍 Step 1: Running pre-deployment validation..."
echo "================================================"
./dev_tools/pre-deployment-check.sh

# Capture validation exit code
VALIDATION_EXIT_CODE=$?

if [ $VALIDATION_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Pre-deployment validation failed!"
    echo "   Fix all issues before rebuilding containers."
    echo ""
    exit 1
fi

echo ""
echo "✅ All validation checks passed! Proceeding with rebuild..."
echo ""

# Step 2: Stop all services
echo "🛑 Step 2: Stopping all services..."
echo "====================================="
docker-compose -f docker/docker-compose.localstack.yml down

# Kill admin app processes
echo "🔧 Stopping admin app processes..."
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

# Step 3: Clean up old build artifacts
echo ""
echo "🧹 Step 3: Cleaning build artifacts..."
echo "======================================="
rm -rf user-app/frontend/dist
rm -rf user-app/frontend/.vite
rm -rf admin-app/frontend/dist
rm -rf admin-app/frontend/.vite

# Step 4: Remove old Docker images
echo ""
echo "🐳 Step 4: Removing old Docker images..."
echo "========================================="
docker rmi galerly-backend-local galerly-frontend-local 2>/dev/null || true

# Step 5: Rebuild and start everything
echo ""
echo "🚀 Step 5: Rebuilding and starting all services..."
echo "==================================================="
./dev_tools/start-all.sh

echo ""
echo "✅ Rebuild complete! Services are starting..."
echo ""

