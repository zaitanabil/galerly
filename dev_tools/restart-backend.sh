#!/bin/bash
# Quick restart for user app backend only
# Useful when making backend code changes

echo "🔄 Restarting User App Backend..."
docker-compose -f docker/docker-compose.localstack.yml restart backend

echo "⏳ Waiting for backend to be ready..."
sleep 3

if curl -s "http://localhost:5001/health" > /dev/null 2>&1; then
    echo "✅ Backend is ready at http://localhost:5001"
else
    echo "⚠️  Backend might not be ready. Check logs:"
    echo "   docker-compose -f docker/docker-compose.localstack.yml logs backend"
fi

