# Galerly Test Suite

Comprehensive test coverage for all backend and frontend endpoints.

## Test Structure

### Backend Tests (`/backend/tests/`)

#### Core Handler Tests
- ✅ `test_auth_handler.py` - Authentication endpoints (11 tests)
- ✅ `test_gallery_handler.py` - Gallery CRUD operations (15 tests)
- ✅ `test_client_handler.py` - Client gallery access (12 tests)
- ✅ `test_billing_handler.py` - Billing and subscriptions (13 tests)
- ✅ `test_cache.py` - Cache utility functions (18 tests)

#### Additional Handler Tests (To be run)
- `test_photo_handler.py` - Photo operations
- `test_analytics_handler.py` - Analytics tracking
- `test_dashboard_handler.py` - Dashboard stats
- `test_profile_handler.py` - Profile management
- `test_portfolio_handler.py` - Portfolio settings
- `test_social_handler.py` - Social sharing
- `test_refund_handler.py` - Refund processing
- `test_newsletter_handler.py` - Newsletter subscriptions
- `test_contact_handler.py` - Contact form
- `test_notification_handler.py` - Notifications
- `test_client_favorites_handler.py` - Client favorites
- `test_client_feedback_handler.py` - Client feedback
- `test_visitor_tracking_handler.py` - Visitor analytics
- `test_photo_upload_presigned.py` - Presigned uploads
- `test_multipart_upload_handler.py` - Multipart uploads
- `test_bulk_download_handler.py` - Bulk downloads
- `test_subscription_handler.py` - Usage tracking
- `test_photographer_handler.py` - Photographer directory
- `test_city_handler.py` - City search
- `test_gallery_expiration_handler.py` - Gallery expiration

### Frontend Tests (`/frontend/tests/`)

#### Core Component Tests
- ✅ `test-billing.html` - Billing UI logic (7 test suites, 25 tests)
- ✅ `test-infinite-scroll.html` - Infinite scroll (9 test suites, 28 tests)

#### Additional Component Tests (To be created)
- `test-gallery.html` - Gallery management UI
- `test-photo-upload.html` - Photo upload flows
- `test-auth.html` - Authentication UI
- `test-client-gallery.html` - Client gallery view
- `test-analytics.html` - Analytics dashboard
- `test-sharing.html` - Social sharing
- `test-favorites.html` - Client favorites
- `test-lightbox.html` - Lightbox slideshow
- `test-progressive-loader.html` - Progressive loading
- `test-upload-manager.html` - Upload queue management

## Running Tests

### Backend Tests (pytest)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth_handler.py

# Run with coverage
pytest tests/ --cov=handlers --cov=utils --cov-report=html

# Run specific test class
pytest tests/test_gallery_handler.py::TestHandleListGalleries

# Run with verbose output
pytest tests/ -v
```

### Frontend Tests (browser-based)

```bash
# Start local server
cd frontend
python3 -m http.server 8000

