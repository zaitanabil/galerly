# RAW Format Support Deployment Guide

## Issue
```
Error: RAW format detected but rawpy is not installed. Cannot sanitize RAW files.
```

DNG, CR2, NEF, and other RAW files are being rejected because the Lambda function doesn't have the `rawpy` library installed.

## Solution - GitHub Actions CI/CD (RECOMMENDED)

**The GitHub Actions workflow now automatically handles RAW format support!**

### What Was Fixed

The `.github/workflows/deploy.yml` workflow has been updated with:

1. ✅ **Automatic Dependency Installation**: `rawpy`, `pillow-heif`, and all image processing libraries are automatically installed
2. ✅ **Dependency Verification**: Workflow verifies that `rawpy` is present before deployment
3. ✅ **Post-Deployment Testing**: After deployment, workflow downloads and inspects the Lambda package to confirm RAW support
4. ✅ **Build Fails on Missing Dependencies**: If `rawpy` or critical libraries are missing, the build fails immediately

### How to Deploy

**Just push to main:**

```bash
git add .
git commit -m "Updated deployment workflow"
git push origin main
```

The GitHub Actions workflow will:
1. Install all dependencies (including `rawpy`)
2. Verify dependencies are present
3. Package everything into a Lambda-compatible zip
4. Deploy to AWS Lambda
5. Verify RAW format support is working
6. Generate a deployment summary showing all supported formats

**That's it!** No manual steps required. 🚀

### What You'll See in GitHub Actions

```
📦 Packaging Lambda function with RAW format support...
📚 Installing Python dependencies (including rawpy for RAW files)...
🔍 Verifying critical dependencies are installed...
✅ Pillow installed
✅ rawpy installed (RAW format support: DNG, CR2, NEF, ARW, etc.)
✅ pillow-heif installed (HEIC/HEIF support for iPhone photos)
✅ boto3 installed (AWS SDK)
✅ stripe installed (Payment processing)

📦 Package contents summary:
   Total size: 45M
   Total files: 2,431

✅ Lambda package created successfully!
   📦 Size: 45M (45MB)
   📸 RAW format support: ENABLED (DNG, CR2, NEF, ARW, RAF, ORF, RW2, PEF, 3FR)
   📱 HEIC support: ENABLED (iPhone photos)
   🔒 Image security: ENABLED (malware scanning + metadata stripping)
```

And after deployment:

```
📸 Verifying RAW format support in Lambda...
✅ rawpy found in Lambda package (RAW format support: DNG, CR2, NEF, ARW, RAF, ORF, RW2, PEF, 3FR)
✅ Pillow found in Lambda package (Image processing)
✅ pillow-heif found in Lambda package (HEIC/HEIF support for iPhone photos)
✅ RAW format support verification complete!
   Lambda is ready to process DNG and other RAW files 📸
```

## Manual Deployment (If Needed)

If you need to deploy manually outside of GitHub Actions:

### Step 1: Install Dependencies

```bash
cd backend

# Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt --upgrade
```

### Step 2: Create Deployment Package

```bash
# Create package directory
rm -rf package
mkdir package

# Copy dependencies
cp -r venv/lib/python*/site-packages/* package/

# Copy application code
cp -r handlers package/
cp -r utils package/
cp api.py package/

# Create zip
cd package
zip -r ../galerly-lambda-raw.zip .
cd ..
```

### Step 3: Deploy to Lambda

```bash
aws lambda update-function-code \
    --function-name galerly-api \
    --zip-file fileb://galerly-lambda-raw.zip \
    --region us-east-1
```

## Option 3: Using AWS Lambda Layers (Advanced)

For better performance, you can create a Lambda Layer with dependencies:

### Create Layer

```bash
cd backend
mkdir python
pip install -r requirements.txt -t python/
zip -r galerly-dependencies-layer.zip python

aws lambda publish-layer-version \
    --layer-name galerly-dependencies \
    --zip-file fileb://galerly-dependencies-layer.zip \
    --compatible-runtimes python3.9 python3.10 python3.11
```

### Attach Layer to Function

```bash
# Get the layer version ARN from previous command output
aws lambda update-function-configuration \
    --function-name galerly-api \
    --layers arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:galerly-dependencies:1
```

Then deploy just your code (much faster):

```bash
zip -r galerly-code.zip handlers utils api.py
aws lambda update-function-code \
    --function-name galerly-api \
    --zip-file fileb://galerly-code.zip
```

