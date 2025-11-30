// Public service - handles public endpoints (no auth required)
import { api } from '../utils/api';

export interface City {
  name: string;
  country: string;
  latitude?: number;
  longitude?: number;
}

export interface Photographer {
  id: string;
  name: string;
  city?: string;
  country?: string;
  bio?: string;
  website?: string;
  profile_image?: string;
  gallery_count?: number;
  subscription_tier?: string;
}

export interface ContactData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface NewsletterData {
  email: string;
  name?: string;
}

// City search (for autocomplete)
export async function searchCities(query: string) {
  return api.get<{ cities: City[] }>(`/cities/search?q=${encodeURIComponent(query)}`);
}

// Photographer directory
export async function listPhotographers(params?: {
  page?: number;
  limit?: number;
  city?: string;
  country?: string;
  search?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.city) queryParams.append('city', params.city);
  if (params?.country) queryParams.append('country', params.country);
  if (params?.search) queryParams.append('search', params.search);
  
  const queryString = queryParams.toString();
  const endpoint = queryString ? `/photographers?${queryString}` : '/photographers';
  
  return api.get<{ photographers: Photographer[]; total: number }>(endpoint);
}

export async function getPhotographer(photographerId: string) {
  return api.get<Photographer>(`/photographers/${photographerId}`);
}

// Contact form
export async function submitContact(data: ContactData) {
  return api.post('/contact/submit', data);
}

// Newsletter
export async function subscribeNewsletter(data: NewsletterData) {
  return api.post('/newsletter/subscribe', data);
}

export async function unsubscribeNewsletter(email: string) {
  return api.post('/newsletter/unsubscribe', { email });
}

// Social sharing info (public)
export async function getGalleryShareInfo(galleryId: string) {
  return api.get(`/share/gallery/${galleryId}`);
}

export async function getPhotoShareInfo(photoId: string) {
  return api.get(`/share/photo/${photoId}`);
}

export default {
  searchCities,
  listPhotographers,
  getPhotographer,
  submitContact,
  subscribeNewsletter,
  unsubscribeNewsletter,
  getGalleryShareInfo,
  getPhotoShareInfo,
};

