#!/bin/bash
# Stop all Galerly services

echo "🛑 Stopping Galerly Development Environment"
echo "==========================================="
echo ""

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
docker-compose -f docker/docker-compose.localstack.yml down
echo "✅ Docker containers stopped"
echo ""

# Delete LocalStack data folder for clean state
echo "🗑️  Cleaning up LocalStack data..."
if [ -d "localstack_data" ]; then
    rm -rf localstack_data
    echo "✅ LocalStack data folder deleted"
else
    echo "ℹ️  No LocalStack data folder found (already clean)"
fi

echo ""
echo "✅ All services stopped and cleaned up successfully!"
echo ""

