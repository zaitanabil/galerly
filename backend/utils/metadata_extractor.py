"""
Enhanced Metadata Extraction - Steps 6-8
Extracts and preserves comprehensive metadata from uploaded images
"""
import os
from datetime import datetime
from decimal import Decimal
try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL not available - metadata extraction disabled")


def extract_image_metadata(image_data, filename):
    """
    Step 7: Extract comprehensive metadata from image
    
    Returns:
        dict: Metadata including:
            - Basic: filename, size, format
            - Camera: camera model, lens, settings
            - EXIF: ISO, aperture, shutter speed, focal length
            - GPS: location if available
            - Color: color profile, color space
            - Timestamps: capture time, modification time
    """
    metadata = {
        'filename': filename,
        'file_size': len(image_data),
        'size_mb': round(len(image_data) / (1024 * 1024), 2),
        'upload_timestamp': datetime.utcnow().isoformat() + 'Z',
        'format': None,
        'dimensions': None,
        'camera': {},
        'exif': {},
        'gps': {},
        'color': {},
        'timestamps': {}
    }
    
    if not PIL_AVAILABLE:
        return metadata
    
    try:
        from io import BytesIO
        try:
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            # Try explicit HEIC support if standard open fails
            try:
                import pillow_heif
                if pillow_heif.is_supported(image_data):
                    heif_file = pillow_heif.read_heif(BytesIO(image_data))
                    image = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                    )
                else:
                    raise e
            except ImportError:
                print("⚠️ pillow-heif not installed or import failed")
                raise e
            except Exception as heic_e:
                print(f"❌ explicit pillow_heif metadata extraction failed: {str(heic_e)}")
                raise e
        
        # Basic image info
        metadata['format'] = image.format
        metadata['dimensions'] = {
            'width': image.width,
            'height': image.height,
            'aspect_ratio': round(image.width / image.height, 2) if image.height > 0 else 0
        }
        metadata['mode'] = image.mode
        
        # Color profile
        if hasattr(image, 'info') and 'icc_profile' in image.info:
            metadata['color']['has_icc_profile'] = True
        
        # EXIF data
        exif_data = image._getexif() if hasattr(image, '_getexif') else None
        
        if exif_data:
            # Helper to clean EXIF values (handle Rationals, bytes, etc.)
            def clean_val(v):
                if v is None: return None
                # Handle IFDRational
                if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                    return float(v)
                # Handle bytes
                if isinstance(v, bytes):
                    try: return v.decode('utf-8').strip('\x00')
                    except: return str(v)
                return v

            # Extract camera info
            camera_make = clean_val(exif_data.get(271))  # Make
            camera_model = clean_val(exif_data.get(272))  # Model
            lens_model = clean_val(exif_data.get(42036))  # LensModel
            
            if camera_make or camera_model:
                metadata['camera'] = {
                    'make': camera_make,
                    'model': camera_model,
                    'lens': lens_model
                }
            
            # Extract shooting settings
            metadata['exif'] = {
                'iso': clean_val(exif_data.get(34855)),  # ISOSpeedRatings
                'aperture': clean_val(exif_data.get(33437)),  # FNumber
                'shutter_speed': clean_val(exif_data.get(33434)),  # ExposureTime
                'focal_length': clean_val(exif_data.get(37386)),  # FocalLength
                'exposure_mode': clean_val(exif_data.get(34850)),  # ExposureProgram
                'metering_mode': clean_val(exif_data.get(37383)),  # MeteringMode
                'flash': clean_val(exif_data.get(37385)),  # Flash
                'white_balance': clean_val(exif_data.get(41987))  # WhiteBalance
            }
            
            # Extract timestamps
            date_taken = exif_data.get(36867)  # DateTimeOriginal
            date_digitized = exif_data.get(36868)  # DateTimeDigitized
            
            if date_taken or date_digitized:
                metadata['timestamps'] = {
                    'date_taken': date_taken,
                    'date_digitized': date_digitized
                }
            
            # Extract GPS data
            gps_info = exif_data.get(34853)  # GPSInfo
            if gps_info:
                gps_data = {}
                for key in gps_info.keys():
                    decode = GPSTAGS.get(key, key)
                    gps_data[decode] = gps_info[key]
                
                # Convert to lat/lon if available
                if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                    lat = convert_to_degrees(gps_data['GPSLatitude'])
                    lon = convert_to_degrees(gps_data['GPSLongitude'])
                    
                    # Apply N/S and E/W
                    if gps_data.get('GPSLatitudeRef') == 'S':
                        lat = -lat
                    if gps_data.get('GPSLongitudeRef') == 'W':
                        lon = -lon
                    
                    metadata['gps'] = {
                        'latitude': lat,
                        'longitude': lon,
                        'altitude': gps_data.get('GPSAltitude')
                    }
        
        # Clean None values
        metadata = {k: v for k, v in metadata.items() if v}
        
    except Exception as e:
        print(f"⚠️  Metadata extraction error: {str(e)}")
    
    return metadata


def convert_to_degrees(value):
    """
    Convert GPS coordinates to degrees
    """
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def create_photo_record_with_metadata(photo_id, gallery_id, user_id, s3_key, metadata, additional_fields=None):
    """
    Step 8: Create database record with comprehensive metadata
    Links stored original to gallery and photographer
    """
    from utils.cdn_urls import get_photo_urls
    
    # Generate CDN URLs
    photo_urls = get_photo_urls(s3_key)
    
    # Build photo record
    photo = {
        'id': photo_id,
        'gallery_id': gallery_id,
        'user_id': user_id,
        'filename': metadata.get('filename', 'unknown'),
        's3_key': s3_key,
        
        # URLs
        'url': photo_urls['url'],
        'large_url': photo_urls.get('large_url'),
        'medium_url': photo_urls['medium_url'],
        'thumbnail_url': photo_urls['thumbnail_url'],
        'small_thumb_url': photo_urls.get('small_thumb_url'),
        
        # File metadata
        'file_size': metadata.get('file_size', 0),
        'size_mb': Decimal(str(metadata.get('size_mb', 0))),
        'format': metadata.get('format'),
        'dimensions': metadata.get('dimensions'),
        
        # Camera metadata
        'camera': metadata.get('camera', {}),
        'exif': metadata.get('exif', {}),
        'gps': metadata.get('gps', {}),
        'color': metadata.get('color', {}),
        'timestamps': metadata.get('timestamps', {}),
        
        # Processing status
        'status': 'processing',  # Will be updated to 'active' after renditions generated
        'processing_started_at': datetime.utcnow().isoformat() + 'Z',
        
        # Photo metadata (from user)
        'title': '',
        'description': '',
        'tags': [],
        
        # Engagement
        'views': 0,
        'downloads': 0,
        'comments': [],
        
        # Timestamps
        'created_at': metadata.get('upload_timestamp'),
        'updated_at': metadata.get('upload_timestamp')
    }
    
    # Add any additional fields
    if additional_fields:
        photo.update(additional_fields)
    
    return photo

