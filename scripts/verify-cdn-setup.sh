#!/bin/bash

echo "🔍 CloudFront CDN Setup Verification"
echo "====================================="
echo ""

# Check 1: ACM Certificate
echo "1️⃣  Checking SSL Certificate..."
CERT_STATUS=$(aws acm list-certificates --region us-east-1 --query "CertificateSummaryList[?DomainName=='cdn.galerly.com'].Status" --output text 2>/dev/null)
if [ "$CERT_STATUS" = "ISSUED" ]; then
    echo "   ✅ SSL Certificate: ISSUED"
else
    echo "   ⏳ SSL Certificate: $CERT_STATUS (waiting for validation)"
fi
echo ""

# Check 2: CloudFront Distribution
echo "2️⃣  Checking CloudFront Distribution..."
CF_STATUS=$(aws cloudfront get-distribution --id E3P0EU1X4VGR58 --query 'Distribution.Status' --output text 2>/dev/null)
if [ "$CF_STATUS" = "Deployed" ]; then
    echo "   ✅ CloudFront: Deployed and ready"
else
    echo "   ⏳ CloudFront: $CF_STATUS (still deploying)"
fi
echo ""

# Check 3: DNS Records
echo "3️⃣  Checking DNS Records..."
CDN_CNAME=$(dig +short cdn.galerly.com | grep cloudfront)
if [ -n "$CDN_CNAME" ]; then
    echo "   ✅ cdn.galerly.com → $CDN_CNAME"
else
    echo "   ❌ cdn.galerly.com not pointing to CloudFront"
fi

SSL_CNAME=$(dig +short _118095ab4a92e6bb47c83659d666bb0b.cdn.galerly.com)
if [ -n "$SSL_CNAME" ]; then
    echo "   ✅ SSL validation CNAME found"
else
    echo "   ❌ SSL validation CNAME not found"
fi
echo ""

# Check 4: Lambda@Edge Function
echo "4️⃣  Checking Lambda@Edge Function..."
LAMBDA_STATE=$(aws lambda get-function --function-name galerly-image-resize-edge --region us-east-1 --query 'Configuration.State' --output text 2>/dev/null)
if [ "$LAMBDA_STATE" = "Active" ]; then
    echo "   ✅ Lambda@Edge: Active"
else
    echo "   ⚠️  Lambda@Edge: $LAMBDA_STATE"
fi
echo ""

# Check 5: GitHub Secret
echo "5️⃣  Checking GitHub Secrets (manual verification needed)..."
echo "   Please verify in GitHub:"
echo "   Settings → Secrets and variables → Actions"
echo "   ✓ CDN_DOMAIN = cdn.galerly.com"
echo ""

# Summary
echo "====================================="
echo "📊 Summary"
echo "====================================="
if [ "$CERT_STATUS" = "ISSUED" ] && [ "$CF_STATUS" = "Deployed" ] && [ -n "$CDN_CNAME" ]; then
    echo "✅ Setup is complete and ready!"
    echo ""
    echo "🧪 Test URLs (after next deployment):"
    echo "   https://cdn.galerly.com/resize/800x600/test.jpg"
    echo ""
    echo "🚀 Next: Deploy backend to apply CDN_DOMAIN"
    echo "   git push origin main"
else
    echo "⏳ Setup in progress. Run this script again in 5 minutes."
fi
