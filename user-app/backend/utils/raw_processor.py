"""
RAW Photo Processing Module
Handles RAW file formats (CR2, NEF, ARW, DNG, RAF, etc.)
- Preview/thumbnail generation from RAW
- Metadata extraction (EXIF, camera info)
- File validation
- RAW-specific handling for Pro/Ultimate plans
"""
import io
import os
from PIL import Image
from datetime import datetime

try:
    import rawpy
    import numpy as np
    RAW_SUPPORT_AVAILABLE = True
except ImportError:
    rawpy = None
    RAW_SUPPORT_AVAILABLE = False
    print("rawpy not installed, RAW processing disabled")


# Supported RAW formats
RAW_EXTENSIONS = {
    '.cr2': 'Canon RAW',
    '.cr3': 'Canon RAW 3',
    '.nef': 'Nikon RAW',
    '.arw': 'Sony RAW',
    '.dng': 'Adobe DNG',
    '.orf': 'Olympus RAW',
    '.rw2': 'Panasonic RAW',
    '.raf': 'Fujifilm RAW',
    '.raw': 'Generic RAW',
    '.pef': 'Pentax RAW',
    '.srw': 'Samsung RAW',
    '.x3f': 'Sigma RAW',
    '.mrw': 'Minolta RAW',
    '.kdc': 'Kodak RAW',
    '.dcr': 'Kodak DCR',
    '.erf': 'Epson RAW'
}


