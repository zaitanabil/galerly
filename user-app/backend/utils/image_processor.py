"""
Simple Image Processing for LocalStack
Generates renditions since there's no Lambda processor in LocalStack
This simulates steps 9-15 of the production pipeline
Includes enhanced RAW photo support and watermarking
VIDEO FILES ARE NOT PROCESSED HERE - see video_processor.py
"""
import os
import io
from PIL import Image, ImageDraw, ImageFont
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("pillow-heif not installed, HEIC support disabled")

try:
    import rawpy
    import numpy as np
except ImportError:
    rawpy = None

from utils.config import s3_client, S3_BUCKET, S3_RENDITIONS_BUCKET
from utils.raw_processor import is_raw_file, generate_raw_preview
from utils.video_processor import is_video_file

# Rendition sizes matching production
RENDITION_SIZES = {
    'thumbnail': (400, 400),      # Grid display
    'small': (800, 600),           # Preview
    'medium': (2000, 2000),        # Detail view
    'large': (4000, 4000)          # High-res zoom
}

def generate_renditions(s3_key, bucket=None, image_data=None):
    """
    Generate all renditions for an uploaded image
    Steps 10-15: Process, generate, store, update database
    
    Args:
        s3_key: S3 key of original image (gallery_id/photo_id.ext)
        bucket: Source bucket (defaults to S3_BUCKET)
        image_data: Optional raw bytes of image (avoids re-download)
    
    Returns:
        dict with rendition URLs and metadata
    """
    if bucket is None:
        bucket = S3_BUCKET
    
    try:
        print(f"Generating renditions for {s3_key}...")
        
        # Check if this is a video file - videos are handled separately
        filename_from_key = s3_key.split('/')[-1]
        if is_video_file(filename_from_key):
            print(f"⚠️ Video file detected: {filename_from_key} - skipping image rendition generation")
            print(f"   Videos should be processed by video_processor.py instead")
            return {
                'success': False,
                'error': 'Video files must be processed by video_processor, not image_processor'
            }
        
        # Step 10a: Get image data (use provided or download)
        if image_data is None:
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            original_data = response['Body'].read()
        else:
            original_data = image_data
        
        # Step 10b: Open image with PIL
        # Check if it's a RAW file first for optimized processing
        is_raw = is_raw_file(filename_from_key)
        
        if is_raw and rawpy:
            # Use enhanced RAW processor
            print(f"🔄 Detected RAW file: {filename_from_key}, using RAW processor...")
            raw_preview = generate_raw_preview(original_data, size='large', quality=90)
            if raw_preview['success']:
                # Convert preview JPEG bytes back to PIL Image for rendition generation
                original_image = Image.open(io.BytesIO(raw_preview['preview_data']))
                print(f"Successfully processed RAW with enhanced processor")
            else:
                raise Exception(f"RAW processing failed: {raw_preview.get('error')}")
        else:
            # Standard image processing
            try:
                # Try standard PIL open (works for JPEG, PNG)
                # Create a NEW BytesIO for each attempt to avoid stream position issues
                original_image = Image.open(io.BytesIO(original_data))
                
                # Verify it's actually loaded
                original_image.load()
            except Exception as e:
                print(f"Standard PIL open failed for {s3_key}: {str(e)}")
                
                # If standard open fails, try explicit pillow_heif for HEIC
                heic_success = False
                try:
                    import pillow_heif
                    # Check if it's HEIC content
                    if pillow_heif.is_supported(original_data):
                        print(f"🔄 Detected HEIC content for {s3_key}, using pillow_heif...")
                        heif_file = pillow_heif.read_heif(io.BytesIO(original_data))
                        original_image = Image.frombytes(
                            heif_file.mode,
                            heif_file.size,
                            heif_file.data,
                            "raw",
                        )
                        heic_success = True
                        print(f"Successfully opened HEIC with pillow_heif")
                except ImportError:
                    print("pillow-heif not installed or import failed")
                except Exception as heic_e:
                    print(f"explicit pillow_heif failed: {str(heic_e)}")

                if not heic_success:
                    # If both failed, try rawpy as last resort
                    if rawpy:
                        try:
                            print(f"🔄 PIL/HEIC failed, trying rawpy for {s3_key}...")
                            with rawpy.imread(io.BytesIO(original_data)) as raw:
                                rgb = raw.postprocess()
                                original_image = Image.fromarray(rgb)
                            print(f"Successfully opened RAW with rawpy")
                        except Exception as raw_e:
                            print(f"rawpy also failed: {str(raw_e)}")
                            # Re-raise the original error if everything fails
                            raise e
                    else:
                        raise e
        
        # Convert RGBA to RGB if needed
        if original_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', original_image.size, (255, 255, 255))
            rgb_image.paste(original_image, mask=original_image.split()[3])
            original_image = rgb_image
        elif original_image.mode not in ('RGB', 'L'):
            original_image = original_image.convert('RGB')
        
        # Extract gallery_id and photo_id from s3_key
        parts = s3_key.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid s3_key format: {s3_key}")
        
        gallery_id = parts[0]
        photo_filename = parts[1]
        photo_id = photo_filename.rsplit('.', 1)[0]
        
        renditions = {}
        
        # Step 11-14: Generate each rendition size
        for size_name, (max_width, max_height) in RENDITION_SIZES.items():
            # Calculate dimensions maintaining aspect ratio
            img_copy = original_image.copy()
            img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Step 12: Convert to JPEG
            output = io.BytesIO()
            img_copy.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Step 14: Upload to renditions bucket
            rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
            s3_client.put_object(
                Bucket=S3_RENDITIONS_BUCKET,
                Key=rendition_key,
                Body=output.getvalue(),
                ContentType='image/jpeg'
            )
            
            renditions[size_name] = {
                'key': rendition_key,
                'size': len(output.getvalue()),
                'dimensions': img_copy.size
            }
            
            print(f"  {size_name}: {img_copy.size[0]}x{img_copy.size[1]} ({len(output.getvalue()) / 1024:.1f} KB)")
        
        print(f"Generated {len(renditions)} renditions for {s3_key}")
        
        # Step 15: Return metadata for database update
        return {
            'success': True,
            'renditions': renditions,
            'original_dimensions': original_image.size
        }
        
    except Exception as e:
        print(f"Error generating renditions for {s3_key}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def apply_watermark(image, watermark_config):
    """
    Apply watermark to an image based on configuration
    
    Args:
        image: PIL Image object
        watermark_config: dict with watermark settings
            {
                'watermark_s3_key': str,  # S3 key of watermark logo
                'position': str,  # 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'
                'opacity': float,  # 0.0 to 1.0
                'size_percent': int  # Watermark size as percentage of image width (5-50)
            }
    
    Returns:
        PIL Image with watermark applied
    """
    try:
        if not watermark_config or not watermark_config.get('watermark_s3_key'):
            return image
        
        # Download watermark from S3
        watermark_key = watermark_config['watermark_s3_key']
        try:
            watermark_response = s3_client.get_object(Bucket=S3_BUCKET, Key=watermark_key)
            watermark_data = watermark_response['Body'].read()
            watermark = Image.open(io.BytesIO(watermark_data))
        except Exception as e:
            print(f"Failed to load watermark from S3: {str(e)}")
            return image  # Return original if watermark fails
        
        # Convert watermark to RGBA if not already
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')
        
        # Get configuration with defaults
        position = watermark_config.get('position', 'bottom-right')
        opacity = watermark_config.get('opacity', 0.7)  # Default 70% opacity
        size_percent = watermark_config.get('size_percent', 15)  # Default 15% of image width
        
        # Clamp values
        opacity = max(0.0, min(1.0, opacity))
        size_percent = max(5, min(50, size_percent))
        
        # Calculate watermark size
        img_width, img_height = image.size
        watermark_width = int(img_width * (size_percent / 100))
        
        # Maintain aspect ratio
        wm_aspect = watermark.size[0] / watermark.size[1]
        watermark_height = int(watermark_width / wm_aspect)
        
        # Resize watermark
        watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
        
        # Apply opacity
        if opacity < 1.0:
            # Create alpha channel with opacity
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            watermark.putalpha(alpha)
        
        # Calculate position
        margin = int(min(img_width, img_height) * 0.02)  # 2% margin
        
        positions = {
            'top-left': (margin, margin),
            'top-right': (img_width - watermark_width - margin, margin),
            'bottom-left': (margin, img_height - watermark_height - margin),
            'bottom-right': (img_width - watermark_width - margin, img_height - watermark_height - margin),
            'center': ((img_width - watermark_width) // 2, (img_height - watermark_height) // 2)
        }
        
        position_coords = positions.get(position, positions['bottom-right'])
        
        # Create a copy of the image and paste watermark
        watermarked = image.copy()
        if watermarked.mode != 'RGBA':
            watermarked = watermarked.convert('RGBA')
        
        watermarked.paste(watermark, position_coords, watermark)
        
        # Convert back to RGB
        if watermarked.mode == 'RGBA':
            rgb_image = Image.new('RGB', watermarked.size, (255, 255, 255))
            rgb_image.paste(watermarked, mask=watermarked.split()[3])
            watermarked = rgb_image
        
        print(f"✓ Watermark applied: {position}, opacity: {opacity}, size: {size_percent}%")
        
        return watermarked
        
    except Exception as e:
        print(f"Error applying watermark: {str(e)}")
        import traceback
        traceback.print_exc()
        return image  # Return original image if watermarking fails


def generate_renditions_with_watermark(s3_key, bucket=None, image_data=None, watermark_config=None):
    """
    Generate renditions with optional watermark
    Wrapper around generate_renditions that applies watermark before generating sizes
    
    Args:
        s3_key: S3 key of original image
        bucket: Source bucket
        image_data: Optional raw bytes
        watermark_config: Optional watermark configuration dict
    
    Returns:
        dict with rendition URLs and metadata
    """
    # First get the original image processed normally
    result = generate_renditions(s3_key, bucket, image_data)
    
    # If watermark config provided and renditions successful, apply watermark
    if watermark_config and result.get('success'):
        try:
            print(f"Applying watermark to renditions for {s3_key}...")
            
            # Get original image
            if image_data is None:
                response = s3_client.get_object(Bucket=bucket or S3_BUCKET, Key=s3_key)
                original_data = response['Body'].read()
            else:
                original_data = image_data
            
            # Open and process original image
            filename_from_key = s3_key.split('/')[-1]
            is_raw = is_raw_file(filename_from_key)
            
            if is_raw and rawpy:
                raw_preview = generate_raw_preview(original_data, size='large', quality=90)
                if raw_preview['success']:
                    original_image = Image.open(io.BytesIO(raw_preview['preview_data']))
                else:
                    raise Exception(f"RAW processing failed: {raw_preview.get('error')}")
            else:
                original_image = Image.open(io.BytesIO(original_data))
                original_image.load()
            
            # Convert RGBA to RGB if needed
            if original_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', original_image.size, (255, 255, 255))
                rgb_image.paste(original_image, mask=original_image.split()[3])
                original_image = rgb_image
            elif original_image.mode not in ('RGB', 'L'):
                original_image = original_image.convert('RGB')
            
            # Apply watermark to original
            watermarked_image = apply_watermark(original_image, watermark_config)
            
            # Extract gallery_id and photo_id
            parts = s3_key.split('/')
            gallery_id = parts[0]
            photo_filename = parts[1]
            photo_id = photo_filename.rsplit('.', 1)[0]
            
            # Regenerate renditions from watermarked image
            renditions = {}
            for size_name, (max_width, max_height) in RENDITION_SIZES.items():
                img_copy = watermarked_image.copy()
                img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                img_copy.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
                s3_client.put_object(
                    Bucket=S3_RENDITIONS_BUCKET,
                    Key=rendition_key,
                    Body=output.getvalue(),
                    ContentType='image/jpeg'
                )
                
                renditions[size_name] = {
                    'key': rendition_key,
                    'size': len(output.getvalue()),
                    'dimensions': img_copy.size
                }
                
                print(f"  {size_name} (watermarked): {img_copy.size[0]}x{img_copy.size[1]} ({len(output.getvalue()) / 1024:.1f} KB)")
            
            print(f"✓ Generated {len(renditions)} watermarked renditions for {s3_key}")
            
            return {
                'success': True,
                'renditions': renditions,
                'original_dimensions': watermarked_image.size,
                'watermarked': True
            }
            
        except Exception as e:
            print(f"Error applying watermark to renditions: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return original non-watermarked result
            return result
    
    return result


def process_upload_async(s3_key, bucket=None, image_data=None, watermark_config=None):
    """
    Simulate async processing queue (Step 9)
    In production, this would be triggered by S3 event → SQS → Lambda
    For LocalStack, we call it synchronously after upload
    
    Args:
        s3_key: S3 key of uploaded image
        bucket: Source bucket
        image_data: Optional raw image bytes
        watermark_config: Optional watermark configuration
    
    Returns:
        dict with processing results
    """
    if watermark_config:
        return generate_renditions_with_watermark(s3_key, bucket, image_data, watermark_config)
    else:
        return generate_renditions(s3_key, bucket, image_data)

