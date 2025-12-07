// User/Profile service - handles user profile and settings
import { api } from '../utils/api';

export interface Profile {
  id: string;
  email: string;
  name: string;
  role: string;
  city?: string;
  country?: string;
  bio?: string;
  website?: string;
  phone?: string;
  profile_image?: string;
  subscription_tier?: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileData {
  name?: string;
  city?: string;
  country?: string;
  bio?: string;
  website?: string;
  phone?: string;
}

export interface PortfolioSettings {
  enabled: boolean;
  custom_domain?: string;
  theme?: string;
  header_image?: string;
  bio?: string;
  social_links?: Record<string, string>;
}

export interface NotificationPreferences {
  email_on_upload: boolean;
  email_on_comment: boolean;
  email_on_favorite: boolean;
  email_on_share: boolean;
  email_weekly_summary: boolean;
}

// Get current user profile
export async function getProfile() {
  return api.get<Profile>('/auth/me');
}

// Update profile
export async function updateProfile(data: UpdateProfileData) {
  return api.put<Profile>('/profile', data);
}

// Delete account
export async function deleteAccount() {
  return api.delete('/auth/delete-account');
}

// Portfolio settings
export async function getPortfolioSettings() {
  return api.get<PortfolioSettings>('/portfolio/settings');
}

export async function updatePortfolioSettings(settings: Partial<PortfolioSettings>) {
  return api.put<PortfolioSettings>('/portfolio/settings', settings);
}

export async function getPublicPortfolio(userId: string) {
  return api.get(`/portfolio/${userId}`);
}

// Notification preferences
export async function getNotificationPreferences() {
  return api.get<NotificationPreferences>('/notifications/preferences');
}

export async function updateNotificationPreferences(preferences: Partial<NotificationPreferences>) {
  return api.put<NotificationPreferences>('/notifications/preferences', preferences);
}

// Dashboard stats
export async function getDashboardStats() {
  return api.get('/dashboard/stats');
}

export default {
  getProfile,
  updateProfile,
  deleteAccount,
  getPortfolioSettings,
  updatePortfolioSettings,
  getPublicPortfolio,
  getNotificationPreferences,
  updateNotificationPreferences,
  getDashboardStats,
};

