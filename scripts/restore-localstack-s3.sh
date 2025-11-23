#!/bin/bash
# LocalStack S3 Restore Script  
# Restores S3 buckets from backup on startup

BACKUP_DIR="./localstack_data/s3_backup"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "No S3 backup found at $BACKUP_DIR"
    exit 0
fi

echo "📦 Restoring LocalStack S3 from backup..."

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack..."
sleep 10

# Restore each bucket
for BUCKET_DIR in "$BACKUP_DIR"/*; do
    if [ -d "$BUCKET_DIR" ]; then
        BUCKET=$(basename "$BUCKET_DIR")
        FILE_COUNT=$(find "$BUCKET_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$FILE_COUNT" -gt 0 ]; then
            echo "  📁 Restoring bucket: $BUCKET ($FILE_COUNT files)"
            
            # Create bucket if it doesn't exist
            docker exec galerly-localstack awslocal s3 mb "s3://$BUCKET" 2>/dev/null || true
            
            # Copy files to container
            docker cp "$BUCKET_DIR/." "galerly-localstack:/tmp/restore/$BUCKET/" 2>/dev/null
            
            # Sync to S3
            docker exec galerly-localstack awslocal s3 sync "/tmp/restore/$BUCKET" "s3://$BUCKET" 2>/dev/null
            
            echo "    ✅ Restored $BUCKET"
        fi
    fi
done

echo "✅ S3 restore complete"

