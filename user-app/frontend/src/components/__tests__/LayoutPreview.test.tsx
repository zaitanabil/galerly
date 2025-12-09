import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import LayoutPreview from '../LayoutPreview';

describe('LayoutPreview', () => {
  const mockGridLayout = {
    id: 'grid_classic',
    name: 'Classic Grid',
    description: 'Evenly spaced squares',
    category: 'grid',
    total_slots: 4,
    slots: [
      { id: 1, aspect_ratio: '1:1', width: 25, height: 25, row: 1, col: 1 },
      { id: 2, aspect_ratio: '1:1', width: 25, height: 25, row: 1, col: 2 },
      { id: 3, aspect_ratio: '1:1', width: 25, height: 25, row: 2, col: 1 },
      { id: 4, aspect_ratio: '1:1', width: 25, height: 25, row: 2, col: 2 },
    ],
  };

  const mockCollageLayout = {
    id: 'collage_creative',
    name: 'Creative Collage',
    description: 'Overlapping photos',
    category: 'collage',
    total_slots: 3,
    positioning: 'absolute',
    slots: [
      { id: 1, aspect_ratio: '2:3', width: 40, height: 60, x: 30, y: 20, z_index: 2 },
      { id: 2, aspect_ratio: '16:9', width: 60, height: 33.75, x: 5, y: 10, z_index: 1 },
      { id: 3, aspect_ratio: '1:1', width: 25, height: 25, x: 70, y: 5, z_index: 3 },
    ],
  };

  const mockStoryLayout = {
    id: 'story_vertical',
    name: 'Story Sequence',
    description: 'Vertical stories',
    category: 'story',
    total_slots: 6,
    scroll_mode: 'vertical',
    slots: [
      { id: 1, aspect_ratio: '9:16', width: 100, height: 177.78, row: 1, col: 1 },
      { id: 2, aspect_ratio: '9:16', width: 100, height: 177.78, row: 2, col: 1 },
      { id: 3, aspect_ratio: '9:16', width: 100, height: 177.78, row: 3, col: 1 },
      { id: 4, aspect_ratio: '9:16', width: 100, height: 177.78, row: 4, col: 1 },
      { id: 5, aspect_ratio: '9:16', width: 100, height: 177.78, row: 5, col: 1 },
      { id: 6, aspect_ratio: '9:16', width: 100, height: 177.78, row: 6, col: 1 },
    ],
  };

  it('renders grid layout preview', () => {
    const { container } = render(<LayoutPreview layout={mockGridLayout} />);
    
    // Check SVG is rendered
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
    
    // Check viewBox
    expect(svg?.getAttribute('viewBox')).toBe('0 0 400 300');
    
    // Check that rectangles are rendered for slots
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBeGreaterThan(mockGridLayout.total_slots); // Includes background and indicator
  });

  it('renders collage layout with absolute positioning', () => {
    const { container } = render(<LayoutPreview layout={mockCollageLayout} />);
    
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
    
    // Should render all slots
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBeGreaterThan(mockCollageLayout.total_slots);
  });

  it('renders story layout with vertical scroll', () => {
    const { container } = render(<LayoutPreview layout={mockStoryLayout} />);
    
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
    
    // Story layout renders only first 2 slots in preview
    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBeGreaterThan(0);
  });

  it('displays total slot count', () => {
    const { container } = render(<LayoutPreview layout={mockGridLayout} />);
    
    // Check for slot count text
    const text = container.querySelector('text');
    expect(text?.textContent).toBe(mockGridLayout.total_slots.toString());
  });

  it('applies custom className', () => {
    const { container } = render(
      <LayoutPreview layout={mockGridLayout} className="custom-class" />
    );
    
    const svg = container.querySelector('svg');
    expect(svg?.classList.contains('custom-class')).toBe(true);
  });

  it('handles layout without positioning property', () => {
    const layoutWithoutPositioning = {
      ...mockGridLayout,
      positioning: undefined,
    };
    
    const { container } = render(<LayoutPreview layout={layoutWithoutPositioning} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
  });

  it('handles horizontal carousel story layout', () => {
    const carouselLayout = {
      id: 'story_carousel',
      name: 'Carousel Story',
      description: 'Horizontal carousel',
      category: 'story',
      total_slots: 10,
      scroll_mode: 'horizontal',
      slots: Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        aspect_ratio: '4:5',
        width: 80,
        height: 100,
        row: 1,
        col: i + 1,
      })),
    };
    
    const { container } = render(<LayoutPreview layout={carouselLayout} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
  });

  it('renders with slots that have captions', () => {
    const layoutWithCaptions = {
      ...mockStoryLayout,
      slots: mockStoryLayout.slots.map(slot => ({ ...slot, has_caption: true })),
    };
    
    const { container } = render(<LayoutPreview layout={layoutWithCaptions} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
  });
});
