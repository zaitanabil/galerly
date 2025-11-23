#!/bin/bash
# Cleanup any orphaned background processes

echo "🧹 Cleaning up background processes..."

# Kill auto-backup processes
if pgrep -f "scripts/auto-backup-s3.sh" > /dev/null; then
    pkill -f "scripts/auto-backup-s3.sh"
    echo "   ✅ Stopped scripts/auto-backup-s3.sh"
else
    echo "   ℹ️  No auto-backup process running"
fi

echo ""
echo "✅ Cleanup complete"

