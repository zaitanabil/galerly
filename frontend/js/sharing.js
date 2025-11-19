/**
 * Social Sharing Functionality
 * Share galleries and photos to social media, copy links, and embed galleries
 */

// Cache for share information (5 minute TTL)
const shareInfoCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const MAX_CACHE_SIZE = 100; // Maximum number of cached items

/**
 * Clean up expired cache entries
 */
function cleanupCache() {
    const now = Date.now();
    for (const [key, value] of shareInfoCache.entries()) {
        if (now - value.timestamp >= CACHE_TTL) {
            shareInfoCache.delete(key);
        }
    }
    
    // If cache is still too large, remove oldest entries
    if (shareInfoCache.size > MAX_CACHE_SIZE) {
        const entries = Array.from(shareInfoCache.entries())
            .sort((a, b) => a[1].timestamp - b[1].timestamp);
        const toRemove = entries.slice(0, shareInfoCache.size - MAX_CACHE_SIZE);
        toRemove.forEach(([key]) => shareInfoCache.delete(key));
    }
}

/**
 * Get cached share info or fetch new
 */
function getCachedShareInfo(key) {
    cleanupCache(); // Clean up expired entries on access
    const cached = shareInfoCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    if (cached) {
        shareInfoCache.delete(key);
    }
    return null;
}

/**
 * Set cached share info
 */
function setCachedShareInfo(key, data) {
    cleanupCache(); // Clean up before adding
    shareInfoCache.set(key, {
        data: data,
        timestamp: Date.now()
    });
}

// Periodic cleanup every 2 minutes
if (typeof setInterval !== 'undefined') {
    setInterval(cleanupCache, 2 * 60 * 1000);
}

/**
 * Get share information for a gallery with retry logic and caching
 */
async function getGalleryShareInfo(galleryId, authenticated = false, retries = 2) {
    if (!galleryId) {
        throw new Error('Gallery ID is required');
    }
    
    // Check cache first
    const cacheKey = `gallery_${galleryId}_${authenticated}`;
    const cached = getCachedShareInfo(cacheKey);
    if (cached) {
        return cached;
    }
    
    try {
        // Use apiRequest helper if authenticated, otherwise use fetch for public access
        if (authenticated && typeof window.apiRequest === 'function') {
            const data = await window.apiRequest(`share/gallery/${galleryId}`);
            setCachedShareInfo(cacheKey, data);
            return data;
        } else {
            // Public access - use fetch directly with timeout
            const apiUrl = window.CONFIG?.API_BASE_URL || window.API_BASE_URL || '';
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            try {
                const response = await fetch(`${apiUrl}/share/gallery/${galleryId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error = new Error(errorData.error || errorData.message || `Failed to get share info: ${response.statusText}`);
                error.status = response.status;
                throw error;
            }
            
                const data = await response.json();
                setCachedShareInfo(cacheKey, data);
                return data;
            } catch (fetchError) {
                clearTimeout(timeoutId);
                if (fetchError.name === 'AbortError') {
                    throw new Error('Request timeout - please check your connection');
                }
                throw fetchError;
            }
        }
    } catch (error) {
        console.error('Error getting gallery share info:', error);
        // Retry on network errors or 5xx errors
        if (retries > 0 && (error.status >= 500 || !error.status || error.message.includes('timeout'))) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
            return getGalleryShareInfo(galleryId, authenticated, retries - 1);
        }
        throw error;
    }
}

/**
 * Get share information for a photo with retry logic
 */
async function getPhotoShareInfo(photoId, authenticated = false, retries = 2) {
    if (!photoId) {
        throw new Error('Photo ID is required');
    }
    
    // Check cache first
    const cacheKey = `photo_${photoId}_${authenticated}`;
    const cached = getCachedShareInfo(cacheKey);
    if (cached) {
        return cached;
    }
    
    try {
        // Use apiRequest helper if authenticated, otherwise use fetch for public access
        if (authenticated && typeof window.apiRequest === 'function') {
            const data = await window.apiRequest(`share/photo/${photoId}`);
            setCachedShareInfo(cacheKey, data);
            return data;
        } else {
            // Public access - use fetch directly with timeout
            const apiUrl = window.CONFIG?.API_BASE_URL || window.API_BASE_URL || '';
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            try {
                const response = await fetch(`${apiUrl}/share/photo/${photoId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    const error = new Error(errorData.error || errorData.message || `Failed to get share info: ${response.statusText}`);
                    error.status = response.status;
                    throw error;
                }
                
                const data = await response.json();
                setCachedShareInfo(cacheKey, data);
                return data;
            } catch (fetchError) {
                clearTimeout(timeoutId);
                if (fetchError.name === 'AbortError') {
                    throw new Error('Request timeout - please check your connection');
                }
                throw fetchError;
            }
        }
    } catch (error) {
        console.error('Error getting photo share info:', error);
        // Retry on network errors or 5xx errors
        if (retries > 0 && (error.status >= 500 || !error.status || error.message.includes('timeout'))) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
            return getPhotoShareInfo(photoId, authenticated, retries - 1);
        }
        throw error;
    }
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    if (!text) {
        console.error('No text provided to copy');
        return false;
    }
    
    try {
        // Modern clipboard API (preferred)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            return true;
        }
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.top = '0';
        textArea.style.left = '0';
        textArea.style.width = '2em';
        textArea.style.height = '2em';
        textArea.style.padding = '0';
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';
        textArea.style.background = 'transparent';
        textArea.style.opacity = '0';
        textArea.setAttribute('readonly', '');
        textArea.setAttribute('aria-hidden', 'true');
        
        document.body.appendChild(textArea);
        
        // Select text
        if (navigator.userAgent.match(/ipad|iphone/i)) {
            // iOS requires a different approach
            const range = document.createRange();
            range.selectNodeContents(textArea);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            textArea.setSelectionRange(0, 999999);
        } else {
            textArea.select();
        }
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful;
        } catch (err) {
            document.body.removeChild(textArea);
            console.error('Fallback copy failed:', err);
            return false;
        }
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
    }
}

