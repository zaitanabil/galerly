"""
CloudFront Origin Request Handler (Lambda@Edge)
Routes image transformation requests with cache-first strategy

Performance optimization:
1. Check S3 cache first (fast)
2. Only invoke transform Lambda if not cached
3. Pass through regular requests immediately

Deploy this to Lambda@Edge for CloudFront Origin Request events
Size limit: 1MB (no heavy dependencies)
"""
import json
import boto3

lambda_client = boto3.client('lambda', region_name='us-east-1')
s3_client = boto3.client('s3')

# Configuration - injected at build time by deployment script
TRANSFORM_LAMBDA_ARN = '__TRANSFORM_LAMBDA_ARN_PLACEHOLDER__'
CACHE_BUCKET = '__CACHE_BUCKET_PLACEHOLDER__'

def lambda_handler(event, context):
    """
    Lambda@Edge Origin Request handler with cache-first strategy
    
    Flow:
    1. Check if transformation requested (?format= or ?width=)
    2. If no transformation, pass through to S3
    3. If transformation, check cache first
    4. If cached, redirect to cache
    5. If not cached, invoke transform Lambda
    """
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    querystring = request.get('querystring', '')
    
    # No transformation requested - pass through to S3 immediately
    if not querystring or ('format=' not in querystring and 'width=' not in querystring):
        return request
    
    # Extract S3 key
    s3_key = uri.lstrip('/')
    
    # Parse transformation parameters
    params = {}
        for item in querystring.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value
    
    # Generate cache key
    cache_parts = [s3_key.replace('/', '_')]
    if params.get('width'):
        cache_parts.append(f"w{params['width']}")
    if params.get('height'):
        cache_parts.append(f"h{params['height']}")
    if params.get('format'):
        cache_parts.append(params['format'])
    
    cache_key = '-'.join(cache_parts)
    
    # Check if cached version exists
    try:
        s3_client.head_object(Bucket=CACHE_BUCKET, Key=cache_key)
        
        # Cached! Redirect to cache bucket
        print(f"✅ Cache HIT: {cache_key}")
        request['origin'] = {
            's3': {
                'domainName': f'{CACHE_BUCKET}.s3.amazonaws.com',
                'region': 'us-east-1',
                'authMethod': 'none',
                'path': '',
                'customHeaders': {}
            }
        }
        request['uri'] = f'/{cache_key}'
        return request
        
    except:
        # Not cached - invoke transform Lambda
        print(f"❌ Cache MISS: {cache_key} - Invoking transform Lambda")
        
    payload = {
        's3_key': s3_key,
            'cache_key': cache_key,
        'format': params.get('format', 'jpeg'),
        'fit': params.get('fit', 'inside'),
        'quality': int(params.get('quality', 85))
    }
    
    if params.get('width'):
        payload['width'] = int(params['width'])
    if params.get('height'):
        payload['height'] = int(params['height'])
    
    try:
            # Invoke transform Lambda asynchronously for better performance
            lambda_client.invoke(
            FunctionName=TRANSFORM_LAMBDA_ARN,
                InvocationType='Event',  # Async - don't wait for response
            Payload=json.dumps(payload)
        )
        
            # Return original while transformation happens in background
            # Next request will hit cache
            print(f"🔄 Transform initiated, serving original")
            return request
            
    except Exception as e:
        print(f"❌ Lambda invocation failed: {str(e)}")
        return request

