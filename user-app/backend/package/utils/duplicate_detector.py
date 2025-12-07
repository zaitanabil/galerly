"""
Duplicate photo detection utility
Detects duplicate photos by filename and file size
"""
import hashlib

def calculate_file_hash(image_data):
    """
    Calculate SHA-256 hash of the file content
    This detects exact duplicates (same file)
    """
    return hashlib.sha256(image_data).hexdigest()

def get_file_size(image_data):
    """
    Get the size of the image file in bytes
    """
    return len(image_data)

def normalize_filename(filename):
    """
    Normalize filename for comparison
    - Remove extension
    - Convert to lowercase
    - Strip whitespace
    """
    if not filename:
        return ""
    
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Normalize: lowercase, strip whitespace
    return name_without_ext.lower().strip()

def check_for_duplicates_in_gallery(image_data, existing_photos, filename_from_client=""):
    """
    Check if the uploaded image is a duplicate of any existing photo in gallery
    Considers a photo duplicate if:
    1. Same file hash (exact duplicate), OR
    2. Same filename AND same file size (likely same photo)
    
    Args:
        image_data: Bytes of the new image
        existing_photos: List of existing photo records
        filename_from_client: Original filename from upload
    
    Returns:
        dict with file info and list of duplicate matches
    """
    # Calculate hashes and size for new image
    new_file_hash = calculate_file_hash(image_data)
    new_file_size = get_file_size(image_data)
    new_filename_normalized = normalize_filename(filename_from_client)
    
    print(f"🔍 Checking duplicates for: {filename_from_client}")
    print(f"   File size: {new_file_size} bytes")
    print(f"   File hash: {new_file_hash[:16]}...")
    print(f"   Normalized name: {new_filename_normalized}")
    
    duplicates = []
    
    for photo in existing_photos:
        existing_filename = photo.get('filename', '')
        existing_file_hash = photo.get('file_hash', '')
        existing_file_size = photo.get('file_size', 0)
        existing_filename_normalized = normalize_filename(existing_filename)
        
        # Check 1: Exact file match (same hash)
        if existing_file_hash and existing_file_hash == new_file_hash:
            duplicates.append({
                'photo_id': photo['id'],
                'photo_url': photo.get('url', ''),
                'thumbnail_url': photo.get('thumbnail_url', ''),
                'filename': existing_filename,
                'match_type': 'exact_file',
                'match_reason': 'Same file hash (identical file)',
                'file_size': existing_file_size,
                'similarity_score': 100.0
            })
            print(f"   ✅ Exact file match: {existing_filename}")
            continue
        
        # Check 2: Same filename AND same size
        if (new_filename_normalized and 
            existing_filename_normalized and 
            new_filename_normalized == existing_filename_normalized and 
            new_file_size == existing_file_size):
            
            duplicates.append({
                'photo_id': photo['id'],
                'photo_url': photo.get('url', ''),
                'thumbnail_url': photo.get('thumbnail_url', ''),
                'filename': existing_filename,
                'match_type': 'filename_size_match',
                'match_reason': f'Same filename and size ({new_file_size} bytes)',
                'file_size': existing_file_size,
                'similarity_score': 95.0
            })
            print(f"   ⚠️  Filename+Size match: {existing_filename}")
    
    # Sort by similarity score (highest first)
    duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    print(f"   📊 Found {len(duplicates)} duplicate(s)")
    
    return {
        'file_hash': new_file_hash,
        'file_size': new_file_size,
        'filename': filename_from_client,
        'duplicates': duplicates
    }

