# CloudFront + Image Transform Lambda Setup
# This connects CloudFront to the image transformation Lambda

## Architecture

```
Browser Request
    ↓
CloudFront (cdn.galerly.com)
    ↓
Origin Request (checks if ?format=jpeg&width=...)
    ↓
API Gateway → Image Transform Lambda
    ↓
Lambda checks cache bucket
    ├─ Hit: Return cached image
    └─ Miss: Fetch original → Transform → Cache → Return
```

## Setup Steps

### 1. Create S3 Cache Bucket
```bash
aws s3 mb s3://galerly-image-cache --region us-east-1

# Enable versioning for safety
aws s3api put-bucket-versioning \
    --bucket galerly-image-cache \
    --versioning-configuration Status=Enabled

# Set lifecycle policy to clean old cache (optional)
aws s3api put-bucket-lifecycle-configuration \
    --bucket galerly-image-cache \
    --lifecycle-configuration file://cache-lifecycle.json
```

### 2. Deploy Image Transform Lambda
```bash
cd backend/image-transform
./deploy.sh
```

### 3. Create Lambda Layer for Image Processing Libraries
```bash
# Create layer directory
mkdir -p layer/python

# Install dependencies
pip install \
    Pillow>=10.0.0 \
    rawpy>=0.18.0 \
    pillow-heif>=0.13.0 \
    numpy>=1.24.0 \
    -t layer/python

# Create layer zip
cd layer
zip -r ../image-processing-layer.zip . -q
cd ..

# Upload layer to AWS
aws lambda publish-layer-version \
    --layer-name image-processing \
    --description "Image processing libraries (Pillow, rawpy, heif)" \
    --zip-file fileb://image-processing-layer.zip \
    --compatible-runtimes python3.11 \
    --region us-east-1

# Attach layer to Lambda (get ARN from previous command)
aws lambda update-function-configuration \
    --function-name galerly-image-transform \
    --layers arn:aws:lambda:us-east-1:ACCOUNT_ID:layer:image-processing:VERSION
```

### 4. Create API Gateway
```bash
# Create REST API
aws apigateway create-rest-api \
    --name "galerly-image-api" \
    --description "Image transformation API" \
    --endpoint-configuration types=REGIONAL

# Get API ID and root resource ID from output
API_ID="your-api-id"
RESOURCE_ID="your-resource-id"

# Create resource for image transformation
aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $RESOURCE_ID \
    --path-part "transform"

# Create GET method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id NEW_RESOURCE_ID \
    --http-method GET \
    --authorization-type NONE

# Integrate with Lambda
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id NEW_RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:ACCOUNT_ID:function:galerly-image-transform/invocations

# Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod
```

### 5. Configure CloudFront

#### Option A: Lambda@Edge (Simple, but size limited)
Create a simple Lambda@Edge function that detects transformation parameters and forwards to the image-transform Lambda:

```python
# cloudfront-image-router.py
import json
import boto3

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    querystring = request.get('querystring', '')
    
    # If transformation parameters present, invoke transform Lambda
    if 'format=' in querystring or 'width=' in querystring:
        # Extract s3_key from URI
        s3_key = uri.lstrip('/')
        
        # Parse query string
        params = dict(item.split('=') for item in querystring.split('&') if '=' in item)
        
        # Invoke transform Lambda
        response = lambda_client.invoke(
            FunctionName='galerly-image-transform',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                's3_key': s3_key,
                'width': int(params.get('width', 0)) if params.get('width') else None,
                'height': int(params.get('height', 0)) if params.get('height') else None,
                'format': params.get('format', 'jpeg'),
                'fit': params.get('fit', 'inside'),
                'quality': int(params.get('quality', 85))
            })
        )
        
        # Return transformed image response
        return response['Payload'].read()
    
    # No transformation - return original
    return request
```

#### Option B: API Gateway Origin (Recommended for RAW)
Add API Gateway as a custom origin in CloudFront for transformation requests:

```yaml
CloudFront Behaviors:
  - Path Pattern: *.dng?*, *.cr2?*, *.nef?*, *.heic?*
    Origin: API Gateway (galerly-image-api.execute-api.us-east-1.amazonaws.com)
    
  - Path Pattern: Default (*)
    Origin: S3 (galerly-uploads.s3.amazonaws.com)
```

### 6. Test
```bash
# Test Lambda directly
aws lambda invoke \
    --function-name galerly-image-transform \
    --payload '{"s3_key":"test-gallery/test.dng","width":800,"height":600,"format":"jpeg"}' \
    response.json

# Test via CloudFront
curl -I "https://cdn.galerly.com/gallery123/photo.dng?format=jpeg&width=800&height=600"
```

## Storage Efficiency

Example for 1000 photos:

**Before (duplicate storage):**
- 1000 RAW files @ 50MB each = 50 GB
- 1000 JPEG previews @ 30MB = 30 GB
- 1000 thumbnails @ 5MB = 5 GB
- **Total: 85 GB**

**After (on-demand transformation):**
- 1000 RAW files @ 50MB each = 50 GB
- 1000 cached medium JPEGs @ 2MB = 2 GB
- 1000 cached thumbnails @ 200KB = 0.2 GB
- **Total: 52.2 GB** (38% savings!)

## Performance

- **First request**: 2-5 seconds (RAW processing)
- **Cached requests**: 50-200ms (CloudFront edge)
- **Cache hit rate**: >95% after warmup

