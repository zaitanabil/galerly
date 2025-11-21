/**
 * Progressive Image Loading - Steps 21-24
 * Implements industry best practices for fast perceived loading
 * 
 * Strategy:
 * - Load smallest thumbnail first (instant page render)
 * - Progressively replace with higher resolution as user scrolls/zooms
 * - CDN serves pre-generated renditions (no processing delay)
 * - Lazy loading for off-screen images
 * - Prefetch on hover for instant zoom
 */

class ProgressiveImageLoader {
    constructor() {
        this.loadedImages = new Set();
        this.observer = null;
        this.prefetchQueue = [];
        this.initializeIntersectionObserver();
    }

    /**
     * Step 21: Initialize with smallest renditions first
     * Loads thumbnails immediately for quick page render
     */
    initializeGalleryView(photos) {
        const container = document.getElementById('gallery-grid');
        if (!container) return;

        container.innerHTML = '';

        photos.forEach(photo => {
            const photoCard = this.createPhotoCard(photo);
            container.appendChild(photoCard);
        });

        // Start observing for lazy loading
        this.observeImages();
    }

    /**
     * Step 22: Create photo card with progressive loading
     * Shows thumbnail immediately, upgrades to higher res on scroll
     */
    createPhotoCard(photo) {
        const card = document.createElement('div');
        card.className = 'photo-card';
        card.dataset.photoId = photo.id;

        // Step 21: Load smallest thumbnail first (instant render)
        const img = document.createElement('img');
        img.dataset.src = photo.medium_url || photo.url;  // Medium for lazy load
        img.dataset.srcLarge = photo.large_url || photo.url;  // Large for zoom
        img.alt = photo.title || photo.filename;
        img.className = 'photo-thumbnail progressive-image';
        
        // Step 21: Show thumbnail immediately (no lazy loading for thumbnails)
        img.src = photo.small_thumb_url || photo.thumbnail_url || photo.url;
        
        // Add loading placeholder
        const placeholder = document.createElement('div');
        placeholder.className = 'image-placeholder';
        placeholder.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                #f0f0f0 25%,
                #e0e0e0 50%,
                #f0f0f0 75%
            );
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        `;

        card.appendChild(placeholder);
        card.appendChild(img);

        // Step 22: Load higher res on scroll into view
        img.addEventListener('load', () => {
            placeholder.remove();
            img.classList.add('loaded');
        });

        // Step 24: Prefetch large version on hover (instant zoom)
        card.addEventListener('mouseenter', () => {
            this.prefetchImage(img.dataset.srcLarge);
        });

        // Click to view lightbox
        card.addEventListener('click', () => {
            this.openLightbox(photo);
        });

        return card;
    }

    /**
     * Step 22: Initialize Intersection Observer for lazy loading
     * Progressively loads higher resolution as user scrolls
     */
    initializeIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '50px',  // Load 50px before entering viewport
            threshold: 0.01
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    this.loadHigherResolution(img);
                    this.observer.unobserve(img);
                }
            });
        }, options);
    }

    /**
     * Observe all progressive images
     */
    observeImages() {
        const images = document.querySelectorAll('.progressive-image:not(.loaded-high-res)');
        images.forEach(img => {
            this.observer.observe(img);
        });
    }

    /**
     * Step 22: Load higher resolution when scrolled into view
     */
    async loadHigherResolution(img) {
        if (!img.dataset.src || this.loadedImages.has(img.dataset.src)) {
            return;
        }

        try {
            // Create temporary image to preload
            const highResImg = new Image();
            highResImg.src = img.dataset.src;

            await new Promise((resolve, reject) => {
                highResImg.onload = resolve;
                highResImg.onerror = reject;
                
                // Timeout after 10 seconds
                setTimeout(() => reject(new Error('Load timeout')), 10000);
            });

            // Smoothly transition to high res
            img.style.transition = 'opacity 0.3s ease';
            img.style.opacity = '0';

            setTimeout(() => {
                img.src = img.dataset.src;
                img.classList.add('loaded-high-res');
                img.style.opacity = '1';
                this.loadedImages.add(img.dataset.src);
            }, 300);

        } catch (error) {
            console.warn('Failed to load high-res image:', error);
            // Keep thumbnail if high-res fails
            img.classList.add('loaded-high-res');
        }
    }

    /**
     * Step 24: Prefetch image for instant display
     * Pre-loads large version on hover for zero-delay zoom
     */
    prefetchImage(url) {
        if (!url || this.loadedImages.has(url)) {
            return;
        }

        // Check if already in queue
        if (this.prefetchQueue.includes(url)) {
            return;
        }

        this.prefetchQueue.push(url);

        // Use link prefetch for browser-native optimization
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        link.as = 'image';
        document.head.appendChild(link);

        this.loadedImages.add(url);
    }

    /**
     * Step 24: Open lightbox with large rendition
     * Shows highest quality immediately (prefetched on hover)
     */
    openLightbox(photo) {
        if (typeof window.openLightbox === 'function') {
            // Use existing lightbox
            window.openLightbox(photo);
        } else {
            // Fallback: Simple lightbox
            this.showSimpleLightbox(photo);
        }
    }

    /**
     * Simple lightbox implementation
     */
    showSimpleLightbox(photo) {
        const overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: zoom-out;
        `;

        const img = document.createElement('img');
        img.src = photo.large_url || photo.url;  // Use largest available
        img.alt = photo.title || photo.filename;
        img.style.cssText = `
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        `;

        overlay.appendChild(img);
        document.body.appendChild(overlay);

        // Close on click
        overlay.addEventListener('click', () => {
            overlay.remove();
        });

        // Close on escape
        const closeOnEscape = (e) => {
            if (e.key === 'Escape') {
                overlay.remove();
                document.removeEventListener('keydown', closeOnEscape);
            }
        };
        document.addEventListener('keydown', closeOnEscape);
    }
}

// Export for global use
window.ProgressiveImageLoader = ProgressiveImageLoader;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.progressiveLoader = new ProgressiveImageLoader();
    });
} else {
    window.progressiveLoader = new ProgressiveImageLoader();
}

// Add CSS for shimmer animation
if (!document.getElementById('progressive-loading-styles')) {
    const style = document.createElement('style');
    style.id = 'progressive-loading-styles';
    style.textContent = `
        @keyframes shimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }
        
        .progressive-image {
            transition: opacity 0.3s ease;
        }
        
        .photo-card {
            position: relative;
            overflow: hidden;
        }
    `;
    document.head.appendChild(style);
}

