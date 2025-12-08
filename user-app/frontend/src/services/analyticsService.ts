import { api } from '../utils/api';

// Client engagement analytics service
// Provides photographers with insights into client behavior and preferences

export interface VideoEngagementEvent {
  photo_id: string;
  gallery_id: string;
  client_id?: string;
  event_type: 'play' | 'pause' | 'seek' | 'rewatch' | 'complete';
  timestamp: number; // Video timestamp where event occurred
  session_time: number; // How long into the viewing session
  event_time: string; // ISO timestamp
}

export interface PhotoEngagementEvent {
  photo_id: string;
  gallery_id: string;
  client_id?: string;
  event_type: 'view' | 'zoom' | 'download' | 'favorite' | 'share';
  duration: number; // Time spent viewing
  event_time: string;
}

export interface ClientEngagementSummary {
  photo_id: string;
  total_views: number;
  total_time_spent: number; // seconds
  avg_view_duration: number;
  rewatch_count: number;
  favorite_count: number;
  download_count: number;
  share_count: number;
  engagement_score: number; // 0-100
  hot_moments?: HotMoment[]; // For videos
  client_comments?: number;
  last_viewed: string;
}

export interface HotMoment {
  start_time: number;
  end_time: number;
  intensity: number; // 0-100, based on pauses, rewinds, time spent
  event_count: number;
  events: string[]; // ['pause', 'rewind', 'pause']
}

export interface ClientPreferences {
  client_id: string;
  preferred_styles: string[]; // e.g., ['close-up', 'candid', 'landscape']
  color_preferences: string[]; // e.g., ['warm', 'high-contrast']
  engagement_pattern: 'quick_browser' | 'detailed_reviewer' | 'selective_engager';
  avg_time_per_photo: number;
  favorite_photo_types: string[]; // e.g., ['portrait', 'group', 'detail']
  decision_speed: 'fast' | 'moderate' | 'slow';
}

// Track video engagement event
export async function trackVideoEngagement(
  galleryId: string,
  photoId: string,
  eventType: 'play' | 'pause' | 'seek' | 'rewatch' | 'complete' | 'download',
  timestamp: number,
  sessionTime: number
) {
  try {
    return await api.post('/analytics/video-engagement', {
      gallery_id: galleryId,
      photo_id: photoId,
      event_type: eventType,
      timestamp,
      session_time: sessionTime,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track video engagement:', error);
  }
}

// Track visitor visit (page view)
export async function trackVisit(galleryId: string, metadata?: {
  path?: string;
  referrer?: string;
  screen_width?: number;
  screen_height?: number;
}) {
  try {
    return await api.post('/analytics/visit', {
      gallery_id: galleryId,
      ...metadata,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track visit:', error);
  }
}

// Track general event
export async function trackEvent(galleryId: string, eventType: string, metadata?: Record<string, any>) {
  try {
    return await api.post('/analytics/event', {
      gallery_id: galleryId,
      event_type: eventType,
      ...metadata,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track event:', error);
  }
}

// Track photo share
export async function trackPhotoShare(photoId: string, platform: string) {
  try {
    return await api.post('/analytics/photo-share', {
      photo_id: photoId,
      platform,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track photo share:', error);
  }
}

// Track gallery share
export async function trackGalleryShare(galleryId: string, platform: string) {
  try {
    return await api.post('/analytics/gallery-share', {
      gallery_id: galleryId,
      platform,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track gallery share:', error);
  }
}

// Track photo engagement
export async function trackPhotoEngagement(
  galleryId: string,
  photoId: string,
  eventType: 'view' | 'zoom' | 'download' | 'favorite' | 'share',
  duration: number
) {
  try {
    return await api.post('/analytics/photo-engagement', {
      gallery_id: galleryId,
      photo_id: photoId,
      event_type: eventType,
      duration,
      event_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to track photo engagement:', error);
  }
}

// Get engagement summary for a photo/video
export async function getPhotoEngagement(photoId: string): Promise<ClientEngagementSummary | null> {
  try {
    const response = await api.get<ClientEngagementSummary>(`/analytics/photos/${photoId}/engagement`);
    return response.data || null;
  } catch (error) {
    console.error('Failed to get photo engagement:', error);
    return null;
  }
}

// Get engagement summary for entire gallery
export async function getGalleryEngagement(galleryId: string): Promise<ClientEngagementSummary[]> {
  try {
    const response = await api.get<ClientEngagementSummary[]>(`/analytics/galleries/${galleryId}/engagement`);
    return response.data || [];
  } catch (error) {
    console.error('Failed to get gallery engagement:', error);
    return [];
  }
}

// Get client preferences based on behavior
export async function getClientPreferences(galleryId: string): Promise<ClientPreferences | null> {
  try {
    const response = await api.get<ClientPreferences>(`/analytics/galleries/${galleryId}/client-preferences`);
    return response.data || null;
  } catch (error) {
    console.error('Failed to get client preferences:', error);
    return null;
  }
}

// Export gallery analytics report
export async function exportGalleryReport(galleryId: string, format: 'pdf' | 'csv' = 'pdf') {
  try {
    const response = await api.get(`/analytics/galleries/${galleryId}/report?format=${format}`, {
      responseType: 'blob'
    } as any);
    
    // Download file
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `gallery-insights-${galleryId}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to export report:', error);
  }
}

// Legacy analytics functions (for backwards compatibility)
export interface AnalyticsData {
  views: number;
  downloads: number;
  shares: number;
  favorites: number;
  comments: number;
  [key: string]: any;
}

export async function getGalleryAnalytics(galleryId: string, startDate?: string, endDate?: string) {
  try {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
    const response = await api.get(`/analytics/galleries/${galleryId}?${params.toString()}`);
    return response; // Return the full ApiResponse {success, data}
  } catch (error) {
    console.error('Failed to get gallery analytics:', error);
    return { success: false, error: 'Failed to get analytics' };
  }
}

export async function getOverallAnalytics(startDate?: string, endDate?: string) {
  try {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
    const response = await api.get(`/analytics/overall?${params.toString()}`);
    return response; // Return the full ApiResponse {success, data}
  } catch (error) {
    console.error('Failed to get overall analytics:', error);
    return { success: false, error: 'Failed to get analytics' };
}
}

export async function getBulkDownloads(galleryId?: string) {
  try {
    const url = galleryId ? `/analytics/bulk-downloads?gallery_id=${galleryId}` : '/analytics/bulk-downloads';
    const response = await api.get(url);
    return response.data || [];
  } catch (error) {
    console.error('Failed to get bulk downloads:', error);
    return [];
  }
}

export async function getVisitorAnalytics(galleryId?: string) {
  try {
    const url = galleryId ? `/analytics/visitors?gallery_id=${galleryId}` : '/analytics/visitors';
    const response = await api.get(url);
    return response.data || {};
  } catch (error) {
    console.error('Failed to get visitor analytics:', error);
    return {};
  }
}

export default {
  trackVideoEngagement,
  trackPhotoEngagement,
  trackVisit,
  trackEvent,
  trackPhotoShare,
  trackGalleryShare,
  getPhotoEngagement,
  getGalleryEngagement,
  getClientPreferences,
  exportGalleryReport,
  getGalleryAnalytics,
  getOverallAnalytics,
  getBulkDownloads,
  getVisitorAnalytics
};
