import { useState } from 'react';
import { Heart, Download } from 'lucide-react';

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
  slots: LayoutSlot[];
  positioning?: string;
  scroll_mode?: string;
}

interface GalleryLayoutRendererProps {
  layout: GalleryLayout;
  photos: Photo[];
  onPhotoClick?: (photo: Photo, index: number) => void;
  onFavoriteToggle?: (photoId: string) => void;
  onDownload?: (photoId: string) => void;
  showActions?: boolean;
}

export default function GalleryLayoutRenderer({
  layout,
  photos,
  onPhotoClick,
  onFavoriteToggle,
  onDownload,
  showActions = true
}: GalleryLayoutRendererProps) {
  const [_loadedImages, setLoadedImages] = useState<Set<string>>(new Set());

  // Convert aspect ratio string to number (e.g., "16:9" -> 16/9)
  const getAspectRatioValue = (ratio: string): number => {
    const [w, h] = ratio.split(':').map(Number);
    return w / h;
  };

  // Render grid-based layout (supports repeating pattern for unlimited photos)
  const renderGridLayout = () => {
    const patternSize = layout.slots.length;
    
    // Calculate how many complete patterns + remaining photos
    const completePatterns = Math.floor(photos.length / patternSize);
    const remainingPhotos = photos.length % patternSize;
    const totalPatterns = completePatterns + (remainingPhotos > 0 ? 1 : 0);
    
    return (
      <div className="space-y-6">
        {Array.from({ length: totalPatterns }).map((_, patternIndex) => {
          // Group slots by row for this pattern
          const rowGroups: Record<number, LayoutSlot[]> = {};
          layout.slots.forEach(slot => {
            const row = slot.row || 1;
            if (!rowGroups[row]) {
              rowGroups[row] = [];
            }
            rowGroups[row].push(slot);
          });

          return (
            <div key={patternIndex} className="space-y-2">
              {Object.entries(rowGroups).map(([rowNum, slots]) => (
                <div key={`${patternIndex}-${rowNum}`} className="flex gap-2">
                  {slots.map((slot) => {
                    // Calculate actual photo index: pattern_index * pattern_size + slot_offset
                    const photoIndex = patternIndex * patternSize + (slot.id - 1);
                    const photo = photos[photoIndex];
                    
                    // Don't render empty slots in the last incomplete pattern
                    if (!photo) return null;

                    const aspectRatio = getAspectRatioValue(slot.aspect_ratio);
                    
                    return (
                      <div
                        key={`${patternIndex}-${slot.id}`}
                        style={{
                          flex: `${slot.width}`,
                          aspectRatio: aspectRatio
                        }}
                        className="relative overflow-hidden rounded-lg bg-gray-100 group cursor-pointer"
                        onClick={() => onPhotoClick?.(photo, photoIndex)}
                      >
                        <img
                          src={photo.medium_url || photo.url}
                          alt={photo.title || `Photo ${photoIndex + 1}`}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                          loading="lazy"
                          onLoad={() => {
                            setLoadedImages(prev => new Set(prev).add(photo.id));
                          }}
                        />
                        
                        {/* Photo overlay with actions */}
                        {showActions && (
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                              <div className="flex gap-2">
                                {onFavoriteToggle && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onFavoriteToggle(photo.id);
                                    }}
                                    className={`p-2 rounded-full backdrop-blur-sm transition-colors ${
                                      photo.is_favorite
                                        ? 'bg-red-500 text-white'
                                        : 'bg-white/20 text-white hover:bg-white/30'
                                    }`}
                                  >
                                    <Heart className={`w-4 h-4 ${photo.is_favorite ? 'fill-current' : ''}`} />
                                  </button>
                                )}
                                {onDownload && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onDownload(photo.id);
                                    }}
                                    className="p-2 rounded-full bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 transition-colors"
                                  >
                                    <Download className="w-4 h-4" />
                                  </button>
                                )}
                              </div>
                              {photo.favorites_count !== undefined && photo.favorites_count > 0 && (
                                <div className="px-2 py-1 rounded-full bg-white/20 backdrop-blur-sm text-white text-xs">
                                  {photo.favorites_count} ♥
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Caption for story layouts */}
                        {slot.has_caption && photo.description && (
                          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                            <p className="text-white text-sm">{photo.description}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    );
  };

  // Render absolute-positioned layout (collages - repeats pattern vertically)
  const renderAbsoluteLayout = () => {
    const patternSize = layout.slots.length;
    const completePatterns = Math.floor(photos.length / patternSize);
    const remainingPhotos = photos.length % patternSize;
    const totalPatterns = completePatterns + (remainingPhotos > 0 ? 1 : 0);
    
    return (
      <div className="space-y-4">
        {Array.from({ length: totalPatterns }).map((_, patternIndex) => (
          <div key={patternIndex} className="relative w-full" style={{ paddingBottom: '100%' }}>
            {layout.slots.map((slot) => {
              const photoIndex = patternIndex * patternSize + (slot.id - 1);
              const photo = photos[photoIndex];
              if (!photo) return null;

              return (
                <div
                  key={`${patternIndex}-${slot.id}`}
                  style={{
                    position: 'absolute',
                    left: `${slot.x}%`,
                    top: `${slot.y}%`,
                    width: `${slot.width}%`,
                    height: `${slot.height}%`,
                    zIndex: slot.z_index || 1
                  }}
                  className="overflow-hidden rounded-lg shadow-lg bg-gray-100 group cursor-pointer"
                  onClick={() => onPhotoClick?.(photo, photoIndex)}
                >
                  <img
                    src={photo.medium_url || photo.url}
                    alt={photo.title || `Photo ${photoIndex + 1}`}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                  />
                  
                  {/* Photo overlay with actions */}
                  {showActions && (
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                        <div className="flex gap-1">
                          {onFavoriteToggle && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onFavoriteToggle(photo.id);
                              }}
                              className={`p-1.5 rounded-full backdrop-blur-sm transition-colors ${
                                photo.is_favorite
                                  ? 'bg-red-500 text-white'
                                  : 'bg-white/20 text-white hover:bg-white/30'
                              }`}
                            >
                              <Heart className={`w-3 h-3 ${photo.is_favorite ? 'fill-current' : ''}`} />
                            </button>
                          )}
                          {onDownload && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDownload(photo.id);
                              }}
                              className="p-1.5 rounded-full bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 transition-colors"
                            >
                              <Download className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    );
  };

  // Render horizontal scrolling layout (for story carousel - shows all photos)
  const renderHorizontalScrollLayout = () => {
    return (
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-4" style={{ width: 'max-content' }}>
          {photos.map((photo, photoIndex) => {
            // Use slot pattern cyclically for aspect ratios
            const slotIndex = photoIndex % layout.slots.length;
            const slot = layout.slots[slotIndex];
            const aspectRatio = getAspectRatioValue(slot.aspect_ratio);

            return (
              <div
                key={photo.id}
                style={{
                  width: '80vw',
                  maxWidth: '400px',
                  aspectRatio: aspectRatio
                }}
                className="relative overflow-hidden rounded-lg bg-gray-100 group cursor-pointer flex-shrink-0"
                onClick={() => onPhotoClick?.(photo, photoIndex)}
              >
                <img
                  src={photo.medium_url || photo.url}
                  alt={photo.title || `Photo ${photoIndex + 1}`}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
                
                {showActions && (
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                      <div className="flex gap-2">
                        {onFavoriteToggle && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onFavoriteToggle(photo.id);
                            }}
                            className={`p-2 rounded-full backdrop-blur-sm transition-colors ${
                              photo.is_favorite
                                ? 'bg-red-500 text-white'
                                : 'bg-white/20 text-white hover:bg-white/30'
                            }`}
                          >
                            <Heart className={`w-4 h-4 ${photo.is_favorite ? 'fill-current' : ''}`} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Main render logic based on layout type
  if (layout.scroll_mode === 'horizontal') {
    return renderHorizontalScrollLayout();
  }

  if (layout.positioning === 'absolute') {
    return renderAbsoluteLayout();
  }

  return renderGridLayout();
}
