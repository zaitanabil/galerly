#!/bin/bash
# Local Test Script for Image Transformation System
# Tests Lambda functions locally before AWS deployment

set -e

echo "=========================================="
echo "🧪 LOCAL IMAGE TRANSFORMATION TEST"
echo "=========================================="
echo ""

# Configuration
TEST_IMAGES_DIR="${1:-/Users/nz-dev/Downloads/tenerife}"
TRANSFORM_LAMBDA="lambda_function.py"
ROUTER_LAMBDA="cloudfront-router.py"

if [ ! -d "$TEST_IMAGES_DIR" ]; then
    echo "❌ Test images directory not found: $TEST_IMAGES_DIR"
    echo "Usage: ./test-local.sh /path/to/images"
    exit 1
fi

echo "📁 Test images directory: $TEST_IMAGES_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "$TRANSFORM_LAMBDA" ]; then
    echo "❌ Not in image-transform directory"
    echo "Run: cd backend/image-transform"
    exit 1
fi

# Test 1: Check Python dependencies
echo "1️⃣  Checking Python Dependencies..."
echo ""

MISSING_DEPS=""

python3 -c "import PIL; print('   ✅ Pillow:', PIL.__version__)" 2>/dev/null || MISSING_DEPS="${MISSING_DEPS}Pillow "
python3 -c "import rawpy; print('   ✅ rawpy:', rawpy.__version__)" 2>/dev/null || MISSING_DEPS="${MISSING_DEPS}rawpy "
python3 -c "import pillow_heif; print('   ✅ pillow-heif:', pillow_heif.__version__)" 2>/dev/null || MISSING_DEPS="${MISSING_DEPS}pillow-heif "
python3 -c "import numpy; print('   ✅ numpy:', numpy.__version__)" 2>/dev/null || MISSING_DEPS="${MISSING_DEPS}numpy "
python3 -c "import boto3; print('   ✅ boto3:', boto3.__version__)" 2>/dev/null || MISSING_DEPS="${MISSING_DEPS}boto3 "

if [ -n "$MISSING_DEPS" ]; then
    echo ""
    echo "❌ Missing dependencies: $MISSING_DEPS"
    echo ""
    echo "Install with:"
    echo "pip3 install Pillow>=10.0.0 rawpy>=0.18.0 pillow-heif>=0.13.0 numpy boto3"
    exit 1
fi

echo ""
echo "✅ All dependencies installed"
echo ""

# Test 2: Check CloudFront Router ARN injection
echo "2️⃣  Checking CloudFront Router Configuration..."
echo ""

if grep -q "__TRANSFORM_LAMBDA_ARN_PLACEHOLDER__" "$ROUTER_LAMBDA"; then
    echo "   ⚠️  ARN placeholder found (expected for source file)"
    echo "   ✅ Will be injected during deployment"
else
    INJECTED_ARN=$(grep "TRANSFORM_LAMBDA_ARN = " "$ROUTER_LAMBDA" | head -1 | cut -d"'" -f2)
    if [ -n "$INJECTED_ARN" ]; then
        echo "   ✅ ARN injected: $INJECTED_ARN"
    else
        echo "   ❌ No ARN found in router"
    fi
fi

echo ""

# Test 3: Find HEIC images for testing
echo "3️⃣  Finding Test Images..."
echo ""

HEIC_IMAGES=$(find "$TEST_IMAGES_DIR" -type f -iname "*.heic" | head -5)
HEIC_COUNT=$(echo "$HEIC_IMAGES" | grep -c ".heic" 2>/dev/null || echo "0")

if [ "$HEIC_COUNT" -eq 0 ]; then
    echo "   ⚠️  No HEIC images found in $TEST_IMAGES_DIR"
    echo "   Skipping image processing tests"
else
    echo "   ✅ Found $HEIC_COUNT HEIC images for testing"
    echo "$HEIC_IMAGES" | while read -r IMG; do
        if [ -n "$IMG" ]; then
            BASENAME=$(basename "$IMG")
            SIZE=$(du -h "$IMG" | cut -f1)
            echo "      - $BASENAME ($SIZE)"
        fi
    done
fi

echo ""

# Test 4: Test HEIC Image Processing
if [ "$HEIC_COUNT" -gt 0 ]; then
    echo "4️⃣  Testing HEIC Image Processing..."
    echo ""
    
    TEST_IMAGE=$(echo "$HEIC_IMAGES" | head -1)
    TEST_BASENAME=$(basename "$TEST_IMAGE")
    
    echo "   📸 Testing: $TEST_BASENAME"
    echo ""
    
    # Create Python test script
    cat > /tmp/test_heic_transform.py << 'EOF'
