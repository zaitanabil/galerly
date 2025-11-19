"""
Test Image Transformation Flow
Tests backend URL generation and CDN transformation parameters
"""
import pytest
import sys
sys.path.insert(0, '.')

from utils.cdn_urls import get_cdn_url, get_photo_urls


class TestImageTransformation:
    """Test URL-based image transformation"""
    
    def test_cdn_url_with_transformation_params(self):
        """Test that CDN URLs include transformation parameters"""
        url = get_cdn_url("gallery/photo.dng", size=(800, 600), format='jpeg')
        
        assert "cdn.galerly.com" in url
        assert "format=jpeg" in url
        assert "width=800" in url
        assert "height=600" in url
        assert "fit=inside" in url
    
    def test_cdn_url_without_transformation(self):
        """Test original URL without transformation"""
        url = get_cdn_url("gallery/photo.jpg")
        
        assert url == "https://cdn.galerly.com/gallery/photo.jpg"
        assert "?" not in url
    
    def test_photo_urls_raw_format(self):
        """Test URL generation for RAW DNG files"""
        urls = get_photo_urls("gallery/photo.dng")
        
        # Original URL (for download)
        assert urls['url'] == "https://cdn.galerly.com/gallery/photo.dng"
        assert "?" not in urls['url']
        
        # Thumbnail URL (for display) - transformed
        assert "format=jpeg" in urls['thumbnail_url']
        assert "width=800" in urls['thumbnail_url']
        assert "height=600" in urls['thumbnail_url']
        
        # Medium URL (for display) - transformed
        assert "format=jpeg" in urls['medium_url']
        assert "width=2000" in urls['medium_url']
    
    def test_photo_urls_heic_format(self):
        """Test URL generation for HEIC files"""
        urls = get_photo_urls("gallery/photo.heic")
        
        # Original preserved
        assert ".heic" in urls['url']
        
        # Display versions transformed to JPEG
        assert "format=jpeg" in urls['thumbnail_url']
        assert "format=jpeg" in urls['medium_url']
    
    def test_photo_urls_jpeg_format(self):
        """Test URL generation for standard JPEG files"""
        urls = get_photo_urls("gallery/photo.jpg")
        
        # Original
        assert urls['url'] == "https://cdn.galerly.com/gallery/photo.jpg"
        
        # Display versions still get transformation params (for resizing)
        assert "format=jpeg" in urls['thumbnail_url']
        assert "width=800" in urls['thumbnail_url']
    
    def test_all_formats_accepted(self):
        """Test that all image formats generate valid URLs"""
        formats = [
            "photo.jpg",
            "photo.png", 
            "photo.heic",
            "photo.dng",
            "photo.cr2",
            "photo.nef",
            "photo.tiff"
        ]
        
        for filename in formats:
            s3_key = f"gallery/{filename}"
            urls = get_photo_urls(s3_key)
            
            # All should have valid URLs
            assert urls['url'].startswith("https://cdn.galerly.com/")
            assert urls['thumbnail_url'].startswith("https://cdn.galerly.com/")
            assert urls['medium_url'].startswith("https://cdn.galerly.com/")
            
            # Original = no transformation
            assert "?" not in urls['url']
            
            # Display = with transformation
            assert "format=jpeg" in urls['thumbnail_url']
            assert "format=jpeg" in urls['medium_url']


class TestTransformationParameters:
    """Test transformation parameter generation"""
    
    def test_different_sizes(self):
        """Test different size parameters"""
        url_small = get_cdn_url("test.dng", size=(400, 400), format='jpeg')
        url_medium = get_cdn_url("test.dng", size=(800, 600), format='jpeg')
        url_large = get_cdn_url("test.dng", size=(2000, 2000), format='jpeg')
        
        assert "width=400" in url_small
        assert "width=800" in url_medium
        assert "width=2000" in url_large
    
    def test_format_conversion(self):
        """Test format parameter"""
        url_jpeg = get_cdn_url("test.dng", format='jpeg')
        url_webp = get_cdn_url("test.dng", format='webp')
        url_png = get_cdn_url("test.dng", format='png')
        
        assert "format=jpeg" in url_jpeg
        assert "format=webp" in url_webp
        assert "format=png" in url_png
    
    def test_fit_parameter(self):
        """Test fit parameter for aspect ratio"""
        url = get_cdn_url("test.dng", size=(800, 600), format='jpeg')
        
        assert "fit=inside" in url


class TestDownloadVsDisplay:
    """Test that download URLs differ from display URLs"""
    
    def test_download_url_is_original(self):
        """Download URL should be original file"""
        urls = get_photo_urls("gallery/photo.dng")
        
        # Download URL = original DNG
        assert urls['url'] == "https://cdn.galerly.com/gallery/photo.dng"
        assert "format=" not in urls['url']
    
    def test_display_url_is_transformed(self):
        """Display URL should have transformation params"""
        urls = get_photo_urls("gallery/photo.dng")
        
        # Display URLs = transformed JPEG
        assert "format=jpeg" in urls['thumbnail_url']
        assert "format=jpeg" in urls['medium_url']
        assert "format=jpeg" in urls['small_thumb_url']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

