"""
Test image security utilities
"""
import pytest
from utils.image_security import (
    validate_image_data, sanitize_image, ImageSecurityError, 
    ALLOWED_MIME_TYPES, ALLOWED_EXTENSIONS, is_raw_format,
    HEIF_SUPPORTED, RAW_SUPPORTED
)


class TestImageSecurity:
    """Test image security validation and sanitization"""
    
    def test_validate_image_invalid_format(self):
        """Test that invalid image formats are rejected"""
        # Not a valid image
        with pytest.raises(ImageSecurityError):
            validate_image_data(b"not-valid-image-data", "image.jpg")
    
    def test_validate_image_empty(self):
        """Test that empty images are rejected"""
        with pytest.raises(ImageSecurityError) as exc_info:
            validate_image_data(b"", "image.jpg")
        assert "empty" in str(exc_info.value).lower()
    
    def test_validate_image_none(self):
        """Test that None is rejected"""
        with pytest.raises((ImageSecurityError, TypeError)):
            validate_image_data(None, "image.jpg")
    
    def test_validate_image_wrong_type(self):
        """Test that non-bytes inputs are rejected"""
        with pytest.raises((ImageSecurityError, TypeError)):
            validate_image_data(12345, "image.jpg")
    
    def test_validate_image_checks_magic_bytes(self):
        """Test that magic bytes are validated"""
        # Create a fake "image" with wrong magic bytes
        fake_data = b"FAKE_IMAGE_DATA_WITH_NO_REAL_HEADER"
        
        with pytest.raises(ImageSecurityError) as exc_info:
            validate_image_data(fake_data, "image.jpg")
        
        assert "invalid" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
    
    def test_sanitize_image_invalid_input(self):
        """Test that sanitize_image rejects invalid inputs"""
        with pytest.raises(ImageSecurityError):
            sanitize_image(b"")
    
    def test_sanitize_image_non_bytes(self):
        """Test that sanitize_image requires bytes input"""
        with pytest.raises((ImageSecurityError, TypeError, AttributeError)):
            sanitize_image("not bytes")


class TestAllowedFileTypes:
    """Test allowed file types configuration"""
    
    def test_allowed_mime_types_defined(self):
        """Test that allowed MIME types are defined"""
        assert isinstance(ALLOWED_MIME_TYPES, dict)
        assert len(ALLOWED_MIME_TYPES) > 0
    
    def test_allowed_extensions_defined(self):
        """Test that allowed extensions are defined"""
        assert isinstance(ALLOWED_EXTENSIONS, list)
        assert len(ALLOWED_EXTENSIONS) > 0
    
    def test_no_executable_extensions(self):
        """Test that no executable extensions are allowed"""
        dangerous_extensions = {'.exe', '.bat', '.sh', '.cmd', '.com', '.scr', '.js', '.vbs'}
        for ext in ALLOWED_EXTENSIONS:
            assert ext.lower() not in dangerous_extensions, f"Dangerous extension {ext} is allowed"
    
    def test_professional_formats_supported(self):
        """Test that professional photography formats are supported"""
        # Standard web formats
        assert '.jpg' in ALLOWED_EXTENSIONS
        assert '.jpeg' in ALLOWED_EXTENSIONS
        assert '.png' in ALLOWED_EXTENSIONS
        assert '.webp' in ALLOWED_EXTENSIONS
        assert '.gif' in ALLOWED_EXTENSIONS
        
        # Apple formats
        assert '.heic' in ALLOWED_EXTENSIONS
        assert '.heif' in ALLOWED_EXTENSIONS
        
        # RAW formats
        assert '.cr2' in ALLOWED_EXTENSIONS  # Canon
        assert '.cr3' in ALLOWED_EXTENSIONS  # Canon (newer)
        assert '.nef' in ALLOWED_EXTENSIONS  # Nikon
        assert '.arw' in ALLOWED_EXTENSIONS  # Sony
        assert '.dng' in ALLOWED_EXTENSIONS  # Adobe Digital Negative
        assert '.raf' in ALLOWED_EXTENSIONS  # Fujifilm
        assert '.orf' in ALLOWED_EXTENSIONS  # Olympus
        assert '.rw2' in ALLOWED_EXTENSIONS  # Panasonic
        assert '.pef' in ALLOWED_EXTENSIONS  # Pentax
        assert '.3fr' in ALLOWED_EXTENSIONS  # Hasselblad
        
        # TIFF
        assert '.tif' in ALLOWED_EXTENSIONS
        assert '.tiff' in ALLOWED_EXTENSIONS
    
    def test_is_raw_format_detection(self):
        """Test RAW format detection"""
        assert is_raw_format('IMG_1234.CR2') == True
        assert is_raw_format('photo.nef') == True
        assert is_raw_format('image.arw') == True
        assert is_raw_format('test.dng') == True
        
        # Not RAW formats
        assert is_raw_format('photo.jpg') == False
        assert is_raw_format('image.png') == False
        assert is_raw_format('test.heic') == False
    
    def test_heif_support_status(self):
        """Test HEIF/HEIC support status is defined"""
        assert isinstance(HEIF_SUPPORTED, bool)
        if HEIF_SUPPORTED:
            print("✅ HEIF/HEIC support is enabled (pillow-heif installed)")
        else:
            print("⚠️  HEIF/HEIC support is disabled (pillow-heif not installed)")
    
    def test_raw_support_status(self):
        """Test RAW support status is defined"""
        assert isinstance(RAW_SUPPORTED, bool)
        if RAW_SUPPORTED:
            print("✅ RAW support is enabled (rawpy installed)")
        else:
            print("⚠️  RAW support is disabled (rawpy not installed)")


