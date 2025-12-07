"""
Video Processing Lambda
Triggers on S3 ObjectCreated (video files)
Creates MediaConvert Job for HLS streaming
Extracts video duration for plan enforcement
"""
import boto3
import os
import json
import uuid
from urllib.parse import unquote_plus
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Initialize clients
# MediaConvert endpoint must be set in environment variables or fetched
mediaconvert = boto3.client('mediaconvert')
s3_client = boto3.client('s3')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
photos_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PHOTOS'))

def lambda_handler(event, context):
    global mediaconvert
    try:
        # Get MediaConvert endpoint if not set (best practice is to cache this)
        endpoint_url = os.environ.get('MEDIACONVERT_ENDPOINT')
        if not endpoint_url:
            try:
                endpoints = mediaconvert.describe_endpoints()
                endpoint_url = endpoints['Endpoints'][0]['Url']
                # Re-init client with endpoint
                mediaconvert = boto3.client('mediaconvert', endpoint_url=endpoint_url)
            except Exception as e:
                print(f"Failed to get MediaConvert endpoint: {e}")
                return {'statusCode': 500, 'body': json.dumps('MediaConvert config error')}

        for record in event['Records']:
            if 's3' not in record: continue
            
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            # Filter for video extensions
            if not key.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4v')):
                print(f"Skipping non-video file: {key}")
                continue
            
            # Skip if it's already in renditions folder (prevent loop)
            if key.startswith('renditions/'):
                continue
                
            print(f"Processing video: s3://{bucket}/{key}")
            
            # Extract video duration before processing
            duration_seconds = extract_video_duration_from_s3(bucket, key)
            
            # Create MediaConvert Job
            create_mediaconvert_job(bucket, key, endpoint_url, duration_seconds)
            
        return {'statusCode': 200, 'body': json.dumps('Processing complete')}
    except Exception as e:
        print(f"Error: {str(e)}")
        # Don't throw error to avoid S3 retry loop for bad files, just log
        return {'statusCode': 200, 'body': json.dumps(f"Error: {str(e)}")}

def extract_video_duration_from_s3(bucket, key):
    """
    Extract video duration using MediaInfo from S3 object metadata
    Falls back to estimating from file size if metadata unavailable
    """
    try:
        # Try to get duration from object metadata (if set during upload)
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        
        if 'duration' in metadata:
            return float(metadata['duration'])
        
        # Fallback: estimate based on file size (rough estimate)
        # Average: 1 MB per minute for standard quality video
        file_size_mb = response.get('ContentLength', 0) / (1024 * 1024)
        estimated_minutes = file_size_mb / 1.0  # Rough estimate
        
        print(f"⚠️  Duration not in metadata, estimating: {estimated_minutes:.2f} minutes")
        return estimated_minutes * 60
        
    except Exception as e:
        print(f"Error extracting duration: {str(e)}")
        # Return None - will be updated later if available
        return None


def create_mediaconvert_job(bucket, key, endpoint_url, duration_seconds=None):
    # Parse gallery_id and photo_id from key: gallery_id/photo_id.mp4
    parts = key.split('/')
    if len(parts) < 2: return
    gallery_id = parts[0]
    filename = parts[-1]
    photo_id = os.path.splitext(filename)[0]
    
    # Get photographer's plan to determine video quality
    # We'll need to fetch from DynamoDB to get user's quality setting
    video_quality = get_video_quality_for_gallery(gallery_id)
    
    # Destination for HLS (s3://bucket/renditions/gallery_id/photo_id/)
    output_key = f"renditions/{gallery_id}/{photo_id}/"
    destination = f"s3://{bucket}/{output_key}"
    
    # Job Settings (HLS output) - Quality based on plan
    # HD: 1080p + 720p
    # 4K: 2160p + 1080p + 720p
    outputs = build_video_outputs(video_quality)
    # Job Settings (HLS output) - Quality based on plan
    # HD: 1080p + 720p
    # 4K: 2160p + 1080p + 720p
    outputs = build_video_outputs(video_quality)
    
    # Using a simplified preset structure
    job_settings = {
        "OutputGroups": [
            {
                "Name": "HLS Group",
                "OutputGroupSettings": {
                    "Type": "HLS_GROUP_SETTINGS",
                    "HlsGroupSettings": {
                        "SegmentLength": 10,
                        "Destination": destination,
                        "MinSegmentLength": 0
                    }
                },
                "Outputs": outputs
            }
        ],
                "Outputs": outputs
            }
        ],
        "Inputs": [
            {
                "FileInput": f"s3://{bucket}/{key}",
                "AudioSelectors": {
                    "Audio Selector 1": {
                        "DefaultSelection": "DEFAULT"
                    }
                }
            }
        ]
    }


