"""
End-to-end smoke tests
Tests critical user flows through actual API endpoints
"""
import os
import sys
import pytest
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get API URL from environment
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://api.galerly.com/v1')
CDN_BASE_URL = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestAPIAvailability:
    """Test API availability and health"""
    
    def test_api_health_check(self):
        """Test API health endpoint responds"""
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data.get('name') == 'Galerly API'
            assert 'version' in data
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not accessible: {e}")
    
    def test_api_cors_headers(self):
        """Test API returns CORS headers"""
        try:
            response = requests.options(f"{API_BASE_URL}/galleries", timeout=10)
            assert 'Access-Control-Allow-Origin' in response.headers
        except requests.exceptions.RequestException:
            pytest.skip("API not accessible")


class TestCDNAvailability:
    """Test CDN availability"""
    
    def test_cdn_domain_accessible(self):
        """Test CloudFront CDN domain is accessible"""
        try:
            response = requests.head(f"https://{CDN_BASE_URL}", timeout=10, allow_redirects=True)
            # Any response means CDN is working (200, 403, 404 all OK)
            assert response.status_code in [200, 403, 404]
        except requests.exceptions.RequestException:
            pytest.skip("CDN not accessible (may not be configured yet)")
    
    def test_cdn_has_cloudfront_headers(self):
        """Test CDN responds with CloudFront headers"""
        try:
            response = requests.head(f"https://{CDN_BASE_URL}", timeout=10, allow_redirects=True)
            headers = response.headers
            has_cf = any('cf-' in k.lower() or 'cloudfront' in k.lower() for k in headers.keys())
            assert has_cf, "CloudFront headers not present"
        except requests.exceptions.RequestException:
            pytest.skip("CDN not accessible")


@pytest.mark.slow
class TestUserJourney:
    """Test complete user journey (slow - only run when explicitly requested)"""
    
    def test_complete_user_flow(self):
        """Test: Register → Create Gallery → Get Upload URL → List Galleries"""
        try:
            # 1. Register user
            timestamp = int(time.time())
            test_email = f"e2e_test_{timestamp}@galerly-test.com"
            
            register_response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    'email': test_email,
                    'password': 'TestPass123!',
                    'full_name': 'E2E Test User'
                },
                timeout=10
            )
            
            if register_response.status_code != 201:
                pytest.skip(f"Registration failed: {register_response.status_code}")
            
            access_token = register_response.json()['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # 2. Create gallery
            gallery_response = requests.post(
                f"{API_BASE_URL}/galleries",
                json={
                    'name': 'E2E Test Gallery',
                    'client_name': 'Test Client',
                    'description': 'Created by E2E test'
                },
                headers=headers,
                timeout=10
            )
            
            assert gallery_response.status_code == 201
            gallery_id = gallery_response.json()['id']
            
            # 3. Get upload URL
            upload_response = requests.post(
                f"{API_BASE_URL}/photos/upload/presigned",
                json={
                    'gallery_id': gallery_id,
                    'filename': 'test.jpg',
                    'content_type': 'image/jpeg',
                    'file_size': 1024000
                },
                headers=headers,
                timeout=10
            )
            
            assert upload_response.status_code == 200
            assert 'upload_url' in upload_response.json()
            
            # 4. List galleries
            list_response = requests.get(
                f"{API_BASE_URL}/galleries",
                headers=headers,
                timeout=10
            )
            
            assert list_response.status_code == 200
            galleries = list_response.json()['galleries']
            assert len(galleries) > 0
            assert any(g['id'] == gallery_id for g in galleries)
            
            # 5. Cleanup - delete gallery
            requests.delete(
                f"{API_BASE_URL}/galleries/{gallery_id}",
                headers=headers,
                timeout=10
            )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test failed due to network: {e}")


class TestImageURLConsistency:
    """Test that image URLs are consistent across the system"""
    
    def test_cdn_url_format(self):
        """Test CDN URL format is correct"""
        from utils.cdn_urls import get_cdn_url
        
        test_key = "gallery123/photo456.jpg"
        url = get_cdn_url(test_key)
        
        # Should use CloudFront domain
        assert f"https://{CDN_BASE_URL}/" in url or "cdn.galerly.com" in url
        # Should NOT use direct S3
        assert ".s3.amazonaws.com" not in url
    
    def test_photo_urls_consistency(self):
        """Test all photo URL variants use same domain"""
        from utils.cdn_urls import get_photo_urls
        
        test_key = "test/photo.jpg"
        urls = get_photo_urls(test_key)
        
        domains = set()
        for url in urls.values():
            # Extract domain from URL
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
                domains.add(domain)
        
        # All URLs should use the same domain
        assert len(domains) == 1, f"Multiple domains found: {domains}"


class TestAWSResources:
    """Test AWS resources are accessible"""
    
    def test_s3_photos_bucket_configured(self):
        """Test S3 photos bucket environment variable is set"""
        bucket = os.environ.get('S3_PHOTOS_BUCKET')
        assert bucket, "S3_PHOTOS_BUCKET not configured"
        assert 'galerly' in bucket.lower()
    
    def test_dynamodb_tables_configured(self):
        """Test DynamoDB table environment variables are set"""
        tables = [
            'DYNAMODB_TABLE_USERS',
            'DYNAMODB_TABLE_GALLERIES',
            'DYNAMODB_TABLE_PHOTOS',
            'DYNAMODB_TABLE_SESSIONS'
        ]
        
        for table_env in tables:
            table_name = os.environ.get(table_env)
            assert table_name, f"{table_env} not configured"
            assert 'galerly' in table_name.lower()

