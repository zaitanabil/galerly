/* eslint-disable @typescript-eslint/no-explicit-any */
// API utility functions - matches old JS frontend config.js pattern
// Uses cookie-based authentication (HttpOnly cookies) like the backend expects
import { apiBaseUrl, config } from '../config/env';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  detail?: string;
  success: boolean;
}

// Get user data from storage (for UI state only, not auth)
export const getUserData = () => {
  const data = localStorage.getItem(config.storage.userDataKey);
  try {
  return data ? JSON.parse(data) : null;
  } catch (e) {
    console.error('Failed to parse user data:', e);
    return null;
  }
};

// Set user data in storage
export const setUserData = (data: unknown): void => {
  localStorage.setItem(config.storage.userDataKey, JSON.stringify(data));
};

// Remove user data
export const removeUserData = (): void => {
  localStorage.removeItem(config.storage.userDataKey);
};

// Check if user data exists (synchronous, for UI state only)
export const hasLocalUserData = (): boolean => {
  const userData = localStorage.getItem(config.storage.userDataKey);
  return userData !== null && userData !== undefined && userData !== '';
};

// API request wrapper with cookie-based auth
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  const url = `${apiBaseUrl}/${cleanEndpoint}`;
  
  const timeout = options.signal ? undefined : config.timeouts.api;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Set up abort controller for timeout if no signal provided
  const controller = new AbortController();
  let timeoutId: NodeJS.Timeout | undefined;
  
  if (timeout && !options.signal) {
    timeoutId = setTimeout(() => controller.abort(), timeout);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // REQUIRED for cookie-based auth
      signal: options.signal || controller.signal,
    });

    if (timeoutId) clearTimeout(timeoutId);

    const data = await response.json();

    // Handle 401 Unauthorized - redirect to login if not on auth endpoints
    if (response.status === 401) {
      const isAuthEndpoint = endpoint.includes('auth/login') || 
                            endpoint.includes('auth/register') ||
                            endpoint.includes('auth/me') ||
                            endpoint.includes('profile');
      
      if (!isAuthEndpoint) {
        removeUserData();
        // Don't auto-redirect in React - let the app handle it
        return {
          success: false,
          error: 'Session expired. Please login again.',
        };
      }
    }

    if (!response.ok) {
      return {
        success: false,
        error: data.error || data.message || data.detail || 'Request failed',
      };
    }

    return {
      success: true,
      data,
    };
  } catch (error) {
    if (timeoutId) clearTimeout(timeoutId);
    
    console.error('API request failed:', error);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return {
          success: false,
          error: 'Request timeout',
        };
      }
      return {
        success: false,
        error: error.message,
      };
    }
    
    return {
      success: false,
      error: 'Network error',
    };
  }
}

// Convenience methods
export const api = {
  get: <T = any>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),
    
  post: <T = any>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
    
  put: <T = any>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
    
  patch: <T = any>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
    
  delete: <T = any>(endpoint: string, body?: unknown, options?: RequestInit) => {
    const config: RequestInit = {
      ...options,
      method: 'DELETE',
    };
    // Only add body if it's provided and not undefined
    if (body !== undefined) {
      config.body = JSON.stringify(body);
    }
    return apiRequest<T>(endpoint, config);
  },
};

// Export for backward compatibility (but cookies handle auth now)
export const getToken = () => null;
export const setToken = () => {};
export const removeToken = removeUserData;

