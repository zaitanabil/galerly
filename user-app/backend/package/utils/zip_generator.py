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
    
    Automatically validates that photos exist in S3 before including them.
    Skips orphaned records where S3 files are missing.
    
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
        
        print(f"✅ Found {len(photos)} photo records in DynamoDB")
        
        # Validate photos - check if S3 files actually exist
        valid_photos = []
        orphaned_photos = []
        
        for photo in photos:
            photo_id = photo.get('id', '')
            s3_key = photo.get('s3_key')
            filename = photo.get('filename', 'unknown')
            
            if not s3_key:
                print(f"  ⚠️  Skipping photo {photo_id}: no s3_key")
                orphaned_photos.append(photo_id)
                continue
            
            # Check if file exists in S3
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
                valid_photos.append(photo)
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print(f"  ⚠️  Skipping orphaned photo: {filename} (ID: {photo_id}) - S3 file missing")
                    orphaned_photos.append(photo_id)
                else:
                    print(f"  ⚠️  Error checking S3 for {filename}: {e}")
                    orphaned_photos.append(photo_id)
            except Exception as e:
                print(f"  ⚠️  Error validating {filename}: {e}")
                orphaned_photos.append(photo_id)
        
        if orphaned_photos:
            print(f"⚠️  Found {len(orphaned_photos)} orphaned photo records (DB exists but S3 file missing)")
            print(f"✅ Including only {len(valid_photos)} valid photos in ZIP")
        else:
            print(f"✅ All {len(valid_photos)} photos validated successfully")
        
        if not valid_photos:
            print(f"⚠️  No valid photos to include in ZIP (all orphaned)")
            # Delete the ZIP file since there are no valid photos
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
        
        # Create in-memory ZIP file with only valid photos
        # Use ZIP_STORED (no compression) to preserve images exactly as uploaded
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:
            used_filenames = {}  # Track duplicates
            
            for photo in valid_photos:
                try:
                    # Using boto3.resource API, items are already in Python format
                    photo_id = photo.get('id', '')
                    s3_key = photo.get('s3_key')
                    
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
        
        print(f"✅ ZIP created: {len(valid_photos)} photos, {zip_size_mb:.2f} MB")
        
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
            'photo_count': len(valid_photos),
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

