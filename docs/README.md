# Galerly Documentation

Technical documentation for IT staff.

## 📚 Core Documentation

### Deployment & Development
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - GitHub Actions CI/CD (automated, 8-stage pipeline)
- **[ENTERPRISE_CICD_COMPLETE.md](ENTERPRISE_CICD_COMPLETE.md)** - Complete CI/CD reference
- **[WORKFLOW_TREE_STRUCTURE.md](WORKFLOW_TREE_STRUCTURE.md)** - CI/CD pipeline tree structure
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local development workflow
- **[SETUP.md](SETUP.md)** - Backend setup scripts
- **[INFRASTRUCTURE.md](INFRASTRUCTURE.md)** - AWS infrastructure automation

### Architecture & API
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, data flow, AWS costs
- **[API.md](API.md)** - Complete API endpoint reference
- **[API_SECURITY_AND_CLEAN_URLS.md](API_SECURITY_AND_CLEAN_URLS.md)** - URL design patterns

### Database
- **[DATABASE_INDEXES.md](DATABASE_INDEXES.md)** - DynamoDB tables, indexes, access patterns
- **[DATABASE_SECURITY.md](DATABASE_SECURITY.md)** - Security model, data isolation, compliance

## 🔐 Security & Authentication

- **[HTTPONLY_COOKIE_MIGRATION.md](HTTPONLY_COOKIE_MIGRATION.md)** - HttpOnly cookie authentication
- **[IMAGE_SECURITY.md](IMAGE_SECURITY.md)** - Image validation & sanitization
- **[TOKEN_EXPIRATION_SYSTEM.md](TOKEN_EXPIRATION_SYSTEM.md)** - Token lifecycle (7-day max)

**Authentication Status**:
- ✅ Web: HttpOnly cookies, SameSite=Strict, 7-day sessions
- ❌ API/Mobile: OAuth2 not implemented (use cookies temporarily)

## 🎨 Features & Systems

### Email & Notifications
- **[EMAIL_VERIFICATION_COMPLETE.md](EMAIL_VERIFICATION_COMPLETE.md)** - Email verification system
- **[EMAIL_SYSTEM_BRAND_GUIDE.md](EMAIL_SYSTEM_BRAND_GUIDE.md)** - Email branding & templates
- **[NOTIFICATION_SYSTEM_COMPLETE.md](NOTIFICATION_SYSTEM_COMPLETE.md)** - Notification preferences

### Client & Gallery Management
- **[MULTI_CLIENT_COMPLETE.md](MULTI_CLIENT_COMPLETE.md)** - Multi-client collaboration
- **[VISITOR_TRACKING_COMPLETE.md](VISITOR_TRACKING_COMPLETE.md)** - Analytics & tracking
- **[VISITOR_TRACKING_DATA_DICTIONARY.md](VISITOR_TRACKING_DATA_DICTIONARY.md)** - Analytics schema

### Design & Typography
- **[SF_PRO_TYPOGRAPHY_GUIDE.md](SF_PRO_TYPOGRAPHY_GUIDE.md)** - SF Pro font system
- **[TYPOGRAPHY_IMPLEMENTATION.md](TYPOGRAPHY_IMPLEMENTATION.md)** - Typography implementation

## 💰 Business

- **[OPTIMAL_PRICING_STRATEGY.md](OPTIMAL_PRICING_STRATEGY.md)** - Pricing tiers, cost analysis

## 🔧 Setup Guides

- **[COMPLETE_DOMAIN_SETUP_GUIDE.md](COMPLETE_DOMAIN_SETUP_GUIDE.md)** - Domain & DNS configuration
- **[STRIPE_SETUP_COMPLETE.md](STRIPE_SETUP_COMPLETE.md)** - Stripe integration & webhooks

## 📋 Reference

- **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Historical database migrations
- **[COMPREHENSIVE_REVIEW.md](COMPREHENSIVE_REVIEW.md)** - System architecture review
- **[To_Implement.md](To_Implement.md)** - Future features & roadmap

---

## 🚀 Quick Start

### 1. Deploy (Automated)
```bash
git add .
git commit -m "your changes"
git push origin main
```
GitHub Actions deploys automatically. See [DEPLOYMENT.md](DEPLOYMENT.md).

### 2. Local Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api.py
```
See [DEVELOPMENT.md](DEVELOPMENT.md) for details.

### 3. Setup AWS Resources
```bash
cd backend
python setup_dynamodb.py create
python setup_aws.py all
```
See [SETUP.md](SETUP.md) for all scripts.

---

## 🏗️ Stack

- **Frontend**: S3 static site (HTML/CSS/JS)
- **CDN**: CloudFront with custom URL rewriting
- **Backend**: AWS Lambda (Python 3.11)
- **Database**: DynamoDB (7 tables, 12 indexes)
- **Storage**: S3 (photos)
- **API**: API Gateway REST
- **Email**: SMTP (branded templates)
- **Payments**: Stripe (subscriptions)
- **CI/CD**: GitHub Actions (8-stage pipeline)

---

## 📊 DynamoDB Tables

| Table | Purpose | TTL |
|-------|---------|-----|
| `galerly-users` | User accounts | - |
| `galerly-galleries` | Photo galleries | - |
| `galerly-photos` | Photos | - |
| `galerly-sessions` | Auth sessions | 7 days |
| `galerly-subscriptions` | Stripe subscriptions | - |
| `galerly-billing` | Payment history | - |
| `galerly-cities` | City autocomplete | - |

---

## 🔒 Security & Compliance

- ✅ **HttpOnly cookies** - XSS protection
- ✅ **SameSite=Strict** - CSRF protection
- ✅ **7-day token expiration** - Swiss law compliance
- ✅ **Content Security Policy** - XSS/Clickjacking prevention
- ✅ **Image validation** - Magic byte checks, format validation
- ✅ **HTTPS enforced** - TLS 1.2+
- ✅ **GDPR compliant** - Cookie consent, data deletion

---

## 🆘 Troubleshooting

### Deployment Failed
1. Check GitHub Actions logs (Repository → Actions)
2. Verify all 28 GitHub Secrets are set
3. Review CloudWatch logs: `/aws/lambda/galerly-api`

### Authentication Issues
- Cookies: Check HttpOnly, Secure, SameSite flags
- Sessions: Verify DynamoDB `galerly-sessions` table
- Tokens: Max 7-day lifetime, check expiration logic

### Database Issues
- Indexes: Run `python manage_indexes.py`
- Security: Review [DATABASE_SECURITY.md](DATABASE_SECURITY.md)
- Performance: Check [DATABASE_INDEXES.md](DATABASE_INDEXES.md)

---

## 📝 CI/CD Pipeline (8 Stages)

```
Stage 1: Validate Secrets (28 secrets)
Stage 2: Code Quality (linting, syntax, imports)
Stage 3: AWS Infrastructure Tests (S3, DynamoDB, Lambda, CloudFront)
Stage 4: Backend Unit Tests (39 tests)
Stage 5: Deploy Frontend (S3, CloudFront)
Stage 6: Deploy Backend (Lambda, env vars)
Stage 7: Post-Deployment Tests (HTTP, Lambda invoke)
Stage 8: Deployment Summary
```

See [ENTERPRISE_CICD_COMPLETE.md](ENTERPRISE_CICD_COMPLETE.md) for details.

---

**Last Updated**: November 2025  
**Total Docs**: 30 files (cleaned & consolidated)
