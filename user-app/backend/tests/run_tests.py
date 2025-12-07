#!/usr/bin/env python3
"""
Comprehensive test runner for all Galerly backend tests.
Runs all tests and generates coverage reports.
"""
import subprocess
import sys
import os

def run_tests():
    """Run all backend tests with coverage."""
    print("=" * 80)
    print("GALERLY BACKEND TEST SUITE")
    print("=" * 80)
    print()
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_dir)
    
    # Run pytest with coverage
    cmd = [
        'pytest',
        'tests/',
        '-v',
        '--cov=handlers',
        '--cov=utils',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov',
        '--tb=short',
        '-ra'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    print()
    print(f"HTML Coverage Report: file://{backend_dir}/htmlcov/index.html")
    print()
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())

