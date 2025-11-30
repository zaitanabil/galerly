/* eslint-disable @typescript-eslint/no-explicit-any */
// Gallery service - handles all gallery-related API calls
import { api } from '../utils/api';

export interface Gallery {
  id: string;
  galleryId?: string;
  user_id: string;
  name: string;
  description?: string;
  client_name?: string;
  client_email?: string;
  share_token?: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  photo_count?: number;
  view_count?: number;
  download_count?: number;
  expiry_date?: string;
  status?: string;
  cover_photo?: string;
  cover_photo_url?: string;
  thumbnail_url?: string;
}

export interface CreateGalleryData {
  name: string;
  description?: string;
  clientName?: string;
  clientEmails?: string[];
  is_public?: boolean;
  expiry_days?: number | string; // Allow 'never' or number
  allowDownload?: boolean;
  allowComments?: boolean;
  privacy?: 'private' | 'public';
}

export interface UpdateGalleryData {
  name?: string;
  description?: string;
  client_name?: string;
  client_email?: string;
  is_public?: boolean;
  expiry_date?: string;
}

// List all galleries for the current user
export async function listGalleries(params?: {
  page?: number;
  limit?: number;
  status?: string;
  sort?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.status) queryParams.append('status', params.status);
  if (params?.sort) queryParams.append('sort', params.sort);
  
  const queryString = queryParams.toString();
  const endpoint = queryString ? `/galleries?${queryString}` : '/galleries';
  
  return api.get<{ galleries: Gallery[]; total: number }>(endpoint);
}

// Create a new gallery
export async function createGallery(data: CreateGalleryData) {
  return api.post<Gallery>('/galleries', data);
}

// Get a specific gallery
export async function getGallery(galleryId: string, params?: { page_size?: number; last_key?: any }) {
  const queryParams = new URLSearchParams();
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params?.last_key) queryParams.append('last_key', JSON.stringify(params.last_key));
  
  const queryString = queryParams.toString();
  return api.get<Gallery & { pagination?: any }>(`/galleries/${galleryId}${queryString ? `?${queryString}` : ''}`);
}

// Update a gallery
export async function updateGallery(galleryId: string, data: UpdateGalleryData) {
  return api.put<Gallery>(`/galleries/${galleryId}`, data);
}

// Delete a gallery
export async function deleteGallery(galleryId: string) {
  return api.delete(`/galleries/${galleryId}`);
}

// Duplicate a gallery
export async function duplicateGallery(galleryId: string, newTitle: string) {
  return api.post<Gallery>(`/galleries/${galleryId}/duplicate`, { new_title: newTitle });
}

// Archive a gallery
export async function archiveGallery(galleryId: string) {
  return api.post(`/galleries/${galleryId}/archive`);
}

// Get gallery by share token (public)
export async function getGalleryByToken(shareToken: string) {
  return api.get<Gallery>(`/client/galleries/by-token/${shareToken}`);
}

export default {
  listGalleries,
  createGallery,
  getGallery,
  updateGallery,
  deleteGallery,
  duplicateGallery,
  archiveGallery,
  getGalleryByToken,
};

