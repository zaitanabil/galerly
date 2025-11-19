#!/usr/bin/env python3
"""
Configure AWS Lambda Environment Variables
Automatically sets environment variables for Lambda function from .env file
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def load_env_file(env_path='.env'):
    """Load environment variables from .env file or environment variables"""
    env_vars = {}
    
    # First, try to load from environment variables (for CI/CD)
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_PRICE_PROFESSIONAL',
        'STRIPE_PRICE_BUSINESS',
        'STRIPE_WEBHOOK_SECRET',
        'FRONTEND_URL',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USER',
        'SMTP_PASSWORD',
        'FROM_EMAIL',
        'FROM_NAME'
    ]
    
    # Check if we're in CI/CD mode (environment variables take precedence)
    from_env = {}
    for var in required_vars:
        value = os.environ.get(var, '').strip()
        # FRONTEND_URL has a default value if not provided
        if var == 'FRONTEND_URL' and not value:
            value = 'https://galerly.com'
        from_env[var] = value
    
    if any(from_env.values()):
        print_info("Loading environment variables from system environment (CI/CD mode)...")
        env_vars = {k: v for k, v in from_env.items() if v}
        if env_vars:
            return env_vars
    
    # Fallback to .env file
    if not os.path.exists(env_path):
        print_warning(f"Environment file not found: {env_path}")
        print_info("Trying to load from system environment variables...")
        env_vars = {k: v for k, v in from_env.items() if v}
        if env_vars:
            return env_vars
        return None
    
    print_info(f"Loading environment variables from {env_path}...")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    return env_vars

def get_lambda_function_name():
    """Get Lambda function name from environment or prompt user"""
    # Try to get from environment variable
    function_name = os.environ.get('LAMBDA_FUNCTION_NAME')
    
    if not function_name:
        # Try common naming patterns
        print_info("Lambda function name not found. Please provide it.")
        print_info("Common patterns: galerly-api, galerly-backend, galerly-lambda")
        function_name = input(f"{Colors.BOLD}Enter Lambda function name: {Colors.RESET}").strip()
    
    if not function_name:
        print_error("Lambda function name is required")
        sys.exit(1)
    
    return function_name

def list_lambda_functions(lambda_client, region):
    """List all Lambda functions in the region"""
    try:
        print_info(f"Fetching Lambda functions in region {region}...")
        response = lambda_client.list_functions()
        functions = response.get('Functions', [])
        
        if not functions:
            print_warning("No Lambda functions found in this region")
            return []
        
        print_success(f"Found {len(functions)} Lambda function(s):")
        for i, func in enumerate(functions, 1):
            print(f"  {i}. {func['FunctionName']} (Runtime: {func.get('Runtime', 'N/A')})")
        
        return [f['FunctionName'] for f in functions]
    except ClientError as e:
        print_error(f"Failed to list Lambda functions: {str(e)}")
        return []

def update_lambda_environment(lambda_client, function_name, env_vars, required_vars, retry_on_conflict=True):
    """Update Lambda function environment variables with retry logic"""
    MAX_RETRIES = 5
    RETRY_DELAY = 5
    RETRY_COUNT = 0
    
    while RETRY_COUNT < MAX_RETRIES:
        try:
            if RETRY_COUNT > 0:
                print_warning(f"Retry attempt {RETRY_COUNT}/{MAX_RETRIES} (waiting {RETRY_DELAY}s)...")
                import time
                time.sleep(RETRY_DELAY)
                RETRY_DELAY = RETRY_DELAY * 2  # Exponential backoff
            
            # Get current configuration
            print_info(f"Fetching current configuration for {function_name}...")
            current_config = lambda_client.get_function_configuration(FunctionName=function_name)
            current_env = current_config.get('Environment', {}).get('Variables', {})
            
            print_info("Current environment variables:")
            for key in sorted(current_env.keys()):
                value = current_env[key]
                # Mask sensitive values
                if 'SECRET' in key or 'KEY' in key or 'PASSWORD' in key:
                    display_value = value[:10] + '...' if len(value) > 10 else '***'
                else:
                    display_value = value
                print(f"  {key} = {display_value}")
            
            # Merge with new variables
            updated_env = current_env.copy()
            
            # Add/update required variables
            missing_vars = []
            for var_name in required_vars:
                if var_name in env_vars:
                    updated_env[var_name] = env_vars[var_name]
                    print_success(f"Will set {var_name}")
                elif var_name == 'FRONTEND_URL':
                    # FRONTEND_URL has a default value
                    default_value = 'https://galerly.com'
                    updated_env[var_name] = default_value
                    print_warning(f"Missing {var_name}, using default: {default_value}")
                else:
                    missing_vars.append(var_name)
                    print_warning(f"Missing {var_name}")
            
            if missing_vars:
                print_error(f"Missing required variables: {', '.join(missing_vars)}")
                # In CI/CD mode, fail fast
                if os.environ.get('CI') or not sys.stdin.isatty():
                    sys.exit(1)
                response = input(f"{Colors.YELLOW}Continue anyway? (y/n): {Colors.RESET}").strip().lower()
                if response != 'y':
                    print_error("Aborted")
                    sys.exit(1)
            
            # Remove empty values
            updated_env = {k: v for k, v in updated_env.items() if v}
            
            # Update Lambda function
            print_info(f"Updating Lambda function {function_name}...")
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={
                    'Variables': updated_env
                }
            )
            
            print_success(f"Lambda function updated successfully!")
            print_info(f"Function ARN: {response['FunctionArn']}")
            
            # Show updated variables
            print_info("\nUpdated environment variables:")
            for key in sorted(updated_env.keys()):
                if key in required_vars:
                    value = updated_env[key]
                    if 'SECRET' in key or 'KEY' in key or 'PASSWORD' in key:
                        display_value = value[:10] + '...' if len(value) > 10 else '***'
                    else:
                        display_value = value
                    print(f"  {Colors.GREEN}{key}{Colors.RESET} = {display_value}")
            
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_msg = str(e)
            
            if error_code == 'ResourceNotFoundException':
                print_error(f"Lambda function '{function_name}' not found")
                print_info("Available functions:")
                list_lambda_functions(lambda_client, os.environ.get('AWS_REGION', 'us-east-1'))
                return False
            
            # Handle ResourceConflictException with retry
            if 'ResourceConflictException' in error_msg and retry_on_conflict:
                RETRY_COUNT += 1
                if RETRY_COUNT >= MAX_RETRIES:
                    print_error(f"Failed to update after {MAX_RETRIES} retries: {error_msg}")
                    return False
                continue
            else:
                print_error(f"Failed to update Lambda function: {error_msg}")
                return False
        except Exception as e:
            error_msg = str(e)
            if 'ResourceConflictException' in error_msg and retry_on_conflict:
                RETRY_COUNT += 1
                if RETRY_COUNT >= MAX_RETRIES:
                    print_error(f"Failed to update after {MAX_RETRIES} retries: {error_msg}")
                    return False
                continue
            else:
                print_error(f"Unexpected error: {error_msg}")
                import traceback
                traceback.print_exc()
                return False
    
    return False

def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("AWS Lambda Environment Variables Configuration")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print_error("AWS credentials not found")
            print_info("Please configure AWS credentials:")
            print_info("  - Run: aws configure")
            print_info("  - Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            sys.exit(1)
        
        print_success("AWS credentials found")
    except Exception as e:
        print_error(f"Failed to check AWS credentials: {str(e)}")
        sys.exit(1)
    
    # Get AWS region
    region = os.environ.get('AWS_REGION', 'us-east-1')
    print_info(f"Using AWS region: {region}")
    
    # Initialize Lambda client
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        print_success("Lambda client initialized")
    except Exception as e:
        print_error(f"Failed to initialize Lambda client: {str(e)}")
        sys.exit(1)
    
    # Load environment variables from .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    
    env_vars = load_env_file(env_path)
    if env_vars is None:
        sys.exit(1)
    
    print_success(f"Loaded {len(env_vars)} environment variables from .env")
    
    # Required Stripe and SMTP environment variables
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_PRICE_PROFESSIONAL',
        'STRIPE_PRICE_BUSINESS',
        'STRIPE_WEBHOOK_SECRET',
        'FRONTEND_URL',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USER',
        'SMTP_PASSWORD',
        'FROM_EMAIL',
        'FROM_NAME'
    ]
    
    # Get Lambda function name (from env or prompt)
    function_name = os.environ.get('LAMBDA_FUNCTION_NAME') or get_lambda_function_name()
    
    # List available functions if function not found
    print_info(f"Configuring Lambda function: {function_name}")
    
    # Update Lambda environment
    success = update_lambda_environment(lambda_client, function_name, env_vars, required_vars)
    
    if success:
        print(f"\n{Colors.BOLD}{Colors.GREEN}")
        print("=" * 60)
        print("Configuration Complete!")
        print("=" * 60)
        print(f"{Colors.RESET}")
        print_info("Your Lambda function environment variables have been updated.")
        print_info("You can now test the billing checkout flow.")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}")
        print("=" * 60)
        print("Configuration Failed")
        print("=" * 60)
        print(f"{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()

