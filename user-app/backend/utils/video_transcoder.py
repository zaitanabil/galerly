"""
Enhanced Video Processing Module
HLS adaptive bitrate streaming, thumbnail generation, transcoding
"""
import subprocess
import os
import json
from pathlib import Path
from utils.video_utils import extract_video_duration


def generate_video_thumbnail(video_path, output_path, timestamp='00:00:03'):
    """
    Generate thumbnail from video at specified timestamp
    
    Args:
        video_path: Path to video file
        output_path: Path for thumbnail output
        timestamp: Timestamp to capture (format: HH:MM:SS)
        
    Returns:
        dict: {'success': bool, 'thumbnail_path': str, 'error': str}
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', timestamp,
            '-vframes', '1',
            '-vf', 'scale=1920:-1',  # Scale to 1920px wide, maintain aspect
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Generated video thumbnail: {output_path}")
            return {
                'success': True,
                'thumbnail_path': output_path
            }
        else:
            print(f"ffmpeg error: {result.stderr}")
            return {
                'success': False,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Thumbnail generation timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def transcode_to_h264(input_path, output_path, quality='high'):
    """
    Transcode video to H.264 (web-optimized)
    
    Args:
        input_path: Input video file
        output_path: Output video file
        quality: 'low', 'medium', 'high', '4k'
        
    Returns:
        dict: {'success': bool, 'output_path': str, 'error': str}
    """
    try:
        # Quality presets
        quality_settings = {
            'low': {
                'crf': 28,
                'preset': 'fast',
                'scale': '854:-2',  # 480p
                'maxrate': '1M',
                'bufsize': '2M'
            },
            'medium': {
                'crf': 23,
                'preset': 'medium',
                'scale': '1280:-2',  # 720p
                'maxrate': '2.5M',
                'bufsize': '5M'
            },
            'high': {
                'crf': 20,
                'preset': 'medium',
                'scale': '1920:-2',  # 1080p
                'maxrate': '5M',
                'bufsize': '10M'
            },
            '4k': {
                'crf': 18,
                'preset': 'slow',
                'scale': '3840:-2',  # 4K
                'maxrate': '20M',
                'bufsize': '40M'
            }
        }
        
        settings = quality_settings.get(quality, quality_settings['high'])
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', str(settings['crf']),
            '-preset', settings['preset'],
            '-vf', f"scale={settings['scale']}",
            '-maxrate', settings['maxrate'],
            '-bufsize', settings['bufsize'],
            '-movflags', '+faststart',  # Enable fast start for web streaming
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        
        print(f"Transcoding to {quality} quality...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10min timeout
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"Transcoded to H.264: {output_path} ({file_size_mb:.1f} MB)")
            return {
                'success': True,
                'output_path': output_path,
                'file_size_mb': file_size_mb
            }
        else:
            return {
                'success': False,
                'error': result.stderr
            }
            
    except Exception as e:
        print(f"Transcode error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_hls_playlist(input_path, output_dir, qualities=['720p', '1080p']):
    """
    Generate HLS adaptive bitrate playlist
    Creates m3u8 playlist + multiple quality variants
    
    Args:
        input_path: Input video file
        output_dir: Directory for HLS output
        qualities: List of quality levels to generate
        
    Returns:
        dict: {'success': bool, 'master_playlist': str, 'variants': list, 'error': str}
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # HLS quality variants
        variant_settings = {
            '360p': {
                'resolution': '640x360',
                'video_bitrate': '800k',
                'audio_bitrate': '96k'
            },
            '480p': {
                'resolution': '854x480',
                'video_bitrate': '1400k',
                'audio_bitrate': '128k'
            },
            '720p': {
                'resolution': '1280x720',
                'video_bitrate': '2800k',
                'audio_bitrate': '128k'
            },
            '1080p': {
                'resolution': '1920x1080',
                'video_bitrate': '5000k',
                'audio_bitrate': '192k'
            },
            '4k': {
                'resolution': '3840x2160',
                'video_bitrate': '15000k',
                'audio_bitrate': '192k'
            }
        }
        
        variants = []
        
        # Generate each quality variant
        for quality in qualities:
            if quality not in variant_settings:
                continue
                
            settings = variant_settings[quality]
            variant_name = f"stream_{quality}"
            variant_path = os.path.join(output_dir, variant_name)
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', f"scale={settings['resolution']}",
                '-c:v', 'libx264',
                '-b:v', settings['video_bitrate'],
                '-c:a', 'aac',
                '-b:a', settings['audio_bitrate'],
                '-hls_time', '6',  # 6 second segments
                '-hls_list_size', '0',
                '-hls_segment_filename', f"{variant_path}_%03d.ts",
                '-f', 'hls',
                f"{variant_path}.m3u8"
            ]
            
            print(f"Generating HLS variant: {quality}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                variants.append({
                    'quality': quality,
                    'playlist': f"{variant_name}.m3u8",
                    'resolution': settings['resolution'],
                    'bitrate': settings['video_bitrate']
                })
                print(f"Generated {quality} variant")
            else:
                print(f" Failed to generate {quality}: {result.stderr}")
        
        if not variants:
            return {
                'success': False,
                'error': 'No variants generated successfully'
            }
        
        # Create master playlist
        master_playlist_path = os.path.join(output_dir, 'master.m3u8')
        with open(master_playlist_path, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-VERSION:3\n\n')
            
            for variant in variants:
                bandwidth = int(variant['bitrate'].replace('k', '000'))
                resolution = variant['resolution']
                f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution}\n')
                f.write(f"{variant['playlist']}\n")
        
        print(f"Generated HLS master playlist: {master_playlist_path}")
        
        return {
            'success': True,
            'master_playlist': 'master.m3u8',
            'variants': variants,
            'output_dir': output_dir
        }
        
    except Exception as e:
        print(f"HLS generation error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def extract_video_metadata(video_path):
    """
    Extract comprehensive video metadata using ffprobe
    
    Args:
        video_path: Path to video file
        
    Returns:
        dict: Video metadata (codec, resolution, duration, bitrate, etc.)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }
        
        data = json.loads(result.stdout)
        
        # Extract video stream info
        video_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'audio'), None)
        format_info = data.get('format', {})
        
        metadata = {
            'success': True,
            'duration_seconds': float(format_info.get('duration', 0)),
            'file_size_bytes': int(format_info.get('size', 0)),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'format': format_info.get('format_name', ''),
        }
        
        if video_stream:
            metadata.update({
                'video_codec': video_stream.get('codec_name', ''),
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'aspect_ratio': video_stream.get('display_aspect_ratio', '')
            })
        
        if audio_stream:
            metadata.update({
                'audio_codec': audio_stream.get('codec_name', ''),
                'audio_sample_rate': audio_stream.get('sample_rate', ''),
                'audio_channels': audio_stream.get('channels', 0)
            })
        
        return metadata
        
    except Exception as e:
        print(f"Metadata extraction error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def optimize_video_for_web(input_path, output_dir, quality='high', generate_hls=True):
    """
    Complete video optimization pipeline:
    1. Extract metadata
    2. Generate thumbnail
    3. Transcode to H.264 (if needed)
    4. Generate HLS playlist (optional)
    
    Args:
        input_path: Input video file
        output_dir: Output directory
        quality: Video quality level
        generate_hls: Whether to generate HLS playlist
        
    Returns:
        dict: {
            'success': bool,
            'thumbnail': str,
            'optimized_video': str,
            'hls_playlist': str,
            'metadata': dict,
            'error': str
        }
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        filename = Path(input_path).stem
        results = {}
        
        # Step 1: Extract metadata
        print("Extracting video metadata...")
        metadata = extract_video_metadata(input_path)
        results['metadata'] = metadata
        
        # Step 2: Generate thumbnail
        print("Generating thumbnail...")
        thumbnail_path = os.path.join(output_dir, f"{filename}_thumb.jpg")
        thumbnail_result = generate_video_thumbnail(input_path, thumbnail_path)
        results['thumbnail'] = thumbnail_result.get('thumbnail_path') if thumbnail_result['success'] else None
        
        # Step 3: Transcode to H.264
        print(f"Transcoding to {quality} quality...")
        optimized_path = os.path.join(output_dir, f"{filename}_{quality}.mp4")
        transcode_result = transcode_to_h264(input_path, optimized_path, quality)
        results['optimized_video'] = transcode_result.get('output_path') if transcode_result['success'] else None
        
        # Step 4: Generate HLS (if requested)
        if generate_hls and transcode_result['success']:
            print("Generating HLS adaptive playlist...")
            hls_dir = os.path.join(output_dir, 'hls')
            hls_result = generate_hls_playlist(optimized_path, hls_dir, qualities=['720p', '1080p'])
            results['hls_playlist'] = os.path.join('hls', hls_result.get('master_playlist', '')) if hls_result['success'] else None
        
        results['success'] = True
        return results
        
    except Exception as e:
        print(f"Video optimization error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
