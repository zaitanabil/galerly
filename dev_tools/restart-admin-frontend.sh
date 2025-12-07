#!/bin/bash
# Restart admin app frontend only

echo "🔄 Restarting Admin App Frontend..."

# Kill existing process
PID=$(lsof -ti:3001)
if [ ! -z "$PID" ]; then
    kill -9 $PID
    echo "✅ Stopped old frontend process"
fi

# Start new process
cd admin-app/frontend
npm run dev > ../../logs/admin-frontend.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > ../../logs/admin-frontend.pid
echo "✅ Started new frontend process (PID: $NEW_PID)"
cd ../..

sleep 5

if curl -s "http://localhost:3001" > /dev/null 2>&1; then
    echo "✅ Admin frontend is ready at http://localhost:3001"
else
    echo "⚠️  Admin frontend might not be ready. Check logs:"
    echo "   tail -f logs/admin-frontend.log"
fi

