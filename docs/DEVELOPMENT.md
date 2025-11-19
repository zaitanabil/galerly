# Development Workflow

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd galerly.com

# 2. Make changes
vim backend/api.py
vim frontend/index.html

# 3. Test locally (optional)
cd backend
python3 api.py

# 4. Deploy
git add .
git commit -m "Your changes"
git push origin main
```

## Deployment Flow

```
Push to main
     ↓
GitHub Actions
     ↓
┌────────────────────────────────┐
│  1. Check Infrastructure       │
│     - Check DynamoDB tables    │
│     - Create if missing        │
│     - Verify indexes           │
│     - Configure AWS            │
└────────────────────────────────┘
     ↓
┌────────────────────────────────┐
│  2. Package Backend            │
│     - Zip api.py + handlers/   │
│     - Exclude __pycache__      │
└────────────────────────────────┘
     ↓
┌────────────────────────────────┐
│  3. Deploy Lambda              │
│     - Update function code     │
│     - Wait for completion      │
│     - Update configuration     │
└────────────────────────────────┘
     ↓
┌────────────────────────────────┐
│  4. Deploy Frontend            │
│     - Sync to S3               │
│     - Delete old files         │
│     - Set cache headers        │
└────────────────────────────────┘
     ↓
┌────────────────────────────────┐
│  5. Verify                     │
│     - Check infrastructure     │
│     - Check Lambda             │
│     - Count S3 files           │
└────────────────────────────────┘
     ↓
  ✅ Done! (3-5 min first time, 2-3 min after)
```

**First push:** Sets up infrastructure + deploys  
**Subsequent:** Just deploys (infrastructure exists)

## Monitoring

### GitHub Actions

```
Repository → Actions → Latest workflow
```

### AWS Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/galerly-api --follow

# Filter errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/galerly-api \
  --filter-pattern "ERROR"

# Recent invocations (last hour)
aws logs tail /aws/lambda/galerly-api --since 1h
```

### Health Check

```bash
curl https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/health
```

## Testing

### Local Testing

```bash
cd backend
python3 api.py
```

### Test API

```bash
# Health check
curl https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/health

# Check cities
curl https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/api/v1/cities/search?q=Paris
```

## Rollback

```bash
# Revert last commit
git revert HEAD
git push origin main

# Revert to specific commit
git revert <commit-hash>
git push origin main
```

GitHub Actions deploys automatically.

## Project Structure

```
galerly.com/
├── backend/
│   ├── api.py              ← Main Lambda handler
│   ├── handlers/           ← Route handlers
│   │   ├── auth_handler.py
│   │   ├── gallery_handler.py
│   │   ├── photo_handler.py
│   │   ├── client_handler.py
│   │   ├── contact_handler.py
│   │   └── newsletter_handler.py
│   ├── utils/              ← Utilities
│   │   ├── auth.py
│   │   ├── config.py
│   │   └── response.py
│   ├── setup_dynamodb.py   ← Table management
│   ├── setup_aws.py        ← AWS configuration
│   └── manage_indexes.py   ← Index management
├── frontend/
│   ├── *.html              ← Pages
│   ├── css/                ← Styles
│   ├── js/                 ← Scripts
│   └── img/                ← Images
├── docs/                   ← All documentation
└── .github/
    └── workflows/
        └── deploy.yml      ← CI/CD
```

## Common Tasks

### Add New API Endpoint

```bash
# 1. Create/update handler
vim backend/handlers/my_handler.py

# 2. Add route in api.py
vim backend/api.py

# 3. Deploy
git add . && git commit -m "Add endpoint" && git push
```

### Update Frontend

```bash
# 1. Edit files
vim frontend/index.html
vim frontend/css/style.css

# 2. Deploy
git add . && git commit -m "Update UI" && git push
```

### Add New Table

```bash
# 1. Update setup_dynamodb.py
vim backend/setup_dynamodb.py

# 2. Update manage_indexes.py (if indexes needed)
vim backend/manage_indexes.py

# 3. Push (GitHub Actions creates table)
git add . && git commit -m "Add table" && git push
```

## Troubleshooting

### Deployment Failed

```bash
# 1. Check Actions logs
Repository → Actions → Failed workflow → View logs

# 2. Common issues:
- AWS credentials expired
- IAM permissions missing
- Package size > 50MB
```

### Lambda Not Updating

```bash
# Check function
aws lambda get-function --function-name galerly-api

# Check logs
aws logs tail /aws/lambda/galerly-api --follow
```

### Frontend Not Updating

```bash
# Clear browser cache (Ctrl+Shift+R)

# Check S3
aws s3 ls s3://galerly-frontend-app/

# Check specific file
aws s3api head-object \
  --bucket galerly-frontend-app \
  --key index.html
```

## Environment

- **Python:** 3.11+
- **AWS Region:** us-east-1
- **Lambda:** galerly-api
- **S3 Bucket:** galerly-frontend-app
- **DynamoDB:** 7 tables, 12 indexes

## Resources

- API: `https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod`
- Frontend: `http://galerly-frontend-app.s3-website-us-east-1.amazonaws.com`
- Workflow: `.github/workflows/deploy.yml`

## Next Steps

1. Make changes
2. Test locally (optional)
3. Push to main
4. Monitor in Actions
5. Verify deployment

**All infrastructure is automated!**

