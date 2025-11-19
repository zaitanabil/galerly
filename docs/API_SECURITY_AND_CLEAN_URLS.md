# API Security & Clean URLs Setup

**Last Updated:** December 2025

---

## 1. Obfuscated API Endpoint

### Why Obfuscate?
Using a hard-to-guess API endpoint adds a layer of security through obscurity. While not a replacement for proper authentication, it helps prevent:
- Automated scanning
- Casual API discovery
- Bot attacks on predictable endpoints

### Your Obfuscated Endpoint

**Production API:**
```
https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1
```

**Local Development:**
```
http://localhost:8000/api/v1
```

### API Gateway Configuration

In AWS API Gateway, you need to configure the custom domain to route this path:

1. **Go to API Gateway Console**
2. **Custom Domain Names** → `api.galerly.com`
3. **API mappings:**
   ```
   Path: /xb667e3fa92f9776468017a9758f31ba4/v1
   API: [Your API Name]
   Stage: prod
   ```

**OR** if you want to keep the API Gateway mapping simple:

1. **API mappings:**
   ```
   Path: /xb667e3fa92f9776468017a9758f31ba4
   API: [Your API Name]
   Stage: prod
   ```

2. **In Lambda/API code**, your routes would be under `/xb667e3fa92f9776468017a9758f31ba4/v1/*`

### Important Security Notes