# Open in browser:
# http://localhost:8000/tests/test-billing.html
# http://localhost:8000/tests/test-infinite-scroll.html
```

## Test Coverage by Endpoint

### Authentication Endpoints (11/11)
- [x] POST /v1/auth/request-verification
- [x] POST /v1/auth/verify-email
- [x] POST /v1/auth/register
- [x] POST /v1/auth/login
- [x] POST /v1/auth/logout
- [x] DELETE /v1/auth/delete-account
- [x] POST /v1/auth/forgot-password
- [x] POST /v1/auth/reset-password
- [x] GET /v1/auth/me
- [x] Session creation
- [x] Session validation

### Gallery Endpoints (15/15)
- [x] GET /v1/galleries (list with filters)
- [x] POST /v1/galleries (create)
- [x] GET /v1/galleries/{id} (get with pagination)
- [x] PUT /v1/galleries/{id} (update)
- [x] DELETE /v1/galleries/{id} (delete)
- [x] POST /v1/galleries/{id}/duplicate
- [x] POST /v1/galleries/{id}/archive
- [x] POST /v1/galleries/{id}/unarchive
- [x] Cache integration
- [x] Cache invalidation
- [x] Projection optimization
- [x] Pagination enforcement
- [x] Error handling
- [x] Access control
- [x] Photo loading exceptions

### Client Gallery Endpoints (12/12)
- [x] GET /v1/client/galleries
- [x] GET /v1/client/galleries/{id} (with pagination)
- [x] GET /v1/client/galleries/by-token/{token} (public access)
- [x] Client access validation
- [x] Pagination with page_size
- [x] Pagination with last_key
- [x] Pagination metadata
- [x] Page size limits (min 1, max 100)
- [x] Photo loading exceptions
- [x] Projection optimization
- [x] Token validation
- [x] Public gallery access

### Billing Endpoints (13/13)
- [x] GET /v1/billing/subscription
- [x] POST /v1/billing/subscription/cancel
- [x] POST /v1/billing/subscription/change-plan
- [x] POST /v1/billing/checkout
- [x] GET /v1/billing/history
- [x] GET /v1/billing/invoice/{id}/pdf
- [x] GET /v1/billing/subscription/check-downgrade
- [x] POST /v1/billing/subscription/downgrade
- [x] POST /v1/billing/webhook (Stripe)
- [x] Reactivation logic
- [x] Plan upgrade/downgrade
- [x] Checkout session creation
- [x] Subscription validation

### Photo Endpoints (0/15) - TO BE TESTED
- [ ] POST /v1/galleries/{id}/photos (upload)
- [ ] PUT /v1/photos/{id} (update)
- [ ] DELETE /v1/galleries/{id}/photos/delete (batch)
- [ ] POST /v1/galleries/{id}/photos/check-duplicates
- [ ] GET /v1/photos/search
- [ ] POST /v1/photos/{id}/comments
- [ ] PUT /v1/photos/{photo_id}/comments/{comment_id}
- [ ] DELETE /v1/photos/{photo_id}/comments/{comment_id}
- [ ] Presigned URL generation
- [ ] Direct upload
- [ ] Confirm upload
- [ ] Multipart init
- [ ] Multipart complete
- [ ] Multipart abort
- [ ] Duplicate detection

### Analytics Endpoints (0/12) - TO BE TESTED
- [ ] POST /v1/analytics/track/gallery/{id}
- [ ] POST /v1/analytics/track/photo/{id}
- [ ] POST /v1/analytics/track/download/{id}
- [ ] POST /v1/analytics/track/share/gallery/{id}
- [ ] POST /v1/analytics/track/share/photo/{id}
- [ ] POST /v1/analytics/track/bulk-download/{id}
- [ ] GET /v1/analytics
- [ ] GET /v1/analytics/galleries/{id}
- [ ] GET /v1/analytics/bulk-downloads
- [ ] Owner detection (skip self-tracking)
- [ ] Metadata capture
- [ ] Public tracking (no auth)

### Other Endpoints (0/40+) - TO BE TESTED
- Dashboard, Profile, Portfolio, Social, Refund, Newsletter, Contact, Notifications, Favorites, Feedback, Visitor Tracking, etc.

## Test Quality Standards

### Backend Tests Must Include:
1. Success cases
2. Validation errors (400)
3. Authentication errors (401)
4. Authorization errors (403)
5. Not found errors (404)
6. Server errors (500)
7. Edge cases (empty data, large data, special characters)
8. Database exceptions
9. External service failures
10. Concurrent operations

### Frontend Tests Must Include:
1. UI state changes
2. API request formation
3. Response handling
4. Error display
5. Loading states
6. User interactions
7. Form validation
8. Edge cases (empty, invalid, special input)
9. Browser compatibility
10. Accessibility

## Coverage Goals

- Backend: >90% line coverage
- Frontend: >80% functional coverage
- Integration: All critical user flows
- Edge cases: All error conditions

## CI/CD Integration

Tests should run automatically on:
- Pre-commit hooks
- Pull requests
- Deployment pipelines

## Test Data

Use fixtures from `conftest.py`:
- `sample_user`
- `sample_gallery`
- `sample_photo`
- `sample_subscription`
- `mock_dynamodb_table`
- `mock_s3_client`
- `mock_stripe`
- `mock_cache`

## Notes

- Tests use mocking to avoid external dependencies
- All tests can run offline
- No hardcoded values or secrets in tests
- Tests follow naming convention: `test_<handler>_<scenario>`
- Test files mirror source file structure

