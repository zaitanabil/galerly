"""
Tests for gallery layout system
"""
import pytest
from utils.gallery_layouts import (
    get_layout, 
    get_all_layouts, 
    get_layouts_by_category,
    get_layout_categories,
    validate_layout_photos
)


def test_get_layout_exists():
    """Test getting an existing layout"""
    layout = get_layout('grid_classic')
    assert layout is not None
    assert layout['name'] == 'Classic Grid'
    assert layout['category'] == 'grid'
    assert layout['total_slots'] == 12
    assert len(layout['slots']) == 12


def test_get_layout_not_exists():
    """Test getting a non-existent layout"""
    layout = get_layout('nonexistent_layout')
    assert layout is None


def test_get_all_layouts():
    """Test getting all layouts"""
    layouts = get_all_layouts()
    assert isinstance(layouts, dict)
    assert len(layouts) > 0
    
    # Check that all required layout types exist
    assert 'grid_classic' in layouts
    assert 'masonry_mixed' in layouts
    assert 'panoramic_hero' in layouts
    assert 'collage_creative' in layouts
    assert 'story_vertical' in layouts


def test_get_layouts_by_category():
    """Test filtering layouts by category"""
    # Test grid category
    grid_layouts = get_layouts_by_category('grid')
    assert len(grid_layouts) >= 2
    for layout in grid_layouts.values():
        assert layout['category'] == 'grid'
    
    # Test masonry category
    masonry_layouts = get_layouts_by_category('masonry')
    assert len(masonry_layouts) >= 2
    for layout in masonry_layouts.values():
        assert layout['category'] == 'masonry'
    
    # Test story category
    story_layouts = get_layouts_by_category('story')
    assert len(story_layouts) >= 3
    for layout in story_layouts.values():
        assert layout['category'] == 'story'


def test_get_layout_categories():
    """Test getting list of all categories"""
    categories = get_layout_categories()
    assert isinstance(categories, list)
    assert 'grid' in categories
    assert 'masonry' in categories
    assert 'panoramic' in categories
    assert 'collage' in categories
    assert 'story' in categories


def test_layout_slot_properties():
    """Test that layout slots have required properties"""
    layout = get_layout('grid_classic')
    
    for slot in layout['slots']:
        assert 'id' in slot
        assert 'aspect_ratio' in slot
        assert 'width' in slot
        assert 'height' in slot
        
        # Grid layouts should have row and col
        assert 'row' in slot
        assert 'col' in slot


def test_collage_layout_absolute_positioning():
    """Test that collage layouts use absolute positioning"""
    layout = get_layout('collage_creative')
    
    assert layout['positioning'] == 'absolute'
    
    for slot in layout['slots']:
        assert 'x' in slot
        assert 'y' in slot
        assert 'z_index' in slot


def test_story_layout_vertical_scroll():
    """Test that story layouts have vertical scroll mode"""
    layout = get_layout('story_vertical')
    
    assert layout['scroll_mode'] == 'vertical'
    
    # Story layouts should have 9:16 aspect ratio (portrait)
    for slot in layout['slots']:
        assert slot['aspect_ratio'] == '9:16'


def test_panoramic_layout_wide_slots():
    """Test that panoramic layouts have wide aspect ratios"""
    layout = get_layout('panoramic_hero')
    
    # First slot should be the hero panoramic
    hero_slot = layout['slots'][0]
    assert hero_slot['aspect_ratio'] == '21:9'
    assert hero_slot['width'] == 100  # Full width


def test_validate_layout_photos_exact_match():
    """Test photo count validation when count matches"""
    is_valid, message = validate_layout_photos('grid_classic', 12)
    assert is_valid is True
    assert message == "Valid"


def test_validate_layout_photos_too_few():
    """Test photo count validation when count is less than required"""
    is_valid, message = validate_layout_photos('grid_classic', 8)
    assert is_valid is False
    assert 'requires 12 photos' in message


def test_validate_layout_photos_too_many():
    """Test photo count validation when count is more than required"""
    is_valid, message = validate_layout_photos('grid_classic', 15)
    assert is_valid is False
    assert 'accepts 12 photos' in message


def test_validate_layout_photos_invalid_layout():
    """Test photo count validation with invalid layout ID"""
    is_valid, message = validate_layout_photos('invalid_layout', 10)
    assert is_valid is False
    assert 'not found' in message


def test_masonry_layout_mixed_aspect_ratios():
    """Test that masonry layouts have mixed aspect ratios"""
    layout = get_layout('masonry_mixed')
    
    aspect_ratios = set(slot['aspect_ratio'] for slot in layout['slots'])
    
    # Should have at least 2 different aspect ratios
    assert len(aspect_ratios) >= 2
    
    # Common aspect ratios in masonry
    assert any(ratio in aspect_ratios for ratio in ['1:1', '2:3', '3:2'])


def test_all_layouts_have_preview_image():
    """Test that all layouts have a preview image specified"""
    layouts = get_all_layouts()
    
    for layout_id, layout in layouts.items():
        assert 'preview_image' in layout
        assert layout['preview_image'] is not None
        assert layout['preview_image'].endswith('.svg')


def test_layout_slot_ids_sequential():
    """Test that slot IDs are sequential starting from 1"""
    layouts = get_all_layouts()
    
    for layout_id, layout in layouts.items():
        slot_ids = [slot['id'] for slot in layout['slots']]
        
        # IDs should start at 1
        assert min(slot_ids) == 1
        
        # IDs should be sequential
        assert max(slot_ids) == len(slot_ids)
        
        # No duplicates
        assert len(slot_ids) == len(set(slot_ids))


def test_grid_portfolio_3x3():
    """Test that portfolio grid is exactly 3x3"""
    layout = get_layout('grid_portfolio')
    
    assert layout['total_slots'] == 9
    
    rows = set(slot['row'] for slot in layout['slots'])
    cols = set(slot['col'] for slot in layout['slots'])
    
    assert len(rows) == 3
    assert len(cols) == 3


def test_story_carousel_horizontal_scroll():
    """Test that carousel has horizontal scroll mode"""
    layout = get_layout('story_carousel')
    
    assert layout['scroll_mode'] == 'horizontal'
    assert layout['total_slots'] == 10


def test_wedding_masonry_hero_image():
    """Test that wedding masonry has a large hero image"""
    layout = get_layout('masonry_wedding')
    
    # First slot should be the hero (spans multiple columns)
    hero_slot = layout['slots'][0]
    assert 'colspan' in hero_slot
    assert hero_slot['colspan'] == 2
    assert hero_slot['aspect_ratio'] == '3:2'
