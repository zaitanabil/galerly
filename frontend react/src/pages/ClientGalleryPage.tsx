// Client Gallery View page - Client's view of a specific gallery
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getImageUrl } from '../config/env';
import * as clientService from '../services/clientService';
import analyticsService from '../services/analyticsService';
import { Photo, Comment } from '../services/photoService';
import {
  ArrowLeft,
  Download,
  Heart,
  MessageCircle,
  X,
  MessageSquare,
  Share2,
  Pencil,
} from 'lucide-react';
import FeedbackModal from '../components/FeedbackModal';
import ShareModal from '../components/ShareModal';
import CommentSection from '../components/CommentSection';
  import ProgressiveImage from '../components/ProgressiveImage';
  import VideoPlayer from '../components/VideoPlayer';
  import { useSlideshow } from '../hooks/useSlideshow';
  import { useSwipe } from '../hooks/useSwipe';

  interface ClientGallery extends clientService.ClientGallery {
  photographer_name?: string;
  hide_branding?: boolean;
  allow_downloads?: boolean;
  allow_comments?: boolean;
  allow_edits?: boolean;
  settings?: {
    download_enabled?: boolean;
    comments_enabled?: boolean;
    favorites_enabled?: boolean;
    edits_enabled?: boolean;
  };
}

import ExpirationBanner from '../components/ExpirationBanner';

