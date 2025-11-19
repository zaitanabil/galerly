"""
Test CDN URL generation and CloudFront integration
"""
import os
import pytest
import requests
from unittest.mock import patch, Mock

# Import the CDN utilities
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.cdn_urls import get_cdn_url, get_photo_urls, IMAGE_SIZES


class TestCDNURLGeneration:
    """Test CDN URL generation logic"""
    
    def test_cdn_url_basic(self):
        """Test basic CDN URL generation"""
        s3_key = "gallery123/photo456.jpg"
        url = get_cdn_url(s3_key)
        
        assert url == "https://cdn.galerly.com/gallery123/photo456.jpg"
        assert url.startswith("https://cdn.galerly.com/")
        assert s3_key in url
    
    def test_cdn_url_with_special_characters(self):
        """Test CDN URL generation with special characters"""
        s3_key = "user-123/gallery_456/photo (1).jpg"
        url = get_cdn_url(s3_key)
        
        assert "https://cdn.galerly.com/" in url
        assert "gallery_456" in url
    
    def test_photo_urls_structure(self):
        """Test photo URLs contain all required variants"""
        s3_key = "test/photo.jpg"
        urls = get_photo_urls(s3_key)
        
        assert 'url' in urls
        assert 'medium_url' in urls
        assert 'thumbnail_url' in urls
        assert 'small_thumb_url' in urls
    
    def test_photo_urls_use_cdn(self):
        """Test that all photo URL variants use CloudFront CDN"""
        s3_key = "test/photo.jpg"
        urls = get_photo_urls(s3_key)
        
        for url_type, url in urls.items():
            assert url.startswith('https://cdn.galerly.com/'), f"{url_type} doesn't use CDN"
            assert s3_key in url, f"{url_type} doesn't contain S3 key"
    
    def test_image_sizes_configured(self):
        """Test that image sizes are properly configured"""
        assert 'thumbnail' in IMAGE_SIZES
        assert 'medium' in IMAGE_SIZES
        assert 'small' in IMAGE_SIZES
        
        # Verify sizes are tuples
        assert isinstance(IMAGE_SIZES['thumbnail'], tuple)
        assert len(IMAGE_SIZES['thumbnail']) == 2


@pytest.mark.integration
class TestCloudFrontIntegration:
    """Test CloudFront CDN integration (integration tests)"""
    
    def test_cloudfront_domain_resolves(self):
        """Test that CloudFront domain resolves"""
        try:
            response = requests.head("https://cdn.galerly.com", timeout=10, allow_redirects=True)
            # CloudFront should respond (200, 403, or 404 are all OK - means it's alive)
            assert response.status_code in [200, 403, 404], f"Unexpected status: {response.status_code}"
        except requests.exceptions.RequestException:
            pytest.skip("CloudFront domain not accessible (may not be configured yet)")
    
    def test_cloudfront_headers_present(self):
        """Test that CloudFront adds its headers"""
        try:
            response = requests.head("https://cdn.galerly.com", timeout=10, allow_redirects=True)
            headers = response.headers
            
            # Check for CloudFront headers
            has_cf = any('cf-' in k.lower() or 'cloudfront' in k.lower() for k in headers.keys())
            assert has_cf, "CloudFront headers not found"
        except requests.exceptions.RequestException:
            pytest.skip("CloudFront domain not accessible")
    
    def test_lambda_edge_no_errors(self):
        """Test that Lambda@Edge doesn't cause 502/503 errors"""
        try:
            response = requests.head("https://cdn.galerly.com/test.jpg", timeout=10, allow_redirects=True)
            # Should not be 502/503 (Lambda@Edge errors)
            assert response.status_code not in [502, 503], f"Lambda@Edge error: {response.status_code}"
        except requests.exceptions.RequestException:
            pytest.skip("CloudFront domain not accessible")


class TestCDNConfiguration:
    """Test CDN configuration"""
    
    def test_cdn_domain_environment_variable(self):
        """Test that CDN_DOMAIN environment variable is set"""
        cdn_domain = os.environ.get('CDN_DOMAIN')
        assert cdn_domain, "CDN_DOMAIN not set"
        assert 'galerly.com' in cdn_domain or 'cloudfront.net' in cdn_domain
    
    def test_cdn_url_no_hardcoded_values(self):
        """Test that CDN URLs don't contain hardcoded S3 URLs"""
        s3_key = "test/photo.jpg"
        url = get_cdn_url(s3_key)
        
        # Should NOT contain direct S3 URLs
        assert '.s3.amazonaws.com' not in url, "URL contains direct S3 reference"
        assert '.s3' not in url or 'cdn' in url, "URL might be using S3 instead of CDN"