## Dependencies Included

After deployment, Lambda will have:

- ✅ **Pillow** (10.0.0+) - Image processing
- ✅ **pillow-heif** (0.13.0+) - HEIC/HEIF support (iPhone photos)
- ✅ **rawpy** (0.18.0+) - RAW format support
- ✅ **imagecodecs** - Additional codec support
- ✅ **boto3** - AWS SDK
- ✅ **stripe** - Payment processing

## Supported RAW Formats After Deployment

| Format | Extension | Camera Brand |
|--------|-----------|--------------|
| Adobe DNG | `.dng` | Adobe, Lightroom, many phones |
| Canon RAW | `.cr2`, `.cr3` | Canon DSLR/Mirrorless |
| Nikon RAW | `.nef` | Nikon DSLR/Mirrorless |
| Sony RAW | `.arw` | Sony cameras |
| Fujifilm RAW | `.raf` | Fujifilm cameras |
| Olympus RAW | `.orf` | Olympus cameras |
| Panasonic RAW | `.rw2` | Panasonic Lumix |
| Pentax RAW | `.pef` | Pentax cameras |
| Hasselblad RAW | `.3fr` | Hasselblad medium format |
| Apple HEIC | `.heic`, `.heif` | iPhone, iPad |

## What Happens to RAW Files

1. **Upload** → RAW file uploaded to S3
2. **Security Check** → Scanned for malicious content
3. **Conversion** → RAW converted to RGB using `rawpy`
4. **Sanitization** → All metadata stripped
5. **Re-encoding** → Saved as JPEG (quality=98)
6. **Storage** → Clean JPEG stored in S3

**Result:** Professional quality JPEG with zero metadata, safe for web delivery.

## Troubleshooting

### Issue: Package too large (>50MB)

Lambda has a 50MB limit for direct upload, 250MB for S3 upload.

**Solution 1:** Use Lambda Layers (Option 3 above)

**Solution 2:** Remove unnecessary files:

```bash
cd package
# Remove test files
find . -type d -name "tests" -exec rm -rf {} +
# Remove .pyc files
find . -name "*.pyc" -delete
# Remove dist-info
find . -type d -name "*.dist-info" -exec rm -rf {} +
```

### Issue: ImportError after deployment

Make sure you're packaging the correct Python version's site-packages.

**Check Lambda runtime:**
```bash
aws lambda get-function-configuration --function-name galerly-api | grep Runtime
```

**Use matching Python version locally:**
```bash
# If Lambda uses Python 3.11
python3.11 -m venv venv
```

### Issue: Still getting rawpy error

**Verify deployment:**
```bash
# Check package size
aws lambda get-function --function-name galerly-api | grep CodeSize

# Check last update
aws lambda get-function --function-name galerly-api | grep LastModified
```

**Test in Lambda console:**
1. Go to AWS Lambda Console
2. Open galerly-api function
3. Test → Create new test event
4. Send a request with DNG file

## Performance Notes

- **Cold Start:** First RAW upload may take 3-5 seconds (Lambda loading dependencies)
- **Warm Start:** Subsequent uploads take 1-2 seconds
- **File Size:** DNG files 20-50MB → JPEG 3-8MB (quality=98)
- **Processing:** DNG → RGB conversion takes 1-2 seconds per file

## Security

All RAW files are:
- ✅ Scanned for malicious code (first 100KB checked)
- ✅ Converted to RGB (strips RAW-specific exploits)
- ✅ Re-encoded to JPEG (removes all metadata)
- ✅ Quality preserved (quality=98, near-lossless)

## Testing

After deployment, test with:

```bash
# Check if rawpy is available
aws lambda invoke \
    --function-name galerly-api \
    --payload '{"path":"/v1/health","httpMethod":"GET"}' \
    response.json

cat response.json
```

Then upload a DNG file through the web interface.

## Estimated Deployment Time

- **Option 1 (Script):** 2-3 minutes
- **Option 2 (Manual):** 5-10 minutes
- **Option 3 (Layers):** 10-15 minutes (one-time setup, then 30 seconds for updates)

---

**Ready to deploy?** Run the script:

```bash
cd backend
chmod +x deploy-lambda.sh
./deploy-lambda.sh
```

After deployment, DNG and all RAW formats will work! 📸✨

