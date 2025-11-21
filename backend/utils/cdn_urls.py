"""
Image URL Generator - CloudFront CDN with On-Demand Transformation

Strategy: CloudFront + Lambda-based Image Transformation
- Store only original files (RAW, HEIC, JPEG, etc.)
- Transform on-demand via Lambda function
- Cache transformed images in S3
- CloudFront serves cached versions globally
- Cost efficient: Only store originals + small cached thumbnails
- Fast: Cached at edge locations
- Scalable: Handles any format (RAW, HEIC, TIFF, etc.)

Similar to Instagram/Google Photos architecture
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
        s3_key: S3 object key (e.g. "gallery123/photo456.dng")
        size: Target size tuple (width, height) or None for original
        format: Output format ('auto', 'jpeg', 'webp', 'png')
    
    Returns:
        CloudFront URL with transformation parameters
    
    Example:
        get_cdn_url('gallery123/photo456.dng', size=(800, 600), format='jpeg')
        -> https://cdn.galerly.com/gallery123/photo456.dng?format=jpeg&width=800&height=600&fit=inside
    
    Note: image-transform Lambda handles the actual transformation
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
    Generate all URL variants for a photo with on-demand transformation
    
    Returns different sizes for responsive display
    Actual transformation happens via image-transform Lambda (invoked by CloudFront)
    
    Args:
        s3_key: S3 object key (original file - RAW, HEIC, JPEG, etc.)
    
    Returns:
        dict with url, medium_url, thumbnail_url, small_thumb_url
    """
    # Original (no transformation) - for download
    original_url = f"https://{CDN_DOMAIN}/{s3_key}"
    
    # Display URLs with transformation parameters
    # These will trigger the image-transform Lambda via CloudFront/API Gateway
    # The Lambda will:
    # 1. Check cache for transformed version
    # 2. If not cached, transform the original
    # 3. Store result in cache bucket
    # 4. Return transformed image
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
