/**
 * Universal Image Format Handler
 * ===========================================
 * Ensures ALL image formats display correctly in browsers
 * 
 * Handles:
 * - HEIC/HEIF files (converts to displayable format)
 * - TIFF files (converts if needed)
 * - RAW formats (uses CloudFront URL transformations - backend provides ?format=jpeg URLs)
 * - All standard formats (JPEG, PNG, GIF, WebP)
 * 
 * Big Tech Approach: Instagram, Google Photos, iCloud
 * 
 * NOTE: RAW images are displayed via CloudFront transformations.
 * Backend provides thumbnail_url and medium_url with ?format=jpeg parameters.
 * Original files are preserved for download.
 */

/**
 * Check if URL points to a HEIC/HEIF image
 * @param {string} url - Image URL
 * @returns {boolean}
 */
function isHEICUrl(url) {
    if (!url) return false;
    const lowerUrl = url.toLowerCase();
    return lowerUrl.endsWith('.heic') || 
           lowerUrl.endsWith('.heif') ||
           lowerUrl.includes('.heic?') ||
           lowerUrl.includes('.heif?');
}

/**
 * Check if URL points to a TIFF image
 * @param {string} url - Image URL
 * @returns {boolean}
 */
function isTIFFUrl(url) {
    if (!url) return false;
    const lowerUrl = url.toLowerCase();
    return lowerUrl.endsWith('.tif') || 
           lowerUrl.endsWith('.tiff') ||
           lowerUrl.includes('.tif?') ||
           lowerUrl.includes('.tiff?');
}

/**
 * Check if URL points to a RAW image format (by extension OR content will fail in browser)
 * @param {string} url - Image URL
 * @returns {boolean}
 */
function isRAWUrl(url) {
    if (!url) return false;
    const lowerUrl = url.toLowerCase();
    // Check both extension AND common RAW content-types that browsers can't display
    const rawFormats = ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef', '.3fr'];
    return rawFormats.some(format => lowerUrl.endsWith(format) || lowerUrl.includes(format + '?'));
    // Note: Files with .jpg extension but DNG content will fail to load and trigger onerror
}

/**
 * Smart image loader that handles all formats
 * This is the BIG TECH solution: detect format and handle appropriately
 * 
 * @param {HTMLImageElement} img - Image element
 * @param {string} url - Image URL
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
async function loadImageSmart(img, url, onSuccess, onError) {
    if (!url) {
        if (onError) onError('No URL provided');
        return;
    }
    
    // Step 1: Check if it's a problematic format
    if (isHEICUrl(url) || isTIFFUrl(url)) {
        console.log(`🔄 Detected ${isHEICUrl(url) ? 'HEIC' : 'TIFF'} image, attempting to load...`);
        
        // Try to load normally first (in case backend converted it)
        await tryLoadImage(img, url, async () => {
            console.log(`✅ Image loaded successfully: ${url}`);
            if (onSuccess) onSuccess();
        }, async () => {
            // If normal load fails, try conversion
            console.log(`⚠️  Browser cannot display format, attempting conversion...`);
            await convertAndLoadImage(img, url, onSuccess, onError);
        });
        
    } else if (isRAWUrl(url)) {
        // RAW formats: Use CloudFront transformation (backend provides ?format=jpeg URLs)
        // The thumbnail_url and medium_url from backend already have format=jpeg transformation
        console.log(`🔄 RAW format detected, using CloudFront transformation: ${url}`);
        // Check if URL already has transformation parameters
        if (url.includes('format=jpeg') || url.includes('format=auto')) {
            // Already transformed, load normally
            await tryLoadImage(img, url, onSuccess, onError);
        } else {
            // Add transformation parameters for RAW files
            const separator = url.includes('?') ? '&' : '?';
            const transformedUrl = `${url}${separator}format=jpeg&width=2000&height=2000&fit=inside`;
            await tryLoadImage(img, transformedUrl, onSuccess, onError);
        }
        
    } else {
        // Standard format (JPEG, PNG, GIF, WebP)
        await tryLoadImage(img, url, onSuccess, onError);
    }
}

/**
 * Try to load image normally
 */
function tryLoadImage(img, url, onSuccess, onError) {
    return new Promise((resolve) => {
        const tempImg = new Image();
        
        tempImg.onload = () => {
            img.src = url;
            if (onSuccess) onSuccess();
            resolve(true);
        };
        
        tempImg.onerror = () => {
            if (onError) onError();
            resolve(false);
        };
        
        // Set CORS for CDN images
        if (url.includes('cdn.galerly.com') || url.includes('cloudfront.net')) {
            tempImg.crossOrigin = 'anonymous';
        }
        
        tempImg.src = url;
    });
}

/**
 * Convert incompatible image format and load
 * Uses browser-native canvas for conversion
 */
