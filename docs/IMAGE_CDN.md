# Image CDN Architecture

## Overview

Galerly uses CloudFront CDN with URL-based image transformation for displaying all image formats (JPEG, PNG, HEIC, RAW) while preserving originals for download.

**Architecture Pattern: Instagram/Google Photos Method**

```
Upload → S3 (Original) → CloudFront → URL Transformation → Display
                              ↓
                         Download (Original)
```

## Image Processing Flow

### 1. Upload
- **All formats accepted**: JPEG, PNG, HEIC, DNG, CR2, NEF, ARW, RAF, ORF, RW2, PEF, TIFF
- **No client-side conversion**: Files uploaded as-is
- **Storage**: Original files stored in S3 with original filenames

### 2. Display (Transformed)
- **URL structure**: `https://cdn.galerly.com/path/image.dng?format=jpeg&width=800&height=600&fit=inside`
- **On-the-fly conversion**: CloudFront transforms images for browser display
- **Format**: All images displayed as JPEG (browser-compatible)
- **Responsive**: Multiple sizes generated (thumbnail, medium, full)

### 3. Download (Original)
- **URL structure**: `https://cdn.galerly.com/path/image.dng`
- **No transformation**: Original file downloaded
- **Full quality**: Photographers get their RAW/HEIC files unchanged

## URL Generation

### Backend (Python)
```python
# backend/utils/cdn_urls.py

def get_cdn_url(s3_key, size=None, format=None):
    """Generate CloudFront URL with optional transformation"""
    base_url = f"https://cdn.galerly.com/{s3_key}"
    if size or format:
        params = []
        if size:
            params.append(f"width={size[0]}&height={size[1]}&fit=inside")
        if format:
            params.append(f"format={format}")
        return f"{base_url}?{'&'.join(params)}"
    return base_url

def get_photo_urls(s3_key):
    """Generate all URL variants for a photo"""
    return {
        'url': get_cdn_url(s3_key),  # Original for download
        'thumbnail_url': get_cdn_url(s3_key, size=(800,600), format='jpeg'),
        'medium_url': get_cdn_url(s3_key, size=(2000,2000), format='jpeg'),
        'small_thumb_url': get_cdn_url(s3_key, size=(400,400), format='jpeg')
    }
```

### Frontend (JavaScript)
```javascript
// frontend/js/config.js

const CDN_URL = 'https://cdn.galerly.com';

function getImageUrl(path) {
    if (!path) return '';
    if (path.startsWith('http')) {
        // Convert old S3 URLs to CloudFront
        return path.replace(/.*\.s3\.amazonaws\.com/, CDN_URL);
    }
    return `${CDN_URL}/${path}`;
}
```

## Image Format Support

| Format | Upload | Store | Display | Download | Notes |
|--------|--------|-------|---------|----------|-------|
| JPEG   | ✅ | Original | JPEG | Original | Direct display |
| PNG    | ✅ | Original | JPEG | Original | Converted for display |
| HEIC   | ✅ | Original | JPEG | Original | iPhone photos |
| DNG    | ✅ | Original | JPEG | Original | Adobe RAW |
| CR2/CR3| ✅ | Original | JPEG | Original | Canon RAW |
| NEF    | ✅ | Original | JPEG | Original | Nikon RAW |
| ARW    | ✅ | Original | JPEG | Original | Sony RAW |
| RAF    | ✅ | Original | JPEG | Original | Fuji RAW |
| ORF    | ✅ | Original | JPEG | Original | Olympus RAW |
| RW2    | ✅ | Original | JPEG | Original | Panasonic RAW |
| PEF    | ✅ | Original | JPEG | Original | Pentax RAW |
| TIFF   | ✅ | Original | JPEG | Original | Large format |

## CloudFront Configuration

### Distribution Setup
```yaml
Origin: galerly-photos.s3.amazonaws.com
Domain: cdn.galerly.com
OAI: Enabled (secure S3 access)
CORS: Enabled (AWS Managed Policy)
Cache: Enabled for transformed images
```

### Response Headers Policy
```json
{
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, HEAD",
  "Access-Control-Allow-Headers": "*",
  "Access-Control-Max-Age": "3600"
}
```

### Cache Behavior
- **Original files**: Short TTL (1 hour) - rarely change
- **Transformed images**: Long TTL (1 year) - immutable
- **Invalidation**: Automatic on deployment

## Lambda Layer Architecture

### Image Processing Layer (~34MB)
- **Pillow**: Image manipulation
- **rawpy**: RAW format support (DNG, CR2, NEF, etc.)
- **pillow-heif**: HEIC/HEIF support (iPhone photos)
- **numpy**: Required by rawpy

### Deployment
```bash
# Layer published via GitHub Actions
Layer: galerly-image-processing
Runtime: python3.11, python3.12
Size: ~34MB
```

## Performance

### Optimizations
- **Client-side validation only**: No heavy processing on upload
- **CloudFront edge caching**: Fast global delivery
- **Responsive images**: Multiple sizes for different devices
- **Lazy loading**: Images load on-demand

### Speed Metrics
- **Thumbnail load**: < 500ms
- **Full image load**: < 2s (typical)
- **Download**: Direct S3 → CloudFront (fast)

## Cost Optimization

### Storage
- **One copy per image**: Only original stored
- **No duplicates**: Transformations on-the-fly
- **S3 lifecycle**: Possible future optimization

### Bandwidth
- **CloudFront caching**: Reduces S3 data transfer
- **Smart sizing**: Only load what's needed
- **Progressive JPEG**: Faster perceived load

## Security

### Access Control
- **S3**: Private bucket, OAI only
- **CloudFront**: Public access via CDN
- **Presigned URLs**: Not needed (CloudFront handles auth)

### Image Security
- **Malware scanning**: On upload
- **Metadata stripping**: EXIF removed for privacy
- **Format validation**: File type verification

## Testing

### Automated Tests
```bash
# Run image transformation tests
cd backend
pytest tests/test_image_transformation.py -v
```

### Manual Testing
```bash
# Test URL generation
python3 -c "
from backend.utils.cdn_urls import get_photo_urls
urls = get_photo_urls('gallery/photo.dng')
print('Original:', urls['url'])
print('Display:', urls['thumbnail_url'])
"
```

## Troubleshooting

### Images Not Loading
1. **Check CloudFront distribution status**: Must be "Deployed"
2. **Verify OAI configuration**: CloudFront → Origin → OAI enabled
3. **Check CORS headers**: Response Headers Policy attached
4. **Clear browser cache**: Hard refresh (Cmd+Shift+R)
5. **Invalidate CloudFront cache**: Via deploy.yml or AWS console

### RAW Files Show Placeholder
- **Expected behavior**: If CloudFront transformation not yet deployed
- **Fallback**: Smart placeholder with "RAW Format" message
- **Download works**: Original file always available

### Slow Loading
1. **Check CloudFront edge location**: Use closest region
2. **Verify cache hit rate**: CloudWatch metrics
3. **Optimize image sizes**: Use appropriate width/height params
4. **Enable lazy loading**: Already implemented in gallery

## Future Enhancements

### Planned (Not Yet Deployed)
- **Lambda@Edge transformation**: On-the-fly format conversion
- **WebP format support**: Better compression
- **AVIF format support**: Next-gen format
- **Smart cropping**: AI-based focal point detection

### Under Consideration
- **Video support**: MP4, MOV, AVI
- **GIF optimization**: Compressed animations
- **Image compression**: Lossy/lossless options

