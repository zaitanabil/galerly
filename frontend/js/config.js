/**
 * Galerly Frontend Configuration with LocalStack Support
 * 
 * Loads configuration from window.GALERLY_ENV_CONFIG (generated from frontend/.env.local)
 * NO hardcoded values - everything comes from config.env.js
 */

// Load configuration from window object (set by config.env.js)
const envConfig = window.GALERLY_ENV_CONFIG;
if (!envConfig) {
    throw new Error('GALERLY_ENV_CONFIG not loaded. Ensure config.env.js is loaded before config.js');
}

// Validate required configuration
if (!envConfig.API_BASE_URL) {
    throw new Error('API_BASE_URL not set in GALERLY_ENV_CONFIG');
}
if (!envConfig.CDN_BASE_URL) {
    throw new Error('CDN_BASE_URL not set in GALERLY_ENV_CONFIG');
}

// Environment detection from config
const isLocalStack = envConfig.IS_LOCALSTACK;

// URLs from configuration
const API_BASE_URL = envConfig.API_BASE_URL;
const CDN_BASE_URL = envConfig.CDN_BASE_URL;

// API Configuration
const CONFIG = {
    // API Base URL
    API_BASE_URL: API_BASE_URL,
    
    // Frontend URLs
    FRONTEND_URL: window.location.origin,
    
    // CDN URL for images
    CDN_URL: CDN_BASE_URL,
    
    // LocalStack mode flag
    IS_LOCALSTACK: isLocalStack,
    
    // Storage configuration
    MAX_FILE_SIZE: Infinity, // No limit - depends on subscription
    ALLOWED_IMAGE_TYPES: [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/tiff', 'image/raw', 'image/heic'
    ],
    
    // Upload configuration (from .env)
    CHUNK_SIZE: envConfig.CHUNK_SIZE,
    MAX_CONCURRENT_UPLOADS: envConfig.MAX_CONCURRENT_UPLOADS,
    
    // Pagination (from .env)
    DEFAULT_PAGE_SIZE: envConfig.DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE: envConfig.MAX_PAGE_SIZE,
    
    // Timeouts (from .env)
    API_TIMEOUT: envConfig.API_TIMEOUT,
    UPLOAD_TIMEOUT: envConfig.UPLOAD_TIMEOUT,
    
    // Features (from .env)
    ENABLE_ANALYTICS: envConfig.ENABLE_ANALYTICS,
    ENABLE_ERROR_REPORTING: envConfig.ENABLE_ERROR_REPORTING,
    
    // Auth (from .env)
    TOKEN_STORAGE_KEY: envConfig.TOKEN_STORAGE_KEY,
    REFRESH_TOKEN_KEY: envConfig.REFRESH_TOKEN_KEY,
    USER_DATA_KEY: envConfig.USER_DATA_KEY,
    
    // Redirects (from .env)
    DASHBOARD_PHOTOGRAPHER: envConfig.DASHBOARD_PHOTOGRAPHER,
    DASHBOARD_CLIENT: envConfig.DASHBOARD_CLIENT,
    LOGIN_PAGE: envConfig.LOGIN_PAGE,
    
    // Stripe Configuration (must be set by backend injection or separate config)
    STRIPE_PUBLISHABLE_KEY: window.STRIPE_PUBLISHABLE_KEY || '',
};

// Debug logging for LocalStack mode
if (isLocalStack) {
    console.log('🔧 LocalStack Mode Enabled');
    console.log('   API Base URL:', API_BASE_URL);
    console.log('   CDN Base URL:', CDN_BASE_URL);
    console.log('   Frontend URL:', window.location.origin);
}

// Helper function to get full API URL
function getApiUrl(endpoint) {
    // Remove leading slash if present
    endpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
    // API_BASE_URL already includes /api/v1, so just append the endpoint
    return `${CONFIG.API_BASE_URL}/${endpoint}`;
}

