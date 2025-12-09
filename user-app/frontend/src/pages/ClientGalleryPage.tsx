import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getImageUrl } from '../config/env';
import * as clientService from '../services/clientService';
import analyticsService from '../services/analyticsService';
import { Photo, Comment } from '../services/photoService';
import { useBrandedModal } from '../components/BrandedModal';
import { useViewerTracking } from '../hooks/useViewerTracking';
import {
  ArrowLeft,
  Download,
  Heart,
  MessageCircle,
  X,
  MessageSquare,
  Share2,
  Pencil,
  PlayCircle,
} from 'lucide-react';
import FeedbackModal from '../components/FeedbackModal';
import ShareModal from '../components/ShareModal';
import CommentSection from '../components/CommentSection';
  import ProgressiveImage from '../components/ProgressiveImage';
  import GalleryLayoutRenderer from '../components/GalleryLayoutRenderer';
  import { useSlideshow } from '../hooks/useSlideshow';
  import { useSwipe } from '../hooks/useSwipe';

  interface ClientGallery extends clientService.ClientGallery {
  photographer_name?: string;
  hide_branding?: boolean;
  allow_downloads?: boolean;
  allow_comments?: boolean;
  allow_edits?: boolean;
  layout_id?: string;  // Added for gallery layouts
  settings?: {
    download_enabled?: boolean;
    comments_enabled?: boolean;
    favorites_enabled?: boolean;
    edits_enabled?: boolean;
  };
}