⚠️ **Never commit this token to public repositories** (it's already in your private repo)
⚠️ **Change it if compromised** - just regenerate with:
```bash
python3 -c "import secrets; print('x' + secrets.token_hex(16))"
```
⚠️ **Use HTTPS only** - Already configured
⚠️ **Implement rate limiting** - Add AWS WAF rules
⚠️ **Monitor access logs** - Check CloudWatch for unusual patterns

---

## 2. Clean URLs (Remove .html Extensions)

### Goal
Transform URLs from:
- ❌ `https://galerly.com/auth.html`
- ❌ `https://galerly.com/dashboard.html`

To:
- ✅ `https://galerly.com/auth`
- ✅ `https://galerly.com/dashboard`

### Implementation: CloudFront Functions

CloudFront Functions are lightweight, cost-effective, and perfect for URL rewrites.

#### Step 1: Create CloudFront Function

1. **Go to AWS CloudFront Console**
2. **Functions** (left sidebar)
3. **Create function**
   - Name: `galerly-url-rewrite`
   - Runtime: `cloudfront-js-1.0`
4. **Copy the code from:** `cloudfront/url-rewrite-function.js`
5. **Test the function:**
   ```json
   {
     "version": "1.0",
     "context": {
       "eventType": "viewer-request"
     },
     "viewer": {
       "ip": "1.2.3.4"
     },
     "request": {
       "method": "GET",
       "uri": "/auth",
       "querystring": {},
       "headers": {},
       "cookies": {}
     }
   }
   ```
   Expected output: `uri` should be `/auth.html`

6. **Publish the function**

#### Step 2: Associate Function with CloudFront Distribution

1. **Go to your CloudFront distribution**
2. **Behaviors tab**
3. **Edit the default behavior**
4. **Function associations:**
   - Viewer request: Select `galerly-url-rewrite`
5. **Save changes**

#### Step 3: Wait for Deployment (5-10 minutes)

CloudFront will deploy the function to all edge locations.

#### Step 4: Test

```bash
# Should load auth.html
curl -I https://galerly.com/auth

# Should load dashboard.html
curl -I https://galerly.com/dashboard

# Should load index.html
curl -I https://galerly.com/

# With extension should still work
curl -I https://galerly.com/auth.html
```

### Supported Clean URLs

The function supports these routes:
- `/` → `/index.html`
- `/auth` → `/auth.html`
- `/dashboard` → `/dashboard.html`
- `/gallery` → `/gallery.html`
- `/new-gallery` → `/new-gallery.html`
- `/client-gallery` → `/client-gallery.html`
- `/client-dashboard` → `/client-dashboard.html`
- `/profile-settings` → `/profile-settings.html`
- `/portfolio-settings` → `/portfolio-settings.html`
- `/portfolio` → `/portfolio.html`
- `/photographers` → `/photographers.html`
- `/pricing` → `/pricing.html`
- `/billing` → `/billing.html`
- `/contact` → `/contact.html`
- `/faq` → `/faq.html`
- `/privacy` → `/privacy.html`
- `/legal-notice` → `/legal-notice.html`

### Update Internal Links

Update all your HTML files to use clean URLs:

**Before:**
```html
<a href="/auth.html">Sign In</a>
<a href="/dashboard.html">Dashboard</a>
```

**After:**
```html
<a href="/auth">Sign In</a>
<a href="/dashboard">Dashboard</a>
```

**JavaScript redirects:**
```javascript
// Before
window.location.href = '/dashboard.html';

// After
window.location.href = '/dashboard';
```

---

## 3. Alternative: S3 Redirect Rules

If you're not using CloudFront or prefer S3 redirect rules:

```xml
<RoutingRules>
  <RoutingRule>
    <Condition>
      <KeyPrefixEquals>auth</KeyPrefixEquals>
    </Condition>
    <Redirect>
      <ReplaceKeyWith>auth.html</ReplaceKeyWith>
    </Redirect>
  </RoutingRule>
  <RoutingRule>
    <Condition>
      <KeyPrefixEquals>dashboard</KeyPrefixEquals>
    </Condition>
    <Redirect>
      <ReplaceKeyWith>dashboard.html</ReplaceKeyWith>
    </Redirect>
  </RoutingRule>
  <!-- Add more rules for each route -->
</RoutingRules>
```

⚠️ **Note:** S3 redirect rules are less flexible and can be tedious with many routes. CloudFront Functions are recommended.

---

## 4. SEO Considerations

### Canonical URLs

Update all HTML files to use clean canonical URLs:

```html
<link rel="canonical" href="https://galerly.com/auth" />
```

### Sitemap

Update `sitemap.xml` to use clean URLs:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://galerly.com/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://galerly.com/auth</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://galerly.com/photographers</loc>
    <priority>0.9</priority>
  </url>
  <!-- Add all routes -->
</urlset>
```

### Robots.txt

```txt
User-agent: *
Allow: /

Sitemap: https://galerly.com/sitemap.xml
```

---

## 5. Cost Comparison

### CloudFront Functions
- **Cost:** $0.10 per 1 million invocations
- **Performance:** <1ms latency
- **Best for:** URL rewrites, header manipulation
- **Recommended:** ✅ Yes

### Lambda@Edge
- **Cost:** $0.60 per 1 million invocations + compute time
- **Performance:** Higher latency
- **Best for:** Complex logic, external API calls
- **Recommended:** ❌ Overkill for URL rewrites

### S3 Redirect Rules
- **Cost:** Free
- **Performance:** Additional redirect (301/302)
- **Best for:** Simple redirects
- **Recommended:** ⚠️ Acceptable but adds redirect overhead

---

## 6. Testing Checklist

After deploying:

- [ ] `/auth` loads auth page
- [ ] `/dashboard` loads dashboard
- [ ] `/` loads index page
- [ ] Direct `.html` access still works (backward compatibility)
- [ ] Images and assets load correctly
- [ ] CSS and JavaScript load correctly
- [ ] API calls work with obfuscated endpoint
- [ ] No 404 errors in browser console
- [ ] Social sharing uses clean URLs
- [ ] Email links use clean URLs

---

## 7. Monitoring & Security

### CloudWatch Logs

Monitor CloudFront function execution:
```bash
aws logs tail /aws/cloudfront/function/galerly-url-rewrite --follow
```

### API Access Monitoring

Check for unauthorized API access attempts:
```bash
aws logs filter-pattern 'API Gateway' \
  --log-group-name '/aws/lambda/galerly-api' \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Rate Limiting with AWS WAF

Create WAF rule to prevent abuse:

1. **Go to AWS WAF Console**
2. **Create web ACL**
3. **Add rule:**
   - Name: `RateLimitAPI`
   - Type: Rate-based rule
   - Rate limit: 2000 requests per 5 minutes per IP
   - Action: Block

4. **Associate with CloudFront distribution**

---

## 8. Emergency Rollback

If something breaks:

### Revert API Endpoint
```javascript
// In frontend/js/config.js
API_BASE_URL: 'https://api.galerly.com/api/v1'
```

### Disable CloudFront Function
1. Go to CloudFront distribution
2. Behaviors → Edit
3. Function associations → None
4. Save

---

## 9. Future Enhancements

### API Endpoint Rotation
Rotate the obfuscated path every 6 months:
```bash
# Generate new token
python3 -c "import secrets; print('x' + secrets.token_hex(16))"

# Update config.js
# Update API Gateway mapping
# Deploy
```

### Advanced URL Routing
For SPA-style routing (all routes to index.html):
```javascript
// Advanced CloudFront Function
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // If no file extension, route to index.html (SPA mode)
    if (!uri.includes('.')) {
        request.uri = '/index.html';
    }
    
    return request;
}
```

---

**Questions?** Refer to:
- CloudFront Functions: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html
- API Gateway Custom Domains: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html

