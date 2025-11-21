"""
Image Transformation Lambda - On-Demand Resizing
Handles RAW, HEIC, TIFF, JPEG, PNG formats
Triggered by CloudFront via Lambda@Edge or API Gateway

Architecture:
1. CloudFront request hits Lambda@Edge (origin request)
2. Lambda@Edge invokes this Lambda function
3. This function fetches original from S3
4. Processes and resizes based on URL parameters
5. Stores result in cache bucket
6. Returns transformed image

URL format: https://cdn.galerly.com/{s3_key}?width=800&height=600&format=jpeg&fit=inside
"""
import os
import io
import json
import boto3
from PIL import Image
import rawpy
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

s3_client = boto3.client('s3')

# Environment variables
SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET', 'galerly-uploads')
CACHE_BUCKET = os.environ.get('CACHE_BUCKET', 'galerly-image-cache')

# RAW file extensions
RAW_EXTENSIONS = {'.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef', '.3fr'}

def lambda_handler(event, context):
    """
    Main Lambda handler for image transformation
    
    Event format:
    {
        "s3_key": "gallery123/photo456.dng",
        "width": 800,
        "height": 600,
        "format": "jpeg",
        "fit": "inside",
        "quality": 85
    }
    """
    try:
        print(f"📸 Image transformation request: {json.dumps(event)}")
        
        # Extract parameters
        s3_key = event.get('s3_key')
        width = event.get('width')
        height = event.get('height')
        output_format = event.get('format', 'jpeg').lower()
        fit = event.get('fit', 'inside')
        quality = event.get('quality', 85)
        
        if not s3_key:
            return error_response(400, 'Missing s3_key parameter')
        
        # Generate cache key based on transformation parameters
        cache_key = generate_cache_key(s3_key, width, height, output_format, fit, quality)
        
        # Check if transformed image exists in cache
        try:
            cache_obj = s3_client.get_object(Bucket=CACHE_BUCKET, Key=cache_key)
            print(f"✅ Cache hit: {cache_key}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': f'image/{output_format}',
                    'Cache-Control': 'public, max-age=31536000',  # 1 year
                    'X-Cache': 'Hit'
                },
                'body': cache_obj['Body'].read(),
                'isBase64Encoded': True
            }
        except s3_client.exceptions.NoSuchKey:
            print(f"⚠️  Cache miss: {cache_key}")
            pass
        
        # Fetch original image from source bucket
        try:
            source_obj = s3_client.get_object(Bucket=SOURCE_BUCKET, Key=s3_key)
            image_data = source_obj['Body'].read()
            print(f"📥 Fetched original: {s3_key} ({len(image_data)} bytes)")
        except Exception as e:
            print(f"❌ Failed to fetch original: {str(e)}")
            return error_response(404, f'Source image not found: {s3_key}')
        
        # Process image based on format
        file_ext = os.path.splitext(s3_key.lower())[1]
        
        try:
            if file_ext in RAW_EXTENSIONS:
                print(f"📸 Processing RAW image: {file_ext}")
                pil_image = process_raw_image(image_data)
            elif file_ext in {'.heic', '.heif'}:
                print(f"📸 Processing HEIC image: {file_ext}")
                pil_image = Image.open(io.BytesIO(image_data))
            else:
                # Standard formats (JPEG, PNG, GIF, WebP, TIFF)
                print(f"📸 Processing standard image: {file_ext}")
                pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if needed (for JPEG output)
            if output_format == 'jpeg' and pil_image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', pil_image.size, (255, 255, 255))
                if pil_image.mode == 'P':
                    pil_image = pil_image.convert('RGBA')
                background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                pil_image = background
            
            # Resize if dimensions specified
            if width or height:
                pil_image = resize_image(pil_image, width, height, fit)
            
            # Convert to output format
            output_buffer = io.BytesIO()
            save_params = {}
            
            if output_format == 'jpeg':
                save_params = {'format': 'JPEG', 'quality': quality, 'optimize': True}
            elif output_format == 'png':
                save_params = {'format': 'PNG', 'optimize': True}
            elif output_format == 'webp':
                save_params = {'format': 'WEBP', 'quality': quality}
            else:
                save_params = {'format': output_format.upper()}
            
            pil_image.save(output_buffer, **save_params)
            output_data = output_buffer.getvalue()
            
            print(f"✅ Transformed: {len(image_data)} → {len(output_data)} bytes")
            
            # Store in cache
            try:
                s3_client.put_object(
                    Bucket=CACHE_BUCKET,
                    Key=cache_key,
                    Body=output_data,
                    ContentType=f'image/{output_format}',
                    CacheControl='public, max-age=31536000'
                )
                print(f"💾 Cached: {cache_key}")
            except Exception as cache_error:
                print(f"⚠️  Failed to cache: {str(cache_error)}")
                # Continue anyway - we can still return the image
            
            # Return transformed image
            import base64
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': f'image/{output_format}',
                    'Cache-Control': 'public, max-age=31536000',
                    'X-Cache': 'Miss'
                },
                'body': base64.b64encode(output_data).decode('utf-8'),
                'isBase64Encoded': True
            }
            
        except Exception as process_error:
            print(f"❌ Image processing failed: {str(process_error)}")
            import traceback
            traceback.print_exc()
            return error_response(500, f'Image processing failed: {str(process_error)}')
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, str(e))


def process_raw_image(raw_data):
    """Convert RAW image to PIL Image"""
    with rawpy.imread(io.BytesIO(raw_data)) as raw:
        # Extract RGB image
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=False,
            no_auto_bright=False,
            output_bps=8
        )
        return Image.fromarray(rgb)


def resize_image(image, width, height, fit='inside'):
    """
    Resize image based on fit mode
    
    Fit modes:
    - inside: Fit inside dimensions (maintain aspect ratio)
    - outside: Cover dimensions (maintain aspect ratio, may crop)
    - fill: Exact dimensions (may distort)
    """
    original_width, original_height = image.size
    
    # If no dimensions specified, return original
    if not width and not height:
        return image
    
    # If only one dimension specified, calculate the other
    if not width:
        width = int(original_width * (height / original_height))
    if not height:
        height = int(original_height * (width / original_width))
    
    if fit == 'inside':
        # Fit inside box (thumbnail)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        return image
    elif fit == 'outside':
        # Cover box (may crop)
        aspect = original_width / original_height
        target_aspect = width / height
        
        if aspect > target_aspect:
            # Image is wider
            new_height = height
            new_width = int(height * aspect)
        else:
            # Image is taller
            new_width = width
            new_height = int(width / aspect)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact dimensions
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        image = image.crop((left, top, left + width, top + height))
        return image
    else:
        # Exact fit (may distort)
        return image.resize((width, height), Image.Resampling.LANCZOS)


def generate_cache_key(s3_key, width, height, format, fit, quality):
    """Generate cache key for transformed image"""
    # Include all transformation parameters in cache key
    parts = [s3_key]
    if width:
        parts.append(f'w{width}')
    if height:
        parts.append(f'h{height}')
    parts.append(f'f{format}')
    if fit != 'inside':
        parts.append(f'fit{fit}')
    if quality != 85:
        parts.append(f'q{quality}')
    
    return '/'.join(parts)


def error_response(status_code, message):
    """Generate error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'error': message})
    }

