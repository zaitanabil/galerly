#!/bin/bash
# Auto-backup LocalStack S3 every 30 seconds while running

set -e

echo "🔄 Starting automatic S3 backup service..."

# Load environment variables
if [ -f ./backend/.env.local ]; then
    export $(cat ./backend/.env.local | grep -v '^#' | xargs)
fi

BACKUP_DIR="./localstack_data/s3_backup"
BUCKETS=("$S3_PHOTOS_BUCKET" "$S3_RENDITIONS_BUCKET" "$S3_BUCKET")

while true; do
    sleep 30  # Backup every 30 seconds
    
    # Check if LocalStack container is running
    if ! docker ps | grep -q galerly-localstack; then
        echo "⚠️  LocalStack container not running. Stopping auto-backup."
        exit 0
    fi
    
    # Silently backup each bucket
    for bucket in "${BUCKETS[@]}"; do
        aws --endpoint-url="$AWS_ENDPOINT_URL" s3 sync "s3://$bucket" "$BACKUP_DIR/$bucket" --delete --only-show-errors 2>/dev/null || true
    done
    
    echo "$(date '+%H:%M:%S') ✅ S3 auto-backup completed"
done

