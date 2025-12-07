#!/bin/bash
# Quick restart for user app frontend only
# Useful when making frontend code changes

echo "🔄 Restarting User App Frontend..."
docker-compose -f docker/docker-compose.localstack.yml restart frontend

echo "⏳ Waiting for frontend to be ready..."
sleep 5

if curl -s "http://localhost:5173" > /dev/null 2>&1; then
    echo "✅ Frontend is ready at http://localhost:5173"
else
    echo "⚠️  Frontend might not be ready. Check logs:"
    echo "   docker-compose -f docker/docker-compose.localstack.yml logs frontend"
fi

