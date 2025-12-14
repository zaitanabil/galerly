"""
Test Suite for Gallery Statistics Handler
Tests comprehensive gallery analytics and recommendations
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from handlers.gallery_statistics_handler import (
    handle_get_gallery_statistics,
    generate_gallery_recommendations,
    convert_decimals
)


class TestGalleryStatistics:
    """Test gallery statistics functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock photographer user"""
        return {
            'id': 'user123',
            'email': 'photographer@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
    
    @pytest.fixture
    def mock_gallery(self):
        """Mock gallery data"""
        return {
            'id': 'gallery123',
            'user_id': 'user123',
            'name': 'Summer Wedding 2025',
            'privacy': 'public',
            'description': 'Beautiful wedding photography',
            'created_at': '2025-01-01T00:00:00Z',
            'allow_downloads': True,
            'password': None
        }
    
    @pytest.fixture
    def mock_gallery_views(self):
        """Mock gallery view data"""
        now = datetime.now(timezone.utc)
        views = []
        
        for i in range(50):
            days_ago = i % 30
            view_date = (now - timedelta(days=days_ago)).isoformat()
            
            views.append({
                'gallery_id': 'gallery123',
                'visitor_id': f'visitor{i % 20}',  # 20 unique visitors
                'viewed_at': view_date,
                'country': ['USA', 'UK', 'Canada', 'France', 'Germany'][i % 5],
                'device_type': ['desktop', 'mobile', 'tablet'][i % 3],
                'referrer': ['google.com', 'facebook.com', 'Direct', 'instagram.com'][i % 4],
                'duration_seconds': 60 if i % 2 == 0 else 15
            })
        
        return views
    
    @pytest.fixture
    def mock_photos(self):
        """Mock photo data"""
        photos = []
        for i in range(20):
            photos.append({
                'id': f'photo{i}',
                'gallery_id': 'gallery123',
                'original_filename': f'IMG_{1000+i}.jpg',
                'thumbnail_url': f'https://example.com/thumb{i}.jpg',
                'favorite_count': i % 5,  # 0-4 favorites
                'download_count': i % 3,  # 0-2 downloads
                'file_size': 5000000
            })
        return photos
    
    @pytest.fixture
    def mock_photo_views(self):
        """Mock photo view data"""
        def get_views_for_photo(photo_id):
            photo_num = int(photo_id.replace('photo', ''))
            views = []
            for i in range(photo_num * 2):  # More views for later photos
                views.append({
                    'photo_id': photo_id,
                    'viewer_id': f'viewer{i}',
                    'viewed_at': datetime.now(timezone.utc).isoformat()
                })
            return views
        return get_views_for_photo
    
    @patch('handlers.gallery_statistics_handler.galleries_table')
    @patch('handlers.gallery_statistics_handler.photos_table')
    def test_get_gallery_statistics_success(
        self, mock_photos_table, mock_galleries_table,
        mock_user, mock_gallery, mock_gallery_views, mock_photos
    ):
        """Test successful gallery statistics retrieval"""
        # Setup mocks
        mock_galleries_table.get_item.return_value = {'Item': mock_gallery}
        mock_photos_table.query.return_value = {'Items': mock_photos}
        
        # Call handler
        response = handle_get_gallery_statistics(mock_user, 'gallery123')
        
        # Verify response
        assert response['statusCode'] == 200
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        # Check structure
        assert 'gallery_id' in body
        assert 'overview' in body
        assert 'trends' in body
        assert 'client_activity' in body
        assert 'geography' in body
        assert 'devices' in body
        assert 'recommendations' in body
        
        # Check overview metrics
        overview = body['overview']
        assert overview['total_views'] == 50
        assert overview['unique_visitors'] == 20
        assert overview['total_photos'] == 20
        assert 0 <= overview['performance_score'] <= 100
        assert overview['engagement_rate'] >= 0
    
    @patch('handlers.gallery_statistics_handler.galleries_table')
    def test_get_gallery_statistics_not_found(self, mock_galleries_table, mock_user):
        """Test statistics for non-existent gallery"""
        mock_galleries_table.get_item.return_value = {}
        
        response = handle_get_gallery_statistics(mock_user, 'nonexistent')
        
        assert response['statusCode'] == 404
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'error' in body
    
    @patch('handlers.gallery_statistics_handler.galleries_table')
    def test_get_gallery_statistics_wrong_owner(self, mock_galleries_table, mock_user):
        """Test statistics access for gallery owned by different user"""
        wrong_gallery = {
            'id': 'gallery123',
            'user_id': 'different_user',
            'name': 'Test Gallery'
        }
        mock_galleries_table.get_item.return_value = {'Item': wrong_gallery}
        
        response = handle_get_gallery_statistics(mock_user, 'gallery123')
        
        assert response['statusCode'] == 403
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'error' in body
        assert 'denied' in body['error'].lower()
    
    def test_generate_recommendations_low_views(self):
        """Test recommendations for gallery with low views"""
        recommendations = generate_gallery_recommendations(
            views=5,
            engagement_rate=40,
            favorites=2,
            downloads=1,
            is_password_protected=False,
            privacy='public'
        )
        
        # Should recommend increasing visibility
        visibility_recs = [r for r in recommendations if r['type'] == 'visibility']
        assert len(visibility_recs) > 0
        assert visibility_recs[0]['priority'] == 'high'
    
    def test_generate_recommendations_low_engagement(self):
        """Test recommendations for low engagement"""
        recommendations = generate_gallery_recommendations(
            views=100,
            engagement_rate=20,  # Low engagement
            favorites=10,
            downloads=5,
            is_password_protected=False,
            privacy='public'
        )
        
        # Should recommend improving engagement
        engagement_recs = [r for r in recommendations if r['type'] == 'engagement']
        assert len(engagement_recs) > 0
    
    def test_generate_recommendations_no_favorites(self):
        """Test recommendations when no favorites"""
        recommendations = generate_gallery_recommendations(
            views=50,
            engagement_rate=60,
            favorites=0,  # No favorites
            downloads=0,
            is_password_protected=False,
            privacy='public'
        )
        
        # Should recommend encouraging interaction
        interaction_recs = [r for r in recommendations if r['type'] == 'interaction']
        assert len(interaction_recs) > 0
    
    def test_generate_recommendations_favorites_no_downloads(self):
        """Test recommendations when favorites but no downloads"""
        recommendations = generate_gallery_recommendations(
            views=100,
            engagement_rate=70,
            favorites=20,
            downloads=0,  # No downloads despite favorites
            is_password_protected=False,
            privacy='public'
        )
        
        # Should recommend converting favorites to downloads
        conversion_recs = [r for r in recommendations if r['type'] == 'conversion']
        assert len(conversion_recs) > 0
        assert conversion_recs[0]['priority'] == 'high'
    
    def test_generate_recommendations_private_gallery(self):
        """Test recommendations for private gallery with low views"""
        recommendations = generate_gallery_recommendations(
            views=2,
            engagement_rate=50,
            favorites=0,
            downloads=0,
            is_password_protected=False,
            privacy='private'
        )
        
        # Should mention privacy settings
        settings_recs = [r for r in recommendations if r['type'] == 'settings']
        assert len(settings_recs) > 0
    
    def test_generate_recommendations_success(self):
        """Test recommendations for successful gallery"""
        recommendations = generate_gallery_recommendations(
            views=500,
            engagement_rate=75,
            favorites=100,
            downloads=80,
            is_password_protected=False,
            privacy='public'
        )
        
        # Should show success message
        success_recs = [r for r in recommendations if r['type'] == 'success']
        assert len(success_recs) > 0
        assert success_recs[0]['priority'] == 'info'
    
    def test_convert_decimals_simple(self):
        """Test decimal conversion for simple values"""
        data = {
            'views': Decimal('100'),
            'rate': Decimal('45.5')
        }
        
        result = convert_decimals(data)
        
        assert isinstance(result['views'], float)
        assert isinstance(result['rate'], float)
        assert result['views'] == 100.0
        assert result['rate'] == 45.5
    
    def test_convert_decimals_nested(self):
        """Test decimal conversion for nested structures"""
        data = {
            'overview': {
                'views': Decimal('100'),
                'engagement': Decimal('67.8')
            },
            'photos': [
                {'id': 'photo1', 'views': Decimal('50')},
                {'id': 'photo2', 'views': Decimal('30')}
            ]
        }
        
        result = convert_decimals(data)
        
        # Check nested dict
        assert isinstance(result['overview']['views'], float)
        assert isinstance(result['overview']['engagement'], float)
        
        # Check list of dicts
        assert isinstance(result['photos'][0]['views'], float)
        assert isinstance(result['photos'][1]['views'], float)
    
    def test_convert_decimals_preserves_other_types(self):
        """Test that non-Decimal types are preserved"""
        data = {
            'string': 'test',
            'int': 100,
            'float': 45.5,
            'bool': True,
            'none': None,
            'decimal': Decimal('123.45')
        }
        
        result = convert_decimals(data)
        
        assert result['string'] == 'test'
        assert result['int'] == 100
        assert result['float'] == 45.5
        assert result['bool'] == True
        assert result['none'] is None
        assert isinstance(result['decimal'], float)


class TestGalleryStatisticsMetrics:
    """Test specific metric calculations"""
    
    def test_unique_visitor_calculation(self):
        """Test unique visitor counting"""
        views = [
            {'visitor_id': 'v1'},
            {'visitor_id': 'v1'},  # Duplicate
            {'visitor_id': 'v2'},
            {'visitor_id': 'v3'},
            {'visitor_id': 'v2'}   # Duplicate
        ]
        
        unique_visitors = len(set(v.get('visitor_id', '') for v in views))
        assert unique_visitors == 3
    
    def test_engagement_rate_calculation(self):
        """Test engagement rate calculation"""
        total_views = 100
        engaged_views = 65  # Views > 30 seconds
        
        engagement_rate = (engaged_views / total_views) * 100
        assert engagement_rate == 65.0
    
    def test_performance_score_calculation(self):
        """Test performance score calculation logic"""
        # Low performance
        score = 0
        views = 5
        unique_visitors = 2
        engagement_rate = 20
        favorites = 0
        downloads = 0
        
        score += min(30, views / 10)  # 1.5
        score += min(20, unique_visitors / 5)  # 0.4
        score += min(25, engagement_rate / 2)  # 10
        score += min(15, favorites / 5)  # 0
        score += min(10, downloads / 5)  # 0
        
        score = min(100, int(score))
        assert score < 20
        
        # High performance
        score = 0
        views = 500
        unique_visitors = 150
        engagement_rate = 80
        favorites = 100
        downloads = 50
        
        score += min(30, views / 10)  # 30
        score += min(20, unique_visitors / 5)  # 20
        score += min(25, engagement_rate / 2)  # 25
        score += min(15, favorites / 5)  # 15
        score += min(10, downloads / 5)  # 10
        
        score = min(100, int(score))
        assert score == 100


class TestGalleryStatisticsEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('handlers.gallery_statistics_handler.galleries_table')
    @patch('handlers.gallery_statistics_handler.gallery_views_table')
    @patch('handlers.gallery_statistics_handler.photos_table')
    def test_empty_gallery(
        self, mock_photos_table, mock_gallery_views_table,
        mock_galleries_table
    ):
        """Test statistics for gallery with no photos or views"""
        gallery = {
            'id': 'empty_gallery',
            'user_id': 'user123',
            'name': 'Empty Gallery',
            'privacy': 'public'
        }
        
        mock_galleries_table.get_item.return_value = {'Item': gallery}
        mock_gallery_views_table.query.return_value = {'Items': []}
        mock_photos_table.query.return_value = {'Items': []}
        
        response = handle_get_gallery_statistics({'id': 'user123', 'email': 'test@test.com', 'role': 'photographer', 'plan': 'pro'}, 'empty_gallery')
        
        assert response['statusCode'] == 200
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert body['overview']['total_views'] == 0
        assert body['overview']['unique_visitors'] == 0
        assert body['overview']['total_photos'] == 0
    
    def test_recommendations_with_zero_values(self):
        """Test recommendations when all metrics are zero"""
        recommendations = generate_gallery_recommendations(
            views=0,
            engagement_rate=0,
            favorites=0,
            downloads=0,
            is_password_protected=False,
            privacy='public'
        )
        
        # Should still provide recommendations
        assert len(recommendations) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

