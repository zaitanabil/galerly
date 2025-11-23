"""
Simple Image Processing for LocalStack
Generates renditions since there's no Lambda processor in LocalStack
This simulates steps 9-15 of the production pipeline
"""
import os
import io
from PIL import Image
from utils.config import s3_client, S3_BUCKET, S3_RENDITIONS_BUCKET

# Rendition sizes matching production
RENDITION_SIZES = {
    'thumbnail': (400, 400),      # Grid display
    'small': (800, 600),           # Preview
    'medium': (2000, 2000),        # Detail view
    'large': (4000, 4000)          # High-res zoom
}

def generate_renditions(s3_key, bucket=None):
    """
    Generate all renditions for an uploaded image
    Steps 10-15: Process, generate, store, update database
    
    Args:
        s3_key: S3 key of original image (gallery_id/photo_id.ext)
        bucket: Source bucket (defaults to S3_BUCKET)
    
    Returns:
        dict with rendition URLs and metadata
    """
    if bucket is None:
        bucket = S3_BUCKET
    
    try:
        print(f"📸 Generating renditions for {s3_key}...")
        
        # Step 10a: Download original from S3
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        original_data = response['Body'].read()
        
        # Step 10b: Open image with PIL
        original_image = Image.open(io.BytesIO(original_data))
        
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
            
            print(f"  ✅ {size_name}: {img_copy.size[0]}x{img_copy.size[1]} ({len(output.getvalue()) / 1024:.1f} KB)")
        
        print(f"✅ Generated {len(renditions)} renditions for {s3_key}")
        
        # Step 15: Return metadata for database update
        return {
            'success': True,
            'renditions': renditions,
            'original_dimensions': original_image.size
        }
        
    except Exception as e:
        print(f"❌ Error generating renditions for {s3_key}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def process_upload_async(s3_key, bucket=None):
    """
    Simulate async processing queue (Step 9)
    In production, this would be triggered by S3 event → SQS → Lambda
    For LocalStack, we call it synchronously after upload
    """
    return generate_renditions(s3_key, bucket)

