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
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import s3_client, S3_BUCKET, S3_RENDITIONS_BUCKET, photos_table


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
        print(f"Generating ZIP for gallery {gallery_id}...")
        
        # Get all photos in this gallery
        photos_response = photos_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id)
        )
        photos = photos_response.get('Items', [])
        
        if not photos:
            print(f" No photos found for gallery {gallery_id}")
            # Still create an empty zip or delete existing zip
            zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
            try:
                # Delete from renditions bucket (where ZIPs are stored)
                s3_client.delete_object(Bucket=S3_RENDITIONS_BUCKET, Key=zip_s3_key)
                print(f" Deleted empty zip file: {zip_s3_key}")
            except:
                pass
            return {
                'success': True,
                's3_key': zip_s3_key,
                'zip_url': None,
                'photo_count': 0
            }
        
        print(f"Found {len(photos)} photo records in DynamoDB")
        
        # Validate photos - check if S3 files actually exist
        valid_photos = []
        orphaned_photos = []
        
        for photo in photos:
            photo_id = photo.get('id', '')
            s3_key = photo.get('s3_key')
            filename = photo.get('filename', 'unknown')
            
            if not s3_key:
                print(f"   Skipping photo {photo_id}: no s3_key")
                orphaned_photos.append(photo_id)
                continue
            
            # Check if file exists in S3
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
                valid_photos.append(photo)
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print(f"   Skipping orphaned photo: {filename} (ID: {photo_id}) - S3 file missing")
                    orphaned_photos.append(photo_id)
                else:
                    print(f"   Error checking S3 for {filename}: {e}")
                    orphaned_photos.append(photo_id)
            except Exception as e:
                print(f"   Error validating {filename}: {e}")
                orphaned_photos.append(photo_id)
        
        if orphaned_photos:
            print(f" Found {len(orphaned_photos)} orphaned photo records (DB exists but S3 file missing)")
            print(f"Including only {len(valid_photos)} valid photos in ZIP")
        else:
            print(f"All {len(valid_photos)} photos validated successfully")
        
        if not valid_photos:
            print(f" No valid photos to include in ZIP (all orphaned)")
            # Delete the ZIP file since there are no valid photos
            zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=zip_s3_key)
                print(f" Deleted empty zip file: {zip_s3_key}")
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
        successfully_added = 0
        failed_photos = []
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:
            used_filenames = {}  # Track duplicates
            
            for idx, photo in enumerate(valid_photos, 1):
                try:
                    # Using boto3.resource API, items are already in Python format
                    photo_id = photo.get('id', '')
                    s3_key = photo.get('s3_key')
                    
                    # PRIORITY: Use original file if available (HEIC, RAW, etc)
                    # Otherwise use converted file (JPEG)
                    original_s3_key = photo.get('original_s3_key')
                    original_filename = photo.get('original_filename')
                    
                    download_s3_key = original_s3_key if original_s3_key else s3_key
                    download_filename = original_filename if original_filename else photo.get('filename')
                    
                    if not download_s3_key:
                        print(f"   Photo {idx}/{len(valid_photos)} ({photo_id}): No s3_key, skipping")
                        failed_photos.append(photo_id)
                        continue
                    
                    # Double-check S3 file exists before downloading
                    try:
                        s3_client.head_object(Bucket=S3_BUCKET, Key=download_s3_key)
                    except s3_client.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == '404':
                            # Original missing, try converted file
                            if original_s3_key and s3_key:
                                print(f"   Original file missing, falling back to converted: {s3_key}")
                                download_s3_key = s3_key
                                download_filename = photo.get('filename')
                                try:
                                    s3_client.head_object(Bucket=S3_BUCKET, Key=download_s3_key)
                                except:
                                    print(f"   Photo {idx}/{len(valid_photos)} ({photo_id}): Both original and converted missing, skipping")
                                    failed_photos.append(photo_id)
                                    continue
                            else:
                                print(f"   Photo {idx}/{len(valid_photos)} ({photo_id}): S3 file missing, skipping")
                                failed_photos.append(photo_id)
                                continue
                        else:
                            raise
                    
                    # Get filename from database
                    filename = download_filename
                    if not filename:
                        # Extract filename from S3 key (e.g., "gallery-id/photo-id.png" → "photo-id.png")
                        filename = download_s3_key.split('/')[-1]
                        print(f"  Photo {idx}/{len(valid_photos)}: No filename in DB for {photo_id}, using S3 key: {filename}")
                    
                    # Handle duplicate filenames
                    original_filename = filename
                    if filename in used_filenames:
                        # Extract extension
                        name_parts = filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            base_name, ext = name_parts
                            filename = f"{base_name}_{used_filenames[original_filename]}.{ext}"
                        else:
                            filename = f"{filename}_{used_filenames[original_filename]}"
                        used_filenames[original_filename] = used_filenames.get(original_filename, 0) + 1
                    else:
                        used_filenames[original_filename] = 1
                    
                    # Download original image from S3 (no processing/modification)
                    # Uses original file (HEIC/RAW) if available, otherwise converted (JPEG)
                    print(f"  📥 Photo {idx}/{len(valid_photos)}: Downloading {download_s3_key}...")
                    s3_object = s3_client.get_object(Bucket=S3_BUCKET, Key=download_s3_key)
                    image_data = s3_object['Body'].read()
                    
                    if not image_data or len(image_data) == 0:
                        print(f"   Photo {idx}/{len(valid_photos)} ({photo_id}): Empty file, skipping")
                        failed_photos.append(photo_id)
                        continue
                    
                    # Add to ZIP without compression (preserves original exactly)
                    zip_file.writestr(filename, image_data)
                    successfully_added += 1
                    print(f"  Photo {idx}/{len(valid_photos)}: Added {filename} ({len(image_data):,} bytes)")
                    
                except Exception as photo_error:
                    photo_id = photo.get('id', 'unknown')
                    print(f"  Photo {idx}/{len(valid_photos)} ({photo_id}): Error - {str(photo_error)}")
                    import traceback
                    traceback.print_exc()
                    failed_photos.append(photo_id)
                    continue
        
        if failed_photos:
            print(f" Failed to add {len(failed_photos)} photos to ZIP (out of {len(valid_photos)} valid photos)")
        
        if successfully_added == 0:
            print(f"No photos were successfully added to ZIP!")
            # Delete the ZIP file since there are no valid photos
            zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
            try:
                # Delete from renditions bucket (where ZIPs are stored)
                s3_client.delete_object(Bucket=S3_RENDITIONS_BUCKET, Key=zip_s3_key)
                print(f" Deleted empty zip file: {zip_s3_key}")
            except:
                pass
            return {
                'success': True,
                's3_key': zip_s3_key,
                'zip_url': None,
                'photo_count': 0
            }
        
        # Get ZIP data
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_size_mb = len(zip_data) / (1024 * 1024)
        
        print(f"ZIP created: {successfully_added} photos successfully added, {zip_size_mb:.2f} MB")
        if failed_photos:
            print(f" {len(failed_photos)} photos failed to add (orphaned or errors)")
        
        # Upload ZIP to S3 renditions bucket (where ZIPs are stored)
        zip_s3_key = f"{gallery_id}/gallery-all-photos.zip"
        print(f"📤 Uploading ZIP to S3: {zip_s3_key}...")
        s3_client.put_object(
            Bucket=S3_RENDITIONS_BUCKET,
            Key=zip_s3_key,
            Body=zip_data,
            ContentType='application/zip',
            CacheControl='no-cache, no-store, must-revalidate'  # Don't cache - always get fresh ZIP
        )
        
        # Invalidate CloudFront cache for this ZIP file to ensure fresh download
        try:
            import os
            import boto3
            cloudfront_dist_id = os.environ.get('CLOUDFRONT_DISTRIBUTION_ID')
            if cloudfront_dist_id:
                cloudfront_client = boto3.client('cloudfront', region_name=os.environ.get('AWS_REGION'))
                try:
                    invalidation = cloudfront_client.create_invalidation(
                        DistributionId=cloudfront_dist_id,
                        InvalidationBatch={
                            'Paths': {
                                'Quantity': 1,
                                'Items': [f'/{zip_s3_key}']
                            },
                            'CallerReference': f'zip-{gallery_id}-{datetime.utcnow().isoformat()}'
                        }
                    )
                    invalidation_id = invalidation.get('Invalidation', {}).get('Id', 'N/A')
                    print(f"🔄 CloudFront cache invalidated for ZIP: {invalidation_id}")
                except Exception as cf_error:
                    print(f" Could not invalidate CloudFront cache: {str(cf_error)}")
                    # Don't fail if cache invalidation fails
        except Exception as invalidation_error:
            print(f" Cache invalidation skipped: {str(invalidation_error)}")
            # Don't fail if cache invalidation fails
        
        # Generate URL for the zip (handles both CloudFront and LocalStack)
        from utils.cdn_urls import get_zip_url
        zip_url = get_zip_url(gallery_id)
        
        print(f"ZIP uploaded to S3: {zip_s3_key} ({zip_size_mb:.2f} MB)")
        print(f"ZIP URL: {zip_url}")
        print(f"ZIP contains {successfully_added} photos (expected {len(valid_photos)} valid photos from DB)")
        if failed_photos:
            print(f" {len(failed_photos)} photos were skipped (missing S3 files or errors)")
        
        return {
            'success': True,
            's3_key': zip_s3_key,
            'zip_url': zip_url,
            'photo_count': successfully_added,  # Return actual count added, not DB count
            'zip_size_mb': zip_size_mb,
            'failed_count': len(failed_photos)
        }
        
    except Exception as e:
        print(f"Error generating gallery ZIP: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