def get_video_quality_for_gallery(gallery_id):
    """
    Get video quality setting (hd or 4k) for a gallery's owner
    """
    try:
        from utils.config import galleries_table, users_table
        from handlers.subscription_handler import get_user_features
        
        # Get gallery to find owner
        gallery_response = galleries_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('id').eq(gallery_id),
            Limit=1
        )
        
        galleries = gallery_response.get('Items', [])
        if not galleries:
            return 'hd'  # Default to HD if gallery not found
        
        gallery = galleries[0]
        user_id = gallery.get('user_id')
        
        if not user_id:
            return 'hd'
        
        # Get user to fetch plan
        user_response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('id').eq(user_id),
            Limit=1
        )
        
        users = user_response.get('Items', [])
        if not users:
            return 'hd'
        
        user = users[0]
        features, _, _ = get_user_features(user)
        
        return features.get('video_quality', 'hd')
    except Exception as e:
        print(f"Error getting video quality: {str(e)}")
        return 'hd'  # Default to HD on error


def build_video_outputs(video_quality='hd'):
    """
    Build MediaConvert outputs based on video quality setting
    HD: 1080p + 720p
    4K: 2160p + 1080p + 720p
    """
    outputs = []
    
    # Common audio settings
    audio_desc = [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 96000, "CodingMode": "CODING_MODE_2_0", "SampleRate": 48000}}}]
    
    # 4K output (only for 4k quality)
    if video_quality == '4k':
        outputs.append({
            "NameModifier": "_2160p",
            "VideoDescription": {
                "CodecSettings": {
                    "Codec": "H_264",
                    "H264Settings": {
                        "RateControlMode": "QVBR",
                        "SceneChangeDetect": "TRANSITION_DETECTION",
                        "MaxBitrate": 15000000,
                        "QvbrSettings": {"QvbrQualityLevel": 9}
                    }
                },
                "Width": 3840,
                "Height": 2160
            },
            "AudioDescriptions": audio_desc
        })
    
    # 1080p output (both HD and 4K)
    outputs.append({
        "NameModifier": "_1080p",
        "VideoDescription": {
            "CodecSettings": {
                "Codec": "H_264",
                "H264Settings": {
                    "RateControlMode": "QVBR",
                    "SceneChangeDetect": "TRANSITION_DETECTION",
                    "MaxBitrate": 5000000,
                    "QvbrSettings": {"QvbrQualityLevel": 8}
                }
            },
            "Width": 1920,
            "Height": 1080
        },
        "AudioDescriptions": audio_desc
    })
    
    # 720p output (both HD and 4K)
    outputs.append({
        "NameModifier": "_720p",
        "VideoDescription": {
            "CodecSettings": {
                "Codec": "H_264",
                "H264Settings": {
                    "RateControlMode": "QVBR",
                    "SceneChangeDetect": "TRANSITION_DETECTION",
                    "MaxBitrate": 3000000,
                    "QvbrSettings": {"QvbrQualityLevel": 7}
                }
            },
            "Width": 1280,
            "Height": 720
        },
        "AudioDescriptions": audio_desc
    })
    
    # Thumbnail
    outputs.append({
        "NameModifier": "_thumbnail",
        "ContainerSettings": {"Container": "RAW"},
        "VideoDescription": {
            "CodecSettings": {
                "Codec": "FRAME_CAPTURE",
                "FrameCaptureSettings": {
                    "Quality": 80
                }
            },
            "Width": 1280,
            "Height": 720
        }
    })
    
    return outputs
    
    role_arn = os.environ.get('MEDIACONVERT_ROLE_ARN')
    if not role_arn:
        print("Error: MEDIACONVERT_ROLE_ARN not set")
        return

    try:
        response = mediaconvert.create_job(
            Role=role_arn,
            Settings=job_settings,
            UserMetadata={
                'gallery_id': gallery_id,
                'photo_id': photo_id
            }
        )
        
        # Update DynamoDB status and duration
        try:
            # Update status, type, and duration if available
            if duration_seconds is not None:
                photos_table.update_item(
                    Key={'id': photo_id},
                    UpdateExpression="SET #s = :s, #t = :t, duration_seconds = :dur",
                    ExpressionAttributeNames={'#s': 'status', '#t': 'type'},
                    ExpressionAttributeValues={
                        ':s': 'processing_video',
                        ':t': 'video',
                        ':dur': Decimal(str(duration_seconds))
                    }
                )
                print(f"✅ Stored duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
            else:
                photos_table.update_item(
                    Key={'id': photo_id},
                    UpdateExpression="SET #s = :s, #t = :t",
                    ExpressionAttributeNames={'#s': 'status', '#t': 'type'},
                    ExpressionAttributeValues={':s': 'processing_video', ':t': 'video'}
                )
        except Exception as db_err:
            print(f"DynamoDB Update Error: {db_err}")
        
        print(f"Created MediaConvert Job: {response['Job']['Id']}")
        
    except Exception as e:
        print(f"MediaConvert Error: {str(e)}")
        raise

