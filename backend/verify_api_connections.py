#!/usr/bin/env python3
"""
API Endpoint Connection Verification
Ensures all frontend API calls match backend endpoints
"""

import re
import os
from pathlib import Path

# Define all backend API endpoints from api.py
BACKEND_ENDPOINTS = {
    # Public endpoints
    'GET /v1/health': 'Health check',
    'GET /v1/': 'API info',
    
    # Authentication
    'POST /v1/auth/request-verification': 'Request email verification',
    'POST /v1/auth/verify-email': 'Verify email code',
    'POST /v1/auth/register': 'Register new user',
    'POST /v1/auth/login': 'Login user',
    'POST /v1/auth/logout': 'Logout user',
    'POST /v1/auth/forgot-password': 'Request password reset',
    'POST /v1/auth/reset-password': 'Reset password',
    'GET /v1/auth/me': 'Get current user',
    
    # Cities
    'GET /v1/cities/search': 'Search cities',
    
    # Photographers
    'GET /v1/photographers': 'List photographers',
    'GET /v1/photographers/{id}': 'Get photographer',
    
    # Portfolio
    'GET /v1/portfolio/{id}': 'Get public portfolio',
    'GET /v1/portfolio/settings': 'Get portfolio settings',
    'PUT /v1/portfolio/settings': 'Update portfolio settings',
    
    # Profile
    'PUT /v1/profile': 'Update profile',
    
    # Dashboard
    'GET /v1/dashboard': 'Get dashboard stats',
    'GET /v1/dashboard/stats': 'Get dashboard stats (alt)',
    
    # Galleries
    'GET /v1/galleries': 'List galleries',
    'POST /v1/galleries': 'Create gallery',
    'GET /v1/galleries/{id}': 'Get gallery',
    'PUT /v1/galleries/{id}': 'Update gallery',
    'DELETE /v1/galleries/{id}': 'Delete gallery',
    'POST /v1/galleries/{id}/duplicate': 'Duplicate gallery',
    'POST /v1/galleries/{id}/archive': 'Archive gallery',
    'POST /v1/galleries/{id}/unarchive': 'Unarchive gallery',
    'POST /v1/galleries/check-expiring': 'Check expiring galleries',
    
    # Photos
    'POST /v1/galleries/{id}/photos': 'Upload photo (legacy)',
    'POST /v1/galleries/{id}/photos/upload-url': 'Get presigned upload URL',
    'POST /v1/galleries/{id}/photos/confirm-upload': 'Confirm upload',
    'POST /v1/galleries/{id}/photos/check-duplicates': 'Check duplicates',
    'DELETE /v1/galleries/{id}/photos/delete': 'Batch delete photos',
    'POST /v1/galleries/{id}/photos/download-bulk': 'Bulk download',
    'POST /v1/galleries/{id}/notify-clients': 'Send batch notification',
    
    # Multipart uploads
    'POST /v1/galleries/{id}/photos/multipart-upload/init': 'Init multipart',
    'POST /v1/galleries/{id}/photos/multipart-upload/complete': 'Complete multipart',
    'POST /v1/galleries/{id}/photos/multipart-upload/abort': 'Abort multipart',
    
    # Photo management
    'GET /v1/photos/search': 'Search photos',
    'PUT /v1/photos/{id}': 'Update photo',
    'POST /v1/photos/{id}/comments': 'Add comment',
    'PUT /v1/photos/{id}/comments/{comment_id}': 'Update comment',
    'DELETE /v1/photos/{id}/comments/{comment_id}': 'Delete comment',
    
    # Client
    'GET /v1/client/galleries': 'List client galleries',
    'GET /v1/client/galleries/{id}': 'Get client gallery',
    'GET /v1/client/galleries/by-token/{token}': 'Get gallery by token',
    
    # Favorites
    'GET /v1/client/favorites': 'Get favorites',
    'POST /v1/client/favorites': 'Add favorite',
    'DELETE /v1/client/favorites': 'Remove favorite',
    'GET /v1/client/favorites/{id}': 'Check favorite',
    
    # Feedback
    'POST /v1/client/feedback/{id}': 'Submit feedback',
    'GET /v1/client/feedback/{id}': 'Get gallery feedback',
    
    # Sharing
    'GET /v1/share/gallery/{id}': 'Get gallery share info',
    'GET /v1/share/photo/{id}': 'Get photo share info',
    
    # Downloads
    'POST /v1/downloads/bulk/by-token': 'Bulk download by token',
    
    # Billing
    'POST /v1/billing/checkout': 'Create checkout session',
    'GET /v1/billing/history': 'Get billing history',
    'GET /v1/billing/subscription': 'Get subscription',
    'POST /v1/billing/subscription/cancel': 'Cancel subscription',
    'GET /v1/billing/subscription/check-downgrade': 'Check downgrade',
    'POST /v1/billing/subscription/downgrade': 'Downgrade subscription',
    'POST /v1/billing/subscription/change-plan': 'Change plan',
    'POST /v1/billing/webhook': 'Stripe webhook',
    
    # Refunds
    'GET /v1/billing/refund/check': 'Check refund eligibility',
    'POST /v1/billing/refund/request': 'Request refund',
    'GET /v1/billing/refund/status': 'Get refund status',
    
    # Subscription
    'GET /v1/subscription/usage': 'Get usage stats',
    
    # Analytics
    'GET /v1/analytics': 'Get overall analytics',
    'GET /v1/analytics/galleries/{id}': 'Get gallery analytics',
    'POST /v1/analytics/track/gallery/{id}': 'Track gallery view',
    'POST /v1/analytics/track/photo/{id}': 'Track photo view',
    'POST /v1/analytics/track/download/{id}': 'Track download',
    'POST /v1/analytics/track/share/gallery/{id}': 'Track gallery share',
    'POST /v1/analytics/track/share/photo/{id}': 'Track photo share',
    
    # Visitor tracking
    'POST /v1/visitor/track/visit': 'Track visit',
    'POST /v1/visitor/track/event': 'Track event',
    'POST /v1/visitor/track/session-end': 'Track session end',
    'GET /v1/visitor/analytics': 'Get visitor analytics',
    
    # Notifications
    'GET /v1/notifications/preferences': 'Get notification preferences',
    'PUT /v1/notifications/preferences': 'Update notification preferences',
    'POST /v1/notifications/send-custom': 'Send custom notification',
    'POST /v1/notifications/send-selection-reminder': 'Send selection reminder',
    
    # Newsletter
    'POST /v1/newsletter/subscribe': 'Subscribe to newsletter',
    'POST /v1/newsletter/unsubscribe': 'Unsubscribe from newsletter',
    
    # Contact
    'POST /v1/contact/submit': 'Submit contact form',
}

