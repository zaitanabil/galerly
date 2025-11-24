"""
Integration tests for complete user workflows.
Tests end-to-end scenarios across multiple handlers.
"""
import pytest
from unittest.mock import Mock, patch
import json

pytestmark = pytest.mark.integration

class TestUserRegistrationFlow:
    """Test complete user registration workflow."""
    
    def test_complete_registration_flow(self):
        """Complete flow: request code -> verify -> register -> login."""
        with patch('handlers.auth_handler.users_table') as mock_users, \
             patch('handlers.auth_handler.verification_codes_table') as mock_codes, \
             patch('handlers.auth_handler.sessions_table') as mock_sessions, \
             patch('handlers.auth_handler.send_email') as mock_email:
            
            # Step 1: Request verification code
            from handlers.auth_handler import handle_request_verification_code
            result = handle_request_verification_code({'email': 'newuser@example.com'})
            assert result['statusCode'] == 200
            assert mock_email.called
            
            # Step 2: Verify code
            from handlers.auth_handler import handle_verify_code
            with patch('handlers.auth_handler.validate_verification_code', return_value=True):
                result = handle_verify_code({'email': 'newuser@example.com', 'code': '123456'})
                assert result['statusCode'] == 200
            
            # Step 3: Register
            from handlers.auth_handler import handle_register
            mock_users.query.return_value = {'Items': []}
            with patch('handlers.auth_handler.validate_verification_code', return_value=True):
                result = handle_register({
                    'email': 'newuser@example.com',
                    'password': 'SecurePass123!',
                    'name': 'New User',
                    'verification_code': '123456'
                })
                assert result['statusCode'] == 201
                body = json.loads(result['body'])
                token = body['token']
            
            # Step 4: Access protected endpoint with token
            from handlers.auth_handler import handle_get_me
            mock_user = {'id': 'user123', 'email': 'newuser@example.com'}
            result = handle_get_me(mock_user)
            assert result['statusCode'] == 200

class TestGalleryPhotoWorkflow:
    """Test complete gallery and photo management workflow."""
    
    def test_gallery_creation_and_photo_upload(self, sample_user):
        """Complete flow: create gallery -> upload photos -> update -> delete."""
        with patch('handlers.gallery_handler.galleries_table') as mock_galleries, \
             patch('handlers.gallery_handler.photos_table') as mock_photos, \
             patch('handlers.photo_handler.s3_client') as mock_s3:
            
            # Step 1: Create gallery
            from handlers.gallery_handler import handle_create_gallery
            with patch('handlers.gallery_handler.enforce_gallery_limit', return_value=True):
                result = handle_create_gallery(sample_user, {
                    'name': 'Wedding Photos',
                    'client_emails': ['client@example.com']
                })
                assert result['statusCode'] == 201
                gallery = json.loads(result['body'])
                gallery_id = gallery['id']
            
            # Step 2: Upload photo
            from handlers.photo_handler import handle_upload_photo
            mock_galleries.get_item.return_value = {'Item': gallery}
            event = {'body': json.dumps({'filename': 'photo.jpg'})}
            result = handle_upload_photo(gallery_id, sample_user, event)
            assert result['statusCode'] in [200, 201]
            
            # Step 3: Update photo
            from handlers.photo_handler import handle_update_photo
            photo = {'id': 'photo123', 'gallery_id': gallery_id, 'user_id': sample_user['id']}
            mock_photos.get_item.return_value = {'Item': photo}
            mock_galleries.get_item.return_value = {'Item': gallery}
            result = handle_update_photo('photo123', {'status': 'approved'}, sample_user)
            assert result['statusCode'] == 200
            
            # Step 4: Delete gallery (cascades to photos)
            from handlers.gallery_handler import handle_delete_gallery
            mock_galleries.get_item.return_value = {'Item': gallery}
            mock_photos.query.return_value = {'Items': [photo]}
            result = handle_delete_gallery(gallery_id, sample_user)
            assert result['statusCode'] == 200

