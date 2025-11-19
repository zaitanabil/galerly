"""
Serverless Image Resizer - Cost-Optimized Solution
Using API Gateway + Lambda (not Lambda@Edge)

This approach:
✅ $0 cost when idle (no CloudFront)
✅ Simple deployment (single Lambda)
✅ Fast enough for most use cases
✅ No Lambda@Edge complexity

Architecture:
Browser → API Gateway → Lambda (Pillow resize) → Return resized image
          ↓
     Cache in S3 for subsequent requests

URL Format:
https://api.galerly.com/resize?url=s3://bucket/key&width=800&height=600
"""

import json
import boto3
import base64
import os
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse, parse_qs

s3_client = boto3.client('s3')

BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
ALLOWED_DIMENSIONS = [
    (800, 600),    # Thumbnail
    (2000, 2000),  # Medium/Large
    (400, 400),    # Small thumb
    (150, 150),    # Tiny thumb
]

# Quality settings
JPEG_QUALITY = 85
WEBP_QUALITY = 80


def lambda_handler(event, context):
    """
    API Gateway Lambda handler for image resizing
    
    Query Parameters:
    - key: S3 key (e.g. "gallery123/photo456.jpg")
    - width: Desired width
    - height: Desired height
    """
    
    print(f"Event: {json.dumps(event)}")
    
    # Parse query parameters
    params = event.get('queryStringParameters', {}) or {}
    s3_key = params.get('key')
    
    try:
        width = int(params.get('width', 800))
        height = int(params.get('height', 600))
    except (ValueError, TypeError):
        return error_response(400, 'Invalid width or height')
    
    # Validate inputs
    if not s3_key:
        return error_response(400, 'Missing "key" parameter')
    
    if (width, height) not in ALLOWED_DIMENSIONS:
        return error_response(
            403, 
            f'Invalid dimensions {width}x{height}. Allowed: {ALLOWED_DIMENSIONS}'
        )
    
    print(f"Resizing {s3_key} to {width}x{height}")
    
    # Check if resized version already exists in S3 cache
    resized_key = f"resized/{width}x{height}/{s3_key}"
    
    try:
        # Try to get cached resized version
        print(f"Checking cache: {resized_key}")
        cached_obj = s3_client.get_object(Bucket=BUCKET, Key=resized_key)
        cached_data = cached_obj['Body'].read()
        content_type = cached_obj.get('ContentType', 'image/jpeg')
        
        print(f"✅ Cache hit! Returning cached version ({len(cached_data)} bytes)")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=31536000, immutable',
                'X-Cache': 'HIT',
            },
            'body': base64.b64encode(cached_data).decode('utf-8'),
            'isBase64Encoded': True
        }
        
    except s3_client.exceptions.NoSuchKey:
        # Cache miss - need to resize
        print(f"Cache miss - will resize original")
        pass
    
    try:
        # Download original from S3
        print(f"Downloading original: {s3_key}")
        original_obj = s3_client.get_object(Bucket=BUCKET, Key=s3_key)
        original_data = original_obj['Body'].read()
        original_content_type = original_obj.get('ContentType', 'image/jpeg')
        
        print(f"Original size: {len(original_data)} bytes")
        
        # Resize image
        print(f"Resizing to {width}x{height}...")
        resized_data, resized_content_type = resize_image(
            original_data, 
            width, 
            height,
            original_content_type
        )
        
        print(f"Resized size: {len(resized_data)} bytes ({len(resized_data)/len(original_data)*100:.1f}%)")
        
        # Upload resized version to S3 (cache for future requests)
        print(f"Caching to S3: {resized_key}")
        s3_client.put_object(
            Bucket=BUCKET,
            Key=resized_key,
            Body=resized_data,
            ContentType=resized_content_type,
            CacheControl='public, max-age=31536000, immutable',
            Metadata={
                'original-key': s3_key,
                'dimensions': f'{width}x{height}'
            }
        )
        
        print(f"✅ Resize complete, cached in S3")
        
        # Return resized image
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': resized_content_type,
                'Cache-Control': 'public, max-age=31536000, immutable',
                'X-Cache': 'MISS',
                'X-Original-Size': str(len(original_data)),
                'X-Resized-Size': str(len(resized_data)),
            },
            'body': base64.b64encode(resized_data).decode('utf-8'),
            'isBase64Encoded': True
        }
        
    except s3_client.exceptions.NoSuchKey:
        print(f"Original not found: {s3_key}")
        return error_response(404, f'Image not found: {s3_key}')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f'Error resizing image: {str(e)}')


def resize_image(image_data, width, height, original_content_type):
    """
    Resize image using Pillow
    
    Returns:
        (resized_bytes, content_type)
    """
    
    # Load image
    img = Image.open(BytesIO(image_data))
    
    # Convert RGBA to RGB if needed (for JPEG)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Calculate new size (maintain aspect ratio)
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    # Save to buffer
    output = BytesIO()
    
    # Determine output format
    if 'image/webp' in original_content_type:
        img.save(output, format='WEBP', quality=WEBP_QUALITY, method=6)
        content_type = 'image/webp'
    elif 'image/png' in original_content_type:
        img.save(output, format='PNG', optimize=True)
        content_type = 'image/png'
    else:
        # Default to JPEG
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
        content_type = 'image/jpeg'
    
    output.seek(0)
    return output.read(), content_type


def error_response(status, message):
    """Generate error response"""
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        },
        'body': json.dumps({'error': message})
    }

