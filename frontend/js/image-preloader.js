/**
 * Galerly - Aggressive Image Preloader
 * Preloads full-resolution images for instant navigation
 * Strategy: Load current + next 3 + previous 3 (7 images in memory)
 */

// Image cache for full-resolution images
window.imageCache = new Map();
window.preloadQueue = [];
window.isPreloading = false;

/**
 * Preload full-resolution image
 */
function preloadImage(url) {
    return new Promise((resolve, reject) => {
        // Already cached?
        if (window.imageCache.has(url)) {
            resolve(url);
            return;
        }
        
        const img = new Image();
        img.onload = () => {
            window.imageCache.set(url, img);
            resolve(url);
        };
        img.onerror = () => reject(url);
        img.src = url;
    });
}

/**
 * Preload images around current index
 * Strategy: Current + next 3 + previous 3 = 7 images
 */
async function preloadAroundIndex(currentIndex) {
    const photos = window.galleryPhotos || [];
    if (!photos.length) return;
    
    // Calculate indices to preload (wrap around)
    const indicesToPreload = [];
    
    // Current photo (highest priority)
    indicesToPreload.push(currentIndex);
    
    // Next 3 photos
    for (let i = 1; i <= 3; i++) {
        const nextIndex = (currentIndex + i) % photos.length;
        indicesToPreload.push(nextIndex);
    }
    
    // Previous 3 photos
    for (let i = 1; i <= 3; i++) {
        const prevIndex = (currentIndex - i + photos.length) % photos.length;
        indicesToPreload.push(prevIndex);
    }
    
    // Get URLs to preload
    const urlsToPreload = indicesToPreload
        .map(idx => photos[idx])
        .filter(photo => photo && photo.url)
        .map(photo => getImageUrl(photo.url))
        .filter(url => !window.imageCache.has(url)); // Skip already cached
    
    // Preload in parallel (all at once)
    if (urlsToPreload.length > 0) {
        console.log(`⚡ Preloading ${urlsToPreload.length} images around index ${currentIndex}`);
        
        try {
            await Promise.all(urlsToPreload.map(url => preloadImage(url)));
            console.log(`✅ Preloaded ${urlsToPreload.length} images`);
        } catch (err) {
            console.warn('Some images failed to preload:', err);
        }
    }
}

/**
 * Preload ALL gallery images in background (after initial view loads)
 * This ensures smooth navigation after a few seconds
 */
async function preloadAllGalleryImages() {
    const photos = window.galleryPhotos || [];
    if (!photos.length) return;
    
    console.log(`📦 Background preload: Loading all ${photos.length} full-res images...`);
    
    const urls = photos
        .filter(photo => photo && photo.url)
        .map(photo => getImageUrl(photo.url))
        .filter(url => !window.imageCache.has(url));
    
    // Load in batches of 10 (to not overwhelm network)
    const batchSize = 10;
    let loaded = 0;
    
    for (let i = 0; i < urls.length; i += batchSize) {
        const batch = urls.slice(i, i + batchSize);
        
        try {
            await Promise.all(batch.map(url => preloadImage(url)));
            loaded += batch.length;
            console.log(`📥 Loaded ${loaded}/${urls.length} images (${Math.round(loaded/urls.length*100)}%)`);
        } catch (err) {
            console.warn('Batch preload error:', err);
        }
        
        // Small delay between batches to not block UI
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log(`✅ All ${photos.length} images preloaded and cached!`);
}

/**
 * Start preloading when gallery loads
 */
function startGalleryPreload(startIndex = 0) {
    // Clear old cache
    window.imageCache.clear();
    
    // Preload around current index immediately
    preloadAroundIndex(startIndex);
    
    // Start background preload of ALL images after 2 seconds
    setTimeout(() => {
        preloadAllGalleryImages();
    }, 2000);
}

/**
 * Get cached image or original URL
 */
function getCachedImageUrl(url) {
    const cached = window.imageCache.get(url);
    return cached ? cached.src : url;
}

/**
 * Check if image is cached
 */
function isImageCached(url) {
    return window.imageCache.has(url);
}

console.log('✅ Aggressive image preloader initialized');