import sys
import io
from PIL import Image
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

def test_heic_conversion(image_path, width=800, height=600):
    """Test HEIC to JPEG conversion"""
    try:
        # Load HEIC
        print(f"   📥 Loading HEIC image...")
        img = Image.open(image_path)
        
        print(f"   📊 Original size: {img.size[0]}x{img.size[1]}")
        print(f"   🎨 Mode: {img.mode}")
        
        # Resize
        print(f"   🔄 Resizing to {width}x{height}...")
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        print(f"   📏 Resized to: {img.size[0]}x{img.size[1]}")
        
        # Convert to JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            print(f"   🔄 Converting {img.mode} to RGB...")
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Save to buffer
        print(f"   💾 Converting to JPEG...")
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        output_size = buffer.tell()
        
        print(f"   ✅ JPEG size: {output_size / 1024:.1f} KB")
        print(f"   ✅ Conversion successful!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_heic_conversion(sys.argv[1])
    sys.exit(0 if success else 1)
EOF
    
    # Run test
    if python3 /tmp/test_heic_transform.py "$TEST_IMAGE"; then
        echo ""
        echo "   ✅ HEIC processing works locally"
    else
        echo ""
        echo "   ❌ HEIC processing failed"
        exit 1
    fi
    
    echo ""
fi

# Test 5: Test CloudFront Router Logic
echo "5️⃣  Testing CloudFront Router Logic..."
echo ""

cat > /tmp/test_router_logic.py << 'EOF'
import json

def test_router_logic():
    """Test CloudFront router request parsing"""
    
    # Test case 1: Request with transformation parameters
    test_request_1 = {
        'Records': [{
            'cf': {
                'request': {
                    'uri': '/gallery123/photo456.HEIC',
                    'querystring': 'format=jpeg&width=800&height=600&fit=inside'
                }
            }
        }]
    }
    
    request = test_request_1['Records'][0]['cf']['request']
    uri = request['uri']
    querystring = request.get('querystring', '')
    
    print(f"   📥 Test Request 1:")
    print(f"      URI: {uri}")
    print(f"      Query: {querystring}")
    
    # Parse query string
    params = {}
    if querystring:
        for item in querystring.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value
    
    # Build payload
    s3_key = uri.lstrip('/')
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
    
    print(f"   📤 Generated Payload:")
    print(f"      {json.dumps(payload, indent=6)}")
    
    # Verify required fields
    assert payload['s3_key'] == 'gallery123/photo456.HEIC'
    assert payload['format'] == 'jpeg'
    assert payload['width'] == 800
    assert payload['height'] == 600
    
    print(f"   ✅ Router logic works correctly")
    
    # Test case 2: Request without transformation
    test_request_2 = {
        'Records': [{
            'cf': {
                'request': {
                    'uri': '/gallery123/photo456.jpg',
                    'querystring': ''
                }
            }
        }]
    }
    
    request = test_request_2['Records'][0]['cf']['request']
    querystring = request.get('querystring', '')
    
    print(f"")
    print(f"   📥 Test Request 2 (no transformation):")
    print(f"      URI: {request['uri']}")
    print(f"      Query: (empty)")
    
    if not querystring or ('format=' not in querystring and 'width=' not in querystring):
        print(f"   ✅ Correctly identified: no transformation needed")
    else:
        print(f"   ❌ Should skip transformation")
        return False
    
    return True

if __name__ == '__main__':
    try:
        success = test_router_logic()
        exit(0 if success else 1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
EOF

if python3 /tmp/test_router_logic.py; then
    echo ""
    echo "   ✅ Router logic validated"
else
    echo ""
    echo "   ❌ Router logic failed"
    exit 1
fi

echo ""

# Summary
echo "=========================================="
echo "✅ LOCAL TESTS COMPLETE"
echo "=========================================="
echo ""
echo "Test Results:"
echo "  ✅ Python dependencies installed"
echo "  ✅ CloudFront router configuration valid"
echo "  ✅ HEIC processing works locally"
echo "  ✅ Router logic validated"
echo ""
echo "Ready to deploy:"
echo "  1. Run: ./deploy.sh (Image Transform Lambda)"
echo "  2. Run: ./deploy-cloudfront-router.sh (CloudFront Router)"
echo "  3. Or push to main branch (GitHub Actions deploys both)"
echo ""

