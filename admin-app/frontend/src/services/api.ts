const API_BASE_URL = 'http://localhost:5002/api';

interface FetchOptions {
  method?: string;
  body?: string;
}

async function fetchAPI(endpoint: string, options?: FetchOptions) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `API Error: ${response.statusText}`);
  }
  return response.json();
}

export const adminAPI = {
  // Dashboard
  getDashboardStats: () => fetchAPI('/dashboard/stats'),
  
  // Users
  getUsers: (params?: { role?: string; plan?: string; limit?: number }) => {
    const queryString = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return fetchAPI(`/users${queryString}`);
  },
  
  getUserDetails: (userId: string) => fetchAPI(`/users/${userId}`),
  
  createUser: (userData: any) => fetchAPI('/users/create', {
    method: 'POST',
    body: JSON.stringify(userData)
  }),
  
  suspendUser: (userId: string, reason: string) => fetchAPI(`/users/${userId}/suspend`, {
    method: 'POST',
    body: JSON.stringify({ reason })
  }),
  
  unsuspendUser: (userId: string) => fetchAPI(`/users/${userId}/unsuspend`, {
    method: 'POST'
  }),
  
  deleteUser: (userId: string) => fetchAPI(`/users/${userId}/delete`, {
    method: 'DELETE'
  }),
  
  // Galleries
  getAllGalleries: (search?: string) => {
    const queryString = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchAPI(`/galleries${queryString}`);
  },
  
  getUserGalleries: (userId: string) => fetchAPI(`/users/${userId}/galleries`),
  
  deleteGallery: (galleryId: string) => fetchAPI(`/galleries/${galleryId}`, {
    method: 'DELETE'
  }),
  
  // Activity
  getActivity: (params?: { hours?: number; limit?: number }) => {
    const queryString = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return fetchAPI(`/activity${queryString}`);
  },
  
  // Revenue
  getRevenueStats: () => fetchAPI('/revenue'),
  
  // Subscriptions
  getSubscriptions: (status?: string) => {
    const queryString = status ? `?status=${status}` : '';
    return fetchAPI(`/subscriptions${queryString}`);
  },
  
  // Data Health
  getDataHealth: () => fetchAPI('/data-health'),
};

export default adminAPI;

