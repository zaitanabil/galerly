#!/bin/bash
# ============================================
# Run Gallery Expiration & Cleanup Job
# ============================================
# This script manually triggers the gallery cleanup process
# In production, this runs automatically via CloudWatch Events (cron)

set -e

echo "🔄 Running Gallery Expiration & Cleanup..."

# Load environment variables
if [ -f ./backend/.env.local ]; then
    export $(grep -v '^#' ./backend/.env.local | grep -v '^$' | xargs)
fi

# Run the cleanup script
cd backend
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from handlers.gallery_expiration_handler import run_daily_cleanup

print("\n🕐 Checking for expired galleries...")
print("=" * 60)

result = run_daily_cleanup()

print("=" * 60)
print(f"\n✅ Cleanup complete!")

if isinstance(result, dict) and 'body' in result:
    import json
    body = result['body'] if isinstance(result['body'], dict) else json.loads(result['body'])
    print(f"\n📊 Summary:")
    print(f"   Galleries archived: {body.get('archived', 0)}")
    print(f"   Galleries deleted: {body.get('deleted', 0)}")
else:
    print(result)
EOF

cd ..

echo ""
echo "✅ Gallery cleanup completed"

