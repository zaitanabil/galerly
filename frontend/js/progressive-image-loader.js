/**
 * Progressive Image Loader - Steps 21-24
 * Implements professional image loading strategy:
 * - Load smallest renditions first for quick page rendering
 * - Progressive enhancement with higher resolution as client scrolls/zooms
 * - CDN-served images for minimum latency
 * - Intelligent prefetching for smooth user experience
 */

class ProgressiveImageLoader {
    constructor() {
        // Rendition sizes matching backend configuration
        this.renditions = {
            thumbnail: 'small_thumb_url',  // 400x400 - initial grid load
            small: 'thumbnail_url',         // 800x600 - grid hover preview
            medium: 'medium_url',           // 2000x2000 - modal view
            large: 'large_url',             // 4000x4000 - zoom view
            original: 'url'                 // Original - download only
        };

        // Track loaded images to avoid duplicate requests
        this.loadedImages = new Map();
        
        // Intersection observer for lazy loading
        this.observer = null;
        
        // Prefetch queue for adjacent photos
        this.prefetchQueue = [];
        
        this.init();
    }

    /**
     * Initialize progressive loading system
     */
    init() {
        // Set up intersection observer for lazy loading
        // Load images when they're about to enter viewport
        this.observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            },
            {
                rootMargin: '50px', // Load before entering viewport
                threshold: 0.01
            }
        );
    }

    /**
     * Step 21: Load thumbnails first for quick page rendering
     * Smallest renditions are fetched first
     */
    loadThumbnail(imgElement, photo) {
        // Use smallest available rendition for initial load
        const thumbnailUrl = photo[this.renditions.thumbnail] || photo[this.renditions.small] || photo.url;
        
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.src = this.getCDNUrl(thumbnailUrl);
            
            img.onload = () => {
                imgElement.src = img.src;
                imgElement.classList.add('loaded');
                this.loadedImages.set(photo.id, { thumbnail: true });
                resolve();
            };
            
            img.onerror = () => {
                console.warn(`Failed to load thumbnail for photo ${photo.id}`);
                reject();
            };
        });
    }

    /**
     * Step 22: Progressive enhancement - replace with higher resolution
     * Called when user scrolls or hovers over image
     */
    async upgradeToHighRes(imgElement, photo, targetSize = 'medium') {
        const photoId = photo.id;
        const loadState = this.loadedImages.get(photoId) || {};

        // Skip if already loaded
        if (loadState[targetSize]) {
            return;
        }

        // Get appropriate rendition URL
        const renditionUrl = photo[this.renditions[targetSize]] || photo.url;
        const cdnUrl = this.getCDNUrl(renditionUrl);

        try {
            // Preload higher resolution image
            const highResImg = new Image();
            highResImg.src = cdnUrl;

            await new Promise((resolve, reject) => {
                highResImg.onload = resolve;
                highResImg.onerror = reject;
            });

            // Smooth transition to higher resolution
            imgElement.style.transition = 'opacity 0.3s ease-in-out';
            imgElement.style.opacity = '0.7';
            
            setTimeout(() => {
                imgElement.src = cdnUrl;
                imgElement.style.opacity = '1';
                
                // Update load state
                loadState[targetSize] = true;
                this.loadedImages.set(photoId, loadState);
            }, 150);

        } catch (error) {
            console.warn(`Failed to load ${targetSize} resolution for photo ${photoId}`);
        }
    }

    /**
     * Step 23: CDN-served images for minimum latency
     * All requests go through CloudFront CDN
     */
    getCDNUrl(url) {
        // Images are already CDN URLs from backend
        // Ensure proper cache headers are used
        return url;
    }

    /**
     * Step 24: High-resolution zoom view
     * Load largest rendition when user requests zoom
     */
    async loadForZoom(imgElement, photo) {
        // Load large rendition for zoom
        await this.upgradeToHighRes(imgElement, photo, 'large');
    }

    /**
     * Lazy load image when it enters viewport
     */
    loadImage(imgElement) {
        const photoId = imgElement.getAttribute('data-photo-id');
        const photoData = imgElement.getAttribute('data-photo');
        
        if (!photoData) {
            return;
        }

        try {
            const photo = JSON.parse(photoData);
            this.loadThumbnail(imgElement, photo);
        } catch (error) {
            console.error('Failed to parse photo data:', error);
        }
    }

    /**
     * Observe image elements for lazy loading
     */
    observe(imgElement) {
        if (this.observer) {
            this.observer.observe(imgElement);
        }
    }

    /**
     * Prefetch adjacent photos for smooth navigation
     * Called when user opens modal to preload next/previous photos
     */
    prefetchAdjacent(photos, currentIndex) {
        const prefetchIndices = [
            currentIndex - 1,  // Previous
            currentIndex + 1,  // Next
            currentIndex + 2   // Next + 1
        ].filter(i => i >= 0 && i < photos.length);

        prefetchIndices.forEach(index => {
            const photo = photos[index];
            if (!photo) return;

            // Prefetch medium resolution for quick modal display
            const mediumUrl = photo[this.renditions.medium] || photo.url;
            const img = new Image();
            img.src = this.getCDNUrl(mediumUrl);
        });
    }

    /**
     * Load photo for modal view
     * Uses medium resolution by default, with option to upgrade to large for zoom
     */
    async loadForModal(imgElement, photo, enableZoom = true) {
        // First load medium resolution
        await this.upgradeToHighRes(imgElement, photo, 'medium');

        // If zoom is enabled, prepare large resolution
        if (enableZoom) {
            // Preload large resolution in background
            const largeUrl = photo[this.renditions.large] || photo.url;
            const img = new Image();
            img.src = this.getCDNUrl(largeUrl);
        }
    }

    /**
     * Get download URL for original file
     * Step 25-28: Download handling with original quality
     */
    getDownloadUrl(photo) {
        // Always use original file for downloads
        return photo[this.renditions.original] || photo.url;
    }

    /**
     * Get appropriate rendition for current viewport and device
     * Responsive image selection
     */
    getResponsiveUrl(photo, containerWidth) {
        // Determine appropriate rendition based on container width
        if (containerWidth <= 400) {
            return photo[this.renditions.thumbnail] || photo.url;
        } else if (containerWidth <= 800) {
            return photo[this.renditions.small] || photo.url;
        } else if (containerWidth <= 2000) {
            return photo[this.renditions.medium] || photo.url;
        } else {
            return photo[this.renditions.large] || photo.url;
        }
    }
}

// Initialize global instance
window.progressiveImageLoader = new ProgressiveImageLoader();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressiveImageLoader;
}

