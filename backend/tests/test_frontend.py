"""
Test frontend JavaScript files for syntax and configuration
"""
import os
import sys
import re
import pytest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / 'frontend'
FRONTEND_JS_DIR = FRONTEND_DIR / 'js'


class TestFrontendStructure:
    """Test frontend file structure"""
    
    def test_required_html_files_exist(self):
        """Test required HTML files exist"""
        required_files = [
            'index.html',
            'auth.html',
            'dashboard.html',
            'gallery.html',
            'client-gallery.html',
            'new-gallery.html'
        ]
        
        for filename in required_files:
            filepath = FRONTEND_DIR / filename
            assert filepath.exists(), f"Missing required file: {filename}"
    
    def test_required_js_files_exist(self):
        """Test required JavaScript files exist"""
        required_files = [
            'config.js',
            'auth.js',
            'gallery.js',
            'gallery-loader.js',
            'client-dashboard.js'
        ]
        
        for filename in required_files:
            filepath = FRONTEND_JS_DIR / filename
            assert filepath.exists(), f"Missing required JS file: {filename}"
    
    def test_css_files_exist(self):
        """Test CSS files exist"""
        css_dir = FRONTEND_DIR / 'css'
        assert css_dir.exists(), "CSS directory missing"
        
        style_file = css_dir / 'style.css'
        assert style_file.exists(), "style.css missing"


class TestConfigJS:
    """Test frontend config.js configuration"""
    
    def test_config_file_exists(self):
        """Test config.js exists"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        assert config_file.exists(), "config.js not found"
    
    def test_config_has_cdn_url(self):
        """Test config.js defines CDN_URL"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        assert 'CDN_URL' in content, "CDN_URL not defined in config.js"
        assert 'cdn.galerly.com' in content or 'cloudfront.net' in content, "CDN URL not configured"
    
    def test_config_has_api_url(self):
        """Test config.js defines API_URL"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        assert 'API_URL' in content or 'API_BASE_URL' in content, "API URL not defined"
    
    def test_config_has_get_image_url_function(self):
        """Test config.js has getImageUrl function"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        assert 'getImageUrl' in content, "getImageUrl function not found"
        assert 'function getImageUrl' in content or 'getImageUrl =' in content, "getImageUrl not properly defined"
    
    def test_get_image_url_uses_cdn(self):
        """Test getImageUrl function uses CDN"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        # Find getImageUrl function
        if 'function getImageUrl' in content:
            func_start = content.index('function getImageUrl')
            func_end = content.index('}', func_start)
            func_content = content[func_start:func_end]
            
            # Should use CDN_URL
            assert 'CDN_URL' in func_content or 'cdn' in func_content.lower(), "getImageUrl doesn't use CDN"


class TestJavaScriptFiles:
    """Test JavaScript files for common issues"""
    
    def test_no_duplicate_get_image_url(self):
        """Test no duplicate getImageUrl functions in other JS files"""
        js_files = [
            'gallery-loader.js',
            'lightbox-slideshow.js',
            'client-dashboard.js'
        ]
        
        for filename in js_files:
            filepath = FRONTEND_JS_DIR / filename
            if filepath.exists():
                content = filepath.read_text()
                
                # Count occurrences of getImageUrl function definitions
                pattern = r'function\s+getImageUrl|const\s+getImageUrl\s*=|let\s+getImageUrl\s*='
                matches = re.findall(pattern, content)
                
                assert len(matches) == 0, f"{filename} has duplicate getImageUrl function (should use global from config.js)"
    
    def test_js_files_no_syntax_errors(self):
        """Test JS files don't have obvious syntax errors"""
        js_files = list(FRONTEND_JS_DIR.glob('*.js'))
        
        for js_file in js_files:
            content = js_file.read_text()
            
            # Check for common syntax errors
            # 1. Balanced braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            assert open_braces == close_braces, f"{js_file.name}: Unbalanced braces"
            
            # 2. Balanced parentheses
            open_parens = content.count('(')
            close_parens = content.count(')')
            assert open_parens == close_parens, f"{js_file.name}: Unbalanced parentheses"
            
            # 3. No trailing commas in object literals (basic check)
            assert ',}' not in content.replace(', }', ''), f"{js_file.name}: Trailing comma before closing brace"
    
    def test_no_hardcoded_s3_urls(self):
        """Test JS files don't contain hardcoded S3 URLs"""
        js_files = list(FRONTEND_JS_DIR.glob('*.js'))
        
        for js_file in js_files:
            content = js_file.read_text()
            
            # Should not have direct S3 URLs (except in comments or as examples)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('//') or line.strip().startswith('*'):
                    continue
                
                # Check for S3 URLs that aren't being replaced
                if '.s3.amazonaws.com' in line and 'replace' not in line.lower() and 'cdn' not in line.lower():
                    # Allow if it's clearly being converted to CDN
                    if 'includes' in line or 'match' in line:
                        continue
                    pytest.fail(f"{js_file.name}:{i} contains hardcoded S3 URL: {line.strip()}")


class TestImageLoading:
    """Test image loading logic"""
    
    def test_gallery_loader_exists(self):
        """Test gallery-loader.js exists"""
        loader_file = FRONTEND_JS_DIR / 'gallery-loader.js'
        assert loader_file.exists(), "gallery-loader.js not found"
    
    def test_gallery_loader_loads_images(self):
        """Test gallery-loader.js has image loading logic"""
        loader_file = FRONTEND_JS_DIR / 'gallery-loader.js'
        content = loader_file.read_text()
        
        # Should have image loading logic
        assert 'img' in content.lower() or 'image' in content.lower(), "No image loading logic found"
        assert 'src' in content.lower(), "No src attribute handling found"
    
    def test_lightbox_exists(self):
        """Test lightbox functionality exists"""
        lightbox_file = FRONTEND_JS_DIR / 'lightbox-slideshow.js'
        if lightbox_file.exists():
            content = lightbox_file.read_text()
            assert 'lightbox' in content.lower() or 'modal' in content.lower(), "Lightbox logic not found"


class TestConfigurationConsistency:
    """Test configuration consistency across files"""
    
    def test_api_url_not_localhost_in_prod(self):
        """Test API URL isn't hardcoded to localhost"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        # Should have conditional logic for localhost
        if 'localhost' in content:
            assert 'hostname' in content or 'location.host' in content, "localhost should be conditional"
    
    def test_cdn_url_consistent(self):
        """Test CDN URL is consistent"""
        config_file = FRONTEND_JS_DIR / 'config.js'
        content = config_file.read_text()
        
        # Extract CDN URL
        cdn_matches = re.findall(r'cdn\.galerly\.com|cloudfront\.net', content)
        
        if len(cdn_matches) > 1:
            # All should be the same domain
            unique_domains = set(cdn_matches)
            assert len(unique_domains) == 1, f"Multiple CDN domains found: {unique_domains}"

