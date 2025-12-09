/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useRef, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';
import { getImageUrl } from '../config/env';
import * as photoService from '../services/photoService';
import * as galleryService from '../services/galleryService';
import * as clientService from '../services/clientService';
import { useBrandedModal } from '../components/BrandedModal';
import {
  ArrowLeft,
  Upload,
  Share2,
  Heart,
  MessageCircle,
  X,
  AlertCircle,
  Settings,
  Mail,
  Bell,
  Download,
  Trash2,
  Pencil,
  PlayCircle,
  BarChart3,
} from 'lucide-react';
import { uploadManager, UploadProgress } from '../utils/uploadManager';
import { isVideoFile, getVideoDuration, checkVideoDurationLimit, getVideoDurationLimitForPlan } from '../utils/videoUtils';
import DuplicateResolutionModal from '../components/DuplicateResolutionModal';
import ShareModal from '../components/ShareModal';
import { Photo, Comment } from '../services/photoService';
import * as analyticsService from '../services/analyticsService';
import { ClientEngagementSummary } from '../services/analyticsService';
import CommentSection from '../components/CommentSection';
import ClientInsights from '../components/ClientInsights';
import GalleryInsightsDashboard from '../components/GalleryInsightsDashboard';
import ProgressiveImage from '../components/ProgressiveImage';
import GalleryLayoutRenderer from '../components/GalleryLayoutRenderer';
import GalleryLayoutSelector from '../components/GalleryLayoutSelector';
import { useSlideshow } from '../hooks/useSlideshow';
import { useSwipe } from '../hooks/useSwipe';

interface Gallery {
  id: string;
  user_id?: string;
  name: string;
  description?: string;
  photo_count: number;
  client_name?: string;
  client_emails?: string[];
  created_at: string;
  status?: string;
  privacy?: string;
  password?: string;
  tags?: string[];
  views?: number;
  view_count?: number;
  seo_title?: string;
  seo_description?: string;
  slug?: string;
  thumbnail_url?: string;
  cover_photo?: string;
  cover_photo_url?: string;
  storage_used?: number;
  layout_id?: string;  // Added for gallery layouts
  settings?: {
    download_enabled?: boolean;
    comments_enabled?: boolean;
    favorites_enabled?: boolean;
  };
  allow_downloads?: boolean;
  allow_comments?: boolean;
  allow_edits?: boolean;
  photos?: Photo[];
  pagination?: {
    has_more: boolean;
    next_key?: any;
  };
}

