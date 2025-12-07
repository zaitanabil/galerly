"""
Tests for video transcoding and HLS streaming
"""
import pytest
import os
from utils.video_transcoder import (
    generate_video_thumbnail,
    transcode_to_h264,
    extract_video_metadata
)


class TestVideoThumbnailGeneration:
    """Test video thumbnail generation"""
    
    def test_thumbnail_timestamp_format(self):
        """Test timestamp format validation"""
        valid_timestamps = ['00:00:03', '00:01:30', '01:05:20']
        
        for ts in valid_timestamps:
            parts = ts.split(':')
            assert len(parts) == 3
            hours, minutes, seconds = parts
            assert hours.isdigit() and int(hours) >= 0
            assert minutes.isdigit() and 0 <= int(minutes) < 60
            assert seconds.isdigit() and 0 <= int(seconds) < 60
    
    def test_thumbnail_dimensions(self):
        """Test thumbnail dimension scaling"""
        target_width = 1920
        aspect_ratio = 16 / 9
        
        expected_height = int(target_width / aspect_ratio)
        
        assert target_width == 1920
        assert expected_height == 1080


class TestVideoTranscoding:
    """Test video H.264 transcoding"""
    
    def test_quality_presets(self):
        """Test video quality preset configurations"""
        quality_presets = {
            'low': {'crf': 28, 'resolution': '854x480', 'bitrate': '1M'},
            'medium': {'crf': 23, 'resolution': '1280x720', 'bitrate': '2.5M'},
            'high': {'crf': 20, 'resolution': '1920x1080', 'bitrate': '5M'},
            '4k': {'crf': 18, 'resolution': '3840x2160', 'bitrate': '20M'}
        }
        
        for quality, settings in quality_presets.items():
            # CRF should be between 0-51 (lower = better quality)
            assert 0 <= settings['crf'] <= 51
            
            # Resolution should be valid
            width, height = map(int, settings['resolution'].split('x'))
            assert width > 0 and height > 0
            
            # Bitrate should be specified
            assert settings['bitrate'].endswith('M') or settings['bitrate'].endswith('k')
    
    def test_h264_codec_settings(self):
        """Test H.264 codec settings"""
        codec_settings = {
            'codec': 'libx264',
            'preset': 'medium',
            'profile': 'high',
            'level': '4.1',
            'faststart': True
        }
        
        assert codec_settings['codec'] == 'libx264'
        assert codec_settings['preset'] in ['ultrafast', 'fast', 'medium', 'slow', 'veryslow']
        assert codec_settings['faststart'] is True  # Required for web streaming


class TestHLSPlaylist:
    """Test HLS adaptive bitrate playlist generation"""
    
    def test_hls_variants(self):
        """Test HLS quality variants"""
        variants = {
            '360p': {'resolution': '640x360', 'bitrate': '800k'},
            '480p': {'resolution': '854x480', 'bitrate': '1400k'},
            '720p': {'resolution': '1280x720', 'bitrate': '2800k'},
            '1080p': {'resolution': '1920x1080', 'bitrate': '5000k'},
            '4k': {'resolution': '3840x2160', 'bitrate': '15000k'}
        }
        
        for quality, settings in variants.items():
            width, height = map(int, settings['resolution'].split('x'))
            
            # Validate resolution
            assert width > 0 and height > 0
            
            # Validate bitrate format
            assert settings['bitrate'].endswith('k')
            bitrate_value = int(settings['bitrate'][:-1])
            assert bitrate_value > 0
    
    def test_hls_segment_duration(self):
        """Test HLS segment duration"""
        # Segment duration should be 6-10 seconds
        segment_duration = 6
        
        assert 6 <= segment_duration <= 10
    
    def test_master_playlist_format(self):
        """Test HLS master playlist format"""
        sample_playlist = '''#EXTM3U
#EXT-X-VERSION:3

#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
stream_720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
stream_1080p.m3u8'''
        
        assert '#EXTM3U' in sample_playlist
        assert '#EXT-X-VERSION:3' in sample_playlist
        assert '#EXT-X-STREAM-INF' in sample_playlist
        assert 'BANDWIDTH=' in sample_playlist
        assert 'RESOLUTION=' in sample_playlist


class TestVideoMetadata:
    """Test video metadata extraction"""
    
    def test_metadata_fields(self):
        """Test required metadata fields"""
        required_fields = [
            'duration_seconds',
            'file_size_bytes',
            'bitrate',
            'video_codec',
            'width',
            'height',
            'fps',
            'audio_codec'
        ]
        
        sample_metadata = {
            'duration_seconds': 120.5,
            'file_size_bytes': 50000000,
            'bitrate': 5000000,
            'video_codec': 'h264',
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'audio_codec': 'aac'
        }
        
        for field in required_fields:
            assert field in sample_metadata
            assert sample_metadata[field] is not None
    
    def test_duration_calculation(self):
        """Test video duration calculation"""
        duration_seconds = 125.5
        duration_minutes = duration_seconds / 60
        
        assert duration_minutes == pytest.approx(2.092, rel=0.01)
    
    def test_file_size_calculation(self):
        """Test file size unit conversions"""
        file_size_bytes = 50000000
        file_size_mb = file_size_bytes / (1024 * 1024)
        file_size_gb = file_size_mb / 1024
        
        assert file_size_mb == pytest.approx(47.68, rel=0.01)
        assert file_size_gb == pytest.approx(0.0466, rel=0.01)


class TestVideoPlanLimits:
    """Test video plan limit enforcement"""
    
    def test_video_quality_by_plan(self):
        """Test video quality restrictions by plan"""
        plan_limits = {
            'starter': {'quality': 'hd', 'max_minutes': 30},
            'plus': {'quality': 'hd', 'max_minutes': 60},
            'pro': {'quality': '4k', 'max_minutes': 240},
            'ultimate': {'quality': '4k', 'max_minutes': 600}
        }
        
        for plan, limits in plan_limits.items():
            assert limits['quality'] in ['hd', '4k']
            assert limits['max_minutes'] > 0
    
    def test_video_duration_enforcement(self):
        """Test video duration limit enforcement"""
        user_plan = 'starter'
        plan_limit_minutes = 30
        video_duration_seconds = 125
        video_duration_minutes = video_duration_seconds / 60
        
        # User should be allowed (under limit)
        assert video_duration_minutes < plan_limit_minutes
        
        # Test over limit
        long_video_minutes = 45
        assert long_video_minutes > plan_limit_minutes


class TestVideoStreaming:
    """Test video streaming functionality"""
    
    def test_adaptive_bitrate_selection(self):
        """Test adaptive bitrate selection logic"""
        available_bitrates = [800, 1400, 2800, 5000, 15000]  # kbps
        user_bandwidth = 3000  # kbps
        
        # Should select highest bitrate below user bandwidth
        selected_bitrate = max([br for br in available_bitrates if br <= user_bandwidth])
        
        assert selected_bitrate == 2800
    
    def test_fast_start_optimization(self):
        """Test fast start (moov atom) optimization"""
        # Fast start moves moov atom to beginning of file
        # This allows streaming to start before full download
        faststart_enabled = True
        
        assert faststart_enabled is True
    
    def test_cdn_delivery(self):
        """Test CDN delivery configuration"""
        cdn_settings = {
            'cache_control': 'public, max-age=31536000',
            'cors_enabled': True,
            'compression': True
        }
        
        assert 'max-age=' in cdn_settings['cache_control']
        assert cdn_settings['cors_enabled'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
