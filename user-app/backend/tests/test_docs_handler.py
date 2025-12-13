"""
Tests for API documentation handler
Verifies OpenAPI spec serving and Swagger UI
"""
import pytest
import json
from unittest.mock import patch, mock_open, MagicMock


class TestDocsHandler:
    """Tests for documentation endpoints"""
    
    def test_get_openapi_spec_success(self):
        """Test serving OpenAPI specification"""
        from handlers.docs_handler import handle_get_openapi_spec
        
        # Mock spec data
        mock_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Galerly API",
                "version": "3.0.0"
            },
            "paths": {}
        }
        
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_spec))):
            with patch('os.path.exists', return_value=True):
                response = handle_get_openapi_spec()
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['openapi'] == '3.0.3'
        assert body['info']['title'] == 'Galerly API'
        
        # Verify CORS headers
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Cache-Control' in response['headers']
    
    def test_get_openapi_spec_file_not_found(self):
        """Test handling missing OpenAPI spec file"""
        from handlers.docs_handler import handle_get_openapi_spec
        
        # Mock file not exists
        with patch('os.path.exists', return_value=False):
            response = handle_get_openapi_spec()
        
        # Should return 404
        assert response['statusCode'] == 404
        
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_get_openapi_spec_read_error(self):
        """Test handling file read errors"""
        from handlers.docs_handler import handle_get_openapi_spec
        
        # Mock file exists but read fails
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception('Read error')):
                response = handle_get_openapi_spec()
        
        # Should return 500
        assert response['statusCode'] == 500
        
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_get_swagger_ui(self):
        """Test serving Swagger UI HTML"""
        from handlers.docs_handler import handle_get_swagger_ui
        
        response = handle_get_swagger_ui()
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/html; charset=utf-8'
        
        # Verify HTML contains Swagger UI elements
        html = response['body']
        assert 'swagger-ui' in html
        assert 'SwaggerUIBundle' in html
        assert 'Galerly API' in html
    
    def test_swagger_ui_uses_correct_api_url(self):
        """Test Swagger UI points to correct API URL"""
        from handlers.docs_handler import handle_get_swagger_ui
        
        # Mock environment variable
        with patch.dict('os.environ', {'API_BASE_URL': 'https://api.test.com'}):
            response = handle_get_swagger_ui()
        
        html = response['body']
        assert 'https://api.test.com/v1/docs/openapi.json' in html
    
    def test_get_redoc_ui(self):
        """Test serving ReDoc UI HTML"""
        from handlers.docs_handler import handle_get_redoc_ui
        
        response = handle_get_redoc_ui()
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/html; charset=utf-8'
        
        # Verify HTML contains ReDoc elements
        html = response['body']
        assert '<redoc' in html
        assert 'redoc.standalone.js' in html
        assert 'Galerly API' in html
    
    def test_redoc_ui_uses_correct_api_url(self):
        """Test ReDoc UI points to correct API URL"""
        from handlers.docs_handler import handle_get_redoc_ui
        
        # Mock environment variable
        with patch.dict('os.environ', {'API_BASE_URL': 'https://api.test.com'}):
            response = handle_get_redoc_ui()
        
        html = response['body']
        assert 'https://api.test.com/v1/docs/openapi.json' in html
    
    def test_documentation_has_cors_headers(self):
        """Test that all documentation endpoints allow CORS"""
        from handlers.docs_handler import (
            handle_get_openapi_spec,
            handle_get_swagger_ui,
            handle_get_redoc_ui
        )
        
        mock_spec = {"openapi": "3.0.3"}
        
        # Test OpenAPI spec CORS
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_spec))):
            with patch('os.path.exists', return_value=True):
                response = handle_get_openapi_spec()
                assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        # Test Swagger UI CORS
        response = handle_get_swagger_ui()
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        # Test ReDoc UI CORS
        response = handle_get_redoc_ui()
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    def test_documentation_has_cache_headers(self):
        """Test that documentation endpoints have appropriate caching"""
        from handlers.docs_handler import (
            handle_get_openapi_spec,
            handle_get_swagger_ui
        )
        
        mock_spec = {"openapi": "3.0.3"}
        
        # Test OpenAPI spec caching (1 hour)
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_spec))):
            with patch('os.path.exists', return_value=True):
                response = handle_get_openapi_spec()
                assert 'Cache-Control' in response['headers']
                assert 'max-age=3600' in response['headers']['Cache-Control']
        
        # Test Swagger UI caching (5 minutes)
        response = handle_get_swagger_ui()
        assert 'Cache-Control' in response['headers']
        assert 'max-age=300' in response['headers']['Cache-Control']


class TestOpenAPIGeneration:
    """Tests for OpenAPI spec generation"""
    
    def test_openapi_spec_file_exists(self):
        """Test that openapi.json file was generated"""
        import os
        
        # Check if file exists in backend directory
        spec_path = 'openapi.json'
        assert os.path.exists(spec_path), "openapi.json should be generated"
    
    def test_openapi_spec_is_valid_json(self):
        """Test that generated spec is valid JSON"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        # Verify basic structure
        assert 'openapi' in spec
        assert 'info' in spec
        assert 'paths' in spec
    
    def test_openapi_spec_has_required_info(self):
        """Test that spec has required metadata"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        # Verify info section
        assert spec['info']['title'] == 'Galerly API'
        assert spec['info']['version'] == '3.0.0'
        assert 'description' in spec['info']
        assert 'contact' in spec['info']
    
    def test_openapi_spec_has_servers(self):
        """Test that spec defines API servers"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        assert 'servers' in spec
        assert len(spec['servers']) >= 1
        assert any('api.galerly.com' in server['url'] for server in spec['servers'])
    
    def test_openapi_spec_has_security_schemes(self):
        """Test that spec defines security schemes"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        assert 'components' in spec
        assert 'securitySchemes' in spec['components']
        assert 'cookieAuth' in spec['components']['securitySchemes']
    
    def test_openapi_spec_has_endpoints(self):
        """Test that spec includes API endpoints"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        # Should have paths defined
        assert 'paths' in spec
        assert len(spec['paths']) > 0
        
        # Check for key endpoints
        paths = spec['paths']
        assert '/v1/auth/register' in paths or any('register' in path for path in paths)
        assert '/v1/galleries' in paths or any('galleries' in path for path in paths)
    
    def test_openapi_spec_has_watermark_endpoints(self):
        """Test that watermark endpoints are documented"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        paths = spec['paths']
        
        # Check for watermark endpoints
        assert '/v1/profile/watermark-logo' in paths
        assert '/v1/profile/watermark-settings' in paths
        assert '/v1/profile/watermark-batch-apply' in paths
    
    def test_openapi_spec_has_custom_domain_endpoints(self):
        """Test that custom domain endpoints are documented"""
        import json
        
        with open('openapi.json', 'r') as f:
            spec = json.load(f)
        
        paths = spec['paths']
        
        # Check for custom domain endpoints
        assert '/v1/portfolio/custom-domain/setup' in paths
        assert '/v1/portfolio/custom-domain/status' in paths


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
