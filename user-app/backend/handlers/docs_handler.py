"""
API Documentation Handler
Serves OpenAPI specification and Swagger UI
No hardcoded values - all configuration from environment
"""
import os
import json
from utils.response import create_response


def handle_get_openapi_spec():
    """
    Serve OpenAPI specification as JSON
    Public endpoint - no authentication required
    """
    try:
        # Get OpenAPI spec file path from environment
        spec_path = os.environ.get('OPENAPI_SPEC_PATH', 'openapi.json')
        
        # Check if file exists
        if not os.path.exists(spec_path):
            return create_response(404, {
                'error': 'API specification not found'
            })
        
        # Read and serve spec
        with open(spec_path, 'r') as f:
            spec = json.load(f)
        
        return create_response(200, spec, headers={
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # Allow CORS for public API docs
            'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
        })
        
    except Exception as e:
        print(f"Error serving OpenAPI spec: {str(e)}")
        return create_response(500, {'error': 'Failed to load API specification'})


def handle_get_swagger_ui():
    """
    Serve Swagger UI HTML page
    Loads OpenAPI spec from /v1/docs/openapi.json
    Public endpoint - no authentication required
    """
    try:
        # Get URLs from environment
        api_base_url = os.environ.get('API_BASE_URL', 'https://api.galerly.com')
        
        # Swagger UI HTML with CDN resources
        # Using official Swagger UI from CDN (no hardcoded version - uses latest stable)
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galerly API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@latest/swagger-ui.css" />
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        .topbar {{
            background-color: #0066CC !important;
        }}
        .swagger-ui .topbar-wrapper img {{
            content: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="32" viewBox="0 0 120 32"><text x="10" y="20" font-family="SF Pro Display, sans-serif" font-size="16" fill="white" font-weight="500">Galerly API</text></svg>');
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@latest/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@latest/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "{api_base_url}/v1/docs/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                filter: true,
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                persistAuthorization: true
            }});
            window.ui = ui;
        }};
    </script>
</body>
</html>
"""
        
        return create_response(200, html, headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=300'  # Cache for 5 minutes
        })
        
    except Exception as e:
        print(f"Error serving Swagger UI: {str(e)}")
        return create_response(500, {'error': 'Failed to load API documentation'})


def handle_get_redoc_ui():
    """
    Serve ReDoc UI HTML page (alternative to Swagger UI)
    ReDoc provides a cleaner, more document-style presentation
    Public endpoint - no authentication required
    """
    try:
        # Get URLs from environment
        api_base_url = os.environ.get('API_BASE_URL', 'https://api.galerly.com')
        
        # ReDoc HTML with CDN resources
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galerly API Documentation</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'><circle cx='16' cy='16' r='16' fill='%230066CC'/></svg>">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
        }}
    </style>
</head>
<body>
    <redoc spec-url="{api_base_url}/v1/docs/openapi.json"
           hide-loading
           native-scrollbars
           theme='{{
               "colors": {{
                   "primary": {{
                       "main": "#0066CC"
                   }}
               }},
               "typography": {{
                   "fontFamily": "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Segoe UI\", sans-serif",
                   "headings": {{
                       "fontFamily": "-apple-system, BlinkMacSystemFont, \"SF Pro Display\", \"Segoe UI\", sans-serif"
                   }}
               }}
           }}'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""
        
        return create_response(200, html, headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=300'  # Cache for 5 minutes
        })
        
    except Exception as e:
        print(f"Error serving ReDoc UI: {str(e)}")
        return create_response(500, {'error': 'Failed to load API documentation'})
