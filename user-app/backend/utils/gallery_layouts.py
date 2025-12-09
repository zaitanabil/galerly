"""
Gallery Layout Definitions
Each layout defines a fixed visual arrangement of photo slots
that photographers can fill with their images
"""

# Layout slot definition with aspect ratio and position
GALLERY_LAYOUTS = {
    'grid_classic': {
        'name': 'Classic Grid',
        'description': 'Evenly spaced squares in a clean grid pattern',
        'category': 'grid',
        'total_slots': 12,
        'slots': [
            # Row 1
            {'id': 1, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 1, 'col': 1},
            {'id': 2, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 1, 'col': 2},
            {'id': 3, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 1, 'col': 3},
            {'id': 4, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 1, 'col': 4},
            # Row 2
            {'id': 5, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 2, 'col': 1},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 2, 'col': 2},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 2, 'col': 3},
            {'id': 8, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 2, 'col': 4},
            # Row 3
            {'id': 9, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 1},
            {'id': 10, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 2},
            {'id': 11, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 3},
            {'id': 12, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 4},
        ],
        'preview_image': 'grid-classic.svg'
    },
    
    'grid_portfolio': {
        'name': 'Portfolio Grid',
        'description': 'Professional 3x3 grid perfect for showcasing work',
        'category': 'grid',
        'total_slots': 9,
        'slots': [
            # 3x3 grid with consistent square slots
            {'id': 1, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 1, 'col': 1},
            {'id': 2, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 1, 'col': 2},
            {'id': 3, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 1, 'col': 3},
            {'id': 4, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 2, 'col': 1},
            {'id': 5, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 2, 'col': 2},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 2, 'col': 3},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 1},
            {'id': 8, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 2},
            {'id': 9, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 3},
        ],
        'preview_image': 'grid-portfolio.svg'
    },
    
    'masonry_mixed': {
        'name': 'Masonry Mix',
        'description': 'Mixed portrait and landscape slots in masonry style',
        'category': 'masonry',
        'total_slots': 10,
        'slots': [
            # Large hero portrait
            {'id': 1, 'aspect_ratio': '2:3', 'width': 40, 'height': 60, 'row': 1, 'col': 1, 'rowspan': 2},
            # Top right square
            {'id': 2, 'aspect_ratio': '1:1', 'width': 30, 'height': 30, 'row': 1, 'col': 2},
            # Top right portrait
            {'id': 3, 'aspect_ratio': '2:3', 'width': 30, 'height': 45, 'row': 1, 'col': 3},
            # Middle landscape
            {'id': 4, 'aspect_ratio': '3:2', 'width': 60, 'height': 40, 'row': 2, 'col': 2, 'colspan': 2},
            # Row 3 - three squares
            {'id': 5, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 1},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 2},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 3},
            # Bottom row - portraits
            {'id': 8, 'aspect_ratio': '2:3', 'width': 33.33, 'height': 50, 'row': 4, 'col': 1},
            {'id': 9, 'aspect_ratio': '2:3', 'width': 33.33, 'height': 50, 'row': 4, 'col': 2},
            {'id': 10, 'aspect_ratio': '2:3', 'width': 33.33, 'height': 50, 'row': 4, 'col': 3},
        ],
        'preview_image': 'masonry-mixed.svg'
    },
    
    'masonry_wedding': {
        'name': 'Wedding Masonry',
        'description': 'Elegant mix optimized for wedding photography',
        'category': 'masonry',
        'total_slots': 8,
        'slots': [
            # Large hero image
            {'id': 1, 'aspect_ratio': '3:2', 'width': 66.66, 'height': 44.44, 'row': 1, 'col': 1, 'colspan': 2},
            # Side portrait
            {'id': 2, 'aspect_ratio': '2:3', 'width': 33.33, 'height': 50, 'row': 1, 'col': 3},
            # Middle row - two landscapes
            {'id': 3, 'aspect_ratio': '3:2', 'width': 50, 'height': 33.33, 'row': 2, 'col': 1},
            {'id': 4, 'aspect_ratio': '3:2', 'width': 50, 'height': 33.33, 'row': 2, 'col': 2},
            # Bottom row - four squares
            {'id': 5, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 1},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 2},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 3},
            {'id': 8, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'row': 3, 'col': 4},
        ],
        'preview_image': 'masonry-wedding.svg'
    },
    
    'panoramic_hero': {
        'name': 'Panoramic Hero',
        'description': 'One large wide hero shot with supporting images',
        'category': 'panoramic',
        'total_slots': 7,
        'slots': [
            # Hero panoramic
            {'id': 1, 'aspect_ratio': '21:9', 'width': 100, 'height': 42.86, 'row': 1, 'col': 1, 'colspan': 3},
            # Supporting row 1
            {'id': 2, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 2, 'col': 1},
            {'id': 3, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 2, 'col': 2},
            {'id': 4, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 2, 'col': 3},
            # Supporting row 2
            {'id': 5, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 1},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 2},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 33.33, 'height': 33.33, 'row': 3, 'col': 3},
        ],
        'preview_image': 'panoramic-hero.svg'
    },
    
    'panoramic_landscape': {
        'name': 'Landscape Showcase',
        'description': 'Wide panoramic layouts for landscape photography',
        'category': 'panoramic',
        'total_slots': 6,
        'slots': [
            # Three panoramic rows
            {'id': 1, 'aspect_ratio': '16:9', 'width': 100, 'height': 56.25, 'row': 1, 'col': 1},
            {'id': 2, 'aspect_ratio': '16:9', 'width': 100, 'height': 56.25, 'row': 2, 'col': 1},
            {'id': 3, 'aspect_ratio': '16:9', 'width': 100, 'height': 56.25, 'row': 3, 'col': 1},
            # Bottom supporting images
            {'id': 4, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 4, 'col': 1},
            {'id': 5, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 4, 'col': 2},
            {'id': 6, 'aspect_ratio': '3:2', 'width': 33.33, 'height': 22.22, 'row': 4, 'col': 3},
        ],
        'preview_image': 'panoramic-landscape.svg'
    },
    
    'collage_creative': {
        'name': 'Creative Collage',
        'description': 'Overlapping and creatively arranged photo slots',
        'category': 'collage',
        'total_slots': 9,
        'slots': [
            # Center large portrait (z-index 2)
            {'id': 1, 'aspect_ratio': '2:3', 'width': 40, 'height': 60, 'x': 30, 'y': 20, 'z_index': 2},
            # Background landscape (z-index 1)
            {'id': 2, 'aspect_ratio': '16:9', 'width': 60, 'height': 33.75, 'x': 5, 'y': 10, 'z_index': 1},
            # Top right square (z-index 2)
            {'id': 3, 'aspect_ratio': '1:1', 'width': 25, 'height': 25, 'x': 70, 'y': 5, 'z_index': 2},
            # Bottom left portrait (z-index 2)
            {'id': 4, 'aspect_ratio': '2:3', 'width': 30, 'height': 45, 'x': 10, 'y': 50, 'z_index': 2},
            # Middle right landscape (z-index 1)
            {'id': 5, 'aspect_ratio': '3:2', 'width': 50, 'height': 33.33, 'x': 45, 'y': 60, 'z_index': 1},
            # Small accents
            {'id': 6, 'aspect_ratio': '1:1', 'width': 15, 'height': 15, 'x': 5, 'y': 5, 'z_index': 3},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 15, 'height': 15, 'x': 75, 'y': 45, 'z_index': 3},
            {'id': 8, 'aspect_ratio': '1:1', 'width': 15, 'height': 15, 'x': 50, 'y': 5, 'z_index': 3},
            {'id': 9, 'aspect_ratio': '1:1', 'width': 15, 'height': 15, 'x': 40, 'y': 85, 'z_index': 3},
        ],
        'positioning': 'absolute',
        'preview_image': 'collage-creative.svg'
    },
    
    'collage_magazine': {
        'name': 'Magazine Spread',
        'description': 'Editorial style layout with dynamic positioning',
        'category': 'collage',
        'total_slots': 7,
        'slots': [
            # Left page hero
            {'id': 1, 'aspect_ratio': '2:3', 'width': 45, 'height': 67.5, 'x': 2, 'y': 15, 'z_index': 2},
            # Right page main
            {'id': 2, 'aspect_ratio': '3:2', 'width': 50, 'height': 33.33, 'x': 48, 'y': 10, 'z_index': 1},
            # Right page secondary
            {'id': 3, 'aspect_ratio': '1:1', 'width': 30, 'height': 30, 'x': 60, 'y': 50, 'z_index': 2},
            # Overlay accents
            {'id': 4, 'aspect_ratio': '1:1', 'width': 20, 'height': 20, 'x': 40, 'y': 5, 'z_index': 3},
            {'id': 5, 'aspect_ratio': '3:2', 'width': 35, 'height': 23.33, 'x': 10, 'y': 75, 'z_index': 2},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 18, 'height': 18, 'x': 75, 'y': 75, 'z_index': 3},
            {'id': 7, 'aspect_ratio': '2:3', 'width': 25, 'height': 37.5, 'x': 48, 'y': 55, 'z_index': 1},
        ],
        'positioning': 'absolute',
        'preview_image': 'collage-magazine.svg'
    },
    
    'story_vertical': {
        'name': 'Story Sequence',
        'description': 'Vertical sequence similar to social media stories',
        'category': 'story',
        'total_slots': 6,
        'slots': [
            # Full-height story slots (9:16 aspect ratio)
            {'id': 1, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 1, 'col': 1},
            {'id': 2, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 2, 'col': 1},
            {'id': 3, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 3, 'col': 1},
            {'id': 4, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 4, 'col': 1},
            {'id': 5, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 5, 'col': 1},
            {'id': 6, 'aspect_ratio': '9:16', 'width': 100, 'height': 177.78, 'row': 6, 'col': 1},
        ],
        'scroll_mode': 'vertical',
        'preview_image': 'story-vertical.svg'
    },
    
    'story_feed': {
        'name': 'Social Feed',
        'description': 'Square posts with captions like social media',
        'category': 'story',
        'total_slots': 8,
        'slots': [
            # Square posts (1:1) with caption space
            {'id': 1, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 1, 'col': 1, 'has_caption': True},
            {'id': 2, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 2, 'col': 1, 'has_caption': True},
            {'id': 3, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 3, 'col': 1, 'has_caption': True},
            {'id': 4, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 4, 'col': 1, 'has_caption': True},
            {'id': 5, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 5, 'col': 1, 'has_caption': True},
            {'id': 6, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 6, 'col': 1, 'has_caption': True},
            {'id': 7, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 7, 'col': 1, 'has_caption': True},
            {'id': 8, 'aspect_ratio': '1:1', 'width': 100, 'height': 100, 'row': 8, 'col': 1, 'has_caption': True},
        ],
        'scroll_mode': 'vertical',
        'preview_image': 'story-feed.svg'
    },
    
    'story_carousel': {
        'name': 'Carousel Story',
        'description': 'Horizontal scrolling carousel for mobile-optimized viewing',
        'category': 'story',
        'total_slots': 10,
        'slots': [
            # Horizontal carousel slots (4:5 aspect ratio - mobile portrait)
            {'id': 1, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 1},
            {'id': 2, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 2},
            {'id': 3, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 3},
            {'id': 4, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 4},
            {'id': 5, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 5},
            {'id': 6, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 6},
            {'id': 7, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 7},
            {'id': 8, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 8},
            {'id': 9, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 9},
            {'id': 10, 'aspect_ratio': '4:5', 'width': 80, 'height': 100, 'row': 1, 'col': 10},
        ],
        'scroll_mode': 'horizontal',
        'preview_image': 'story-carousel.svg'
    }
}


def get_layout(layout_id):
    """Get a specific layout by ID"""
    return GALLERY_LAYOUTS.get(layout_id)


def get_all_layouts():
    """Get all available layouts"""
    return GALLERY_LAYOUTS


def get_layouts_by_category(category):
    """Get all layouts in a specific category"""
    return {
        layout_id: layout 
        for layout_id, layout in GALLERY_LAYOUTS.items() 
        if layout['category'] == category
    }


def get_layout_categories():
    """Get list of all layout categories"""
    categories = set()
    for layout in GALLERY_LAYOUTS.values():
        categories.add(layout['category'])
    return sorted(list(categories))


def validate_layout_photos(layout_id, photo_count):
    """
    Validate that the number of photos matches the layout requirements
    Returns (is_valid, message)
    """
    layout = get_layout(layout_id)
    if not layout:
        return False, f"Layout '{layout_id}' not found"
    
    required_slots = layout['total_slots']
    if photo_count < required_slots:
        return False, f"Layout requires {required_slots} photos, but only {photo_count} provided"
    
    if photo_count > required_slots:
        return False, f"Layout accepts {required_slots} photos, but {photo_count} were provided"
    
    return True, "Valid"
