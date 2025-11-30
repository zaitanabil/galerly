"""
Video Processing Lambda
Triggers on S3 ObjectCreated (video files)
Creates MediaConvert Job for HLS streaming
"""
import boto3
import os
import json
import uuid
from urllib.parse import unquote_plus

# Initialize clients
# MediaConvert endpoint must be set in environment variables or fetched
mediaconvert = boto3.client('mediaconvert')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
photos_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PHOTOS', 'galerly-photos'))

def lambda_handler(event, context):
    try:
        # Get MediaConvert endpoint if not set (best practice is to cache this)
        endpoint_url = os.environ.get('MEDIACONVERT_ENDPOINT')
        if not endpoint_url:
            try:
                endpoints = mediaconvert.describe_endpoints()
                endpoint_url = endpoints['Endpoints'][0]['Url']
                # Re-init client with endpoint
                global mediaconvert
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
            
            # Create MediaConvert Job
            create_mediaconvert_job(bucket, key, endpoint_url)
            
        return {'statusCode': 200, 'body': json.dumps('Processing complete')}
    except Exception as e:
        print(f"Error: {str(e)}")
        # Don't throw error to avoid S3 retry loop for bad files, just log
        return {'statusCode': 200, 'body': json.dumps(f"Error: {str(e)}")}

def create_mediaconvert_job(bucket, key, endpoint_url):
    # Parse gallery_id and photo_id from key: gallery_id/photo_id.mp4
    parts = key.split('/')
    if len(parts) < 2: return
    gallery_id = parts[0]
    filename = parts[-1]
    photo_id = os.path.splitext(filename)[0]
    
    # Destination for HLS (s3://bucket/renditions/gallery_id/photo_id/)
    output_key = f"renditions/{gallery_id}/{photo_id}/"
    destination = f"s3://{bucket}/{output_key}"
    
    # Job Settings (HLS output)
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
                "Outputs": [
                    {
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
                        "AudioDescriptions": [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 96000, "CodingMode": "CODING_MODE_2_0", "SampleRate": 48000}}}]
                    },
                    {
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
                        "AudioDescriptions": [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 96000, "CodingMode": "CODING_MODE_2_0", "SampleRate": 48000}}}]
                    },
                    {
                        "NameModifier": "_thumbnail", # Poster image
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
                    }
                ]
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
        
        # Update DynamoDB status
        try:
            # We also update the 'type' to 'video' just in case
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

