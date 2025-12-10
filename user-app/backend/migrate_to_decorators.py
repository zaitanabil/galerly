#!/usr/bin/env python3
"""
Decorator Migration Assistant
Helps migrate handlers to use centralized plan enforcement decorators

Usage:
    python migrate_to_decorators.py scan          # Find candidates
    python migrate_to_decorators.py suggest FILE  # Get suggestions for file
"""

import os
import re
import sys
from pathlib import Path

DECORATOR_PATTERNS = {
    'role_check': {
        'pattern': r"if user\.get\(['\"]role['\"]\)\s*!=\s*['\"](\w+)['\"]:",
        'decorator': '@require_role(\'{role}\')',
        'import': 'from utils.plan_enforcement import require_role'
    },
    'feature_check': {
        'pattern': r"if not features\.get\(['\"](\w+)['\"]",
        'decorator': '@require_plan(feature=\'{feature}\')',
        'import': 'from utils.plan_enforcement import require_plan'
    },
    'plan_level': {
        'pattern': r"if plan_id not in \[['\"](\w+)['\"],",
        'decorator': '@require_plan(min_plan=\'{plan}\')',
        'import': 'from utils.plan_enforcement import require_plan'
    }
}


def scan_file(file_path):
    """Scan a file for decorator opportunities"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    opportunities = []
    
    # Find role checks
    role_matches = re.findall(DECORATOR_PATTERNS['role_check']['pattern'], content)
    for role in role_matches:
        opportunities.append({
            'type': 'role',
            'value': role,
            'decorator': f"@require_role('{role}')",
            'import': DECORATOR_PATTERNS['role_check']['import']
        })
    
    # Find feature checks
    feature_matches = re.findall(DECORATOR_PATTERNS['feature_check']['pattern'], content)
    for feature in feature_matches:
        opportunities.append({
            'type': 'feature',
            'value': feature,
            'decorator': f"@require_plan(feature='{feature}')",
            'import': DECORATOR_PATTERNS['feature_check']['import']
        })
    
    return opportunities


def suggest_migration(file_path):
    """Provide migration suggestions for a file"""
    opportunities = scan_file(file_path)
    
    if not opportunities:
        print(f"✅ {file_path.name} - No decorator opportunities found")
        return
    
    print(f"\n📝 {file_path.name}")
    print("=" * 60)
    
    # Group by type
    by_type = {}
    for opp in opportunities:
        if opp['type'] not in by_type:
            by_type[opp['type']] = []
        by_type[opp['type']].append(opp)
    
    # Required imports
    imports = set(opp['import'] for opp in opportunities)
    print("\n1. Add imports:")
    for imp in imports:
        print(f"   {imp}")
    
    # Decorator suggestions
    print("\n2. Add decorators to functions:")
    for type_name, opps in by_type.items():
        print(f"\n   {type_name.title()} checks ({len(opps)} found):")
        for opp in opps:
            print(f"   {opp['decorator']}")
    
    print("\n3. Remove manual checks from function bodies")
    print("   (The decorators will handle validation automatically)")
    
    print("\n💡 Example migration:")
    print("""
   BEFORE:
   def handle_create_invoice(user, body):
       if user.get('role') != 'photographer':
           return create_response(403, {...})
       features, _, _ = get_user_features(user)
       if not features.get('client_invoicing'):
           return create_response(403, {...})
       # ... handler logic
   
   AFTER:
   @require_role('photographer')
   @require_plan(feature='client_invoicing')
   def handle_create_invoice(user, body):
       # ... handler logic (clean!)
    """)


def scan_all_handlers():
    """Scan all handler files"""
    handlers_dir = Path('user-app/backend/handlers')
    if not handlers_dir.exists():
        handlers_dir = Path('handlers')
    
    files = list(handlers_dir.glob('*_handler.py'))
    
    print("🔍 Scanning for decorator opportunities...")
    print("=" * 60)
    
    total_opportunities = 0
    files_with_opps = 0
    
    for file_path in files:
        opps = scan_file(file_path)
        if opps:
            files_with_opps += 1
            total_opportunities += len(opps)
            print(f"📄 {file_path.name}: {len(opps)} opportunities")
    
    print("=" * 60)
    print(f"Files scanned: {len(files)}")
    print(f"Files with opportunities: {files_with_opps}")
    print(f"Total opportunities: {total_opportunities}")
    
    if files_with_opps > 0:
        print("\n💡 Run 'python migrate_to_decorators.py suggest FILE' for detailed suggestions")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate_to_decorators.py scan")
        print("  python migrate_to_decorators.py suggest FILENAME")
        return 1
    
    command = sys.argv[1]
    
    if command == 'scan':
        scan_all_handlers()
    elif command == 'suggest' and len(sys.argv) > 2:
        filename = sys.argv[2]
        file_path = Path('user-app/backend/handlers') / filename
        if not file_path.exists():
            file_path = Path('handlers') / filename
        if not file_path.exists():
            print(f"❌ File not found: {filename}")
            return 1
        suggest_migration(file_path)
    else:
        print("Invalid command. Use 'scan' or 'suggest FILENAME'")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
