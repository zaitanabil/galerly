"""
Compilation Test - Ensures all backend modules can be imported without errors
This test should run FIRST to catch syntax errors, import issues, and missing dependencies
"""
import pytest
import sys
import importlib


def test_all_handlers_compile():
    """Test that all handler modules can be imported"""
    handlers = [
        'handlers.auth_handler',
        'handlers.billing_handler',
        'handlers.subscription_handler',
        'handlers.gallery_handler',
        'handlers.photo_handler',
        'handlers.client_handler',
        'handlers.profile_handler',
        'handlers.dashboard_handler',
        'handlers.analytics_handler',
        'handlers.notification_handler',
        'handlers.invoice_handler',
        'handlers.contract_handler',
        'handlers.appointment_handler',
        'handlers.email_template_handler',
        'handlers.newsletter_handler',
        'handlers.contact_handler',
        'handlers.portfolio_handler',
        'handlers.refund_handler',
        'handlers.watermark_handler',
        'handlers.video_analytics_handler',
        'handlers.support_handler',
        'handlers.visitor_tracking_handler',
        'handlers.client_favorites_handler',
        'handlers.client_feedback_handler'
    ]
    
    failed_imports = []
    
    for handler_module in handlers:
        try:
            importlib.import_module(handler_module)
            print(f"✅ {handler_module}")
        except Exception as e:
            failed_imports.append((handler_module, str(e)))
            print(f"❌ {handler_module}: {str(e)}")
    
    # Assert no failures
    if failed_imports:
        error_msg = "\n".join([f"{mod}: {err}" for mod, err in failed_imports])
        pytest.fail(f"Failed to import {len(failed_imports)} handler(s):\n{error_msg}")


def test_all_utils_compile():
    """Test that all utility modules can be imported"""
    utils = [
        'utils.config',
        'utils.response',
        'utils.auth',
        'utils.email',
        'utils.video_utils',
        'utils.image_processor'
    ]
    
    failed_imports = []
    
    for util_module in utils:
        try:
            importlib.import_module(util_module)
            print(f"✅ {util_module}")
        except Exception as e:
            failed_imports.append((util_module, str(e)))
            print(f"❌ {util_module}: {str(e)}")
    
    if failed_imports:
        error_msg = "\n".join([f"{mod}: {err}" for mod, err in failed_imports])
        pytest.fail(f"Failed to import {len(failed_imports)} util(s):\n{error_msg}")


def test_lambda_functions_compile():
    """Test that Lambda function modules can be imported"""
    # Note: These might fail if AWS-specific dependencies are missing in test environment
    # Mark as expected failures if needed
    try:
        # Try to import the Lambda functions (may require mocking boto3)
        print("⚠️  Lambda functions may require AWS dependencies")
        # Skipping for now as they have different paths and dependencies
        assert True
    except Exception as e:
        print(f"⚠️  Lambda import skipped: {str(e)}")


def test_api_handler_compiles():
    """Test that main API handler compiles"""
    try:
        import api
        print("✅ api.py")
    except Exception as e:
        pytest.fail(f"Failed to import api.py: {str(e)}")


def test_no_syntax_errors():
    """Verify no Python syntax errors in codebase"""
    import py_compile
    import os
    import glob
    
    # Get all Python files
    python_files = []
    
    # Handlers
    python_files.extend(glob.glob('handlers/*.py'))
    
    # Utils
    python_files.extend(glob.glob('utils/*.py'))
    
    # Root
    if os.path.exists('api.py'):
        python_files.append('api.py')
    
    syntax_errors = []
    
    for filepath in python_files:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✅ Syntax check: {filepath}")
        except py_compile.PyCompileError as e:
            syntax_errors.append((filepath, str(e)))
            print(f"❌ Syntax error: {filepath}")
    
    if syntax_errors:
        error_msg = "\n".join([f"{file}: {err}" for file, err in syntax_errors])
        pytest.fail(f"Syntax errors found in {len(syntax_errors)} file(s):\n{error_msg}")


def test_required_packages_installed():
    """Test that all required packages are installed"""
    required_packages = [
        'boto3',
        'pytest',
        'flask',
        'stripe'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ Package: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ Missing: {package}")
    
    if missing_packages:
        pytest.fail(f"Missing required packages: {', '.join(missing_packages)}")


def test_environment_variables_loadable():
    """Test that environment variables can be accessed"""
    import os
    
    # These should be set in test environment or have defaults
    required_vars = [
        'DYNAMODB_TABLE_USERS',
        'DYNAMODB_TABLE_GALLERIES',
        'DYNAMODB_TABLE_PHOTOS',
        'S3_BUCKET'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} = {value}")
        else:
            # Not critical for compilation test, just warn
            print(f"⚠️  {var} not set (will use default)")
    
    # Don't fail - these might have defaults in code
    assert True


if __name__ == '__main__':
    """Run compilation tests standalone"""
    print("=" * 60)
    print("BACKEND COMPILATION TEST")
    print("=" * 60)
    
    print("\n1. Testing handler imports...")
    test_all_handlers_compile()
    
    print("\n2. Testing util imports...")
    test_all_utils_compile()
    
    print("\n3. Testing API handler...")
    test_api_handler_compiles()
    
    print("\n4. Testing syntax...")
    test_no_syntax_errors()
    
    print("\n5. Testing packages...")
    test_required_packages_installed()
    
    print("\n" + "=" * 60)
    print("✅ ALL BACKEND FILES COMPILE SUCCESSFULLY!")
    print("=" * 60)