/**
 * Check if native Web Share API is available
 */
function isWebShareSupported() {
    return navigator.share && typeof navigator.share === 'function';
}

/**
 * Use native Web Share API if available (mobile devices)
 */
async function nativeShare(title, text, url) {
    if (!isWebShareSupported()) {
        return false;
    }
    
    // Validate inputs
    if (!url || typeof url !== 'string') {
        console.error('Invalid URL for native share');
        return false;
    }
    
    try {
        const shareData = {
            url: url
        };
        
        // Only include title and text if provided (some platforms don't support them)
        if (title && typeof title === 'string') {
            shareData.title = title;
        }
        if (text && typeof text === 'string') {
            shareData.text = text;
        }
        
        await navigator.share(shareData);
        return true;
    } catch (error) {
        // User cancelled or error occurred
        if (error.name !== 'AbortError') {
            console.error('Error sharing:', error);
        }
        return false;
    }
}

/**
 * Generate QR code URL using a free QR code service
 */
function generateQRCodeUrl(text, size = 200) {
    if (!text || typeof text !== 'string') {
        console.error('Invalid text for QR code generation');
        return '';
    }
    
    // Validate and sanitize size
    const sanitizedSize = Math.max(100, Math.min(1000, parseInt(size, 10) || 200));
    
    const encodedText = encodeURIComponent(text);
    return `https://api.qrserver.com/v1/create-qr-code/?size=${sanitizedSize}x${sanitizedSize}&data=${encodedText}`;
}

/**
 * Show a temporary notification
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        background: ${type === 'success' ? '#98FF98' : '#FF6F61'};
        color: ${type === 'success' ? '#1D1D1F' : '#FFFFFF'};
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 15px;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            document.body.removeChild(notification);
            document.head.removeChild(style);
        }, 300);
    }, 3000);
}

/**
 * Share gallery to social media
 */
async function shareGalleryToSocial(galleryId, platform, authenticated = false) {
    try {
        // Validate inputs
        if (!galleryId || typeof galleryId !== 'string') {
            throw new Error('Invalid gallery ID');
        }
        if (!platform || typeof platform !== 'string') {
            throw new Error('Invalid platform');
        }
        
        const shareInfo = await getGalleryShareInfo(galleryId, authenticated);
        if (!shareInfo || !shareInfo.share_url) {
            throw new Error('Invalid share information received');
        }
        const shareUrl = shareInfo.share_url;
        const galleryName = shareInfo.gallery_name || 'Gallery';
        
        // Try native share API first (mobile devices)
        if (platform === 'native' && isWebShareSupported()) {
            const shared = await nativeShare(galleryName, `Check out this gallery: ${galleryName}`, shareUrl);
            if (shared) {
                // Track share action (analytics)
                if (typeof window.trackGalleryShare === 'function' && window.currentGalleryId) {
                    try {
                        window.trackGalleryShare(window.currentGalleryId, 'native', {
                            timestamp: new Date().toISOString(),
                            share_url: shareUrl
                        });
                    } catch (err) {
                    }
                }
                return;
            }
        }
        
        const encodedUrl = encodeURIComponent(shareUrl);
        const encodedName = encodeURIComponent(galleryName);
        
        let shareLink = '';
        
        switch (platform) {
            case 'facebook':
                shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
                break;
            case 'twitter':
                shareLink = `https://x.com/intent/tweet?url=${encodedUrl}&text=${encodedName}`;
                break;
            case 'instagram':
                // Instagram doesn't have a direct web share URL, so we copy the link and notify the user
                await copyToClipboard(shareUrl);
                showNotification('Link copied! Open Instagram app to share', 'success');
                return;
            case 'linkedin':
                shareLink = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`;
                break;
            case 'pinterest':
                shareLink = `https://pinterest.com/pin/create/button/?url=${encodedUrl}&description=${encodedName}`;
                break;
            case 'whatsapp':
                shareLink = `https://wa.me/?text=${encodedUrl} ${encodedName}`;
                break;
            case 'email':
                shareLink = `mailto:?subject=${encodedName}&body=${encodedUrl}`;
                break;
            default:
                throw new Error(`Unknown platform: ${platform}`);
        }
        
        // Track share action (analytics)
        if (typeof window.trackGalleryShare === 'function' && window.currentGalleryId) {
            try {
                window.trackGalleryShare(window.currentGalleryId, platform, {
                    timestamp: new Date().toISOString(),
                    share_url: shareUrl
                });
            } catch (err) {
            }
        }
        
        // Show feedback
        showNotification(`Opening ${platform}...`, 'success');
        
        if (platform === 'email') {
            window.location.href = shareLink;
        } else {
            window.open(shareLink, '_blank', 'width=600,height=400');
        }
    } catch (error) {
        console.error('Error sharing gallery:', error);
        showNotification('Failed to share gallery', 'error');
    }
}

/**
 * Share photo to social media
 */
