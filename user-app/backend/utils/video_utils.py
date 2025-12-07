"""
Video utilities for duration extraction and management
Supports duration tracking for plan enforcement
"""
import subprocess
import json
import tempfile
import os
import boto3
from decimal import Decimal


def extract_video_duration(file_path_or_url):
    """
    Extract video duration in seconds using ffprobe
    Supports local file paths and S3 URLs
    
    Args:
        file_path_or_url: Local path or s3:// URL
    
    Returns:
        float: Duration in seconds, or None if extraction fails
    """
    try:
        # If S3 URL, download temporarily
        temp_file = None
        if file_path_or_url.startswith('s3://'):
            temp_file = download_s3_temp(file_path_or_url)
            target_path = temp_file
        else:
            target_path = file_path_or_url
        
        # Use ffprobe to get duration
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            target_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Cleanup temp file if created
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        
        if result.returncode != 0:
            print(f"ffprobe error: {result.stderr}")
            return None
        
        # Parse JSON output
        data = json.loads(result.stdout)
        duration_str = data.get('format', {}).get('duration')
        
        if duration_str:
            return float(duration_str)
        
        return None
        
    except subprocess.TimeoutExpired:
        print("ffprobe timeout - video may be too large")
        return None
    except Exception as e:
        print(f"Error extracting video duration: {str(e)}")
        return None


def download_s3_temp(s3_url):
    """
    Download S3 object to temporary file
    Returns: temp file path
    """
    # Parse s3://bucket/key
    parts = s3_url.replace('s3://', '').split('/', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid S3 URL: {s3_url}")
    
    bucket, key = parts
    
    s3_client = boto3.client('s3')
    
    # Create temp file
    suffix = os.path.splitext(key)[1]
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(temp_fd)
    
    # Download
    s3_client.download_file(bucket, key, temp_path)
    
    return temp_path


def get_user_video_usage(user_id, dynamodb_table):
    """
    Calculate total video minutes used by a user
    
    Args:
        user_id: User ID
        dynamodb_table: DynamoDB photos table resource
    
    Returns:
        dict: {
            'total_minutes': float,
            'total_seconds': float,
            'video_count': int
        }
    """
    try:
        from boto3.dynamodb.conditions import Key
        
        # Query all videos for this user
        # Assuming photos table has UserIdIndex and type field
        response = dynamodb_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression='#t = :video',
            ExpressionAttributeNames={'#t': 'type'},
            ExpressionAttributeValues={':video': 'video'}
        )
        
        videos = response.get('Items', [])
        
        total_seconds = 0
        video_count = 0
        
        for video in videos:
            duration = video.get('duration_seconds', 0)
            if duration:
                total_seconds += float(duration)
                video_count += 1
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = dynamodb_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('user_id').eq(user_id),
                FilterExpression='#t = :video',
                ExpressionAttributeNames={'#t': 'type'},
                ExpressionAttributeValues={':video': 'video'},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            videos = response.get('Items', [])
            for video in videos:
                duration = video.get('duration_seconds', 0)
                if duration:
                    total_seconds += float(duration)
                    video_count += 1
        
        total_minutes = total_seconds / 60.0
        
        return {
            'total_minutes': round(total_minutes, 2),
            'total_seconds': round(total_seconds, 2),
            'video_count': video_count
        }
        
    except Exception as e:
        print(f"Error calculating video usage: {str(e)}")
        return {
            'total_minutes': 0,
            'total_seconds': 0,
            'video_count': 0
        }


def enforce_video_duration_limit(user, additional_minutes, features):
    """
    Check if user can upload additional video minutes
    
    Args:
        user: User object with 'id'
        additional_minutes: Minutes to add
        features: User features dict with 'video_minutes' limit
    
    Returns:
        tuple: (allowed: bool, error_message: str or None)
    """
    try:
        from utils.config import photos_table
        
        # Get video minute limit from features
        video_limit_minutes = features.get('video_minutes', 0)
        
        # -1 means unlimited
        if video_limit_minutes == -1:
            return True, None
        
        # 0 means no video allowed
        if video_limit_minutes == 0:
            return False, "Video uploads are not available on your plan. Please upgrade to upload videos."
        
        # Get current usage
        usage = get_user_video_usage(user['id'], photos_table)
        current_minutes = usage['total_minutes']
        
        # Check if adding this video would exceed limit
        projected_minutes = current_minutes + additional_minutes
        
        if projected_minutes > video_limit_minutes:
            remaining = max(0, video_limit_minutes - current_minutes)
            return False, f"Video duration limit reached. You have {remaining:.1f} minutes remaining on your plan (limit: {video_limit_minutes} minutes). Please upgrade for more video storage."
        
        return True, None
        
    except Exception as e:
        print(f"Error enforcing video limit: {str(e)}")
        # Fail open - allow upload if check fails
        return True, None


def format_duration(seconds):
    """
    Format seconds as human-readable duration
    
    Examples:
        90 -> "1:30"
        3665 -> "1:01:05"
    """
    if not seconds:
        return "0:00"
    
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

