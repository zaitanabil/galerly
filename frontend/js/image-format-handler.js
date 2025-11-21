/**
 * Simplified Image Handler for Pre-Generated Renditions
 * 
 * All images are pre-processed by backend Lambda on upload
 * Frontend simply loads pre-generated JPEG renditions
 * No client-side conversion, no transformation parameters needed
 */

/**
 * Load image with fallback handling
 * If rendition URL fails, falls back to original
 * 
 * @param {HTMLImageElement} img - Image element
 * @param {string} url - Rendition URL from backend
 * @param {string} fallbackUrl - Original URL for fallback
 * @param {function} onSuccess - Success callback
 * @param {function} onError - Error callback
 */
async function loadImageWithFallback(img, url, fallbackUrl, onSuccess, onError) {
    return new Promise((resolve, reject) => {
        // Try loading rendition URL
        const tempImg = new Image();
        tempImg.crossOrigin = 'anonymous';
        
        tempImg.onload = () => {
            img.src = url;
            if (onSuccess) onSuccess();
            resolve();
        };
        
        tempImg.onerror = () => {
            // Rendition not ready yet, try original
            if (fallbackUrl && fallbackUrl !== url) {
                const fallbackImg = new Image();
                fallbackImg.crossOrigin = 'anonymous';
                
                fallbackImg.onload = () => {
                    img.src = fallbackUrl;
                    if (onSuccess) onSuccess();
                    resolve();
                };
                
                fallbackImg.onerror = () => {
                    if (onError) onError();
                    reject(new Error('Failed to load image'));
                };
                
                fallbackImg.src = fallbackUrl;
            } else {
                if (onError) onError();
                reject(new Error('Failed to load image'));
            }
        };
        
        tempImg.src = url;
    });
}

/**
 * Enhanced image loading with retry logic
 * Handles pre-generated renditions from backend
 */
async function enhanceImageLoading(img, onSuccess, onError) {
    const url = img.getAttribute('data-src') || img.src;
    const fallbackUrl = img.getAttribute('data-fallback') || img.getAttribute('data-full');
    
    try {
        await loadImageWithFallback(img, url, fallbackUrl, onSuccess, onError);
    } catch (error) {
        console.error('Image loading failed:', error);
        if (onError) onError();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { loadImageWithFallback, enhanceImageLoading };
}
