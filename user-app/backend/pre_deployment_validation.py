#!/usr/bin/env python3
"""
Pre-Deployment Validation Script
Verifies all plan enforcement implementations before production deployment
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

def print_success(text):
    print(f"{GREEN}✓{NC} {text}")

def print_error(text):
    print(f"{RED}✗{NC} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{NC} {text}")

def check_file_has_content(file_path: str, content: str) -> bool:
    """Check if file contains specific content"""
    try:
        with open(file_path, 'r') as f:
            return content in f.read()
    except FileNotFoundError:
        return False

def check_critical_fixes() -> Tuple[int, int]:
    """Verify all critical fixes are in place"""
    print_header("Critical Fixes Verification")
    
    passed = 0
    failed = 0
    
    checks = [
        {
            'name': 'Storage limit in photo_handler.py',
            'file': 'handlers/photo_handler.py',
            'content': 'enforce_storage_limit'
        },
        {
            'name': 'Storage limit in multipart_upload_handler.py',
            'file': 'handlers/multipart_upload_handler.py',
            'content': 'enforce_storage_limit'
        },
        {
            'name': 'File validation in photo_handler.py',
            'file': 'handlers/photo_handler.py',
            'content': 'validate_image_data'
        },
        {
            'name': 'Client favorites plan check',
            'file': 'handlers/client_favorites_handler.py',
            'content': "get('client_favorites')"
        },
        {
            'name': 'Invoice role check',
            'file': 'handlers/invoice_handler.py',
            'content': "role') != 'photographer"
        },
        {
            'name': 'Contract role check',
            'file': 'handlers/contract_handler.py',
            'content': "role') != 'photographer"
        }
    ]
    
    for check in checks:
        if check_file_has_content(check['file'], check['content']):
            print_success(check['name'])
            passed += 1
        else:
            print_error(f"{check['name']} - NOT FOUND")
            failed += 1
    
    return passed, failed

def check_enhancements() -> Tuple[int, int]:
    """Verify all enhancements are present"""
    print_header("Production Enhancements Verification")
    
    passed = 0
    failed = 0
    
    files = [
        ('utils/rate_limiter.py', 'Rate limiting system'),
        ('utils/plan_monitoring.py', 'Violation monitoring'),
        ('handlers/admin_plan_handler.py', 'Admin tools'),
        ('utils/query_optimization.py', 'Query optimization'),
        ('utils/plan_enforcement.py', 'Enforcement middleware'),
        ('tests/test_plan_enforcement.py', 'Test suite')
    ]
    
    for file_path, name in files:
        if Path(file_path).exists():
            print_success(name)
            passed += 1
        else:
            print_error(f"{name} - FILE MISSING")
            failed += 1
    
    return passed, failed

def check_schemas() -> Tuple[int, int]:
    """Verify DynamoDB schemas exist"""
    print_header("Database Schema Verification")
    
    passed = 0
    failed = 0
    
    schemas = [
        'schemas/rate-limits-table.json',
        'schemas/plan-violations-table.json',
        'schemas/README.md'
    ]
    
    for schema in schemas:
        if Path(schema).exists():
            print_success(schema)
            passed += 1
        else:
            print_error(f"{schema} - MISSING")
            failed += 1
    
    return passed, failed

def check_api_integration() -> Tuple[int, int]:
    """Verify API integration"""
    print_header("API Integration Verification")
    
    passed = 0
    failed = 0
    
    api_file = 'api.py'
    
    checks = [
        ('Admin endpoints integrated', '/v1/admin/'),
        ('Rate limiting imported', 'rate_limit'),
        ('Admin handler imported', 'admin_plan_handler')
    ]
    
    for name, content in checks:
        if check_file_has_content(api_file, content):
            print_success(name)
            passed += 1
        else:
            print_error(f"{name} - NOT FOUND")
            failed += 1
    
    return passed, failed

def check_documentation() -> Tuple[int, int]:
    """Verify documentation exists"""
    print_header("Documentation Verification")
    
    passed = 0
    failed = 0
    
    docs = [
        ('DEPLOYMENT_GUIDE.md', 'Deployment guide'),
        ('FINAL_IMPLEMENTATION_REPORT.md', 'Implementation report')
    ]
    
    for file, name in docs:
        if Path(f'../../{file}').exists():
            print_success(name)
            passed += 1
        else:
            print_error(f"{name} - MISSING")
            failed += 1
    
    return passed, failed

def check_environment_vars() -> Tuple[int, int]:
    """Check if required environment variables are documented"""
    print_header("Environment Variables Check")
    
    passed = 0
    failed = 0
    
    required_vars = [
        'DYNAMODB_TABLE_RATE_LIMITS',
        'DYNAMODB_TABLE_PLAN_VIOLATIONS'
    ]
    
    for var in required_vars:
        # Check if documented in schema README
        if check_file_has_content('schemas/README.md', var):
            print_success(f"{var} documented")
            passed += 1
        else:
            print_error(f"{var} not documented")
            failed += 1
    
    return passed, failed

def main():
    print(f"\n{BLUE}╔{'═'*58}╗{NC}")
    print(f"{BLUE}║  Galerly Pre-Deployment Validation                        ║{NC}")
    print(f"{BLUE}║  Version: 3.1.0                                            ║{NC}")
    print(f"{BLUE}╚{'═'*58}╝{NC}\n")
    
    # Change to backend directory
    os.chdir(Path(__file__).parent)
    
    total_passed = 0
    total_failed = 0
    
    # Run all checks
    p, f = check_critical_fixes()
    total_passed += p
    total_failed += f
    
    p, f = check_enhancements()
    total_passed += p
    total_failed += f
    
    p, f = check_schemas()
    total_passed += p
    total_failed += f
    
    p, f = check_api_integration()
    total_passed += p
    total_failed += f
    
    p, f = check_documentation()
    total_passed += p
    total_failed += f
    
    p, f = check_environment_vars()
    total_passed += p
    total_failed += f
    
    # Summary
    print_header("Validation Summary")
    
    total_checks = total_passed + total_failed
    percentage = (total_passed / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Total Checks: {total_checks}")
    print(f"{GREEN}Passed: {total_passed}{NC}")
    print(f"{RED}Failed: {total_failed}{NC}")
    print(f"Success Rate: {percentage:.1f}%")
    print("")
    
    if total_failed == 0:
        print(f"{GREEN}{'='*60}{NC}")
        print(f"{GREEN}✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT{NC}")
        print(f"{GREEN}{'='*60}{NC}")
        print("")
        print("Next steps:")
        print("  1. Run tests: pytest tests/test_plan_enforcement.py -v")
        print("  2. Setup infrastructure: cd ../../../dev_tools && ./setup-plan-enforcement.sh")
        print("  3. Deploy to production")
        return 0
    else:
        print(f"{RED}{'='*60}{NC}")
        print(f"{RED}❌ VALIDATION FAILED - FIX ISSUES BEFORE DEPLOYMENT{NC}")
        print(f"{RED}{'='*60}{NC}")
        print("")
        print("Review failed checks above and fix before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