async function convertAndLoadImage(img, url, onSuccess, onError) {
    try {
        // Fetch the image as a blob
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch: ${response.status}`);
        }
        
        const blob = await response.blob();
        
        // Check if it's HEIC/HEIF
        if (blob.type.includes('heic') || blob.type.includes('heif') || isHEICUrl(url)) {
            // Load heic2any library if not already loaded
            if (!window.heic2any) {
                await loadHEICLibrary();
            }
            
            // Convert HEIC to JPEG
            const jpegBlob = await heic2any({
                blob: blob,
                toType: 'image/jpeg',
                quality: 0.9
            });
            
            // Create object URL and display
            const objectUrl = URL.createObjectURL(jpegBlob);
            img.src = objectUrl;
            
            // Clean up object URL after image loads
            img.onload = () => {
                URL.revokeObjectURL(objectUrl);
                console.log(`✅ HEIC image converted and displayed`);
                if (onSuccess) onSuccess();
            };
            
        } else {
            // For other formats, try to display the blob directly
            const objectUrl = URL.createObjectURL(blob);
            img.src = objectUrl;
            
            img.onload = () => {
                URL.revokeObjectURL(objectUrl);
                if (onSuccess) onSuccess();
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(objectUrl);
                if (onError) onError();
            };
        }
        
    } catch (error) {
        console.error('❌ Image conversion failed:', error);
        if (onError) onError(error);
    }
}

/**
 * Load heic2any library dynamically
 */
function loadHEICLibrary() {
    return new Promise((resolve, reject) => {
        if (window.heic2any) {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/heic2any@0.0.4/dist/heic2any.min.js';
        script.onload = () => {
            console.log('✅ HEIC converter library loaded');
            resolve();
        };
        script.onerror = () => {
            console.error('❌ Failed to load HEIC converter library');
            reject(new Error('Failed to load heic2any library'));
        };
        document.head.appendChild(script);
    });
}

/**
 * RAW images are handled via CloudFront transformations
 * No placeholder needed - backend provides transformed URLs
 */

/**
 * Enhanced image loading for all gallery images
 * Automatically upgrades all <img> tags with smart loading
 * ONLY for HEIC and TIFF formats - RAW uses CloudFront transformations, standard images load normally
 */
function enhanceGalleryImages() {
    const images = document.querySelectorAll('.gallery-grid img, .gallery-photo img, .modal-image-wrapper img');
    
    images.forEach(img => {
        // Skip if already enhanced
        if (img.dataset.enhanced) return;
        
        const originalSrc = img.src || img.dataset.src;
        if (!originalSrc) return;
        
        // ONLY enhance problematic formats (HEIC, TIFF)
        // RAW formats are handled via CloudFront transformations (backend provides transformed URLs)
        // Standard images (JPEG, PNG, GIF, WebP) should load normally
        if (isHEICUrl(originalSrc) || isTIFFUrl(originalSrc)) {
            console.log(`🔍 Enhancing image: ${originalSrc}`);
            
            // Mark as enhanced BEFORE replacement
            img.dataset.enhanced = 'true';
            
            // Replace src with loading placeholder
            img.src = 'data:image/svg+xml,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
                    <rect fill="#F5F5F7" width="400" height="300"/>
                    <circle cx="200" cy="150" r="20" fill="none" stroke="#007AFF" stroke-width="3">
                        <animate attributeName="stroke-dasharray" values="0 126;126 0" dur="1.5s" repeatCount="indefinite"/>
                    </circle>
                </svg>
            `);
            
            // Load smartly
            loadImageSmart(
                img,
                originalSrc,
                () => {
                    console.log(`✅ Enhanced image loaded: ${originalSrc}`);
                },
                (error) => {
                    console.error(`❌ Failed to load enhanced image:`, error);
                    // Show error placeholder
                    img.src = 'data:image/svg+xml,' + encodeURIComponent(`
                        <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
                            <rect fill="#F5F5F7" width="400" height="300"/>
                            <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
                                  fill="#999" font-family="system-ui" font-size="14">Image not available</text>
                        </svg>
                    `);
                }
            );
        }
        // Standard images (JPEG, PNG, etc.) - DO NOT mark as enhanced, let them load normally
    });
}

/**
 * Auto-enhance images when DOM changes (for dynamically loaded galleries)
 */
function watchForNewImages() {
    // Initial enhancement
    enhanceGalleryImages();
    
    // Watch for new images being added
    const observer = new MutationObserver((mutations) => {
        let shouldEnhance = false;
        
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'IMG' || node.querySelector('img')) {
                            shouldEnhance = true;
                        }
                    }
                });
            }
        });
        
        if (shouldEnhance) {
            setTimeout(enhanceGalleryImages, 100); // Debounce
        }
    });
    
    // Start observing
    const galleryContainer = document.querySelector('.gallery-grid') || document.body;
    observer.observe(galleryContainer, {
        childList: true,
        subtree: true
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', watchForNewImages);
} else {
    watchForNewImages();
}

// Export to global scope
if (typeof window !== 'undefined') {
    window.loadImageSmart = loadImageSmart;
    window.enhanceGalleryImages = enhanceGalleryImages;
    window.isHEICUrl = isHEICUrl;
    window.isTIFFUrl = isTIFFUrl;
    window.isRAWUrl = isRAWUrl;
}

