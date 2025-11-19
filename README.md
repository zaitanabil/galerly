# Galerly Documentation

Photography gallery platform. Share art, not files.

---

## Quick Start

### Deploy

**All deployments via GitHub Actions:**
```bash
git add .
git commit -m "Your changes"
git push origin main
```

GitHub Actions automatically:
- ✅ Checks/creates DynamoDB tables (if needed)
- ✅ Checks/creates indexes (if needed)
- ✅ Verifies AWS configuration
- ✅ Deploys backend (Lambda)
- ✅ Deploys frontend (S3)
- ⏱️ Takes ~5-7 min (first time), ~2-3 min (after)

See: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for setup.

---

## Architecture

```
Browser → S3 (Frontend) → API Gateway → Lambda (Python) → DynamoDB
                                                        ↓
                                                   S3 (Images)
```

**Components:**
- **Frontend:** S3 static website (HTML/CSS/JS)
- **Backend:** Lambda Python 3.11 (`galerly-api`)
- **Database:** DynamoDB (users, galleries, photos, sessions)
- **Storage:** S3 (`galerly-images-storage`)
- **API:** `https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod`

---

## API Endpoints

### Authentication
```
POST /api/v1/auth/register    - Register user
POST /api/v1/auth/login       - Login
GET  /api/v1/auth/me          - Current user
```

### Galleries
```
GET    /api/v1/galleries         - List galleries
POST   /api/v1/galleries         - Create gallery
GET    /api/v1/galleries/{id}    - Get gallery
PUT    /api/v1/galleries/{id}    - Update gallery
DELETE /api/v1/galleries/{id}    - Delete gallery
```

### Photos
```
POST /api/v1/galleries/{id}/photos  - Upload photo
PUT  /api/v1/photos/{id}            - Update photo status
POST /api/v1/photos/{id}/comments   - Add comment
```

### Client Access
```
GET /api/v1/client/galleries     - Client galleries
GET /api/v1/client/galleries/{id} - Client gallery view
```

### Public
```
GET  /api/v1/photographers        - List photographers
GET  /api/v1/photographers/{id}   - Photographer profile
GET  /api/v1/cities/search?q=     - City autocomplete
POST /api/v1/newsletter/subscribe - Subscribe to newsletter
POST /api/v1/contact/submit       - Submit support ticket
```

**Full API docs:** See `docs/API.md`

---

## Database Schema

### galerly-users
```
PK: email
- id, username, name, password_hash, role, subscription
- city, bio, specialties, created_at, updated_at
```

### galerly-galleries
```
PK: user_id, SK: id
- name, description, client_name, client_email
- privacy, share_token, allow_download, allow_comments
- photo_count, view_count, created_at, updated_at
```

### galerly-photos
```
PK: id, GSI: gallery_id
- filename, s3_key, url, title, description
- status (pending/approved), views, comments
- created_at, updated_at
```

### galerly-sessions
```
PK: token, GSI: user_id
- user (full object), created_at
- TTL: 24 hours
```

### galerly-newsletters
```
PK: email, GSI: subscribed_at
- firstName, status (active/unsubscribed)
- subscribed_at, updated_at, source
```

### galerly-contact
```
PK: id, GSI: created_at, status
- name, email, issue_type, message
- status (new/in_progress/resolved/closed)
- created_at, updated_at
```

---

## Design System

**Colors:**
- Science Blue: `#0066CC`
- Shark (Dark): `#1D1D1F`
- Light Gray: `#F5F5F7`
- Pure White: `#FFFFFF`
- Coral Accent: `#FF6F61`
- Mint Green: `#98FF98`

**Design:** Liquid Glass (glassmorphism)

**Files:**
- `frontend/css/variables.css` - Design system (507 lines)
- `docs/BRAND.md` - Brand guidelines
- `docs/DESIGN_SYSTEM.md` - Complete design system

---

## Backend Structure

