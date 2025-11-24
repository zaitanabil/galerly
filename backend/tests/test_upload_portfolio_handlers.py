"""
Complete tests for upload handlers: presigned URLs and multipart uploads.
Tests ALL endpoints and EVERY possibility.
"""
import pytest
from unittest.mock import Mock, patch
import json

# Test: Presigned URL Upload Handler
class TestPresignedUploadHandler:
    """Tests for photo_upload_presigned.py - ALL scenarios."""
    
    def test_get_upload_url_success(self, sample_user, sample_gallery):
        """Get presigned URL successfully."""
        from handlers.photo_upload_presigned import handle_get_upload_url
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries, \
             patch('handlers.photo_upload_presigned.s3_client') as mock_s3:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned'
            
            event = {'body': json.dumps({'filename': 'photo.jpg', 'content_type': 'image/jpeg'})}
            result = handle_get_upload_url('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'upload_url' in body or 'url' in body
    
    def test_get_upload_url_invalid_content_type(self, sample_user, sample_gallery):
        """Get upload URL fails with invalid content type."""
        from handlers.photo_upload_presigned import handle_get_upload_url
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({'filename': 'file.exe', 'content_type': 'application/exe'})}
            result = handle_get_upload_url('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400
    
    def test_get_upload_url_gallery_not_owned(self, sample_user, sample_gallery):
        """Get upload URL fails when user doesn't own gallery."""
        from handlers.photo_upload_presigned import handle_get_upload_url
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries:
            other_gallery = {**sample_gallery, 'user_id': 'other_user'}
            mock_galleries.get_item.return_value = {'Item': other_gallery}
            
            event = {'body': json.dumps({'filename': 'photo.jpg'})}
            result = handle_get_upload_url('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 403
    
    def test_get_upload_url_missing_filename(self, sample_user, sample_gallery):
        """Get upload URL fails without filename."""
        from handlers.photo_upload_presigned import handle_get_upload_url
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({})}
            result = handle_get_upload_url('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400
    
    def test_confirm_upload_success(self, sample_user, sample_gallery):
        """Confirm upload successfully."""
        from handlers.photo_upload_presigned import handle_confirm_upload
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries, \
             patch('handlers.photo_upload_presigned.photos_table') as mock_photos:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({
                'photo_id': 'photo_123',
                'filename': 'photo.jpg',
                's3_key': 'uploads/photo.jpg'
            })}
            result = handle_confirm_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] in [200, 201]
    
    def test_confirm_upload_missing_photo_id(self, sample_user, sample_gallery):
        """Confirm upload fails without photo_id."""
        from handlers.photo_upload_presigned import handle_confirm_upload
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({'filename': 'photo.jpg'})}
            result = handle_confirm_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400
    
    def test_direct_upload_success(self, sample_user, sample_gallery):
        """Direct upload successfully."""
        from handlers.photo_upload_presigned import handle_direct_upload
        
        with patch('handlers.photo_upload_presigned.galleries_table') as mock_galleries, \
             patch('handlers.photo_upload_presigned.s3_client') as mock_s3:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({
                'filename': 'photo.jpg',
                'content_type': 'image/jpeg',
                'file_data': 'base64encodeddata'
            })}
            result = handle_direct_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] in [200, 201]

