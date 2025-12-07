#!/bin/bash
# Restart admin app backend only

echo "🔄 Restarting Admin App Backend..."

# Kill existing process
PID=$(lsof -ti:5002)
if [ ! -z "$PID" ]; then
    kill -9 $PID
    echo "✅ Stopped old backend process"
fi

# Start new process
cd admin-app/backend
source ../../user-app/backend/venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python3 api.py > ../../logs/admin-backend.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > ../../logs/admin-backend.pid
echo "✅ Started new backend process (PID: $NEW_PID)"
cd ../..

sleep 2

if curl -s "http://localhost:5002/health" > /dev/null 2>&1; then
    echo "✅ Admin backend is ready at http://localhost:5002"
else
    echo "⚠️  Admin backend might not be ready. Check logs:"
    echo "   tail -f logs/admin-backend.log"
fi

