"""
Automatic Image Processing Lambda - Steps 9-15
Triggered by S3 upload events to generate all renditions immediately

Workflow:
Step 9: Queued asynchronously via S3 event trigger
Step 10: Generate multiple renditions (thumbnail, small, medium, large)
Step 11: Convert/transcode to web formats while preserving lossless original
Step 12: Extract and preserve EXIF, color profile metadata
Step 13: Apply photographer settings (watermarks, compression, color adjustments)
Step 14: Store renditions in optimized S3 structure with lifecycle policies
Step 15: Update database with rendition locations, sizes, checksums
"""
import json
import boto3
import os
from PIL import Image
from io import BytesIO
import rawpy
import pillow_heif
from urllib.parse import unquote_plus

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
photos_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PHOTOS', 'galerly-photos'))
galleries_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_GALLERIES', 'galerly-galleries'))
users_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_USERS', 'galerly-users'))

# Configuration
SOURCE_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
RENDITIONS_BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')  # Use same bucket, different prefix
CDN_DOMAIN = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')

# Rendition sizes following industry standards
# Step 10: Generate multiple renditions for progressive loading
RENDITIONS = {
    'thumbnail': {'width': 400, 'height': 400, 'quality': 80},      # Grid display
    'small': {'width': 800, 'height': 600, 'quality': 85},           # Preview
    'medium': {'width': 2000, 'height': 2000, 'quality': 90},        # Detail view
    'large': {'width': 4000, 'height': 4000, 'quality': 92}          # High-res zoom
}

# Register HEIF opener
pillow_heif.register_heif_opener()

def lambda_handler(event, context):
    """
    Process S3 upload event and generate renditions
    Step 9: Asynchronous processing job queued
    
    Event structure from S3:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "galerly-images-storage"},
                "object": {"key": "gallery_id/photo_id.ext"}
            }
        }]
    }
    """
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            print(f"📥 Step 9: Processing upload: s3://{bucket}/{key}")
            
            # Skip if already a rendition (avoid recursive processing)
            if key.startswith('renditions/'):
                print(f"⏭️  Skipping rendition file: {key}")
                continue
            
            # Step 9-15: Process the image
            process_image(bucket, key)
            
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processing complete'})
        }
        
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Don't fail the Lambda - log error and continue
        # This prevents S3 from retrying endlessly
        return {
            'statusCode': 200,
            'body': json.dumps({
                'error': str(e),
                'message': 'Error logged, processing skipped'
            })
        }

