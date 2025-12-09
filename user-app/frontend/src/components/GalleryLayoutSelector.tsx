import { useState, useEffect } from 'react';
import { Grid, Layers, Maximize2, Shuffle, TrendingUp, Check, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import LayoutPreview from './LayoutPreview';

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
  preview_image?: string;
  scroll_mode?: string;
  positioning?: string;
}

interface GalleryLayoutSelectorProps {
  selectedLayoutId?: string;
  onSelectLayout: (layoutId: string, layout: GalleryLayout) => void;
  onCancel?: () => void;
  inline?: boolean; // If true, select immediately without "Use Layout" button
}

const CATEGORY_ICONS: Record<string, any> = {
  grid: Grid,
  masonry: Layers,
  panoramic: Maximize2,
  collage: Shuffle,
  story: TrendingUp
};

const CATEGORY_NAMES: Record<string, string> = {
  grid: 'Grid',
  masonry: 'Masonry',
  panoramic: 'Panoramic',
  collage: 'Collage',
  story: 'Story'
};

export default function GalleryLayoutSelector({ 
  selectedLayoutId, 
  onSelectLayout,
  onCancel,
  inline = false
}: GalleryLayoutSelectorProps) {
  const [layouts, setLayouts] = useState<GalleryLayout[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedLayout, setSelectedLayout] = useState<string>(selectedLayoutId || '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch layouts from API
  useEffect(() => {
    const fetchLayouts = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
        
        // Public endpoint - no auth required
        const response = await fetch(`${apiUrl}/v1/gallery-layouts`);
        const data = await response.json();
        
        if (response.ok) {
          setLayouts(data.layouts || []);
          setCategories(data.categories || []);
          
          // Select first category by default
          if (data.categories && data.categories.length > 0) {
            setSelectedCategory(data.categories[0]);
          }
        } else {
          throw new Error(data.error || 'Failed to fetch layouts');
        }
      } catch (err) {
        console.error('Error fetching layouts:', err);
        setError(err instanceof Error ? err.message : 'Failed to load layouts');
        toast.error('Failed to load gallery layouts');
      } finally {
        setLoading(false);
      }
    };

    fetchLayouts();
  }, []);

  // Filter layouts by selected category
  const filteredLayouts = selectedCategory
    ? layouts.filter(layout => layout.category === selectedCategory)
    : layouts;

  const handleSelectLayout = () => {
    const layout = layouts.find(l => l.id === selectedLayout);
    if (layout) {
      onSelectLayout(selectedLayout, layout);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-[#1D1D1F]/60">Loading layouts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-6 py-2.5 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="text-center mb-8">
        <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
          Choose Gallery Layout
        </h3>
        <p className="text-sm text-[#1D1D1F]/60">
          Select a predefined layout to arrange your photos
        </p>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {categories.map((category) => {
          const Icon = CATEGORY_ICONS[category] || Grid;
          const isActive = selectedCategory === category;

          return (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-[#0066CC] text-white'
                  : 'bg-gray-100 text-[#1D1D1F]/60 hover:bg-gray-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{CATEGORY_NAMES[category] || category}</span>
            </button>
          );
        })}
      </div>

      {/* Layout Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {filteredLayouts.map((layout) => {
          const isSelected = selectedLayout === layout.id;

          return (
            <button
              key={layout.id}
              onClick={() => {
                setSelectedLayout(layout.id);
                // In inline mode, select immediately
                if (inline) {
                  onSelectLayout(layout.id, layout);
                }
              }}
              className={`text-left p-5 rounded-xl border-2 transition-all ${
                isSelected
                  ? 'border-[#0066CC] bg-blue-50/50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-medium text-[#1D1D1F] mb-1">{layout.name}</h4>
                  <p className="text-sm text-[#1D1D1F]/60 mb-3">{layout.description}</p>
                </div>
                {isSelected && (
                  <div className="w-6 h-6 bg-[#0066CC] rounded-full flex items-center justify-center flex-shrink-0 ml-2">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>

              {/* Layout Preview */}
              <div className="bg-gray-50 rounded-lg p-3 mb-3 overflow-hidden">
                <div className="aspect-video">
                  {layout && layout.slots ? (
                    <LayoutPreview layout={{ ...layout, id: layout.id }} />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <Layers className="w-8 h-8 text-[#1D1D1F]/30" />
                    </div>
                  )}
                </div>
              </div>

              {/* Layout Info */}
              <div className="flex items-center gap-2 text-xs text-[#1D1D1F]/60">
                <Info className="w-3 h-3" />
                <span>{layout.total_slots} photo slots</span>
              </div>
            </button>
          );
        })}
      </div>

      {filteredLayouts.length === 0 && (
        <div className="text-center py-8 text-[#1D1D1F]/60">
          No layouts available in this category
        </div>
      )}

      {/* Actions */}
      {!inline && (
        <div className="flex gap-3 justify-center">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-6 py-2.5 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleSelectLayout}
            disabled={!selectedLayout}
            className="px-8 py-2.5 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Use Layout
          </button>
        </div>
      )}
    </div>
  );
}
