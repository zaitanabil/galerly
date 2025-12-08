/* eslint-disable @typescript-eslint/no-explicit-any */
// Client service - handles client-related operations
import { api } from '../utils/api';
import { Gallery } from './galleryService';
import { Photo } from './photoService';

export interface ClientGallery extends Gallery {
  photos?: Photo[];
}

export interface Favorite {
  id: string;
  photo_id: string;
  gallery_id: string;
  client_identifier: string;
  created_at: string;
}

export interface Feedback {
  id: string;
  gallery_id: string;
  client_name?: string;
  client_email?: string;
  rating?: number;
  comment?: string;
  created_at: string;
}

// Get client galleries (for logged-in clients)
export async function getClientGalleries(params?: { page?: number; limit?: number }) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  
  const queryString = queryParams.toString();
  const endpoint = queryString ? `/client/galleries?${queryString}` : '/client/galleries';
  
  return api.get<{ galleries: ClientGallery[]; total: number }>(endpoint);
}

// Get client gallery (for logged-in clients or public with token)
export async function getClientGallery(galleryId: string, params?: { page_size?: number; last_key?: any; token?: string }) {
  // If token is provided, use the public token endpoint
  if (params?.token) {
    return getClientGalleryByToken(params.token, {
      page_size: params.page_size,
      last_key: params.last_key
    });
  }

  const queryParams = new URLSearchParams();
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.last_key) queryParams.append('last_key', JSON.stringify(params.last_key));
  
  const queryString = queryParams.toString();
  return api.get<ClientGallery & { pagination?: any }>(`/client/galleries/${galleryId}${queryString ? `?${queryString}` : ''}`);
}

// Get client gallery by share token (public access)
export async function getClientGalleryByToken(shareToken: string, params?: { page_size?: number; last_key?: any }) {
  const queryParams = new URLSearchParams();
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.last_key) queryParams.append('last_key', JSON.stringify(params.last_key));
  
  const queryString = queryParams.toString();
  return api.get<ClientGallery & { pagination?: any }>(`/client/galleries/by-token/${shareToken}${queryString ? `?${queryString}` : ''}`);
}

// Client favorites
export async function addFavorite(photoId: string, galleryId: string, clientEmail?: string, clientName?: string, shareToken?: string) {
  const body: any = {
    photo_id: photoId,
    gallery_id: galleryId,
  };
  if (clientEmail) body.client_email = clientEmail;
  if (clientName) body.client_name = clientName;
  if (shareToken) body.token = shareToken;

  return api.post<Favorite>('/client/favorites', body);
}

export async function removeFavorite(photoId: string, clientEmail?: string) {
  const body: any = { photo_id: photoId };
  if (clientEmail) body.client_email = clientEmail;
  
  return api.delete('/client/favorites', body);
}

export async function getFavorites(galleryId: string) {
  return api.get<{ favorites: Favorite[] }>(`/client/favorites?gallery_id=${galleryId}`);
}

export async function checkFavorite(photoId: string, galleryId: string) {
  return api.get<{ is_favorite: boolean; favorite_id?: string }>(
    `/client/favorites/${photoId}?gallery_id=${galleryId}`
  );
}

// Client feedback
export async function submitFeedback(galleryId: string, data: {
  client_name?: string;
  client_email?: string;
  rating?: number;
  comment?: string;
}) {
  return api.post<Feedback>(`/client/feedback/${galleryId}`, data);
}

export async function getGalleryFeedback(galleryId: string) {
  return api.get<{ feedback: Feedback[] }>(`/client/feedback/${galleryId}`);
}

// Bulk download
export async function bulkDownload(galleryId: string, photoIds?: string[]) {
  // Backend expects POST to /galleries/{id}/download-bulk
  return api.post<{ download_url: string; photo_count?: number }>(`/galleries/${galleryId}/download-bulk`, {
    photo_ids: photoIds, // Currently backend ignores this and downloads all, but keeping for future
  });
}

export async function bulkDownloadByToken(shareToken: string, photoIds?: string[]) {
  return api.post<{ download_url: string; photo_count?: number }>('/downloads/bulk/by-token', {
    token: shareToken, // Backend expects 'token'
    photo_ids: photoIds,
  });
}

// Send selection reminder
export async function sendSelectionReminder(galleryId: string) {
  return api.post('/notifications/send-selection-reminder', {
    gallery_id: galleryId,
  });
}

export async function submitFavorites(galleryId: string, clientEmail?: string) {
  const body: any = { gallery_id: galleryId };
  if (clientEmail) body.client_email = clientEmail;
  return api.post<{ success: boolean; message: string; count: number }>('/client/favorites/submit', body);
}

export default {
  getClientGalleries,
  getClientGallery,
  getClientGalleryByToken,
  addFavorite,
  removeFavorite,
  getFavorites,
  checkFavorite,
  submitFavorites,
  submitFeedback,
  getGalleryFeedback,
  bulkDownload,
  bulkDownloadByToken,
};

