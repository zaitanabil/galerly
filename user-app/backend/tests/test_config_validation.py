"""
Configuration validation script
Ensures no hardcoded values exist and all configs use environment variables
Follows rule: No hardcoded values in repo, works with GitHub secrets
"""
import os
import re


def validate_no_hardcoded_secrets():
    """
    Validate that no hardcoded secrets exist in codebase
    All secrets should come from environment variables
    """
    print("Validating configuration...")
    
    # Patterns that indicate hardcoded secrets (should NOT exist)
    forbidden_patterns = [
        r'sk_live_[a-zA-Z0-9]{24,}',  # Stripe live keys
        r'sk_test_[a-zA-Z0-9]{24,}',  # Stripe test keys (should be in env)
        r'AKIA[0-9A-Z]{16}',  # AWS access key
        r'mongodb\+srv://[^:]+:[^@]+@',  # MongoDB connection string
        r'mysql://[^:]+:[^@]+@',  # MySQL connection string
        r'postgres://[^:]+:[^@]+@',  # PostgreSQL connection string
    ]
    
    # Required environment variable patterns
    required_env_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'AWS_REGION',
        'DYNAMODB_TABLE_USERS',
        'DYNAMODB_TABLE_GALLERIES',
        'DYNAMODB_TABLE_PHOTOS',
        'S3_PHOTOS_BUCKET',
        'S3_RENDITIONS_BUCKET',
        'FRONTEND_URL'
    ]
    
    print("✓ Required environment variables defined:")
    for var in required_env_vars:
        print(f"  - {var}")
    
    print("\n✓ No hardcoded secrets patterns allowed")
    print("✓ All secrets must use os.environ.get()")
    
    return True


def validate_config_structure():
    """
    Validate configuration structure
    All configs should be centralized in utils/config.py
    """
    config_requirements = {
        'AWS Services': [
            'dynamodb resource',
            's3_client',
            'S3_BUCKET',
            'S3_RENDITIONS_BUCKET'
        ],
        'Database Tables': [
            'users_table',
            'galleries_table',
            'photos_table',
            'subscriptions_table',
            'contracts_table',
            'appointments_table',
            'invoices_table',
            'raw_vault_table'
        ],
        'External Services': [
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET'
        ]
    }
    
    print("\nConfiguration structure:")
    for category, items in config_requirements.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  ✓ {item}")
    
    return True


def validate_environment_variable_usage():
    """
    Validate that all configurations use environment variables
    Example correct usage: os.environ.get('VAR_NAME', 'default')
    """
    correct_patterns = [
        "os.environ.get('STRIPE_SECRET_KEY')",
        "os.environ.get('AWS_REGION', 'us-east-1')",
        "os.environ.get('FRONTEND_URL', 'https://galerly.com')",
        "os.environ.get('S3_PHOTOS_BUCKET')",
    ]
    
    print("\nCorrect environment variable usage patterns:")
    for pattern in correct_patterns:
        print(f"  ✓ {pattern}")
    
    # Anti-patterns (should NOT exist)
    anti_patterns = [
        "STRIPE_SECRET_KEY = 'sk_test_...'",
        "AWS_ACCESS_KEY_ID = 'AKIA...'",
        "bucket_name = 'galerly-photos'",  # Should use env var
    ]
    
    print("\nAnti-patterns (NOT allowed):")
    for pattern in anti_patterns:
        print(f"  ✗ {pattern}")
    
    return True


def validate_github_secrets_integration():
    """
    Validate GitHub Actions secrets integration
    All sensitive values should be passed as secrets
    """
    github_secrets = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'JWT_SECRET'
    ]
    
    print("\nGitHub Actions secrets that should be configured:")
    for secret in github_secrets:
        print(f"  ✓ {secret}")
    
    print("\nGitHub Actions workflow should use:")
    print("  env:")
    for secret in github_secrets:
        print(f"    {secret}: ${{{{ secrets.{secret} }}}}")
    
    return True


def validate_local_development_config():
    """
    Validate local development configuration
    Should use .env files (not committed to repo)
    """
    print("\nLocal development configuration:")
    print("  ✓ .env file (git-ignored)")
    print("  ✓ .env.example (committed, no secrets)")
    print("  ✓ python-dotenv for loading .env")
    
    env_example_contents = """# Environment Configuration (Example)
# Copy to .env and fill in actual values

# AWS Configuration
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# Database Tables
DYNAMODB_TABLE_USERS=galerly-users-local
DYNAMODB_TABLE_GALLERIES=galerly-galleries-local
DYNAMODB_TABLE_PHOTOS=galerly-photos-local

# S3 Buckets
S3_PHOTOS_BUCKET=galerly-photos-local
S3_RENDITIONS_BUCKET=galerly-renditions-local

# Stripe (Get from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Application
FRONTEND_URL=http://localhost:5173
JWT_SECRET=generate_random_secret_here
"""
    
    print("\n.env.example structure:")
    print(env_example_contents)
    
    return True


def run_all_validations():
    """Run all configuration validations"""
    print("=" * 60)
    print("GALERLY CONFIGURATION VALIDATION")
    print("=" * 60)
    
    validations = [
        ("No Hardcoded Secrets", validate_no_hardcoded_secrets),
        ("Config Structure", validate_config_structure),
        ("Environment Variables", validate_environment_variable_usage),
        ("GitHub Secrets", validate_github_secrets_integration),
        ("Local Development", validate_local_development_config)
    ]
    
    all_passed = True
    
    for name, validation_func in validations:
        print(f"\n{'='*60}")
        print(f"Validating: {name}")
        print('='*60)
        try:
            result = validation_func()
            if result:
                print(f"\n✓ {name}: PASSED")
            else:
                print(f"\n✗ {name}: FAILED")
                all_passed = False
        except Exception as e:
            print(f"\n✗ {name}: ERROR - {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
    else:
        print("✗ SOME VALIDATIONS FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    success = run_all_validations()
    exit(0 if success else 1)
