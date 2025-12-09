/**
 * LayoutPreview Component
 * Generates dynamic SVG previews for gallery layouts
 */
import { useMemo } from 'react';

interface LayoutSlot {
  id: number;
  aspect_ratio: string;
  width: number;
  height: number;
  row?: number;
  col?: number;
  rowspan?: number;
  colspan?: number;
  x?: number;
  y?: number;
  z_index?: number;
  has_caption?: boolean;
}

interface GalleryLayout {
  id: string;
  name: string;
  description: string;
  category: string;
  total_slots: number;
  slots: LayoutSlot[];
  positioning?: string;
  scroll_mode?: string;
}

interface LayoutPreviewProps {
  layout: GalleryLayout;
  className?: string;
}

export default function LayoutPreview({ layout, className = '' }: LayoutPreviewProps) {
  const svgPreview = useMemo(() => {
    // Validate layout and slots
    if (!layout || !layout.slots || layout.slots.length === 0) {
      return (
        <svg
          viewBox="0 0 400 300"
          xmlns="http://www.w3.org/2000/svg"
          className={`w-full h-full ${className}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <rect width="400" height="300" fill="#F9FAFB" />
          <text
            x="200"
            y="150"
            textAnchor="middle"
            fontSize="14"
            fill="#9CA3AF"
          >
            No preview available
          </text>
        </svg>
      );
    }
    
    const viewBoxWidth = 400;
    const viewBoxHeight = 300;
    const padding = 8;
    
    // Base colors
    const baseColor = '#E5E7EB'; // gray-200
    const accentColor = '#0066CC'; // primary blue
    
    const renderGridLayout = () => {
      // Calculate grid dimensions
      const maxRow = Math.max(...layout.slots.map(s => s.row || 1));
      const maxCol = Math.max(...layout.slots.map(s => s.col || 1));
      
      const cellWidth = (viewBoxWidth - (maxCol + 1) * padding) / maxCol;
      const cellHeight = (viewBoxHeight - (maxRow + 1) * padding) / maxRow;
      
      return layout.slots.map((slot, index) => {
        const x = ((slot.col || 1) - 1) * (cellWidth + padding) + padding;
        const y = ((slot.row || 1) - 1) * (cellHeight + padding) + padding;
        const width = cellWidth * (slot.colspan || 1) + padding * ((slot.colspan || 1) - 1);
        const height = cellHeight * (slot.rowspan || 1) + padding * ((slot.rowspan || 1) - 1);
        
        // Alternate colors for visual interest
        const color = index % 3 === 0 ? accentColor : baseColor;
        const opacity = index % 3 === 0 ? 0.6 : 0.9;
        
        return (
          <rect
            key={slot.id}
            x={x}
            y={y}
            width={width}
            height={height}
            fill={color}
            opacity={opacity}
            rx="6"
          />
        );
      });
    };
    
    const renderAbsoluteLayout = () => {
      return layout.slots.map((slot, _index) => {
        const x = (slot.x || 0) * viewBoxWidth / 100;
        const y = (slot.y || 0) * viewBoxHeight / 100;
        const width = (slot.width || 20) * viewBoxWidth / 100;
        const height = (slot.height || 20) * viewBoxHeight / 100;
        
        // Use z_index for color variation
        const zIndex = slot.z_index || 1;
        const color = zIndex === 3 ? accentColor : zIndex === 2 ? '#3B82F6' : baseColor;
        const opacity = zIndex === 3 ? 0.8 : zIndex === 2 ? 0.7 : 0.6;
        
        return (
          <rect
            key={slot.id}
            x={x}
            y={y}
            width={width}
            height={height}
            fill={color}
            opacity={opacity}
            rx="6"
          />
        );
      });
    };
    
    const renderStoryLayout = () => {
      if (!layout.slots || layout.slots.length === 0) return [];
      
      if (layout.scroll_mode === 'horizontal') {
        // Carousel style - show first 3 slots horizontally
        const visibleSlots = layout.slots.slice(0, 3);
        const slotWidth = (viewBoxWidth - 4 * padding) / 3;
        const slotHeight = viewBoxHeight - 2 * padding;
        
        return visibleSlots.map((slot, index) => {
          const x = index * (slotWidth + padding) + padding;
          const y = padding;
          const color = index === 0 ? accentColor : baseColor;
          const opacity = index === 0 ? 0.7 : 0.8;
          
          return (
            <rect
              key={slot.id}
              x={x}
              y={y}
              width={slotWidth}
              height={slotHeight}
              fill={color}
              opacity={opacity}
              rx="8"
            />
          );
        });
      } else {
        // Vertical story - show stacked vertical rectangles
        const visibleSlots = layout.slots.slice(0, 2);
        const slotWidth = viewBoxWidth * 0.6;
        const slotHeight = viewBoxHeight * 0.45;
        const x = (viewBoxWidth - slotWidth) / 2;
        
        return visibleSlots.map((slot, index) => {
          const y = index * (slotHeight + padding) + padding;
          const color = index === 0 ? accentColor : baseColor;
          const opacity = 0.75;
          
          return (
            <g key={slot.id}>
              <rect
                x={x}
                y={y}
                width={slotWidth}
                height={slotHeight}
                fill={color}
                opacity={opacity}
                rx="12"
              />
              {slot.has_caption && (
                <rect
                  x={x + 10}
                  y={y + slotHeight - 30}
                  width={slotWidth - 20}
                  height={4}
                  fill="white"
                  opacity="0.6"
                  rx="2"
                />
              )}
            </g>
          );
        });
      }
    };
    
    // Determine rendering method based on layout properties
    let slots;
    if (layout.category === 'story') {
      slots = renderStoryLayout();
    } else if (layout.positioning === 'absolute' || layout.category === 'collage') {
      slots = renderAbsoluteLayout();
    } else {
      slots = renderGridLayout();
    }
    
    return (
      <svg
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        xmlns="http://www.w3.org/2000/svg"
        className={`w-full h-full ${className}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Background */}
        <rect
          width={viewBoxWidth}
          height={viewBoxHeight}
          fill="#F9FAFB"
        />
        
        {/* Layout slots */}
        {slots}
        
        {/* Slot count indicator */}
        <g>
          <rect
            x={viewBoxWidth - 50}
            y={viewBoxHeight - 30}
            width="40"
            height="20"
            fill="white"
            opacity="0.9"
            rx="10"
          />
          <text
            x={viewBoxWidth - 30}
            y={viewBoxHeight - 15}
            textAnchor="middle"
            fontSize="12"
            fontWeight="600"
            fill="#1D1D1F"
          >
            {layout.total_slots}
          </text>
        </g>
      </svg>
    );
  }, [layout, className]);
  
  return svgPreview;
}
