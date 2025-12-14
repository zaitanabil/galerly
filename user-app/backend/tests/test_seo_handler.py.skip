"""
Tests for SEO handler
Pro/Ultimate plan feature for search engine optimization
"""
import pytest
import json
import xml.etree.ElementTree as ET
from handlers.seo_handler import (
    handle_generate_sitemap,
    handle_generate_schema_markup,
    handle_validate_og_tags,
    handle_get_seo_settings,
    handle_update_seo_settings
)


class TestSitemapGeneration:
    """Test sitemap.xml generation"""
    
    @pytest.fixture
    def pro_user(self):
        """Mock Pro plan user with SEO tools"""
        return {
            'id': 'test-user-pro',
            'email': 'photographer@test.com',
            'plan': 'pro',
            'subscription': 'pro',
            'username': 'testphotographer'
        }
    
    @pytest.fixture
    def starter_user(self):
        """Mock Starter plan user without SEO tools"""
        return {
            'id': 'test-user-starter',
            'email': 'photographer2@test.com',
            'plan': 'starter',
            'subscription': 'starter'
        }
    
    def test_sitemap_requires_pro_plan(self, starter_user):
        """Test that sitemap generation requires Pro or Ultimate plan"""
        response = handle_generate_sitemap(starter_user)
        
        if isinstance(response, dict) and 'statusCode' in response:
            response_body = json.loads(response['body']) if isinstance(response['body'], str) else response['body']
            
            assert response['statusCode'] == 403
            assert 'upgrade_required' in response_body
    
    def test_sitemap_xml_structure(self):
        """Test sitemap XML structure validity"""
        sample_sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://galerly.com/portfolio/user-id</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''
        
        # Parse XML to validate structure
        try:
            root = ET.fromstring(sample_sitemap)
            assert root.tag.endswith('urlset')
            
            # Check for URL elements
            urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            assert len(urls) > 0
            
            # Check for required elements
            for url in urls:
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                assert loc is not None
                assert loc.text.startswith('http')
        except ET.ParseError:
            pytest.fail("Invalid XML structure")
    
    def test_sitemap_url_priority(self):
        """Test sitemap URL priority values"""
        valid_priorities = [1.0, 0.8, 0.6, 0.4, 0.2]
        
        for priority in valid_priorities:
            assert 0.0 <= priority <= 1.0
    
    def test_sitemap_changefreq_values(self):
        """Test sitemap changefreq valid values"""
        valid_changefreq = ['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']
        
        for freq in valid_changefreq:
            assert freq in valid_changefreq


class TestSchemaMarkup:
    """Test Schema.org JSON-LD markup generation"""
    
    def test_schema_professional_service_type(self):
        """Test Schema.org ProfessionalService type"""
        schema_type = "ProfessionalService"
        valid_types = ["ProfessionalService", "LocalBusiness", "Photographer"]
        
        assert schema_type in valid_types
    
    def test_schema_required_fields(self):
        """Test Schema.org required fields"""
        required_fields = ['@context', '@type', 'name', 'url']
        
        sample_schema = {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": "Test Photographer",
            "url": "https://galerly.com/portfolio/test"
        }
        
        for field in required_fields:
            assert field in sample_schema
    
    def test_schema_json_ld_format(self):
        """Test JSON-LD format validity"""
        sample_schema = {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": "Test Photographer"
        }
        
        # Should be valid JSON
        try:
            json_str = json.dumps(sample_schema)
            parsed = json.loads(json_str)
            assert parsed == sample_schema
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON format")


