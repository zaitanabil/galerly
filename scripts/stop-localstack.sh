#!/bin/bash
# Galerly LocalStack - Stop Services
# Stops all LocalStack services and cleans up containers

set -e

echo "🛑 Stopping Galerly LocalStack Development Environment"
echo "======================================================"
echo ""

# Stop auto-backup process if running
echo "🛑 Stopping auto-backup service..."
pkill -f "scripts/auto-backup-s3.sh" 2>/dev/null || true
echo "   ✅ Auto-backup service stopped"
echo ""

# Final S3 backup before stopping
echo "📦 Final S3 backup before shutdown..."
./scripts/backup-localstack-s3.sh
echo ""

# Stop all services
echo "🐳 Stopping containers..."
docker-compose -f docker-compose.localstack.yml down

echo ""
echo "✅ All services stopped"
echo "💾 S3 data backed up to: ./localstack_data/s3_backup/"
echo ""
echo "To start again, run: ./scripts/start-localstack.sh"
echo ""

