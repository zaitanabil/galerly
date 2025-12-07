#!/bin/bash
# Reset LocalStack data (clear all S3 buckets and DynamoDB tables)

echo "⚠️  LocalStack Data Reset"
echo "========================"
echo ""
echo "This will DELETE all data in LocalStack:"
echo "  • All S3 buckets and objects"
echo "  • All DynamoDB tables"
echo "  • All other LocalStack resources"
echo ""
read -p "Are you sure? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🔄 Resetting LocalStack..."

# Stop containers
docker-compose -f docker/docker-compose.localstack.yml down

# Remove LocalStack volume data
docker volume rm galerly-localstack-data 2>/dev/null || true

# Start LocalStack again
echo "🐳 Starting fresh LocalStack..."
docker-compose -f docker/docker-compose.localstack.yml up -d localstack

# Wait for ready
echo "⏳ Waiting for LocalStack..."
sleep 10

# Re-setup AWS resources
echo "⚙️  Setting up AWS resources..."
cd user-app/backend
source venv/bin/activate
export $(cat .env.local | grep -v '^#' | xargs)
python3 setup_localstack.py
cd ../..

echo ""
echo "✅ LocalStack reset complete!"
echo "   Restart your applications:"
echo "   ./dev_tools/start-all.sh"

