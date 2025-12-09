"""
Content Security Policy Configuration
Implements CSP headers for frontend security
"""

# Content Security Policy directives
CSP_DIRECTIVES = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'unsafe-inline'",  # Required for React
        "https://www.googletagmanager.com",
        "https://www.google-analytics.com",
        "https://js.stripe.com",
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",  # Required for styled-components
        "https://fonts.googleapis.com",
    ],
    'font-src': [
        "'self'",
        "https://fonts.gstatic.com",
        "data:",
    ],
    'img-src': [
        "'self'",
        "data:",
        "blob:",
        "https:",  # Allow images from CDN/S3
    ],
    'connect-src': [
        "'self'",
        "https://api.stripe.com",
        "https://www.google-analytics.com",
    ],
    'frame-src': [
        "https://js.stripe.com",
        "https://hooks.stripe.com",
    ],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'none'"],
    'upgrade-insecure-requests': [],
}

def generate_csp_header(environment='production'):
    """
    Generate CSP header string
    
    Args:
        environment: 'development', 'staging', or 'production'
    """
    directives = CSP_DIRECTIVES.copy()
    
    # Development adjustments
    if environment == 'development':
        # Allow localhost connections
        directives['connect-src'].append('http://localhost:*')
        directives['connect-src'].append('ws://localhost:*')  # WebSocket for hot reload
    
    # Build CSP string
    csp_parts = []
    for directive, sources in directives.items():
        if sources:
            csp_parts.append(f"{directive} {' '.join(sources)}")
        else:
            csp_parts.append(directive)
    
    return '; '.join(csp_parts)

# Security headers configuration
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

def get_security_headers(environment='production'):
    """
    Get all security headers including CSP
    
    Returns: dict of headers
    """
    headers = SECURITY_HEADERS.copy()
    headers['Content-Security-Policy'] = generate_csp_header(environment)
    
    return headers

def add_security_headers_to_response(response, environment='production'):
    """
    Add security headers to API Gateway response
    
    Args:
        response: API Gateway response dict
        environment: 'development', 'staging', or 'production'
    
    Returns: Modified response with security headers
    """
    if 'headers' not in response:
        response['headers'] = {}
    
    security_headers = get_security_headers(environment)
    response['headers'].update(security_headers)
    
    return response