async function sharePhotoToSocial(photoId, platform, authenticated = false) {
    try {
        // Validate inputs
        if (!photoId || typeof photoId !== 'string') {
            throw new Error('Invalid photo ID');
        }
        if (!platform || typeof platform !== 'string') {
            throw new Error('Invalid platform');
        }
        
        const shareInfo = await getPhotoShareInfo(photoId, authenticated);
        if (!shareInfo || !shareInfo.share_url) {
            throw new Error('Invalid share information received');
        }
        const shareUrl = shareInfo.share_url;
        const photoUrl = shareInfo.direct_image_url || '';
        const galleryName = shareInfo.gallery_name || 'Photo';
        
        // Try native share API first (mobile devices)
        if (platform === 'native' && isWebShareSupported()) {
            const shared = await nativeShare(galleryName, `Check out this photo from ${galleryName}`, shareUrl);
            if (shared) {
                // Track share action (analytics)
                if (typeof window.trackPhotoShare === 'function' && photoId) {
                    try {
                        window.trackPhotoShare(photoId, 'native', {
                            timestamp: new Date().toISOString(),
                            share_url: shareUrl,
                            gallery_id: shareInfo.gallery_id
                        });
                    } catch (err) {
                    }
                }
                return;
            }
        }
        
        const encodedUrl = encodeURIComponent(shareUrl);
        const encodedPhotoUrl = encodeURIComponent(photoUrl);
        const encodedName = encodeURIComponent(galleryName);
        
        let shareLink = '';
        
        switch (platform) {
            case 'facebook':
                shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
                break;
            case 'twitter':
                shareLink = `https://x.com/intent/tweet?url=${encodedUrl}&text=${encodedName}`;
                break;
            case 'instagram':
                // Instagram doesn't have a direct web share URL, so we copy the link and notify the user
                await copyToClipboard(shareUrl);
                showNotification('Link copied! Open Instagram app to share', 'success');
                return;
            case 'pinterest':
                shareLink = `https://pinterest.com/pin/create/button/?url=${encodedUrl}&media=${encodedPhotoUrl}&description=${encodedName}`;
                break;
            case 'whatsapp':
                shareLink = `https://wa.me/?text=${encodedUrl} ${encodedName}`;
                break;
            case 'email':
                shareLink = `mailto:?subject=${encodedName}&body=${encodedUrl}`;
                break;
            default:
                throw new Error(`Unknown platform: ${platform}`);
        }
        
        // Track share action (analytics)
        if (typeof window.trackPhotoShare === 'function' && photoId) {
            try {
                window.trackPhotoShare(photoId, platform, {
                    timestamp: new Date().toISOString(),
                    share_url: shareUrl,
                    gallery_id: shareInfo.gallery_id
                });
            } catch (err) {
            }
        }
        
        // Show feedback
        showNotification(`Opening ${platform}...`, 'success');
        
        if (platform === 'email') {
            window.location.href = shareLink;
        } else {
            window.open(shareLink, '_blank', 'width=600,height=400');
        }
    } catch (error) {
        console.error('Error sharing photo:', error);
        showNotification('Failed to share photo', 'error');
    }
}

/**
 * Copy gallery link to clipboard
 */
async function copyGalleryLink(galleryId, authenticated = false) {
    try {
        const shareInfo = await getGalleryShareInfo(galleryId, authenticated);
        const success = await copyToClipboard(shareInfo.share_url);
        
        if (success) {
            showNotification('Gallery link copied to clipboard!');
        } else {
            showNotification('Failed to copy link', 'error');
        }
    } catch (error) {
        console.error('Error copying gallery link:', error);
        showNotification('Failed to copy link', 'error');
    }
}

/**
 * Copy photo link to clipboard
 */
async function copyPhotoLink(photoId, authenticated = false) {
    try {
        const shareInfo = await getPhotoShareInfo(photoId, authenticated);
        const success = await copyToClipboard(shareInfo.share_url);
        
        if (success) {
            showNotification('Photo link copied to clipboard!');
        } else {
            showNotification('Failed to copy link', 'error');
        }
    } catch (error) {
        console.error('Error copying photo link:', error);
        showNotification('Failed to copy link', 'error');
    }
}

/**
 * Copy embed code to clipboard
 */
async function copyEmbedCode(galleryId, authenticated = false) {
    try {
        const shareInfo = await getGalleryShareInfo(galleryId, authenticated);
        const success = await copyToClipboard(shareInfo.embed_code);
        
        if (success) {
            showNotification('Embed code copied to clipboard!');
        } else {
            showNotification('Failed to copy embed code', 'error');
        }
    } catch (error) {
        console.error('Error copying embed code:', error);
        showNotification('Failed to copy embed code', 'error');
    }
}

/**
 * Show share modal for gallery
 */