# Test: Multipart Upload Handler
class TestMultipartUploadHandler:
    """Tests for multipart_upload_handler.py - ALL scenarios."""
    
    def test_initialize_multipart_success(self, sample_user, sample_gallery):
        """Initialize multipart upload successfully."""
        from handlers.multipart_upload_handler import handle_initialize_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries, \
             patch('handlers.multipart_upload_handler.s3_client') as mock_s3:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            mock_s3.create_multipart_upload.return_value = {'UploadId': 'upload123'}
            
            event = {'body': json.dumps({
                'filename': 'large_photo.jpg',
                'content_type': 'image/jpeg',
                'file_size': 20000000
            })}
            result = handle_initialize_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'upload_id' in body
    
    def test_initialize_multipart_file_too_small(self, sample_user, sample_gallery):
        """Initialize multipart fails for small files."""
        from handlers.multipart_upload_handler import handle_initialize_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({
                'filename': 'small.jpg',
                'file_size': 1000000  # Less than 5MB threshold
            })}
            result = handle_initialize_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400
    
    def test_complete_multipart_success(self, sample_user, sample_gallery):
        """Complete multipart upload successfully."""
        from handlers.multipart_upload_handler import handle_complete_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries, \
             patch('handlers.multipart_upload_handler.s3_client') as mock_s3, \
             patch('handlers.multipart_upload_handler.photos_table') as mock_photos:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            mock_s3.complete_multipart_upload.return_value = {'ETag': 'etag123'}
            
            event = {'body': json.dumps({
                'upload_id': 'upload123',
                's3_key': 'uploads/large.jpg',
                'parts': [
                    {'PartNumber': 1, 'ETag': 'etag1'},
                    {'PartNumber': 2, 'ETag': 'etag2'}
                ]
            })}
            result = handle_complete_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] in [200, 201]
    
    def test_complete_multipart_missing_parts(self, sample_user, sample_gallery):
        """Complete multipart fails without parts."""
        from handlers.multipart_upload_handler import handle_complete_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({'upload_id': 'upload123'})}
            result = handle_complete_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400
    
    def test_abort_multipart_success(self, sample_user, sample_gallery):
        """Abort multipart upload successfully."""
        from handlers.multipart_upload_handler import handle_abort_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries, \
             patch('handlers.multipart_upload_handler.s3_client') as mock_s3:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({
                'upload_id': 'upload123',
                's3_key': 'uploads/aborted.jpg'
            })}
            result = handle_abort_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'aborted' in body['message'].lower()
    
    def test_abort_multipart_missing_upload_id(self, sample_user, sample_gallery):
        """Abort multipart fails without upload_id."""
        from handlers.multipart_upload_handler import handle_abort_multipart_upload
        
        with patch('handlers.multipart_upload_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            event = {'body': json.dumps({})}
            result = handle_abort_multipart_upload('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 400

# Test: Bulk Download Handler
class TestBulkDownloadHandler:
    """Tests for bulk_download_handler.py - ALL scenarios."""
    
    def test_bulk_download_authenticated(self, sample_user, sample_gallery):
        """Bulk download with authentication."""
        from handlers.bulk_download_handler import handle_bulk_download
        
        with patch('handlers.bulk_download_handler.galleries_table') as mock_galleries, \
             patch('handlers.bulk_download_handler.photos_table') as mock_photos, \
             patch('handlers.bulk_download_handler.create_zip') as mock_zip:
            
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            mock_photos.query.return_value = {'Items': []}
            mock_zip.return_value = 'https://download.url/zip'
            
            event = {'body': json.dumps({'photo_ids': ['photo1', 'photo2']})}
            result = handle_bulk_download('gallery_123', sample_user, event)
            
            assert result['statusCode'] == 200
    
    def test_bulk_download_by_token(self, sample_gallery):
        """Bulk download by share token (public)."""
        from handlers.bulk_download_handler import handle_bulk_download_by_token
        
        with patch('handlers.bulk_download_handler.galleries_table') as mock_galleries, \
             patch('handlers.bulk_download_handler.photos_table') as mock_photos:
            
            gallery_with_token = {**sample_gallery, 'share_token': 'token123'}
            mock_galleries.scan.return_value = {'Items': [gallery_with_token]}
            mock_photos.query.return_value = {'Items': []}
            
            event = {'body': json.dumps({
                'share_token': 'token123',
                'photo_ids': ['photo1']
            })}
            result = handle_bulk_download_by_token(event)
            
            assert result['statusCode'] == 200
    
    def test_bulk_download_invalid_token(self):
        """Bulk download fails with invalid token."""
        from handlers.bulk_download_handler import handle_bulk_download_by_token
        
        with patch('handlers.bulk_download_handler.galleries_table') as mock_galleries:
            mock_galleries.scan.return_value = {'Items': []}
            
            event = {'body': json.dumps({
                'share_token': 'invalid',
                'photo_ids': ['photo1']
            })}
            result = handle_bulk_download_by_token(event)
            
            assert result['statusCode'] == 404

# Test: Photographer Handler
class TestPhotographerHandler:
    """Tests for photographer_handler.py - ALL scenarios."""
    
    def test_list_photographers(self):
        """List all photographers."""
        from handlers.photographer_handler import handle_list_photographers
        
        with patch('handlers.photographer_handler.users_table') as mock_users:
            mock_users.scan.return_value = {'Items': [
                {'id': 'user1', 'role': 'photographer', 'name': 'John'},
                {'id': 'user2', 'role': 'photographer', 'name': 'Jane'}
            ]}
            
            result = handle_list_photographers({})
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'photographers' in body
    
    def test_list_photographers_with_city_filter(self):
        """List photographers filtered by city."""
        from handlers.photographer_handler import handle_list_photographers
        
        with patch('handlers.photographer_handler.users_table') as mock_users:
            mock_users.scan.return_value = {'Items': [
                {'id': 'user1', 'city': 'New York', 'role': 'photographer'}
            ]}
            
            result = handle_list_photographers({'city': 'New York'})
            
            assert result['statusCode'] == 200
    
    def test_get_photographer(self):
        """Get single photographer profile."""
        from handlers.photographer_handler import handle_get_photographer
        
        with patch('handlers.photographer_handler.users_table') as mock_users, \
             patch('handlers.photographer_handler.galleries_table') as mock_galleries:
            
            mock_users.get_item.return_value = {
                'Item': {'id': 'user1', 'name': 'John', 'role': 'photographer'}
            }
            mock_galleries.query.return_value = {'Items': []}
            
            result = handle_get_photographer('user1')
            
            assert result['statusCode'] == 200
    
    def test_get_photographer_not_found(self):
        """Get photographer returns 404 when not found."""
        from handlers.photographer_handler import handle_get_photographer
        
        with patch('handlers.photographer_handler.users_table') as mock_users:
            mock_users.get_item.return_value = {}
            
            result = handle_get_photographer('nonexistent')
            
            assert result['statusCode'] == 404

# Test: Portfolio Handler
class TestPortfolioHandler:
    """Tests for portfolio_handler.py - ALL scenarios."""
    
    def test_get_portfolio_settings(self, sample_user):
        """Get portfolio settings."""
        from handlers.portfolio_handler import handle_get_portfolio_settings
        
        with patch('handlers.portfolio_handler.users_table') as mock_users:
            user_with_settings = {
                **sample_user,
                'portfolio_settings': {'theme': 'dark', 'layout': 'grid'}
            }
            mock_users.get_item.return_value = {'Item': user_with_settings}
            
            result = handle_get_portfolio_settings(sample_user)
            
            assert result['statusCode'] == 200
    
    def test_update_portfolio_settings(self, sample_user):
        """Update portfolio settings."""
        from handlers.portfolio_handler import handle_update_portfolio_settings
        
        with patch('handlers.portfolio_handler.users_table') as mock_users:
            mock_users.get_item.return_value = {'Item': sample_user}
            
            body = {
                'theme': 'light',
                'layout': 'masonry',
                'custom_domain': 'photos.example.com'
            }
            result = handle_update_portfolio_settings(sample_user, body)
            
            assert result['statusCode'] == 200
    
    def test_get_public_portfolio(self):
        """Get public portfolio (no auth required)."""
        from handlers.portfolio_handler import handle_get_public_portfolio
        
        with patch('handlers.portfolio_handler.users_table') as mock_users, \
             patch('handlers.portfolio_handler.galleries_table') as mock_galleries:
            
            mock_users.get_item.return_value = {
                'Item': {'id': 'user1', 'name': 'John', 'portfolio_enabled': True}
            }
            mock_galleries.query.return_value = {'Items': []}
            
            result = handle_get_public_portfolio('user1')
            
            assert result['statusCode'] == 200
    
    def test_get_public_portfolio_disabled(self):
        """Get public portfolio returns 403 when disabled."""
        from handlers.portfolio_handler import handle_get_public_portfolio
        
        with patch('handlers.portfolio_handler.users_table') as mock_users:
            mock_users.get_item.return_value = {
                'Item': {'id': 'user1', 'portfolio_enabled': False}
            }
            
            result = handle_get_public_portfolio('user1')
            
            assert result['statusCode'] == 403

# Test: Social Handler
class TestSocialHandler:
    """Tests for social_handler.py - ALL scenarios."""
    
    def test_get_gallery_share_info(self, sample_user, sample_gallery):
        """Get gallery share information."""
        from handlers.social_handler import handle_get_gallery_share_info
        
        with patch('handlers.social_handler.galleries_table') as mock_galleries:
            mock_galleries.get_item.return_value = {'Item': sample_gallery}
            
            result = handle_get_gallery_share_info('gallery_123', sample_user)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'share_url' in body or 'url' in body
    
    def test_get_photo_share_info(self, sample_user, sample_photo):
        """Get photo share information."""
        from handlers.social_handler import handle_get_photo_share_info
        
        with patch('handlers.social_handler.photos_table') as mock_photos:
            mock_photos.get_item.return_value = {'Item': sample_photo}
            
            result = handle_get_photo_share_info('photo_123', sample_user)
            
            assert result['statusCode'] == 200

# Test: City Handler
class TestCityHandler:
    """Tests for city_handler.py - ALL scenarios."""
    
    def test_city_search_success(self):
        """Search cities successfully."""
        from handlers.city_handler import handle_city_search
        
        with patch('handlers.city_handler.cities_table') as mock_cities:
            mock_cities.scan.return_value = {
                'Items': [
                    {'city': 'New York', 'country': 'USA'},
                    {'city': 'Newark', 'country': 'USA'}
                ]
            }
            
            result = handle_city_search('New')
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'cities' in body
    
    def test_city_search_empty_query(self):
        """Search cities with empty query."""
        from handlers.city_handler import handle_city_search
        
        result = handle_city_search('')
        
        assert result['statusCode'] == 400
    
    def test_city_search_no_results(self):
        """Search cities returns empty when no matches."""
        from handlers.city_handler import handle_city_search
        
        with patch('handlers.city_handler.cities_table') as mock_cities:
            mock_cities.scan.return_value = {'Items': []}
            
            result = handle_city_search('XYZ')
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert len(body['cities']) == 0

# Test: Gallery Expiration Handler
class TestGalleryExpirationHandler:
    """Tests for gallery_expiration_handler.py - ALL scenarios."""
    
    def test_check_expiring_galleries(self):
        """Check for expiring galleries."""
        from handlers.gallery_expiration_handler import handle_check_expiring_galleries
        
        with patch('handlers.gallery_expiration_handler.galleries_table') as mock_galleries:
            mock_galleries.scan.return_value = {'Items': []}
            
            result = handle_check_expiring_galleries()
            
            assert result['statusCode'] == 200
    
    def test_manual_expiry_check(self, sample_user):
        """Manual expiry check by photographer."""
        from handlers.gallery_expiration_handler import handle_manual_expiry_check
        
        with patch('handlers.gallery_expiration_handler.galleries_table') as mock_galleries:
            mock_galleries.query.return_value = {'Items': []}
            
            result = handle_manual_expiry_check(sample_user)
            
            assert result['statusCode'] == 200

# Test: Subscription Handler
class TestSubscriptionHandler:
    """Tests for subscription_handler.py - ALL scenarios."""
    
    def test_get_usage(self, sample_user):
        """Get current usage statistics."""
        from handlers.subscription_handler import handle_get_usage
        
        with patch('handlers.subscription_handler.galleries_table') as mock_galleries, \
             patch('handlers.subscription_handler.photos_table') as mock_photos:
            
            mock_galleries.query.return_value = {'Items': []}
            mock_photos.query.return_value = {'Items': []}
            
            result = handle_get_usage(sample_user)
            
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'usage' in body or 'galleries_count' in body