export default function ClientGalleryPage() {
  const { galleryId } = useParams<{ galleryId: string }>();
  const { user, isAuthenticated } = useAuth();
  const [gallery, setGallery] = useState<ClientGallery | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [pagination, setPagination] = useState<{ has_more: boolean; next_key?: unknown }>({ has_more: false });
  const [error, setError] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(true);
  const [showMobileComments, setShowMobileComments] = useState(false);
  
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [sharePhotoId, setSharePhotoId] = useState<string | undefined>(undefined);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);

  const [lastScrollTime, setLastScrollTime] = useState(0);

  const [slideDirection, setSlideDirection] = useState<'up' | 'down' | null>(null);
  const [lastTap, setLastTap] = useState(0);
  
  // Annotation state
  const [isEditing, setIsEditing] = useState(false);
  const [drawingPoints, setDrawingPoints] = useState<{x: number, y: number}[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const [imgDims, setImgDims] = useState<{width: number, height: number} | null>(null);

  // Reset dims when photo changes
  useEffect(() => {
    setImgDims(null);
  }, [selectedPhoto?.id]);

  // Slideshow
  const navigatePhotoRef = useRef<(dir: number) => void>(() => {});
  const { togglePlay, stop: stopSlideshow } = useSlideshow(
    () => navigatePhotoRef.current(1), 
    3000
  );

  const navigatePhoto = useCallback((direction: number) => {
    if (!selectedPhoto) return;
    const currentIndex = photos.findIndex(p => p.id === selectedPhoto.id);
    if (currentIndex === -1) return;

    let newIndex = currentIndex + direction;
    if (newIndex < 0) newIndex = photos.length - 1;
    if (newIndex >= photos.length) newIndex = 0;

    setSlideDirection(direction > 0 ? 'up' : 'down');
    setSelectedPhoto(photos[newIndex]);
  }, [selectedPhoto, photos]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    const now = Date.now();
    if (now - lastScrollTime < 300) return; // Debounce 300ms

    if (e.deltaY > 50) {
        navigatePhoto(1);
        setLastScrollTime(now);
    } else if (e.deltaY < -50) {
        navigatePhoto(-1);
        setLastScrollTime(now);
    }
  }, [lastScrollTime, navigatePhoto]);

  const swipeHandlers = useSwipe({
    onSwipedUp: () => navigatePhoto(1), // Swipe content up -> Next
    onSwipedDown: () => navigatePhoto(-1), // Swipe content down -> Prev
    onSwipedLeft: () => {}, // Disable horizontal swipe nav
    onSwipedRight: () => {},
  });

  // Update ref for slideshow
  useEffect(() => {
    navigatePhotoRef.current = navigatePhoto;
  }, [navigatePhoto]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedPhoto) return;
      
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        return;
      }

      if (e.key === 'Escape') {
        setSelectedPhoto(null);
        stopSlideshow();
      }
      if (e.key === 'ArrowUp') {
        navigatePhoto(-1);
        stopSlideshow();
      }
      if (e.key === 'ArrowDown') {
        navigatePhoto(1);
        stopSlideshow();
      }
      if (e.key === ' ') {
        e.preventDefault();
        togglePlay();
      }
      // Toggle controls with Enter or something? No, keep simple.
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPhoto, navigatePhoto, stopSlideshow, togglePlay]);

  // Image preloading
  useEffect(() => {
    if (selectedPhoto && photos.length > 0) {
      const currentIndex = photos.findIndex(p => p.id === selectedPhoto.id);
      if (currentIndex === -1) return;

      const preloadImages = [
        photos[(currentIndex + 1) % photos.length],
        photos[(currentIndex + 2) % photos.length],
        photos[(currentIndex - 1 + photos.length) % photos.length],
      ];

      preloadImages.forEach(photo => {
        if (photo) {
          const img = new Image();
          img.src = getImageUrl(photo.medium_url || photo.url);
        }
      });
    }
  }, [selectedPhoto, photos]);

  const loadGallery = useCallback(async (loadMore = false) => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const targetGalleryId = galleryId; // Use local var to avoid closure staleness issues with token fallback

    if (!targetGalleryId && !token) return;
    
    // Prevent concurrent loads
    if (loadMore && (!pagination.has_more || loadingMore)) return;
    
    if (loadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setError(null);
    }

    try {
      const params: { page_size: number; last_key?: unknown; token?: string } = { page_size: 50 };
      if (loadMore && pagination.next_key) {
        params.last_key = pagination.next_key;
      }
      
      let response;
      if (token && !targetGalleryId) {
         response = await clientService.getClientGalleryByToken(token, params);
      } else {
         if (token) params.token = token;
         response = await clientService.getClientGallery(targetGalleryId!, params);
      }

      if (response.success && response.data) {
        if (loadMore) {
          const newPhotos = (response.data?.photos || []).map(p => ({
            ...p,
            favorites_count: Math.max(0, p.favorites_count || 0), // Ensure no negative counts
            comments_count: p.comments?.length || 0
          }));
          setPhotos(prev => [...prev, ...newPhotos]);
        } else {
          setGallery(response.data);
          const photosWithCounts = (response.data.photos || []).map(p => ({
            ...p,
            favorites_count: Math.max(0, p.favorites_count || 0), // Ensure no negative counts from backend
            comments_count: p.comments?.length || 0
          }));
          setPhotos(photosWithCounts);
        }
        
        // Update pagination
        if (response.data.pagination) {
          setPagination({
            has_more: response.data.pagination.has_more,
            next_key: response.data.pagination.next_key
          });
        } else {
          setPagination({ has_more: false });
        }
      } else {
        if (!loadMore) setError(response.error || 'Failed to load gallery');
      }
    } catch (err) {
      if (!loadMore) setError('An error occurred while loading the gallery');
      console.error(err);
    } finally {
      if (loadMore) {
        setLoadingMore(false);
      } else {
        setLoading(false);
      }
    }
  }, [galleryId, pagination.has_more, pagination.next_key, loadingMore]);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    if (galleryId || token) {
      loadGallery();
    }
  }, [galleryId, loadGallery]);

  const handleToggleFavorite = async (photoId: string) => {
    const targetGalleryId = galleryId || gallery?.id;
    if (!targetGalleryId) return;

    // Optimistic update
    const photoToUpdate = photos.find(p => p.id === photoId);
    if (!photoToUpdate) return;
    
    const wasFavorite = photoToUpdate.is_favorite;
    const newIsFavorite = !wasFavorite;
    
    // Update local state immediately
    const updatePhotoState = (p: Photo) => {
      if (p.id !== photoId) return p;
      return {
        ...p,
        is_favorite: newIsFavorite,
        favorites_count: Math.max(0, (p.favorites_count || 0) + (newIsFavorite ? 1 : -1))
      };
    };

    setPhotos(photos.map(updatePhotoState));
    if (selectedPhoto?.id === photoId) {
      setSelectedPhoto(updatePhotoState(selectedPhoto));
    }

    try {
      // Use logged-in user's email if available, otherwise check guest email
      let emailToUse = user?.email || localStorage.getItem('guest_email') || undefined;
      
      // If we don't have auth AND don't have a guest email, we MUST prompt
      if (!isAuthenticated && !emailToUse) {
          const email = prompt("Please enter your email to save favorites:");
          if (!email) {
              // User cancelled - revert UI
              const revertPhotoState = (p: Photo) => {
                if (p.id !== photoId) return p;
                return {
                  ...p,
                  is_favorite: wasFavorite, 
                  favorites_count: (p.favorites_count || 0)
                };
              };
              setPhotos(photos.map(revertPhotoState));
              if (selectedPhoto?.id === photoId) {
                setSelectedPhoto(revertPhotoState(selectedPhoto));
              }
              return;
          }
          localStorage.setItem('guest_email', email);
          emailToUse = email;
      }

      if (wasFavorite) {
        await clientService.removeFavorite(photoId, emailToUse);
      } else {
        await clientService.addFavorite(photoId, targetGalleryId, emailToUse);
      }
    } catch (error: unknown) {
      // If error suggests missing email/auth (400 or 401), and we haven't prompted yet (e.g. expired session case)
      // We should prompt and retry. 
      // Implementing retry here is complex, so we'll just alert and clear "auth" assumptions for next time?
      // Or just prompt now and tell them to try again.
      
      console.error("Error toggling favorite:", error);
      
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isAuthError = errorMessage.includes('401') || errorMessage.includes('Unauthorized') || 
                          errorMessage.includes('User email not found') || errorMessage.includes('400');

      if (isAuthError) {
          // It's an auth/email issue. 
          const email = prompt("Session expired or email required. Please enter your email to save favorites:");
          if (email) {
              localStorage.setItem('guest_email', email);
              // Retry immediately?
              try {
                  if (wasFavorite) {
                    await clientService.removeFavorite(photoId, email);
                  } else {
                    await clientService.addFavorite(photoId, targetGalleryId, email);
                  }
                  // Success on retry! Don't revert.
                  return; 
              } catch (retryError) {
                  console.error("Retry failed:", retryError);
                  alert("Failed to save favorite. Please try refreshing the page.");
              }
          }
      }

      // Revert on error (if not recovered)
      const revertPhotoState = (p: Photo) => {
        if (p.id !== photoId) return p;
        return {
          ...p,
          is_favorite: wasFavorite, // revert to old
          favorites_count: Math.max(0, (p.favorites_count || 0)) // revert count
        };
      };
      setPhotos(photos.map(revertPhotoState));
      if (selectedPhoto?.id === photoId) {
        setSelectedPhoto(revertPhotoState(selectedPhoto));
      }
    }
  };

  const handleCommentsChange = (newComments: Comment[]) => {
    if (!selectedPhoto) return;
    
    // Update local state for immediate feedback
    const updatePhotoWithComments = (p: Photo) => {
      if (p.id !== selectedPhoto.id) return p;
      return {
        ...p,
        comments: newComments,
        comments_count: newComments.length
      };
    };

    setPhotos(photos.map(updatePhotoWithComments));
    setSelectedPhoto(updatePhotoWithComments(selectedPhoto));
  };

  const handleDownload = async (photoId: string) => {
    const photo = photos.find(p => p.id === photoId);
    if (!photo || !galleryId) return;
    
    // Track download
    analyticsService.trackPhotoDownload(photoId, galleryId).catch(console.error);
    
    // Download - prefer original_download_url if available to get the original file (HEIC/RAW/Original JPEG)
    // Fallback to url (which might be a converted JPEG rendition)
    const downloadUrl = photo.original_download_url || photo.url;
    const imageUrl = getImageUrl(downloadUrl);
    
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = photo.filename || `photo-${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading photo:', error);
    }
  };

  const handleDownloadAll = async () => {
    if (!galleryId) return;

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    try {
      let response;
      if (token) {
        response = await clientService.bulkDownloadByToken(token);
      } else {
        response = await clientService.bulkDownload(galleryId);
      }

      if (response.success && response.data?.download_url) {
        // Track bulk download
        const photoCount = response.data.photo_count || photos.length || 0;
        analyticsService.trackBulkDownload(galleryId, photoCount).catch(console.error);

        window.location.href = response.data.download_url;
      } else {
        alert('Download not available or failed to start.');
      }
    } catch (error) {
      console.error('Bulk download error:', error);
    }
  };

  const favoritesCount = photos.filter(p => p.is_favorite).length;

  const handleSubmitSelection = async () => {
    if (!galleryId) return;
    const emailToUse = user?.email || localStorage.getItem('guest_email');
    
    if (!emailToUse) {
        alert("Please select a photo first to identify yourself.");
        return;
    }
    
    if (!confirm(`Are you finished selecting photos? This will notify the photographer of your ${favoritesCount} selections.`)) return;

    try {
      const response = await clientService.submitFavorites(galleryId, emailToUse);
      if (response.success && response.data) {
         alert(`Selection submitted! The photographer has been notified of your ${response.data.count} selected photos.`);
      } else {
         alert("Failed to submit selection.");
      }
    } catch (e) {
      console.error(e);
      alert("Error submitting selection.");
    }
  };

  useEffect(() => {
    if (gallery) {
      document.title = `${gallery.name} | ${gallery.photographer_name || 'Galerly'}`;
    }
    return () => {
      document.title = 'Galerly - Professional Photo Galleries';
    };
  }, [gallery]);

  // Safety check for settings - Default to true if undefined
  // Backend provides allow_downloads/allow_comments at root
  const settings = {
    download_enabled: gallery?.allow_downloads ?? gallery?.settings?.download_enabled ?? true,
    comments_enabled: gallery?.allow_comments ?? gallery?.settings?.comments_enabled ?? true,
    edits_enabled: gallery?.allow_edits ?? gallery?.settings?.edits_enabled ?? true,
    favorites_enabled: gallery?.settings?.favorites_enabled ?? true
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[#1D1D1F]/60">Loading gallery...</p>
        </div>
      </div>
    );
  }

  if (error || !gallery) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-[#1D1D1F]/60">{error || 'Gallery not found'}</p>
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
              {isAuthenticated && user?.role === 'client' && (
                <Link
                  to="/client-dashboard"
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  title="Back to Dashboard"
                >
                  <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
                </Link>
              )}
            <div>
              <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                {gallery.name}
              </h1>
              <p className="text-sm text-[#1D1D1F]/60">
                by {gallery.photographer_name || 'Photographer'}
              </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
            {settings.favorites_enabled && favoritesCount > 0 && (
                <button
                onClick={handleSubmitSelection}
                className="px-4 py-2 bg-green-600 text-white rounded-full text-sm font-medium hover:bg-green-700 transition-all flex items-center gap-2 shadow-sm"
                >
                <Heart className="w-4 h-4 fill-white" />
                Submit Selection ({favoritesCount})
                </button>
            )}
            {settings.download_enabled && (
              <button
                onClick={handleDownloadAll}
                className="px-4 py-2 bg-[#0066CC] text-white rounded-full text-sm font-medium hover:bg-[#0052A3] transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20"
              >
                <Download className="w-4 h-4" />
                Download All
              </button>
            )}
            <button
              onClick={() => {
                setSharePhotoId(undefined);
                setShareModalOpen(true);
              }}
              className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
            >
              <Share2 className="w-4 h-4" />
              Share
            </button>
            <button
              onClick={() => setFeedbackModalOpen(true)}
              className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              Feedback
            </button>
            </div>
          </div>
        </div>
      </header>

      {/* Expiration Banner */}
      <ExpirationBanner 
        expiryDate={gallery.expiry_date} 
        archived={gallery.status === 'archived'} 
      />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {gallery.description && (
          <div className="glass-panel p-6 mb-8">
            <p className="text-[#1D1D1F]/70 break-words whitespace-pre-wrap">{gallery.description}</p>
          </div>
        )}

        {/* Photos Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {photos.map((photo) => (
            <div
              key={photo.id}
              className="relative aspect-square bg-gray-100 rounded-2xl overflow-hidden group cursor-pointer"
              onClick={() => setSelectedPhoto(photo)}
            >
              <ProgressiveImage
                src={getImageUrl(photo.thumbnail_url || photo.url)}
                placeholderSrc={getImageUrl(photo.thumbnail_url || photo.url)} // Could add low-res param
                alt=""
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              {/* Actions - Top Right */}
              <div className="absolute top-3 right-3 z-30 flex items-center gap-3">
                {/* Edit Request Indicator */}
                {photo.comments?.some(c => c.annotation) && (
                  <div className="relative group/edit" title="Edit Requested">
                    <div className="absolute inset-0 bg-yellow-500 blur-sm opacity-50 rounded-full"></div>
                    <div className="relative w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center shadow-lg transform transition-transform group-hover/edit:scale-110">
                      <Pencil className="w-4 h-4 text-white" />
                    </div>
                  </div>
                )}
                
                {/* Favorite Indicator */}
                  {settings.favorites_enabled && (
                    <button
                    onClick={(e) => { e.stopPropagation(); handleToggleFavorite(photo.id); }}
                    className={`transform transition-all duration-200 hover:scale-110 ${
                      photo.is_favorite ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                    }`}
                    >
                      <Heart
                      className={`w-7 h-7 drop-shadow-lg ${
                        photo.is_favorite 
                        ? 'fill-red-500 text-red-500' 
                        : 'text-white hover:text-red-200'
                      }`} 
                      strokeWidth={1.5}
                    />
                    </button>
                  )}
              </div>
              
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                <div className="absolute bottom-0 left-0 right-0 p-4 flex items-end justify-between">
                   {/* Left: Spacer */}
                   <div></div>

                   {/* Right: Stats */}
                   <div className="flex items-center gap-4">
                      {/* Favorites count */}
                      {settings.favorites_enabled && (photo.favorites_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <Heart className="w-4 h-4 text-white drop-shadow-md" />
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.favorites_count}</span>
                    </div>
                  )}
                      {/* Comments count */}
                      {settings.comments_enabled && (photo.comments_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <MessageCircle className="w-4 h-4 text-white drop-shadow-md" />
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.comments_count}</span>
                        </div>
                      )}
                   </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Load More Button */}
        {photos.length > 0 && pagination.has_more && (
          <div className="mt-8 flex justify-center">
            <button
              onClick={() => loadGallery(true)}
              disabled={loadingMore}
              className="px-6 py-3 bg-white border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-gray-50 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loadingMore ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#1D1D1F] border-t-transparent rounded-full animate-spin" />
                  Loading...
                </>
              ) : (
                'Load More Photos'
              )}
            </button>
          </div>
        )}

        {/* Branding (for Free/Starter plans) */}
        {!gallery.hide_branding && (
          <div className="mt-16 pb-8 text-center">
            <a 
              href="https://galerly.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white/50 backdrop-blur-sm rounded-full text-[10px] uppercase tracking-widest font-medium text-[#1D1D1F]/40 hover:text-[#1D1D1F] hover:bg-white transition-all border border-gray-200/50"
            >
              Powered by <span className="font-bold text-[#1D1D1F]">Galerly</span>
            </a>
          </div>
        )}
      </main>

      {/* Lightbox Modal */}
      {selectedPhoto && (
        <div 
          className="fixed inset-0 bg-black z-[9999] flex items-center justify-center overflow-hidden"
          {...swipeHandlers}
          onWheel={handleWheel}
          onClick={() => setShowControls(prev => !prev)}
        >
          {/* Top Bar (Gradient Overlay) */}
          <div 
            className={`absolute top-0 left-0 right-0 p-6 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent z-[1000] transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSelectedPhoto(null)}
                className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-full backdrop-blur-md transition-colors border border-white/10"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
              <span className="text-white/90 font-medium text-sm tracking-wide bg-black/30 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
                {photos.findIndex(p => p.id === selectedPhoto.id) + 1} / {photos.length}
              </span>
            </div>
            
             {/* Desktop Actions - REMOVED for TikTok Style */}
             <div className="hidden lg:flex items-center gap-3 opacity-0 pointer-events-none">
             </div>
          </div>

          {/* Navigation Buttons - REMOVED for TikTok Style (Scroll/Swipe only) */}
          
          {/* Main Layout Container */}
          <div 
             className="w-full h-[100dvh] flex flex-col items-center justify-center relative overflow-hidden touch-none" 
             style={{ overscrollBehavior: 'none' }}
             onClick={() => {
                // Handle single tap for controls, but allow double tap for like
                // We rely on standard click here, double click handled separately on image
                const now = Date.now();
                if (now - lastTap < 300) {
                    if (selectedPhoto) handleToggleFavorite(selectedPhoto.id);
                } else {
                    setShowControls(prev => !prev);
                }
                setLastTap(now);
             }}
          >
             <style>{`
                @keyframes slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                @keyframes slideDown { from { transform: translateY(-100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                .animate-slide-up { animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
                .animate-slide-down { animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
             `}</style>

             {/* Blurred Background */}
             <div className="absolute inset-0 z-0">
                <ProgressiveImage
                  key={`blur-${selectedPhoto.id}`}
                  src={getImageUrl(selectedPhoto.thumbnail_url || selectedPhoto.url)}
                  placeholderSrc=""
                  alt=""
                  className="w-full h-full object-cover blur-2xl opacity-40 scale-110 transition-opacity duration-500" 
                />
                <div className="absolute inset-0 bg-black/20" />
             </div>

             {/* Image/Video Area */}
             <div 
                ref={imageContainerRef}
                className={`relative z-10 max-w-full max-h-full flex items-center justify-center ${isEditing ? 'cursor-crosshair touch-none' : 'cursor-pointer'} ${slideDirection === 'up' ? 'animate-slide-up' : slideDirection === 'down' ? 'animate-slide-down' : ''}`}
                style={{ 
                    width: (selectedPhoto.width || imgDims?.width) ? 'auto' : '100%', 
                    height: (selectedPhoto.height || imgDims?.height) ? 'auto' : '100%',
                    aspectRatio: (selectedPhoto.width && selectedPhoto.height) 
                        ? `${selectedPhoto.width} / ${selectedPhoto.height}` 
                        : (imgDims ? `${imgDims.width} / ${imgDims.height}` : undefined)
                }}
                key={selectedPhoto.id}
                onPointerDown={(e) => {
                    if (!isEditing) return;
                    e.preventDefault();
                    e.stopPropagation();
                        const rect = e.currentTarget.getBoundingClientRect();
                        const x = (e.clientX - rect.left) / rect.width * 100;
                        const y = (e.clientY - rect.top) / rect.height * 100;
                    setDrawingPoints([{ x, y }]);
                    setIsDrawing(true);
                }}
                onPointerMove={(e) => {
                    if (!isEditing || !isDrawing) return;
                    e.preventDefault();
                    e.stopPropagation();
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = (e.clientX - rect.left) / rect.width * 100;
                    const y = (e.clientY - rect.top) / rect.height * 100;
                    setDrawingPoints(prev => [...prev, { x, y }]);
                }}
                onPointerUp={(e) => {
                    if (!isEditing || !isDrawing) return;
                    e.preventDefault();
                    e.stopPropagation();
                    setIsDrawing(false);
                    // Open feedback modal with the shape
                        setFeedbackModalOpen(true);
                    setIsEditing(false); // Exit edit mode
                }}
                onPointerLeave={() => {
                    if (isDrawing) {
                        setIsDrawing(false);
                        setFeedbackModalOpen(true);
                        setIsEditing(false);
                    }
                }}
                onClick={(e) => {
                    if (isEditing) return; // Handled by pointer events
                    e.stopPropagation();
                    const now = Date.now();
                    if (now - lastTap < 300) {
                        handleToggleFavorite(selectedPhoto.id);
                    } else {
                        setShowControls(prev => !prev);
                    }
                    setLastTap(now);
                }}
             >
              {selectedPhoto.type === 'video' ? (
                  <VideoPlayer
                    options={{
                        autoplay: true,
                        controls: true,
                        responsive: true,
                        fluid: true,
                        sources: [{
                            src: selectedPhoto.hls_url || selectedPhoto.url,
                            type: selectedPhoto.hls_url ? 'application/x-mpegURL' : 'video/mp4'
                        }]
                    }}
                    className="w-full h-full max-h-[100vh] max-w-[100vw]"
                  />
              ) : (
              <ProgressiveImage
                src={getImageUrl(selectedPhoto.medium_url || selectedPhoto.url)}
                placeholderSrc={getImageUrl(selectedPhoto.thumbnail_url || selectedPhoto.url)}
                alt=""
                className="max-w-full max-h-full object-contain shadow-2xl drop-shadow-2xl select-none pointer-events-none"
                onLoad={(e) => {
                    const img = e.currentTarget;
                    if (img.naturalWidth && img.naturalHeight) {
                        setImgDims({ width: img.naturalWidth, height: img.naturalHeight });
                    }
                }}
              />
              )}
              
              {/* Render Drawing Path */}
              {selectedPhoto.type !== 'video' && drawingPoints.length > 0 && (
                  <svg 
                    className="absolute inset-0 w-full h-full pointer-events-none z-50"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                  >
                      <path 
                        d={`M ${drawingPoints.map(p => `${p.x} ${p.y}`).join(' L ')} ${!isDrawing ? 'Z' : ''}`}
                        fill="rgba(181, 137, 0, 0.5)" 
                        stroke="#B58900" 
                        strokeWidth="2"
                        vectorEffect="non-scaling-stroke"
                        strokeLinejoin="round"
                        strokeLinecap="round"
                      />
                  </svg>
              )}

              {/* Render Saved Annotations from Comments */}
              {!isEditing && selectedPhoto.comments?.map((comment) => {
                  if (!comment.annotation) return null;
                  try {
                      const points = JSON.parse(comment.annotation);
                      if (!Array.isArray(points) || points.length === 0) return null;
                      
                      return (
                          <svg 
                            key={`annotation-${comment.id}`}
                            className="absolute inset-0 w-full h-full pointer-events-none z-40"
                            viewBox="0 0 100 100"
                            preserveAspectRatio="none"
                          >
                              <path 
                                d={`M ${points.map((p: {x: number; y: number}) => `${p.x} ${p.y}`).join(' L ')} Z`}
                                fill="rgba(181, 137, 0, 0.5)" 
                                stroke="#B58900" 
                                strokeWidth="2"
                                vectorEffect="non-scaling-stroke"
                                strokeLinejoin="round"
                                strokeLinecap="round"
                              />
                          </svg>
                      );
                  } catch {
                      return null;
                  }
              })}
            </div>
          </div>

           {/* Edit Mode Overlay Instruction */}
           {isEditing && (
                <div className="absolute top-20 left-0 right-0 z-[2000] flex justify-center pointer-events-none">
                    <div className="bg-black/70 backdrop-blur-md text-white px-6 py-3 rounded-full text-sm font-medium animate-pulse border border-white/20 text-center">
                        Draw a lasso around the area to modify<br/>
                        <span className="text-xs text-white/70">(Release to finish)</span>
                    </div>
                </div>
           )}

           {/* Bottom Left Text Overlay (TikTok Style) */}
           <div 
              className={`absolute bottom-4 left-4 right-20 z-[1000] transition-all duration-300 transform text-left ${showControls ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}
              onClick={(e) => e.stopPropagation()}
           >
              <h3 className="text-white font-medium text-lg drop-shadow-md truncate w-full mb-1">
                {gallery?.photographer_name || 'Photographer'}
              </h3>
              <p className="text-white/90 text-sm drop-shadow-md line-clamp-2">
                {selectedPhoto.filename}
              </p>
           </div>

           {/* Mobile Comments Sheet (Updated to Bottom-up Sheet) */}
          <div 
            className={`absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl transition-transform duration-300 z-[3000] flex flex-col h-[60%] ${showMobileComments ? 'translate-y-0' : 'translate-y-[120%]'}`}
            onClick={(e) => e.stopPropagation()}
          >
             <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h3 className="font-medium text-[#1D1D1F]">Comments</h3>
                <button onClick={() => setShowMobileComments(false)} className="p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors">
                    <X className="w-5 h-5 text-[#1D1D1F]" />
                </button>
             </div>
             <div className="flex-1 overflow-y-auto p-4">
                <CommentSection
                  photoId={selectedPhoto.id}
                  comments={selectedPhoto.comments || []}
                  onCommentsChange={handleCommentsChange}
                  allowComments={settings.comments_enabled || false}
                  isGalleryOwner={false}
                />
             </div>
          </div>


          {/* Right Side Vertical Stack (TikTok Style - Universal) */}
          <div 
             className={`absolute bottom-40 right-4 z-[2000] transition-all duration-300 transform ${showControls ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8 pointer-events-none'}`}
             onClick={(e) => e.stopPropagation()}
          >
              <div className="flex flex-col items-center gap-6">
                  {/* Play/Pause - Removed for cleaner TikTok UI */}
                  {/* <div className="flex flex-col items-center gap-1">
                    <button 
                       onClick={togglePlay}
                       className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">
                        {isPlaying ? 'Pause' : 'Play'}
                    </span>
                  </div> */}
                  
                  {/* Favorite (Mobile/Tablet) */}
                  {/* Always show Like button per user request */}
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={() => handleToggleFavorite(selectedPhoto.id)}
                        className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        <Heart className={`w-6 h-6 text-white ${selectedPhoto.is_favorite ? 'fill-red-500 text-red-500' : ''}`} />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">
                        {selectedPhoto.favorites_count || 0}
                    </span>
                  </div>

                  {/* Comments Trigger (Mobile/Tablet) */}
                   {settings.comments_enabled && (
                      <div className="flex flex-col items-center gap-1">
                        <button 
                            onClick={(e) => { e.stopPropagation(); setShowMobileComments(true); }}
                            className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform relative"
                        >
                            <MessageCircle className="w-6 h-6" />
                        </button>
                        <span className="text-white text-xs font-medium drop-shadow-md">
                            {selectedPhoto.comments_count || 0}
                        </span>
                      </div>
                  )}

                  {/* Feedback / Edit */}
                  {settings.edits_enabled && (
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={() => {
                            if (drawingPoints.length > 0) {
                                // If drawing exists, just open modal
                                setFeedbackModalOpen(true);
                            } else {
                                // Start editing mode
                                setIsEditing(true);
                                setShowControls(false); // Hide controls to see photo clearly
                            }
                        }}
                        className={`p-3 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform ${isEditing ? 'bg-yellow-500' : 'bg-black/40'}`}
                    >
                        <Pencil className="w-7 h-7" />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">{isEditing ? 'Cancel' : 'Edit'}</span>
                  </div>
                  )}

                  {/* Share (Mobile/Tablet) */}
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={() => { setSharePhotoId(selectedPhoto.id); setShareModalOpen(true); }}
                        className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        <Share2 className="w-6 h-6" />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">Share</span>
                  </div>

                  {settings.download_enabled && (
                    <div className="flex flex-col items-center gap-1">
                      <button 
                          onClick={() => handleDownload(selectedPhoto.id)}
                          className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                      >
                          <Download className="w-6 h-6" />
                      </button>
                      <span className="text-white text-xs font-medium drop-shadow-md">Save</span>
                    </div>
                 )}
              </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={feedbackModalOpen}
        onClose={() => {
            setFeedbackModalOpen(false);
            setDrawingPoints([]); // Clear drawing on close
        }}
        galleryId={galleryId || ''}
        photoId={drawingPoints.length > 0 ? selectedPhoto?.id : undefined}
        annotation={drawingPoints.length > 0 ? JSON.stringify(drawingPoints) : undefined}
        initialComment={drawingPoints.length > 0 ? '' : ''}
        onCommentAdded={(newComment) => {
            handleCommentsChange([...(selectedPhoto?.comments || []), newComment]);
        }}
      />

      {/* Share Modal */}
      <ShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        galleryId={galleryId!}
        photoId={sharePhotoId}
        title={gallery?.name}
      />
    </div>
  );
}
