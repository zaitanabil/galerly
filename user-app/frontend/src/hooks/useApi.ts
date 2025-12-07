// Custom hooks for API operations - provides easy-to-use React hooks
import { useState, useEffect, useCallback } from 'react';
import * as galleryService from '../services/galleryService';
import * as photoService from '../services/photoService';
import * as billingService from '../services/billingService';
import * as analyticsService from '../services/analyticsService';
import * as clientService from '../services/clientService';
import * as userService from '../services/userService';

// Generic hook for async operations
export function useAsync<T>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  asyncFunction: () => Promise<any>, // Service functions still return Promise<any> or specific types, but usually wrapped in ApiResponse
  immediate = true
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await asyncFunction();
      if (response.success) {
        setData(response.data);
        return { success: true, data: response.data };
      } else {
        setError(response.error || 'Operation failed');
        return { success: false, error: response.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate]); // Only run when 'immediate' changes, not on every 'execute' change

  return { data, loading, error, execute };
}

// Gallery hooks
export function useGalleries(params?: Parameters<typeof galleryService.listGalleries>[0]) {
  return useAsync<{ galleries: galleryService.Gallery[]; total: number }>(
    () => galleryService.listGalleries(params)
  );
}

export function useGallery(galleryId: string | undefined, immediate = true) {
  return useAsync<galleryService.Gallery>(
    () => galleryService.getGallery(galleryId!),
    immediate && !!galleryId
  );
}

// Photo hooks
export function usePhotos(params: Parameters<typeof photoService.searchPhotos>[0]) {
  return useAsync<{ photos: photoService.Photo[]; total: number }>(
    () => photoService.searchPhotos(params)
  );
}

// Billing hooks
export function useSubscription() {
  return useAsync<billingService.Subscription>(
    () => billingService.getSubscription()
  );
}

export function useUsage() {
  return useAsync<billingService.UsageStats>(
    () => billingService.getUsage()
  );
}

export function useBillingHistory(params?: Parameters<typeof billingService.getBillingHistory>[0]) {
  return useAsync<{ invoices: billingService.Invoice[]; total: number }>(
    () => billingService.getBillingHistory(params)
  );
}

// Analytics hooks
export function useGalleryAnalytics(galleryId: string | undefined, startDate?: string, endDate?: string) {
  return useAsync<analyticsService.AnalyticsData>(
    () => analyticsService.getGalleryAnalytics(galleryId!, startDate, endDate),
    !!galleryId
  );
}

export function useOverallAnalytics(startDate?: string, endDate?: string) {
  return useAsync<analyticsService.AnalyticsData>(
    () => analyticsService.getOverallAnalytics(startDate, endDate)
  );
}

export function useBulkDownloads(galleryId?: string) {
  return useAsync(
    () => analyticsService.getBulkDownloads(galleryId)
  );
}

export function useVisitorAnalytics(galleryId?: string) {
  return useAsync(
    () => analyticsService.getVisitorAnalytics(galleryId)
  );
}

// Client hooks
export function useClientGalleries(params?: Parameters<typeof clientService.getClientGalleries>[0]) {
  return useAsync<{ galleries: clientService.ClientGallery[]; total: number }>(
    () => clientService.getClientGalleries(params)
  );
}

export function useClientGallery(galleryId: string | undefined) {
  return useAsync<clientService.ClientGallery>(
    () => clientService.getClientGallery(galleryId!),
    !!galleryId
  );
}

export function useClientGalleryByToken(shareToken: string | undefined) {
  return useAsync<clientService.ClientGallery>(
    () => clientService.getClientGalleryByToken(shareToken!),
    !!shareToken
  );
}

export function useFavorites(galleryId: string | undefined) {
  return useAsync<{ favorites: clientService.Favorite[] }>(
    () => clientService.getFavorites(galleryId!),
    !!galleryId
  );
}

// User/Profile hooks
export function useProfile() {
  return useAsync<userService.Profile>(
    () => userService.getProfile()
  );
}

export function useDashboardStats() {
  return useAsync(
    () => userService.getDashboardStats()
  );
}

export function usePortfolioSettings() {
  return useAsync<userService.PortfolioSettings>(
    () => userService.getPortfolioSettings()
  );
}

export function useNotificationPreferences() {
  return useAsync<userService.NotificationPreferences>(
    () => userService.getNotificationPreferences()
  );
}

// Mutation hook for creating/updating/deleting
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useMutation<TArgs extends any[], TResult>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  mutationFn: (...args: TArgs) => Promise<any>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(async (...args: TArgs) => {
    setLoading(true);
    setError(null);

    try {
      const response = await mutationFn(...args);
      if (response.success) {
        return { success: true, data: response.data as TResult };
      } else {
        setError(response.error || 'Operation failed');
        return { success: false, error: response.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [mutationFn]);

  return { mutate, loading, error };
}

// Common mutations
export function useCreateGallery() {
  return useMutation((data: Parameters<typeof galleryService.createGallery>[0]) =>
    galleryService.createGallery(data)
  );
}

export function useUpdateGallery() {
  return useMutation((galleryId: string, data: Parameters<typeof galleryService.updateGallery>[1]) =>
    galleryService.updateGallery(galleryId, data)
  );
}

export function useDeleteGallery() {
  return useMutation((galleryId: string) =>
    galleryService.deleteGallery(galleryId)
  );
}

export function useDeletePhotos() {
  return useMutation((galleryId: string, photoIds: string[]) =>
    photoService.deletePhotos(galleryId, photoIds)
  );
}

export function useAddComment() {
  return useMutation((photoId: string, text: string) =>
    photoService.addComment(photoId, text)
  );
}

export function useUpdateProfile() {
  return useMutation((data: Parameters<typeof userService.updateProfile>[0]) =>
    userService.updateProfile(data)
  );
}

export function useSubmitFeedback() {
  return useMutation((galleryId: string, data: Parameters<typeof clientService.submitFeedback>[1]) =>
    clientService.submitFeedback(galleryId, data)
  );
}
