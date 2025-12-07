"""
Tests for RAW photo processing
"""
import pytest
import os
import io
from PIL import Image

# Import RAW processor functions
from utils.raw_processor import (
    is_raw_file,
    get_raw_format_name,
    RAW_EXTENSIONS
)

try:
    import rawpy
    RAW_SUPPORT_AVAILABLE = True
except ImportError:
    RAW_SUPPORT_AVAILABLE = False


class TestRawFileDetection:
    """Test RAW file detection"""
    
    def test_is_raw_file_cr2(self):
        """Test Canon CR2 detection"""
        assert is_raw_file('photo.cr2') == True
        assert is_raw_file('photo.CR2') == True
        assert is_raw_file('PHOTO.CR2') == True
    
    def test_is_raw_file_nef(self):
        """Test Nikon NEF detection"""
        assert is_raw_file('photo.nef') == True
        assert is_raw_file('photo.NEF') == True
    
    def test_is_raw_file_arw(self):
        """Test Sony ARW detection"""
        assert is_raw_file('photo.arw') == True
        assert is_raw_file('photo.ARW') == True
    
    def test_is_raw_file_dng(self):
        """Test Adobe DNG detection"""
        assert is_raw_file('photo.dng') == True
        assert is_raw_file('photo.DNG') == True
    
    def test_is_not_raw_file(self):
        """Test non-RAW files"""
        assert is_raw_file('photo.jpg') == False
        assert is_raw_file('photo.jpeg') == False
        assert is_raw_file('photo.png') == False
        assert is_raw_file('photo.gif') == False
        assert is_raw_file('photo.heic') == False
    
    def test_get_raw_format_name(self):
        """Test format name retrieval"""
        assert get_raw_format_name('photo.cr2') == 'Canon RAW'
        assert get_raw_format_name('photo.nef') == 'Nikon RAW'
        assert get_raw_format_name('photo.arw') == 'Sony RAW'
        assert get_raw_format_name('photo.dng') == 'Adobe DNG'
        assert get_raw_format_name('photo.jpg') is None
    
    def test_all_raw_extensions_covered(self):
        """Test that all RAW extensions have names"""
        for ext, name in RAW_EXTENSIONS.items():
            assert isinstance(ext, str)
            assert ext.startswith('.')
            assert isinstance(name, str)
            assert len(name) > 0


class TestRawPreviewGeneration:
    """Test RAW preview generation (requires rawpy)"""
    
    @pytest.mark.skipif(not RAW_SUPPORT_AVAILABLE, reason="rawpy not installed")
    def test_generate_preview_sizes(self):
        """Test different preview sizes"""
        # This test would require actual RAW file data
        # In production, we'd use test RAW files
        pass
    
    @pytest.mark.skipif(not RAW_SUPPORT_AVAILABLE, reason="rawpy not installed")
    def test_extract_metadata(self):
        """Test metadata extraction"""
        # This test would require actual RAW file data
        pass


class TestRawValidation:
    """Test RAW file validation"""
    
    def test_raw_support_status(self):
        """Test RAW support availability"""
        if RAW_SUPPORT_AVAILABLE:
            import rawpy
            assert rawpy is not None
        else:
            print("⚠️ RAW support not available - rawpy not installed")


class TestRawIntegration:
    """Test RAW photo integration with photo handler"""
    
    def test_raw_file_rejected_on_free_plan(self):
        """Test that RAW files are rejected for users without raw_support feature"""
        # This would be tested in photo_handler tests
        pass
    
    def test_raw_file_accepted_on_pro_plan(self):
        """Test that RAW files are accepted for Pro/Ultimate users"""
        # This would be tested in photo_handler tests
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