class TestSubscriptionBillingWorkflow:
    """Test complete subscription and billing workflow."""
    
    def test_subscription_lifecycle(self, sample_user):
        """Complete flow: subscribe -> use -> cancel -> reactivate."""
        with patch('handlers.billing_handler.subscriptions_table') as mock_subs, \
             patch('handlers.billing_handler.users_table') as mock_users, \
             patch('handlers.billing_handler.stripe') as mock_stripe:
            
            # Step 1: Create checkout session
            from handlers.billing_handler import handle_create_checkout_session
            mock_stripe.checkout.Session.create.return_value = Mock(
                url='https://checkout.stripe.com/test'
            )
            result = handle_create_checkout_session(sample_user, {'plan': 'pro'})
            assert result['statusCode'] == 200
            
            # Step 2: Get subscription (after payment)
            from handlers.billing_handler import handle_get_subscription
            subscription = {
                'user_id': sample_user['id'],
                'plan': 'pro',
                'status': 'active',
                'cancel_at_period_end': False
            }
            mock_subs.query.return_value = {'Items': [subscription]}
            result = handle_get_subscription(sample_user)
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['plan'] == 'pro'
            
            # Step 3: Cancel subscription
            from handlers.billing_handler import handle_cancel_subscription
            mock_subs.get_item.return_value = {'Item': subscription}
            result = handle_cancel_subscription(sample_user)
            assert result['statusCode'] == 200
            
            # Step 4: Reactivate subscription
            from handlers.billing_handler import handle_change_plan
            canceled_sub = {**subscription, 'cancel_at_period_end': True, 'pending_plan': 'free'}
            mock_subs.query.return_value = {'Items': [canceled_sub]}
            mock_subs.get_item.return_value = {'Item': canceled_sub}
            with patch('handlers.billing_handler.PRICE_IDS', {'pro': 'price_pro'}):
                mock_stripe.Subscription.retrieve.return_value = Mock(
                    items=Mock(data=[Mock(price=Mock(id='price_pro'))])
                )
                result = handle_change_plan(sample_user, {'new_plan': 'pro'})
                assert result['statusCode'] == 200

class TestClientGalleryAccessWorkflow:
    """Test client accessing and interacting with gallery."""
    
    def test_client_gallery_interaction(self, sample_user, sample_gallery, sample_photo):
        """Complete flow: client views gallery -> favorites photo -> submits feedback."""
        with patch('handlers.client_handler.galleries_table') as mock_galleries, \
             patch('handlers.client_handler.photos_table') as mock_photos, \
             patch('handlers.client_handler.users_table') as mock_users:
            
            client = {'id': 'client123', 'email': 'client@example.com', 'role': 'client'}
            gallery_with_access = {**sample_gallery, 'client_emails': [client['email']]}
            
            # Step 1: Access gallery
            from handlers.client_handler import handle_get_client_gallery
            mock_galleries.scan.return_value = {'Items': [gallery_with_access]}
            mock_users.query.return_value = {'Items': [sample_user]}
            mock_photos.query.return_value = {'Items': [sample_photo], 'LastEvaluatedKey': None}
            
            result = handle_get_client_gallery(gallery_with_access['id'], client, None)
            assert result['statusCode'] == 200
            
            # Step 2: Add photo to favorites
            from handlers.client_favorites_handler import handle_add_favorite
            with patch('handlers.client_favorites_handler.favorites_table') as mock_favorites:
                result = handle_add_favorite(client, {
                    'photo_id': sample_photo['id'],
                    'gallery_id': gallery_with_access['id']
                })
                assert result['statusCode'] in [200, 201]
            
            # Step 3: Submit feedback
            from handlers.client_feedback_handler import handle_submit_client_feedback
            with patch('handlers.client_feedback_handler.feedback_table') as mock_feedback:
                result = handle_submit_client_feedback(gallery_with_access['id'], {
                    'rating': 5,
                    'comment': 'Amazing photos!',
                    'client_email': client['email']
                })
                assert result['statusCode'] in [200, 201]

class TestAnalyticsTrackingWorkflow:
    """Test analytics tracking across user journey."""
    
    def test_analytics_tracking_flow(self, sample_gallery):
        """Track gallery view -> photo view -> photo download."""
        with patch('handlers.analytics_handler.analytics_table') as mock_analytics, \
             patch('handlers.analytics_handler.galleries_table') as mock_galleries:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            # Step 1: Track gallery view
            from handlers.analytics_handler import handle_track_gallery_view
            result = handle_track_gallery_view(sample_gallery['id'], None, {})
            assert result['statusCode'] == 200
            
            # Step 2: Track photo view
            from handlers.analytics_handler import handle_track_photo_view
            result = handle_track_photo_view('photo123', sample_gallery['id'], None, {})
            assert result['statusCode'] == 200
            
            # Step 3: Track photo download
            from handlers.analytics_handler import handle_track_photo_download
            result = handle_track_photo_download('photo123', sample_gallery['id'], None, {})
            assert result['statusCode'] == 200
            
            # Step 4: Get analytics
            from handlers.analytics_handler import handle_get_gallery_analytics
            user = {'id': sample_gallery['user_id']}
            mock_analytics.query.return_value = {'Items': []}
            result = handle_get_gallery_analytics(user, sample_gallery['id'])
            assert result['statusCode'] == 200

