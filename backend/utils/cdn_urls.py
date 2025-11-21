"""
Image URL Generator - CloudFront CDN with Pre-Generated Renditions

Strategy: Upload-Time Processing (Industry Best Practice)
- Store original files (RAW, HEIC, JPEG, etc.) for download
- Generate ALL renditions during upload (thumbnail, small, medium, large)
- Store renditions in optimized S3 structure
- CloudFront serves pre-generated renditions (instant, no processing delay)
- Cost efficient: Process once during upload, serve millions of times
- Fast: No transformation delay, instant page loads
- Scalable: Handles any format (RAW, HEIC, TIFF, etc.)

This follows industry standards:
- Instagram: Pre-generates multiple sizes on upload
- Airbnb: Pre-processes all images immediately
- Booking.com: Creates all variants during upload
- Flickr: Generates renditions in background job
"""
import os

# CloudFront CDN domain
CDN_DOMAIN = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')

# Rendition sizes matching processing Lambda
RENDITION_SIZES = {
    'thumbnail': (400, 400),      # Grid display
    'small': (800, 600),           # Preview
    'medium': (2000, 2000),        # Detail view
    'large': (4000, 4000)          # High-res zoom
}


def get_rendition_url(s3_key, size_name):
    """
    Generate URL for pre-generated rendition
    
    Args:
        s3_key: Original S3 key (e.g. "gallery_id/photo_id.ext")
        size_name: Rendition size ('thumbnail', 'small', 'medium', 'large')
    
    Returns:
        CloudFront URL to pre-generated rendition
    
    Example:
        get_rendition_url('gallery123/photo456.dng', 'thumbnail')
        -> https://cdn.galerly.com/renditions/gallery123/photo456_thumbnail.jpg
    """
    # Extract photo_id and gallery_id from S3 key
    # Format: gallery_id/photo_id.ext
    parts = s3_key.split('/')
    if len(parts) != 2:
        # Fallback to original if invalid format
        return f"https://{CDN_DOMAIN}/{s3_key}"
    
    gallery_id = parts[0]
    photo_filename = parts[1]
    photo_id = os.path.splitext(photo_filename)[0]
    
    # Generate rendition URL
    # Format: renditions/gallery_id/photo_id_size.jpg
    rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
    
    return f"https://{CDN_DOMAIN}/{rendition_key}"


def get_photo_urls(s3_key):
    """
    Generate all URL variants for a photo using pre-generated renditions
    
    Returns URLs to pre-generated renditions for instant page loads
    Processing Lambda creates: renditions/{gallery_id}/{photo_id}_{size}.jpg
    
    Args:
        s3_key: S3 object key (original file - gallery_id/photo_id.ext)
    
    Returns:
        dict with url, medium_url, thumbnail_url, small_thumb_url, large_url
    """
    # Original URL (no transformation) - for download
    original_url = f"https://{CDN_DOMAIN}/{s3_key}"
    
    # Extract gallery_id and photo_id from s3_key
    # Format: gallery_id/photo_id.ext
    parts = s3_key.split('/')
    if len(parts) != 2:
        # Fallback to original if invalid format
        return {
            'url': original_url,
            'large_url': original_url,
            'medium_url': original_url,
            'thumbnail_url': original_url,
            'small_thumb_url': original_url,
        }
    
    gallery_id = parts[0]
    photo_filename = parts[1]
    photo_id = os.path.splitext(photo_filename)[0]
    
    # Pre-generated rendition URLs matching Lambda output
    # Lambda creates: renditions/{gallery_id}/{photo_id}_{size}.jpg
    return {
        'url': original_url,  # Original for download only
        'large_url': f"https://{CDN_DOMAIN}/renditions/{gallery_id}/{photo_id}_large.jpg",
        'medium_url': f"https://{CDN_DOMAIN}/renditions/{gallery_id}/{photo_id}_medium.jpg",
        'thumbnail_url': f"https://{CDN_DOMAIN}/renditions/{gallery_id}/{photo_id}_small.jpg",
        'small_thumb_url': f"https://{CDN_DOMAIN}/renditions/{gallery_id}/{photo_id}_thumbnail.jpg",
    }


def get_responsive_srcset(s3_key):
    """
    Generate responsive image srcset for modern browsers
    
    Returns URLs to multiple renditions for responsive loading
    """
    small_url = get_rendition_url(s3_key, 'small')
    medium_url = get_rendition_url(s3_key, 'medium')
    large_url = get_rendition_url(s3_key, 'large')
    
    return f"{small_url} 800w, {medium_url} 2000w, {large_url} 4000w"
