"""
Tests for gallery layout integration in gallery handler
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from handlers.gallery_handler import (
    handle_create_gallery,
    handle_update_gallery,
    handle_list_layouts,
    handle_get_layout
)


# In-memory storage for galleries during tests
_test_galleries = {}


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown test database"""
    global _test_galleries
    _test_galleries = {}
    yield
    _test_galleries = {}


@pytest.fixture
def mock_galleries_table_with_storage():
    """Mock galleries table that actually stores data in memory"""
    def put_item_impl(Item):
        key = (Item['user_id'], Item['id'])
        _test_galleries[key] = Item.copy()
        return {}
    
    def get_item_impl(Key):
        key = (Key['user_id'], Key['id'])
        if key in _test_galleries:
            return {'Item': _test_galleries[key].copy()}
        return {}
    
    def update_item_impl(Key, **kwargs):
        key = (Key['user_id'], Key['id'])
        if key not in _test_galleries:
            raise Exception("ConditionalCheckFailedException")
        
        # Apply updates
        item = _test_galleries[key]
        if 'AttributeUpdates' in kwargs:
            for attr, update in kwargs['AttributeUpdates'].items():
                item[attr] = update['Value']
        
        return {'Attributes': item.copy()}
    
    mock_table = MagicMock()
    mock_table.put_item.side_effect = put_item_impl
    mock_table.get_item.side_effect = get_item_impl
    mock_table.update_item.side_effect = update_item_impl
    
    return mock_table


def test_create_gallery_with_layout(sample_user, mock_galleries_table_with_storage):
    """Test creating a gallery with a specific layout"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        body = {
            'name': 'Wedding Portfolio',
            'clientName': 'John & Jane',
            'clientEmails': ['john@example.com'],
            'layout_id': 'masonry_wedding',
            'description': 'Beautiful wedding day'
        }
        
        response = handle_create_gallery(sample_user, body)
        
        assert response['statusCode'] == 201
        data = json.loads(response['body'])
        
        assert data['name'] == 'Wedding Portfolio'
        assert data['layout_id'] == 'masonry_wedding'
        assert 'layout_config' in data


def test_create_gallery_default_layout(sample_user, mock_galleries_table_with_storage):
    """Test creating a gallery without specifying layout uses default"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        body = {
            'name': 'My Gallery',
            'clientName': 'Test Client',
            'clientEmails': ['test@example.com']
        }
        
        response = handle_create_gallery(sample_user, body)
        
        assert response['statusCode'] == 201
        data = json.loads(response['body'])
        
        # Should default to grid_classic
        assert data['layout_id'] == 'grid_classic'


def test_create_gallery_with_invalid_layout(sample_user, mock_galleries_table_with_storage):
    """Test creating a gallery with invalid layout ID"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        body = {
            'name': 'My Gallery',
            'clientName': 'Test Client',
            'clientEmails': ['test@example.com'],
            'layout_id': 'invalid_layout'
        }
        
        # Layout validation happens on update, not create
        # Create should accept any string
        response = handle_create_gallery(sample_user, body)
        
        assert response['statusCode'] == 201


def test_update_gallery_layout(sample_user, mock_galleries_table_with_storage):
    """Test updating a gallery's layout"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        # First create a gallery
        create_body = {
            'name': 'Test Gallery',
            'clientName': 'Test Client',
            'clientEmails': ['test@example.com'],
            'layout_id': 'grid_classic'
        }
        
        create_response = handle_create_gallery(sample_user, create_body)
        assert create_response['statusCode'] == 201
        created_gallery = json.loads(create_response['body'])
        gallery_id = created_gallery['id']
        
        # Update the layout
        body = {
            'layout_id': 'panoramic_hero'
        }
        
        response = handle_update_gallery(gallery_id, sample_user, body)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        assert data['layout_id'] == 'panoramic_hero'


