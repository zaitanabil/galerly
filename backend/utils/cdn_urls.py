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


def get_cdn_url(s3_key, size=None, format='auto'):
    """
    Generate CloudFront CDN URL for image with transformation parameters
    
    Args:
        s3_key: S3 object key (e.g. "gallery123/photo456.jpg")
        size: Target size tuple (width, height) or None for original
        format: Output format ('auto', 'jpeg', 'webp', 'png')
    
    Returns:
        CloudFront URL with transformation parameters
    
    Example:
        get_cdn_url('gallery123/photo456.dng', size=(800, 600), format='jpeg')
        -> https://cdn.galerly.com/gallery123/photo456.dng?format=jpeg&width=800&height=600
    
    Note: CloudFront + Lambda@Edge will handle the transformation
    """
    base_url = f"https://{CDN_DOMAIN}/{s3_key}"
    
    # Add transformation parameters
    params = []
    if format and format != 'auto':
        params.append(f"format={format}")
    if size:
        width, height = size
        params.append(f"width={width}")
        params.append(f"height={height}")
        params.append("fit=inside")  # Maintain aspect ratio
    
    if params:
        return f"{base_url}?{'&'.join(params)}"
    
    return base_url


def get_photo_urls(s3_key):
    """
    Generate all URL variants for a photo with CloudFront transformation
    
    Returns different sizes for responsive display, all transformed to JPEG
    Original URL has no transformation (for download)
    
    Args:
        s3_key: S3 object key
    
    Returns:
        dict with url, medium_url, thumbnail_url, small_thumb_url
    """
    # Original (no transformation) - for download
    original_url = f"https://{CDN_DOMAIN}/{s3_key}"
    
    # Transformed versions (JPEG) - for display
    return {
        'url': original_url,  # Original for download
        'medium_url': get_cdn_url(s3_key, size=(2000, 2000), format='jpeg'),  # Display (large)
        'thumbnail_url': get_cdn_url(s3_key, size=(800, 600), format='jpeg'),  # Gallery grid
        'small_thumb_url': get_cdn_url(s3_key, size=(400, 400), format='jpeg'),  # Small thumbnails
    }


def get_responsive_srcset(s3_key):
    """
    Generate responsive image srcset
    
    Returns single CloudFront URL
    """
    url = get_cdn_url(s3_key)
    return f"{url} 1x"
