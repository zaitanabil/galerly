#!/bin/bash
# Stop all Galerly services (User App + Admin App)

echo "🛑 Stopping Galerly Complete Development Environment"
echo "===================================================="
echo ""

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
docker-compose -f docker/docker-compose.localstack.yml down
echo "✅ Docker containers stopped"
echo ""

# Stop Admin Backend
if [ -f logs/admin-backend.pid ]; then
    ADMIN_BACKEND_PID=$(cat logs/admin-backend.pid)
    if ps -p $ADMIN_BACKEND_PID > /dev/null 2>&1; then
        echo "🔧 Stopping Admin Backend (PID: $ADMIN_BACKEND_PID)..."
        kill $ADMIN_BACKEND_PID 2>/dev/null || true
        echo "✅ Admin backend stopped"
    fi
    rm logs/admin-backend.pid
fi

# Stop Admin Frontend
if [ -f logs/admin-frontend.pid ]; then
    ADMIN_FRONTEND_PID=$(cat logs/admin-frontend.pid)
    if ps -p $ADMIN_FRONTEND_PID > /dev/null 2>&1; then
        echo "🎨 Stopping Admin Frontend (PID: $ADMIN_FRONTEND_PID)..."
        kill $ADMIN_FRONTEND_PID 2>/dev/null || true
        echo "✅ Admin frontend stopped"
    fi
    rm logs/admin-frontend.pid
fi

# Kill any remaining processes on ports 5002 and 3001
echo ""
echo "🔍 Cleaning up any remaining processes..."
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

echo ""
echo "✅ All services stopped successfully!"
echo ""

