"""
Automatic Image Processing Lambda
Triggered by S3 upload events to generate all renditions immediately

Flow:
1. S3 upload triggers this Lambda
2. Download original from S3
3. Generate multiple renditions (thumbnail, small, medium, large)
4. Upload renditions to S3 renditions bucket
5. Update DynamoDB with rendition URLs

This follows industry best practices (Instagram, Airbnb, etc.)
where images are processed ONCE during upload, not on every view.
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
photos_table = dynamodb.Table('galerly-photos')

# Configuration
SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET', 'galerly-images-storage')
RENDITIONS_BUCKET = os.environ.get('RENDITIONS_BUCKET', 'galerly-renditions')
CDN_DOMAIN = os.environ.get('CDN_DOMAIN', 'cdn.galerly.com')

# Rendition sizes following industry standards
RENDITIONS = {
    'thumbnail': (400, 400),      # Grid display
    'small': (800, 600),           # Preview
    'medium': (2000, 2000),        # Detail view
    'large': (4000, 4000)          # High-res zoom
}

# Register HEIF opener
pillow_heif.register_heif_opener()

def lambda_handler(event, context):
    """
    Process S3 upload event and generate renditions
    
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
            
            print(f"📥 Processing upload: s3://{bucket}/{key}")
            
            # Skip if already a rendition (avoid recursive processing)
            if key.startswith('renditions/'):
                print(f"⏭️  Skipping rendition file: {key}")
                continue
            
            # Process the image
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
    Download image, generate all renditions, upload to S3, update database
    
    Args:
        bucket: Source S3 bucket
        s3_key: S3 key (gallery_id/photo_id.ext)
    """
    try:
        # Download original
        print(f"⬇️  Downloading original: {s3_key}")
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        original_data = response['Body'].read()
        
        # Detect format from file extension
        file_ext = os.path.splitext(s3_key)[1].lower()
        
        # Load image based on format
        image = load_image(original_data, file_ext)
        
        if image is None:
            print(f"⚠️  Could not load image: {s3_key}")
            return
        
        # Extract photo_id and gallery_id from S3 key
        # Format: gallery_id/photo_id.ext
        parts = s3_key.split('/')
        if len(parts) != 2:
            print(f"⚠️  Invalid S3 key format: {s3_key}")
            return
            
        gallery_id = parts[0]
        photo_filename = parts[1]
        photo_id = os.path.splitext(photo_filename)[0]
        
        # Generate and upload all renditions
        rendition_urls = {}
        
        for size_name, (max_width, max_height) in RENDITIONS.items():
            try:
                # Resize image
                rendition = resize_image(image, max_width, max_height)
                
                # Convert to JPEG for web display
                buffer = BytesIO()
                rendition.convert('RGB').save(
                    buffer, 
                    format='JPEG', 
                    quality=85, 
                    optimize=True
                )
                buffer.seek(0)
                
                # Generate S3 key for rendition
                # Format: renditions/gallery_id/photo_id_size.jpg
                rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
                
                # Upload to S3
                s3_client.put_object(
                    Bucket=RENDITIONS_BUCKET,
                    Key=rendition_key,
                    Body=buffer.getvalue(),
                    ContentType='image/jpeg',
                    CacheControl='public, max-age=31536000'  # 1 year cache
                )
                
                # Generate CDN URL
                rendition_url = f"https://{CDN_DOMAIN}/{rendition_key}"
                rendition_urls[f"{size_name}_url"] = rendition_url
                
                print(f"✅ Generated {size_name}: {rendition_key}")
                
            except Exception as e:
                print(f"❌ Error generating {size_name}: {str(e)}")
                continue
        
        # Update DynamoDB with rendition URLs
        if rendition_urls:
            update_photo_record(gallery_id, photo_id, rendition_urls)
        
        print(f"🎉 Processing complete for {s3_key}")
        
    except Exception as e:
        print(f"❌ Error processing {s3_key}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def load_image(image_data, file_ext):
    """
    Load image from bytes, handling multiple formats
    
    Args:
        image_data: Raw image bytes
        file_ext: File extension (.jpg, .heic, .dng, etc.)
    
    Returns:
        PIL Image object or None
    """
    try:
        # RAW formats
        raw_extensions = ['.dng', '.cr2', '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef']
        
        if file_ext in raw_extensions:
            print(f"📸 Processing RAW image: {file_ext}")
            with rawpy.imread(BytesIO(image_data)) as raw:
                rgb = raw.postprocess()
                return Image.fromarray(rgb)
        
        # HEIC format
        elif file_ext in ['.heic', '.heif']:
            print(f"📸 Processing HEIC image")
            return Image.open(BytesIO(image_data))
        
        # Standard formats (JPEG, PNG, TIFF, etc.)
        else:
            return Image.open(BytesIO(image_data))
            
    except Exception as e:
        print(f"❌ Error loading image: {str(e)}")
        return None

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

def update_photo_record(gallery_id, photo_id, rendition_urls):
    """
    Update DynamoDB photo record with rendition URLs
    
    Args:
        gallery_id: Gallery ID
        photo_id: Photo ID
        rendition_urls: Dictionary of rendition URLs
    """
    try:
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        
        for key, value in rendition_urls.items():
            update_expr += f"#{key} = :{key}, "
            expr_attr_values[f":{key}"] = value
        
        # Add processing status
        update_expr += "#status = :status, #processed_at = :processed_at"
        expr_attr_values[':status'] = 'active'
        expr_attr_values[':processed_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Expression attribute names (to handle reserved keywords)
        expr_attr_names = {'#status': 'status', '#processed_at': 'processed_at'}
        for key in rendition_urls.keys():
            expr_attr_names[f"#{key}"] = key
        
        # Update DynamoDB
        photos_table.update_item(
            Key={
                'gallery_id': gallery_id,
                'id': photo_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        print(f"✅ Updated DynamoDB record: {gallery_id}/{photo_id}")
        
    except Exception as e:
        print(f"⚠️  Error updating DynamoDB: {str(e)}")
        # Don't fail processing if database update fails
        # Renditions are already in S3 and can be regenerated

from datetime import datetime

