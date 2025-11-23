/**
 * Galerly Frontend Environment Configuration
 * 
 * ⚠️  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
 * This file is generated from frontend/.env.local by generate-frontend-config.sh
 * 
 * Generated: 2025-11-22 13:25:25 UTC
 * Environment: local
 */

// Detect current hostname
const hostname = window.location.hostname;

// Environment configuration from .env file
window.GALERLY_ENV_CONFIG = {
    // Environment
    ENVIRONMENT: 'local',
    IS_LOCALSTACK: true,
    
    // Backend Configuration
    BACKEND_HOST: 'localhost',
    BACKEND_PORT: '5001',
    BACKEND_PROTOCOL: 'http',
    
    // LocalStack S3
    LOCALSTACK_HOST: 'localhost',
    LOCALSTACK_PORT: '4566',
    S3_RENDITIONS_BUCKET: 'galerly-renditions-local',
    
    // Upload Configuration
    CHUNK_SIZE: 5 * 1024 * 1024,
    MAX_CONCURRENT_UPLOADS: 3,
    
    // Pagination
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    
    // Timeouts
    API_TIMEOUT: 30000,
    UPLOAD_TIMEOUT: 300000,
    
    // Feature Flags
    ENABLE_ANALYTICS: false,
    ENABLE_ERROR_REPORTING: false,
    
    // Storage Keys
    TOKEN_STORAGE_KEY: 'galerly_access_token',
    REFRESH_TOKEN_KEY: 'galerly_refresh_token',
    USER_DATA_KEY: 'galerly_user_data',
    
    // Routes
    DASHBOARD_PHOTOGRAPHER: '/dashboard.html',
    DASHBOARD_CLIENT: '/gallery.html',
    LOGIN_PAGE: '/auth.html',
};

// Computed URLs (no hardcoded values)
if (window.GALERLY_ENV_CONFIG.IS_LOCALSTACK) {
    const cfg = window.GALERLY_ENV_CONFIG;
    
    // API Base URL (no /api prefix for local Flask - goes directly to Lambda handler)
    cfg.API_BASE_URL = `${cfg.BACKEND_PROTOCOL}://${cfg.BACKEND_HOST}:${cfg.BACKEND_PORT}/v1`;
    
    // CDN Base URL (LocalStack S3)
    cfg.CDN_BASE_URL = `${cfg.BACKEND_PROTOCOL}://${cfg.LOCALSTACK_HOST}:${cfg.LOCALSTACK_PORT}/${cfg.S3_RENDITIONS_BUCKET}`;
    
    console.log('🔧 LocalStack Mode - Configuration Loaded');
    console.log('   Backend:', cfg.API_BASE_URL);
    console.log('   CDN:', cfg.CDN_BASE_URL);
} else {
    // Production: Auto-detect from hostname (includes /api prefix from API Gateway)
    const baseDomain = hostname.replace(/^www\./, '');
    window.GALERLY_ENV_CONFIG.API_BASE_URL = `https://api.${baseDomain}/xb667e3fa92f9776468017a9758f31ba4/v1`;
    window.GALERLY_ENV_CONFIG.CDN_BASE_URL = `https://cdn.${baseDomain}`;
}
