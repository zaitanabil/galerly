#!/bin/bash
# Deploy Galerly Lambda with RAW format support (DNG, CR2, NEF, etc.)

set -e  # Exit on error

echo "🚀 Deploying Galerly Lambda with RAW support..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install/Update ONLY lightweight dependencies (image libs come from Lambda layer)
echo "📦 Installing lightweight dependencies..."
echo "   Note: Pillow, rawpy, pillow-heif, numpy come from Lambda layer"
pip install boto3>=1.28.0 stripe>=7.0.0 python-dotenv>=1.0.0 --upgrade

# Create package directory
echo "📁 Creating deployment package..."
rm -rf package
mkdir -p package

# Copy ONLY lightweight dependencies (exclude image processing libs)
echo "📚 Copying lightweight Python packages..."
echo "   Including: boto3, stripe, python-dotenv and their dependencies"
echo "   Excluding: Pillow, rawpy, pillow-heif, numpy (from Lambda layer)"

# Copy all packages, then remove image processing ones
cp -r venv/lib/python*/site-packages/* package/ 2>/dev/null || true

# Remove image processing libraries (they come from Lambda layer)
echo "   Removing image processing libs (from layer)..."
# Remove directories
find package -type d \( -name "PIL" -o -name "Pillow*" -o -name "rawpy*" -o -name "pillow_heif*" -o -name "numpy*" -o -name "imagecodecs*" \) -exec rm -rf {} + 2>/dev/null || true
# Remove .dist-info directories
find package -type d \( -name "Pillow*.dist-info" -o -name "rawpy*.dist-info" -o -name "pillow-heif*.dist-info" -o -name "numpy*.dist-info" -o -name "imagecodecs*.dist-info" \) -exec rm -rf {} + 2>/dev/null || true
# Remove .so files (compiled extensions) for image processing libs
find package -type f \( -name "*pillow*.so" -o -name "*rawpy*.so" -o -name "*numpy*.so" -o -name "*imagecodecs*.so" -o -name "_imaging*.so" -o -name "_pillow_heif*.so" \) -delete 2>/dev/null || true
# Remove any remaining files with these names
find package -type f -name "*PIL*" -delete 2>/dev/null || true
find package -type f -name "*Pillow*" -delete 2>/dev/null || true
find package -type f -name "*rawpy*" -delete 2>/dev/null || true
find package -type f -name "*pillow_heif*" -delete 2>/dev/null || true
find package -type f -name "*numpy*" -delete 2>/dev/null || true

# Copy application code
echo "📄 Copying application code..."
cp -r handlers package/
cp -r utils package/
cp api.py package/

# Remove unnecessary files to reduce package size
echo "🧹 Cleaning up unnecessary files..."
cd package
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
# Note: Don't delete .so files - boto3 may need them
# Image processing libs (Pillow, rawpy) come from Lambda layer, not this package

# Create deployment zip
echo "📦 Creating deployment package..."
zip -r ../galerly-lambda-raw.zip . -q
cd ..

echo ""
echo "✅ Deployment package created: galerly-lambda-raw.zip"
echo "📊 Package size: $(du -h galerly-lambda-raw.zip | cut -f1)"
echo ""
echo "🚀 Deploying to AWS Lambda..."

# Deploy to Lambda
aws lambda update-function-code \
    --function-name galerly-api \
    --zip-file fileb://galerly-lambda-raw.zip \
    --region us-east-1

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Testing RAW support..."
echo "   Upload a .dng, .cr2, or .nef file to test"
echo ""
echo "📸 Supported RAW formats:"
echo "   - DNG (Adobe, Lightroom)"
echo "   - CR2/CR3 (Canon)"
echo "   - NEF (Nikon)"
echo "   - ARW (Sony)"
echo "   - RAF (Fujifilm)"
echo "   - ORF (Olympus)"
echo "   - RW2 (Panasonic)"
echo "   - PEF (Pentax)"
echo "   - 3FR (Hasselblad)"
echo ""

