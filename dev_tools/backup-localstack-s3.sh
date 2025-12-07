#!/bin/bash
# LocalStack S3 Backup Script
# Backs up all S3 buckets to local disk since LocalStack Community doesn't persist S3

BACKUP_DIR="./localstack_data/s3_backup"
ENDPOINT="http://localhost:4566"

echo "📦 Backing up LocalStack S3 buckets..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get list of buckets
BUCKETS=$(docker exec galerly-localstack awslocal s3 ls 2>/dev/null | awk '{print $3}')

if [ -z "$BUCKETS" ]; then
    echo "No buckets found to backup"
    exit 0
fi

# Backup each bucket
for BUCKET in $BUCKETS; do
    echo "  📁 Backing up bucket: $BUCKET"
    BUCKET_DIR="$BACKUP_DIR/$BUCKET"
    mkdir -p "$BUCKET_DIR"
    
    # Sync bucket to local directory
    docker exec galerly-localstack awslocal s3 sync "s3://$BUCKET" "/tmp/backup/$BUCKET" 2>/dev/null
    docker cp "galerly-localstack:/tmp/backup/$BUCKET/." "$BUCKET_DIR/" 2>/dev/null
    
    FILE_COUNT=$(find "$BUCKET_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "    ✅ Backed up $FILE_COUNT files"
done

echo "✅ S3 backup complete: $BACKUP_DIR"

