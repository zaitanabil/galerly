"""
Galerly API - Clean Modular Architecture
Main entry point for AWS Lambda
"""
import json
from datetime import datetime

# Import utilities
from utils.response import create_response
from utils.auth import get_user_from_token

# Import handlers
from handlers.auth_handler import handle_register, handle_login, handle_logout, handle_get_me, handle_request_password_reset, handle_reset_password, handle_request_verification_code, handle_verify_code, handle_delete_account
from handlers.city_handler import handle_city_search
from handlers.profile_handler import handle_update_profile
from handlers.gallery_handler import (
    handle_list_galleries,
    handle_create_gallery,
    handle_get_gallery,
    handle_update_gallery,
    handle_delete_gallery,
    handle_duplicate_gallery,
    handle_archive_gallery
)
from handlers.photo_handler import (
    handle_upload_photo,
    handle_check_duplicates,
    handle_update_photo,
    handle_add_comment,
    handle_update_comment,
    handle_delete_comment,
    handle_search_photos,
    handle_delete_photos,
    handle_send_batch_notification
)
from handlers.photo_upload_presigned import (
    handle_get_upload_url,
    handle_confirm_upload,
    handle_direct_upload
)
from handlers.multipart_upload_handler import (
    handle_initialize_multipart_upload,
    handle_complete_multipart_upload,
    handle_abort_multipart_upload
)
from handlers.dashboard_handler import handle_dashboard_stats
from handlers.client_handler import handle_client_galleries, handle_get_client_gallery, handle_get_client_gallery_by_token
from handlers.photographer_handler import handle_list_photographers, handle_get_photographer
from handlers.newsletter_handler import handle_newsletter_subscribe, handle_newsletter_unsubscribe
from handlers.contact_handler import handle_contact_submit
from handlers.billing_handler import (
    handle_create_checkout_session,
    handle_get_billing_history,
    handle_get_invoice_pdf,
    handle_get_subscription,
    handle_cancel_subscription,
    handle_stripe_webhook,
    handle_check_downgrade_limits,
    handle_downgrade_subscription,
    handle_change_plan
)
from handlers.refund_handler import (
    handle_check_refund_eligibility,
    handle_request_refund,
    handle_get_refund_status
)
from handlers.subscription_handler import handle_get_usage
from handlers.analytics_handler import (
    handle_get_gallery_analytics,
    handle_get_overall_analytics,
    handle_track_gallery_view,
    handle_track_photo_view,
    handle_track_photo_download,
    handle_track_gallery_share,
    handle_track_photo_share,
    handle_track_bulk_download,
    handle_get_bulk_downloads
)
from handlers.client_favorites_handler import (
    handle_add_favorite,
    handle_remove_favorite,
    handle_get_favorites,
    handle_check_favorite
)
from handlers.portfolio_handler import (
    handle_get_portfolio_settings,
    handle_update_portfolio_settings,
    handle_get_public_portfolio
)
from handlers.social_handler import (
    handle_get_gallery_share_info,
    handle_get_photo_share_info
)
from handlers.client_feedback_handler import (
    handle_submit_client_feedback,
    handle_get_gallery_feedback
)
from handlers.visitor_tracking_handler import (
    handle_track_visit,
    handle_track_event,
    handle_track_session_end,
    handle_get_visitor_analytics
)
from handlers.notification_handler import (
    handle_get_preferences,
    handle_update_preferences,
    handle_send_custom_notification,
    handle_send_selection_reminder
)
from handlers.gallery_expiration_handler import (
    handle_check_expiring_galleries,
    handle_manual_expiry_check
)
from handlers.bulk_download_handler import (
    handle_bulk_download,
    handle_bulk_download_by_token
)
from handlers.email_template_handler import (
    handle_list_templates,
    handle_get_template,
    handle_save_template,
    handle_delete_template,
    handle_preview_template
)

