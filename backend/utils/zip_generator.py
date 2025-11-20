"""
Zip File Generator Utility
Pre-generates ZIP files containing all gallery photos and stores them in S3

IMPORTANT: Images are stored in the ZIP file exactly as uploaded by the photographer.
- No compression (ZIP_STORED method)
- No format conversion
- No resizing or processing
- Byte-for-byte identical to original S3 files
"""
import io
import zipfile
from boto3.dynamodb.conditions import Key
from utils.config import s3_client, S3_BUCKET, photos_table


def generate_gallery_zip(gallery_id):
    """
    Generate ZIP file containing all photos in a gallery and store it in S3
    
    Args:
        gallery_id: The gallery ID
        
    Returns:
        dict with 'success' (bool), 's3_key' (str), 'zip_url' (str), 'photo_count' (int)
    """
    try:
        print(f"📦 Generating ZIP for gallery {gallery_id}...")
        
        # Get all photos in this gallery
        photos_response = photos_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        photos = photos_response.get('Items', [])
        
        if not photos:
            print(f"⚠️  No photos found for gallery {gallery_id}")
            # Still create an empty zip or delete existing zip
            zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=zip_s3_key)
                print(f"🗑️  Deleted empty zip file: {zip_s3_key}")
            except:
                pass
            return {
                'success': True,
                's3_key': zip_s3_key,
                'zip_url': None,
                'photo_count': 0
            }
        
        print(f"✅ Found {len(photos)} photos")
        
        # Create in-memory ZIP file
        # Use ZIP_STORED (no compression) to preserve images exactly as uploaded
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:
            used_filenames = {}  # Track duplicates
            
            for photo in photos:
                try:
                    # Using boto3.resource API, items are already in Python format
                    photo_id = photo.get('id', '')
                    s3_key = photo.get('s3_key')
                    
                    if not s3_key:
                        print(f"  ⚠️  Skipping photo {photo_id}: no s3_key")
                        continue
                    
                    # Get filename from database, or extract from S3 key to preserve original format
                    filename = photo.get('filename')
                    if not filename:
                        # Extract filename from S3 key (e.g., "gallery-id/photo-id.png" → "photo-id.png")
                        filename = s3_key.split('/')[-1]
                        print(f"  ℹ️  No filename in DB for {photo_id}, using S3 key: {filename}")
                    
                    # Handle duplicate filenames
                    if filename in used_filenames:
                        # Extract extension
                        name_parts = filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            base_name, ext = name_parts
                            filename = f"{base_name}_{used_filenames[filename]}.{ext}"
                        else:
                            filename = f"{filename}_{used_filenames[filename]}"
                        used_filenames[filename] = used_filenames.get(filename, 0) + 1
                    else:
                        used_filenames[filename] = 1
                    
                    # Download original image from S3 (no processing/modification)
                    print(f"  📥 Adding {s3_key} as {filename}...")
                    s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
                    image_data = s3_object['Body'].read()
                    
                    # Add to ZIP without compression (preserves original exactly)
                    zip_file.writestr(filename, image_data)
                    print(f"  ✅ Added {filename} ({len(image_data):,} bytes)")
                    
                except Exception as photo_error:
                    photo_id = photo.get('id', 'unknown')
                    print(f"  ❌ Error processing photo {photo_id}: {str(photo_error)}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Get ZIP data
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_size_mb = len(zip_data) / (1024 * 1024)
        
        print(f"✅ ZIP created: {len(photos)} photos, {zip_size_mb:.2f} MB")
        
        # Upload ZIP to S3
        zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=zip_s3_key,
            Body=zip_data,
            ContentType='application/zip',
            CacheControl='max-age=3600'  # Cache for 1 hour
        )
        
        # Generate CloudFront URL for the zip
        from utils.cdn_urls import CDN_DOMAIN
        zip_url = f"https://{CDN_DOMAIN}/{zip_s3_key}"
        
        print(f"✅ ZIP uploaded to S3: {zip_s3_key}")
        print(f"✅ ZIP URL: {zip_url}")
        
        return {
            'success': True,
            's3_key': zip_s3_key,
            'zip_url': zip_url,
            'photo_count': len(photos),
            'zip_size_mb': zip_size_mb
        }
        
    except Exception as e:
        print(f"❌ Error generating gallery ZIP: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

