#!/usr/bin/env python3
"""
Generate GitHub Actions secrets and variables configuration from .env.production
Categorizes environment variables by sensitivity and generates exact commands
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Exact secrets (sensitive credentials)
SECRETS_EXACT = {
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'JWT_SECRET',
    'SMTP_PASSWORD',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'STRIPE_PUBLISHABLE_KEY'
}

# Pattern-based classification (only for items not in SECRETS_EXACT)
SECRET_PATTERNS = ['_SECRET_', '_PASSWORD_', '_TOKEN_', '_CREDENTIALS_']
VARIABLE_PATTERNS = [
    'TABLE', 'BUCKET', 'REGION', 'URL', 'PORT', 'HOST',
    'ENVIRONMENT', 'DEBUG', 'DOMAIN', 'FUNCTION_NAME', 'DISTRIBUTION_ID',
    'SIZE', 'LIMIT', 'DAYS', 'TIMEOUT', 'DELAY', 'MAX_AGE',
    'CURRENCY', 'METHOD', 'EMAIL', 'PRICE', 'VITE_', 'DEFAULT_',
    'LIFECYCLE_', 'FROM_', 'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER',
    'CDN_', 'API_', 'FRONTEND_', 'BACKEND_', 'WEBSITE_',
    'DYNAMODB_', 'S3_', 'CLOUDFRONT_', 'LAMBDA_'
]

def is_secret(key: str) -> bool:
    """Determine if environment variable should be a secret"""
    # Check exact matches first
    if key in SECRETS_EXACT:
        return True
    
    # Check patterns
    key_upper = key.upper()
    return any(pattern in key_upper for pattern in SECRET_PATTERNS)

def is_variable(key: str) -> bool:
    """Determine if environment variable should be a variable"""
    # Check if it's an exact secret first
    if key in SECRETS_EXACT:
        return False
    
    key_upper = key.upper()
    return any(key_upper.startswith(pattern) or pattern in key_upper for pattern in VARIABLE_PATTERNS)

def parse_env_file(filepath: Path) -> Dict[str, str]:
    """Parse .env file and return key-value pairs"""
    env_vars = {}
    
    if not filepath.exists():
        return env_vars
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments, empty lines, section headers
            if not line or line.startswith('#') or line.startswith('='):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                if key and value:
                    env_vars[key] = value
    
    return env_vars

def categorize_env_vars(env_vars: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Categorize environment variables into secrets and variables
    Returns: (secrets, variables)
    """
    secrets = {}
    variables = {}
    
    for key, value in env_vars.items():
        if is_secret(key):
            secrets[key] = value
        else:
            variables[key] = value
    
    return secrets, variables

def generate_gh_commands(secrets: Dict[str, str], variables: Dict[str, str], repo: str) -> List[str]:
    """Generate GitHub CLI commands to set secrets and variables"""
    commands = []
    
    # Generate secret commands
    for key, value in sorted(secrets.items()):
        # Escape single quotes in value
        escaped_value = value.replace("'", "'\\''")
        commands.append(f"gh secret set {key} --body '{escaped_value}' --repo {repo}")
    
    # Generate variable commands
    for key, value in sorted(variables.items()):
        # Escape single quotes in value
        escaped_value = value.replace("'", "'\\''")
        commands.append(f"gh variable set {key} --body '{escaped_value}' --repo {repo}")
    
    return commands

def generate_workflow_env(secrets: Dict[str, str], variables: Dict[str, str]) -> str:
    """Generate GitHub Actions workflow env section"""
    lines = ["env:"]
    
    # Variables can be directly referenced
    for key in sorted(variables.keys()):
        lines.append(f"  {key}: ${{{{ vars.{key} }}}}")
    
    # Secrets must be explicitly referenced
    for key in sorted(secrets.keys()):
        lines.append(f"  {key}: ${{{{ secrets.{key} }}}}")
    
    return '\n'.join(lines)

def main():
    # Find .env.production
    env_file = Path('.env.production')
    
    if not env_file.exists():
        print("ERROR: .env.production not found")
        return
    
    # Parse environment variables
    env_vars = parse_env_file(env_file)
    
    if not env_vars:
        print("ERROR: No environment variables found in .env.production")
        return
    
    # Categorize variables
    secrets, variables = categorize_env_vars(env_vars)
    
    # Repository - auto-detect from git remote or use environment variable
    repo = os.getenv('GITHUB_REPOSITORY')
    if not repo:
        try:
            import subprocess
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner'],
                capture_output=True, text=True, check=True
            )
            repo = result.stdout.strip()
        except:
            repo = 'OWNER/REPO'  # Placeholder if detection fails
    
    # Output directory
    output_dir = Path('.github/generated')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate commands
    commands = generate_gh_commands(secrets, variables, repo)
    
    # Write commands to file
    commands_file = output_dir / 'gh-commands.sh'
    with open(commands_file, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# GitHub Actions Secrets and Variables Setup\n')
        f.write('# Auto-generated from .env.production\n\n')
        f.write('set -e\n\n')
        f.write('\n'.join(commands))
        f.write('\n')
    
    # Make executable
    os.chmod(commands_file, 0o755)
    
    # Generate workflow env section
    workflow_env = generate_workflow_env(secrets, variables)
    workflow_file = output_dir / 'workflow-env.yml'
    with open(workflow_file, 'w') as f:
        f.write('# GitHub Actions Workflow Environment Configuration\n')
        f.write('# Copy this to your workflow .yml files\n\n')
        f.write(workflow_env)
        f.write('\n')
    
    # Generate summary
    summary_file = output_dir / 'summary.txt'
    with open(summary_file, 'w') as f:
        f.write('GitHub Actions Configuration Summary\n')
        f.write('='*80 + '\n\n')
        f.write(f'Total Variables: {len(env_vars)}\n')
        f.write(f'Secrets: {len(secrets)}\n')
        f.write(f'Variables: {len(variables)}\n\n')
        
        f.write('SECRETS (sensitive):\n')
        for key in sorted(secrets.keys()):
            f.write(f'  - {key}\n')
        f.write('\n')
        
        f.write('VARIABLES (non-sensitive):\n')
        for key in sorted(variables.keys()):
            f.write(f'  - {key}\n')
        f.write('\n')
        
        f.write('USAGE:\n')
        f.write(f'  1. Review .github/generated/summary.txt\n')
        f.write(f'  2. Run: .github/generated/gh-commands.sh\n')
        f.write(f'  3. Copy env from: .github/generated/workflow-env.yml\n')
    
    # Print summary to console
    print(f'\nGenerated configuration for {len(env_vars)} environment variables:')
    print(f'  Secrets: {len(secrets)}')
    print(f'  Variables: {len(variables)}')
    
    print(f'\nFiles created:')
    print(f'  - {commands_file}')
    print(f'  - {workflow_file}')
    print(f'  - {summary_file}')

if __name__ == '__main__':
    main()
