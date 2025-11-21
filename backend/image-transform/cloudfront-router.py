"""
CloudFront Origin Request Handler (Lambda@Edge)
Routes image transformation requests to the image-transform Lambda

Deploy this to Lambda@Edge for CloudFront Origin Request events
Size limit: 1MB (no heavy dependencies)

Configuration:
- Set TRANSFORM_LAMBDA_ARN environment variable during deployment
- Attach to CloudFront as Origin Request trigger
- Ensure Lambda@Edge role has lambda:InvokeFunction permission
"""
import json
import boto3
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Image transform Lambda ARN from environment variable
# Lambda@Edge must invoke Lambda in us-east-1
# Set via: aws lambda update-function-configuration --environment Variables={TRANSFORM_LAMBDA_ARN=...}
TRANSFORM_LAMBDA_ARN = os.environ.get('TRANSFORM_LAMBDA_ARN')

if not TRANSFORM_LAMBDA_ARN:
    raise ValueError('TRANSFORM_LAMBDA_ARN environment variable is required')

def lambda_handler(event, context):
    """
    Lambda@Edge Origin Request handler
    Detects transformation parameters and invokes transform Lambda
    """
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    querystring = request.get('querystring', '')
    
    print(f"📥 Origin request: {uri}?{querystring}")
    
    # Check if transformation requested
    if not querystring or ('format=' not in querystring and 'width=' not in querystring):
        # No transformation - pass through to S3
        print(f"✅ No transformation needed, passing to S3")
        return request
    
    # Extract s3_key from URI (remove leading slash)
    s3_key = uri.lstrip('/')
    
    # Parse query string parameters
    params = {}
    if querystring:
        for item in querystring.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value
    
    # Build Lambda payload
    payload = {
        's3_key': s3_key,
        'format': params.get('format', 'jpeg'),
        'fit': params.get('fit', 'inside'),
        'quality': int(params.get('quality', 85))
    }
    
    if params.get('width'):
        payload['width'] = int(params['width'])
    if params.get('height'):
        payload['height'] = int(params['height'])
    
    print(f"🔄 Invoking transform Lambda: {json.dumps(payload)}")
    
    try:
        # Invoke image transform Lambda
        response = lambda_client.invoke(
            FunctionName=TRANSFORM_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse Lambda response
        lambda_response = json.loads(response['Payload'].read())
        
        if lambda_response.get('statusCode') == 200:
            # Success - return transformed image
            print(f"✅ Transform successful")
            
            # CloudFront expects specific response format
            return {
                'status': '200',
                'statusDescription': 'OK',
                'headers': {
                    'content-type': [{
                        'key': 'Content-Type',
                        'value': lambda_response['headers']['Content-Type']
                    }],
                    'cache-control': [{
                        'key': 'Cache-Control',
                        'value': lambda_response['headers']['Cache-Control']
                    }]
                },
                'body': lambda_response['body'],
                'bodyEncoding': 'base64'
            }
        else:
            # Transform failed - log and pass through to S3
            print(f"⚠️  Transform failed: {lambda_response}")
            return request
            
    except Exception as e:
        print(f"❌ Lambda invocation failed: {str(e)}")
        # On error, pass through to S3 (return original)
        return request