def handler(event, context):
    """Main Lambda handler with clean routing"""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # Get path and method
        raw_path = event.get('path', '/')
        method = event.get('httpMethod', 'GET')
        
        # Strip the obfuscated base path if present (from API Gateway custom domain mapping)
        path = raw_path.replace('/prod', '')
        if path.startswith('/xb667e3fa92f9776468017a9758f31ba4'):
            path = path.replace('/xb667e3fa92f9776468017a9758f31ba4', '', 1)
        
        # Log request (without sensitive data)
        print(f"Request: {method} {path}")
        # Parse body (keep raw body for webhook signature verification)
        raw_body_str = event.get('body', '')
        body = {}
        if raw_body_str:
            try:
                body = json.loads(raw_body_str)
            except:
                body = {}
        
        # ================================================================
        # PUBLIC ENDPOINTS (No authentication required)
        # ================================================================
        
        # Root endpoint
        if path in ['/', '', '/v1', '/v1/']:
            return create_response(200, {
                'name': 'Galerly API',
                'version': '3.0.0',
                'architecture': 'Modular',
                'storage': 'DynamoDB (isolated per photographer)',
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        # Health check
        if path in ['/health', '/v1/health']:
            return create_response(200, {
                'status': 'healthy',
                'architecture': 'modular',
                'storage': 'DynamoDB',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        # Authentication endpoints
        if path == '/v1/auth/request-verification' and method == 'POST':
            return handle_request_verification_code(body)
        
        if path == '/v1/auth/verify-email' and method == 'POST':
            return handle_verify_code(body)
        
        if path == '/v1/auth/register' and method == 'POST':
            return handle_register(body)
        
        if path == '/v1/auth/login' and method == 'POST':
            return handle_login(body)
        
        if path == '/v1/auth/logout' and method == 'POST':
            return handle_logout(event)
        
        if path == '/v1/auth/delete-account' and method == 'DELETE':
            # Requires authentication
            user = get_user_from_token(event)
            if not user:
                return create_response(401, {'error': 'Authentication required'})
            return handle_delete_account(user)
        
        if path == '/v1/auth/forgot-password' and method == 'POST':
            return handle_request_password_reset(body)
        
        if path == '/v1/auth/reset-password' and method == 'POST':
            return handle_reset_password(body)
        
        # City search endpoint (PUBLIC)
        if path == '/v1/cities/search' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            query = query_params.get('q', '')
            return handle_city_search(query)
        
        # Photographer directory endpoints (PUBLIC - no auth required)
        if path == '/v1/photographers' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_photographers(query_params)
        
        if path.startswith('/v1/photographers/') and method == 'GET':
            photographer_id = path.split('/')[-1]
            return handle_get_photographer(photographer_id)
        
        # Public portfolio endpoint (with customization)
        if path.startswith('/v1/portfolio/') and method == 'GET':
            photographer_id = path.split('/')[-1]
            if photographer_id != 'settings':  # Avoid conflict with settings endpoint
                return handle_get_public_portfolio(photographer_id)
        
        # Social sharing endpoints (PUBLIC - for public galleries/photos)
        if path.startswith('/v1/share/gallery/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_gallery_share_info(gallery_id, user=None)
        
        if path.startswith('/v1/share/photo/') and method == 'GET':
            photo_id = path.split('/')[-1]
            return handle_get_photo_share_info(photo_id, user=None)
        
        # Newsletter endpoints (PUBLIC)
        if path == '/v1/newsletter/subscribe' and method == 'POST':
            return handle_newsletter_subscribe(body)
        
        if path == '/v1/newsletter/unsubscribe' and method == 'POST':
            return handle_newsletter_unsubscribe(body)
        
        # Contact/Support endpoint (PUBLIC)
        if path == '/v1/contact/submit' and method == 'POST':
            return handle_contact_submit(body)
        
        # Client feedback endpoint (PUBLIC - clients can submit feedback)
        if path.startswith('/v1/client/feedback/') and method == 'POST':
            gallery_id = path.split('/')[-1]
            return handle_submit_client_feedback(gallery_id, body)
        
        # Client gallery by token endpoint (PUBLIC - anyone with token can view)
        if path.startswith('/v1/client/galleries/by-token/') and method == 'GET':
            share_token = path.split('/')[-1]
            return handle_get_client_gallery_by_token(share_token)
        
        # Bulk download by token endpoint (PUBLIC - for clients with share token)
        if path == '/v1/downloads/bulk/by-token' and method == 'POST':
            return handle_bulk_download_by_token(event)
        
        # Stripe webhook endpoint (PUBLIC - verified by signature)
        if path == '/v1/billing/webhook' and method == 'POST':
            # Get Stripe signature from headers
            headers = event.get('headers', {}) or {}
            stripe_signature = headers.get('stripe-signature') or headers.get('Stripe-Signature') or ''
            # Use raw body string for signature verification
            return handle_stripe_webhook(body, stripe_signature, raw_body_str)
        
        # Analytics tracking endpoints (PUBLIC - no auth required, gets user_id from gallery)
        # viewer_user_id is the user viewing (if authenticated), used to skip tracking if they're the owner
        if path.startswith('/v1/analytics/track/gallery/') and method == 'POST':
            gallery_id = path.split('/')[-1]
            metadata = body.get('metadata', {})
            # Get viewer's user_id from token if available (to check if they're the owner)
            user = get_user_from_token(event)
            viewer_user_id = user['id'] if user else None
            return handle_track_gallery_view(gallery_id, viewer_user_id, metadata)
        
        if path.startswith('/v1/analytics/track/photo/') and method == 'POST':
            photo_id = path.split('/')[-1]
            gallery_id = body.get('gallery_id')
            metadata = body.get('metadata', {})
            # Get viewer's user_id from token if available (to check if they're the owner)
            user = get_user_from_token(event)
            viewer_user_id = user['id'] if user else None
            return handle_track_photo_view(photo_id, gallery_id, viewer_user_id, metadata)
        
        if path.startswith('/v1/analytics/track/download/') and method == 'POST':
            photo_id = path.split('/')[-1]
            gallery_id = body.get('gallery_id')
            metadata = body.get('metadata', {})
            # Get viewer's user_id from token if available (to check if they're the owner)
            user = get_user_from_token(event)
            viewer_user_id = user['id'] if user else None
            return handle_track_photo_download(photo_id, gallery_id, viewer_user_id, metadata)
        
        # Share tracking endpoints (PUBLIC - can track shares from anyone)
        if path.startswith('/v1/analytics/track/share/gallery/') and method == 'POST':
            gallery_id = path.split('/')[-1]
            platform = body.get('platform', 'unknown')
            metadata = body.get('metadata', {})
            # Get user from token if available (for analytics)
            user = get_user_from_token(event)
            return handle_track_gallery_share(gallery_id, platform, user, metadata)
        
        if path.startswith('/v1/analytics/track/share/photo/') and method == 'POST':
            photo_id = path.split('/')[-1]
            platform = body.get('platform', 'unknown')
            metadata = body.get('metadata', {})
            # Get user from token if available (for analytics)
            user = get_user_from_token(event)
            return handle_track_photo_share(photo_id, platform, user, metadata)
        
        # Bulk download tracking endpoint (PUBLIC - tracks downloads from all users)
        if path.startswith('/v1/analytics/track/bulk-download/') and method == 'POST':
            gallery_id = path.split('/')[-1]
            metadata = body.get('metadata', {})
            # Get user from token if available (for analytics)
            user = get_user_from_token(event)
            viewer_user_id = user.get('id') if user else None
            # Extract IP address from request
            request_context = event.get('requestContext', {})
            identity = request_context.get('identity', {})
            client_ip = identity.get('sourceIp', 'unknown')
            return handle_track_bulk_download(gallery_id, viewer_user_id, metadata, client_ip)
        
        # Visitor tracking endpoints (PUBLIC - tracks ALL visitors for UX improvement)
        # These are mandatory for understanding user behavior and improving UX
        if path == '/v1/visitor/track/visit' and method == 'POST':
            return handle_track_visit(body)
        
        if path == '/v1/visitor/track/event' and method == 'POST':
            return handle_track_event(body)
        
        if path == '/v1/visitor/track/session-end' and method == 'POST':
            return handle_track_session_end(body)
        
        # ================================================================
        # AUTHENTICATED ENDPOINTS (Require valid token)
        # ================================================================
        
        user = get_user_from_token(event)
        if not user:
            return create_response(401, {'error': 'Authentication required'})
        
        # Log authenticated request (without email for security)
        print(f"Authenticated request from user: {user.get('id')}")
        
        # Get current user info
        if path == '/v1/auth/me' and method == 'GET':
            return handle_get_me(user)
        
        # Profile update endpoint
        if path == '/v1/profile' and method == 'PUT':
            return handle_update_profile(user, body)
        
        # Portfolio settings endpoints
        if path == '/v1/portfolio/settings' and method == 'GET':
            return handle_get_portfolio_settings(user)
        
        if path == '/v1/portfolio/settings' and method == 'PUT':
            return handle_update_portfolio_settings(user, body)
        
        # Dashboard
        if path == '/v1/dashboard' and method == 'GET':
            return handle_dashboard_stats(user)
        
        # Dashboard stats (explicit endpoint for clarity)
        if path == '/v1/dashboard/stats' and method == 'GET':
            return handle_dashboard_stats(user)
        
        # Client galleries endpoint
        if path == '/v1/client/galleries' and method == 'GET':
            return handle_client_galleries(user)
        
        # Client single gallery endpoint
        if path.startswith('/v1/client/galleries/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_client_gallery(gallery_id, user)
        
        # Client favorites endpoints
        if path == '/v1/client/favorites' and method == 'GET':
            return handle_get_favorites(user)
        
        if path == '/v1/client/favorites' and method == 'POST':
            return handle_add_favorite(user, body)
        
        if path == '/v1/client/favorites' and method == 'DELETE':
            return handle_remove_favorite(user, body)
        
        if path.startswith('/v1/client/favorites/') and method == 'GET':
            photo_id = path.split('/')[-1]
            return handle_check_favorite(user, photo_id)
        
        # Photos endpoints (MUST come BEFORE gallery endpoints to avoid path collision)
        if path.startswith('/v1/galleries/') and '/photos' in path:
            parts = path.split('/')
            gallery_id = parts[parts.index('galleries') + 1]
            
            # Presigned URL endpoints (NEW - for large file uploads)
            if '/upload-url' in path and method == 'POST':
                return handle_get_upload_url(gallery_id, user, event)
            
            if '/direct-upload' in path and method == 'POST':
                return handle_direct_upload(gallery_id, user, event)
            
            if '/confirm-upload' in path and method == 'POST':
                return handle_confirm_upload(gallery_id, user, event)
            
            # Multipart upload endpoints (for files > 10MB)
            if '/multipart-upload/init' in path and method == 'POST':
                return handle_initialize_multipart_upload(gallery_id, user, event)
            
            if '/multipart-upload/complete' in path and method == 'POST':
                return handle_complete_multipart_upload(gallery_id, user, event)
            
            if '/multipart-upload/abort' in path and method == 'POST':
                return handle_abort_multipart_upload(gallery_id, user, event)
            
            # Check for duplicate detection endpoint
            if '/check-duplicates' in path and method == 'POST':
                return handle_check_duplicates(gallery_id, user, event)
            
            # Check for delete photos endpoint (batch delete)
            if '/delete' in path and method == 'DELETE':
                return handle_delete_photos(gallery_id, user, event)
            
            if method == 'POST':
                return handle_upload_photo(gallery_id, user, event)
        
        # Bulk download endpoint (authenticated photographers/clients) - OUTSIDE photos section
        if path.startswith('/v1/galleries/') and '/download-bulk' in path and method == 'POST':
            parts = path.split('/')
            gallery_id = parts[parts.index('galleries') + 1]
            return handle_bulk_download(gallery_id, user, event)
        
        # Batch email notification endpoint
        if path.startswith('/v1/galleries/') and '/notify-clients' in path and method == 'POST':
            parts = path.split('/')
            gallery_id = parts[parts.index('galleries') + 1]
            return handle_send_batch_notification(gallery_id, user)
        
        # Galleries
        if path == '/v1/galleries' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_galleries(user, query_params)
        
        if path == '/v1/galleries' and method == 'POST':
            return handle_create_gallery(user, body)
        
        if path.startswith('/v1/galleries/'):
            parts = path.split('/')
            gallery_index = parts.index('galleries')
            
            # Check if it's a special action endpoint
            if len(parts) > gallery_index + 2:
                action = parts[gallery_index + 2]
                gallery_id = parts[gallery_index + 1]
                
                if action == 'duplicate' and method == 'POST':
                    return handle_duplicate_gallery(gallery_id, user, body)
                
                if action == 'archive' and method == 'POST':
                    return handle_archive_gallery(gallery_id, user, archive=True)
                
                if action == 'unarchive' and method == 'POST':
                    return handle_archive_gallery(gallery_id, user, archive=False)
            
            # Regular gallery operations
            gallery_id = parts[-1]
            
            if method == 'GET':
                return handle_get_gallery(gallery_id, user)
            
            if method == 'PUT':
                return handle_update_gallery(gallery_id, user, body)
            
            if method == 'DELETE':
                return handle_delete_gallery(gallery_id, user)
        
        # Photo comments
        if path.startswith('/v1/photos/') and '/comments' in path:
            parts = path.split('/')
            photo_id = parts[parts.index('photos') + 1]
            
            # Check if it's a specific comment (update/delete)
            if len(parts) > parts.index('comments') + 1:
                comment_id = parts[parts.index('comments') + 1]
                
                if method == 'PUT':
                    return handle_update_comment(photo_id, comment_id, user, body)
                
                if method == 'DELETE':
                    return handle_delete_comment(photo_id, comment_id, user)
            
            # Add new comment
            if method == 'POST':
                return handle_add_comment(photo_id, user, body)
        
        # Photo search endpoint
        if path == '/v1/photos/search' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_search_photos(user, query_params)
        
        # Social sharing endpoints (AUTHENTICATED - for user's own galleries/photos)
        if path.startswith('/v1/share/gallery/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_gallery_share_info(gallery_id, user)
        
        if path.startswith('/v1/share/photo/') and method == 'GET':
            photo_id = path.split('/')[-1]
            return handle_get_photo_share_info(photo_id, user)
        
        # Photo update (status, etc.)
        if path.startswith('/v1/photos/') and '/comments' not in path:
            photo_id = path.split('/')[-1]
            
            if method == 'PUT':
                return handle_update_photo(photo_id, body, user)
        
        # Billing endpoints
        if path == '/v1/billing/checkout' and method == 'POST':
            return handle_create_checkout_session(user, body)
        
        if path == '/v1/billing/history' and method == 'GET':
            return handle_get_billing_history(user)
        
        if path.startswith('/v1/billing/invoice/') and path.endswith('/pdf') and method == 'GET':
            # Extract invoice_id from path: /v1/billing/invoice/{invoice_id}/pdf
            invoice_id = path.split('/')[-2]
            return handle_get_invoice_pdf(user, invoice_id)
        
        if path == '/v1/billing/subscription' and method == 'GET':
            return handle_get_subscription(user)
        
        if path == '/v1/billing/subscription/cancel' and method == 'POST':
            return handle_cancel_subscription(user)
        
        if path == '/v1/billing/subscription/check-downgrade' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            target_plan = query_params.get('target_plan', 'free')
            return handle_check_downgrade_limits(user, target_plan)
        
        if path == '/v1/billing/subscription/downgrade' and method == 'POST':
            return handle_downgrade_subscription(user, body)
        
        if path == '/v1/billing/subscription/change-plan' and method == 'POST':
            return handle_change_plan(user, body)
        
        # Refund endpoints
        if path == '/v1/billing/refund/check' and method == 'GET':
            return handle_check_refund_eligibility(user)
        
        if path == '/v1/billing/refund/request' and method == 'POST':
            return handle_request_refund(user, body)
        
        if path == '/v1/billing/refund/status' and method == 'GET':
            return handle_get_refund_status(user)
        
        # Subscription/Usage endpoints
        if path == '/v1/subscription/usage' and method == 'GET':
            return handle_get_usage(user)
        
        # Analytics endpoints
        if path == '/v1/analytics' and method == 'GET':
            return handle_get_overall_analytics(user)
        
        if path == '/v1/analytics/bulk-downloads' and method == 'GET':
            return handle_get_bulk_downloads(user)
        
        if path.startswith('/v1/analytics/galleries/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_gallery_analytics(user, gallery_id)
        
        # Client feedback endpoint (AUTHENTICATED - photographers can view feedback)
        if path.startswith('/v1/client/feedback/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_gallery_feedback(gallery_id, user)
        
        # Visitor analytics endpoint (AUTHENTICATED - photographers can view their site analytics)
        if path == '/v1/visitor/analytics' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_get_visitor_analytics(user, query_params)
        
        # ================================================================
        # NOTIFICATION PREFERENCES ENDPOINTS
        # ================================================================
        
        # Get notification preferences
        if path == '/v1/notifications/preferences' and method == 'GET':
            return handle_get_preferences(user)
        
        # Update notification preferences
        if path == '/v1/notifications/preferences' and method == 'PUT':
            return handle_update_preferences(user, body)
        
        # Send custom notification to client
        if path == '/v1/notifications/send-custom' and method == 'POST':
            return handle_send_custom_notification(user, body)
        
        # Send selection reminder to client (matches frontend call)
        if path == '/v1/notifications/send-selection-reminder' and method == 'POST':
            return handle_send_selection_reminder(user, body)
        
        # ================================================================
        # EMAIL TEMPLATES (Pro Feature Only)
        # ================================================================
        
        # List all email templates
        if path == '/v1/email-templates' and method == 'GET':
            return handle_list_templates(user)
        
        # Get specific template
        if path.startswith('/v1/email-templates/') and method == 'GET' and '/preview' not in path:
            parts = path.split('/')
            template_type = parts[-1]
            return handle_get_template(user, template_type)
        
        # Save/update template
        if path.startswith('/v1/email-templates/') and method == 'PUT':
            parts = path.split('/')
            template_type = parts[-1]
            return handle_save_template(user, template_type, body)
        
        # Delete custom template (revert to default)
        if path.startswith('/v1/email-templates/') and method == 'DELETE':
            parts = path.split('/')
            template_type = parts[-1]
            return handle_delete_template(user, template_type)
        
        # Preview template with sample data
        if path.startswith('/v1/email-templates/') and '/preview' in path and method == 'POST':
            parts = path.split('/')
            template_type = parts[parts.index('email-templates') + 1]
            return handle_preview_template(user, template_type, body)
        
        # Manual expiry check (photographer can test expiry notifications)
        if path == '/v1/galleries/check-expiring' and method == 'POST':
            return handle_manual_expiry_check(user)
        
        # ================================================================
        # ADMIN/SYSTEM ENDPOINTS
        # ================================================================
        
        # Gallery cleanup (automated job - can be triggered manually)
        if path == '/v1/admin/cleanup/galleries' and method == 'POST':
            from handlers.gallery_expiration_handler import run_daily_cleanup
            return run_daily_cleanup()
        
        # ================================================================
        # 404 - Endpoint not found
        # ================================================================
        return create_response(404, {
            'error': 'Endpoint not found',
            'path': path,
            'method': method
        })
    
    except Exception as e:
        error_msg = str(e) if e else 'Unknown error'
        error_type = type(e).__name__
        print(f"❌ Error ({error_type}): {error_msg}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'Internal server error',
            'message': error_msg,
            'type': error_type,
            'path': path,
            'method': method
        })

# For local development - run Flask directly
if __name__ == '__main__':
    import os
    from flask import Flask, request
    from flask_cors import CORS
    
    def get_required_env(key):
        """Get required environment variable or raise error"""
        value = os.environ.get(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value
    
    app = Flask(__name__)
    
    # Get CORS origins from environment - REQUIRED
    frontend_url = get_required_env('FRONTEND_URL')
    allowed_origins = [frontend_url]
    
    # Add additional CORS origins from environment if specified
    additional_origins = os.environ.get('CORS_ADDITIONAL_ORIGINS')
    if additional_origins:
        allowed_origins.extend([origin.strip() for origin in additional_origins.split(',')])
    
    # Enable CORS for local development
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Cookie"],
            "supports_credentials": True,
            "expose_headers": ["Set-Cookie"]
        }
    })
    
    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def catch_all(path):
        """Route all requests to the Lambda handler"""
        # Get client IP address (support both direct and proxied requests)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            client_ip = client_ip.split(',')[0].strip()
        
        event = {
            'httpMethod': request.method,
            'path': '/' + path if path else '/',
            'headers': dict(request.headers),
            'body': request.get_data(as_text=True) if request.data else None,
            'queryStringParameters': dict(request.args) if request.args else None,
            'requestContext': {
                'identity': {
                    'sourceIp': client_ip
                }
            }
        }
        
        response = handler(event, None)
        
        # Convert Lambda response to Flask response
        from flask import Response
        return Response(
            response.get('body', ''),
            status=response.get('statusCode', 200),
            headers=response.get('headers', {})
        )
    
    # Get Flask configuration from environment - REQUIRED
    port = int(get_required_env('PORT'))
    host = get_required_env('FLASK_HOST')
    debug_str = get_required_env('FLASK_DEBUG').lower()
    debug = debug_str == 'true'
    
    # Get values for logging
    environment = get_required_env('ENVIRONMENT')
    aws_endpoint = os.environ.get('AWS_ENDPOINT_URL')
    
    print(f"🚀 Starting Galerly API on {host}:{port}")
    print(f"   Environment: {environment}")
    print(f"   LocalStack: {aws_endpoint if aws_endpoint else 'not configured'}")
    print(f"   CORS enabled for: {', '.join(allowed_origins)}")
    
    app.run(host=host, port=port, debug=debug)
