// Environment configuration - matches old JS frontend config.js
const isLocalstack = import.meta.env.VITE_IS_LOCALSTACK === 'true';
const hostname = typeof window !== 'undefined' ? window.location.hostname : '';

// Base configuration from environment variables
export const config = {
  environment: import.meta.env.VITE_ENVIRONMENT || 'local',
  isLocalstack,
  
  backend: {
    host: import.meta.env.VITE_BACKEND_HOST || 'localhost',
    port: import.meta.env.VITE_BACKEND_PORT || '5001',
    protocol: import.meta.env.VITE_BACKEND_PROTOCOL || 'http',
  },
  
  localstack: {
    host: import.meta.env.VITE_LOCALSTACK_HOST || 'localhost',
    port: import.meta.env.VITE_LOCALSTACK_PORT || '4566',
    bucket: import.meta.env.VITE_S3_RENDITIONS_BUCKET || 'galerly-renditions-local',
  },
  
  upload: {
    chunkSize: parseInt(import.meta.env.VITE_CHUNK_SIZE || '5242880', 10),
    maxConcurrentUploads: parseInt(import.meta.env.VITE_MAX_CONCURRENT_UPLOADS || '3', 10),
  },
  
  pagination: {
    defaultPageSize: parseInt(import.meta.env.VITE_DEFAULT_PAGE_SIZE || '20', 10),
    maxPageSize: parseInt(import.meta.env.VITE_MAX_PAGE_SIZE || '100', 10),
  },
  
  timeouts: {
    api: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),
    upload: parseInt(import.meta.env.VITE_UPLOAD_TIMEOUT || '300000', 10),
  },
  
  features: {
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    errorReporting: import.meta.env.VITE_ENABLE_ERROR_REPORTING === 'true',
  },
  
  storage: {
    // Backend uses cookie-based auth (galerly_session HttpOnly cookie)
    // These keys are for caching user data only
    userDataKey: 'galerly_user_data',
  },
  
  allowedImageTypes: [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif',
    'image/webp',
    'image/tiff',
    'image/raw',
    'image/heic'
  ],
};

// Computed URLs - matches old JS frontend pattern
export const apiBaseUrl = isLocalstack
  ? `${config.backend.protocol}://${config.backend.host}:${config.backend.port}/v1`
  : `https://api.${hostname.replace(/^www\./, '')}/xb667e3fa92f9776468017a9758f31ba4/v1`;

export const cdnBaseUrl = isLocalstack
  ? `${config.backend.protocol}://${config.localstack.host}:${config.localstack.port}/${config.localstack.bucket}`
  : `https://cdn.${hostname.replace(/^www\./, '')}`;

// Helper to get full image URL with CDN
export function getImageUrl(path: string): string {
  if (!path) return '';
  
  // LocalStack mode
  if (isLocalstack) {
    const { host, port } = config.localstack;
    const bucket = config.localstack.bucket;
    
    // If path is already a full LocalStack URL, return as-is
    if (path.includes(`${host}:${port}`) || path.includes(`127.0.0.1:${port}`)) {
      return path;
    }
    // Convert relative path to LocalStack S3 URL
    return `${config.backend.protocol}://${host}:${port}/${bucket}/${path}`;
  }
  
  // Production mode - use CloudFront CDN
  
  // Convert old S3 URLs to CloudFront CDN
  if (path.includes('.s3.') || path.includes('.s3-')) {
    const s3Match = path.match(/\.s3[^/]*\.amazonaws\.com\/(.+)$/);
    if (s3Match) {
      const s3Key = s3Match[1];
      return `${cdnBaseUrl.startsWith('http') ? '' : 'https://'}${cdnBaseUrl}/${s3Key}`;
    }
  }
  
  // If already CDN or full URL, return as-is
  if (path.includes('cdn.') || path.includes('cloudfront.net') || 
      path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  
  // Use CDN for production
  const cdnUrl = cdnBaseUrl.startsWith('http') ? cdnBaseUrl : `https://${cdnBaseUrl}`;
  return `${cdnUrl}/${path}`;
}

// Helper to validate file
export function validateFile(file: File): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!config.allowedImageTypes.includes(file.type)) {
    errors.push(`${file.name} is not a valid image type`);
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

if (import.meta.env.DEV) {
  console.log('🔧 Configuration Loaded');
  console.log('   Backend:', apiBaseUrl);
  console.log('   CDN:', cdnBaseUrl);
  console.log('   LocalStack:', isLocalstack);
}