export default function GalleryPage() {
  const { galleryId } = useParams<{ galleryId: string }>();
  const navigate = useNavigate();
  const { showAlert, showConfirm, ModalComponent } = useBrandedModal();
  const [gallery, setGallery] = useState<Gallery | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [pagination, setPagination] = useState<{ has_more: boolean; next_key?: any }>({ has_more: false });
  
  // Gallery layout state
  const [galleryLayout, setGalleryLayout] = useState<any>(null);
  
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { user } = useAuth(); // Ensure user is available
  
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  const [showMobileComments, setShowMobileComments] = useState(false);
  const [showInsights, setShowInsights] = useState(true); // Show insights by default for photographers
  const [photoEngagement, setPhotoEngagement] = useState<Record<string, ClientEngagementSummary>>({});

  // Photo modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);

  // Settings modal state
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [analyticsModalOpen, setAnalyticsModalOpen] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    name: '',
    description: '',
    client_name: '',
    client_emails: [] as string[],
    allow_downloads: true,
    allow_comments: true,
    allow_edits: true,
    tags: [] as string[],
    privacy: 'private',
    password: '',
    layout_id: '' as string | undefined,
    seo: {
      title: '',
      description: '',
      slug: ''
    }
  });
  const [newClientEmail, setNewClientEmail] = useState('');
  const [newTag, setNewTag] = useState('');

  // Duplicate resolution
  const [duplicateModalOpen, setDuplicateModalOpen] = useState(false);
  const [duplicateFile, setDuplicateFile] = useState<File | null>(null);
  const [duplicateMatches, setDuplicateMatches] = useState<Photo[]>([]);
  const [pendingUploadQueue, setPendingUploadQueue] = useState<File[]>([]);
  const [accumulatedFiles, setAccumulatedFiles] = useState<File[]>([]); // Files ready for batch upload

  // Selection state
  const [selectedPhotos, setSelectedPhotos] = useState<Set<string>>(new Set());

  // Share Modal state
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [showControls, setShowControls] = useState(true);

  const [slideDirection, setSlideDirection] = useState<'up' | 'down' | null>(null);
  const [lastTap, setLastTap] = useState(0);
  const [imgDims, setImgDims] = useState<{width: number, height: number} | null>(null);

  const [lastScrollTime, setLastScrollTime] = useState(0);
  const [filterFavorites, setFilterFavorites] = useState(false);

  // Slideshow
  const navigatePhotoRef = useRef<(dir: number) => void>(() => {});
  const { stop: stopSlideshow } = useSlideshow(
    () => navigatePhotoRef.current(1), 
    Number(import.meta.env.VITE_SLIDESHOW_INTERVAL) || 3000
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Video playback state
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [videoProgress, setVideoProgress] = useState(0);

  // Compute current photo
  const currentPhoto = photos[currentPhotoIndex];

  // Reset dims when photo changes
  useEffect(() => {
    setImgDims(null);
  }, [currentPhotoIndex]);

  // Auto-play videos when modal opens or photo changes (TikTok style)
  useEffect(() => {
    if (modalOpen && currentPhoto && currentPhoto.type === 'video' && videoRef.current) {
      // Reset progress
      setVideoProgress(0);
      // Delay to ensure video is loaded (from env)
      const autoplayDelay = Number(import.meta.env.VITE_VIDEO_AUTOPLAY_DELAY) || 300;
      const timer = setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.play()
            .then(() => setIsVideoPlaying(true))
            .catch(() => setIsVideoPlaying(false));
        }
      }, autoplayDelay);
      return () => clearTimeout(timer);
    } else {
      setIsVideoPlaying(false);
      setVideoProgress(0);
    }
  }, [modalOpen, currentPhotoIndex, currentPhoto]);

  // Pause video when modal closes
  useEffect(() => {
    if (!modalOpen && videoRef.current) {
      videoRef.current.pause();
      setIsVideoPlaying(false);
      setVideoProgress(0);
    }
  }, [modalOpen]);

  // Update video progress for smooth progress bar
  useEffect(() => {
    if (isVideoPlaying && videoRef.current) {
      const updateProgress = () => {
        if (videoRef.current && videoRef.current.duration) {
          setVideoProgress((videoRef.current.currentTime / videoRef.current.duration) * 100);
        }
      };
      
      // Progress update interval from env
      const progressInterval = Number(import.meta.env.VITE_VIDEO_PROGRESS_UPDATE_INTERVAL) || 100;
      const interval = setInterval(updateProgress, progressInterval);
      return () => clearInterval(interval);
    }
  }, [isVideoPlaying]);

  const loadGallery = useCallback(async (loadMore = false) => {
    if (!galleryId) return;
    
    // Prevent concurrent loads or loading more if nothing more to load
    if (loadMore && (!pagination.has_more || loadingMore)) return;
    
    if (loadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const params: { page_size: number; last_key?: unknown } = { 
        page_size: Number(import.meta.env.VITE_PAGE_SIZE) || 50 
      };
      if (loadMore && pagination.next_key) {
        params.last_key = pagination.next_key;
      }

      const galleryRes = await galleryService.getGallery(galleryId, params);

      if (galleryRes.success && galleryRes.data) {
        // If loading more, append photos
        if (loadMore) {
          const data = galleryRes.data as unknown as Gallery;
          const newPhotos = (data.photos || []).map(p => ({
            ...p,
            comments_count: p.comments?.length || 0
          }));
          setPhotos(prev => [...prev, ...newPhotos]);
        } else {
          // Cast the response to unknown then Gallery to avoid TS overlap issues with service types
          const data = galleryRes.data as unknown as Gallery & { seo_title?: string; seo_description?: string; slug?: string }; 
          setGallery(data);
          
          // Fetch layout if gallery has a layout_id
          if (data.layout_id) {
            try {
              const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
              const layoutResponse = await fetch(`${apiUrl}/v1/gallery-layouts/${data.layout_id}`);
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
          
          // Ensure comments_count is accurate from the comments array
          const photosWithCounts = (data.photos || []).map(p => ({
            ...p,
            comments_count: p.comments?.length || 0
          }));
          setPhotos(photosWithCounts);
          
          // Load engagement data for all photos (photographer insights)
          if (!loadMore && galleryId) {
            analyticsService.getGalleryEngagement(galleryId).then(engagementData => {
              const engagementMap: Record<string, ClientEngagementSummary> = {};
              engagementData.forEach(item => {
                engagementMap[item.photo_id] = item;
              });
              setPhotoEngagement(engagementMap);
            }).catch(err => console.error('Failed to load engagement data:', err));
          }
          
          // Initialize settings form only on first load
          setSettingsForm({
            name: data.name || '',
            description: data.description || '',
            client_name: data.client_name || '',
            client_emails: data.client_emails || [],
            allow_downloads: data.allow_downloads !== false,
            allow_comments: data.allow_comments !== false,
            allow_edits: data.allow_edits !== false,
            tags: data.tags || [],
            privacy: data.privacy || 'private',
            password: data.password || '',
            layout_id: data.layout_id || undefined,
            seo: {
                title: data.seo_title || '',
                description: data.seo_description || '',
                slug: data.slug || ''
            }
          });
        }
        
        // Update pagination state
        if (galleryRes.data.pagination) {
          setPagination({
            has_more: galleryRes.data.pagination.has_more,
            next_key: galleryRes.data.pagination.next_key
          });
        } else {
           // Fallback if pagination not returned
           setPagination({ has_more: false });
        }
      } else {
        console.error("Failed to load gallery:", galleryRes.error);
      }
    } catch (error) {
      console.error("Error loading gallery:", error);
    } finally {
      if (loadMore) {
        setLoadingMore(false);
      } else {
        setLoading(false);
      }
    }
  }, [galleryId, pagination.has_more, pagination.next_key, loadingMore]);

  useEffect(() => {
    if (galleryId) {
      loadGallery();
    }
  }, [galleryId, loadGallery]);

  const openPhotoModal = (index: number) => {
    setCurrentPhotoIndex(index);
    setModalOpen(true);
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    setModalOpen(false);
    stopSlideshow();
    document.body.style.overflow = '';
  };

  const navigatePhoto = useCallback((direction: number) => {
    let newIndex = currentPhotoIndex + direction;
    if (newIndex < 0) newIndex = photos.length - 1;
    if (newIndex >= photos.length) newIndex = 0;
    
    setSlideDirection(direction > 0 ? 'up' : 'down');
    setCurrentPhotoIndex(newIndex);
  }, [currentPhotoIndex, photos.length]);

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

  // Keyboard navigation for modal (TikTok-style up/down + left/right)
  useEffect(() => {
    if (!modalOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in input
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      switch(e.key) {
        case 'ArrowUp':
        case 'ArrowLeft':
          e.preventDefault();
          navigatePhoto(-1);
          break;
        case 'ArrowDown':
        case 'ArrowRight':
          e.preventDefault();
          navigatePhoto(1);
          break;
        case 'Escape':
          e.preventDefault();
          closeModal();
          break;
        case ' ':
        case 'Spacebar': // Older browsers
          e.preventDefault(); // Always prevent page scroll
          // Space bar for video play/pause only
          if (currentPhoto?.type === 'video') {
            toggleVideoPlayback();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [modalOpen, navigatePhoto, currentPhoto, toggleVideoPlayback]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    const now = Date.now();
    const debounceDelay = Number(import.meta.env.VITE_SCROLL_DEBOUNCE_DELAY) || 300;
    const scrollThreshold = Number(import.meta.env.VITE_SCROLL_THRESHOLD) || 50;

    if (now - lastScrollTime < debounceDelay) return; // Debounce from env

    if (e.deltaY > scrollThreshold) {
        navigatePhoto(1);
        setLastScrollTime(now);
    } else if (e.deltaY < -scrollThreshold) {
        navigatePhoto(-1);
        setLastScrollTime(now);
    }
  }, [lastScrollTime, navigatePhoto]);

  const swipeHandlers = useSwipe({
    onSwipedUp: () => navigatePhoto(1),
    onSwipedDown: () => navigatePhoto(-1),
    onSwipedLeft: () => {},
    onSwipedRight: () => {},
  });

  const handleShareGallery = () => {
    if (!gallery) return;
    setShareModalOpen(true);
  };

  const handleSendEmail = async () => {
    if (!galleryId || !gallery?.client_emails?.length) {
      await showAlert('Missing Information', 'Please add client emails in settings first.', 'error');
      return;
    }

    const confirmed = await showConfirm(
      'Send Email Notifications',
      `Send notification email to ${gallery.client_emails.length} client(s)?`,
      'Send',
      'Cancel'
    );
    
    if (!confirmed) return;

    try {
      const response = await photoService.sendBatchNotification(
        galleryId, 
        [], 
        'New photos added to your gallery'
      );
      
      if (response.success) {
        await showAlert('Success', 'Email notifications sent successfully!', 'success');
      } else {
        await showAlert('Error', 'Failed to send emails: ' + (response.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      console.error('Error sending emails:', error);
      await showAlert('Error', 'An error occurred while sending emails.', 'error');
    }
  };

  const handleRemind = async () => {
    if (!galleryId) return;

    const confirmed = await showConfirm(
      'Send Reminder',
      "Send a reminder to clients who haven't selected photos yet?",
      'Send Reminder',
      'Cancel'
    );
    
    if (!confirmed) return;

    try {
      const response = await clientService.sendSelectionReminder(galleryId);
      
      if (response.success) {
        await showAlert('Success', 'Reminder sent successfully!', 'success');
      } else {
        await showAlert('Error', 'Failed to send reminder: ' + (response.error || 'Unknown error'), 'error');
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
      await showAlert('Error', 'An error occurred while sending reminder.', 'error');
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!galleryId || !e.target.files || e.target.files.length === 0) return;

    const files = Array.from(e.target.files).filter(
      (file) => file.type.startsWith('image/') || file.type.startsWith('video/')
    );

    if (files.length === 0) {
      setUploadError('Please select valid image or video files.');
      return;
    }

    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';

    // Start checking for duplicates one by one
    // We will build a "safe" list to upload and handle duplicates interactively
    // Initialize accumulation with empty array
    setUploadError(null);
    setCheckingDuplicates(true); // Show checking status
    processUploadQueue(files, []);
  };

  const processUploadQueue = async (queue: File[], currentBatch: File[]) => {
    if (queue.length === 0) {
        setCheckingDuplicates(false);
        // All checked. Start upload of collected files if any.
        if (currentBatch.length > 0) {
            startUpload(currentBatch);
        }
        return;
    }

    const currentFile = queue[0];
    const remainingQueue = queue.slice(1);

    try {
      // Check for duplicates
      const checkRes = await photoService.checkDuplicates(galleryId!, currentFile.name, currentFile.size);
      
      if (checkRes.success && checkRes.data && checkRes.data.has_duplicates) {
        // Show modal
        setDuplicateFile(currentFile);
        setDuplicateMatches(checkRes.data.duplicates);
        setDuplicateModalOpen(true);
        setPendingUploadQueue(remainingQueue);
        setAccumulatedFiles(currentBatch); // Save progress
        
        // Wait for user action via callback
        return; 
      }

      // No duplicate, add to batch
      // Continue with next file, passing updated batch
      processUploadQueue(remainingQueue, [...currentBatch, currentFile]);

    } catch (error) {
      console.error('Error checking duplicates:', error);
      // On error, assume safe to upload
      processUploadQueue(remainingQueue, [...currentBatch, currentFile]);
    }
  };

  const handleDuplicateResolve = (action: 'skip' | 'upload') => {
    // Retrieve accumulated files from state
    const currentBatch = [...accumulatedFiles];
    
    if (action === 'upload' && duplicateFile) {
        // Add the duplicate file if user chose to upload anyway
        currentBatch.push(duplicateFile);
    }
    
    // Continue queue
    setDuplicateModalOpen(false);
    setDuplicateFile(null);
    setDuplicateMatches([]);
    setAccumulatedFiles([]); // Clear temp state
    
    // Process remaining
    processUploadQueue(pendingUploadQueue, currentBatch);
  };

  const handleToggleFavorite = async (photoId: string) => {
    if (!galleryId) return;
    
    // Check if user is the photographer (owner of the gallery)
    if (user && gallery && user.id === gallery.user_id) {
      await showAlert(
        'Cannot Favorite',
        'As the photographer, you cannot favorite your own photos. Only clients can mark photos as favorites.',
        'info'
      );
      return;
    }
    
    const photo = photos.find(p => p.id === photoId);
    if (!photo) return;

    try {
      let response;
      if (photo.is_favorite) {
          response = await clientService.removeFavorite(photoId);
      } else {
          response = await clientService.addFavorite(photoId, galleryId);
      }

      if (response.success) {
         setPhotos(currentPhotos => currentPhotos.map(p => {
             if (p.id === photoId) {
                 return {
                     ...p,
                     is_favorite: !p.is_favorite,
                     favorites_count: (p.favorites_count || 0) + (p.is_favorite ? -1 : 1)
                 };
             }
             return p;
         }));
      } else if (response.error) {
        // Show error message from backend
        await showAlert('Error', response.error, 'error');
      }
    } catch (error: any) {
      console.error('Error toggling favorite:', error);
      // Show user-friendly error message
      const errorMessage = error?.response?.data?.error || error?.message || 'Failed to favorite photo';
      await showAlert('Error', errorMessage, 'error');
    }
  };

  const startUpload = async (filesToUpload: File[]) => {
    if (!galleryId) return;
    
    // Validate video files before upload
    const videoValidationErrors: string[] = [];
    
    for (const file of filesToUpload) {
      if (isVideoFile(file)) {
        try {
          const duration = await getVideoDuration(file);
          const planLimit = getVideoDurationLimitForPlan(user?.plan || 'free');
          const validation = checkVideoDurationLimit(duration, planLimit);
          
          if (!validation.allowed) {
            videoValidationErrors.push(`${file.name}: ${validation.message}`);
          }
        } catch (error) {
          console.error('Error validating video:', error);
          videoValidationErrors.push(`${file.name}: Could not validate video duration`);
        }
      }
    }
    
    // Show errors if any videos are too long
    if (videoValidationErrors.length > 0) {
      await showAlert(
        'Video Duration Limit Exceeded',
        videoValidationErrors.join('\n\n'),
        'error'
      );
      return;
    }
    
    setUploading(true);
    setUploadError(null);

    try {
      await uploadManager.uploadFiles(filesToUpload, {
        galleryId,
        onProgress: (progressArray: UploadProgress[]) => {
          // Merge with existing progress if needed, but for now simple single batch view
          // This logic simplifies progress to just the current batch
          const totalFiles = progressArray.length;
          const completedFiles = progressArray.filter(p => p.status === 'completed').length;
          const inProgressFiles = progressArray.filter(p => p.status === 'uploading' || p.status === 'processing');
          
          let currentProgressSum = 0;
          inProgressFiles.forEach(p => currentProgressSum += p.progress);
          
          const overallProgress = totalFiles > 0 
            ? ((completedFiles * 100) + currentProgressSum) / totalFiles
            : 0;
          
          setUploadProgress(Math.round(overallProgress));
        },
        onError: (errorMsg) => {
          console.error("Upload error:", errorMsg);
          setUploadError(errorMsg);
        },
        onComplete: () => {
          // Ideally we should have a global upload state manager.
          // For simplicity, we just reload gallery to get new photos.
          // We reset pagination to get the latest state including new uploads (usually at top if sorted by date desc, but photos sorted by created_at in backend)
          // Actually backend sorts by created_at. New photos might be at end or beginning.
          // Let's reload everything for consistency.
          loadGallery(false);
          
          // We set uploading to false only if we don't have pending modal
          if (!duplicateModalOpen) {
             setUploading(false);
             setUploadProgress(0);
          }
        }
      });
    } catch (err: any) {
      console.error("Overall upload process failed:", err);
      setUploading(false);
      setUploadProgress(0);
      setUploadError(err.message || 'Upload failed. Please try again.');
    }
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleCommentsChange = (newComments: Comment[]) => {
    if (!photos[currentPhotoIndex]) return;
    
    // Update local state for immediate feedback
    const updatePhotoWithComments = (p: Photo) => {
      if (p.id !== photos[currentPhotoIndex].id) return p;
      return {
        ...p,
        comments: newComments,
        comments_count: newComments.length
      };
    };

    setPhotos(photos.map(updatePhotoWithComments));
  };

  const handleSaveSettings = async () => {
    if (!galleryId) return;

    try {
      const response = await api.put(`/galleries/${galleryId}`, {
        name: settingsForm.name,
        description: settingsForm.description,
        client_name: settingsForm.client_name,
        client_emails: settingsForm.client_emails,
        allow_downloads: settingsForm.allow_downloads,
        allow_comments: settingsForm.allow_comments,
        allow_edits: settingsForm.allow_edits,
        tags: settingsForm.tags,
        privacy: settingsForm.privacy,
        password: settingsForm.password,
        layout_id: settingsForm.layout_id || null,
        seo: settingsForm.seo
      });

      if (response.success) {
        setSettingsModalOpen(false);
        // Reload gallery to reflect updated settings
        loadGallery(false);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const handleDeleteGallery = async () => {
    if (!galleryId) return;
    
    const confirmed = await showConfirm(
      'Delete Gallery',
      `This will permanently delete:\n\n` +
      `• Gallery "${gallery?.name}"\n` +
      `• All uploaded photos\n` +
      `• All comments\n` +
      `• Share links\n\n` +
      `This action CANNOT be undone.`,
      'Delete Gallery',
      'Cancel',
      'danger'
    );

    if (confirmed) {
      try {
        const response = await galleryService.deleteGallery(galleryId);
        if (response.success) {
          navigate('/dashboard');
        } else {
          await showAlert('Error', 'Failed to delete gallery: ' + response.error, 'error');
        }
      } catch (error) {
        console.error('Error deleting gallery:', error);
        await showAlert('Error', 'An error occurred while deleting the gallery.', 'error');
      }
    }
  };

  const handleArchiveOriginals = async () => {
    if (!galleryId) return;
    
    const confirmed = await showConfirm(
      'Archive Original Files',
      'Archive all original RAW files to Glacier Vault?\n\nThis will move high-res originals to long-term cold storage to save costs. They will still be available for download but retrieval may take 1-5 minutes.',
      'Archive',
      'Cancel'
    );
    
    if (!confirmed) return;

    try {
      const response = await api.post(`/galleries/${galleryId}/archive-originals`, {});
      if (response.success) {
        await showAlert('Success', response.data?.message || 'Originals archived successfully.', 'success');
      } else {
        await showAlert('Error', response.error || 'Failed to archive originals', 'error');
      }
    } catch (error) {
      console.error('Error archiving originals:', error);
      await showAlert('Error', 'An error occurred.', 'error');
    }
  };

  const handleAddClientEmail = async () => {
    const email = newClientEmail.trim().toLowerCase();
    if (!email) return;

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      await showAlert('Invalid Email', 'Please enter a valid email address', 'error');
      return;
    }

    if (settingsForm.client_emails.includes(email)) {
      await showAlert('Duplicate Email', 'This email is already added', 'error');
      return;
    }

    setSettingsForm({
      ...settingsForm,
      client_emails: [...settingsForm.client_emails, email],
    });
    setNewClientEmail('');
  };

  const handleRemoveClientEmail = (email: string) => {
    setSettingsForm({
      ...settingsForm,
      client_emails: settingsForm.client_emails.filter(e => e !== email),
    });
  };

  const handleAddTag = () => {
    const tag = newTag.trim().toLowerCase();
    if (!tag) return;
    if (settingsForm.tags.includes(tag)) {
      showAlert('Duplicate Tag', 'This tag is already added', 'error');
      return;
    }
    setSettingsForm({
      ...settingsForm,
      tags: [...settingsForm.tags, tag],
    });
    setNewTag('');
  };

  const handleRemoveTag = (tag: string) => {
    setSettingsForm({
      ...settingsForm,
      tags: settingsForm.tags.filter(t => t !== tag),
    });
  };

  const handleSelectPhoto = (photoId: string) => {
    const newSelected = new Set(selectedPhotos);
    if (newSelected.has(photoId)) {
      newSelected.delete(photoId);
    } else {
      newSelected.add(photoId);
    }
    setSelectedPhotos(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedPhotos.size === photos.length) {
      setSelectedPhotos(new Set());
    } else {
      setSelectedPhotos(new Set(photos.map(p => p.id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedPhotos.size === 0) return;
    if (!galleryId) return;
    
    const confirmed = await showConfirm(
      'Delete Photos',
      `Delete ${selectedPhotos.size} photo(s)?`,
      'Delete',
      'Cancel',
      'danger'
    );
    
    if (!confirmed) return;

    try {
      const photoIds = Array.from(selectedPhotos);
      await photoService.deletePhotos(galleryId, photoIds);
      
      setSelectedPhotos(new Set());
      // Remove from local state instead of full reload to preserve scroll
      setPhotos(prev => prev.filter(p => !photoIds.includes(p.id)));
      
      // Update gallery count locally
      if (gallery) {
          setGallery({ ...gallery, photo_count: Math.max(0, gallery.photo_count - photoIds.length) });
      }
    } catch (error) {
      console.error('Error deleting photos:', error);
      // Reload on error to ensure sync
      loadGallery(false);
    }
  };

  const handleDownloadPhoto = async () => {
    if (!photos[currentPhotoIndex]) return;
    
    const photo = photos[currentPhotoIndex];
    // Prefer original_download_url if available (for HEIC, RAW, etc)
    const downloadUrl = photo.original_download_url || photo.url;
    // Use getImageUrl to handle full URLs correctly if they already contain http
    const imageUrl = getImageUrl(downloadUrl);
    
    // Use original filename if available, otherwise use converted filename
    const downloadFilename = photo.original_filename || photo.filename || `photo-${Date.now()}.jpg`;
    
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading photo:', error);
    }
  };

  const handleBulkDownload = async () => {
    if (!galleryId) return;
    try {
      const response = await clientService.bulkDownload(galleryId);
      if (response.success && response.data?.download_url) {
        window.location.href = response.data.download_url;
      } else {
        await showAlert('Error', 'Download not available or failed to start.', 'error');
      }
    } catch (error) {
      console.error('Bulk download error:', error);
    }
  };

  const displayedPhotos = filterFavorites 
    ? photos.filter(p => (p.favorites_count || 0) > 0) 
    : photos;

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

  if (!gallery) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-[#1D1D1F]/60">Gallery not found</p>
          <Link
            to="/dashboard"
            className="mt-4 inline-block text-[#0066CC] hover:text-[#0052A3]"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/dashboard"
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <div>
                <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                  {gallery.name.toUpperCase()}
                </h1>
                <p className="text-sm text-[#1D1D1F]/60">
                  {gallery.client_name} • {gallery.photo_count} photos • {new Date(gallery.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterFavorites(!filterFavorites)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                  filterFavorites 
                    ? 'bg-red-50 text-red-600 border border-red-100' 
                    : 'bg-white border border-gray-200 text-[#1D1D1F] hover:bg-gray-50'
                }`}
              >
                <Heart className={`w-4 h-4 ${filterFavorites ? 'fill-red-600' : ''}`} />
                {filterFavorites ? 'Favorites Only' : 'Filter Favorites'}
              </button>
              {photos.length > 0 && (
                <button
                  onClick={handleBulkDownload}
                  className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download All
                </button>
              )}
              <button
                onClick={() => setAnalyticsModalOpen(true)}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-sm font-medium hover:from-blue-600 hover:to-indigo-600 transition-all flex items-center gap-2 shadow-lg"
              >
                <BarChart3 className="w-4 h-4" />
                Gallery Insights
              </button>
              <button
                onClick={handleShareGallery}
                className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <button
                onClick={() => {
                  // Populate form with current gallery data
                  setSettingsForm({
                    name: gallery.name || '',
                    description: gallery.description || '',
                    client_name: gallery.client_name || '',
                    client_emails: gallery.client_emails || [],
                    allow_downloads: gallery.allow_downloads !== undefined ? gallery.allow_downloads : true,
                    allow_comments: gallery.allow_comments !== undefined ? gallery.allow_comments : true,
                    allow_edits: gallery.allow_edits !== undefined ? gallery.allow_edits : true,
                    tags: gallery.tags || [],
                    privacy: gallery.privacy || 'private',
                    password: gallery.password || '',
                    layout_id: gallery.layout_id || undefined,
                    seo: {
                      title: gallery.seo_title || '',
                      description: gallery.seo_description || '',
                      slug: gallery.slug || ''
                    }
                  });
                  setSettingsModalOpen(true);
                }}
                className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>
              {photos.length > 0 && gallery.client_emails && gallery.client_emails.length > 0 && (
                <>
                  <button
                    onClick={handleSendEmail}
                    className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
                  >
                    <Mail className="w-4 h-4" />
                    Send Email
                  </button>
                  <button
                    onClick={handleRemind}
                    className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all flex items-center gap-2"
                  >
                    <Bell className="w-4 h-4" />
                    Remind
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {uploadError && (
        <div className="max-w-7xl mx-auto px-6 mt-4">
          <div className="p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">Upload error: {uploadError}</p>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Gallery Description */}
        <div className="glass-panel p-8 mb-8">
          <h1 className="text-3xl font-serif font-medium text-[#1D1D1F] mb-4">
            {gallery.name}
          </h1>
          <p className="text-[#1D1D1F]/70 break-words whitespace-pre-wrap">
            {gallery.description || 'Add a description in Gallery Settings to share details with your clients.'}
          </p>
        </div>

        {/* Upload Section */}
        <div className="glass-panel p-12 mb-8 text-center">
          <input
            type="file"
            multiple
            accept="image/*,video/*,.dng,.cr2,.cr3,.nef,.arw,.raf,.orf,.rw2,.pef,.3fr,.raw"
            ref={fileInputRef}
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <div 
            className="cursor-pointer transition-opacity hover:opacity-100 opacity-60"
            onClick={openFilePicker}
          >
            <svg 
              width="80" 
              height="80" 
              viewBox="0 0 80 80" 
              fill="none" 
              className="mx-auto mb-6"
            >
              <circle cx="40" cy="40" r="38" stroke="currentColor" strokeWidth="1.5" opacity="0.2" />
              <path d="M25 40h30M40 25v30" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-3">
              Add Photos to Gallery
            </h3>
            <p className="text-[#1D1D1F]/60 mb-6">
              Upload images to share with your client
            </p>
            <button
              onClick={(e) => { e.stopPropagation(); openFilePicker(); }}
              disabled={uploading || checkingDuplicates}
              className="px-8 py-3 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {checkingDuplicates ? 'Checking files...' : uploading ? `Uploading ${uploadProgress}%` : 'Choose Files'}
            </button>
          </div>
        </div>

        {/* Bulk Actions Toolbar */}
        {photos.length > 0 && (
          <div className="glass-panel p-4 mb-6 flex items-center justify-between sticky top-20 z-30 bg-white/80 backdrop-blur-md">
            <div className="flex items-center gap-4">
              <button
                onClick={handleSelectAll}
                className="text-sm font-medium text-[#0066CC] hover:text-[#0052A3] transition-colors"
              >
                {selectedPhotos.size > 0 && selectedPhotos.size === photos.length ? 'Deselect All' : 'Select All'}
              </button>
        {selectedPhotos.size > 0 && (
                <p className="text-sm text-[#1D1D1F]/60">
                  {selectedPhotos.size} selected
            </p>
              )}
            </div>

            {selectedPhotos.size > 0 && (
            <button
              onClick={handleDeleteSelected}
              className="px-4 py-2 bg-red-50 border border-red-200 text-red-600 rounded-full text-sm font-medium hover:bg-red-100 transition-all flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
                Delete Selected
            </button>
            )}
          </div>
        )}

        {/* Photos Grid or Layout */}
        {displayedPhotos.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-8 h-8 text-[#0066CC]" />
            </div>
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">
              {filterFavorites ? 'No favorites yet' : 'No photos yet'}
            </h3>
            <p className="text-[#1D1D1F]/60">
              {filterFavorites ? 'Photos favorited by clients will appear here' : 'Use the upload section above to add your first photo'}
            </p>
            {galleryLayout && (
              <p className="text-sm text-[#0066CC] mt-3">
                This gallery uses the "{galleryLayout.name}" layout (minimum {galleryLayout.total_slots} photos recommended)
              </p>
            )}
          </div>
        ) : galleryLayout && displayedPhotos.length >= galleryLayout.total_slots ? (
          // Use layout renderer if layout is set and enough photos
          <div>
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <p className="text-sm text-[#0066CC] font-medium">
                ✓ Layout Applied: {galleryLayout.name} ({displayedPhotos.length} photos)
              </p>
              <p className="text-xs text-[#0066CC]/70 mt-1">
                Pattern repeats every {galleryLayout.total_slots} photos
              </p>
            </div>
            <GalleryLayoutRenderer
              layout={galleryLayout}
              photos={displayedPhotos}
              onPhotoClick={(_photo, index) => {
                setCurrentPhotoIndex(index);
                setModalOpen(true);
              }}
              onFavoriteToggle={handleToggleFavorite}
              onDownload={handleDownloadPhoto}
              showActions={true}
            />
          </div>
        ) : galleryLayout && displayedPhotos.length < galleryLayout.total_slots ? (
          // Layout is set but not enough photos
          <div>
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <p className="text-sm text-amber-800 font-medium">
                ⏳ Upload {galleryLayout.total_slots - displayedPhotos.length} more photo{galleryLayout.total_slots - displayedPhotos.length !== 1 ? 's' : ''} to activate the "{galleryLayout.name}" layout
              </p>
              <p className="text-xs text-amber-600 mt-1">
                {displayedPhotos.length}/{galleryLayout.total_slots} photos uploaded (pattern will repeat with more photos)
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">{displayedPhotos.map((photo, index) => (
              <div
                key={photo.id}
                className={`relative aspect-square bg-gray-100 rounded-2xl overflow-hidden group ${
                  selectedPhotos.has(photo.id) ? 'ring-4 ring-[#0066CC]' : ''
                }`}
              >
                {/* Selection checkbox */}
                <div 
                  className="absolute top-3 left-3 z-10"
                  onClick={(e) => { e.stopPropagation(); handleSelectPhoto(photo.id); }}
                >
                  <div className={`w-6 h-6 rounded-full border-2 ${
                    selectedPhotos.has(photo.id) 
                      ? 'bg-[#0066CC] border-[#0066CC]' 
                      : 'bg-white border-white/60'
                  } flex items-center justify-center cursor-pointer`}>
                    {selectedPhotos.has(photo.id) && (
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </div>

                <ProgressiveImage
                  src={getImageUrl(photo.thumbnail_url || photo.url)}
                  placeholderSrc={getImageUrl(photo.thumbnail_url || photo.url)} // Fake low-res param or just use thumb
                  alt={photo.filename}
                  className="w-full h-full object-cover cursor-pointer"
                  onClick={() => {
                      // If filtering, we need to find the correct original index for the modal
                      const originalIndex = photos.findIndex(p => p.id === photo.id);
                      openPhotoModal(originalIndex);
                  }}
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
                
                {/* Client Engagement Badge - Shows interest level */}
                {photoEngagement[photo.id] && photoEngagement[photo.id].engagement_score >= 50 && (
                  <div className={`absolute bottom-3 left-3 px-2 py-1 rounded text-xs font-medium backdrop-blur-sm flex items-center gap-1 ${
                    photoEngagement[photo.id].engagement_score >= 80
                      ? 'bg-green-500/90 text-white'
                      : 'bg-blue-500/90 text-white'
                  }`}>
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    {photoEngagement[photo.id].engagement_score >= 80 ? 'High' : 'Good'} Interest
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
                </div>

                {/* Hover Overlay */}
                <div 
                  className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 cursor-pointer pointer-events-none"
                  onClick={() => openPhotoModal(index)}
                >
                  <div className="absolute bottom-0 left-0 right-0 p-4 flex items-end justify-between">
                    {/* Left: Status */}
                    <p className="text-white/90 text-xs font-medium drop-shadow-md">
                      {photo.status === 'approved' ? '✓ Approved' :
                       photo.status === 'active' ? 'Ready' : ''}
                    </p>

                    {/* Right: Stats */}
                    <div className="flex items-center gap-4">
                      {/* Favorites count - showing count only, heart icon is in top-right */}
                      {(gallery?.settings?.favorites_enabled ?? true) && (photo.favorites_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.favorites_count} likes</span>
                        </div>
                      )}
                      {/* Comments count */}
                      {(gallery?.allow_comments ?? true) && (photo.comments_count || 0) > 0 && (
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
          </div>
        ) : (
          // Default grid view (no layout or enough photos for layout)
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {displayedPhotos.map((photo, index) => (
              <div
                key={photo.id}
                className={`relative aspect-square bg-gray-100 rounded-2xl overflow-hidden group ${
                  selectedPhotos.has(photo.id) ? 'ring-4 ring-[#0066CC]' : ''
                }`}
              >
                {/* Selection checkbox */}
                <div 
                  className="absolute top-3 left-3 z-10"
                  onClick={(e) => { e.stopPropagation(); handleSelectPhoto(photo.id); }}
                >
                  <div className={`w-6 h-6 rounded-full border-2 ${
                    selectedPhotos.has(photo.id) 
                      ? 'bg-[#0066CC] border-[#0066CC]' 
                      : 'bg-white border-white/60'
                  } flex items-center justify-center cursor-pointer`}>
                    {selectedPhotos.has(photo.id) && (
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </div>

                {/* Play icon for videos */}
                {photo.type === 'video' && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-16 h-16 bg-black/40 backdrop-blur-sm rounded-full flex items-center justify-center">
                      <PlayCircle className="w-10 h-10 text-white" />
                    </div>
                  </div>
                )}

                {/* Favorite Heart - Top Right */}
                <div className="absolute top-3 right-3 z-10">
                  <button
                    onClick={() => handleToggleFavorite(photo.id)}
                    className={`p-2 rounded-full transition-all ${
                      photo.is_favorite
                        ? 'bg-red-500 text-white'
                        : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30'
                    }`}
                    aria-label={photo.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                  >
                    <Heart className={`w-4 h-4 ${photo.is_favorite ? 'fill-current' : ''}`} />
                  </button>
                </div>

                {/* Hover Overlay */}
                <div 
                  className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 cursor-pointer pointer-events-none"
                  onClick={() => openPhotoModal(index)}
                >
                  <div className="absolute bottom-0 left-0 right-0 p-4 flex items-end justify-between">
                    {/* Left: Status */}
                    <p className="text-white/90 text-xs font-medium drop-shadow-md">
                      {photo.status === 'approved' ? '✓ Approved' :
                       photo.status === 'active' ? 'Ready' : ''}
                    </p>

                    {/* Right: Stats */}
                    <div className="flex items-center gap-4">
                      {/* Favorites count - showing count only, heart icon is in top-right */}
                      {(gallery?.settings?.favorites_enabled ?? true) && (photo.favorites_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.favorites_count} likes</span>
                        </div>
                      )}
                      {/* Comments count */}
                      {(gallery?.allow_comments ?? true) && (photo.comments_count || 0) > 0 && (
                        <div className="flex items-center gap-1.5">
                          <MessageCircle className="w-4 h-4 text-white drop-shadow-md" />
                          <span className="text-white text-xs font-medium drop-shadow-md">{photo.comments_count}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Image */}
                <ProgressiveImage
                  src={photo.medium_url || photo.url}
                  placeholderSrc={photo.thumbnail_url}
                  alt={photo.filename || `Photo ${index + 1}`}
                  onClick={() => openPhotoModal(index)}
                  className="cursor-pointer"
                />
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
      </main>

      {/* Photo Modal */}
      {modalOpen && currentPhoto && (
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
                  onClick={closeModal}
                  className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-full backdrop-blur-md transition-colors border border-white/10"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
                <span className="text-white/90 font-medium text-sm tracking-wide bg-black/30 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
                  {currentPhotoIndex + 1} / {photos.length}
                </span>
             </div>
             
             {/* Desktop Actions - REMOVED for TikTok Style */}
             <div className="hidden lg:flex items-center gap-3 opacity-0 pointer-events-none">
             </div>
          </div>

          {/* Main Layout Container */}
          <div 
             className="w-full h-[100dvh] flex flex-col items-center justify-center relative overflow-hidden" 
             onClick={() => {
                 setShowControls(prev => !prev);
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
                  key={`blur-${currentPhoto.id}`}
                  src={getImageUrl(currentPhoto.thumbnail_url || currentPhoto.url)}
                  placeholderSrc=""
                  alt=""
                  className="w-full h-full object-cover blur-2xl opacity-40 scale-110 transition-opacity duration-500" 
                />
                <div className="absolute inset-0 bg-black/20" />
             </div>

            {/* Image/Video Area */}
             <div 
                className={`relative z-10 max-w-full max-h-full flex items-center justify-center ${currentPhoto.type === 'video' ? '' : 'cursor-pointer'} ${slideDirection === 'up' ? 'animate-slide-up' : slideDirection === 'down' ? 'animate-slide-down' : ''}`}
                style={{ 
                    width: (currentPhoto.width || imgDims?.width) ? 'auto' : '100%', 
                    height: (currentPhoto.height || imgDims?.height) ? 'auto' : '100%',
                    aspectRatio: (currentPhoto.width && currentPhoto.height) 
                        ? `${currentPhoto.width} / ${currentPhoto.height}` 
                        : (imgDims ? `${imgDims.width} / ${imgDims.height}` : undefined)
                }}
                key={currentPhoto.id}
                onClick={(e) => {
                    // For videos, click handling is on video element directly
                    if (currentPhoto.type === 'video') {
                      return;
                    }
                    
                    // Image double-tap to favorite
                    e.stopPropagation();
                    const now = Date.now();
                    const doubleTapThreshold = Number(import.meta.env.VITE_DOUBLE_TAP_THRESHOLD) || 300;
                    if (now - lastTap < doubleTapThreshold) {
                        handleToggleFavorite(currentPhoto.id);
                    } else {
                        setShowControls(prev => !prev);
                    }
                    setLastTap(now);
                }}
             >
              {currentPhoto.type === 'video' ? (
                /* TikTok-style Video Player - Click to play/pause, auto-play on scroll */
                <div className="relative w-full h-full flex items-center justify-center">
                  <video
                    ref={videoRef}
                    preload="auto"
                    poster={getImageUrl(currentPhoto.thumbnail_url || '')}
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
                    onPlay={() => setIsVideoPlaying(true)}
                    onPause={() => setIsVideoPlaying(false)}
                  >
                    {/* Use original video URL (not medium_url which is JPEG thumbnail) */}
                    <source src={getImageUrl(currentPhoto.url)} type="video/mp4" />
                    <source src={getImageUrl(currentPhoto.url)} type="video/quicktime" />
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
                    {currentPhoto.comments?.map((comment) => {
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
                /* Image Display */
                <>
              <ProgressiveImage
                src={getImageUrl(currentPhoto.medium_url || currentPhoto.url)}
                placeholderSrc={getImageUrl(currentPhoto.thumbnail_url || currentPhoto.url)}
                alt={currentPhoto.filename}
                className="max-w-full max-h-full object-contain shadow-2xl drop-shadow-2xl"
                onLoad={(e) => {
                    const img = e.currentTarget;
                    if (img.naturalWidth && img.naturalHeight) {
                        setImgDims({ width: img.naturalWidth, height: img.naturalHeight });
                    }
                }}
              />

                  {/* Render Saved Annotations from Comments (Images Only) */}
              {currentPhoto.comments?.map((comment) => {
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
                                d={`M ${points.map((p: any) => `${p.x} ${p.y}`).join(' L ')} Z`}
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
                </>
              )}
            </div>
          </div>

           {/* Bottom Left Text Overlay (TikTok Style) */}
           <div 
              className={`absolute bottom-4 left-4 right-20 z-[1000] transition-all duration-300 transform text-left ${showControls ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}
              onClick={(e) => e.stopPropagation()}
           >
              <h3 className="text-white font-medium text-lg drop-shadow-md truncate w-full mb-1">
                {gallery?.client_name || 'Client'}
              </h3>
              <p className="text-white/90 text-sm drop-shadow-md line-clamp-2">
                {currentPhoto.filename}
              </p>
           </div>

          {/* Mobile Comments/Insights Sheet (Photographer View) */}
          <div 
            className={`absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl transition-transform duration-300 z-[3000] flex flex-col h-[70%] ${showMobileComments ? 'translate-y-0' : 'translate-y-[120%]'}`}
            onClick={(e) => e.stopPropagation()}
          >
             {/* Tabs Header */}
             <div className="flex items-center border-b border-gray-200">
                <button 
                  onClick={() => setShowInsights(false)} 
                  className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${!showInsights ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600'}`}
                >
                  Comments ({currentPhoto.comments?.length || 0})
                </button>
                <button 
                  onClick={() => setShowInsights(true)} 
                  className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${showInsights ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600'}`}
                >
                  Client Insights
                </button>
                <button onClick={() => setShowMobileComments(false)} className="p-2 mr-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors">
                    <X className="w-5 h-5 text-[#1D1D1F]" />
                </button>
             </div>
             
             {/* Tab Content */}
             <div className="flex-1 overflow-y-auto p-4">
                {showInsights ? (
                  <ClientInsights
                    photoId={currentPhoto.id}
                    engagement={photoEngagement[currentPhoto.id] || null}
                    isVideo={currentPhoto.type === 'video'}
                    videoDuration={videoRef.current?.duration}
                    currentVideoTime={videoRef.current?.currentTime}
                    onSeekVideo={(time) => {
                      if (videoRef.current) {
                        videoRef.current.currentTime = time;
                        setVideoProgress((time / videoRef.current.duration) * 100);
                      }
                    }}
                  />
                ) : (
                <CommentSection
                  photoId={currentPhoto.id}
                  comments={currentPhoto.comments || []}
                  onCommentsChange={handleCommentsChange}
                  allowComments={gallery?.allow_comments || true}
                  isGalleryOwner={true}
                />
                )}
             </div>
          </div>

          {/* Right Side Vertical Stack (TikTok Style - Universal) */}
          <div 
             className={`absolute bottom-40 right-4 z-[2000] transition-all duration-300 transform ${showControls ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8 pointer-events-none'}`}
             onClick={(e) => e.stopPropagation()}
          >
              <div className="flex flex-col items-center gap-6">
                  
                  {/* Like */}
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={() => handleToggleFavorite(currentPhoto.id)}
                        className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        <Heart className={`w-7 h-7 text-white ${currentPhoto.is_favorite ? 'fill-red-500 text-red-500' : ''}`} />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">
                        {currentPhoto.favorites_count || 0}
                    </span>
                  </div>

                  {/* Comments Trigger */}
                   {(gallery?.allow_comments ?? true) && (
                      <div className="flex flex-col items-center gap-1">
                        <button 
                            onClick={(e) => { e.stopPropagation(); setShowMobileComments(prev => !prev); }}
                            className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform relative"
                        >
                            <MessageCircle className="w-7 h-7" />
                        </button>
                        <span className="text-white text-xs font-medium drop-shadow-md">
                            {currentPhoto.comments_count || 0}
                        </span>
                      </div>
                  )}

                  {/* Share */}
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={handleShareGallery}
                        className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        <Share2 className="w-7 h-7" />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">Share</span>
                  </div>
                  
                  {/* Pencil (Edit/Settings) */}
                  <div className="flex flex-col items-center gap-1">
                    <button 
                        onClick={() => setSettingsModalOpen(true)}
                        className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                    >
                        <Pencil className="w-7 h-7" />
                    </button>
                    <span className="text-white text-xs font-medium drop-shadow-md">Edit</span>
                  </div>

                  {gallery?.allow_downloads && (
                    <div className="flex flex-col items-center gap-1">
                      <button 
                          onClick={handleDownloadPhoto}
                          className="p-3 bg-black/40 backdrop-blur-md rounded-full text-white shadow-lg border border-white/10 active:scale-95 transition-transform"
                      >
                          <Download className="w-7 h-7" />
                      </button>
                      <span className="text-white text-xs font-medium drop-shadow-md">Save</span>
                    </div>
                 )}
             </div>
          </div>
        </div>
      )}

      {/* Settings Modal - Full Screen Apple Design */}
      {settingsModalOpen && (
        <div className="fixed inset-0 bg-[#F5F5F7] z-[20000] animate-in fade-in duration-300">
          <div className="h-full flex flex-col">
            {/* Top Navigation Bar */}
            <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 px-6 py-4">
              <div className="max-w-7xl mx-auto flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSettingsModalOpen(false)}
                    className="p-2 hover:bg-gray-100 rounded-full transition-all"
                  >
                    <X className="w-5 h-5 text-[#1D1D1F]" />
                  </button>
                  <div>
                    <h1 className="text-xl font-semibold text-[#1D1D1F]">Gallery Settings</h1>
                    <p className="text-sm text-[#1D1D1F]/60">{gallery.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSettingsModalOpen(false)}
                    className="px-5 py-2.5 text-[#1D1D1F] hover:bg-gray-100 rounded-full font-medium transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveSettings}
                    className="px-5 py-2.5 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all shadow-sm"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </div>

            {/* Content Area - Two Column Layout */}
            <div className="flex-1 overflow-hidden">
              <div className="h-full max-w-7xl mx-auto px-6 py-8">
                <div className="h-full grid grid-cols-12 gap-8">
                  
                  {/* Left Content - Settings Forms */}
                  <div className="col-span-12 lg:col-span-8 overflow-y-auto space-y-8 pr-4">
                    
                    {/* Gallery Details */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Gallery Details</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-6">
                        <div>
                          <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                            Gallery Name
                          </label>
                          <input
                            type="text"
                            value={settingsForm.name}
                            onChange={(e) => setSettingsForm({ ...settingsForm, name: e.target.value })}
                            className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                            Client Name
                          </label>
                          <input
                            type="text"
                            value={settingsForm.client_name}
                            onChange={(e) => setSettingsForm({ ...settingsForm, client_name: e.target.value })}
                            className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                            Description
                          </label>
                          <textarea
                            value={settingsForm.description}
                            onChange={(e) => setSettingsForm({ ...settingsForm, description: e.target.value })}
                            rows={4}
                            className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                            placeholder="Share details about this gallery..."
                          />
                        </div>
                      </div>
                    </section>

                    {/* Gallery Layout */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Gallery Layout</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50">
                        <GalleryLayoutSelector
                          selectedLayoutId={settingsForm.layout_id}
                          onSelectLayout={(layoutId: string) => {
                            setSettingsForm({ ...settingsForm, layout_id: layoutId });
                          }}
                          inline={true}
                        />
                      </div>
                    </section>

                    {/* Privacy & Access */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Privacy & Access</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-6">
                        <div>
                          <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                            Privacy Setting
                          </label>
                          <select
                            value={settingsForm.privacy}
                            onChange={(e) => setSettingsForm({ ...settingsForm, privacy: e.target.value })}
                            className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F] cursor-pointer"
                          >
                            <option value="private">Private - Link only</option>
                            <option value="public">Public - Listed</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                            Password Protection
                          </label>
                          <input
                            type="text"
                            value={settingsForm.password}
                            onChange={(e) => setSettingsForm({ ...settingsForm, password: e.target.value })}
                            placeholder="Leave empty for no password"
                            className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                          />
                          <p className="mt-2 text-xs text-[#1D1D1F]/60">Optional password for extra security</p>
                        </div>
                      </div>
                    </section>

                    {/* Client Emails */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Client Access</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-4">
                        {settingsForm.client_emails.length > 0 && (
                          <div className="space-y-2 mb-4">
                            {settingsForm.client_emails.map((email) => (
                              <div key={email} className="flex items-center justify-between p-3 bg-[#F5F5F7] rounded-xl group hover:bg-gray-100 transition-all">
                                <span className="text-sm text-[#1D1D1F] font-medium">{email}</span>
                                <button
                                  onClick={() => handleRemoveClientEmail(email)}
                                  className="text-[#1D1D1F]/40 hover:text-red-600 text-sm font-medium px-3 py-1 rounded-lg hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
                                >
                                  Remove
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="flex gap-2">
                          <input
                            type="email"
                            value={newClientEmail}
                            onChange={(e) => setNewClientEmail(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddClientEmail())}
                            placeholder="client@example.com"
                            className="flex-1 px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                          />
                          <button
                            onClick={handleAddClientEmail}
                            className="px-6 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all shadow-sm"
                          >
                            Add
                          </button>
                        </div>
                        <p className="text-xs text-[#1D1D1F]/60">Add client email addresses to grant access to this gallery</p>
                      </div>
                    </section>

                    {/* Tags */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Organization</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-4">
                        {settingsForm.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-4">
                            {settingsForm.tags.map((tag) => (
                              <div key={tag} className="flex items-center gap-2 px-4 py-2 bg-[#F5F5F7] rounded-full group hover:bg-gray-100 transition-all">
                                <span className="text-sm text-[#1D1D1F] font-medium">#{tag}</span>
                                <button
                                  onClick={() => handleRemoveTag(tag)}
                                  className="text-[#1D1D1F]/40 hover:text-red-600 transition-colors"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                            placeholder="wedding, outdoor, portrait..."
                            className="flex-1 px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                          />
                          <button
                            onClick={handleAddTag}
                            className="px-6 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all shadow-sm"
                          >
                            Add
                          </button>
                        </div>
                        <p className="text-xs text-[#1D1D1F]/60">Tags help you organize and search your galleries</p>
                      </div>
                    </section>

                    {/* Client Permissions */}
                    <section>
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Client Permissions</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-3">
                        <label className="flex items-center justify-between p-4 bg-[#F5F5F7] rounded-xl cursor-pointer hover:bg-gray-100 transition-all">
                          <div className="flex items-center gap-4">
                            <div className={`w-11 h-6 rounded-full transition-all ${settingsForm.allow_downloads ? 'bg-[#0066CC]' : 'bg-gray-300'}`}>
                              <div className={`w-5 h-5 bg-white rounded-full shadow-sm transition-all mt-0.5 ${settingsForm.allow_downloads ? 'ml-5' : 'ml-0.5'}`} />
                            </div>
                            <div>
                              <p className="font-medium text-[#1D1D1F]">Allow Downloads</p>
                              <p className="text-xs text-[#1D1D1F]/60">Clients can download high-resolution photos</p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={settingsForm.allow_downloads}
                            onChange={(e) => setSettingsForm({ ...settingsForm, allow_downloads: e.target.checked })}
                            className="sr-only"
                          />
                        </label>
                        
                        <label className="flex items-center justify-between p-4 bg-[#F5F5F7] rounded-xl cursor-pointer hover:bg-gray-100 transition-all">
                          <div className="flex items-center gap-4">
                            <div className={`w-11 h-6 rounded-full transition-all ${settingsForm.allow_comments ? 'bg-[#0066CC]' : 'bg-gray-300'}`}>
                              <div className={`w-5 h-5 bg-white rounded-full shadow-sm transition-all mt-0.5 ${settingsForm.allow_comments ? 'ml-5' : 'ml-0.5'}`} />
                            </div>
                            <div>
                              <p className="font-medium text-[#1D1D1F]">Enable Comments</p>
                              <p className="text-xs text-[#1D1D1F]/60">Clients can leave comments on photos</p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={settingsForm.allow_comments}
                            onChange={(e) => setSettingsForm({ ...settingsForm, allow_comments: e.target.checked })}
                            className="sr-only"
                          />
                        </label>
                        
                        <label 
                          className="flex items-center justify-between p-4 bg-[#F5F5F7] rounded-xl cursor-pointer hover:bg-gray-100 transition-all"
                          onClick={async (e) => {
                            // Check if user is on free plan and trying to enable
                            if (user?.plan === 'free' && !settingsForm.allow_edits) {
                              e.preventDefault();
                              const confirmed = await showConfirm(
                                'Upgrade Required',
                                'Edit requests are available on paid plans.',
                                'Upgrade',
                                'Cancel'
                              );
                              if (confirmed) {
                                navigate('/billing');
                              }
                              return;
                            }
                          }}
                        >
                          <div className="flex items-center gap-4">
                            <div className={`w-11 h-6 rounded-full transition-all ${settingsForm.allow_edits ? 'bg-[#0066CC]' : 'bg-gray-300'}`}>
                              <div className={`w-5 h-5 bg-white rounded-full shadow-sm transition-all mt-0.5 ${settingsForm.allow_edits ? 'ml-5' : 'ml-0.5'}`} />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-[#1D1D1F]">Allow Edit Requests</p>
                                {user?.plan === 'free' && (
                                  <span className="text-xs bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-2 py-0.5 rounded-full font-semibold">
                                    STARTER+
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-[#1D1D1F]/60">Clients can request photo edits</p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={settingsForm.allow_edits}
                            onChange={(e) => {
                              // Only allow toggle if not free plan
                              if (user?.plan !== 'free') {
                                setSettingsForm({ ...settingsForm, allow_edits: e.target.checked });
                              }
                            }}
                            disabled={user?.plan === 'free' && !settingsForm.allow_edits}
                            className="sr-only"
                          />
                        </label>
                      </div>
                    </section>

                    {/* SEO Settings (Pro/Ultimate) */}
                    {(user?.plan === 'pro' || user?.plan === 'ultimate') && (
                      <section>
                        <div className="flex items-center justify-between mb-6">
                          <h2 className="text-2xl font-semibold text-[#1D1D1F]">Search Optimization</h2>
                          <span className="text-xs bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-3 py-1 rounded-full font-semibold">PRO</span>
                        </div>
                        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50 space-y-6">
                          <div>
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">URL Slug</label>
                            <div className="flex items-stretch overflow-hidden rounded-xl border border-gray-200">
                              <span className="text-sm text-[#1D1D1F]/60 bg-[#F5F5F7] px-4 py-3 border-r border-gray-200 flex items-center">galerly.com/gallery/</span>
                              <input 
                                type="text" 
                                value={settingsForm.seo.slug}
                                onChange={(e) => setSettingsForm({ ...settingsForm, seo: { ...settingsForm.seo, slug: e.target.value } })}
                                className="flex-1 px-4 py-3 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-[#0066CC] text-[#1D1D1F]"
                                placeholder="my-gallery-name"
                              />
                            </div>
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Meta Title</label>
                            <input 
                              type="text" 
                              value={settingsForm.seo.title}
                              onChange={(e) => setSettingsForm({ ...settingsForm, seo: { ...settingsForm.seo, title: e.target.value } })}
                              className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                              placeholder="Gallery Title - Photographer Name"
                            />
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Meta Description</label>
                            <textarea 
                              value={settingsForm.seo.description}
                              onChange={(e) => setSettingsForm({ ...settingsForm, seo: { ...settingsForm.seo, description: e.target.value } })}
                              rows={3}
                              className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent transition-all text-[#1D1D1F]"
                              placeholder="View beautiful photos from..."
                            />
                          </div>
                        </div>
                      </section>
                    )}

                    {/* Advanced Actions (Ultimate) */}
                    {user?.plan === 'ultimate' && (
                      <section>
                        <div className="flex items-center justify-between mb-6">
                          <h2 className="text-2xl font-semibold text-[#1D1D1F]">Advanced Actions</h2>
                          <span className="text-xs bg-gradient-to-r from-gray-900 to-gray-700 text-white px-3 py-1 rounded-full font-semibold">ULTIMATE</span>
                        </div>
                        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50">
                          <button
                            onClick={handleArchiveOriginals}
                            className="w-full px-5 py-4 bg-[#F5F5F7] border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-100 transition-all flex items-center justify-center gap-2"
                          >
                            <Download className="w-5 h-5" />
                            Archive Originals to Vault (Glacier)
                          </button>
                          <p className="mt-3 text-xs text-center text-[#1D1D1F]/60">Moves original RAW/High-Res files to cold storage</p>
                        </div>
                      </section>
                    )}

                    {/* Danger Zone */}
                    <section className="pb-8">
                      <h2 className="text-2xl font-semibold text-[#1D1D1F] mb-6">Danger Zone</h2>
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-red-200/50">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-[#1D1D1F] mb-1">Delete Gallery</h3>
                            <p className="text-sm text-[#1D1D1F]/60">Permanently remove this gallery and all its photos</p>
                          </div>
                          <button
                            onClick={handleDeleteGallery}
                            className="px-5 py-2.5 bg-red-600 text-white rounded-xl font-medium hover:bg-red-700 transition-all shadow-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </section>

                  </div>

                  {/* Right Sidebar - Info & Preview */}
                  <div className="col-span-12 lg:col-span-4 overflow-y-auto">
                    <div className="sticky top-0 space-y-6">
                      
                      {/* Gallery Info Card */}
                      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200/50">
                        <h3 className="font-semibold text-[#1D1D1F] mb-4">Gallery Info</h3>
                        <div className="space-y-3 text-sm">
                          <div className="flex justify-between">
                            <span className="text-[#1D1D1F]/60">Photos</span>
                            <span className="font-medium text-[#1D1D1F]">{gallery.photo_count || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#1D1D1F]/60">Created</span>
                            <span className="font-medium text-[#1D1D1F]">{new Date(gallery.created_at).toLocaleDateString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#1D1D1F]/60">Status</span>
                            <span className={`font-medium ${gallery.privacy === 'public' ? 'text-green-600' : 'text-[#0066CC]'}`}>
                              {gallery.privacy === 'public' ? 'Public' : 'Private'}
                            </span>
                          </div>
                          {gallery.views !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-[#1D1D1F]/60">Views</span>
                              <span className="font-medium text-[#1D1D1F]">{gallery.views || 0}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Quick Tips */}
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100/50">
                        <h3 className="font-semibold text-[#1D1D1F] mb-3">Tips</h3>
                        <ul className="space-y-2 text-sm text-[#1D1D1F]/80">
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600 mt-0.5">•</span>
                            <span>Use tags to organize galleries by event type</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600 mt-0.5">•</span>
                            <span>Automated selection reminders</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600 mt-0.5">•</span>
                            <span>Client download tracking and reminders</span>
                          </li>
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600 mt-0.5">•</span>
                            <span>Add client emails for automatic notifications</span>
                          </li>
                        </ul>
                      </div>

                    </div>
                  </div>

                </div>
              </div>
            </div>

          </div>
        </div>
      )}
      {/* Duplicate Modal */}
      <DuplicateResolutionModal
        isOpen={duplicateModalOpen}
        onClose={() => {
            setDuplicateModalOpen(false);
            // If closed without action, we skip? Or just stop queue?
            // Let's assume closing means skip current and continue
            handleDuplicateResolve('skip');
        }}
        newFile={duplicateFile!}
        duplicates={duplicateMatches}
        onResolve={handleDuplicateResolve}
      />

      {/* Share Modal */}
      <ShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        galleryId={galleryId!}
        title={gallery?.name}
      />

      {/* Analytics Dashboard Modal */}
      {analyticsModalOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-semibold text-gray-900">Gallery Insights</h2>
              <button
                onClick={() => setAnalyticsModalOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-6 h-6 text-gray-600" />
              </button>
            </div>
            
            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <GalleryInsightsDashboard
                galleryId={galleryId!}
                photos={photos.map(p => ({
                  id: p.id,
                  filename: p.filename,
                  thumbnail_url: p.thumbnail_url,
                  url: p.url,
                  type: p.type
                }))}
              />
            </div>
          </div>
        </div>
      )}

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}
