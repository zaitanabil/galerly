"""
API Response utilities
"""
import json

def create_response(status_code, body):
    """Create API Gateway response with CORS headers (supports credentials) and CSP"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://galerly.com',  # Must be specific origin when using credentials
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,Cookie',
            'Access-Control-Allow-Credentials': 'true',
            # Content Security Policy - Protect against XSS
            'Content-Security-Policy': "default-src 'self'; img-src 'self' https://*.s3.amazonaws.com data:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com;",
            # Additional security headers
            'X-Content-Type-Options': 'nosniff',  # Prevent MIME-type sniffing
            'X-Frame-Options': 'DENY',  # Prevent clickjacking
            'X-XSS-Protection': '1; mode=block',  # Enable XSS filter
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'  # Force HTTPS
        },
        'body': json.dumps(body, default=str)
    }



