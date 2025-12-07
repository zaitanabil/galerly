"""
Tests for photographer_handler.py  
Tests photographer directory and public profile features
FIX: Use conftest.global_mock_table - requires public galleries
"""
import pytest
import json
from handlers.photographer_handler import (
    handle_list_photographers,
    handle_get_photographer
)


class TestListPhotographers:
    """Test photographer directory listing"""
    
    def test_list_photographers_returns_only_photographers(self):
        """Only users with photographer role are returned"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'name': 'John Doe'},
                {'id': 'user2', 'role': 'client', 'name': 'Jane Smith'},
                {'id': 'user3', 'role': 'photographer', 'name': 'Bob Wilson'}
            ]
        }
        # Handler requires photographers to have public galleries
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        response = handle_list_photographers()
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        photographers = body['photographers']
        assert len(photographers) == 2
    
    def test_list_photographers_filters_by_city(self):
        """Photographers can be filtered by city"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'city': 'New York'},
                {'id': 'user2', 'role': 'photographer', 'city': 'Los Angeles'},
                {'id': 'user3', 'role': 'photographer', 'city': 'New York'}
            ]
        }
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        query_params = {'city': 'New York'}
        response = handle_list_photographers(query_params)
        
        body = json.loads(response['body'])
        photographers = body['photographers']
        assert len(photographers) == 2
        assert all('New York' in p.get('city', '') for p in photographers)
    
    def test_list_photographers_filters_by_specialty(self):
        """Photographers can be filtered by specialty"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'specialties': ['wedding', 'portrait']},
                {'id': 'user2', 'role': 'photographer', 'specialties': ['landscape', 'nature']},
                {'id': 'user3', 'role': 'photographer', 'specialties': ['wedding', 'event']}
            ]
        }
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        query_params = {'specialty': 'wedding'}
        response = handle_list_photographers(query_params)
        
        body = json.loads(response['body'])
        photographers = body['photographers']
        assert len(photographers) == 2
    
    def test_list_photographers_filters_by_price_range(self):
        """Photographers can be filtered by price range"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'hourly_rate': 100},
                {'id': 'user2', 'role': 'photographer', 'hourly_rate': 200},
                {'id': 'user3', 'role': 'photographer', 'hourly_rate': 150}
            ]
        }
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        query_params = {'min_price': '80', 'max_price': '160'}
        response = handle_list_photographers(query_params)
        
        body = json.loads(response['body'])
        photographers = body['photographers']
        assert len(photographers) == 2


class TestGetPhotographerProfile:
    """Test individual photographer profile retrieval"""
    
    def test_get_photographer_profile_public_access(self):
        """Public can view photographer profiles"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [{
                'id': 'photo123',
                'role': 'photographer',
                'name': 'John Doe',
                'city': 'New York',
                'bio': 'Professional photographer'
            }]
        }
        global_mock_table.query.return_value = {'Items': []}
        
        photographer_id = 'photo123'
        response = handle_get_photographer(photographer_id)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['name'] == 'John Doe'
        assert body['city'] == 'New York'
    
    def test_get_photographer_profile_not_found(self):
        """Returns 404 for non-existent photographer"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {'Items': []}
        
        photographer_id = 'nonexistent'
        response = handle_get_photographer(photographer_id)
        
        assert response['statusCode'] == 404
    
    def test_get_photographer_profile_includes_galleries(self):
        """Profile includes photographer's public galleries"""
        from tests.conftest import global_mock_table
        
        # Mock scan to return photographer
        global_mock_table.scan.return_value = {
            'Items': [{
                'id': 'photo123',
                'role': 'photographer',
                'name': 'John Doe',
                'username': 'johndoe',
                'bio': 'Test bio'
            }]
        }
        
        # Mock query for galleries
        def mock_query(**kwargs):
            # Check if it's a gallery query or photo query
            if 'IndexName' in kwargs:
                # Photo query
                return {'Items': [{'id': 'photo1'}, {'id': 'photo2'}]}
            else:
                # Gallery query
                return {
                    'Items': [
                        {'id': 'gal1', 'privacy': 'public', 'title': 'Wedding Gallery'},
                        {'id': 'gal2', 'privacy': 'private', 'title': 'Private Gallery'},
                        {'id': 'gal3', 'privacy': 'public', 'title': 'Portrait Gallery'}
                    ]
                }
        
        global_mock_table.query.side_effect = mock_query
        
        photographer_id = 'photo123'
        response = handle_get_photographer(photographer_id)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should include public galleries with photos
        assert 'galleries' in body
        assert len(body['galleries']) == 2  # Only public galleries
        assert body['gallery_count'] == 2
        assert body['photo_count'] == 4  # 2 photos per gallery


class TestSearchPhotographers:
    """Test photographer search functionality"""
    
    def test_search_photographers_by_name(self):
        """Photographers can be searched by name"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'name': 'John Doe'},
                {'id': 'user2', 'role': 'photographer', 'name': 'Jane Smith'},
                {'id': 'user3', 'role': 'photographer', 'name': 'John Wilson'}
            ]
        }
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        # Search by name 'John'
        query_params = {'q': 'John'}
        response = handle_list_photographers(query_params)
        
        body = json.loads(response['body'])
        photographers = body['photographers']
        # Should return photographers with 'John' in name
        assert len(photographers) == 2
        assert all('john' in p.get('name', '').lower() for p in photographers)
    
    def test_list_returns_all_photographers(self):
        """List returns all photographers when no filters applied"""
        from tests.conftest import global_mock_table
        
        global_mock_table.scan.return_value = {
            'Items': [
                {'id': 'user1', 'role': 'photographer', 'name': 'John Doe'},
                {'id': 'user2', 'role': 'photographer', 'name': 'Jane Smith'}
            ]
        }
        global_mock_table.query.return_value = {
            'Items': [{'id': 'gal1', 'privacy': 'public', 'photo_count': 5}]
        }
        
        response = handle_list_photographers()
        
        body = json.loads(response['body'])
        photographers = body['photographers']
        assert len(photographers) == 2
