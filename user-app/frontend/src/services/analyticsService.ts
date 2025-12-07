/* eslint-disable @typescript-eslint/no-explicit-any */
// Analytics service - handles tracking and analytics operations
import { api } from '../utils/api';

export interface AnalyticsData {
  // Core metrics (from backend)
  total_galleries?: number;
  total_views: number;
  total_photo_views?: number;
  total_downloads: number;
  total_bulk_downloads?: number;
  
  // Legacy/Frontend aliases
  views?: number; 
  downloads?: number;
  shares?: number;
  unique_visitors?: number;
  
  // Period info
  period?: {
    start: string;
    end: string;
    days: number;
  };
  
  // Lists
  daily_stats?: Array<{ date: string; views: number; downloads: number }>;
  daily_stats_list?: Array<{ date: string; views: number; downloads: number }>;
  gallery_stats?: Array<{
    gallery_id: string;
    gallery_name: string;
    cover_photo?: string;
  views: number;
    photo_views: number;
  downloads: number;
    bulk_downloads: number;
  }>;
  top_photos?: Array<{
    id: string;
    url?: string;
    thumbnail_url?: string;
    name: string;
    views: number;
    avg_time_seconds: number;
  }>;
  
  // Timeline (legacy)
  timeline?: Array<{ date: string; views: number; downloads: number }>;
  
  // Optional container for metrics if some endpoints wrap it
  metrics?: AnalyticsData;
}

export interface VisitorData {
  visitor_id: string;
  ip?: string;
  user_agent?: string;
  location?: string;
  timestamp: string;
}

// Track gallery view
export async function trackGalleryView(galleryId: string, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/gallery/${galleryId}`, { metadata });
}

// Track photo view
export async function trackPhotoView(photoId: string, galleryId: string, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/photo/${photoId}`, { gallery_id: galleryId, metadata });
}

// Track photo download
export async function trackPhotoDownload(photoId: string, galleryId: string, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/download/${photoId}`, { gallery_id: galleryId, metadata });
}

// Track gallery share
export async function trackGalleryShare(galleryId: string, platform: string, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/share/gallery/${galleryId}`, { platform, metadata });
}

// Track photo share
export async function trackPhotoShare(photoId: string, platform: string, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/share/photo/${photoId}`, { platform, metadata });
}

// Track bulk download
export async function trackBulkDownload(galleryId: string, photoCount: number, metadata?: Record<string, any>) {
  return api.post(`/analytics/track/bulk-download/${galleryId}`, { photo_count: photoCount, metadata });
}

// Get gallery analytics
export async function getGalleryAnalytics(galleryId: string, startDate?: string, endDate?: string) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  
  const queryString = params.toString();
  const endpoint = queryString 
    ? `/analytics/galleries/${galleryId}?${queryString}`
    : `/analytics/galleries/${galleryId}`;
  
  return api.get<AnalyticsData>(endpoint);
}

// Get overall analytics
export async function getOverallAnalytics(startDate?: string, endDate?: string) {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  
  const queryString = params.toString();
  const endpoint = queryString ? `/analytics?${queryString}` : '/analytics';
  
  return api.get<AnalyticsData>(endpoint);
}

// Get bulk download history
export async function getBulkDownloads(galleryId?: string) {
  const endpoint = galleryId ? `/analytics/bulk-downloads?gallery_id=${galleryId}` : '/analytics/bulk-downloads';
  return api.get(endpoint);
}

// Helper to generate UUID
function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older environments
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Helper to get or create IDs
function getIds() {
  let visitorId = localStorage.getItem('galerly_visitor_id');
  if (!visitorId) {
    visitorId = generateUUID();
    localStorage.setItem('galerly_visitor_id', visitorId);
  }

  let sessionId = sessionStorage.getItem('galerly_session_id');
  if (!sessionId) {
    sessionId = generateUUID();
    sessionStorage.setItem('galerly_session_id', sessionId);
  }
  
  return { visitorId, sessionId };
}

// Visitor tracking
export async function trackVisit(galleryId: string, metadata?: Record<string, any>) {
  const { visitorId, sessionId } = getIds();
  
  // Construct payload matching backend expectations
  const payload = {
    session_id: sessionId,
    visitor_id: visitorId,
    page_url: metadata?.path || window.location.pathname,
    referrer: metadata?.referrer || document.referrer,
    user_agent: navigator.userAgent,
    device: {
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        pixel_ratio: window.devicePixelRatio,
    },
    location: {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    },
    metadata: {
        ...metadata,
        gallery_id: galleryId
    }
  };

  return api.post('/visitor/track/visit', payload);
}

export async function trackEvent(galleryId: string, eventType: string, eventData?: Record<string, any>) {
  const { visitorId, sessionId } = getIds();
  
  const payload = {
    session_id: sessionId,
    visitor_id: visitorId,
    event_type: eventType,
    page_url: window.location.pathname,
    metadata: {
        ...eventData,
        gallery_id: galleryId
    }
  };

  return api.post('/visitor/track/event', payload);
}

export async function trackSessionEnd(sessionId: string) {
  return api.post('/visitor/track/session-end', { session_id: sessionId });
}

export async function getVisitorAnalytics(galleryId?: string) {
  const queryString = galleryId ? `?gallery_id=${galleryId}` : '';
  return api.get(`/visitor/analytics${queryString}`);
}

export default {
  trackGalleryView,
  trackPhotoView,
  trackPhotoDownload,
  trackGalleryShare,
  trackPhotoShare,
  trackBulkDownload,
  getGalleryAnalytics,
  getOverallAnalytics,
  getBulkDownloads,
  trackVisit,
  trackEvent,
  trackSessionEnd,
  getVisitorAnalytics,
};

