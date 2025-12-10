#!/usr/bin/env python3
"""
Migration Script: Apply Query Optimizations
Replaces scan() operations with optimized GSI queries

Usage:
    python migrate_to_optimized_queries.py --dry-run    # Preview changes
    python migrate_to_optimized_queries.py --apply      # Apply changes
"""

import os
import re
import sys
from pathlib import Path

# Patterns to find and replace
MIGRATIONS = [
    {
        'name': 'Gallery lookup by ID',
        'pattern': r'galleries_table\.scan\(\s*FilterExpression=[\'"]?id\s*=\s*:gid[\'"]?,\s*ExpressionAttributeValues=\{[\'"]?:gid[\'"]?:\s*(\w+)\}[,\s]*\)',
        'replacement': r'''# Optimized: Use GalleryIdIndex GSI
from utils.query_optimization import get_gallery_by_id_optimized
gallery = get_gallery_by_id_optimized(\1)
if gallery:
    gallery_owner_id = gallery['user_id']''',
        'files': ['analytics_handler.py', 'realtime_viewers_handler.py', 'bulk_download_handler.py']
    },
    {
        'name': 'User lookup by ID',
        'pattern': r'users_table\.scan\(\s*FilterExpression=[\'"]?id\s*=\s*:uid[\'"]?,\s*ExpressionAttributeValues=\{[\'"]?:uid[\'"]?:\s*(\w+)\}[,\s]*Limit=1\)',
        'replacement': r'''# Optimized: Use UserIdIndex GSI
from utils.query_optimization import get_user_by_id_optimized
user_data = get_user_by_id_optimized(\1)
if user_data:''',
        'files': ['client_favorites_handler.py', 'subscription_handler.py', 'admin_plan_handler.py']
    },
    {
        'name': 'Get photos by gallery',
        'pattern': r'photos_table\.query\(\s*IndexName=[\'"]?GalleryIdIndex[\'"]?,\s*KeyConditionExpression=Key\([\'"]?gallery_id[\'"]?\)\.eq\((\w+)\)\)',
        'replacement': r'''# Already optimized with GalleryIdIndex
from utils.query_optimization import get_gallery_photos_optimized
photos = get_gallery_photos_optimized(\1)''',
        'files': ['gallery_handler.py', 'photo_handler.py']
    }
]


def find_handler_files(base_path='handlers'):
    """Find all Python handler files"""
    handlers_dir = Path(base_path)
    if not handlers_dir.exists():
        handlers_dir = Path('user-app/backend/handlers')
    
    return list(handlers_dir.glob('*_handler.py'))


def apply_migration(file_path, dry_run=True):
    """Apply migrations to a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    for migration in MIGRATIONS:
        if file_path.name in migration['files']:
            matches = re.findall(migration['pattern'], content)
            if matches:
                new_content = re.sub(migration['pattern'], migration['replacement'], content)
                if new_content != content:
                    changes_made.append(migration['name'])
                    content = new_content
    
    if content != original_content:
        if not dry_run:
            with open(file_path, 'w') as f:
                f.write(content)
        return True, changes_made
    
    return False, []


def main():
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print("=" * 60)
    else:
        print("✏️  APPLYING MIGRATIONS")
        print("=" * 60)
    
    handler_files = find_handler_files()
    
    if not handler_files:
        print("❌ No handler files found. Run from project root.")
        return 1
    
    total_files = 0
    modified_files = 0
    
    for file_path in handler_files:
        total_files += 1
        changed, migrations = apply_migration(file_path, dry_run)
        
        if changed:
            modified_files += 1
            status = "📝 WOULD MODIFY" if dry_run else "✅ MODIFIED"
            print(f"{status}: {file_path.name}")
            for migration in migrations:
                print(f"  - {migration}")
        else:
            print(f"✓ No changes: {file_path.name}")
    
    print("=" * 60)
    print(f"Scanned: {total_files} files")
    print(f"Modified: {modified_files} files")
    
    if dry_run:
        print("\n💡 To apply changes, run: python migrate_to_optimized_queries.py --apply")
    else:
        print("\n✅ Migrations applied successfully!")
        print("⚠️  Remember to:")
        print("   1. Create required GSI indexes on DynamoDB tables")
        print("   2. Test all affected endpoints")
        print("   3. Monitor query performance")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
