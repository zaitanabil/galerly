#!/bin/bash
# Galerly LocalStack - Stop Services
# Stops all LocalStack services using Docker Compose

set -e

echo "🛑 Stopping Galerly LocalStack Development Environment (Docker)"
echo "================================================================"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

# Stop all services using docker-compose
echo "🐳 Stopping all Docker containers..."
docker-compose -f docker/docker-compose.localstack.yml down 2>/dev/null || {
    echo "⚠️  docker-compose down failed, trying to stop containers manually..."
    docker stop galerly-frontend-react-local galerly-backend-local galerly-localstack 2>/dev/null || true
    docker rm galerly-frontend-react-local galerly-backend-local galerly-localstack 2>/dev/null || true
}
echo ""

echo "✅ All services stopped"
echo ""
echo "Service Status:"
echo "  • Backend API:      ✅ Stopped"
echo "  • React Frontend:   ✅ Stopped"
echo "  • LocalStack:       ✅ Stopped"
echo ""
echo "To start again, run: ./scripts/start-localstack.sh"
echo ""