def is_raw_file(filename):
    """
    Check if file is a RAW format
    
    Args:
        filename: Filename with extension
        
    Returns:
        bool: True if RAW format
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in RAW_EXTENSIONS


def get_raw_format_name(filename):
    """
    Get human-readable RAW format name
    
    Args:
        filename: Filename with extension
        
    Returns:
        str: Format name (e.g., 'Canon RAW') or None
    """
    ext = os.path.splitext(filename)[1].lower()
    return RAW_EXTENSIONS.get(ext)


def generate_raw_preview(raw_data, size='medium', quality=85):
    """
    Generate JPEG preview from RAW file data
    
    Args:
        raw_data: Bytes of RAW file
        size: Preview size - 'thumbnail' (400px), 'medium' (2000px), 'large' (4000px)
        quality: JPEG quality 1-100
        
    Returns:
        dict: {
            'success': bool,
            'preview_data': bytes (JPEG),
            'dimensions': tuple (width, height),
            'error': str (if failed)
        }
    """
    if not RAW_SUPPORT_AVAILABLE:
        return {
            'success': False,
            'error': 'RAW processing not available - rawpy not installed'
        }
    
    try:
        print(f"🔄 Processing RAW file to {size} preview...")
        
        # Step 1: Open RAW file with rawpy
        with rawpy.imread(io.BytesIO(raw_data)) as raw:
            # Step 2: Process RAW to RGB array
            # postprocess() applies demosaicing, white balance, color correction
            rgb_array = raw.postprocess(
                use_camera_wb=True,  # Use camera white balance
                half_size=False,      # Full resolution for quality
                no_auto_bright=False, # Allow auto brightness
                output_color=rawpy.ColorSpace.sRGB,  # sRGB color space
                output_bps=8          # 8-bit output
            )
        
        # Step 3: Convert to PIL Image
        image = Image.fromarray(rgb_array)
        
        # Step 4: Resize based on requested size
        size_map = {
            'thumbnail': (400, 400),
            'small': (800, 600),
            'medium': (2000, 2000),
            'large': (4000, 4000),
            'original': None  # No resize
        }
        
        target_size = size_map.get(size, (2000, 2000))
        original_dimensions = image.size
        
        if target_size:
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Step 5: Convert to JPEG
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        preview_data = output.getvalue()
        
        print(f"Generated {size} preview: {image.size[0]}x{image.size[1]} ({len(preview_data) / 1024:.1f} KB)")
        
        return {
            'success': True,
            'preview_data': preview_data,
            'dimensions': image.size,
            'original_dimensions': original_dimensions,
            'file_size': len(preview_data)
        }
        
    except Exception as e:
        print(f"Error generating RAW preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def extract_raw_metadata(raw_data):
    """
    Extract metadata from RAW file
    
    Args:
        raw_data: Bytes of RAW file
        
    Returns:
        dict: {
            'success': bool,
            'metadata': dict with camera info, EXIF, etc.
            'error': str (if failed)
        }
    """
    if not RAW_SUPPORT_AVAILABLE:
        return {
            'success': False,
            'error': 'RAW processing not available'
        }
    
    try:
        print(f"📋 Extracting RAW metadata...")
        
        with rawpy.imread(io.BytesIO(raw_data)) as raw:
            # Extract camera and image metadata
            metadata = {
                'camera_make': getattr(raw, 'camera_make', 'Unknown'),
                'camera_model': getattr(raw, 'camera_model', 'Unknown'),
                'iso_speed': getattr(raw, 'camera_iso_speed', None),
                'shutter_speed': getattr(raw, 'camera_shutter', None),
                'aperture': getattr(raw, 'camera_aperture', None),
                'focal_length': getattr(raw, 'camera_focal_length', None),
                'timestamp': getattr(raw, 'camera_timestamp', None),
                'white_balance': getattr(raw, 'camera_whitebalance', None),
                'dimensions': (raw.sizes.raw_width, raw.sizes.raw_height),
                'num_colors': raw.num_colors,
                'raw_type': raw.raw_type,
            }
            
            # Try to get additional EXIF data if available
            try:
                if hasattr(raw, 'color_desc'):
                    metadata['color_description'] = raw.color_desc.decode('utf-8') if raw.color_desc else None
            except:
                pass
        
        # Clean up None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        print(f"Extracted metadata: {metadata.get('camera_make')} {metadata.get('camera_model')}")
        
        return {
            'success': True,
            'metadata': metadata
        }
        
    except Exception as e:
        print(f"Error extracting RAW metadata: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'metadata': {}
        }


def validate_raw_file(raw_data, filename):
    """
    Validate RAW file integrity
    
    Args:
        raw_data: Bytes of RAW file
        filename: Original filename
        
    Returns:
        dict: {
            'valid': bool,
            'format': str (Canon RAW, etc.),
            'file_size_mb': float,
            'warnings': list of str,
            'error': str (if invalid)
        }
    """
    if not RAW_SUPPORT_AVAILABLE:
        return {
            'valid': False,
            'error': 'RAW processing not available'
        }
    
    warnings = []
    file_size_mb = len(raw_data) / (1024 * 1024)
    
    # Check file size (RAW files are typically 20-80MB)
    if file_size_mb < 1:
        warnings.append('File size unusually small for RAW format')
    elif file_size_mb > 200:
        warnings.append('File size very large - may cause slow processing')
    
    try:
        # Try to open and read basic info
        with rawpy.imread(io.BytesIO(raw_data)) as raw:
            camera_make = getattr(raw, 'camera_make', 'Unknown')
            camera_model = getattr(raw, 'camera_model', 'Unknown')
            dimensions = (raw.sizes.raw_width, raw.sizes.raw_height)
        
        # Check dimensions
        if dimensions[0] < 1000 or dimensions[1] < 1000:
            warnings.append('Resolution unusually low for RAW file')
        
        format_name = get_raw_format_name(filename)
        
        print(f"Valid RAW file: {format_name} ({file_size_mb:.1f} MB)")
        
        return {
            'valid': True,
            'format': format_name,
            'camera': f"{camera_make} {camera_model}",
            'dimensions': dimensions,
            'file_size_mb': round(file_size_mb, 2),
            'warnings': warnings
        }
        
    except Exception as e:
        print(f"Invalid RAW file: {str(e)}")
        return {
            'valid': False,
            'error': f'Invalid RAW file: {str(e)}',
            'file_size_mb': round(file_size_mb, 2)
        }


def process_raw_upload(raw_data, filename, s3_client, bucket, s3_key_prefix):
    """
    Complete RAW file processing workflow:
    1. Validate RAW file
    2. Extract metadata
    3. Generate preview JPEG
    4. Upload original RAW + preview to S3
    
    Args:
        raw_data: Bytes of RAW file
        filename: Original filename
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        s3_key_prefix: S3 key prefix (e.g., 'gallery_id/photo_id')
        
    Returns:
        dict: {
            'success': bool,
            'raw_key': str (S3 key of RAW file),
            'preview_key': str (S3 key of preview JPEG),
            'metadata': dict,
            'error': str (if failed)
        }
    """
    try:
        print(f"🔄 Processing RAW upload: {filename}")
        
        # Step 1: Validate
        validation = validate_raw_file(raw_data, filename)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation.get('error', 'Invalid RAW file')
            }
        
        # Step 2: Extract metadata
        metadata_result = extract_raw_metadata(raw_data)
        metadata = metadata_result.get('metadata', {})
        
        # Step 3: Generate preview
        preview_result = generate_raw_preview(raw_data, size='medium', quality=85)
        if not preview_result['success']:
            return {
                'success': False,
                'error': f"Failed to generate preview: {preview_result.get('error')}"
            }
        
        # Step 4: Upload original RAW
        raw_ext = os.path.splitext(filename)[1]
        raw_key = f"{s3_key_prefix}{raw_ext}"
        
        from utils.mime_types import get_mime_type
        mime_type = get_mime_type(filename)
        
        s3_client.put_object(
            Bucket=bucket,
            Key=raw_key,
            Body=raw_data,
            ContentType=mime_type,
            Metadata={
                'original-filename': filename,
                'file-type': 'raw',
                'format': validation.get('format', 'RAW'),
                'camera': validation.get('camera', 'Unknown')
            }
        )
        
        # Step 5: Upload preview JPEG
        preview_key = f"{s3_key_prefix}_preview.jpg"
        s3_client.put_object(
            Bucket=bucket,
            Key=preview_key,
            Body=preview_result['preview_data'],
            ContentType='image/jpeg',
            Metadata={
                'source': 'raw-preview',
                'original-filename': filename
            }
        )
        
        print(f"RAW upload complete: {raw_key}")
        
        return {
            'success': True,
            'raw_key': raw_key,
            'preview_key': preview_key,
            'metadata': {
                **metadata,
                'file_size_mb': validation['file_size_mb'],
                'format': validation['format'],
                'dimensions': validation['dimensions'],
                'warnings': validation.get('warnings', [])
            }
        }
        
    except Exception as e:
        print(f"Error processing RAW upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_raw_download_options(raw_key, s3_client, bucket):
    """
    Get download options for RAW file:
    - Original RAW file
    - High-quality JPEG conversion
    
    Args:
        raw_key: S3 key of RAW file
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        
    Returns:
        dict: {
            'raw_url': presigned URL for RAW,
            'jpeg_url': presigned URL for JPEG,
            'raw_size_mb': float,
            'estimated_jpeg_size_mb': float
        }
    """
    try:
        # Generate presigned URL for RAW
        raw_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': raw_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Get RAW file size
        response = s3_client.head_object(Bucket=bucket, Key=raw_key)
        raw_size_mb = response['ContentLength'] / (1024 * 1024)
        
        # Check if JPEG preview exists
        preview_key = raw_key.rsplit('.', 1)[0] + '_preview.jpg'
        jpeg_url = None
        jpeg_size_mb = None
        
        try:
            jpeg_response = s3_client.head_object(Bucket=bucket, Key=preview_key)
            jpeg_size_mb = jpeg_response['ContentLength'] / (1024 * 1024)
            jpeg_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': preview_key},
                ExpiresIn=3600
            )
        except:
            pass
        
        return {
            'raw_url': raw_url,
            'jpeg_url': jpeg_url,
            'raw_size_mb': round(raw_size_mb, 2),
            'jpeg_size_mb': round(jpeg_size_mb, 2) if jpeg_size_mb else None
        }
        
    except Exception as e:
        print(f"Error getting download options: {str(e)}")
        return {
            'error': str(e)
        }