function showGalleryShareModal(galleryId, authenticated = false) {
    // Close existing modal if open
    const existingModal = document.getElementById('shareModal');
    if (existingModal) {
        closeShareModal();
    }
    
    const modal = document.createElement('div');
    modal.id = 'shareModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(29, 29, 31, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.2s ease-out;
        padding: 24px;
        box-sizing: border-box;
    `;
    
    // Check if mobile
    const isMobile = window.innerWidth <= 768;
    
    modal.innerHTML = `
        <div style="
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: ${isMobile ? '20px' : '28px'};
            padding: 0;
            max-width: ${isMobile ? '100%' : '520px'};
            width: 100%;
            max-height: calc(100vh - 48px);
            overflow: hidden;
            position: relative;
            box-sizing: border-box;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        " role="dialog" aria-labelledby="shareModalTitle" aria-modal="true">
            <!-- Header -->
            <div style="
                padding: ${isMobile ? '32px 24px 24px' : '40px 40px 32px'};
                border-bottom: 1px solid rgba(29, 29, 31, 0.1);
                position: relative;
            ">
                <h2 id="shareModalTitle" style="
                    margin: 0;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: ${isMobile ? '28px' : '32px'};
                    font-weight: 300;
                    color: #1D1D1F;
                    letter-spacing: -0.03em;
                    padding-right: 48px;
                    line-height: 1.2;
                ">Share</h2>
                <button onclick="closeShareModal()" aria-label="Close" style="
                    position: absolute;
                    top: ${isMobile ? '32px' : '40px'};
                    right: ${isMobile ? '24px' : '40px'};
                    background: transparent;
                    border: none;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    color: #86868B;
                    font-size: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='#F5F5F7'; this.style.color='#1D1D1F'" onmouseout="this.style.background='transparent'; this.style.color='#86868B'">&times;</button>
            </div>
            
            <!-- Content -->
            <div style="
                overflow-y: auto;
                max-height: calc(100vh - ${isMobile ? '180px' : '220px'});
            ">
                <div id="shareModalLoading" style="
                    text-align: center;
                    padding: ${isMobile ? '48px 24px' : '64px 40px'};
                ">
                    <div style="
                        display: inline-block;
                        width: 40px;
                        height: 40px;
                        border: 2px solid #F5F5F7;
                        border-top: 2px solid #0066CC;
                        border-radius: 50%;
                        animation: spin 0.8s linear infinite;
                    "></div>
                    <p style="
                        margin-top: 24px;
                        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 15px;
                        font-weight: 400;
                        color: #86868B;
                    ">Loading...</p>
            </div>
            
                <div id="shareModalContent" style="display: none; padding: ${isMobile ? '32px 24px' : '40px'};">
                    <!-- Link Section -->
                    <div style="margin-bottom: 32px;">
                        <label style="
                            display: block;
                            margin-bottom: 16px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 400;
                            font-size: 13px;
                            color: #86868B;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        ">LINK</label>
                        <div style="
                            display: flex;
                            gap: 8px;
                            ${isMobile ? 'flex-direction: column;' : ''}
                        ">
                            <input type="text" id="shareLinkInput" readonly aria-label="Share link" style="
                                flex: 1;
                                padding: ${isMobile ? '14px 16px' : '16px 18px'};
                                background: #F5F5F7;
                                border: none;
                                border-radius: 12px;
                                font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
                                font-size: 14px;
                                color: #1D1D1F;
                                transition: all 0.2s ease;
                            " onclick="this.select();">
                            <button id="copyLinkBtn" onclick="copyGalleryLinkFromModal('${galleryId}', ${authenticated})" aria-label="Copy link" style="
                                padding: ${isMobile ? '14px 32px' : '16px 36px'};
                                background: #0066CC;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                                font-weight: 500;
                                font-size: 15px;
                                transition: all 0.2s ease;
                                white-space: nowrap;
                            " onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">Copy</button>
                    </div>
                </div>
            
                    <!-- Social Section -->
                    <div style="margin-bottom: 32px;">
                        <label style="
                            display: block;
                            margin-bottom: 16px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 400;
                            font-size: 13px;
                            color: #86868B;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        ">SHARE</label>
                        <div style="
                            display: grid;
                            grid-template-columns: repeat(${isMobile ? '3' : '7'}, 1fr);
                            gap: 12px;
                        ">
                            <button onclick="shareGalleryToSocial('${galleryId}', 'facebook', ${authenticated})" aria-label="Facebook" title="Facebook" style="
                                padding: 18px;
                                background: #1877F2;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'twitter', ${authenticated})" aria-label="X" title="X" style="
                                padding: 18px;
                                background: #000000;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'instagram', ${authenticated})" aria-label="Instagram" title="Instagram" style="
                                padding: 18px;
                                background: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%,#d6249f 60%,#285AEB 90%);
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'linkedin', ${authenticated})" aria-label="LinkedIn" title="LinkedIn" style="
                                padding: 18px;
                                background: #0077B5;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'pinterest', ${authenticated})" aria-label="Pinterest" title="Pinterest" style="
                                padding: 18px;
                                background: #BD081C;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'whatsapp', ${authenticated})" aria-label="WhatsApp" title="WhatsApp" style="
                                padding: 18px;
                                background: #25D366;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    </button>
                            <button onclick="shareGalleryToSocial('${galleryId}', 'email', ${authenticated})" aria-label="Email" title="Email" style="
                                padding: 18px;
                                background: #636366;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                    </button>
                </div>
            </div>
            
                    <!-- QR Code Section -->
                    <div>
                        <label style="
                            display: block;
                            margin-bottom: 16px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 400;
                            font-size: 13px;
                            color: #86868B;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        ">QR CODE</label>
                        <div style="
                            text-align: center;
                            padding: ${isMobile ? '32px 24px' : '40px'};
                            background: #F5F5F7;
                            border-radius: 16px;
                        ">
                            <p style="
                                color: #86868B;
                                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 14px;
                                font-weight: 400;
                                margin: 0 0 24px 0;
                            ">Scan to open</p>
                            <img id="qrCodeImage" src="" alt="QR Code" style="
                                max-width: ${isMobile ? '180px' : '200px'};
                                width: 100%;
                                height: auto;
                                border-radius: 12px;
                                display: none;
                                margin: 0 auto;
                                background: white;
                                padding: 16px;
                            ">
                </div>
            </div>
                </div>
            </div>
        </div>
    `;
    
    // Add spinner and fade animations (store reference for cleanup)
    if (!shareModalStyleElement || !shareModalStyleElement.parentNode) {
        shareModalStyleElement = document.createElement('style');
        shareModalStyleElement.id = 'shareModalSpinnerStyle';
        shareModalStyleElement.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(shareModalStyleElement);
    }
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    
    document.body.appendChild(modal);
    
    // Load share info and populate inputs
    getGalleryShareInfo(galleryId, authenticated).then(shareInfo => {
        if (!shareInfo) {
            throw new Error('No share information received');
        }
        
        // Validate share URL exists
        if (!shareInfo.share_url) {
            throw new Error('Share URL not available for this gallery');
        }
        
        // Hide loading, show content
        const loadingEl = document.getElementById('shareModalLoading');
        const contentEl = document.getElementById('shareModalContent');
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'block';
        
        const linkInput = document.getElementById('shareLinkInput');
        const embedInput = document.getElementById('embedCodeInput');
        const qrCodeImage = document.getElementById('qrCodeImage');
        
        if (linkInput) {
            linkInput.value = shareInfo.share_url || '';
        }
        if (embedInput && shareInfo.embed_code) {
            embedInput.value = shareInfo.embed_code;
        }
        if (qrCodeImage && shareInfo.share_url) {
            qrCodeImage.src = generateQRCodeUrl(shareInfo.share_url, 200);
            qrCodeImage.style.display = 'block';
        }
        
        // Track share modal view (analytics) - only track once per modal open
        if (typeof window.trackGalleryShare === 'function' && window.currentGalleryId) {
            try {
                window.trackGalleryShare(window.currentGalleryId, 'modal_viewed', {
                    timestamp: new Date().toISOString()
                });
            } catch (err) {
            }
        }
    }).catch(error => {
        console.error('Error loading share info:', error);
        
        // Provide user-friendly error messages based on error status
        let errorMessage = 'Failed to load share information';
        if (error.status === 404) {
            errorMessage = 'Gallery not found';
        } else if (error.status === 403) {
            errorMessage = 'Access denied';
        } else if (error.status === 400) {
            errorMessage = error.message || 'Invalid gallery ID';
        } else if (error.message) {
            errorMessage = error.message;
        } else if (error.details?.error) {
            errorMessage = error.details.error;
        }
        
        showNotification(errorMessage, 'error');
        
        // Hide loading on error and show retry option
        const loadingEl = document.getElementById('shareModalLoading');
        const contentEl = document.getElementById('shareModalContent');
        if (loadingEl) {
            loadingEl.innerHTML = `
                <p style="color: #FF6F61; margin-bottom: 24px; font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; font-weight: 400;">${errorMessage}</p>
                <button id="retryShareBtn" onclick="retryShareInfo('${galleryId}', ${authenticated}, 'gallery')" style="padding: 12px 24px; background: #0066CC; color: white; border: none; border-radius: 12px; cursor: pointer; font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif; font-weight: 500; font-size: 15px; transition: all 0.2s ease;" onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">Try Again</button>
            `;
        }
    });
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeShareModal();
        }
    });
    
    // Keyboard navigation support
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeShareModal();
        }
        // Trap focus within modal
        if (e.key === 'Tab') {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    });
    
    // Focus first element when modal opens
    setTimeout(() => {
        const firstInput = modal.querySelector('input, button');
        if (firstInput) {
            firstInput.focus();
        }
    }, 100);
}

/**
 * Show share modal for photo
 */
function showPhotoShareModal(photoId, authenticated = false) {
    // Validate inputs
    if (!photoId || typeof photoId !== 'string') {
        console.error('Invalid photo ID provided to share modal');
        showNotification('Invalid photo ID', 'error');
        return;
    }
    
    // Close existing modal if open
    const existingModal = document.getElementById('shareModal');
    if (existingModal) {
        closeShareModal();
    }
    
    const modal = document.createElement('div');
    modal.id = 'shareModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.2s ease-out;
        padding: 20px;
        box-sizing: border-box;
    `;
    
    // Check if mobile
    const isMobile = window.innerWidth <= 768;
    
    modal.innerHTML = `
        <div style="
            background: var(--background-secondary, #ffffff);
            border-radius: ${isMobile ? 'var(--border-radius-l, 20px)' : 'var(--border-radius-xl, 28px)'};
            padding: 0;
            max-width: ${isMobile ? '100%' : '560px'};
            width: 100%;
            max-height: calc(100vh - ${isMobile ? '20px' : '40px'});
            overflow: hidden;
            position: relative;
            box-sizing: border-box;
            box-shadow: var(--shadow-default, 0 8px 32px 0 rgba(0, 0, 0, 0.15));
            border: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
        " role="dialog" aria-labelledby="shareModalTitle" aria-modal="true">
            <!-- Header -->
            <div style="
                padding: ${isMobile ? '24px 20px 20px 20px' : '32px 32px 24px 32px'};
                border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
                position: relative;
            ">
                <h2 id="shareModalTitle" style="
                    margin: 0;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: ${isMobile ? '22px' : '28px'};
                    font-weight: 600;
                    color: var(--text-primary, #1D1D1F);
                    letter-spacing: -0.02em;
                    padding-right: 40px;
                ">Share Photo</h2>
                <button onclick="closeShareModal()" aria-label="Close share modal" style="
                    position: absolute;
                    top: ${isMobile ? '24px' : '32px'};
                    right: ${isMobile ? '20px' : '32px'};
                    background: var(--background-primary, #F5F5F7);
                    border: none;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    color: var(--text-secondary, #86868B);
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='var(--primary-200, #E0E0E0)'" onmouseout="this.style.background='var(--background-primary, #F5F5F7)'">&times;</button>
            </div>
            
            <!-- Content -->
            <div style="
                overflow-y: auto;
                max-height: calc(100vh - ${isMobile ? '120px' : '180px'});
            ">
                <div id="shareModalLoading" style="
                    text-align: center;
                    padding: ${isMobile ? '40px 20px' : '60px 32px'};
                    color: var(--text-secondary, #86868B);
                ">
                    <div style="
                        display: inline-block;
                        width: 40px;
                        height: 40px;
                        border: 3px solid var(--primary-200, #E0E0E0);
                        border-top: 3px solid var(--color-blue, #0066CC);
                        border-radius: 50%;
                        animation: spin 0.8s linear infinite;
                    "></div>
                    <p style="
                        margin-top: 20px;
                        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 15px;
                        font-weight: 400;
                        color: var(--text-secondary, #86868B);
                    ">Loading share information...</p>
            </div>
            
                <div id="shareModalContent" style="display: none; padding: ${isMobile ? '24px 20px' : '32px'};">
                    <!-- Share Link Section -->
                    <div style="margin-bottom: ${isMobile ? '28px' : '36px'};">
                        <label style="
                            display: block;
                            margin-bottom: 14px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 600;
                            font-size: 15px;
                            color: var(--text-primary, #1D1D1F);
                        ">Share Link</label>
                        <div style="
                            display: flex;
                            gap: 10px;
                            ${isMobile ? 'flex-direction: column;' : ''}
                        ">
                            <input type="text" id="shareLinkInput" readonly aria-label="Share link" style="
                                flex: 1;
                                padding: ${isMobile ? '14px 16px' : '15px 18px'};
                                background: var(--background-primary, #F5F5F7);
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
                                font-size: ${isMobile ? '13px' : '14px'};
                                color: var(--text-primary, #1D1D1F);
                                transition: all 0.2s ease;
                            " onclick="this.select();">
                            <button id="copyLinkBtn" onclick="copyPhotoLinkFromModal('${photoId}', ${authenticated})" aria-label="Copy share link" style="
                                padding: ${isMobile ? '14px 28px' : '15px 32px'};
                                background: var(--color-blue, #0066CC);
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                                font-weight: 600;
                                font-size: 15px;
                                transition: all 0.2s ease;
                                white-space: nowrap;
                            " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Copy Link</button>
                    </div>
                </div>
            
                    <!-- Social Media Section -->
                    <div style="margin-bottom: ${isMobile ? '28px' : '36px'};">
                        <label style="
                            display: block;
                            margin-bottom: 18px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 600;
                            font-size: 15px;
                            color: var(--text-primary, #1D1D1F);
                        ">Share to</label>
                        <div id="socialButtonsContainer" style="
                            display: grid;
                            grid-template-columns: repeat(${isMobile ? '3' : '6'}, 1fr);
                            gap: ${isMobile ? '10px' : '12px'};
                        ">
                            <button onclick="sharePhotoToSocial('${photoId}', 'facebook', ${authenticated})" aria-label="Share to Facebook" title="Facebook" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: #1877F2;
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                    </button>
                            <button onclick="sharePhotoToSocial('${photoId}', 'twitter', ${authenticated})" aria-label="Share to X" title="X" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: #000000;
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </button>
                            <button onclick="sharePhotoToSocial('${photoId}', 'instagram', ${authenticated})" aria-label="Share to Instagram" title="Instagram" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%,#d6249f 60%,#285AEB 90%);
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                    </button>
                            <button onclick="sharePhotoToSocial('${photoId}', 'pinterest', ${authenticated})" aria-label="Share to Pinterest" title="Pinterest" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: #BD081C;
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>
                    </button>
                            <button onclick="sharePhotoToSocial('${photoId}', 'whatsapp', ${authenticated})" aria-label="Share to WhatsApp" title="WhatsApp" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: #25D366;
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    </button>
                            <button onclick="sharePhotoToSocial('${photoId}', 'email', ${authenticated})" aria-label="Share via Email" title="Email" style="
                                padding: ${isMobile ? '16px' : '18px'};
                                background: #636366;
                                color: white;
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-size: 24px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                transition: all 0.2s ease;
                                aspect-ratio: 1;
                            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                    </button>
                </div>
                ${isWebShareSupported() ? `
                            <button onclick="sharePhotoToSocial('${photoId}', 'native', ${authenticated})" aria-label="More sharing options" style="
                                padding: ${isMobile ? '14px' : '16px'};
                                background: var(--background-primary, #F5F5F7);
                                color: var(--text-primary, #1D1D1F);
                                border: none;
                                border-radius: var(--border-radius-s, 12px);
                                cursor: pointer;
                                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                                font-weight: 600;
                                font-size: ${isMobile ? '14px' : '15px'};
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                gap: 8px;
                                margin-top: 12px;
                                width: 100%;
                                transition: all 0.2s ease;
                            " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='var(--background-primary, #F5F5F7)'">
                        <span>More</span>
                    </button>
                ` : ''}
            </div>
            
                    <!-- QR Code Section -->
                    <div>
                        <label style="
                            display: block;
                            margin-bottom: 14px;
                            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 600;
                            font-size: 15px;
                            color: var(--text-primary, #1D1D1F);
                        ">QR Code</label>
                        <div id="qrCodeContainer" style="
                            text-align: center;
                            padding: ${isMobile ? '24px' : '28px'};
                            background: var(--background-primary, #F5F5F7);
                            border-radius: var(--border-radius-m, 16px);
                            border: none;
                        ">
                            <p style="
                                color: var(--text-secondary, #86868B);
                                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 14px;
                                font-weight: 400;
                                margin: 0 0 18px 0;
                            ">Scan to view photo</p>
                            <img id="qrCodeImage" src="" alt="QR Code" style="
                                max-width: ${isMobile ? '180px' : '220px'};
                                width: 100%;
                                height: auto;
                                border-radius: var(--border-radius-s, 12px);
                                display: none;
                                background: white;
                                padding: 12px;
                                margin: 0 auto;
                            ">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    
    document.body.appendChild(modal);
    
    // Load share info and populate input
    getPhotoShareInfo(photoId, authenticated).then(shareInfo => {
        if (!shareInfo) {
            throw new Error('No share information received');
        }
        
        // Validate share URL exists
        if (!shareInfo.share_url) {
            throw new Error('Share URL not available for this photo');
        }
        
        // Hide loading, show content
        const loadingEl = document.getElementById('shareModalLoading');
        const contentEl = document.getElementById('shareModalContent');
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'block';
        
        const linkInput = document.getElementById('shareLinkInput');
        const qrCodeImage = document.getElementById('qrCodeImage');
        
        if (linkInput) {
            linkInput.value = shareInfo.share_url || '';
        }
        if (qrCodeImage && shareInfo.share_url) {
            qrCodeImage.src = generateQRCodeUrl(shareInfo.share_url, 200);
            qrCodeImage.style.display = 'block';
        }
        
        // Track photo share modal view (analytics) - only track once per modal open
        if (typeof window.trackPhotoShare === 'function' && photoId) {
            try {
                window.trackPhotoShare(photoId, 'modal_viewed', {
                    timestamp: new Date().toISOString()
                });
            } catch (err) {
            }
        }
    }).catch(error => {
        console.error('Error loading share info:', error);
        
        // Provide user-friendly error messages based on error status
        let errorMessage = 'Failed to load share information';
        if (error.status === 404) {
            errorMessage = 'Photo not found. It may have been deleted or you may not have access.';
        } else if (error.status === 403) {
            errorMessage = 'Access denied. This photo may be in a private gallery.';
        } else if (error.status === 400) {
            errorMessage = error.message || 'Invalid photo ID.';
        } else if (error.message) {
            errorMessage = error.message;
        } else if (error.details?.error) {
            errorMessage = error.details.error;
        }
        
        showNotification(errorMessage, 'error');
        
        // Hide loading on error and show retry option
        const loadingEl = document.getElementById('shareModalLoading');
        const contentEl = document.getElementById('shareModalContent');
        if (loadingEl) {
            loadingEl.innerHTML = `
                <p style="color: #f44336; margin-bottom: 16px;">${errorMessage}</p>
                <button id="retryShareBtn" onclick="retryShareInfo('${photoId}', ${authenticated}, 'photo')" style="padding: 8px 16px; background: #0066CC; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Retry</button>
            `;
        }
    });
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeShareModal();
        }
    });
    
    // Keyboard navigation support
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeShareModal();
        }
        // Trap focus within modal
        if (e.key === 'Tab') {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    });
    
    // Focus first element when modal opens
    setTimeout(() => {
        const firstInput = modal.querySelector('input, button');
        if (firstInput) {
            firstInput.focus();
        }
    }, 100);
}

/**
 * Close share modal
 */
// Store modal style element reference for cleanup
let shareModalStyleElement = null;

function closeShareModal() {
    const modal = document.getElementById('shareModal');
    if (modal) {
        modal.style.animation = 'fadeIn 0.2s ease-out reverse';
        setTimeout(() => {
            if (modal.parentNode) {
                document.body.removeChild(modal);
            }
            // Clean up spinner animation style if it exists
            if (shareModalStyleElement && shareModalStyleElement.parentNode) {
                document.head.removeChild(shareModalStyleElement);
                shareModalStyleElement = null;
            }
            // Restore body scroll
            document.body.style.overflow = '';
        }, 200);
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('shareModal');
        if (modal && modal.style.display !== 'none') {
            closeShareModal();
        }
    }
});

/**
 * Helper functions for modal buttons (need to be global)
 */
window.copyGalleryLinkFromModal = async function(galleryId, authenticated) {
    const linkInput = document.getElementById('shareLinkInput');
    const copyBtn = document.getElementById('copyLinkBtn');
    
    if (linkInput) {
        const success = await copyToClipboard(linkInput.value);
        if (success) {
            // Visual feedback
            if (copyBtn) {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied';
                copyBtn.style.background = '#98FF98';
                copyBtn.style.color = '#1D1D1F';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.background = '#0066CC';
                    copyBtn.style.color = 'white';
                }, 2000);
            }
            showNotification('Link copied');
        } else {
            showNotification('Failed to copy link', 'error');
        }
    }
};

window.copyPhotoLinkFromModal = async function(photoId, authenticated) {
    const linkInput = document.getElementById('shareLinkInput');
    const copyBtn = document.getElementById('copyLinkBtn');
    
    if (linkInput) {
        const success = await copyToClipboard(linkInput.value);
        if (success) {
            // Visual feedback
            if (copyBtn) {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied';
                copyBtn.style.background = '#98FF98';
                copyBtn.style.color = '#1D1D1F';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.background = '#0066CC';
                    copyBtn.style.color = 'white';
                }, 2000);
            }
            showNotification('Link copied');
        } else {
            showNotification('Failed to copy link', 'error');
        }
    }
};

window.copyEmbedCodeFromModal = async function(galleryId, authenticated) {
    const embedInput = document.getElementById('embedCodeInput');
    const copyBtn = embedInput?.nextElementSibling;
    
    if (embedInput) {
        const success = await copyToClipboard(embedInput.value);
        if (success) {
            // Visual feedback
            if (copyBtn && copyBtn.tagName === 'BUTTON') {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied';
                copyBtn.style.background = '#98FF98';
                copyBtn.style.color = '#1D1D1F';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.background = '#0066CC';
                    copyBtn.style.color = 'white';
                }, 2000);
            }
            showNotification('Embed code copied');
        } else {
            showNotification('Failed to copy embed code', 'error');
        }
    }
};

window.updateEmbedCode = async function(galleryId, authenticated) {
    const widthInput = document.getElementById('embedWidth');
    const heightInput = document.getElementById('embedHeight');
    const embedInput = document.getElementById('embedCodeInput');
    const linkInput = document.getElementById('shareLinkInput');
    
    if (!widthInput || !heightInput || !embedInput || !linkInput) {
        showNotification('Embed inputs not found', 'error');
        return;
    }
    
    let width = widthInput.value || '100%';
    let height = heightInput.value || '600';
    const shareUrl = linkInput.value;
    
    if (!shareUrl) {
        showNotification('Share URL not available', 'error');
        return;
    }
    
    // Validate and sanitize dimensions
    if (width !== '100%') {
        const widthNum = parseInt(width, 10);
        if (isNaN(widthNum) || widthNum < 300 || widthNum > 1920) {
            showNotification('Width must be between 300 and 1920 pixels', 'error');
            return;
        }
        width = widthNum + 'px';
    }
    
    const heightNum = parseInt(height, 10);
    if (isNaN(heightNum) || heightNum < 400 || heightNum > 1080) {
        showNotification('Height must be between 400 and 1080 pixels', 'error');
        return;
    }
    height = heightNum + 'px';
    
    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    const safeUrl = escapeHtml(shareUrl);
    const safeWidth = escapeHtml(width);
    const safeHeight = escapeHtml(height);
    
    const embedCode = `<iframe 
    src="${safeUrl}" 
    width="${safeWidth}" 
    height="${safeHeight}" 
    frameborder="0" 
    allowfullscreen>
</iframe>`;
    
    embedInput.value = embedCode;
    showNotification('Embed code updated!', 'success');
};

/**
 * Test gallery share link by opening it in a new tab
 */
window.testGalleryLink = async function(galleryId, authenticated) {
    try {
        const shareInfo = await getGalleryShareInfo(galleryId, authenticated);
        if (shareInfo && shareInfo.share_url) {
            window.open(shareInfo.share_url, '_blank');
            showNotification('Opening share link in new tab...', 'success');
        } else {
            showNotification('Share link not available', 'error');
        }
    } catch (error) {
        console.error('Error testing gallery link:', error);
        showNotification('Failed to test link', 'error');
    }
};

/**
 * Test photo share link by opening it in a new tab
 */
window.testPhotoLink = async function(photoId, authenticated) {
    try {
        const shareInfo = await getPhotoShareInfo(photoId, authenticated);
        if (shareInfo && shareInfo.share_url) {
            window.open(shareInfo.share_url, '_blank');
            showNotification('Opening share link in new tab...', 'success');
        } else {
            showNotification('Share link not available', 'error');
        }
    } catch (error) {
        console.error('Error testing photo link:', error);
        showNotification('Failed to test link', 'error');
    }
};

/**
 * Retry share info fetch (called from error state retry button)
 */
window.retryShareInfo = async function(id, authenticated, type = 'gallery') {
    const loadingEl = document.getElementById('shareModalLoading');
    const contentEl = document.getElementById('shareModalContent');
    
    if (!loadingEl) return;
    
    // Show loading state
    loadingEl.innerHTML = `
        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #0066CC; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="margin-top: 16px;">Retrying...</p>
    `;
    if (contentEl) contentEl.style.display = 'none';
    
    try {
        let shareInfo;
        if (type === 'photo') {
            shareInfo = await getPhotoShareInfo(id, authenticated);
            
            // Validate share URL exists
            if (!shareInfo || !shareInfo.share_url) {
                throw new Error('Share URL not available for this photo');
            }
            
            // Update photo modal content
            const linkInput = document.getElementById('shareLinkInput');
            const qrCodeImage = document.getElementById('qrCodeImage');
            if (linkInput) {
                linkInput.value = shareInfo.share_url;
            }
            if (qrCodeImage) {
                qrCodeImage.src = generateQRCodeUrl(shareInfo.share_url, 200);
                qrCodeImage.style.display = 'block';
            }
        } else {
            shareInfo = await getGalleryShareInfo(id, authenticated);
            
            // Validate share URL exists
            if (!shareInfo || !shareInfo.share_url) {
                throw new Error('Share URL not available for this gallery');
            }
            
            // Update gallery modal content
            const linkInput = document.getElementById('shareLinkInput');
            const embedInput = document.getElementById('embedCodeInput');
            const qrCodeImage = document.getElementById('qrCodeImage');
            if (linkInput) {
                linkInput.value = shareInfo.share_url;
            }
            if (embedInput && shareInfo.embed_code) {
                embedInput.value = shareInfo.embed_code;
            }
            if (qrCodeImage) {
                qrCodeImage.src = generateQRCodeUrl(shareInfo.share_url, 200);
                qrCodeImage.style.display = 'block';
            }
        }
        
        // Show content
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'block';
        showNotification('Share information loaded successfully!', 'success');
    } catch (error) {
        console.error('Error retrying share info:', error);
        
        // Provide user-friendly error messages based on error status
        let errorMessage = 'Failed to load share information';
        if (error.status === 404) {
            errorMessage = type === 'photo' 
                ? 'Photo not found. It may have been deleted or you may not have access.'
                : 'Gallery not found. It may have been deleted or you may not have access.';
        } else if (error.status === 403) {
            errorMessage = type === 'photo'
                ? 'Access denied. This photo may be in a private gallery.'
                : 'Access denied. This gallery may be private.';
        } else if (error.status === 400) {
            errorMessage = error.message || `Invalid ${type} ID.`;
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        loadingEl.innerHTML = `
            <p style="color: #f44336; margin-bottom: 16px;">${errorMessage}</p>
            <button id="retryShareBtn" onclick="retryShareInfo('${id}', ${authenticated}, '${type}')" style="padding: 8px 16px; background: #0066CC; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Retry</button>
        `;
        showNotification(errorMessage, 'error');
    }
};

window.shareGalleryToSocial = shareGalleryToSocial;
window.sharePhotoToSocial = sharePhotoToSocial;
window.showGalleryShareModal = showGalleryShareModal;
window.showPhotoShareModal = showPhotoShareModal;
window.closeShareModal = closeShareModal;
window.copyGalleryLink = copyGalleryLink;
window.copyPhotoLink = copyPhotoLink;
window.copyEmbedCode = copyEmbedCode;