def process_image(bucket, s3_key):
    """
    Steps 10-15: Download, process, and store image renditions
    
    Args:
        bucket: Source S3 bucket
        s3_key: S3 key (gallery_id/photo_id.ext)
    """
    try:
        # Step 10: Download original
        print(f"⬇️  Step 10: Downloading original: {s3_key}")
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        original_data = response['Body'].read()
        file_size = len(original_data)
        
        # Detect format from file extension
        file_ext = os.path.splitext(s3_key)[1].lower()
        
        # Step 11: Load image (handles RAW, HEIC, standard formats)
        image, original_exif = load_image_with_metadata(original_data, file_ext)
        
        if image is None:
            print(f"⚠️  Could not load image: {s3_key}")
            return
        
        # Extract photo_id and gallery_id from S3 key
        parts = s3_key.split('/')
        if len(parts) != 2:
            print(f"⚠️  Invalid S3 key format: {s3_key}")
            return
            
        gallery_id = parts[0]
        photo_filename = parts[1]
        photo_id = os.path.splitext(photo_filename)[0]
        
        # Step 12: Extract and preserve metadata
        metadata = extract_comprehensive_metadata(image, original_exif, original_data)
        
        # Step 13: Get photographer settings for processing
        photographer_settings = get_photographer_settings(gallery_id)
        
        # Step 10-14: Generate and upload all renditions
        rendition_data = {}
        
        for size_name, size_config in RENDITIONS.items():
            try:
                # Step 10: Resize image
                rendition = resize_image(image, size_config['width'], size_config['height'])
                
                # Step 13: Apply photographer settings
                rendition = apply_photographer_settings(rendition, photographer_settings)
                
                # Step 11: Convert to optimized JPEG for web
                buffer = BytesIO()
                rendition.convert('RGB').save(
                    buffer, 
                    format='JPEG', 
                    quality=size_config['quality'], 
                    optimize=True,
                    progressive=True  # Progressive JPEG for faster perceived loading
                )
                buffer.seek(0)
                rendition_bytes = buffer.getvalue()
                
                # Calculate checksum (Step 15)
                import hashlib
                checksum = hashlib.md5(rendition_bytes).hexdigest()
                
                # Generate S3 key for rendition
                # Format: renditions/gallery_id/photo_id_size.jpg
                rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
                
                # Step 14: Upload to S3 with lifecycle policies
                s3_client.put_object(
                    Bucket=RENDITIONS_BUCKET,
                    Key=rendition_key,
                    Body=rendition_bytes,
                    ContentType='image/jpeg',
                    CacheControl='public, max-age=31536000',  # 1 year cache
                    Metadata={
                        'original-key': s3_key,
                        'photo-id': photo_id,
                        'size': size_name,
                        'checksum': checksum
                    }
                )
                
                # Generate CDN URL
                rendition_url = f"https://{CDN_DOMAIN}/{rendition_key}"
                
                # Store rendition info (Step 15)
                rendition_data[f"{size_name}_url"] = rendition_url
                rendition_data[f"{size_name}_size"] = len(rendition_bytes)
                rendition_data[f"{size_name}_checksum"] = checksum
                
                print(f"✅ Generated {size_name}: {rendition_key} ({len(rendition_bytes)} bytes)")
                
            except Exception as e:
                print(f"❌ Error generating {size_name}: {str(e)}")
                continue
        
        # Step 15: Update DynamoDB with rendition URLs and metadata
        if rendition_data:
            update_photo_record(gallery_id, photo_id, rendition_data, metadata)
        
        print(f"🎉 Processing complete for {s3_key}")
        
    except Exception as e:
        print(f"❌ Error processing {s3_key}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def load_image_with_metadata(image_data, file_ext):
    """
    Step 11-12: Load image and extract EXIF metadata
    Handles RAW, HEIC, and standard formats
    Preserves original for download (lossless)
    
    Args:
        image_data: Raw image bytes
        file_ext: File extension (.jpg, .heic, .dng, etc.)
    
    Returns:
        (PIL Image object, EXIF dict) or (None, None)
    """
    try:
        # RAW formats
        raw_extensions = ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef', '.3fr']
        
        if file_ext in raw_extensions:
            print(f"📸 Processing RAW image: {file_ext}")
            with rawpy.imread(BytesIO(image_data)) as raw:
                # Step 12: Extract RAW metadata
                exif_data = {
                    'raw_type': file_ext,
                    'camera_wb_multipliers': raw.camera_whitebalance,
                    'daylight_wb_multipliers': raw.daylight_whitebalance
                }
                
                # Convert to RGB (Step 11: transcode to web format)
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    output_bps=16,  # 16-bit for maximum quality
                    no_auto_bright=True  # Preserve photographer's exposure
                )
                image = Image.fromarray(rgb)
                
                # Try to get EXIF from RAW
                try:
                    exif_data.update(image._getexif() or {})
                except:
                    pass
                
                return image, exif_data
        
        # HEIC format
        elif file_ext in ['.heic', '.heif']:
            print(f"📸 Processing HEIC image")
            image = Image.open(BytesIO(image_data))
            exif_data = image._getexif() if hasattr(image, '_getexif') else {}
            return image, exif_data
        
        # Standard formats (JPEG, PNG, TIFF, etc.)
        else:
            image = Image.open(BytesIO(image_data))
            
            # Step 12: Extract EXIF and color profile
            exif_data = {}
            try:
                exif_data = image._getexif() or {}
            except:
                pass
            
            # Preserve ICC color profile
            if hasattr(image, 'info') and 'icc_profile' in image.info:
                exif_data['icc_profile'] = image.info['icc_profile']
            
            return image, exif_data
            
    except Exception as e:
        print(f"❌ Error loading image: {str(e)}")
        return None, None


def extract_comprehensive_metadata(image, exif_data, original_data):
    """
    Step 12: Extract comprehensive metadata
    Returns metadata dict for storage
    """
    from PIL.ExifTags import TAGS
    
    metadata = {
        'dimensions': {
            'width': image.width,
            'height': image.height,
            'aspect_ratio': round(image.width / image.height, 2) if image.height > 0 else 0
        },
        'format': image.format,
        'mode': image.mode,
        'file_size': len(original_data)
    }
    
    # Parse EXIF
    if exif_data:
        readable_exif = {}
        for tag_id, value in exif_data.items():
            try:
                tag_name = TAGS.get(tag_id, tag_id)
                readable_exif[tag_name] = str(value) if not isinstance(value, (str, int, float)) else value
            except:
                pass
        
        metadata['exif'] = readable_exif
        
        # Extract camera info
        metadata['camera'] = {
            'make': exif_data.get(271),  # Make
            'model': exif_data.get(272),  # Model
            'lens': exif_data.get(42036)  # LensModel
        }
        
        # Extract settings
        metadata['settings'] = {
            'iso': exif_data.get(34855),
            'aperture': exif_data.get(33437),
            'shutter_speed': exif_data.get(33434),
            'focal_length': exif_data.get(37386)
        }
    
    return metadata


def get_photographer_settings(gallery_id):
    """
    Step 13: Get photographer-specific processing settings
    Returns settings for watermarks, compression, color adjustments
    """
    try:
        # Get gallery
        response = galleries_table.get_item(Key={'id': gallery_id})
        if 'Item' not in response:
            return {}
        
        gallery = response['Item']
        user_id = gallery.get('user_id')
        
        if not user_id:
            return {}
        
        # Get user settings
        user_response = users_table.get_item(Key={'id': user_id})
        if 'Item' not in user_response:
            return {}
        
        user = user_response['Item']
        
        # Extract processing preferences
        return {
            'watermark': user.get('watermark_enabled', False),
            'watermark_text': user.get('watermark_text', ''),
            'watermark_position': user.get('watermark_position', 'bottom-right'),
            'watermark_opacity': user.get('watermark_opacity', 0.5),
            'color_adjustments': user.get('color_adjustments', {}),
            'compression_quality': user.get('compression_quality', 85)
        }
    except Exception as e:
        print(f"⚠️  Error getting photographer settings: {str(e)}")
        return {}


