# Galerly

Professional photo gallery management platform for photographers.

## Project Structure

```
galerly.com/
├── backend/           # Python API (Flask/Lambda)
├── frontend/          # HTML/CSS/JavaScript
├── docker/            # Container configuration
├── scripts/           # Operational automation
├── docs/              # Documentation
├── .github/workflows/ # CI/CD pipelines
└── tests/             # Comprehensive test suite (500+ tests)
```

## Quick Start

### Local Development

```bash
# Start LocalStack (local AWS)
./scripts/start-localstack.sh

# Run backend
cd backend
python api.py

# Frontend served via Python HTTP server or deploy to S3
```

### Run Tests

```bash
# All tests with Docker
./scripts/run-tests.sh

# Backend tests only
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=handlers --cov=utils --cov-report=html
```

## Features

- 📸 **Gallery Management** - Create, organize, and share photo galleries
- 👥 **Client Portal** - Secure client access to their photos
- ⭐ **Favorites & Feedback** - Clients can favorite photos and leave feedback
- 💳 **Subscription Billing** - Tiered plans with Stripe integration
- 📊 **Analytics** - Track views, downloads, and engagement
- 🔐 **Authentication** - Secure user auth with sessions
- 📧 **Notifications** - Email notifications and reminders
- 🎨 **Portfolio** - Public portfolio pages for photographers
- 📱 **Responsive** - Works on desktop, tablet, and mobile

## Tech Stack

- **Backend**: Python 3.11, Flask, AWS Lambda
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: AWS DynamoDB
- **Storage**: AWS S3 + CloudFront CDN
- **Payments**: Stripe
- **Infrastructure**: AWS (Lambda, API Gateway, CloudFront, S3, DynamoDB)
- **Local Dev**: LocalStack
- **CI/CD**: GitHub Actions
- **Testing**: Pytest, 500+ automated tests

## Documentation

- [Project Organization](docs/PROJECT_ORGANIZATION.md) - Directory structure
- [Pagination Implementation](docs/PAGINATION.md) - Pagination guide
- [Stripe Webhook Setup](docs/STRIPE_WEBHOOK_SETUP.md) - Payment integration
- [Subscription Validation](docs/SUBSCRIPTION_VALIDATION.md) - Business rules
- [Brand Identity](docs/BRAND_IDENTITY.md) - Design guidelines

## Testing

- ✅ 500+ automated tests
- ✅ 100% endpoint coverage
- ✅ Integration workflows tested
- ✅ CI/CD with GitHub Actions
- ✅ Docker test containers

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific tests
pytest backend/tests/test_auth_handler.py
pytest backend/tests/test_gallery_handler.py
pytest backend/tests/test_billing_handler.py
```

## Deployment

### Backend (AWS Lambda)
```bash
cd backend
./deploy-lambda.sh
```

### Frontend (S3 + CloudFront)
```bash
aws s3 sync frontend/ s3://your-bucket/ --delete
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

## Scripts

Located in `scripts/` directory:

- `run-tests.sh` - Run comprehensive test suite
- `start-localstack.sh` - Start local AWS environment
- `stop-localstack.sh` - Stop LocalStack
- `auto-backup-s3.sh` - Automated S3 backups
- `run-gallery-cleanup.sh` - Cleanup expired galleries
- `generate-frontend-config.sh` - Generate frontend config

## Environment Variables

Create `.env` file in backend/:

```bash
ENVIRONMENT=local
AWS_ENDPOINT_URL=http://localhost:4566
FRONTEND_URL=http://localhost:8000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## API Endpoints

112+ RESTful endpoints organized by feature:

- `/v1/auth/*` - Authentication & authorization
- `/v1/galleries/*` - Gallery management
- `/v1/photos/*` - Photo operations
- `/v1/client/*` - Client portal
- `/v1/billing/*` - Subscription & billing
- `/v1/analytics/*` - Analytics & tracking
- `/v1/notifications/*` - Notification system

See [API Documentation](docs/API.md) for complete reference.

## Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure all tests pass (`./scripts/run-tests.sh`)
4. Follow coding standards (`.cursor/rules/rule1.mdc`)
5. Create pull request

## License

Proprietary - All rights reserved

## Support

For questions or issues, contact: support@galerly.com