```
backend/
├── api.py                    # Main router
├── setup_dynamodb.py         # DynamoDB setup (replaces 5 shell scripts)
├── setup_aws.py              # AWS configuration (CORS, etc.)
├── manage_indexes.py         # Index management
├── import_cities_to_dynamodb.py  # City data import
├── utils/
│   ├── config.py            # AWS clients
│   ├── auth.py              # Authentication
│   ├── response.py          # API responses
│   ├── security.py          # Security utilities
│   └── cities.py            # City search
└── handlers/
    ├── auth_handler.py      # Login/Register
    ├── gallery_handler.py   # Gallery CRUD
    ├── photo_handler.py     # Photo upload
    ├── client_handler.py    # Client access
    ├── dashboard_handler.py # Stats
    ├── photographer_handler.py
    ├── profile_handler.py
    ├── newsletter_handler.py # Newsletter subscriptions
    └── city_handler.py
```

### Backend Setup Scripts

**DynamoDB Management:**
```bash
python setup_dynamodb.py create    # Create all tables
python setup_dynamodb.py optimize  # Optimize tables
python setup_dynamodb.py list      # List tables
```

**AWS Configuration:**
```bash
python setup_aws.py api-cors       # Enable API Gateway CORS
python setup_aws.py s3-cors        # Enable S3 CORS
python setup_aws.py all            # Configure everything
```

**Index Management:**
```bash
python manage_indexes.py           # Check indexes
python manage_indexes.py --create  # Create missing indexes
```

See `backend/README_SETUP.md` for detailed documentation.

---

## Frontend Structure

```
frontend/
├── index.html               # Landing page
├── auth.html                # Login/Register
├── dashboard.html           # Photographer dashboard
├── client-dashboard.html    # Client dashboard
├── gallery.html             # Gallery management
├── profile-settings.html    # Profile editor
├── css/
│   ├── variables.css        # Design system
│   ├── style.css            # Main styles
│   └── gallery.css          # Gallery-specific
└── js/
    ├── config.js            # API config
    ├── auth.js              # Auth logic
    ├── gallery-loader.js    # Gallery operations
    └── *.js                 # Other modules
```

---

## Development

### Local Testing

**Backend:**
```bash
cd backend
python3 -c "from api import handler; print(handler({'path': '/health', 'httpMethod': 'GET'}, {}))"
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 8000
# Open http://localhost:8000
```

### Environment Variables

**Lambda:**
```bash
S3_BUCKET_NAME=galerly-images-storage
```

**Frontend (`js/config.js`):**
```javascript
const API_BASE_URL = 'https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod';
```

---

## Monitoring

**CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/galerly-api --follow
```

**Health Check:**
```bash
curl https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/health
```

---

## Troubleshooting

**Lambda not updating:**
```bash
aws lambda update-function-code --function-name galerly-api --zip-file fileb://galerly-modular.zip
aws lambda wait function-updated --function-name galerly-api
```

**Frontend not updating:**
```bash
aws s3 sync frontend/ s3://galerly-frontend-app/ --delete --cache-control "no-cache"
```

**Check logs:**
```bash
aws logs tail /aws/lambda/galerly-api --follow
```

---

## Resources

- **Website:** http://galerly-frontend-app.s3-website-us-east-1.amazonaws.com
- **API:** https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod
- **Region:** us-east-1
- **Docs:** [`/docs`](docs/) folder

---

## Documentation

**All documentation in [`/docs`](docs/) folder** - See [`docs/README.md`](docs/README.md)

**Quick Links:**
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - How to deploy (GitHub Actions)
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development workflow
- **[docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md)** - AWS infrastructure automation
- **[docs/API.md](docs/API.md)** - API reference
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture

---

**Version:** 2.0.0  
**Updated:** November 13, 2025  
**Major Changes:** Consolidated backend scripts into Python (removed 5 shell scripts), centralized documentation