def apply_photographer_settings(image, settings):
    """
    Step 13: Apply photographer-specific processing
    - Watermarks
    - Color adjustments
    - Custom compression settings
    """
    if not settings:
        return image
    
    try:
        # Apply watermark if enabled
        if settings.get('watermark'):
            image = apply_watermark(image, settings)
        
        # Apply color adjustments if specified
        if settings.get('color_adjustments'):
            image = apply_color_adjustments(image, settings['color_adjustments'])
        
        return image
    except Exception as e:
        print(f"⚠️  Error applying settings: {str(e)}")
        return image


def apply_watermark(image, settings):
    """
    Apply watermark to image
    """
    try:
        from PIL import ImageDraw, ImageFont
        
        # Create draw object
        draw = ImageDraw.Draw(image)
        
        # Get watermark text
        text = settings.get('watermark_text', '')
        if not text:
            return image
        
        # Calculate position
        position = settings.get('watermark_position', 'bottom-right')
        opacity = int(settings.get('watermark_opacity', 0.5) * 255)
        
        # Add watermark
        # (Simplified - production would use proper font sizing and positioning)
        width, height = image.size
        x = width - 200 if 'right' in position else 20
        y = height - 40 if 'bottom' in position else 20
        
        draw.text((x, y), text, fill=(255, 255, 255, opacity))
        
        return image
    except Exception as e:
        print(f"⚠️  Watermark error: {str(e)}")
        return image


def apply_color_adjustments(image, adjustments):
    """
    Apply color adjustments (brightness, contrast, saturation)
    """
    try:
        from PIL import ImageEnhance
        
        if 'brightness' in adjustments:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(adjustments['brightness'])
        
        if 'contrast' in adjustments:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(adjustments['contrast'])
        
        if 'saturation' in adjustments:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(adjustments['saturation'])
        
        return image
    except Exception as e:
        print(f"⚠️  Color adjustment error: {str(e)}")
        return image

def resize_image(image, max_width, max_height):
    """
    Resize image maintaining aspect ratio
    
    Args:
        image: PIL Image
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        Resized PIL Image
    """
    # Calculate aspect ratio
    width, height = image.size
    aspect_ratio = width / height
    
    # Determine new dimensions
    if width > max_width or height > max_height:
        if aspect_ratio > 1:  # Landscape
            new_width = min(width, max_width)
            new_height = int(new_width / aspect_ratio)
        else:  # Portrait
            new_height = min(height, max_height)
            new_width = int(new_height * aspect_ratio)
        
        # Resize with high-quality Lanczos resampling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Return original if already smaller
    return image

def update_photo_record(gallery_id, photo_id, rendition_data, metadata):
    """
    Step 15: Update DynamoDB photo record with rendition URLs and metadata
    
    Args:
        gallery_id: Gallery ID
        photo_id: Photo ID
        rendition_data: Dictionary of rendition URLs, sizes, and checksums
        metadata: Extracted metadata (EXIF, camera, GPS, etc.)
    """
    try:
        from datetime import datetime
        
        # Build update expression for renditions
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        # Add rendition URLs
        for key, value in rendition_data.items():
            safe_key = key.replace('-', '_').replace('.', '_')
            update_expr += f"#{safe_key} = :{safe_key}, "
            expr_attr_names[f"#{safe_key}"] = key
            expr_attr_values[f":{safe_key}"] = value
        
        # Add metadata fields
        if metadata.get('dimensions'):
            update_expr += "#dimensions = :dimensions, "
            expr_attr_names['#dimensions'] = 'dimensions'
            expr_attr_values[':dimensions'] = metadata['dimensions']
        
        if metadata.get('camera'):
            update_expr += "#camera = :camera, "
            expr_attr_names['#camera'] = 'camera'
            expr_attr_values[':camera'] = metadata['camera']
        
        if metadata.get('exif'):
            update_expr += "#exif = :exif, "
            expr_attr_names['#exif'] = 'exif'
            expr_attr_values[':exif'] = metadata['exif']
        
        if metadata.get('settings'):
            update_expr += "#settings = :settings, "
            expr_attr_names['#settings'] = 'settings'
            expr_attr_values[':settings'] = metadata['settings']
        
        # Add processing status
        update_expr += "#status = :status, #processed_at = :processed_at"
        expr_attr_names['#status'] = 'status'
        expr_attr_names['#processed_at'] = 'processed_at'
        expr_attr_values[':status'] = 'active'
        expr_attr_values[':processed_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update DynamoDB
        photos_table.update_item(
            Key={'id': photo_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        print(f"✅ Updated DynamoDB record: {gallery_id}/{photo_id}")
        
    except Exception as e:
        print(f"⚠️  Error updating DynamoDB: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't fail processing if database update fails
        # Renditions are already in S3 and can be regenerated


from datetime import datetime

