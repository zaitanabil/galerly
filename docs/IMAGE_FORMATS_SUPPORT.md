# Image Format Support - Galerly

## Overview

Galerly supports ALL professional photography formats, including standard web formats, Apple HEIC, and RAW formats from all major camera manufacturers.

## Supported Formats

### Standard Web Formats
- **JPEG** (`.jpg`, `.jpeg`) - Universal standard
- **PNG** (`.png`) - Lossless with transparency
- **WEBP** (`.webp`) - Modern web format
- **GIF** (`.gif`) - Animated images
- **TIFF** (`.tif`, `.tiff`) - Uncompressed professional format

### Apple Formats
- **HEIC** (`.heic`) - iPhone/iPad default format
- **HEIF** (`.heif`) - High Efficiency Image Format

### RAW Formats by Manufacturer

#### Canon
- `.cr2` - Canon Raw 2
- `.cr3` - Canon Raw 3 (newer cameras)

#### Nikon
- `.nef` - Nikon Electronic Format

#### Sony
- `.arw` - Sony Alpha Raw

#### Adobe
- `.dng` - Digital Negative (universal RAW format)

#### Fujifilm
- `.raf` - Fuji Raw

#### Olympus
- `.orf` - Olympus Raw Format

#### Panasonic
- `.rw2` - Panasonic Raw 2

#### Pentax
- `.pef` - Pentax Electronic File

#### Hasselblad
- `.3fr` - Hasselblad 3F Raw

## Security Validation

All uploaded images go through security validation:

1. **Extension Check** - Validates file extension against whitelist
2. **Magic Bytes Check** - Verifies actual file format matches extension
3. **Deep Validation** - Parses image structure to detect malicious content
4. **RAW Validation** - Special handling for RAW formats using rawpy library

## Size Limits

**NO SIZE OR DIMENSION LIMITS** - Photographers need flexibility for:
- Large RAW files (50-100MB+)
- High-resolution panoramas
- Professional quality images

## Dependencies

### Required (Already Installed)
- `Pillow>=10.0.0` - Core image processing

### Optional (Auto-detected)
- `pillow-heif>=0.13.0` - Enables HEIC/HEIF support
- `rawpy>=0.18.0` - Enables RAW format support
- `imagecodecs>=2023.1.23` - Additional codec support

## Installation

### Full Support (All Formats)
```bash
cd backend
pip install -r requirements.txt
```

This installs all dependencies including HEIC and RAW support.

### Minimal Support (Web Formats Only)
```bash
pip install Pillow>=10.0.0
```

This provides support for JPEG, PNG, WEBP, GIF only.

## Format Detection

The system automatically detects:
- **Standard formats** - Validated with PIL
- **HEIC formats** - Validated with pillow-heif (if installed)
- **RAW formats** - Validated with rawpy (if installed)

If optional libraries are not installed, those formats will either:
- Show a warning (RAW formats - basic validation only)
- Fail with helpful error message (HEIC formats)

## Usage in Code

```python
from utils.image_security import validate_image_data, sanitize_image

# Validate any format
result = validate_image_data(image_bytes, filename='photo.cr2')
# Returns: {
#   'valid': True,
#   'format': 'RAW',
#   'mode': 'RAW',
#   'size': (6000, 4000),
#   'file_size': 25000000,
#   'raw_format': True
# }

# Sanitize/convert to web format
sanitized = sanitize_image(image_bytes, output_format='JPEG', quality=95, filename='photo.cr2')
# Returns: JPEG bytes (RAW converted to JPEG)
```

## RAW File Handling

RAW files are:
1. **Validated** on upload (extension + rawpy validation if available)
2. **Stored** in original RAW format in S3
3. **Converted** to JPEG for web display when needed
4. **Preserved** in original quality for download

## HEIC File Handling

HEIC files are:
1. **Validated** on upload (requires pillow-heif)
2. **Stored** in original HEIC format in S3
3. **Can be converted** to JPEG for older browser compatibility
4. **Preserved** in original format for download

## Browser Compatibility

| Format | Upload | Display | Download |
|--------|--------|---------|----------|
| JPEG | ✅ | ✅ | ✅ |
| PNG | ✅ | ✅ | ✅ |
| WEBP | ✅ | ✅ | ✅ |
| GIF | ✅ | ✅ | ✅ |
| HEIC | ✅ | ⚠️ Convert | ✅ |
| RAW | ✅ | ❌ Convert | ✅ |
| TIFF | ✅ | ⚠️ Limited | ✅ |

Legend:
- ✅ Native support
- ⚠️ Requires conversion for display
- ❌ Must convert (no browser support)

## Security Features

1. **No Executable Extensions** - Only image formats allowed
2. **Magic Byte Validation** - Prevents fake extensions
3. **Deep Parsing** - Detects malicious embedded content
4. **Metadata Stripping** - Removes EXIF/metadata during sanitization
5. **Re-encoding** - Creates clean copy without hidden data

## Performance Notes

- **Standard formats** (JPEG, PNG) - Very fast validation
- **HEIC formats** - Fast validation (with pillow-heif)
- **RAW formats** - Slower validation (large files, complex parsing)
- **Sanitization** - Moderate speed (re-encoding required)

## Troubleshooting

### HEIC Files Not Working
```bash
pip install pillow-heif
```

### RAW Files Not Working
```bash
pip install rawpy
```

### "Invalid format" Error
Check that:
1. File extension matches actual file format
2. File is not corrupted
3. Required libraries are installed

## Testing

Run tests:
```bash
cd backend
pytest tests/test_image_security.py -v
```

Tests will show which format support is enabled.