def test_update_gallery_with_invalid_layout(sample_user, mock_galleries_table_with_storage):
    """Test updating gallery with invalid layout returns error"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        # First create a gallery
        create_body = {
            'name': 'Test Gallery',
            'clientName': 'Test Client',
            'clientEmails': ['test@example.com'],
            'layout_id': 'grid_classic'
        }
        
        create_response = handle_create_gallery(sample_user, create_body)
        assert create_response['statusCode'] == 201
        created_gallery = json.loads(create_response['body'])
        gallery_id = created_gallery['id']
        
        body = {
            'layout_id': 'nonexistent_layout'
        }
        
        response = handle_update_gallery(gallery_id, sample_user, body)
        
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Invalid layout_id' in data['error']


def test_list_layouts_all():
    """Test listing all layouts"""
    response = handle_list_layouts()
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert 'layouts' in data
    assert 'categories' in data
    assert 'total' in data
    
    assert len(data['layouts']) > 0
    assert len(data['categories']) > 0
    
    # Check layout structure
    first_layout = data['layouts'][0]
    assert 'id' in first_layout
    assert 'name' in first_layout
    assert 'description' in first_layout
    assert 'category' in first_layout
    assert 'total_slots' in first_layout


def test_list_layouts_by_category():
    """Test listing layouts filtered by category"""
    response = handle_list_layouts({'category': 'grid'})
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert 'layouts' in data
    # All returned layouts should be in grid category
    for layout in data['layouts']:
        assert layout['category'] == 'grid'


def test_list_layouts_categories():
    """Test getting all layout categories"""
    response = handle_list_layouts()
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    expected_categories = ['grid', 'masonry', 'panoramic', 'collage', 'story']
    for category in expected_categories:
        assert category in data['categories']


def test_get_layout_details():
    """Test getting detailed information about a specific layout"""
    response = handle_get_layout('grid_classic')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert data['id'] == 'grid_classic'
    assert data['name'] == 'Classic Grid'
    assert data['category'] == 'grid'
    assert 'slots' in data
    assert len(data['slots']) == 12


def test_get_layout_not_found():
    """Test getting a non-existent layout returns 404"""
    response = handle_get_layout('nonexistent_layout')
    
    assert response['statusCode'] == 404
    data = json.loads(response['body'])
    assert 'error' in data


def test_get_masonry_layout_details():
    """Test masonry layout has mixed aspect ratios"""
    response = handle_get_layout('masonry_mixed')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert data['category'] == 'masonry'
    # Masonry should have different aspect ratios
    aspect_ratios = set(slot['aspect_ratio'] for slot in data['slots'])
    assert len(aspect_ratios) > 1  # Multiple different aspect ratios


def test_get_collage_layout_absolute_positioning():
    """Test collage layout uses absolute positioning"""
    response = handle_get_layout('collage_creative')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert data['positioning'] == 'absolute'
    # Absolute positioning should have x, y coordinates
    for slot in data['slots']:
        assert 'x' in slot
        assert 'y' in slot


def test_get_story_layout_scroll_mode():
    """Test story layout has vertical scroll mode"""
    response = handle_get_layout('story_vertical')
    
    assert response['statusCode'] == 200
    data = json.loads(response['body'])
    
    assert data['category'] == 'story'
    assert data['scroll_mode'] == 'vertical'


def test_update_gallery_layout_config(sample_user, mock_galleries_table_with_storage):
    """Test updating gallery with custom layout configuration"""
    with patch('handlers.gallery_handler.galleries_table', mock_galleries_table_with_storage), \
         patch('handlers.gallery_handler.enforce_gallery_limit', return_value=(True, None)), \
         patch('handlers.gallery_handler.send_gallery_shared_email'):
        
        # Create gallery
        create_body = {
            'name': 'Test Gallery',
            'clientName': 'Test Client',
            'clientEmails': ['test@example.com'],
            'layout_id': 'grid_classic'
        }
        
        create_response = handle_create_gallery(sample_user, create_body)
        assert create_response['statusCode'] == 201
        created_gallery = json.loads(create_response['body'])
        gallery_id = created_gallery['id']
        
        # Update with custom config
        body = {
            'layout_config': {
                'spacing': 20,
                'border_radius': 10
            }
        }
        
        response = handle_update_gallery(gallery_id, sample_user, body)
        
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        
        assert 'layout_config' in data
        assert data['layout_config']['spacing'] == 20
        assert data['layout_config']['border_radius'] == 10
