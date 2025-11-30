#!/bin/bash
# Check backend logs and status
# Useful for debugging when backend won't start

echo "🔍 Backend Diagnostics"
echo "===================="
echo ""

# Check if backend is running
if [ -f ./localstack_data/backend.pid ]; then
    BACKEND_PID=$(cat ./localstack_data/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "✅ Backend process is running (PID: $BACKEND_PID)"
    else
        echo "❌ Backend process is NOT running (PID file exists: $BACKEND_PID)"
    fi
else
    echo "⚠️  No backend PID file found"
fi

echo ""
echo "📝 Backend Log (last 30 lines):"
echo "──────────────────────────────────────"

if [ -f ./localstack_data/backend.log ]; then
    tail -30 ./localstack_data/backend.log
else
    echo "❌ No backend log file found"
fi

echo "──────────────────────────────────────"
echo ""

# Check if backend is responding
echo "🔌 Testing backend connection..."
BACKEND_PORT="${BACKEND_PORT:-5001}"

if curl -s -f "http://localhost:${BACKEND_PORT}/health" > /dev/null 2>&1; then
    echo "✅ Backend health endpoint responding"
    curl -s "http://localhost:${BACKEND_PORT}/health" | python3 -m json.tool 2>/dev/null || echo ""
elif curl -s -f "http://localhost:${BACKEND_PORT}/" > /dev/null 2>&1; then
    echo "✅ Backend root endpoint responding"
    curl -s "http://localhost:${BACKEND_PORT}/" | python3 -m json.tool 2>/dev/null || echo ""
else
    echo "❌ Backend not responding on port $BACKEND_PORT"
fi

echo ""
echo "🔧 Environment Check:"
echo "──────────────────────────────────────"

if [ -f backend/.env.local ]; then
    echo "✅ backend/.env.local exists"
    echo ""
    echo "Key variables:"
    grep -E "^(AWS_REGION|AWS_ENDPOINT_URL|BACKEND_PORT)" backend/.env.local || echo "   (none found)"
else
    echo "❌ backend/.env.local NOT found"
fi

echo "──────────────────────────────────────"
echo ""
echo "Commands:"
echo "  • View live logs:    tail -f ./localstack_data/backend.log"
echo "  • Restart backend:   ./scripts/stop-localstack.sh && ./scripts/start-localstack.sh"
echo "  • Manual start:      cd backend && source venv/bin/activate && python api.py"
echo ""

