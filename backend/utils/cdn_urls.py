"""
Image URL Generator - CloudFront CDN (Production-Ready)

Strategy: CloudFront CDN for fast global delivery
- CloudFront caches images at edge locations worldwide
- Lambda@Edge (pass-through) - no additional processing
- Cost: Only CloudFront bandwidth (~$0.085/GB)
- Fast: 50-200ms from edge locations
- Reliable: CloudFront 99.9% uptime SLA

For resizing: Images served at original size (simple, fast, reliable)
"""
import os

# CloudFront CDN domain
CDN_DOMAIN = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')

# Standard image sizes (for reference)
IMAGE_SIZES = {
    'thumbnail': (800, 600),     # Gallery grid view
    'medium': (2000, 2000),      # Lightbox/detail view
    'small': (400, 400),         # Small thumbnails
    'tiny': (150, 150),          # Ultra-small
}


def get_cdn_url(s3_key, size=None):
    """
    Generate CloudFront CDN URL for image
    
    Args:
        s3_key: S3 object key (e.g. "gallery123/photo456.jpg")
        size: Ignored (no resizing in this version)
    
    Returns:
        CloudFront URL
    
    Example:
        get_cdn_url('gallery123/photo456.jpg')
        -> https://cdn.galerly.com/gallery123/photo456.jpg
    """
    return f"https://{CDN_DOMAIN}/{s3_key}"


def get_photo_urls(s3_key):
    """
    Generate all URL variants for a photo
    
    All URLs point to original (served via CloudFront for fast delivery)
    
    Args:
        s3_key: S3 object key
    
    Returns:
        dict with url, medium_url, thumbnail_url, small_thumb_url
    """
    url = get_cdn_url(s3_key)
    
    return {
        'url': url,                 # Original via CloudFront
        'medium_url': url,          # Same (CloudFront cached)
        'thumbnail_url': url,       # Same (CloudFront cached)
        'small_thumb_url': url,     # Same (CloudFront cached)
}


def get_responsive_srcset(s3_key):
    """
    Generate responsive image srcset
    
    Returns single CloudFront URL
    """
    url = get_cdn_url(s3_key)
    return f"{url} 1x"
