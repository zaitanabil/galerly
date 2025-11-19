"""
Lambda Origin Function - Image Resizing
Production-grade solution like Instagram/Pinterest

This Lambda runs in us-east-1 (not @Edge) and handles:
1. Downloading original from S3
2. Resizing with Pillow (AWS Lambda native)
3. Uploading resized version back to S3
4. Returning resized image to CloudFront (which caches it)

Architecture:
- Lambda@Edge (viewer-request) = Fast URL rewriting
- This Lambda (origin) = Heavy image processing
- S3 = Storage for originals + resized cache
- CloudFront = CDN caching layer

Cost Optimization:
- Each image resized ONCE (then cached forever in S3 + CloudFront)
- No Sharp compilation issues (uses Pillow which is pre-installed in Lambda)
- CloudFront serves 99%+ of requests from cache
"""

import json
import boto3
import os
from io import BytesIO
from PIL import Image

s3_client = boto3.client('s3')

BUCKET = os.environ.get('S3_PHOTOS_BUCKET', 'galerly-images-storage')
ALLOWED_DIMENSIONS = [
    (800, 600),    # Thumbnail
    (2000, 2000),  # Medium/Large
    (400, 400),    # Small thumb
    (150, 150),    # Tiny thumb
]

# Quality settings (Instagram-like)
JPEG_QUALITY = 85
WEBP_QUALITY = 80


def lambda_handler(event, context):
    """
    CloudFront Origin Request Handler
    Triggered when CloudFront doesn't find resized image in S3
    """
    
    print(f"[Origin Lambda] Event: {json.dumps(event)}")
    
    # CloudFront origin request structure
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    
    print(f"[Origin Lambda] URI: {uri}")
    
    # Parse: /resized/{width}x{height}/{s3_key}
    parts = uri.strip('/').split('/')
    if len(parts) < 3 or parts[0] != 'resized':
        # Not a resize request, return 404
        print(f"[Origin Lambda] Invalid resize URI: {uri}")
        return {
            'status': '404',
            'statusDescription': 'Not Found',
            'headers': {
                'content-type': [{'key': 'Content-Type', 'value': 'text/plain'}],
                'cache-control': [{'key': 'Cache-Control', 'value': 'public, max-age=300'}],
            },
            'body': 'Image not found'
        }
    
    # Parse dimensions
    dimensions = parts[1]  # e.g. "800x600"
    s3_key = '/'.join(parts[2:])  # Original S3 key
    
    try:
        width, height = map(int, dimensions.split('x'))
    except ValueError:
        print(f"[Origin Lambda] Invalid dimensions: {dimensions}")
        return error_response(400, 'Invalid dimensions')
    
    # Validate dimensions
    if (width, height) not in ALLOWED_DIMENSIONS:
        print(f"[Origin Lambda] Dimension not allowed: {width}x{height}")
        return error_response(403, f'Forbidden dimension. Allowed: {ALLOWED_DIMENSIONS}')
    
    print(f"[Origin Lambda] Processing: {width}x{height} for {s3_key}")
    
    try:
        # 1. Download original from S3
        print(f"[Origin Lambda] Downloading original: {s3_key}")
        original_obj = s3_client.get_object(Bucket=BUCKET, Key=s3_key)
        original_data = original_obj['Body'].read()
        original_content_type = original_obj.get('ContentType', 'image/jpeg')
        
        print(f"[Origin Lambda] Original size: {len(original_data)} bytes")
        
        # 2. Resize image
        print(f"[Origin Lambda] Resizing to {width}x{height}...")
        resized_data, resized_content_type = resize_image(
            original_data, 
            width, 
            height,
            original_content_type
        )
        
        print(f"[Origin Lambda] Resized size: {len(resized_data)} bytes ({len(resized_data)/len(original_data)*100:.1f}%)")
        
        # 3. Upload resized version to S3 (cache for future requests)
        resized_key = f"resized/{width}x{height}/{s3_key}"
        print(f"[Origin Lambda] Uploading to S3: {resized_key}")
        
        s3_client.put_object(
            Bucket=BUCKET,
            Key=resized_key,
            Body=resized_data,
            ContentType=resized_content_type,
            CacheControl='public, max-age=31536000, immutable',  # Cache forever
            Metadata={
                'original-key': s3_key,
                'resized-by': 'lambda-origin',
                'dimensions': f'{width}x{height}'
            }
        )
        
        print(f"[Origin Lambda] ✅ Upload complete, returning to CloudFront")
        
        # 4. Return to CloudFront (which will cache it)
        import base64
        return {
            'status': '200',
            'statusDescription': 'OK',
            'headers': {
                'content-type': [{'key': 'Content-Type', 'value': resized_content_type}],
                'cache-control': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}],
                'x-resized-by': [{'key': 'X-Resized-By', 'value': 'lambda-origin'}],
                'x-original-size': [{'key': 'X-Original-Size', 'value': str(len(original_data))}],
                'x-resized-size': [{'key': 'X-Resized-Size', 'value': str(len(resized_data))}],
            },
            'bodyEncoding': 'base64',
            'body': base64.b64encode(resized_data).decode('utf-8')
        }
        
    except s3_client.exceptions.NoSuchKey:
        print(f"[Origin Lambda] Original not found: {s3_key}")
        return error_response(404, 'Original image not found')
    
    except Exception as e:
        print(f"[Origin Lambda] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, 'Internal error resizing image')


def resize_image(image_data, width, height, original_content_type):
    """
    Resize image using Pillow (like Instagram/Pinterest)
    
    Returns:
        (resized_bytes, content_type)
    """
    
    # Load image
    img = Image.open(BytesIO(image_data))
    
    # Convert RGBA to RGB if needed (for JPEG)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Calculate new size (maintain aspect ratio, fit inside box)
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    # Save to buffer
    output = BytesIO()
    
    # Determine output format
    if 'image/webp' in original_content_type or original_content_type == 'image/webp':
        img.save(output, format='WEBP', quality=WEBP_QUALITY, method=6)
        content_type = 'image/webp'
    elif 'image/png' in original_content_type:
        # PNG optimization
        img.save(output, format='PNG', optimize=True)
        content_type = 'image/png'
    else:
        # Default to JPEG (most common, best compression)
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
        content_type = 'image/jpeg'
    
    output.seek(0)
    return output.read(), content_type


def error_response(status, message):
    """Generate error response"""
    return {
        'status': str(status),
        'statusDescription': message,
        'headers': {
            'content-type': [{'key': 'Content-Type', 'value': 'text/plain'}],
            'cache-control': [{'key': 'Cache-Control', 'value': 'public, max-age=300'}],
        },
        'body': message
    }

