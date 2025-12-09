import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Settings, Layers } from 'lucide-react';
import GalleryLayoutRenderer from '../components/GalleryLayoutRenderer';

interface Photo {
  id: string;
  url: string;
  thumbnail_url?: string;
  medium_url?: string;
  title?: string;
  description?: string;
  is_favorite?: boolean;
  favorites_count?: number;
}

interface GalleryLayout {
  id: string;
  name: string;
  description: string;
  category: string;
  total_slots: number;
  slots: any[];
  positioning?: string;
  scroll_mode?: string;
}

interface Gallery {
  id: string;
  name: string;
  description?: string;
  layout_id?: string;
  photos: Photo[];
}

export default function GalleryLayoutPreview() {
  const { galleryId } = useParams<{ galleryId: string }>();
  const [gallery, setGallery] = useState<Gallery | null>(null);
  const [layout, setLayout] = useState<GalleryLayout | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGalleryAndLayout = async () => {
      if (!galleryId) return;

      try {
        setLoading(true);
        
        // Fetch gallery data
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
        const token = localStorage.getItem('token');
        
        const galleryResponse = await fetch(`${apiUrl}/v1/galleries/${galleryId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!galleryResponse.ok) {
          throw new Error('Failed to fetch gallery');
        }
        
        const galleryData = await galleryResponse.json();
        setGallery(galleryData);
        
        // Fetch layout if specified (public endpoint - no auth required)
        const layoutId = galleryData.layout_id || 'grid_classic';
        const layoutResponse = await fetch(`${apiUrl}/v1/gallery-layouts/${layoutId}`);
        
        if (!layoutResponse.ok) {
          throw new Error('Failed to fetch layout');
        }
        
        const layoutData = await layoutResponse.json();
        setLayout(layoutData);
        
      } catch (err) {
        console.error('Error fetching gallery/layout:', err);
        setError(err instanceof Error ? err.message : 'Failed to load gallery');
      } finally {
        setLoading(false);
      }
    };

    fetchGalleryAndLayout();
  }, [galleryId]);

  const handlePhotoClick = (photo: Photo, index: number) => {
    // Open lightbox or full view
    console.log('Photo clicked:', photo, index);
  };

  const handleFavoriteToggle = async (photoId: string) => {
    if (!gallery) return;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('token');
      
      // Check if photo is already favorited
      const photo = gallery.photos.find(p => p.id === photoId);
      const isFavorited = photo?.is_favorite;
      
      // Call favorite API
      const response = await fetch(
        `${apiUrl}/v1/galleries/${gallery.id}/photos/${photoId}/favorite`,
        {
          method: isFavorited ? 'DELETE' : 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to toggle favorite');
      }
      
      // Update local state
      setGallery(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          photos: prev.photos.map(p => 
            p.id === photoId 
              ? { 
                  ...p, 
                  is_favorite: !isFavorited,
                  favorites_count: (p.favorites_count || 0) + (isFavorited ? -1 : 1)
                }
              : p
          )
        };
      });
      
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  const handleDownload = async (photoId: string) => {
    if (!gallery) return;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
      const token = localStorage.getItem('token');
      
      // Get download URL from API
      const response = await fetch(
        `${apiUrl}/v1/galleries/${gallery.id}/photos/${photoId}/download`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }
      
      const data = await response.json();
      
      // Trigger download
      if (data.download_url) {
        const photo = gallery.photos.find(p => p.id === photoId);
        const filename = photo?.title || `photo_${photoId}.jpg`;
        
        // Create hidden link and trigger download
        const link = document.createElement('a');
        link.href = data.download_url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      
    } catch (err) {
      console.error('Error downloading photo:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#1D1D1F]/60">Loading gallery...</p>
        </div>
      </div>
    );
  }

  if (error || !gallery || !layout) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-6">
          <p className="text-red-600 mb-4">{error || 'Gallery not found'}</p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#0066CC] text-white rounded-full hover:bg-[#0052A3] transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/gallery/${galleryId}`}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <div>
                <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                  {gallery.name}
                </h1>
                <div className="flex items-center gap-2 text-sm text-[#1D1D1F]/60 mt-1">
                  <Layers className="w-4 h-4" />
                  <span>{layout.name}</span>
                </div>
              </div>
            </div>
            <Link
              to={`/gallery/${galleryId}/settings`}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <Settings className="w-5 h-5 text-[#1D1D1F]" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {gallery.description && (
          <div className="mb-8 text-center">
            <p className="text-[#1D1D1F]/70">{gallery.description}</p>
          </div>
        )}

        {gallery.photos.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <Layers className="w-16 h-16 text-[#1D1D1F]/20 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
              No Photos Yet
            </h3>
            <p className="text-[#1D1D1F]/60 mb-6">
              Upload {layout.total_slots} photos to fill this {layout.name} layout
            </p>
            <Link
              to={`/gallery/${galleryId}`}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#0066CC] text-white rounded-full hover:bg-[#0052A3] transition-all"
            >
              Upload Photos
            </Link>
          </div>
        ) : (
          <div>
            <GalleryLayoutRenderer
              layout={layout}
              photos={gallery.photos}
              onPhotoClick={handlePhotoClick}
              onFavoriteToggle={handleFavoriteToggle}
              onDownload={handleDownload}
              showActions={true}
            />
            
            {/* Layout Info */}
            <div className="mt-8 p-6 glass-panel text-center">
              <div className="flex items-center justify-center gap-2 text-sm text-[#1D1D1F]/60">
                <Layers className="w-4 h-4" />
                <span>
                  Using {layout.name} layout ({gallery.photos.length} of {layout.total_slots} photos)
                </span>
              </div>
              {gallery.photos.length < layout.total_slots && (
                <p className="mt-2 text-sm text-[#0066CC]">
                  Add {layout.total_slots - gallery.photos.length} more photo(s) to complete this layout
                </p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

