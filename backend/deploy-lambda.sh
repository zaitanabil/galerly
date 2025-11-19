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

# Install/Update dependencies
echo "📦 Installing dependencies (including rawpy for RAW files)..."
pip install -r requirements.txt --upgrade

# Create package directory
echo "📁 Creating deployment package..."
rm -rf package
mkdir -p package

# Copy dependencies to package
echo "📚 Copying Python packages..."
cp -r venv/lib/python*/site-packages/* package/

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
find . -type f -name "*.so" -delete 2>/dev/null || true  # Remove compiled extensions (Lambda will use its own)

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

