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
    // Handle URLs with or without query parameters
    const rawFormats = ['.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.rw2', '.pef', '.3fr'];
    // Remove query parameters for extension check, but also check if format is in the path
    const urlWithoutQuery = lowerUrl.split('?')[0];
    return rawFormats.some(format => urlWithoutQuery.endsWith(format) || lowerUrl.includes(format));
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
    
    // Check if it's a problematic format
    if (isHEICUrl(url) || isTIFFUrl(url)) {
        // Try to load normally first (in case CloudFront transformed it)
        await tryLoadImage(img, url, async () => {
            if (onSuccess) onSuccess();
        }, async () => {
            // If normal load fails, try client-side conversion
            await convertAndLoadImage(img, url, onSuccess, onError);
        });
        
    } else if (isRAWUrl(url)) {
        // RAW formats: Use CloudFront transformation (backend provides ?format=jpeg URLs)
        // The thumbnail_url and medium_url from backend already have format=jpeg transformation
        
        // Always try to load the URL - CloudFront should transform it via Lambda@Edge
        // If the URL already has format=jpeg, CloudFront should return JPEG
        await tryLoadImage(img, url, async () => {
            if (onSuccess) onSuccess();
        }, async (error) => {
            // CloudFront transformation failed
            if (onError) onError(error || 'RAW transformation failed');
        });
        
    } else {
        // Standard format (JPEG, PNG, GIF, WebP)
        await tryLoadImage(img, url, onSuccess, onError);
    }
}

/**
 * Try to load image normally
 * Sets img.src only after successful load to prevent premature onerror
 */
function tryLoadImage(img, url, onSuccess, onError) {
    return new Promise((resolve) => {
        const tempImg = new Image();
        
        tempImg.onload = () => {
            // Only set src on actual img after successful load
            img.src = url;
            if (onSuccess) onSuccess();
            resolve(true);
        };
        
        tempImg.onerror = () => {
            // Don't set src on error - prevents browser from trying to load broken URL
            if (onError) onError();
            resolve(false);
        };
        
        // Set CORS for CDN images
        if (url.includes('cdn.galerly.com') || url.includes('cloudfront.net')) {
            tempImg.crossOrigin = 'anonymous';
        }
        
        // Test load with temp image first
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
            // Handle 503 errors from CloudFront (Lambda@Edge timeout/failure)
            if (response.status === 503) {
                // CloudFront Lambda@Edge error
                throw new Error('CloudFront transformation failed (503)');
            }
            throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }
        
        const blob = await response.blob();
        
        // Check if it's HEIC/HEIF
        if (blob.type.includes('heic') || blob.type.includes('heif') || isHEICUrl(url)) {
            // Load heic2any library if not already loaded
            if (!window.heic2any) {
                await loadHEICLibrary();
            }
            
            try {
                // Convert HEIC to JPEG
                const jpegBlob = await heic2any({
                    blob: blob,
                    toType: 'image/jpeg',
                    quality: 0.9
                });
                
                // heic2any returns array for multiple outputs, get first item
                const finalBlob = Array.isArray(jpegBlob) ? jpegBlob[0] : jpegBlob;
                
                // Create object URL and display
                const objectUrl = URL.createObjectURL(finalBlob);
                img.src = objectUrl;
                
                // Clean up object URL after image loads
                img.onload = () => {
                    URL.revokeObjectURL(objectUrl);
                    if (onSuccess) onSuccess();
                };
                
                img.onerror = () => {
                    URL.revokeObjectURL(objectUrl);
                    if (onError) onError(new Error('Failed to display converted HEIC'));
                };
            } catch (conversionError) {
                // Conversion failed
                const objectUrl = URL.createObjectURL(blob);
                img.src = objectUrl;
                img.onload = () => {
                    URL.revokeObjectURL(objectUrl);
                    if (onSuccess) onSuccess();
                };
                img.onerror = () => {
                    URL.revokeObjectURL(objectUrl);
                    if (onError) onError(conversionError);
                };
            }
            
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
        
        // Get src from either src attribute or data-src (for deferred loading)
        const originalSrc = img.src || img.dataset.src || img.getAttribute('data-src');
        if (!originalSrc) return;
        
        // If image has data-src but no src, it's waiting for enhancement
        // Set up blur effect and prepare for loading
        if (img.dataset.src && !img.src) {
            // Ensure blur and background are set
            if (!img.style.filter) {
                img.style.filter = 'blur(10px)';
            }
            if (!img.style.transition) {
                img.style.transition = 'filter 0.3s ease';
            }
            if (!img.style.backgroundColor) {
                img.style.backgroundColor = '#F5F5F7';
            }
            if (!img.style.minHeight) {
                img.style.minHeight = '200px';
            }
        }
        
        // ONLY enhance problematic formats (HEIC, TIFF, RAW)
        // Standard images (JPEG, PNG, GIF, WebP) should load normally
        if (isHEICUrl(originalSrc) || isTIFFUrl(originalSrc) || isRAWUrl(originalSrc)) {
            // Mark as enhanced BEFORE processing
            img.dataset.enhanced = 'true';
            
            // Ensure blur effect is set BEFORE loading
            if (!img.style.filter || !img.style.filter.includes('blur')) {
                img.style.filter = 'blur(10px)';
            }
            if (!img.style.transition) {
                img.style.transition = 'filter 0.3s ease';
            }
            if (!img.style.backgroundColor) {
                img.style.backgroundColor = '#F5F5F7';
            }
            
            if (isHEICUrl(originalSrc) || isTIFFUrl(originalSrc)) {
                // For HEIC/TIFF, use loadImageSmart which handles conversion
                loadImageSmart(
                    img,
                    originalSrc,
                    () => {
                        // Remove blur when loaded
                        img.style.filter = 'none';
                    },
                    (error) => {
                        // Keep blur and show error state
                        img.style.filter = 'blur(10px)';
                        img.style.opacity = '0.5';
                        img.alt = 'Image not available';
                    }
                );
            } else if (isRAWUrl(originalSrc)) {
                // RAW images: Try to load directly - CloudFront should transform via Lambda@Edge
                
                // Set src now (with blur already applied)
                if (img.dataset.src && !img.src) {
                    img.src = originalSrc;
                }
                
                // Try loading the transformed URL
                const tempImg = new Image();
                tempImg.crossOrigin = 'anonymous';
                tempImg.onload = () => {
                    // Ensure src is set on actual img
                    if (!img.src) {
                        img.src = originalSrc;
                    }
                    // Remove blur when loaded
                    img.style.filter = 'none';
                };
                tempImg.onerror = () => {
                    // RAW transformation failed
                    img.style.filter = 'blur(10px)';
                    img.style.opacity = '0.5';
                    img.style.border = '2px solid #ef4444';
                };
                tempImg.src = originalSrc;
            }
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

