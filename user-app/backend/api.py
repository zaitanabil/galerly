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
from handlers.auth_handler import (
    handle_register, handle_login, handle_logout, handle_get_me, 
    handle_request_password_reset, handle_reset_password, 
    handle_request_verification_code, handle_verify_code, 
    handle_delete_account, handle_generate_api_key, handle_get_api_key
)

from handlers.city_handler import handle_city_search
from handlers.profile_handler import handle_update_profile
from handlers.gallery_handler import (
    handle_list_galleries,
    handle_create_gallery,
    handle_get_gallery,
    handle_update_gallery,
    handle_delete_gallery,
    handle_duplicate_gallery,
    handle_archive_gallery,
    handle_archive_originals
)
from handlers.photo_handler import (
    handle_upload_photo,
    handle_get_photo,
    handle_check_duplicates,
    handle_update_photo,
    handle_add_comment,
    handle_update_comment,
    handle_delete_comment,
    handle_search_photos,
    handle_delete_photos,
    handle_send_batch_notification
)
from handlers.engagement_analytics_handler import (
    handle_track_visit,
    handle_track_event,
    handle_track_photo_engagement,
    handle_track_video_engagement,
    handle_get_gallery_engagement,
    handle_get_client_preferences,
    handle_get_overall_engagement,
    handle_get_gallery_engagement_summary
)
from handlers.realtime_viewers_handler import (
    handle_track_viewer_heartbeat,
    handle_get_active_viewers,
    handle_viewer_disconnect
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
    handle_check_favorite,
    handle_submit_favorites
)
from handlers.portfolio_handler import (
    handle_get_portfolio_settings,
    handle_update_portfolio_settings,
    handle_get_public_portfolio,
    handle_verify_domain,
    handle_check_domain_status
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
    handle_track_visit as handle_track_visitor_visit,
    handle_track_event as handle_track_visitor_event,
    handle_track_session_end,
    handle_get_visitor_analytics
)
from handlers.notification_handler import (
    handle_get_preferences,
    handle_update_preferences,
    handle_send_custom_notification,
    handle_send_selection_reminder
)
from handlers.invoice_handler import (
    handle_list_invoices,
    handle_create_invoice,
    handle_get_invoice,
    handle_update_invoice,
    handle_delete_invoice,
    handle_send_invoice,
    handle_mark_invoice_paid
)
from handlers.appointment_handler import (
    handle_list_appointments,
    handle_create_appointment,
    handle_update_appointment,
    handle_delete_appointment,
    handle_create_public_appointment_request
)
from handlers.availability_handler import (
    handle_get_availability_settings,
    handle_update_availability_settings,
    handle_get_available_slots,
    handle_check_slot_availability,
    handle_get_busy_times,
    handle_generate_ical_feed
)
from handlers.branding_handler import (
    handle_get_branding_settings,
    handle_update_branding_settings,
    handle_upload_branding_logo,
    handle_get_public_branding
)
from handlers.contract_handler import (
    handle_list_contracts,
    handle_create_contract,
    handle_get_contract,
    handle_update_contract,
    handle_delete_contract,
    handle_send_contract,
    handle_sign_contract
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
from handlers.email_automation_handler import (
    handle_schedule_automated_email,
    handle_setup_gallery_automation,
    handle_cancel_scheduled_email,
    handle_list_scheduled_emails,
    handle_process_email_queue
)
from handlers.raw_vault_handler import (
    handle_archive_to_vault,
    handle_list_vault_files,
    handle_request_retrieval,
    handle_check_retrieval_status,
    handle_download_vault_file,
    handle_delete_vault_file
)
from handlers.seo_handler import (
    handle_generate_sitemap,
    handle_generate_schema_markup,
    handle_validate_og_tags,
    handle_get_seo_settings,
    handle_update_seo_settings,
    handle_get_robots_txt
)
from handlers.leads_handler import (
    handle_capture_lead,
    handle_list_leads,
    handle_get_lead,
    handle_update_lead,
    handle_cancel_followup_sequence
)
from handlers.testimonials_handler import (
    handle_list_testimonials,
    handle_create_testimonial,
    handle_update_testimonial,
    handle_delete_testimonial,
    handle_request_testimonial
)
from handlers.services_handler import (
    handle_list_services,
    handle_create_service,
    handle_update_service,
    handle_delete_service,
    handle_get_service
)
from handlers.sales_handler import (
    handle_list_packages,
    handle_create_package,
    handle_create_payment_intent,
    handle_confirm_sale,
    handle_get_download,
    handle_list_sales
)
from handlers.payment_reminders_handler import (
    handle_create_reminder_schedule,
    handle_cancel_reminder_schedule
)
from handlers.onboarding_handler import (
    handle_create_onboarding_workflow,
    handle_list_workflows,
    handle_update_workflow,
    handle_delete_workflow
)
from handlers.analytics_export_handler import (
    handle_export_analytics_csv,
    handle_export_analytics_pdf
)
from handlers.invoice_pdf_handler import (
    handle_generate_invoice_pdf,
    handle_download_invoice_pdf
)
from handlers.contract_pdf_handler import (
    handle_generate_contract_pdf,
    handle_download_contract_pdf
)
from handlers.calendar_ics_handler import (
    handle_export_appointment_ics,
    handle_export_calendar_feed,
    handle_generate_calendar_token
)
from handlers.feature_requests_handler import (
    handle_list_feature_requests,
    handle_create_feature_request,
    handle_vote_feature_request,
    handle_unvote_feature_request,
    handle_update_feature_request_status
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
            
            # Pass cookie header to delete account handler so it can clear the session
            cookie_header = event.get('headers', {}).get('cookie') or event.get('headers', {}).get('Cookie')
            return handle_delete_account(user, cookie_header)
        
        # API Keys (Protected)
        if path == '/v1/auth/api-key' and method == 'POST':
            user = get_user_from_token(event)
            if not user: return create_response(401, {'error': 'Authentication required'})
            return handle_generate_api_key(user)
            
        if path == '/v1/auth/api-key' and method == 'GET':
            user = get_user_from_token(event)
            if not user: return create_response(401, {'error': 'Authentication required'})
            return handle_get_api_key(user)
        
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
        
        # Client favorites endpoints (PUBLIC - allows guest access via email in body/query)
        if path == '/v1/client/favorites' and method == 'GET':
            # user might be None
            user = get_user_from_token(event)
            query_params = event.get('queryStringParameters') or {}
            return handle_get_favorites(user, query_params)
        
        if path == '/v1/client/favorites' and method == 'POST':
            user = get_user_from_token(event)
            return handle_add_favorite(user, body)

        if path == '/v1/client/favorites/submit' and method == 'POST':
            user = get_user_from_token(event)
            return handle_submit_favorites(user, body)
        
        if path == '/v1/client/favorites' and method == 'DELETE':
            user = get_user_from_token(event)
            return handle_remove_favorite(user, body)
        
        if path.startswith('/v1/client/favorites/') and method == 'GET':
            photo_id = path.split('/')[-1]
            user = get_user_from_token(event)
            query_params = event.get('queryStringParameters') or {}
            return handle_check_favorite(user, photo_id, query_params)

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
        
        # New engagement analytics tracking endpoints (PUBLIC - for guest tracking)
        if path == '/v1/analytics/visit' and method == 'POST':
            return handle_track_visit(body)

        if path == '/v1/analytics/event' and method == 'POST':
            return handle_track_event(body)

        if path == '/v1/analytics/photo-engagement' and method == 'POST':
            return handle_track_photo_engagement(body)

        if path == '/v1/analytics/video-engagement' and method == 'POST':
            return handle_track_video_engagement(body)
        
        # Real-time viewer tracking endpoints (PUBLIC - for live globe)
        if path == '/v1/viewers/heartbeat' and method == 'POST':
            return handle_track_viewer_heartbeat(event)
        
        if path == '/v1/viewers/disconnect' and method == 'POST':
            return handle_viewer_disconnect(event)
        
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
        
        # Photo comments (PUBLIC - Allows guests to comment)
        if path.startswith('/v1/photos/') and '/comments' in path:
            parts = path.split('/')
            photo_id = parts[parts.index('photos') + 1]
            
            # Check if it's a specific comment (update/delete)
            if len(parts) > parts.index('comments') + 1:
                comment_id = parts[parts.index('comments') + 1]
                
                # Update/Delete - allow for authenticated users AND guests who own the comment
                user = get_user_from_token(event)  # Get user if authenticated, otherwise None
                
                # For guest users, create a temporary user object from localStorage info sent in headers
                if not user:
                    # Check if guest user info is in request body or headers
                    try:
                        # Try to get guest info from headers (sent by frontend)
                        headers = event.get('headers', {}) or {}
                        guest_name = headers.get('x-guest-name') or headers.get('X-Guest-Name')
                        guest_email = headers.get('x-guest-email') or headers.get('X-Guest-Email')
                        
                        if guest_name or guest_email:
                            # Create temporary guest user object for permission check
                            if guest_email:
                                guest_user_id = f"guest-{guest_email}"
                            else:
                                # If no email, we can't match against stored comments
                                guest_user_id = None
                            
                            if guest_user_id:
                                user = {
                                    'id': guest_user_id,
                                    'username': guest_name,
                                    'email': guest_email,
                                    'is_guest': True
                                }
                    except Exception as e:
                        print(f"Error creating guest user object: {str(e)}")
                
                if method == 'PUT':
                    return handle_update_comment(photo_id, comment_id, user, body)
                
                if method == 'DELETE':
                    return handle_delete_comment(photo_id, comment_id, user)
                    
            elif method == 'POST':
                # Add new comment - Publicly accessible (handler checks gallery settings)
                user = get_user_from_token(event) # Optional user
                return handle_add_comment(photo_id, user, body)

        # Photo details (PUBLIC - for polling comments etc)
        if path.startswith('/v1/photos/') and '/comments' not in path and method == 'GET':
             photo_id = path.split('/')[-1]
             return handle_get_photo(photo_id)

        # Visitor tracking endpoints (PUBLIC - tracks ALL visitors for UX improvement)
        # These are mandatory for understanding user behavior and improving UX
        if path == '/v1/visitor/track/visit' and method == 'POST':
            return handle_track_visit(body)
        
        if path == '/v1/visitor/track/event' and method == 'POST':
            return handle_track_event(body)
        
        if path == '/v1/visitor/track/session-end' and method == 'POST':
            return handle_track_session_end(body)
        
        # Public contract signing
        if path.startswith('/v1/public/contracts/') and method == 'GET':
            contract_id = path.split('/')[-1]
            return handle_get_contract(contract_id, user=None)
            
        if path.startswith('/v1/public/contracts/') and path.endswith('/sign') and method == 'POST':
             parts = path.split('/')
             contract_id = parts[-2]
             request_context = event.get('requestContext', {})
             identity = request_context.get('identity', {})
             ip_address = identity.get('sourceIp', 'unknown')
             return handle_sign_contract(contract_id, body, ip_address)

        # Public Booking Request
        if path.startswith('/v1/public/photographers/') and path.endswith('/appointments') and method == 'POST':
            parts = path.split('/')
            photographer_id = parts[-2]
            return handle_create_public_appointment_request(photographer_id, body)
        
        # Public availability endpoints
        if path.startswith('/v1/public/photographers/'):
            parts = path.split('/')
            if len(parts) >= 5:
                photographer_id = parts[4]
                query_params = event.get('queryStringParameters') or {}
                
                # Branding settings
                if '/branding' in path and method == 'GET':
                    return handle_get_public_branding(photographer_id)
                
                # Lead capture (contact/inquiry)
                if '/lead' in path and method == 'POST':
                    return handle_capture_lead(photographer_id, body)
                
                # Testimonials (public)
                if '/testimonials' in path:
                    if method == 'GET':
                        return handle_list_testimonials(photographer_id, query_params)
                    elif method == 'POST':
                        return handle_create_testimonial(photographer_id, body)
                
                # Services pricing (public)
                if '/services' in path:
                    if method == 'GET':
                        return handle_list_services(photographer_id, is_public=True)
                
                # Packages (public)
                if '/packages' in path and method == 'GET':
                    return handle_list_packages(photographer_id, is_public=True)
                
                if '/availability/available-slots' in path and method == 'GET':
                    return handle_get_available_slots(photographer_id, query_params)
                
                if '/availability/busy-times' in path and method == 'GET':
                    return handle_get_busy_times(photographer_id, query_params)
                
                if path.endswith('/calendar.ics') and method == 'GET':
                    return handle_generate_ical_feed(photographer_id)
        
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
        
        # Watermark logo upload endpoint
        if path == '/v1/profile/watermark-logo' and method == 'POST':
            from handlers.watermark_handler import handle_upload_watermark_logo
            return handle_upload_watermark_logo(user, body)
        
        # Branding settings
        if path == '/v1/profile/branding-settings' and method == 'GET':
            return handle_get_branding_settings(user)
        
        if path == '/v1/profile/branding-settings' and method == 'PUT':
            return handle_update_branding_settings(user, body)
        
        if path == '/v1/profile/branding-logo' and method == 'POST':
            return handle_upload_branding_logo(user, body)
        
        # Background jobs endpoints
        if path.startswith('/v1/jobs/'):
            from handlers.background_jobs_handler import handle_get_job_status, handle_process_background_job
            
            # Get job status
            if method == 'GET':
                job_id = path.split('/')[-1]
                return handle_get_job_status(user, job_id)
            
            # Process job (internal use / worker)
            if path.endswith('/process') and method == 'POST':
                job_id = path.split('/')[-2]
                return handle_process_background_job(job_id)
        
        # Portfolio settings endpoints
        if path == '/v1/portfolio/settings' and method == 'GET':
            return handle_get_portfolio_settings(user)
        
        if path == '/v1/portfolio/settings' and method == 'PUT':
            return handle_update_portfolio_settings(user, body)
        
        if path == '/v1/portfolio/domain-status' and method == 'GET':
            domain = event.get('queryStringParameters', {}).get('domain', '')
            return handle_check_domain_status(user, domain)
            
        if path == '/v1/portfolio/verify-domain' and method == 'POST':
            return handle_verify_domain(user, body)
        
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
                
                if action == 'archive-originals' and method == 'POST':
                    return handle_archive_originals(gallery_id, user)
            
            # Regular gallery operations
            gallery_id = parts[-1]
            
            if method == 'GET':
                return handle_get_gallery(gallery_id, user)
            
            if method == 'PUT':
                return handle_update_gallery(gallery_id, user, body)
            
            if method == 'DELETE':
                return handle_delete_gallery(gallery_id, user)
        
        # Photo comments - already handled in PUBLIC section above
        # Kept here for backward compatibility if needed
        # if path.startswith('/v1/photos/') and '/comments' in path:
        #     ...
        
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
        
        if path == '/v1/billing/customer-portal' and method == 'POST':
            from handlers.billing_handler import handle_create_customer_portal_session
            return handle_create_customer_portal_session(user, body)
        
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
        
        # Invoice management
        if path == '/v1/invoices' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_invoices(user, query_params)
        
        if path == '/v1/invoices' and method == 'POST':
            return handle_create_invoice(user, body)
        
        if path.startswith('/v1/invoices/'):
            parts = path.split('/')
            invoice_id = parts[3] if len(parts) > 3 else None
            
            # PDF generation routes
            if 'pdf' in parts and method == 'POST':
                event['pathParameters'] = {'invoice_id': invoice_id}
                return handle_generate_invoice_pdf(event)
            
            if 'pdf' in parts and 'download' in parts and method == 'GET':
                event['pathParameters'] = {'invoice_id': invoice_id}
                return handle_download_invoice_pdf(event)
            
            # Check for specific actions like /v1/invoices/{id}/send
            if parts[-1] == 'send' and method == 'POST':
                invoice_id = parts[-2]
                return handle_send_invoice(invoice_id, user)
            
            invoice_id = parts[-1]
            
            if method == 'GET':
                return handle_get_invoice(invoice_id, user)
                
            if method == 'PUT':
                # Check if marking as paid
                if 'mark-paid' in path:
                    return handle_mark_invoice_paid(invoice_id, user, body)
                return handle_update_invoice(invoice_id, user, body)
                
            if method == 'DELETE':
                return handle_delete_invoice(invoice_id, user)

        # Appointment scheduler
        if path == '/v1/appointments' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_appointments(user, query_params)
        
        if path == '/v1/appointments' and method == 'POST':
            return handle_create_appointment(user, body)
            
        if path.startswith('/v1/appointments/'):
            parts = path.split('/')
            appt_id = parts[3] if len(parts) > 3 else None
            
            # ICS export route
            if 'ics' in parts and method == 'GET':
                event['pathParameters'] = {'appointment_id': appt_id}
                return handle_export_appointment_ics(event)
            
            appt_id = path.split('/')[-1]
            if method == 'PUT':
                return handle_update_appointment(appt_id, user, body)
            if method == 'DELETE':
                return handle_delete_appointment(appt_id, user)
        
        # Calendar feed routes
        if path == '/v1/calendar/feed.ics' and method == 'GET':
            return handle_export_calendar_feed(event)
        
        if path == '/v1/calendar/token' and method == 'POST':
            return handle_generate_calendar_token(event)
        
        # Availability settings
        if path == '/v1/availability/settings' and method == 'GET':
            return handle_get_availability_settings(user)
        
        if path == '/v1/availability/settings' and method == 'PUT':
            return handle_update_availability_settings(user, body)
        
        # Check slot availability
        if path == '/v1/availability/check-slot' and method == 'POST':
            return handle_check_slot_availability(user['id'], body)
        
        # Get busy times for calendar
        if path == '/v1/availability/busy-times' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_get_busy_times(user['id'], query_params)

        # Contract management
        if path == '/v1/contracts' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_contracts(user, query_params)
        
        if path == '/v1/contracts' and method == 'POST':
            return handle_create_contract(user, body)
            
        if path.startswith('/v1/contracts/'):
            parts = path.split('/')
            contract_id = parts[3] if len(parts) > 3 else None
            
            # PDF generation routes
            if 'pdf' in parts and method == 'POST':
                event['pathParameters'] = {'contract_id': contract_id}
                return handle_generate_contract_pdf(event)
            
            if 'pdf' in parts and 'download' in parts and method == 'GET':
                event['pathParameters'] = {'contract_id': contract_id}
                return handle_download_contract_pdf(event)
            
            # Check for specific actions
            if parts[-1] == 'send' and method == 'POST':
                contract_id = parts[-2]
                return handle_send_contract(contract_id, user)
            
            contract_id = parts[-1]
            if method == 'GET':
                return handle_get_contract(contract_id, user)
            if method == 'PUT':
                return handle_update_contract(contract_id, user, body)
            if method == 'DELETE':
                return handle_delete_contract(contract_id, user)
        
        # RAW Vault management (Ultimate plan feature)
        if path == '/v1/raw-vault' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_vault_files(user, query_params)
        
        if path == '/v1/raw-vault' and method == 'POST':
            return handle_archive_to_vault(user, body)
        
        if path.startswith('/v1/raw-vault/'):
            parts = path.split('/')
            vault_id = parts[3] if len(parts) > 3 else None
            
            # Handle sub-actions: /raw-vault/{id}/retrieve, /raw-vault/{id}/download, etc.
            if len(parts) > 4:
                action = parts[4]
                if action == 'retrieve' and method == 'POST':
                    return handle_request_retrieval(vault_id, user, body)
                elif action == 'status' and method == 'GET':
                    return handle_check_retrieval_status(vault_id, user)
                elif action == 'download' and method == 'GET':
                    return handle_download_vault_file(vault_id, user)
            
            # Direct vault file operations
            if vault_id and method == 'DELETE':
                return handle_delete_vault_file(vault_id, user)
        
        # Subscription/Usage endpoints
        if path == '/v1/subscription/usage' and method == 'GET':
            return handle_get_usage(user)
        
        # Analytics endpoints
        # Support both /v1/analytics and /v1/analytics/overall
        if (path == '/v1/analytics' or path == '/v1/analytics/overall') and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            print(f"[API] Analytics request - path: {path}, query_params: {query_params}")
            # Use engagement analytics for more accurate data
            use_engagement = query_params.get('use_engagement', 'true').lower() == 'true'
            print(f"[API] Using engagement analytics: {use_engagement}")
            if use_engagement:
                return handle_get_overall_engagement(user)
            else:
                return handle_get_overall_analytics(user, query_params)
        
        # Analytics export routes
        if path == '/v1/analytics/export/csv' and method == 'GET':
            return handle_export_analytics_csv(event)
        
        if path == '/v1/analytics/export/pdf' and method == 'POST':
            return handle_export_analytics_pdf(event)
        
        if path == '/v1/analytics/bulk-downloads' and method == 'GET':
            return handle_get_bulk_downloads(user)
        
        # Visitor analytics endpoint (support both paths for compatibility)
        if (path == '/v1/analytics/visitors' or path == '/v1/visitor/analytics') and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_get_visitor_analytics(user, query_params)
        
        if path.startswith('/v1/analytics/galleries/') and method == 'GET':
            # Handle multiple analytics endpoints for galleries
            if '/engagement' in path:
                # GET /v1/analytics/galleries/{gallery_id}/engagement
                gallery_id = path.split('/')[4]
                return handle_get_gallery_engagement(user, gallery_id)
            elif '/client-preferences' in path:
                # GET /v1/analytics/galleries/{gallery_id}/client-preferences
                gallery_id = path.split('/')[4]
                return handle_get_client_preferences(user, gallery_id)
            else:
                # GET /v1/analytics/galleries/{gallery_id} - Use engagement analytics summary
            gallery_id = path.split('/')[-1]
                query_params = event.get('queryStringParameters') or {}
                use_engagement = query_params.get('use_engagement', 'true').lower() == 'true'
                if use_engagement:
                    return handle_get_gallery_engagement_summary(user, gallery_id)
                else:
                    return handle_get_gallery_analytics(user, gallery_id, query_params)
        
        # Video analytics endpoints
        if path == '/v1/videos/track-view' and method == 'POST':
            from handlers.video_analytics_handler import handle_track_video_view
            return handle_track_video_view(body)
        
        if path.startswith('/v1/videos/') and path.endswith('/analytics') and method == 'GET':
            from handlers.video_analytics_handler import handle_get_video_analytics
            photo_id = path.split('/')[-2]
            return handle_get_video_analytics(user, photo_id)
        
        # Client feedback endpoint (AUTHENTICATED - photographers can view feedback)
        if path.startswith('/v1/client/feedback/') and method == 'GET':
            gallery_id = path.split('/')[-1]
            return handle_get_gallery_feedback(gallery_id, user)
        
        # Real-time viewers endpoint (AUTHENTICATED - photographers view their active viewers)
        if path == '/v1/viewers/active' and method == 'GET':
            return handle_get_active_viewers(user)
        
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
        if path.startswith('/v1/email-templates/') and method == 'PUT' and '/preview' not in path:
            parts = path.split('/')
            template_type = parts[-1]
            return handle_save_template(user, template_type, body)
        
        # Delete custom template (revert to default)
        if path.startswith('/v1/email-templates/') and method == 'DELETE' and '/preview' not in path:
            parts = path.split('/')
            template_type = parts[-1]
            return handle_delete_template(user, template_type)
        
        # Preview template with sample data
        if path.startswith('/v1/email-templates/') and '/preview' in path and method == 'POST':
            parts = path.split('/')
            # Path should be: /v1/email-templates/{template_type}/preview
            # Extract template_type safely (it's before 'preview')
            try:
                preview_index = parts.index('preview')
                if preview_index > 0:
                    template_type = parts[preview_index - 1]
                    return handle_preview_template(user, template_type, body)
            except (ValueError, IndexError):
                return create_response(400, {'error': 'Invalid template preview path'})
        
        # ================================================================
        # EMAIL AUTOMATION (Pro/Ultimate Feature)
        # ================================================================
        
        # Schedule automated email
        if path == '/v1/email-automation/schedule' and method == 'POST':
            return handle_schedule_automated_email(user, body)
        
        # Setup gallery automation (auto-schedule reminders)
        if path == '/v1/email-automation/setup-gallery' and method == 'POST':
            return handle_setup_gallery_automation(user, body)
        
        # List scheduled emails
        if path == '/v1/email-automation/scheduled' and method == 'GET':
            gallery_id = event.get('queryStringParameters', {}).get('gallery_id')
            return handle_list_scheduled_emails(user, gallery_id)
        
        # Cancel scheduled email
        if path.startswith('/v1/email-automation/scheduled/') and method == 'DELETE':
            email_id = path.split('/')[-1]
            return handle_cancel_scheduled_email(user, email_id)
        
        # Manual expiry check (photographer can test expiry notifications)
        if path == '/v1/galleries/check-expiring' and method == 'POST':
            return handle_manual_expiry_check(user)
        
        # ================================================================
        # CRM & LEADS (Pro/Ultimate Feature)
        # ================================================================
        
        # List leads
        if path == '/v1/crm/leads' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_leads(user, query_params)
        
        # Get single lead
        if path.startswith('/v1/crm/leads/') and method == 'GET':
            lead_id = path.split('/')[-1]
            return handle_get_lead(user, lead_id)
        
        # Update lead
        if path.startswith('/v1/crm/leads/') and method == 'PUT':
            lead_id = path.split('/')[-1]
            return handle_update_lead(user, lead_id, body)
        
        # Cancel follow-up sequence for lead
        if path.startswith('/v1/crm/leads/') and path.endswith('/cancel-followup') and method == 'POST':
            lead_id = path.split('/')[-2]
            return handle_cancel_followup_sequence(user, lead_id)
        
        # List testimonials (photographer view - includes unapproved)
        if path == '/v1/crm/testimonials' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            query_params['show_all'] = 'true'
            return handle_list_testimonials(user['id'], query_params)
        
        # Update testimonial (approve/feature)
        if path.startswith('/v1/crm/testimonials/') and method == 'PUT':
            testimonial_id = path.split('/')[-1]
            return handle_update_testimonial(user, testimonial_id, body)
        
        # Delete testimonial
        if path.startswith('/v1/crm/testimonials/') and method == 'DELETE':
            testimonial_id = path.split('/')[-1]
            return handle_delete_testimonial(user, testimonial_id)
        
        # Request testimonial from client
        if path == '/v1/crm/testimonials/request' and method == 'POST':
            return handle_request_testimonial(user, body)
        
        # ================================================================
        # SERVICES MANAGEMENT
        # ================================================================
        
        # List photographer's services
        if path == '/v1/services' and method == 'GET':
            return handle_list_services(user['id'], is_public=False)
        
        # Create service
        if path == '/v1/services' and method == 'POST':
            return handle_create_service(user, body)
        
        # Get single service
        if path.startswith('/v1/services/') and method == 'GET':
            service_id = path.split('/')[-1]
            return handle_get_service(service_id, user['id'])
        
        # Update service
        if path.startswith('/v1/services/') and method == 'PUT':
            service_id = path.split('/')[-1]
            return handle_update_service(user, service_id, body)
        
        # Delete service
        if path.startswith('/v1/services/') and method == 'DELETE':
            service_id = path.split('/')[-1]
            return handle_delete_service(user, service_id)
        
        # ================================================================
        # PHOTO SALES & PACKAGES
        # ================================================================
        
        # List sales with revenue stats
        if path == '/v1/sales' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            return handle_list_sales(user, query_params)
        
        # Create payment intent
        if path == '/v1/sales/create-payment-intent' and method == 'POST':
            return handle_create_payment_intent(body)
        
        # Confirm sale after payment
        if path.startswith('/v1/sales/') and path.endswith('/confirm') and method == 'POST':
            sale_id = path.split('/')[-2]
            payment_intent_id = body.get('payment_intent_id')
            return handle_confirm_sale(sale_id, payment_intent_id)
        
        # List packages
        if path == '/v1/packages' and method == 'GET':
            return handle_list_packages(user['id'], is_public=False)
        
        # Create package
        if path == '/v1/packages' and method == 'POST':
            return handle_create_package(user, body)
        
        # Update package
        if path.startswith('/v1/packages/') and method == 'PUT':
            package_id = path.split('/')[-1]
            # Note: Need to implement handle_update_package in sales_handler.py
            return create_response(501, {'error': 'Update package endpoint pending implementation'})
        
        # Delete package
        if path.startswith('/v1/packages/') and method == 'DELETE':
            package_id = path.split('/')[-1]
            # Note: Need to implement handle_delete_package in sales_handler.py
            return create_response(501, {'error': 'Delete package endpoint pending implementation'})
        
        # Get download link (requires customer email verification)
        if path.startswith('/v1/downloads/') and method == 'GET':
            download_id = path.split('/')[-1]
            query_params = event.get('queryStringParameters') or {}
            customer_email = query_params.get('email', '')
            return handle_get_download(download_id, customer_email)
        
        # ================================================================
        # PAYMENT REMINDERS
        # ================================================================
        
        # Create reminder schedule for invoice
        if path.startswith('/v1/invoices/') and path.endswith('/reminders') and method == 'POST':
            invoice_id = path.split('/')[-2]
            return handle_create_reminder_schedule(user, invoice_id, body)
        
        # Cancel reminder schedule
        if path.startswith('/v1/invoices/') and path.endswith('/reminders') and method == 'DELETE':
            invoice_id = path.split('/')[-2]
            return handle_cancel_reminder_schedule(user, invoice_id)
        
        # ================================================================
        # CLIENT ONBOARDING WORKFLOWS
        # ================================================================
        
        # List onboarding workflows
        if path == '/v1/onboarding/workflows' and method == 'GET':
            return handle_list_workflows(user)
        
        # Create onboarding workflow
        if path == '/v1/onboarding/workflows' and method == 'POST':
            return handle_create_onboarding_workflow(user, body)
        
        # Update onboarding workflow
        if path.startswith('/v1/onboarding/workflows/') and method == 'PUT':
            workflow_id = path.split('/')[-1]
            return handle_update_workflow(user, workflow_id, body)
        
        # Delete onboarding workflow
        if path.startswith('/v1/onboarding/workflows/') and method == 'DELETE':
            workflow_id = path.split('/')[-1]
            return handle_delete_workflow(user, workflow_id)
        
        # ================================================================
        # SEO TOOLS (Pro/Ultimate Feature)
        # ================================================================
        
        # Generate sitemap.xml
        if path == '/v1/seo/sitemap' and method == 'GET':
            return handle_generate_sitemap(user)
        
        # Generate Schema.org markup
        if path == '/v1/seo/schema' and method == 'GET':
            return handle_generate_schema_markup(user)
        
        # Validate OG tags
        if path == '/v1/seo/validate-og' and method == 'POST':
            return handle_validate_og_tags(user, body)
        
        # Get SEO settings
        if path == '/v1/seo/settings' and method == 'GET':
            return handle_get_seo_settings(user)
        
        # Update SEO settings
        if path == '/v1/seo/settings' and method == 'PUT':
            return handle_update_seo_settings(user, body)
        
        # Get robots.txt
        if path == '/v1/seo/robots.txt' and method == 'GET':
            return handle_get_robots_txt(user)
        
        # ================================================================
        # ADMIN/SYSTEM ENDPOINTS
        # ================================================================
        
        # Gallery cleanup endpoint removed - galleries never expire
        
        # ================================================================
        # FEATURE REQUESTS & FEEDBACK
        # ================================================================
        
        # List feature requests
        if path == '/v1/feature-requests' and method == 'GET':
            return handle_list_feature_requests(event)
        
        # Submit feature request
        if path == '/v1/feature-requests' and method == 'POST':
            return handle_create_feature_request(event)
        
        # Vote/unvote on feature request
        if path.startswith('/v1/feature-requests/') and '/vote' in path:
            request_id = path.split('/')[3]
            event['pathParameters'] = {'request_id': request_id}
            
            if method == 'POST':
                return handle_vote_feature_request(event)
            elif method == 'DELETE':
                return handle_unvote_feature_request(event)
        
        # Update feature request status (admin only)
        if path.startswith('/v1/feature-requests/') and '/status' in path:
            request_id = path.split('/')[3]
            event['pathParameters'] = {'request_id': request_id}
            
            if method == 'PUT':
                return handle_update_feature_request_status(event)
        
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
    from dotenv import load_dotenv
    
    # Force load .env.local for local execution
    # override=False ensures Docker environment variables (like AWS_ENDPOINT_URL) are preserved
    load_dotenv('.env.local', override=False)
    load_dotenv() # Load .env if exists
    
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
            "allow_headers": ["Content-Type", "Authorization", "Cookie", "X-Guest-Name", "X-Guest-Email"],
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