// Helper function to get image URL (with CDN if available)
function getImageUrl(path) {
    if (!path) return '';
    
    // LocalStack mode: Use LocalStack S3 URLs
    if (isLocalStack) {
        const localhostHost = envConfig.LOCALSTACK_HOST;
        const localhostPort = envConfig.LOCALSTACK_PORT;
        const renditionsBucket = envConfig.S3_RENDITIONS_BUCKET;
        
        // If path is already a full LocalStack URL, return as-is
        if (path.includes(`${localhostHost}:${localhostPort}`) || path.includes(`127.0.0.1:${localhostPort}`)) {
            return path;
        }
        // Convert relative path to LocalStack S3 URL
        return `${envConfig.BACKEND_PROTOCOL}://${localhostHost}:${localhostPort}/${renditionsBucket}/${path}`;
    }
    
    // Production mode: Use CloudFront CDN
    
    // Convert old S3 URLs to CloudFront CDN
    if (path.includes('galerly-images-storage.s3') || path.includes('.s3.') || path.includes('.s3-')) {
        const s3Match = path.match(/\.s3[^/]*\.amazonaws\.com\/(.+)$/);
        if (s3Match) {
            const s3Key = s3Match[1];
            return `${CONFIG.CDN_URL.startsWith('http') ? '' : 'https://'}${CONFIG.CDN_URL}/${s3Key}`;
        }
    }
    
    // If already CDN URL, return as-is
    if (path.includes('cdn.') || path.includes('cloudfront.net')) {
        return path;
    }
    
    // If path is already a full URL, return it
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    
    // Use CDN for production
    if (CONFIG.CDN_URL) {
        const cdnUrl = CONFIG.CDN_URL.startsWith('http') ? CONFIG.CDN_URL : `https://${CONFIG.CDN_URL}`;
        return `${cdnUrl}/${path}`;
    }
    
    // Use relative path as fallback
    return path.startsWith('/') ? path : `/${path}`;
}

// Helper function to get auth headers
function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json',
    };
    return headers;
}

// Helper function to check if user is authenticated
async function isAuthenticated() {
    try {
        const response = await fetch(getApiUrl('auth/me'), {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const userData = await response.json();
            localStorage.setItem(CONFIG.USER_DATA_KEY, JSON.stringify(userData));
            return true;
        } else {
            localStorage.removeItem(CONFIG.USER_DATA_KEY);
            return false;
        }
    } catch (error) {
        localStorage.removeItem(CONFIG.USER_DATA_KEY);
        return false;
    }
}

// Synchronous helper for UI state ONLY
function hasLocalUserData() {
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
    localStorage.removeItem(CONFIG.USER_DATA_KEY);
    fetch(getApiUrl('auth/logout'), {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(() => {
        window.location.href = CONFIG.LOGIN_PAGE;
    }).catch((error) => {
        console.error('Logout error:', error);
        window.location.href = CONFIG.LOGIN_PAGE;
    });
}

// Helper function to validate file
function validateFile(file) {
    const errors = [];
    if (!CONFIG.ALLOWED_IMAGE_TYPES.includes(file.type)) {
        errors.push(`${file.name} is not a valid image type`);
    }
    return {
        valid: errors.length === 0,
        errors
    };
}

// API request wrapper with error handling
async function apiRequest(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    const timeout = options.timeout || CONFIG.API_TIMEOUT;
    
    if (!options.headers) {
        options.headers = getAuthHeaders();
    }
    
    options.credentials = 'include';
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (response.status === 401) {
            const isAuthEndpoint = endpoint.includes('auth/login') || 
                                  endpoint.includes('auth/register') ||
                                  endpoint.includes('auth/me') ||
                                  endpoint.includes('profile');
            
            if (!isAuthEndpoint) {
                logout();
                throw new Error('Session expired. Please login again.');
            }
        }
        
        if (!response.ok) {
            const error = new Error(data.message || data.detail || data.error || 'Request failed');
            error.details = data;
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

// Export configuration
if (typeof window !== 'undefined') {
    window.GalerlyConfig = CONFIG;
    window.getApiUrl = getApiUrl;
    window.getImageUrl = getImageUrl;
    window.getAuthHeaders = getAuthHeaders;
    window.isAuthenticated = isAuthenticated;
    window.hasLocalUserData = hasLocalUserData;
    window.getUserData = getUserData;
    window.logout = logout;
    window.validateFile = validateFile;
    window.apiRequest = apiRequest;
}
