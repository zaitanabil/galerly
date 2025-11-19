/**
 * Galerly Frontend Configuration
 * 
 * This file centralizes all API endpoints and configuration.
 * Update API_BASE_URL for production deployment.
 */
// API Configuration
const CONFIG = {
    // API Base URL - automatically detects environment
    // Set via window.API_BASE_URL environment variable
    API_BASE_URL: window.API_BASE_URL || 
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000/api/v1'
            : ''),  // Must be set via environment variable in production
    // Frontend URLs
    FRONTEND_URL: window.location.origin,
    // CloudFront CDN for fast global delivery
    CDN_URL: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
        ? 'https://cdn.galerly.com'
        : '',
    // Storage configuration - NO LIMITS on individual files
    // Photographers need flexibility for various image sizes
    // Storage limits are enforced at the subscription level
    MAX_FILE_SIZE: Infinity, // No limit - depends on subscription
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/tiff', 'image/raw', 'image/heic'],
    // Upload configuration
    CHUNK_SIZE: 5 * 1024 * 1024, // 5MB chunks for large uploads
    MAX_CONCURRENT_UPLOADS: 3,
    // Pagination
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    // Timeouts
    API_TIMEOUT: 30000, // 30 seconds
    UPLOAD_TIMEOUT: 300000, // 5 minutes
    // Features
    ENABLE_ANALYTICS: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
    ENABLE_ERROR_REPORTING: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
    // Auth
    TOKEN_STORAGE_KEY: 'galerly_access_token',
    REFRESH_TOKEN_KEY: 'galerly_refresh_token',
    USER_DATA_KEY: 'galerly_user_data',
    // Redirects
    DASHBOARD_PHOTOGRAPHER: '/dashboard',
    DASHBOARD_CLIENT: '/gallery',
    LOGIN_PAGE: '/auth',
    // Stripe Configuration (loaded from environment)
    STRIPE_PUBLISHABLE_KEY: window.STRIPE_PUBLISHABLE_KEY || '',
};
// Helper function to get full API URL
function getApiUrl(endpoint) {
    // Remove leading slash if present
    endpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
    return `${CONFIG.API_BASE_URL}/${endpoint}`;
}
// Helper function to get image URL (with CDN if available)
function getImageUrl(path) {
    if (!path) return '';
    
    // Convert old S3 URLs to CloudFront CDN
    if (path.includes('galerly-images-storage.s3')) {
        const match = path.match(/galerly-images-storage\.s3[^/]*\.amazonaws\.com\/(.+)$/);
        if (match) {
            const s3Key = match[1];
            return `https://cdn.galerly.com/${s3Key}`;
        }
    }
    
    // If already CDN URL, return as-is
    if (path.includes('cdn.galerly.com')) {
        return path;
    }
    
    // If path is already a full URL, return it
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    
    // Use CDN for production
    if (CONFIG.CDN_URL) {
        return `${CONFIG.CDN_URL}/${path}`;
    }
    
    // Use relative path for local development
    return path.startsWith('/') ? path : `/${path}`;
}
// Helper function to get auth headers
function getAuthHeaders() {
    // No need to include Authorization header - cookies are sent automatically
    // When credentials: 'include' is used
    const headers = {
        'Content-Type': 'application/json',
    };
    return headers;
}
// Helper function to check if user is authenticated
function isAuthenticated() {
    // Check if there's user data in localStorage (for UI state only)
    // Actual auth is handled by HttpOnly cookie
    const userData = localStorage.getItem(CONFIG.USER_DATA_KEY);
    return userData !== null && userData !== undefined && userData !== '';
}
// Helper function to get user data
function getUserData() {
    const userData = localStorage.getItem(CONFIG.USER_DATA_KEY);
    try {
        return userData ? JSON.parse(userData) : null;
    } catch (e) {
        console.error('Failed to parse user data:', e);
        return null;
    }
}
// Helper function to logout
function logout() {
    // Clear user data from localStorage
    localStorage.removeItem(CONFIG.USER_DATA_KEY);
    // Call logout API to clear HttpOnly cookie
    fetch(getApiUrl('auth/logout'), {
        method: 'POST',
        credentials: 'include',  // Important: sends cookie
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(() => {
        // Redirect to login page
        window.location.href = CONFIG.LOGIN_PAGE;
    }).catch((error) => {
        console.error('Logout error:', error);
        // Still redirect even if API call fails
        window.location.href = CONFIG.LOGIN_PAGE;
    });
}
// Helper function to validate file
function validateFile(file) {
    const errors = [];
    // Check file type
    if (!CONFIG.ALLOWED_IMAGE_TYPES.includes(file.type)) {
        errors.push(`${file.name} is not a valid image type`);
    }
    // NO SIZE CHECK - Photographers need any size
    // Storage limits are enforced at subscription level, not per-file
    return {
        valid: errors.length === 0,
        errors
    };
}
// API request wrapper with error handling
async function apiRequest(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    const timeout = options.timeout || CONFIG.API_TIMEOUT;
    // Set default headers
    if (!options.headers) {
        options.headers = getAuthHeaders();
    }
    // IMPORTANT: Always include credentials for cookies
    options.credentials = 'include';
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        // Parse JSON response
        const data = await response.json();
        // Handle session expiration ONLY for protected endpoints
        // Don't auto-logout on auth/me, auth/login, auth/register, or profile endpoints
        if (response.status === 401) {
            const isAuthEndpoint = endpoint.includes('auth/login') || 
                                  endpoint.includes('auth/register') ||
                                  endpoint.includes('auth/me') ||
                                  endpoint.includes('profile');
            // Only auto-logout if it's NOT an auth/profile endpoint
            if (!isAuthEndpoint) {
                logout();
                throw new Error('Session expired. Please login again.');
            }
        }
        if (!response.ok) {
            // Create error object with full details
            const error = new Error(data.message || data.detail || data.error || 'Request failed');
            error.details = data; // Attach full response for detailed error messages
            throw error;
        }
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout');
        }
        throw error;
    }
}
// Export configuration (for use in other scripts)
if (typeof window !== 'undefined') {
    window.GalerlyConfig = CONFIG;
    window.getApiUrl = getApiUrl;
    window.getImageUrl = getImageUrl;
    window.getAuthHeaders = getAuthHeaders;
    window.isAuthenticated = isAuthenticated;
    window.getUserData = getUserData;
    window.logout = logout;
    window.validateFile = validateFile;
    window.apiRequest = apiRequest;
}