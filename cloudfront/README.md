# CloudFront Function Automated Deployment

This directory contains automation for deploying CloudFront functions via GitHub Actions.

## Overview

The CloudFront URL rewrite function is now automatically deployed whenever you push to the `main` branch. This ensures that routing changes (like 404 redirects) are always in sync with your codebase.

## Files

- **`url-rewrite-function.js`**: The CloudFront function code that handles URL rewrites and 404 redirects
- **`../backend/update_cloudfront_function.py`**: Python script that updates the CloudFront function via AWS API

## How It Works

### Automatic Deployment (GitHub Actions)

1. You push changes to `main` branch
2. GitHub Actions workflow runs
3. Backend (Lambda) is deployed
4. Frontend (S3) is deployed
5. **CloudFront function is automatically updated** ✨
6. Changes are live immediately

### Manual Deployment (if needed)

If you need to manually update the CloudFront function:

```bash
cd backend
python3 update_cloudfront_function.py
```

Or via AWS Console:
1. Go to: https://console.aws.amazon.com/cloudfront/v3/home#/functions
2. Select function: `galerly-url-rewrite`
3. Edit code
4. Save changes
5. **Publish** (important!)

## Setup Requirements

### GitHub Secrets

You need to add this secret to your GitHub repository:

```
CLOUDFRONT_FUNCTION_NAME=galerly-url-rewrite
```

**How to add:**
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CLOUDFRONT_FUNCTION_NAME`
4. Value: `galerly-url-rewrite` (or your function name)
5. Click "Add secret"

### AWS IAM Permissions

Your GitHub Actions AWS user needs these CloudFront permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:DescribeFunction",
        "cloudfront:UpdateFunction",
        "cloudfront:PublishFunction"
      ],
      "Resource": "arn:aws:cloudfront::*:function/galerly-url-rewrite"
    }
  ]
}
```

## What the Function Does

The URL rewrite function:

1. **Handles clean URLs**: `/auth` → `/auth.html`
2. **Serves index for root**: `/` → `/index.html`
3. **Preserves static assets**: CSS, JS, images pass through unchanged
4. **Redirects invalid routes to 404**: `/nonexistent` → `/404.html`

## Valid Routes

The function recognizes these routes (defined in `url-rewrite-function.js`):

- `/index` (home page)
- `/auth` (login/register)
- `/reset-password`
- `/dashboard` (photographer dashboard)
- `/gallery` (gallery detail)
- `/new-gallery` (create gallery)
- `/client-gallery` (client view)
- `/client-dashboard` (client dashboard)
- `/profile-settings`
- `/portfolio-settings`
- `/portfolio`
- `/photographers`
- `/pricing`
- `/billing`
- `/contact`
- `/faq`
- `/privacy`
- `/legal-notice`
- `/404` (error page)

**Any other route** → Redirects to `/404`

## Testing

After deployment, test the 404 redirect:

```bash
# Should show the 404 page
curl -I https://galerly.com/nonexistent-page

# Should show the auth page
curl -I https://galerly.com/auth

# Should show the home page
curl -I https://galerly.com/
```

## Troubleshooting

### Function not updating

1. Check GitHub Actions logs for errors
2. Verify `CLOUDFRONT_FUNCTION_NAME` secret is set
3. Verify AWS IAM permissions
4. Check that function exists in AWS Console

### 404 not working

1. Verify function is **Published** (not just saved)
2. Check CloudFront distribution has the function associated
3. Wait 1-2 minutes for CloudFront to propagate changes

### Script errors

```bash
# Run locally to test
cd backend
export CLOUDFRONT_FUNCTION_NAME=galerly-url-rewrite
python3 update_cloudfront_function.py
```

## Architecture

```
┌─────────────────┐
│  GitHub Push    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ GitHub Actions  │
│  - Backend      │
│  - Frontend     │
│  - CloudFront   │ ← New!
└────────┬────────┘
         │
         v
┌─────────────────┐
│   AWS Account   │
│                 │
│ ┌─────────────┐ │
│ │   Lambda    │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │     S3      │ │
│ └─────────────┘ │
│                 │
│ ┌─────────────┐ │
│ │ CloudFront  │ │ ← Automatically updated!
│ │  Function   │ │
│ └─────────────┘ │
└─────────────────┘
```

## Benefits

✅ **Automated**: No manual updates needed  
✅ **Consistent**: Function always matches codebase  
✅ **Fast**: Changes live in seconds  
✅ **Safe**: Script validates before publishing  
✅ **Traceable**: GitHub Actions logs all changes  

## Adding New Routes

To add a new route:

1. Add the HTML file to `frontend/`
2. Update `validRoutes` in `cloudfront/url-rewrite-function.js`
3. Add to RBAC in `frontend/js/rbac.js` if protected
4. Commit and push
5. GitHub Actions automatically updates CloudFront! ✨

Example:

```javascript
var validRoutes = [
    // ... existing routes ...
    '/my-new-page'  // Add here
];
```

That's it! The automation handles the rest.

