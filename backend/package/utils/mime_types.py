"""
MIME Type Helper
Maps file extensions to proper MIME types for S3 uploads
"""

def get_mime_type(filename):
    """
    Get MIME type from filename extension
    
    Args:
        filename: The filename with extension
        
    Returns:
        str: MIME type (e.g., 'image/jpeg', 'image/png')
    """
    import os
    
    extension = os.path.splitext(filename)[1].lower()
    
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.heic': 'image/heic',
        '.heif': 'image/heif',
        '.dng': 'image/x-adobe-dng',
        '.cr2': 'image/x-canon-cr2',
        '.nef': 'image/x-nikon-nef',
        '.arw': 'image/x-sony-arw',
        '.orf': 'image/x-olympus-orf',
        '.rw2': 'image/x-panasonic-rw2',
        '.svg': 'image/svg+xml',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
    }
    
    return mime_types.get(extension, 'application/octet-stream')

