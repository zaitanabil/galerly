import { api } from '../utils/api';

// Real-time viewer tracking service
// Sends heartbeat to backend to maintain active viewer status

export interface ViewerLocation {
  city: string;
  region: string;
  country: string;
  country_code: string;
  latitude: number;
  longitude: number;
}

export interface ActiveViewer {
  viewer_id: string;
  gallery_id?: string;
  gallery_name?: string;
  page_type: 'gallery' | 'portfolio' | 'client_gallery';
  location: ViewerLocation;
  duration: number; // seconds
}

export interface ActiveViewersResponse {
  viewers: ActiveViewer[];
  total_active: number;
  by_country: Record<string, number>;
  by_gallery: Record<string, number>;
  last_updated: string;
}

// Send heartbeat to maintain active status
export async function sendViewerHeartbeat(params: {
  viewer_id?: string;
  gallery_id?: string;
  page_type: 'gallery' | 'portfolio' | 'client_gallery';
  gallery_name?: string;
}) {
  try {
    const response = await api.post('/viewers/heartbeat', params);
    return response;
  } catch (error) {
    console.error('Failed to send viewer heartbeat:', error);
    return { success: false };
  }
}

// Get all active viewers (for photographers)
export async function getActiveViewers(): Promise<ActiveViewersResponse | null> {
  try {
    const response = await api.get<ActiveViewersResponse>('/viewers/active');
    return response.data || null;
  } catch (error) {
    console.error('Failed to get active viewers:', error);
    return null;
  }
}

// Notify backend when viewer disconnects
export async function notifyViewerDisconnect(viewer_id: string) {
  try {
    await api.post('/viewers/disconnect', { viewer_id });
  } catch (error) {
    // Don't log errors on disconnect - connection may already be closed
  }
}
