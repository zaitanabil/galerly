#!/bin/bash
# ============================================
# Generate Frontend Configuration from .env
# ============================================
# This script reads frontend/.env.local and generates frontend/config.env.js
# NO hardcoded values - everything comes from .env file

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Generating Frontend Configuration${NC}"

# Check if frontend .env.local exists
FRONTEND_ENV_FILE="./frontend/.env.local"
if [ ! -f "$FRONTEND_ENV_FILE" ]; then
    echo -e "${RED}❌ Error: $FRONTEND_ENV_FILE not found${NC}"
    exit 1
fi

# Load environment variables from frontend .env.local
echo -e "${YELLOW}📄 Loading configuration from $FRONTEND_ENV_FILE${NC}"
export $(grep -v '^#' "$FRONTEND_ENV_FILE" | grep -v '^$' | xargs)

# Validate required variables
REQUIRED_VARS=(
    "ENVIRONMENT"
    "IS_LOCALSTACK"
    "BACKEND_HOST"
    "BACKEND_PORT"
    "BACKEND_PROTOCOL"
    "LOCALSTACK_HOST"
    "LOCALSTACK_PORT"
    "S3_RENDITIONS_BUCKET"
    "CHUNK_SIZE_MB"
    "MAX_CONCURRENT_UPLOADS"
    "DEFAULT_PAGE_SIZE"
    "MAX_PAGE_SIZE"
    "API_TIMEOUT_MS"
    "UPLOAD_TIMEOUT_MS"
    "ENABLE_ANALYTICS"
    "ENABLE_ERROR_REPORTING"
    "TOKEN_STORAGE_KEY"
    "REFRESH_TOKEN_KEY"
    "USER_DATA_KEY"
    "DASHBOARD_PHOTOGRAPHER"
    "DASHBOARD_CLIENT"
    "LOGIN_PAGE"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: Required variable '$var' is not set in $FRONTEND_ENV_FILE${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All required variables found${NC}"

# Generate config.env.js
OUTPUT_FILE="./frontend/config.env.js"
echo -e "${YELLOW}📝 Generating $OUTPUT_FILE${NC}"

cat > "$OUTPUT_FILE" << EOF
/**
 * Galerly Frontend Environment Configuration
 * 
 * ⚠️  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
 * This file is generated from frontend/.env.local by scripts/generate-frontend-config.sh
 * 
 * Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
 * Environment: ${ENVIRONMENT}
 */

// Detect current hostname
const hostname = window.location.hostname;

// Environment configuration from .env file
window.GALERLY_ENV_CONFIG = {
    // Environment
    ENVIRONMENT: '${ENVIRONMENT}',
    IS_LOCALSTACK: ${IS_LOCALSTACK},
    
    // Backend Configuration
    BACKEND_HOST: '${BACKEND_HOST}',
    BACKEND_PORT: '${BACKEND_PORT}',
    BACKEND_PROTOCOL: '${BACKEND_PROTOCOL}',
    
    // LocalStack S3
    LOCALSTACK_HOST: '${LOCALSTACK_HOST}',
    LOCALSTACK_PORT: '${LOCALSTACK_PORT}',
    S3_RENDITIONS_BUCKET: '${S3_RENDITIONS_BUCKET}',
    
    // Upload Configuration
    CHUNK_SIZE: ${CHUNK_SIZE_MB} * 1024 * 1024,
    MAX_CONCURRENT_UPLOADS: ${MAX_CONCURRENT_UPLOADS},
    
    // Pagination
    DEFAULT_PAGE_SIZE: ${DEFAULT_PAGE_SIZE},
    MAX_PAGE_SIZE: ${MAX_PAGE_SIZE},
    
    // Timeouts
    API_TIMEOUT: ${API_TIMEOUT_MS},
    UPLOAD_TIMEOUT: ${UPLOAD_TIMEOUT_MS},
    
    // Feature Flags
    ENABLE_ANALYTICS: ${ENABLE_ANALYTICS},
    ENABLE_ERROR_REPORTING: ${ENABLE_ERROR_REPORTING},
    
    // Storage Keys
    TOKEN_STORAGE_KEY: '${TOKEN_STORAGE_KEY}',
    REFRESH_TOKEN_KEY: '${REFRESH_TOKEN_KEY}',
    USER_DATA_KEY: '${USER_DATA_KEY}',
    
    // Routes
    DASHBOARD_PHOTOGRAPHER: '${DASHBOARD_PHOTOGRAPHER}',
    DASHBOARD_CLIENT: '${DASHBOARD_CLIENT}',
    LOGIN_PAGE: '${LOGIN_PAGE}',
};

// Computed URLs (no hardcoded values)
if (window.GALERLY_ENV_CONFIG.IS_LOCALSTACK) {
    const cfg = window.GALERLY_ENV_CONFIG;
    
    cfg.API_BASE_URL = \`\${cfg.BACKEND_PROTOCOL}://\${cfg.BACKEND_HOST}:\${cfg.BACKEND_PORT}/v1\`;
    
    // CDN Base URL (LocalStack S3)
    cfg.CDN_BASE_URL = \`\${cfg.BACKEND_PROTOCOL}://\${cfg.LOCALSTACK_HOST}:\${cfg.LOCALSTACK_PORT}/\${cfg.S3_RENDITIONS_BUCKET}\`;
    
    console.log('🔧 LocalStack Mode - Configuration Loaded');
    console.log('   Backend:', cfg.API_BASE_URL);
    console.log('   CDN:', cfg.CDN_BASE_URL);
} else {
    const baseDomain = hostname.replace(/^www\./, '');
    window.GALERLY_ENV_CONFIG.API_BASE_URL = \`https://api.\${baseDomain}/xb667e3fa92f9776468017a9758f31ba4/v1\`;
    window.GALERLY_ENV_CONFIG.CDN_BASE_URL = \`https://cdn.\${baseDomain}\`;
}
EOF

echo -e "${GREEN}✅ Generated $OUTPUT_FILE${NC}"
echo -e "${GREEN}📋 Configuration Summary:${NC}"
echo -e "   Environment: ${ENVIRONMENT}"
echo -e "   LocalStack: ${IS_LOCALSTACK}"
echo -e "   Backend: ${BACKEND_PROTOCOL}://${BACKEND_HOST}:${BACKEND_PORT}"
echo -e "   CDN Bucket: ${S3_RENDITIONS_BUCKET}"
echo -e "${GREEN}✅ Frontend configuration ready${NC}"

