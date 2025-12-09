"""
Video Processing Module
Extracts video metadata and generates thumbnail using ffmpeg
Separate from image processing to handle video-specific requirements
"""
import os
import io
import subprocess
import json
import tempfile
from PIL import Image
from decimal import Decimal
from datetime import datetime, timezone

from utils.config import s3_client, S3_BUCKET, S3_RENDITIONS_BUCKET


def is_video_file(filename):
    """
    Check if file is a video based on extension
    
    Args:
        filename: File name with extension
    
    Returns:
        bool: True if video file
    """
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm', '.mpeg', '.mpg']
    ext = os.path.splitext(filename)[1].lower()
    return ext in video_extensions


def extract_video_metadata(video_data, filename):
    """
    Extract comprehensive metadata from video file using ffprobe
    
    Args:
        video_data: Raw video bytes
        filename: Original filename
    
    Returns:
        dict: Video metadata including duration, dimensions, codec, bitrate
    """
    metadata = {
        'filename': filename,
        'file_size': len(video_data),
        'size_mb': round(len(video_data) / (1024 * 1024), 2),
        'upload_timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
        'format': 'video',
        'type': 'video',
        'dimensions': None,
        'duration_seconds': None,
        'duration_minutes': None,
        'codec': {},
        'bitrate': None
    }
    
    # Create temporary file for ffprobe analysis
    temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[1])
    
    try:
        # Write video data to temp file
        os.write(temp_fd, video_data)
        os.close(temp_fd)
        
        # Use ffprobe to extract metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            temp_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Extract format info
            format_info = data.get('format', {})
            duration_str = format_info.get('duration')
            if duration_str:
                duration_seconds = float(duration_str)
                metadata['duration_seconds'] = duration_seconds
                metadata['duration_minutes'] = round(duration_seconds / 60.0, 2)
            
            metadata['bitrate'] = format_info.get('bit_rate')
            metadata['format_name'] = format_info.get('format_name')
            
            # Extract video stream info
            streams = data.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    metadata['dimensions'] = {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'aspect_ratio': round(stream.get('width', 0) / stream.get('height', 1), 2) if stream.get('height') else None
                    }
                    metadata['codec'] = {
                        'video_codec': stream.get('codec_name'),
                        'profile': stream.get('profile'),
                        'level': stream.get('level'),
                        'fps': stream.get('r_frame_rate')
                    }
                    break
        
        return metadata
        
    except subprocess.TimeoutExpired:
        print(f"⚠️ ffprobe timeout for {filename}")
        return metadata
    except Exception as e:
        print(f"⚠️ Error extracting video metadata: {str(e)}")
        return metadata
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass


def generate_video_thumbnail(s3_key, video_data=None, bucket=None):
    """
    Generate thumbnail image from video using ffmpeg
    Extracts frame at 1 second mark
    
    Args:
        s3_key: S3 key of video (gallery_id/photo_id.ext)
        video_data: Optional raw video bytes (avoids re-download)
        bucket: Source bucket (defaults to S3_BUCKET)
    
    Returns:
        dict: {
            'success': bool,
            'thumbnail_key': str,  # S3 key of thumbnail
            'thumbnail_size': int,  # Bytes
            'error': str  # If failed
        }
    """
    if bucket is None:
        bucket = S3_BUCKET
    
    temp_video_path = None
    temp_thumb_path = None
    
    try:
        print(f"🎬 Generating video thumbnail for {s3_key}...")
        
        # Get video data if not provided
        if video_data is None:
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            video_data = response['Body'].read()
        
        # Create temp file for video
        video_ext = os.path.splitext(s3_key)[1]
        temp_video_fd, temp_video_path = tempfile.mkstemp(suffix=video_ext)
        os.write(temp_video_fd, video_data)
        os.close(temp_video_fd)
        
        # Create temp file for thumbnail
        temp_thumb_fd, temp_thumb_path = tempfile.mkstemp(suffix='.jpg')
        os.close(temp_thumb_fd)
        
        # Use ffmpeg to extract frame at 1 second
        cmd = [
            'ffmpeg',
            '-ss', '1',  # Seek to 1 second
            '-i', temp_video_path,
            '-vframes', '1',  # Extract 1 frame
            '-q:v', '2',  # High quality
            '-y',  # Overwrite output
            temp_thumb_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"⚠️ ffmpeg error: {result.stderr}")
            return {
                'success': False,
                'error': 'Failed to extract video frame'
            }
        
        # Read generated thumbnail
        with open(temp_thumb_path, 'rb') as f:
            thumbnail_data = f.read()
        
        # Generate thumbnail renditions (thumbnail, small, medium)
        # No large rendition needed for video thumbnails
        parts = s3_key.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid s3_key format: {s3_key}")
        
        gallery_id = parts[0]
        photo_filename = parts[1]
        photo_id = photo_filename.rsplit('.', 1)[0]
        
        # Open thumbnail image with PIL
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        
        # Convert RGBA to RGB if needed
        if thumbnail_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', thumbnail_image.size, (255, 255, 255))
            rgb_image.paste(thumbnail_image, mask=thumbnail_image.split()[3])
            thumbnail_image = rgb_image
        elif thumbnail_image.mode not in ('RGB', 'L'):
            thumbnail_image = thumbnail_image.convert('RGB')
        
        # Generate rendition sizes
        rendition_sizes = {
            'thumbnail': (400, 400),
            'small': (800, 600),
            'medium': (2000, 2000)
        }
        
        renditions = {}
        total_size = 0
        
        for size_name, (max_width, max_height) in rendition_sizes.items():
            img_copy = thumbnail_image.copy()
            img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to JPEG
            output = io.BytesIO()
            img_copy.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Upload to renditions bucket
            rendition_key = f"renditions/{gallery_id}/{photo_id}_{size_name}.jpg"
            s3_client.put_object(
                Bucket=S3_RENDITIONS_BUCKET,
                Key=rendition_key,
                Body=output.getvalue(),
                ContentType='image/jpeg'
            )
            
            renditions[size_name] = {
                'key': rendition_key,
                'size': len(output.getvalue()),
                'dimensions': img_copy.size
            }
            total_size += len(output.getvalue())
            
            print(f"  {size_name}: {img_copy.size[0]}x{img_copy.size[1]} ({len(output.getvalue()) / 1024:.1f} KB)")
        
        print(f"✅ Generated {len(renditions)} thumbnail renditions for video")
        
        return {
            'success': True,
            'renditions': renditions,
            'total_renditions_size': total_size,
            'original_dimensions': thumbnail_image.size
        }
        
    except subprocess.TimeoutExpired:
        print(f"⚠️ ffmpeg timeout for {s3_key}")
        return {
            'success': False,
            'error': 'Video thumbnail generation timeout'
        }
    except Exception as e:
        print(f"⚠️ Error generating video thumbnail: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Clean up temp files
        for temp_path in [temp_video_path, temp_thumb_path]:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass


def process_video_upload_async(s3_key, bucket=None, video_data=None):
    """
    Process video upload - generate thumbnail only
    Videos are served as-is, only thumbnails are generated
    
    Args:
        s3_key: S3 key of video
        bucket: Source bucket
        video_data: Optional video bytes
    
    Returns:
        dict: Processing result with thumbnail info
    """
    return generate_video_thumbnail(s3_key, video_data, bucket)
