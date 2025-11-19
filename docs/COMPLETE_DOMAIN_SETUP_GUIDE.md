# Complete Domain Setup Guide for Galerly.com

**Last Updated:** November 2025  
**Domain:** galerly.com (purchased from Namecheap)

This guide documents the complete process of setting up the custom domain `galerly.com` for both frontend (CloudFront) and backend (API Gateway), including SSL certificates, DNS configuration, clean URLs, and API obfuscation.

---

## Table of Contents

1. [Overview](#overview)
2. [Frontend Setup (galerly.com)](#frontend-setup-galerlycom)
3. [Backend API Setup (api.galerly.com)](#backend-api-setup-apigalerlycom)
4. [Clean URLs Implementation](#clean-urls-implementation)
5. [API Security Obfuscation](#api-security-obfuscation)
6. [DNS Configuration Summary](#dns-configuration-summary)
7. [Testing & Verification](#testing--verification)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Architecture
- **Frontend:** S3 bucket → CloudFront CDN → galerly.com
- **Backend:** Lambda/API Gateway → api.galerly.com
- **DNS Provider:** Namecheap
- **SSL Certificates:** AWS Certificate Manager (ACM)
- **Clean URLs:** CloudFront Functions
- **API Path:** Obfuscated with unique hash

### Key URLs
- Frontend: `https://galerly.com`
- API: `https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1`

---

## Frontend Setup (galerly.com)

### Step 1: Request SSL Certificate in ACM

**Region:** Must be in **us-east-1 (N. Virginia)** for CloudFront

1. Go to AWS Certificate Manager: https://console.aws.amazon.com/acm/home?region=us-east-1
2. Click **"Request certificate"**
3. Select **"Request a public certificate"**
4. Configure certificate:
   - Domain names:
     - `galerly.com`
     - `www.galerly.com`
   - Validation method: **DNS validation - recommended**
   - Key algorithm: **RSA 2048**
   - Allow export: **Disable export**
5. Click **"Request"**

### Step 2: Validate Certificate via DNS

1. After requesting, ACM will show **CNAME records** for validation
2. You'll see two records (one for each domain)
3. Copy each CNAME record

**Add to Namecheap:**
1. Go to Namecheap → Domain List → galerly.com → **Manage** → **Advanced DNS**
2. Click **"Add New Record"**
3. For each validation record:
   - **Type:** CNAME Record
   - **Host:** `_abc123def` (extract subdomain part, remove `.galerly.com`)
   - **Value:** `_something.acm-validations.aws.` (paste full value)
   - **TTL:** Automatic

4. **Save all changes**
5. Wait 5-30 minutes for validation
6. Check ACM - status should change to **"Issued"**

### Step 3: Create CloudFront Distribution

1. Go to CloudFront Console: https://console.aws.amazon.com/cloudfront
2. Click **"Create distribution"**
3. **Distribution settings:**
   - **Distribution name:** `galerly-frontend` (or any name)
   - **Description:** "Frontend distribution for galerly.com"
   - **Distribution type:** Single website or app
   - **Route 53 managed domain:** Skip this (using Namecheap)

4. Click **"Next"** or **"Continue"**

### Step 4: Configure Origin

**Origin Type:** Select **"Other"** (not "Amazon S3")
- Why? Because we're using S3 website endpoint, not REST API endpoint

**Origin settings:**
- **Custom origin:** `galerly-frontend-app.s3-website-us-east-1.amazonaws.com`
- **Origin path:** (leave empty)
- **Origin settings:** Use recommended origin settings

**Cache settings:**
- **Viewer protocol policy:** Redirect HTTP to HTTPS
- **Allowed HTTP methods:** GET, HEAD
- **Cache policy:** CachingOptimized

### Step 5: Configure Security (WAF)

- Select **"Do not enable security protections"**
- You can add AWS WAF later if needed (~$14/month minimum)

### Step 6: Wait for Initial Deployment

- CloudFront will create the distribution
- Status: **"Deploying"** (takes 5-15 minutes)
- You'll get a CloudFront domain like: `d2z19tvf697uie.cloudfront.net`

### Step 7: Add Custom Domain and SSL to CloudFront

Once deployed:

1. Go to your distribution → **"General"** tab → Click **"Edit"**
2. **Alternate domain names (CNAMEs):**
   - Click "Add domain" → Enter: `galerly.com`
   - Click "Add domain" → Enter: `www.galerly.com`
3. **Custom SSL certificate:**
   - Select your `galerly.com` certificate from the dropdown
4. **Default root object:** (may not be available in newer UI, skip if not present)
5. Click **"Save changes"**
6. Wait for deployment (5-15 minutes)

### Step 8: Configure DNS in Namecheap

1. Go to Namecheap → galerly.com → Advanced DNS
2. **Remove** any existing A or CNAME records for `@` and `www`
3. Add these CNAME records:

```
Type    Host    Value                           TTL
CNAME   @       d2z19tvf697uie.cloudfront.net  Automatic
CNAME   www     d2z19tvf697uie.cloudfront.net  Automatic
```

**Note:** Replace `d2z19tvf697uie.cloudfront.net` with your actual CloudFront domain

4. Save all changes
5. Wait 5-30 minutes for DNS propagation

---

## Backend API Setup (api.galerly.com)

### Step 1: Request SSL Certificate for API

**Region:** Use the **same region as your API Gateway** (likely us-east-1)

1. Go to AWS Certificate Manager in your API region
2. Click **"Request certificate"**
3. Configure:
   - Domain name: `api.galerly.com`
   - Validation method: **DNS validation**
   - Key algorithm: **RSA 2048**
   - Allow export: **Disable export**
4. Click **"Request"**

### Step 2: Validate API Certificate

1. Copy the CNAME record from ACM
2. Add to Namecheap DNS:
   - **Type:** CNAME Record
   - **Host:** `_abc123def.api` (extract subdomain)
   - **Value:** `_something.acm-validations.aws.`
   - **TTL:** Automatic
3. Wait 5-30 minutes for validation
4. Check ACM - status should be **"Issued"**

### Step 3: Create API Gateway Custom Domain

1. Go to API Gateway Console
2. Click **"Custom domain names"** (left sidebar)
3. Click **"Create"**
4. Configure:
   - **Domain name:** `api.galerly.com`
   - **Domain type:** Public
   - **Routing mode:** API mappings only
   - **API endpoint type:** Regional (recommended)
   - **IP address type:** IPv4
   - **Minimum TLS version:** TLS 1.2
   - **Mutual TLS authentication:** Leave unchecked
   - **ACM certificate:** Select your `api.galerly.com` certificate
5. Click **"Create domain name"**

### Step 4: Configure API Mappings

After creating the custom domain:

1. In the custom domain page, find **"API mappings"** section
2. Click **"Configure API mappings"** or **"Add mapping"**
3. Fill in:
   - **API:** Select your API (your Lambda API)
   - **Stage:** `prod` (or your production stage name)
   - **Path:** `xb667e3fa92f9776468017a9758f31ba4/v1`
     - This is the obfuscated path for security
4. Click **"Save"**

### Step 5: Configure DNS for API

1. Copy the **API Gateway domain name** (looks like: `d-xxxxxxxxx.execute-api.us-east-1.amazonaws.com`)
2. Go to Namecheap → galerly.com → Advanced DNS
3. Add CNAME record:

```
Type    Host    Value                                           TTL
CNAME   api     d-xxxxxxxxx.execute-api.us-east-1.amazonaws.com  Automatic
```

4. Save changes
5. Wait 5-30 minutes for DNS propagation

---

## Clean URLs Implementation

This removes `.html` extensions from URLs (e.g., `/auth` instead of `/auth.html`).

### Step 1: Create CloudFront Function

1. Go to CloudFront Console → **"Functions"** (left sidebar)
2. Click **"Create function"**
3. Configure:
   - **Name:** `galerly-url-rewrite`
   - **Description:** "Rewrites URLs to remove .html extensions and handle index.html"
   - **Runtime:** cloudfront-js-2.0
4. Click **"Create function"**

### Step 2: Add Function Code

Copy and paste this code into the function editor:

```javascript
// CloudFront Function to handle clean URLs (remove .html extension)
// This function runs on viewer request

function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // List of valid routes (without .html extension)
    var validRoutes = [
        '/index',
        '/auth',
        '/dashboard',
        '/gallery',
        '/new-gallery',
        '/client-gallery',
        '/client-dashboard',
        '/profile-settings',
        '/portfolio-settings',
        '/portfolio',
        '/photographers',
        '/pricing',
        '/billing',
        '/contact',
        '/faq',
        '/privacy',
        '/legal-notice'
    ];
    
    // If URI ends with '/', append 'index.html'
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
    }
    // If URI is exactly a valid route (no extension), append '.html'
    else if (validRoutes.includes(uri)) {
        request.uri += '.html';
    }
    // If URI doesn't have an extension and isn't in validRoutes, try appending .html
    else if (!uri.includes('.') && !uri.includes('view/')) {
        request.uri += '.html';
    }
    
    return request;
}
```

5. Click **"Save changes"**
6. Click **"Publish"** (important!)
7. Verify status shows **"Published"**

### Step 3: Associate Function with CloudFront

1. Go to your CloudFront distribution
2. Go to **"Behaviors"** tab
3. Select the **"Default (*)"** behavior
4. Click **"Edit"**
5. Scroll to **"Function associations"** section
6. For **"Viewer request":**
   - **Function type:** CloudFront Functions
   - **Function ARN / Name:** Select `galerly-url-rewrite`
7. Click **"Save changes"**
8. Wait 5-15 minutes for deployment

### How It Works

- Request: `galerly.com/auth` → CloudFront Function → S3: `/auth.html`
- Request: `galerly.com/` → CloudFront Function → S3: `/index.html`
- Request: `galerly.com/css/style.css` → No change (has extension)

---

## API Security Obfuscation

To prevent easy guessing of API endpoints, a unique hash is used in the URL path.

### Obfuscated API Path

**Format:** `https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1`

**Components:**
- `api.galerly.com` - Custom domain
- `xb667e3fa92f9776468017a9758f31ba4` - Random unique hash (impossible to guess)
- `v1` - API version

### Implementation

**Frontend Configuration (`frontend/js/config.js`):**

```javascript
const API_BASE_URL = 'https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1';
```

**Backend Configuration (`backend/.env`):**

```bash
FRONTEND_URL=https://galerly.com
FROM_EMAIL=noreply@galerly.com
```

### Security Benefits

1. **Obscurity:** API path is not easily guessable
2. **No standard patterns:** Doesn't follow `/api/v1` conventions
3. **Unique identifier:** Acts as an additional layer of protection
4. **Can be rotated:** Easy to generate a new hash and redeploy

**Important:** Keep this path confidential. Don't expose it in public documentation.

---

## DNS Configuration Summary

### Final Namecheap DNS Records for galerly.com

```
Type    Host    Value                                           TTL         Purpose
CNAME   @       d2z19tvf697uie.cloudfront.net                  Automatic   Frontend root domain
CNAME   www     d2z19tvf697uie.cloudfront.net                  Automatic   Frontend www subdomain
CNAME   api     d-xxxxxxxxx.execute-api.us-east-1.amazonaws.com Automatic   Backend API
CNAME   _val1   _something.acm-validations.aws.                 Automatic   SSL validation (can delete after)
CNAME   _val2   _something.acm-validations.aws.                 Automatic   SSL validation (can delete after)
CNAME   _val3.api _something.acm-validations.aws.               Automatic   SSL validation (can delete after)
```

**Note:** 
- Replace CloudFront and API Gateway domains with your actual values
- Validation CNAMEs can be deleted after certificates are issued, but it's safe to keep them

---

## Testing & Verification

### Frontend Tests

Test these URLs in your browser:

1. **Root domain:**
   - `https://galerly.com` → Should load homepage
   - `https://www.galerly.com` → Should load homepage

2. **Clean URLs:**
   - `https://galerly.com/auth` → Should load auth page
   - `https://galerly.com/dashboard` → Should load dashboard
   - `https://galerly.com/photographers` → Should load photographers page

3. **Static assets:**
   - Check that CSS, JS, and images load correctly
   - Open browser DevTools → Network tab → Verify no 404s

4. **HTTPS:**
   - Verify padlock icon in browser
   - Check certificate details → Should show `galerly.com`

5. **HTTP redirect:**
   - Try `http://galerly.com` → Should redirect to `https://galerly.com`

### Backend API Tests

Test API endpoints:

```bash
# Health check (if you have one)
curl https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1/health

# Authentication endpoint
curl -X POST https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

Expected responses:
- ✅ Valid JSON responses
- ✅ HTTPS connection
- ✅ Correct CORS headers (if applicable)
- ❌ No SSL errors
- ❌ No 504/502 Gateway errors

### DNS Propagation Check

Check if DNS has propagated globally:

```bash
# Check from your location
nslookup galerly.com
nslookup www.galerly.com
nslookup api.galerly.com

# Check globally (use online tools)
# https://dnschecker.org
# https://www.whatsmydns.net
```

---

## Troubleshooting

### Issue: 504 Gateway Timeout on Frontend

**Symptoms:** 
- Visiting `galerly.com` shows CloudFront 504 error
- "We can't connect to the server"

**Cause:** CloudFront can't connect to S3 origin

**Solution:**
1. Go to CloudFront → Your distribution → **Origins** tab
2. Edit the origin
3. Verify:
   - **Origin domain:** `galerly-frontend-app.s3-website-us-east-1.amazonaws.com` (website endpoint)
   - **Protocol:** HTTP only (not HTTPS)
   - **NOT** using REST API endpoint (`s3.amazonaws.com`)
4. Save and wait 5-10 minutes for deployment

**Verify S3 bucket:**
1. Go to S3 → `galerly-frontend-app` → **Properties**
2. Scroll to "Static website hosting"
3. Ensure it's **Enabled**
4. Index document: `index.html`

### Issue: Certificate Validation Stuck at "Pending"

**Symptoms:**
- ACM certificate shows "Pending validation" for >30 minutes

**Solution:**
1. Go to ACM → Click on your certificate
2. Check if there are **two CNAME records** (for galerly.com and www.galerly.com)
3. Verify **both** CNAMEs are added to Namecheap
4. Check CNAME format in Namecheap:
   - **Host:** Only the subdomain part (e.g., `_abc123` not `_abc123.galerly.com`)
   - **Value:** Full ACM validation value with trailing dot
5. Wait another 30-60 minutes
6. Try clicking "Refresh" in ACM

### Issue: DNS Not Propagating

**Symptoms:**
- `galerly.com` not resolving after >1 hour
- `nslookup` returns NXDOMAIN

**Solution:**
1. Check Namecheap DNS records are saved
2. Verify no typos in Host or Value fields
3. Check Namecheap nameservers are active:
   ```bash
   nslookup -type=NS galerly.com
   ```
4. Wait 24-48 hours for full global propagation
5. Clear your local DNS cache:
   - Mac: `sudo dscacheutil -flushcache`
   - Windows: `ipconfig /flushdns`
   - Linux: `sudo systemd-resolve --flush-caches`

### Issue: API 403 Forbidden

**Symptoms:**
- API calls to `api.galerly.com` return 403 Forbidden

**Solution:**
1. Check API Gateway custom domain mapping:
   - Path should be: `xb667e3fa92f9776468017a9758f31ba4/v1`
   - API and Stage should be correct
2. Check Lambda permissions (if using Lambda)
3. Check API Gateway authorization settings
4. Verify CORS configuration (if making browser requests)

### Issue: Clean URLs Not Working

**Symptoms:**
- `/auth` returns 404
- `/auth.html` works fine

**Solution:**
1. Check CloudFront Function is **Published** (not just saved)
2. Check Function is **associated** with distribution:
   - Distribution → Behaviors → Default → Function associations → Viewer request
3. Check validRoutes array in function includes your route
4. Wait 5-15 minutes for CloudFront deployment
5. Clear CloudFront cache (create invalidation for `/*`)

### Issue: Mixed Content Warnings

**Symptoms:**
- Browser console shows "Mixed Content" warnings
- Some assets fail to load

**Solution:**
1. Check all internal links use relative paths or HTTPS:
   - ✅ `/css/style.css` or `https://galerly.com/css/style.css`
   - ❌ `http://galerly.com/css/style.css`
2. Check API calls in JavaScript use HTTPS
3. Update any hardcoded HTTP URLs to HTTPS

### Issue: API Endpoint in Frontend Not Working

**Symptoms:**
- Frontend can't connect to API
- CORS errors or network errors

**Solution:**
1. Check `frontend/js/config.js`:
   ```javascript
   const API_BASE_URL = 'https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1';
   ```
2. Deploy updated frontend to S3
3. Invalidate CloudFront cache
4. Check browser console for exact error
5. Test API endpoint directly with curl

---

## Maintenance & Updates

### Updating Frontend

1. Build/prepare your frontend files
2. Upload to S3 bucket: `galerly-frontend-app`
3. Create CloudFront invalidation:
   - Go to CloudFront → Your distribution → **Invalidations** tab
   - Create invalidation for `/*` (all files)
   - Wait 5-10 minutes

### Rotating API Obfuscation Hash

If you need to change the API path for security:

1. Generate a new random hash:
   ```bash
   openssl rand -hex 20
   # Output: new_random_hash_here
   ```

2. Update `frontend/js/config.js`:
   ```javascript
   const API_BASE_URL = 'https://api.galerly.com/new_random_hash_here/v1';
   ```

3. Update API Gateway custom domain mapping:
   - Edit mapping path to: `new_random_hash_here/v1`

4. Deploy frontend changes
5. Test thoroughly

### Adding New Clean URL Routes

When you add new pages:

1. Add the route to CloudFront Function:
   ```javascript
   var validRoutes = [
       // ... existing routes
       '/new-page',
       '/another-page'
   ];
   ```

2. Save and **Publish** the function
3. Wait for CloudFront deployment (5-15 minutes)

### Renewing SSL Certificates

**Good news:** ACM certificates auto-renew!

- ACM automatically renews certificates before expiry
- No action needed if DNS validation records remain
- Check certificate expiry in ACM console

---

## Cost Breakdown

### AWS Services

**CloudFront:**
- First 1TB/month: ~$0.085/GB = ~$85/month for 1TB
- First 10TB: Cheaper per GB
- First 10 million requests free (for 12 months free tier)

**API Gateway:**
- First 1 million requests free (12 months)
- After: ~$3.50 per million requests

**ACM (SSL Certificates):**
- **FREE** for public certificates
- Auto-renewal included

**CloudFront Functions:**
- First 2 million invocations free
- After: $0.10 per 1 million invocations

**Route 53 (if you migrate DNS):**
- $0.50 per hosted zone per month
- Not required (using Namecheap DNS)

### Namecheap

**Domain Registration:**
- galerly.com: ~$10-15/year
- Renewal: Check Namecheap pricing

**Total Estimated Monthly Cost:**
- Low traffic (<100k requests): ~$5-10/month
- Medium traffic (1M requests): ~$20-50/month
- High traffic (10M requests): ~$100-200/month

---

## Additional Resources

### AWS Documentation
- [CloudFront User Guide](https://docs.aws.amazon.com/cloudfront/)
- [API Gateway Custom Domains](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html)
- [ACM User Guide](https://docs.aws.amazon.com/acm/)
- [CloudFront Functions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html)

### Namecheap Documentation
- [How to set up DNS records](https://www.namecheap.com/support/knowledgebase/article.aspx/319/2237/how-can-i-set-up-an-a-address-record-for-my-domain/)
- [CNAME Record Setup](https://www.namecheap.com/support/knowledgebase/article.aspx/9646/2237/how-to-create-a-cname-record-for-your-domain/)

### Testing Tools
- [DNS Checker](https://dnschecker.org)
- [SSL Labs](https://www.ssllabs.com/ssltest/) - Test SSL configuration
- [CloudFlare Speed Test](https://speed.cloudflare.com/) - Test CDN performance

---

## Security Checklist

✅ **HTTPS Everywhere:**
- All traffic redirected from HTTP to HTTPS
- Valid SSL certificates for all domains
- TLS 1.2 minimum

✅ **API Security:**
- Obfuscated API endpoint
- No predictable patterns
- CORS properly configured (check backend)

✅ **CloudFront Security:**
- Origin access restricted to CloudFront
- Default root object set
- Error pages configured (optional)

✅ **DNS Security:**
- DNSSEC enabled (optional, check Namecheap)
- No wildcard records exposing subdomains

✅ **S3 Security:**
- Bucket not publicly accessible (served via CloudFront only)
- Bucket policy restricts access
- Versioning enabled (optional)

---

## Conclusion

You now have a fully configured production domain setup with:

✅ Custom domain: `galerly.com`  
✅ SSL/HTTPS encryption  
✅ CloudFront CDN for fast global delivery  
✅ Clean URLs (no .html extensions)  
✅ Obfuscated API endpoint  
✅ API subdomain: `api.galerly.com`  
✅ Auto-renewing SSL certificates  

The setup is production-ready, secure, and scalable.

**Next Steps:**
1. Monitor CloudFront and API Gateway metrics in AWS Console
2. Set up CloudWatch alarms for errors/high traffic
3. Consider adding AWS WAF if you experience attacks
4. Implement caching strategies for API responses
5. Set up proper logging and analytics

---

**Last Updated:** November 2025  
**Maintained by:** Galerly Development Team  
**Version:** 1.0
