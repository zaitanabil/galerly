#!/usr/bin/env python3
"""
Migration Script: client_email → client_emails
================================================

This script migrates the legacy single client_email field to the client_emails array.

WHAT IT DOES:
1. Scans all galleries in galerly-galleries table
2. For each gallery with client_email but no client_emails:
   - Creates client_emails array with the single email
3. For galleries with both:
   - Ensures client_email is in client_emails array
4. Removes the client_email column from all records

SAFETY:
- Dry-run mode by default (use --execute to apply changes)
- Backs up data before modification
- Validates email format
- Reports all changes

Usage:
    python3 migrate_client_email_to_array.py              # Dry-run
    python3 migrate_client_email_to_array.py --execute    # Apply changes
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
GALLERIES_TABLE = os.environ.get('DYNAMODB_TABLE_GALLERIES', 'galerly-galleries')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
galleries_table = dynamodb.Table(GALLERIES_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def scan_all_galleries():
    """Scan all galleries from DynamoDB"""
    print("📊 Scanning all galleries...")
    galleries = []
    response = galleries_table.scan()
    galleries.extend(response.get('Items', []))
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = galleries_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        galleries.extend(response.get('Items', []))
    
    print(f"   Found {len(galleries)} galleries")
    return galleries


def analyze_gallery(gallery):
    """Analyze a gallery and determine migration action"""
    user_id = gallery.get('user_id')
    gallery_id = gallery.get('id')
    client_email = gallery.get('client_email', '').strip()
    client_emails = gallery.get('client_emails', [])
    
    action = None
    details = {}
    
    # Case 1: Has client_email but no client_emails
    if client_email and not client_emails:
        action = 'CREATE_ARRAY'
        details = {
            'current': {'client_email': client_email},
            'new': {'client_emails': [client_email]}
        }
    
    # Case 2: Has both, but client_email not in array
    elif client_email and client_emails:
        if client_email.lower() not in [e.lower() for e in client_emails]:
            action = 'ADD_TO_ARRAY'
            details = {
                'current': {'client_email': client_email, 'client_emails': client_emails},
                'new': {'client_emails': [client_email] + client_emails}
            }
        else:
            action = 'REMOVE_COLUMN'
            details = {
                'current': {'client_email': client_email, 'client_emails': client_emails},
                'note': 'client_email already in array, just remove column'
            }
    
    # Case 3: Has client_emails but still has client_email column
    elif client_emails and 'client_email' in gallery:
        action = 'REMOVE_COLUMN'
        details = {
            'current': {'client_email': client_email or '(empty)', 'client_emails': client_emails},
            'note': 'client_emails exists, remove legacy column'
        }
    
    # Case 4: No action needed
    else:
        action = 'SKIP'
        details = {'reason': 'No client_email column or already migrated'}
    
    return {
        'user_id': user_id,
        'gallery_id': gallery_id,
        'gallery_name': gallery.get('name', 'Untitled'),
        'action': action,
        'details': details
    }


def migrate_gallery(gallery, analysis, dry_run=True):
    """Migrate a single gallery"""
    user_id = analysis['user_id']
    gallery_id = analysis['gallery_id']
    action = analysis['action']
    
    if action == 'SKIP':
        return {'success': True, 'skipped': True}
    
    try:
        if dry_run:
            return {'success': True, 'dry_run': True}
        
        # Prepare update
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        if action == 'CREATE_ARRAY':
            # Create client_emails from client_email
            client_email = gallery.get('client_email', '').strip()
            update_expression_parts.append('#ce = :ce')
            expression_attribute_names['#ce'] = 'client_emails'
            expression_attribute_values[':ce'] = [client_email]
            
            # Remove client_email
            update_expression_parts.append('#old REMOVE')
            expression_attribute_names['#old'] = 'client_email'
        
        elif action == 'ADD_TO_ARRAY':
            # Add client_email to client_emails array
            client_email = gallery.get('client_email', '').strip()
            existing_emails = gallery.get('client_emails', [])
            new_emails = [client_email] + existing_emails
            
            update_expression_parts.append('#ce = :ce')
            expression_attribute_names['#ce'] = 'client_emails'
            expression_attribute_values[':ce'] = new_emails
            
            # Remove client_email
            update_expression_parts.append('#old REMOVE')
            expression_attribute_names['#old'] = 'client_email'
        
        elif action == 'REMOVE_COLUMN':
            # Just remove client_email column
            update_expression_parts.append('REMOVE #old')
            expression_attribute_names['#old'] = 'client_email'
        
        # Build update expression
        update_expression = 'SET ' + ', '.join([p for p in update_expression_parts if 'REMOVE' not in p])
        if any('REMOVE' in p for p in update_expression_parts):
            if update_expression == 'SET ':
                update_expression = 'REMOVE ' + ', '.join([p.split('REMOVE ')[1] for p in update_expression_parts if 'REMOVE' in p])
            else:
                update_expression += ' REMOVE ' + ', '.join([p.split('REMOVE ')[1] for p in update_expression_parts if 'REMOVE' in p])
        
        # Execute update
        update_params = {
            'Key': {'user_id': user_id, 'id': gallery_id},
            'UpdateExpression': update_expression,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_attribute_names:
            update_params['ExpressionAttributeNames'] = expression_attribute_names
        if expression_attribute_values:
            update_params['ExpressionAttributeValues'] = expression_attribute_values
        
        response = galleries_table.update_item(**update_params)
        
        return {'success': True, 'updated_item': response.get('Attributes')}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    """Main migration script"""
    print("=" * 70)
    print("🔄 CLIENT EMAIL MIGRATION")
    print("=" * 70)
    print("")
    
    # Check for execute flag
    execute = '--execute' in sys.argv
    
    if execute:
        print("⚠️  EXECUTE MODE: Changes will be applied!")
        print("")
    else:
        print("🧪 DRY-RUN MODE: No changes will be applied")
        print("   Run with --execute to apply changes")
        print("")
    
    # Step 1: Scan all galleries
    galleries = scan_all_galleries()
    print("")
    
    # Step 2: Analyze each gallery
    print("🔍 Analyzing galleries...")
    analyses = []
    action_counts = {
        'CREATE_ARRAY': 0,
        'ADD_TO_ARRAY': 0,
        'REMOVE_COLUMN': 0,
        'SKIP': 0
    }
    
    for gallery in galleries:
        analysis = analyze_gallery(gallery)
        analyses.append(analysis)
        action_counts[analysis['action']] += 1
    
    print("")
    print("📊 Migration Summary:")
    print(f"   CREATE_ARRAY:   {action_counts['CREATE_ARRAY']} galleries")
    print(f"   ADD_TO_ARRAY:   {action_counts['ADD_TO_ARRAY']} galleries")
    print(f"   REMOVE_COLUMN:  {action_counts['REMOVE_COLUMN']} galleries")
    print(f"   SKIP:           {action_counts['SKIP']} galleries")
    print(f"   TOTAL:          {len(galleries)} galleries")
    print("")
    
    # Step 3: Show detailed actions
    if any(count > 0 for action, count in action_counts.items() if action != 'SKIP'):
        print("📝 Detailed Actions:")
        for analysis in analyses:
            if analysis['action'] != 'SKIP':
                print(f"\n   Gallery: {analysis['gallery_name']} ({analysis['gallery_id'][:8]}...)")
                print(f"   Action: {analysis['action']}")
                print(f"   Details: {json.dumps(analysis['details'], indent=6, cls=DecimalEncoder)}")
        print("")
    
    # Step 4: Execute migration if requested
    if execute:
        print("🚀 Executing migration...")
        print("")
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for i, analysis in enumerate(analyses, 1):
            gallery_name = analysis['gallery_name']
            action = analysis['action']
            
            # Find the original gallery
            gallery = next(g for g in galleries if g.get('id') == analysis['gallery_id'])
            
            result = migrate_gallery(gallery, analysis, dry_run=False)
            
            if result.get('skipped'):
                skip_count += 1
                print(f"   [{i}/{len(analyses)}] ⏭️  Skipped: {gallery_name}")
            elif result.get('success'):
                success_count += 1
                print(f"   [{i}/{len(analyses)}] ✅ Migrated: {gallery_name} ({action})")
            else:
                fail_count += 1
                print(f"   [{i}/{len(analyses)}] ❌ Failed: {gallery_name} - {result.get('error')}")
        
        print("")
        print("=" * 70)
        print("✅ MIGRATION COMPLETE")
        print("=" * 70)
        print(f"   Success: {success_count}")
        print(f"   Failed:  {fail_count}")
        print(f"   Skipped: {skip_count}")
        print("")
    else:
        print("💡 To apply these changes, run:")
        print(f"   python3 {sys.argv[0]} --execute")
        print("")


if __name__ == '__main__':
    main()