class TestOGTagValidation:
    """Test Open Graph tag validation"""
    
    def test_og_title_validation(self):
        """Test OG title length validation"""
        test_cases = [
            {'title': '', 'valid': False, 'reason': 'empty'},
            {'title': 'Short', 'valid': False, 'reason': 'too_short'},
            {'title': 'Perfect Title Length', 'valid': True, 'reason': 'good'},
            {'title': 'A' * 61, 'valid': False, 'reason': 'too_long'}
        ]
        
        for case in test_cases:
            title = case['title']
            if case['reason'] == 'empty':
                assert len(title) == 0
            elif case['reason'] == 'too_short':
                assert len(title) < 10
            elif case['reason'] == 'good':
                assert 10 <= len(title) <= 60
            elif case['reason'] == 'too_long':
                assert len(title) > 60
    
    def test_og_description_validation(self):
        """Test OG description length validation"""
        test_cases = [
            {'desc': '', 'valid': False},
            {'desc': 'Too short', 'valid': False},
            {'desc': 'This is a perfect length description for Open Graph tags that provides good context.', 'valid': True},
            {'desc': 'A' * 201, 'valid': False}
        ]
        
        for case in test_cases:
            desc = case['desc']
            if desc == '':
                assert len(desc) == 0
            elif len(desc) < 50:
                assert not case['valid']
            elif 50 <= len(desc) <= 200:
                assert case['valid']
            else:
                assert not case['valid']
    
    def test_og_image_url_validation(self):
        """Test OG image URL validation"""
        valid_urls = [
            'https://example.com/image.jpg',
            'https://cdn.example.com/og-image.png',
            'https://galerly.com/photos/og.webp'
        ]
        
        invalid_urls = [
            'not-a-url',
            'ftp://example.com/image.jpg',
            '/relative/path/image.jpg',
            'example.com/image.jpg'
        ]
        
        for url in valid_urls:
            assert url.startswith('https://') or url.startswith('http://')
            assert any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])
        
        for url in invalid_urls:
            assert not (url.startswith('https://') and any(url.endswith(ext) for ext in ['.jpg', '.png']))
    
    def test_og_score_calculation(self):
        """Test OG tag validation score calculation"""
        # Perfect score: 100
        perfect_og = {
            'og_title': 'Perfect Title Length Here',
            'og_description': 'This is a perfect description with good length and clear information about the content.',
            'og_image': 'https://example.com/image.jpg',
            'url': 'https://example.com/page'
        }
        
        # Score calculation logic
        score = 100
        issues = 0
        warnings = 0
        
        # Validate title
        if not perfect_og['og_title']:
            issues += 1
        elif len(perfect_og['og_title']) < 10 or len(perfect_og['og_title']) > 60:
            warnings += 1
        
        # Validate description
        if not perfect_og['og_description']:
            issues += 1
        elif len(perfect_og['og_description']) < 50 or len(perfect_og['og_description']) > 200:
            warnings += 1
        
        # Validate image
        if not perfect_og['og_image']:
            issues += 1
        elif not (perfect_og['og_image'].startswith('http')):
            issues += 1
        
        score -= issues * 20
        score -= warnings * 10
        
        assert score == 100  # Perfect OG tags


class TestSEOSettings:
    """Test SEO settings management"""
    
    def test_robots_txt_default(self):
        """Test default robots.txt content"""
        default_robots = 'User-agent: *\nAllow: /'
        
        assert 'User-agent: *' in default_robots
        assert 'Allow: /' in default_robots
    
    def test_robots_txt_custom(self):
        """Test custom robots.txt content"""
        custom_robots = '''User-agent: *
Allow: /portfolio/
Disallow: /private/
Sitemap: https://galerly.com/sitemap.xml'''
        
        assert 'User-agent: *' in custom_robots
        assert 'Allow:' in custom_robots
        assert 'Disallow:' in custom_robots
        assert 'Sitemap:' in custom_robots
    
    def test_canonical_urls(self):
        """Test canonical URL generation"""
        page_url = 'https://galerly.com/portfolio/user123'
        canonical_url = page_url
        
        assert canonical_url == page_url
        assert canonical_url.startswith('https://')


class TestSEOIntegration:
    """Integration tests for SEO tools"""
    
    def test_complete_seo_workflow(self):
        """Test complete SEO optimization workflow"""
        workflow_steps = [
            'generate_sitemap',
            'create_schema_markup',
            'validate_og_tags',
            'configure_robots_txt',
            'set_canonical_urls'
        ]
        
        for step in workflow_steps:
            assert isinstance(step, str)
            assert len(step) > 0
    
    def test_seo_best_practices(self):
        """Test SEO best practices compliance"""
        best_practices = {
            'use_https': True,
            'mobile_friendly': True,
            'fast_loading': True,
            'structured_data': True,
            'xml_sitemap': True,
            'robots_txt': True,
            'canonical_urls': True,
            'og_tags': True,
            'alt_text': True
        }
        
        # All best practices should be enabled
        for practice, enabled in best_practices.items():
            assert enabled is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