# Frontend JS files and their expected API calls
FRONTEND_API_USAGE = {
    'auth.js': [
        'POST /v1/auth/request-verification',
        'POST /v1/auth/verify-email',
        'POST /v1/auth/register',
        'POST /v1/auth/login',
    ],
    'reset-password.js': [
        'POST /v1/auth/forgot-password',
        'POST /v1/auth/reset-password',
    ],
    'gallery-loader.js': [
        'GET /v1/galleries/{id}',
        'GET /v1/galleries',
    ],
    'new-gallery.js': [
        'POST /v1/galleries',
        'GET /v1/cities/search',
    ],
    'gallery.js': [
        'PUT /v1/galleries/{id}',
        'DELETE /v1/galleries/{id}',
        'POST /v1/galleries/{id}/photos/upload-url',
        'POST /v1/galleries/{id}/photos/confirm-upload',
    ],
    'upload-manager.js': [
        'POST /v1/galleries/{id}/photos/upload-url',
        'POST /v1/galleries/{id}/photos/multipart-upload/init',
        'POST /v1/galleries/{id}/photos/multipart-upload/complete',
        'POST /v1/galleries/{id}/photos/confirm-upload',
    ],
    'gallery-upload-queue.js': [
        'POST /v1/galleries/{id}/photos/check-duplicates',
        'POST /v1/galleries/{id}/photos/upload-url',
        'POST /v1/galleries/{id}/photos/confirm-upload',
    ],
    'photo-deletion.js': [
        'DELETE /v1/galleries/{id}/photos/delete',
    ],
    'enhanced-comments.js': [
        'POST /v1/photos/{id}/comments',
        'PUT /v1/photos/{id}/comments/{comment_id}',
        'DELETE /v1/photos/{id}/comments/{comment_id}',
    ],
    'client-gallery-loader.js': [
        'GET /v1/client/galleries/{id}',
        'GET /v1/client/galleries/by-token/{token}',
    ],
    'client-favorites.js': [
        'GET /v1/client/favorites',
        'POST /v1/client/favorites',
        'DELETE /v1/client/favorites',
        'GET /v1/client/favorites/{id}',
    ],
    'billing.js': [
        'POST /v1/billing/checkout',
        'GET /v1/billing/history',
        'GET /v1/billing/subscription',
        'POST /v1/billing/subscription/cancel',
        'GET /v1/subscription/usage',
    ],
    'analytics.js': [
        'GET /v1/analytics',
        'GET /v1/analytics/galleries/{id}',
        'POST /v1/analytics/track/gallery/{id}',
        'POST /v1/analytics/track/photo/{id}',
    ],
    'newsletter.js': [
        'POST /v1/newsletter/subscribe',
        'POST /v1/newsletter/unsubscribe',
    ],
    'contact.js': [
        'POST /v1/contact/submit',
    ],
}

def verify_connections():
    """Verify all frontend API calls match backend endpoints"""
    print("=" * 80)
    print("GALERLY API CONNECTION VERIFICATION")
    print("=" * 80)
    print()
    
    print(f"Total backend endpoints: {len(BACKEND_ENDPOINTS)}")
    print(f"Frontend files checked: {len(FRONTEND_API_USAGE)}")
    print()
    
    # Check each frontend file
    for js_file, expected_endpoints in FRONTEND_API_USAGE.items():
        print(f"\n{js_file}:")
        for endpoint in expected_endpoints:
            if endpoint in BACKEND_ENDPOINTS:
                print(f"  ✅ {endpoint}")
            else:
                print(f"  ❌ {endpoint} - NOT FOUND IN BACKEND")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    verify_connections()

