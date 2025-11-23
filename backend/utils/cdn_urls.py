"""
CDN URL Generator with LocalStack S3 support
Automatically detects LocalStack and generates appropriate URLs
"""
import os

def get_required_env(key):
    """Get required environment variable or raise error"""
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

# Environment detection - REQUIRED
IS_LOCAL = get_required_env('ENVIRONMENT') == 'local'
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
S3_PHOTOS_BUCKET = get_required_env('S3_PHOTOS_BUCKET')

# CDN domain configuration - REQUIRED
# Production: CloudFront CDN
# LocalStack: S3 direct access (no CloudFront)
if IS_LOCAL and AWS_ENDPOINT_URL:
    # LocalStack S3 bucket URL format
    # Format: http://localhost:4566/bucket-name/key
    CDN_DOMAIN = get_required_env('CDN_DOMAIN')
    IS_LOCALSTACK_S3 = True
else:
    # Production CloudFront
    CDN_DOMAIN = get_required_env('CDN_DOMAIN')
    IS_LOCALSTACK_S3 = False

# Rendition sizes matching processing Lambda
RENDITION_SIZES = {
    'thumbnail': (400, 400),      # Grid display
    'small': (800, 600),           # Preview
    'medium': (2000, 2000),        # Detail view
    'large': (4000, 4000)          # High-res zoom
}

def get_zip_url(gallery_id):
    """
    Generate ZIP download URL for bulk downloads
    
    Args:
        gallery_id: Gallery ID
    
    Returns:
        URL to gallery ZIP file
    """
    from utils.config import S3_RENDITIONS_BUCKET
    
    zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
    
    if IS_LOCALSTACK_S3 and AWS_ENDPOINT_URL:
        # LocalStack: ZIP files are stored in renditions bucket
        # Replace 'localstack' hostname with 'localhost' for browser access
        endpoint = AWS_ENDPOINT_URL.replace('http://localstack:', 'http://localhost:')
        return f"{endpoint}/{S3_RENDITIONS_BUCKET}/{zip_s3_key}"
    else:
        # Production: CloudFront
        return f"https://{CDN_DOMAIN}/{zip_s3_key}"

def get_rendition_url(s3_key, size_name):
    """
    Generate rendition URL for CloudFront or LocalStack S3
    
    Args:
        s3_key: Original S3 key (gallery_id/photo_id.ext)
        size_name: Rendition size ('thumbnail', 'small', 'medium', 'large')
    
    Returns:
        URL to pre-generated rendition
    
    Example Production:
        s3_key='gallery123/photo456.jpg', size_name='thumbnail'
        -> https://cdn.galerly.com/renditions/gallery123/photo456_thumbnail.jpg
    
    Example LocalStack:
        s3_key='gallery123/photo456.jpg', size_name='thumbnail'
        -> http://localhost:4566/galerly-renditions-local/renditions/gallery123/photo456_thumbnail.jpg
    """
    # Extract photo info from S3 key
    parts = s3_key.split('/')
    if len(parts) != 2:
        # Invalid key format, return original
        return get_original_url(s3_key)
    
    gallery_id = parts[0]
    photo_filename = parts[1]
    photo_id = photo_filename.rsplit('.', 1)[0]  # Remove extension
    
    # Generate rendition key
    # Format: renditions/gallery_id/photo_id_size.jpg
    rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
    
    # Generate URL based on environment
    if IS_LOCALSTACK_S3:
        # LocalStack S3 URL format
        # http://localhost:4566/bucket-name/key
        from utils.config import S3_RENDITIONS_BUCKET
        # Replace 'localstack' hostname with 'localhost' for browser access
        endpoint = AWS_ENDPOINT_URL.replace('http://localstack:', 'http://localhost:')
        return f"{endpoint}/{S3_RENDITIONS_BUCKET}/{rendition_key}"
    else:
        # Production CloudFront URL
        return f"https://{CDN_DOMAIN}/{rendition_key}"

def get_original_url(s3_key):
    """
    Get URL for original file (download)
    
    Args:
        s3_key: S3 key (gallery_id/photo_id.ext)
    
    Returns:
        URL to original file
    """
    if IS_LOCALSTACK_S3:
        # LocalStack: Direct S3 URL to photos bucket
        bucket = get_required_env('S3_PHOTOS_BUCKET')
        return f"http://localhost:4566/{bucket}/{s3_key}"
    else:
        # Production: CloudFront URL to photos bucket
        return f"https://{CDN_DOMAIN}/{s3_key}"

def get_photo_urls(s3_key):
    """
    Generate all URL variants for a photo
    Returns pre-generated rendition URLs for responsive display
    
    Args:
        s3_key: S3 key (gallery_id/photo_id.ext)
    
    Returns:
        dict with url (original), thumbnail_url, small_url, medium_url, large_url
    """
    return {
        'url': get_original_url(s3_key),           # Original for download
        'thumbnail_url': get_rendition_url(s3_key, 'thumbnail'),  # 400x400
        'small_url': get_rendition_url(s3_key, 'small'),          # 800x600
        'medium_url': get_rendition_url(s3_key, 'medium'),        # 2000x2000
        'large_url': get_rendition_url(s3_key, 'large')           # 4000x4000
    }

# Debug logging for local development
if IS_LOCAL:
    print(f"🖼️  CDN Configuration:")
    print(f"   Mode: {'LocalStack S3' if IS_LOCALSTACK_S3 else 'CloudFront'}")
    print(f"   CDN Domain: {CDN_DOMAIN}")
    if IS_LOCALSTACK_S3:
        print(f"   S3 Endpoint: {AWS_ENDPOINT_URL}")