export default function ClientGalleryPage() {
  const { galleryId } = useParams<{ galleryId: string }>();
  const { user, isAuthenticated } = useAuth();
  const { showAlert, showConfirm, showPrompt, ModalComponent } = useBrandedModal();
  
  const [gallery, setGallery] = useState<ClientGallery | null>(null);
  
  // Gallery layout state
  const [galleryLayout, setGalleryLayout] = useState<any>(null);
  
  // Track viewer presence for real-time globe
  useViewerTracking({
    gallery_id: galleryId,
    page_type: 'client_gallery',
    gallery_name: gallery?.name || 'Gallery',
    enabled: !!galleryId
  });
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
  
  // Video playback state (TikTok-style)
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [videoProgress, setVideoProgress] = useState(0);
  const [videoTimestamp, setVideoTimestamp] = useState<number | null>(null); // For timestamp comments
  const [showTimestampCapture, setShowTimestampCapture] = useState(false); // Visual feedback for timestamp capture
  
  // Engagement tracking state
  const viewStartTime = useRef<Record<string, number>>({}); // Track start time per photo ID
  const sessionStartTime = useRef<number>(Date.now());
  const hasTrackedView = useRef<Set<string>>(new Set());
  
  // Annotation state (only for images, not videos)
  const [isEditing, setIsEditing] = useState(false);
  const [drawingPoints, setDrawingPoints] = useState<{x: number, y: number}[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const [imgDims, setImgDims] = useState<{width: number, height: number} | null>(null);

  // Reset dims and annotation state when photo changes
  useEffect(() => {
    setImgDims(null);
    setDrawingPoints([]);
    setIsEditing(false);
    setVideoTimestamp(null);
  }, [selectedPhoto?.id]);

  // Track engagement when viewing a photo/video
  useEffect(() => {
    // Use galleryId from params or from loaded gallery object
    const targetGalleryId = galleryId || gallery?.id;
    if (!selectedPhoto || !targetGalleryId) return;

    const photoId = selectedPhoto.id;
    
    // Track view start time for this specific photo
    viewStartTime.current[photoId] = Date.now();

    // Track initial view (once per photo per session)
    if (!hasTrackedView.current.has(photoId)) {
      hasTrackedView.current.add(photoId);

      if (selectedPhoto.type === 'video') {
        analyticsService.trackVideoEngagement(
          targetGalleryId,
          photoId,
          'play',
          0,
          (Date.now() - sessionStartTime.current) / 1000
        );
      } else {
        analyticsService.trackPhotoEngagement(
          targetGalleryId,
          photoId,
          'view',
          0
        );
      }
    }
    
    // Track time spent when leaving
    return () => {
      const startTime = viewStartTime.current[photoId] || Date.now();
      const duration = (Date.now() - startTime) / 1000; // seconds
      
      if (selectedPhoto.type === 'video') {
        // Track video completion or partial view
        const eventType = duration > 0 ? 'pause' : 'complete';
        analyticsService.trackVideoEngagement(
          targetGalleryId,
          photoId,
          eventType,
          videoRef.current?.currentTime || 0,
          (Date.now() - sessionStartTime.current) / 1000
        );
      } else if (duration > 0.5) { // Only track if viewed for more than 0.5s
        analyticsService.trackPhotoEngagement(
          targetGalleryId,
          photoId,
          'view',
          duration
        );
      }
    };
  }, [selectedPhoto?.id, galleryId, gallery?.id, selectedPhoto?.type]);

  // Slideshow
  const navigatePhotoRef = useRef<(dir: number) => void>(() => {});
  const { stop: stopSlideshow } = useSlideshow(
    () => navigatePhotoRef.current(1), 
    Number(import.meta.env.VITE_SLIDESHOW_INTERVAL) || 3000
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

  // Toggle video play/pause (TikTok style)
  const toggleVideoPlayback = useCallback(() => {
    if (videoRef.current) {
      if (isVideoPlaying) {
        videoRef.current.pause();
        setIsVideoPlaying(false);
      } else {
        videoRef.current.play()
          .then(() => setIsVideoPlaying(true))
          .catch(() => {}); // Silently handle autoplay prevention
      }
    }
  }, [isVideoPlaying]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    const now = Date.now();
    const debounceDelay = Number(import.meta.env.VITE_SCROLL_DEBOUNCE_DELAY) || 300;
    if (now - lastScrollTime < debounceDelay) return;

    const scrollThreshold = Number(import.meta.env.VITE_SCROLL_THRESHOLD) || 50;
    if (e.deltaY > scrollThreshold) {
        navigatePhoto(1);
        setLastScrollTime(now);
    } else if (e.deltaY < -scrollThreshold) {
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

  // Auto-play videos when modal opens or photo changes (TikTok style)
  useEffect(() => {
    if (selectedPhoto && selectedPhoto.type === 'video' && videoRef.current) {
      setVideoProgress(0);
      videoRef.current.currentTime = 0; // Reset to beginning
      
      const autoplayDelay = Number(import.meta.env.VITE_VIDEO_AUTOPLAY_DELAY) || 300;
      const timer = setTimeout(() => {
        if (videoRef.current && selectedPhoto.type === 'video') {
          videoRef.current.play()
            .then(() => setIsVideoPlaying(true))
            .catch(() => setIsVideoPlaying(false)); // Handle autoplay prevention
        }
      }, autoplayDelay);
      return () => clearTimeout(timer);
    } else if (videoRef.current) {
      videoRef.current.pause();
      setIsVideoPlaying(false);
      setVideoProgress(0);
    }
  }, [selectedPhoto?.id, selectedPhoto?.type]); // Stable dependencies to prevent re-runs

  // Update progress bar smoothly
  useEffect(() => {
    if (isVideoPlaying && videoRef.current && videoRef.current.duration) {
      const updateProgress = () => {
        if (videoRef.current && videoRef.current.duration) {
          setVideoProgress((videoRef.current.currentTime / videoRef.current.duration) * 100);
        }
      };
      const progressInterval = Number(import.meta.env.VITE_VIDEO_PROGRESS_UPDATE_INTERVAL) || 100;
      const interval = setInterval(updateProgress, progressInterval);
      return () => clearInterval(interval);
    }
  }, [isVideoPlaying]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedPhoto) return;
      
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        return;
      }

      if (e.key === 'Escape') {
        e.preventDefault();
        setSelectedPhoto(null);
        stopSlideshow();
      }
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        navigatePhoto(-1);
        stopSlideshow();
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        navigatePhoto(1);
        stopSlideshow();
      }
      if (e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        // Space for video play/pause
        if (selectedPhoto.type === 'video') {
          toggleVideoPlayback();
      }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPhoto, navigatePhoto, stopSlideshow, toggleVideoPlayback]);

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
          
          // Fetch layout if gallery has a layout_id
          if (response.data.layout_id) {
            try {
              const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
              const layoutResponse = await fetch(`${apiUrl}/v1/gallery-layouts/${response.data.layout_id}`);
              if (layoutResponse.ok) {
                const layoutData = await layoutResponse.json();
                setGalleryLayout(layoutData);
              }
            } catch (err) {
              console.error('Failed to fetch layout:', err);
            }
          } else {
            setGalleryLayout(null);
          }
          
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

    // Get share token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const shareToken = urlParams.get('token') || undefined;

    console.log('DEBUG: handleToggleFavorite called', { 
      photoId, 
      targetGalleryId, 
      shareToken: shareToken ? '***' : 'none',
      isAuthenticated,
      userEmail: user?.email
    });

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

    // Track engagement
    if (targetGalleryId && newIsFavorite) {
      const photo = photos.find(p => p.id === photoId);
      // Calculate duration: if we have a start time for this photo, use it; otherwise default to 0
      const startTime = viewStartTime.current[photoId] || Date.now();
      const duration = (Date.now() - startTime) / 1000;
      
      if (photo?.type === 'video') {
        analyticsService.trackVideoEngagement(targetGalleryId, photoId, 'complete', videoRef.current?.currentTime || 0, (Date.now() - sessionStartTime.current) / 1000);
      } else {
        analyticsService.trackPhotoEngagement(targetGalleryId, photoId, 'favorite', duration);
      }
    }

    try {
      // Use logged-in user's email if available, otherwise check guest email
      let emailToUse = user?.email || localStorage.getItem('guest_email') || undefined;
      let nameToUse = user?.name || localStorage.getItem('guest_name') || undefined;
      
      console.log('DEBUG: Email check', { emailToUse, nameToUse, isAuthenticated });
      
      // If we don't have auth AND don't have a guest email, we MUST prompt
      if (!isAuthenticated && !emailToUse) {
          console.log('DEBUG: Prompting for name...');
          // First ask for name
          const name = await showPrompt(
            'Welcome!',
            'Please enter your name:',
            'John Doe'
          );
          
          console.log('DEBUG: Name received:', name);
          
          if (!name) {
              console.log('DEBUG: User cancelled name prompt');
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
          
          console.log('DEBUG: Prompting for email...');
          // Then ask for email
          const email = await showPrompt(
            'Enter Your Email',
            'Please enter your email to save favorites and receive updates:',
            'your@email.com'
          );
          
          console.log('DEBUG: Email received:', email);
          
          if (!email) {
              console.log('DEBUG: User cancelled email prompt');
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
          
          console.log('DEBUG: Saving guest info to localStorage');
          localStorage.setItem('guest_name', name);
          localStorage.setItem('guest_email', email);
          emailToUse = email;
          nameToUse = name;
      }

      console.log('DEBUG: Proceeding with favorite toggle', { emailToUse, nameToUse });

      if (wasFavorite) {
        console.log('DEBUG: Calling removeFavorite', { photoId, emailToUse });
        await clientService.removeFavorite(photoId, emailToUse);
      } else {
        console.log('DEBUG: Calling addFavorite', { photoId, targetGalleryId, emailToUse, nameToUse, shareToken: shareToken ? '***' : 'none' });
        await clientService.addFavorite(photoId, targetGalleryId, emailToUse, nameToUse, shareToken);
      }
      console.log('DEBUG: Favorite toggle successful');
    } catch (error: unknown) {
      console.error("Error toggling favorite:", error);
      
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isAuthError = errorMessage.includes('401') || errorMessage.includes('Unauthorized') || 
                          errorMessage.includes('User email not found') || errorMessage.includes('400');
      const isAccessDenied = errorMessage.includes('403') || errorMessage.includes('Access denied');

      // Handle access denied (403) - likely plan issue or invalid token
      if (isAccessDenied) {
          await showAlert(
            'Access Denied', 
            'Unable to favorite this photo. This may be due to the gallery owner\'s plan restrictions or an invalid share link. Please contact the photographer.',
            'error'
          );
          // Revert UI
          const revertPhotoState = (p: Photo) => {
            if (p.id !== photoId) return p;
            return {
              ...p,
              is_favorite: wasFavorite,
              favorites_count: Math.max(0, (p.favorites_count || 0))
            };
          };
          setPhotos(photos.map(revertPhotoState));
          if (selectedPhoto?.id === photoId) {
            setSelectedPhoto(revertPhotoState(selectedPhoto));
          }
          return;
      }

      // Handle auth errors (401/400) - retry with email prompt
      if (isAuthError) {
          const email = await showPrompt(
            'Email Required',
            'Please enter your email to save favorites:',
            'your@email.com'
          );
          
          if (email) {
              localStorage.setItem('guest_email', email);
              // Retry immediately
              try {
                  if (wasFavorite) {
                    await clientService.removeFavorite(photoId, email);
                  } else {
                    const nameToUse = localStorage.getItem('guest_name') || undefined;
                    await clientService.addFavorite(photoId, targetGalleryId, email, nameToUse, shareToken);
                  }
                  console.log('DEBUG: Retry successful');
                  // Success on retry! Don't revert.
                  return; 
              } catch (retryError) {
                  console.error("Retry failed:", retryError);
                  await showAlert('Error', 'Failed to save favorite. Please try refreshing the page.', 'error');
              }
          }
      } else {
          // Generic error
          await showAlert('Error', 'An unexpected error occurred. Please try again.', 'error');
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
    const targetGalleryId = galleryId || gallery?.id;
    if (!photo || !targetGalleryId) return;
    
    // Track download engagement
    const startTime = viewStartTime.current[photoId] || Date.now();
    const duration = (Date.now() - startTime) / 1000;
    
    if (photo.type === 'video') {
      analyticsService.trackVideoEngagement(targetGalleryId, photoId, 'download', videoRef.current?.duration || 0, (Date.now() - sessionStartTime.current) / 1000);
    } else {
      analyticsService.trackPhotoEngagement(targetGalleryId, photoId, 'download', duration);
    }
    
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
        window.location.href = response.data.download_url;
      } else {
        await showAlert('Error', 'Download not available or failed to start.', 'error');
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
        await showAlert('Email Required', 'Please select a photo first to identify yourself.', 'error');
        return;
    }
    
    const confirmed = await showConfirm(
      'Submit Selection',
      `Are you finished selecting photos?\n\nThis will notify the photographer of your ${favoritesCount} selections.`,
      'Submit Selection',
      'Keep Selecting'
    );
    
    if (!confirmed) return;

    try {
      const response = await clientService.submitFavorites(galleryId, emailToUse);
      if (response.success && response.data) {
         await showAlert('Success', `Selection submitted!\n\nThe photographer has been notified of your ${response.data.count} selected photos.`, 'success');
      } else {
         await showAlert('Error', 'Failed to submit selection.', 'error');
      }
    } catch (e) {
      console.error(e);
      await showAlert('Error', 'Error submitting selection.', 'error');
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

      <main className="max-w-7xl mx-auto px-6 py-8">
        {gallery.description && (
          <div className="glass-panel p-6 mb-8">
            <p className="text-[#1D1D1F]/70 break-words whitespace-pre-wrap">{gallery.description}</p>
          </div>
        )}

        {/* Photos Grid or Layout */}
        {galleryLayout && photos.length >= galleryLayout.total_slots ? (
          // Use layout renderer if layout is set and enough photos
          <div>
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-center">
              <p className="text-sm text-[#0066CC] font-medium">
                {galleryLayout.name} Layout ({photos.length} photos)
              </p>
            </div>
            <GalleryLayoutRenderer
              layout={galleryLayout}
              photos={photos.map(p => ({
                id: p.id,
                url: getImageUrl(p.url),
                thumbnail_url: getImageUrl(p.thumbnail_url || p.url),
                medium_url: getImageUrl(p.medium_url || p.url),
                is_favorite: p.is_favorite,
                favorites_count: p.favorites_count
              }))}
              onPhotoClick={(photo) => {
                const fullPhoto = photos.find(p => p.id === photo.id);
                if (fullPhoto) setSelectedPhoto(fullPhoto);
              }}
              onFavoriteToggle={handleToggleFavorite}
              showActions={settings.favorites_enabled}
            />
          </div>
        ) : (
          // Default grid view
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">{photos.map((photo) => (
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
              
              {/* Video Play Button Overlay */}
              {photo.type === 'video' && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="bg-black/50 rounded-full p-4 backdrop-blur-sm">
                    <PlayCircle className="w-12 h-12 text-white" strokeWidth={1.5} />
                  </div>
                </div>
              )}
              
              {/* Video Duration Badge */}
              {photo.type === 'video' && photo.duration_seconds && (
                <div className="absolute bottom-3 right-3 bg-black/75 text-white text-xs px-2 py-1 rounded backdrop-blur-sm font-medium">
                  {Math.floor(photo.duration_seconds / 60)}:{String(Math.floor(photo.duration_seconds % 60)).padStart(2, '0')}
                </div>
              )}
              
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
                      {/* Favorites count - showing count only, heart icon is in top-right */}
                      {settings.favorites_enabled && (photo.favorites_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.favorites_count} likes</span>
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
        )}
        
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

        {/* Branding Footer - Show Galerly branding unless hidden by photographer's plan */}
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
                const now = Date.now();
                const doubleTapThreshold = Number(import.meta.env.VITE_DOUBLE_TAP_THRESHOLD) || 300;
                if (now - lastTap < doubleTapThreshold) {
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
                @keyframes fadeInScale { 
                  from { transform: translate(-50%, -50%) scale(0.8); opacity: 0; } 
                  to { transform: translate(-50%, -50%) scale(1); opacity: 1; } 
                }
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
                className={`relative z-10 max-w-full max-h-full flex items-center justify-center ${selectedPhoto.type === 'video' ? '' : isEditing ? 'cursor-crosshair touch-none' : 'cursor-pointer'} ${slideDirection === 'up' ? 'animate-slide-up' : slideDirection === 'down' ? 'animate-slide-down' : ''}`}
                style={{ 
                    width: (selectedPhoto.width || imgDims?.width) ? 'auto' : '100%', 
                    height: (selectedPhoto.height || imgDims?.height) ? 'auto' : '100%',
                    aspectRatio: (selectedPhoto.width && selectedPhoto.height) 
                        ? `${selectedPhoto.width} / ${selectedPhoto.height}` 
                        : (imgDims ? `${imgDims.width} / ${imgDims.height}` : undefined)
                }}
                key={selectedPhoto.id}
                onPointerDown={(e) => {
                    // Only allow lasso for images, not videos
                    if (!isEditing || selectedPhoto.type === 'video') return;
                    e.preventDefault();
                    e.stopPropagation();
                        const rect = e.currentTarget.getBoundingClientRect();
                        const x = (e.clientX - rect.left) / rect.width * 100;
                        const y = (e.clientY - rect.top) / rect.height * 100;
                    setDrawingPoints([{ x, y }]);
                    setIsDrawing(true);
                }}
                onPointerMove={(e) => {
                    if (!isEditing || !isDrawing || selectedPhoto.type === 'video') return;
                    e.preventDefault();
                    e.stopPropagation();
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = (e.clientX - rect.left) / rect.width * 100;
                    const y = (e.clientY - rect.top) / rect.height * 100;
                    setDrawingPoints(prev => [...prev, { x, y }]);
                }}
                onPointerUp={(e) => {
                    if (!isEditing || !isDrawing || selectedPhoto.type === 'video') return;
                    e.preventDefault();
                    e.stopPropagation();
                    setIsDrawing(false);
                    // Open feedback modal with the shape
                        setFeedbackModalOpen(true);
                    setIsEditing(false); // Exit edit mode
                }}
                onPointerLeave={() => {
                    if (isDrawing && selectedPhoto.type !== 'video') {
                        setIsDrawing(false);
                        setFeedbackModalOpen(true);
                        setIsEditing(false);
                    }
                }}
                onClick={(e) => {
                    if (isEditing) return; // Handled by pointer events
                    // For videos, click handling is on video element directly
                    if (selectedPhoto.type === 'video') {
                      return;
                    }
                    
                    e.stopPropagation();
                    const now = Date.now();
                    const doubleTapThreshold = Number(import.meta.env.VITE_DOUBLE_TAP_THRESHOLD) || 300;
                    if (now - lastTap < doubleTapThreshold) {
                        handleToggleFavorite(selectedPhoto.id);
                    } else {
                        setShowControls(prev => !prev);
                    }
                    setLastTap(now);
                }}
             >
              {selectedPhoto.type === 'video' ? (
                /* TikTok-style Video Player - Click to play/pause, auto-play on scroll */
                <div className="relative w-full h-full flex items-center justify-center">
                  <video
                    ref={videoRef}
                    preload="auto"
                    poster={getImageUrl(selectedPhoto.thumbnail_url || '')}
                    className="w-full h-full object-contain shadow-2xl drop-shadow-2xl cursor-pointer"
                    style={{ maxHeight: '100vh' }}
                    loop
                    playsInline
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleVideoPlayback();
                    }}
                    onLoadedMetadata={(e) => {
                      // Store video dimensions for aspect ratio
                      const video = e.currentTarget;
                      if (video.videoWidth && video.videoHeight) {
                        setImgDims({ width: video.videoWidth, height: video.videoHeight });
                      }
                    }}
                    onPlay={() => {
                      setIsVideoPlaying(true);
                      // Track play event
                      const targetGalleryId = galleryId || gallery?.id;
                      if (targetGalleryId && selectedPhoto) {
                        analyticsService.trackVideoEngagement(
                          targetGalleryId,
                          selectedPhoto.id,
                          'play',
                          videoRef.current?.currentTime || 0,
                          (Date.now() - sessionStartTime.current) / 1000
                        );
                      }
                    }}
                    onPause={() => {
                      setIsVideoPlaying(false);
                      // Track pause event
                      const targetGalleryId = galleryId || gallery?.id;
                      if (targetGalleryId && selectedPhoto && videoRef.current) {
                        analyticsService.trackVideoEngagement(
                          targetGalleryId,
                          selectedPhoto.id,
                          'pause',
                          videoRef.current.currentTime,
                          (Date.now() - sessionStartTime.current) / 1000
                        );
                      }
                    }}
                    onSeeked={() => {
                      // Track seek event (user jumped to different time)
                      const targetGalleryId = galleryId || gallery?.id;
                      if (targetGalleryId && selectedPhoto && videoRef.current) {
                        analyticsService.trackVideoEngagement(
                          targetGalleryId,
                          selectedPhoto.id,
                          'seek',
                          videoRef.current.currentTime,
                          (Date.now() - sessionStartTime.current) / 1000
                        );
                      }
                    }}
                    onEnded={() => {
                      // Track video completion
                      const targetGalleryId = galleryId || gallery?.id;
                      if (targetGalleryId && selectedPhoto && videoRef.current) {
                        analyticsService.trackVideoEngagement(
                          targetGalleryId,
                          selectedPhoto.id,
                          'complete',
                          videoRef.current.duration,
                          (Date.now() - sessionStartTime.current) / 1000
                        );
                      }
                    }}
                  >
                    {/* Use original video URL (not medium_url which is JPEG thumbnail) */}
                    <source src={getImageUrl(selectedPhoto.url)} type="video/mp4" />
                    <source src={getImageUrl(selectedPhoto.url)} type="video/quicktime" />
                    Your browser does not support the video tag.
                  </video>

                  {/* Play button overlay - Apple-style with smooth transitions */}
                  {!isVideoPlaying && (
                    <div 
                      className="absolute inset-0 flex items-center justify-center pointer-events-none transition-opacity duration-300 ease-out"
                    >
                      <div className="relative">
                        {/* Outer glow ring */}
                        <div className="absolute inset-0 bg-white/20 rounded-full blur-2xl scale-150 animate-pulse" />
                        {/* Main button */}
                        <div className="relative bg-gradient-to-br from-white/30 to-white/10 rounded-full p-8 backdrop-blur-xl border border-white/20 shadow-2xl transform transition-transform duration-300 ease-out hover:scale-110">
                          <PlayCircle className="w-16 h-16 text-white drop-shadow-2xl" strokeWidth={1.5} />
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Timestamp Capture Feedback - Apple-style elegant notification */}
                  {showTimestampCapture && videoTimestamp !== null && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none z-50">
                      <div className="bg-black/90 backdrop-blur-2xl px-6 py-4 rounded-2xl shadow-2xl border border-white/10 animate-[fadeInScale_0.4s_ease-out]">
                        <div className="flex items-center gap-3">
                          {/* Clock icon */}
                          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          {/* Timestamp text */}
                          <div>
                            <div className="text-white font-medium text-sm">Moment Captured</div>
                            <div className="text-blue-400 font-mono text-xs">
                              {Math.floor(videoTimestamp / 60)}:{String(Math.floor(videoTimestamp % 60)).padStart(2, '0')}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Progress bar - PIXIESET-style with Apple smoothness */}
                  <div 
                    className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-t from-black/40 to-transparent backdrop-blur-sm cursor-pointer hover:h-2 transition-all duration-300 ease-out group"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (videoRef.current && videoRef.current.duration) {
                        const rect = e.currentTarget.getBoundingClientRect();
                        const clickX = e.clientX - rect.left;
                        const newTime = (clickX / rect.width) * videoRef.current.duration;
                        videoRef.current.currentTime = newTime;
                        setVideoProgress((newTime / videoRef.current.duration) * 100);
                      }
                    }}
                  >
                    {/* Background track */}
                    <div className="absolute bottom-0 left-0 right-0 h-full bg-white/10 rounded-full" />
                    
                    {/* Progress fill with gradient */}
                    <div 
                      className="absolute bottom-0 left-0 h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-75 ease-out shadow-lg"
                      style={{ width: `${videoProgress}%` }}
                    >
                      {/* Playhead indicator - appears on hover */}
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-out transform group-hover:scale-110" />
                    </div>
                    
                    {/* Timestamp markers for comments - Interactive */}
                    {selectedPhoto.comments?.map((comment) => {
                      if (comment.timestamp !== undefined && videoRef.current?.duration) {
                        const markerPosition = (comment.timestamp / videoRef.current.duration) * 100;
                        const formatTime = (seconds: number) => {
                          const mins = Math.floor(seconds / 60);
                          const secs = Math.floor(seconds % 60);
                          return `${mins}:${String(secs).padStart(2, '0')}`;
                        };
                        
                        return (
                          <div
                            key={`marker-${comment.id}`}
                            className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full shadow-lg hover:scale-150 hover:bg-blue-400 transition-all duration-200 ease-out cursor-pointer z-10 group/marker"
                            style={{ left: `${markerPosition}%` }}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (videoRef.current && comment.timestamp !== undefined) {
                                videoRef.current.currentTime = comment.timestamp;
                                setVideoProgress((comment.timestamp / videoRef.current.duration) * 100);
                              }
                            }}
                          >
                            {/* Tooltip on hover - Apple style */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 px-3 py-1.5 bg-black/90 text-white text-xs rounded-lg whitespace-nowrap opacity-0 group-hover/marker:opacity-100 transition-all duration-200 ease-out pointer-events-none backdrop-blur-xl shadow-2xl">
                              <div className="font-medium">{formatTime(comment.timestamp)}</div>
                              <div className="text-white/70 text-[10px] mt-0.5 max-w-[200px] truncate">
                                {comment.text}
                              </div>
                              {/* Arrow */}
                              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                                <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-black/90" />
                              </div>
                            </div>
                            
                            {/* Pulse animation for new comments */}
                            <div className="absolute inset-0 bg-blue-400 rounded-full animate-ping opacity-75" />
                          </div>
                        );
                      }
                      return null;
                    })}
                  </div>
                </div>
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

           {/* Edit Mode Overlay Instruction - Only for images */}
           {isEditing && selectedPhoto.type !== 'video' && (
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
                            if (selectedPhoto.type === 'video') {
                              // For videos: Pause and capture timestamp with elegant feedback
                              if (videoRef.current) {
                                videoRef.current.pause();
                                setIsVideoPlaying(false);
                                setVideoTimestamp(videoRef.current.currentTime);
                                
                                // Show visual feedback
                                setShowTimestampCapture(true);
                                setTimeout(() => setShowTimestampCapture(false), 2000);
                              }
                              setFeedbackModalOpen(true);
                            } else {
                              // For images: Use lasso tool
                            if (drawingPoints.length > 0) {
                                // If drawing exists, just open modal
                                setFeedbackModalOpen(true);
                            } else {
                                // Start editing mode
                                setIsEditing(true);
                                setShowControls(false); // Hide controls to see photo clearly
                              }
                            }
                        }}
                        className={`p-3 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-all duration-200 ${isEditing ? 'bg-yellow-500' : 'bg-black/40 hover:bg-black/60'}`}
                    >
                        <Pencil className="w-7 h-7" />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">
                      {selectedPhoto.type === 'video' ? 'Comment' : (isEditing ? 'Cancel' : 'Edit')}
                    </span>
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
            setVideoTimestamp(null); // Clear timestamp on close
        }}
        galleryId={galleryId || ''}
        photoId={drawingPoints.length > 0 || videoTimestamp !== null ? selectedPhoto?.id : undefined}
        annotation={drawingPoints.length > 0 ? JSON.stringify(drawingPoints) : undefined}
        timestamp={videoTimestamp !== null ? videoTimestamp : undefined}
        initialComment={drawingPoints.length > 0 || videoTimestamp !== null ? '' : ''}
        onCommentAdded={(newComment) => {
            handleCommentsChange([...(selectedPhoto?.comments || []), newComment]);
            setVideoTimestamp(null); // Clear timestamp after adding comment
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

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}
