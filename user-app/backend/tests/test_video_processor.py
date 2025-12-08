"""
Tests for Video Processing Module
Tests video thumbnail generation and metadata extraction
"""
import pytest
import os
import io
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from utils.video_processor import (
    is_video_file,
    extract_video_metadata,
    generate_video_thumbnail,
    process_video_upload_async
)


class TestVideoFileDetection:
    """Test video file type detection"""
    
    def test_video_extensions(self):
        """Test that common video extensions are detected"""
        assert is_video_file('video.mp4') == True
        assert is_video_file('VIDEO.MOV') == True
        assert is_video_file('file.avi') == True
        assert is_video_file('clip.mkv') == True
        assert is_video_file('movie.m4v') == True
        assert is_video_file('web.webm') == True
    
    def test_non_video_extensions(self):
        """Test that non-video files are not detected as videos"""
        assert is_video_file('image.jpg') == False
        assert is_video_file('photo.png') == False
        assert is_video_file('raw.cr2') == False
        assert is_video_file('document.pdf') == False
    
    def test_no_extension(self):
        """Test files with no extension"""
        assert is_video_file('filename') == False


class TestVideoMetadataExtraction:
    """Test video metadata extraction using ffprobe"""
    
    @patch('subprocess.run')
    def test_extract_video_metadata_success(self, mock_run):
        """Test successful video metadata extraction"""
        # Mock ffprobe output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "format": {
                "duration": "45.5",
                "bit_rate": "5000000",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "profile": "High",
                    "level": 40
                }
            ]
        }
        '''
        mock_run.return_value = mock_result
        
        # Create dummy video data
        video_data = b'fake video data'
        
        metadata = extract_video_metadata(video_data, 'test_video.mp4')
        
        # Verify metadata structure
        assert metadata['type'] == 'video'
        assert metadata['format'] == 'video'
        assert metadata['duration_seconds'] == 45.5
        assert metadata['duration_minutes'] == pytest.approx(0.76, rel=0.01)
        assert metadata['dimensions']['width'] == 1920
        assert metadata['dimensions']['height'] == 1080
        assert metadata['codec']['video_codec'] == 'h264'
    
    @patch('subprocess.run')
    def test_extract_video_metadata_ffprobe_failure(self, mock_run):
        """Test handling of ffprobe failure"""
        # Mock ffprobe error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_run.return_value = mock_result
        
        video_data = b'fake video data'
        
        metadata = extract_video_metadata(video_data, 'bad_video.mp4')
        
        # Should return basic metadata even on failure
        assert metadata['type'] == 'video'
        assert metadata['format'] == 'video'
        assert metadata['duration_seconds'] is None
    
    @patch('subprocess.run')
    def test_extract_video_metadata_timeout(self, mock_run):
        """Test handling of ffprobe timeout"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 60)
        
        video_data = b'fake video data'
        
        metadata = extract_video_metadata(video_data, 'large_video.mp4')
        
        # Should return basic metadata on timeout
        assert metadata['type'] == 'video'
        assert metadata['duration_seconds'] is None


class TestVideoThumbnailGeneration:
    """Test video thumbnail generation using ffmpeg"""
    
    @patch('utils.video_processor.s3_client')
    @patch('subprocess.run')
    @patch('PIL.Image.open')
    def test_generate_video_thumbnail_success(self, mock_image_open, mock_run, mock_s3):
        """Test successful thumbnail generation from video"""
        # Mock ffmpeg success
        mock_ffmpeg = Mock()
        mock_ffmpeg.returncode = 0
        mock_run.return_value = mock_ffmpeg
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_img.mode = 'RGB'
        mock_img.copy.return_value = mock_img
        mock_image_open.return_value = mock_img
        
        # Mock thumbnail save
        mock_img.save = Mock()
        
        video_data = b'fake video data'
        s3_key = 'gallery123/video456_test.mp4'
        
        result = generate_video_thumbnail(s3_key, video_data=video_data, bucket='test-bucket')
        
        # Verify success
        assert result['success'] == True
        assert 'renditions' in result
        assert 'thumbnail' in result['renditions']
        assert 'small' in result['renditions']
        assert 'medium' in result['renditions']
        
        # Verify S3 uploads happened
        assert mock_s3.put_object.call_count == 3  # thumbnail, small, medium
    
    @patch('subprocess.run')
    def test_generate_video_thumbnail_ffmpeg_failure(self, mock_run):
        """Test handling of ffmpeg failure"""
        # Mock ffmpeg failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = 'Invalid video format'
        mock_run.return_value = mock_result
        
        video_data = b'fake video data'
        s3_key = 'gallery123/video456_bad.mp4'
        
        result = generate_video_thumbnail(s3_key, video_data=video_data, bucket='test-bucket')
        
        # Should return error
        assert result['success'] == False
        assert 'error' in result
    
    @patch('subprocess.run')
    def test_generate_video_thumbnail_timeout(self, mock_run):
        """Test handling of ffmpeg timeout"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 60)
        
        video_data = b'fake video data'
        s3_key = 'gallery123/video456_large.mp4'
        
        result = generate_video_thumbnail(s3_key, video_data=video_data, bucket='test-bucket')
        
        # Should return error
        assert result['success'] == False
        assert 'timeout' in result['error'].lower()


class TestVideoProcessingPipeline:
    """Test complete video processing pipeline"""
    
    @patch('utils.video_processor.generate_video_thumbnail')
    def test_process_video_upload_async(self, mock_generate_thumbnail):
        """Test async video processing wrapper"""
        # Mock thumbnail generation
        mock_generate_thumbnail.return_value = {
            'success': True,
            'renditions': {
                'thumbnail': {'key': 'renditions/gallery/video_thumbnail.jpg', 'size': 50000},
                'small': {'key': 'renditions/gallery/video_small.jpg', 'size': 100000},
                'medium': {'key': 'renditions/gallery/video_medium.jpg', 'size': 200000}
            },
            'total_renditions_size': 350000
        }
        
        s3_key = 'gallery123/video456_test.mp4'
        video_data = b'fake video data'
        
        result = process_video_upload_async(s3_key, 'test-bucket', video_data=video_data)
        
        # Verify result
        assert result['success'] == True
        assert len(result['renditions']) == 3
        assert result['total_renditions_size'] == 350000
        
        # Verify function was called correctly
        mock_generate_thumbnail.assert_called_once_with(s3_key, video_data, 'test-bucket')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
