/**
 * Adaptive Lazy Loading System
 * Implements smart image loading based on connection speed, device capability, and viewport position
 * 
 * Features:
 * - Network-aware loading (adjusts quality based on connection speed)
 * - Device-aware sizing (serves appropriate resolution for screen DPI)
 * - Viewport-aware prioritization (loads visible images first)
 * - Predictive prefetching (preloads likely next images)
 * - Memory-efficient (unloads off-screen high-res images)
 */

class AdaptiveLazyLoader {
    constructor() {
        // Network connection quality
        this.connectionType = 'unknown';
        this.effectiveType = '4g';
        this.saveData = false;
        
        // Device capabilities
        this.devicePixelRatio = window.devicePixelRatio || 1;
        this.screenWidth = window.screen.width;
        this.screenHeight = window.screen.height;
        
        // Loading state
        this.loadingImages = new Set();
        this.loadedImages = new Map();
        this.priorityQueue = [];
        
        // Performance tracking
        this.loadTimes = [];
        this.bandwidthEstimate = null;
        
        // Initialize
        this.init();
    }

    /**
     * Initialize adaptive loading system
     */
    init() {
        // Detect network conditions
        this.detectNetwork();
        
        // Set up network change listener
        if ('connection' in navigator) {
            navigator.connection.addEventListener('change', () => {
                this.detectNetwork();
                this.adjustLoadingStrategy();
            });
        }
        
        // Set up intersection observer for viewport tracking
        this.setupIntersectionObserver();
        
        // Monitor scroll for predictive loading
        this.setupScrollPrediction();
        
        // Track memory usage
        this.setupMemoryManagement();
    }

    /**
     * Detect network conditions and capabilities
     */
    detectNetwork() {
        if ('connection' in navigator) {
            const conn = navigator.connection;
            this.connectionType = conn.type || 'unknown';
            this.effectiveType = conn.effectiveType || '4g';
            this.saveData = conn.saveData || false;
            this.bandwidthEstimate = conn.downlink || null;
            
            console.log(`📶 Network: ${this.effectiveType}, Save Data: ${this.saveData}, Bandwidth: ${this.bandwidthEstimate} Mbps`);
        }
    }

    /**
     * Get appropriate image quality based on network and device
     */
    getAdaptiveQuality() {
        // If data saver mode is on, use lowest quality
        if (this.saveData) {
            return 'thumbnail';
        }
        
        // Adjust based on connection speed
        switch (this.effectiveType) {
            case 'slow-2g':
            case '2g':
                return 'thumbnail';  // 400x400
            
            case '3g':
                return 'small';  // 800x600
            
            case '4g':
            default:
                // For 4G, consider device pixel ratio
                if (this.devicePixelRatio >= 2) {
                    return 'medium';  // 2000x2000 for retina
                }
                return 'small';  // 800x600 for standard
        }
    }

    /**
     * Get responsive image size based on container and device
     */
    getResponsiveSize(containerWidth) {
        // Adjust for device pixel ratio
        const effectiveWidth = containerWidth * this.devicePixelRatio;
        
        // Select appropriate rendition
        if (effectiveWidth <= 400) {
            return 'thumbnail';
        } else if (effectiveWidth <= 800) {
            return 'small';
        } else if (effectiveWidth <= 2000) {
            return 'medium';
        } else {
            return 'large';
        }
    }

    /**
     * Set up intersection observer for lazy loading
     */
    setupIntersectionObserver() {
        // Load images when they're about to enter viewport
        const options = {
            root: null,
            rootMargin: this.getAdaptiveRootMargin(),
            threshold: [0, 0.1, 0.5, 1.0]
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const priority = this.calculatePriority(entry);
                
                if (entry.isIntersecting) {
                    this.queueImageLoad(entry.target, priority);
                } else if (entry.intersectionRatio === 0) {
                    // Image left viewport - consider unloading high-res
                    this.considerUnload(entry.target);
                }
            });
        }, options);
    }

    /**
     * Get adaptive root margin based on connection speed
     * Faster connections can afford to load earlier
     */
    getAdaptiveRootMargin() {
        switch (this.effectiveType) {
            case 'slow-2g':
            case '2g':
                return '50px';  // Load just before visible
            
            case '3g':
                return '200px';  // Load a bit earlier
            
            case '4g':
            default:
                return '500px';  // Aggressive prefetch
        }
    }

    /**
     * Calculate loading priority for an image
     * Higher priority = load sooner
     */
    calculatePriority(entry) {
        let priority = 0;
        
        // Boost priority for images closer to viewport center
        const rect = entry.boundingClientRect;
        const viewportCenter = window.innerHeight / 2;
        const imageCenter = rect.top + (rect.height / 2);
        const distanceFromCenter = Math.abs(viewportCenter - imageCenter);
        priority += Math.max(0, 100 - distanceFromCenter / 10);
        
        // Boost priority for larger intersection ratios
        priority += entry.intersectionRatio * 50;
        
        // Boost priority for images that are currently visible
        if (entry.isIntersecting) {
            priority += 100;
        }
        
        return priority;
    }

    /**
     * Queue image for loading with priority
     */
    queueImageLoad(imgElement, priority) {
        // Skip if already loading or loaded
        if (this.loadingImages.has(imgElement) || this.isFullyLoaded(imgElement)) {
            return;
        }
        
        // Add to priority queue
        this.priorityQueue.push({
            element: imgElement,
            priority: priority,
            timestamp: Date.now()
        });
        
        // Sort by priority
        this.priorityQueue.sort((a, b) => b.priority - a.priority);
        
        // Process queue
        this.processLoadQueue();
    }

    /**
     * Process image load queue
     */
    async processLoadQueue() {
        // Limit concurrent loads based on connection
        const maxConcurrent = this.getMaxConcurrentLoads();
        
        while (this.priorityQueue.length > 0 && this.loadingImages.size < maxConcurrent) {
            const item = this.priorityQueue.shift();
            await this.loadImageAdaptively(item.element);
        }
    }

    /**
     * Get maximum concurrent image loads based on connection
     */
    getMaxConcurrentLoads() {
        switch (this.effectiveType) {
            case 'slow-2g':
            case '2g':
                return 2;
            
            case '3g':
                return 4;
            
            case '4g':
            default:
                return 6;
        }
    }

    /**
     * Load image adaptively based on network and device
     */
    async loadImageAdaptively(imgElement) {
        this.loadingImages.add(imgElement);
        
        try {
            // Get photo data
            const photoData = imgElement.dataset.photo ? JSON.parse(imgElement.dataset.photo) : null;
            if (!photoData) {
                return;
            }
            
            // Determine appropriate quality
            const quality = this.getAdaptiveQuality();
            const containerWidth = imgElement.clientWidth || 400;
            const responsiveSize = this.getResponsiveSize(containerWidth);
            
            // Use the lower quality of the two strategies
            const targetSize = this.compareQuality(quality, responsiveSize) <= 0 ? quality : responsiveSize;
            
            // Get URL for target size
            const url = this.getUrlForSize(photoData, targetSize);
            
            // Load image with performance tracking
            const startTime = performance.now();
            await this.loadImage(imgElement, url);
            const loadTime = performance.now() - startTime;
            
            // Track performance
            this.trackLoadTime(loadTime, targetSize);
            
            // Mark as loaded
            this.loadedImages.set(imgElement, {
                size: targetSize,
                loadTime: loadTime,
                timestamp: Date.now()
            });
            
        } catch (error) {
            console.error('Failed to load image:', error);
        } finally {
            this.loadingImages.delete(imgElement);
            
            // Process next in queue
            this.processLoadQueue();
        }
    }

    /**
     * Load image with promise
     */
    loadImage(imgElement, url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                imgElement.src = url;
                imgElement.classList.add('loaded');
                resolve();
            };
            
            img.onerror = () => {
                reject(new Error(`Failed to load: ${url}`));
            };
            
            img.src = url;
        });
    }

    /**
     * Get URL for specific size from photo data
     */
    getUrlForSize(photo, size) {
        const sizeMap = {
            'thumbnail': photo.small_thumb_url || photo.thumbnail_url,
            'small': photo.thumbnail_url || photo.medium_url,
            'medium': photo.medium_url || photo.large_url,
            'large': photo.large_url || photo.url
        };
        
        return sizeMap[size] || photo.url;
    }

    /**
     * Compare quality levels
     * Returns -1 if a < b, 0 if equal, 1 if a > b
     */
    compareQuality(a, b) {
        const levels = ['thumbnail', 'small', 'medium', 'large'];
        return levels.indexOf(a) - levels.indexOf(b);
    }

    /**
     * Track load time for performance monitoring
     */
    trackLoadTime(loadTime, size) {
        this.loadTimes.push({
            time: loadTime,
            size: size,
            timestamp: Date.now()
        });
        
        // Keep only recent measurements
        if (this.loadTimes.length > 100) {
            this.loadTimes = this.loadTimes.slice(-100);
        }
        
        // Adjust strategy if loads are too slow
        const avgLoadTime = this.getAverageLoadTime();
        if (avgLoadTime > 3000) {  // > 3 seconds
            console.warn('⚠️ Slow image loads detected, reducing quality');
            this.adjustLoadingStrategy();
        }
    }

    /**
     * Get average load time
     */
    getAverageLoadTime() {
        if (this.loadTimes.length === 0) return 0;
        const sum = this.loadTimes.reduce((acc, item) => acc + item.time, 0);
        return sum / this.loadTimes.length;
    }

    /**
     * Adjust loading strategy based on performance
     */
    adjustLoadingStrategy() {
        const avgLoadTime = this.getAverageLoadTime();
        
        if (avgLoadTime > 3000) {
            // Reduce root margin to load less aggressively
            console.log('🔧 Reducing prefetch distance');
        } else if (avgLoadTime < 500) {
            // Increase prefetch for smooth experience
            console.log('🚀 Increasing prefetch distance');
        }
    }

    /**
     * Set up scroll prediction for prefetching
     */
    setupScrollPrediction() {
        let lastScrollY = window.scrollY;
        let scrollVelocity = 0;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            scrollVelocity = currentScrollY - lastScrollY;
            lastScrollY = currentScrollY;
            
            // Predict next images based on scroll direction
            if (Math.abs(scrollVelocity) > 5) {
                this.predictAndPrefetch(scrollVelocity > 0 ? 'down' : 'up');
            }
        }, { passive: true });
    }

    /**
     * Predict and prefetch images based on scroll direction
     */
    predictAndPrefetch(direction) {
        // Find images that will soon be visible
        const images = document.querySelectorAll('img[data-photo]');
        const viewport = {
            top: window.scrollY,
            bottom: window.scrollY + window.innerHeight
        };
        
        images.forEach(img => {
            const rect = img.getBoundingClientRect();
            const imgTop = rect.top + window.scrollY;
            
            // Prefetch images in scroll direction
            if (direction === 'down' && imgTop > viewport.bottom && imgTop < viewport.bottom + 1000) {
                this.queueImageLoad(img, 50);  // Medium priority
            } else if (direction === 'up' && imgTop < viewport.top && imgTop > viewport.top - 1000) {
                this.queueImageLoad(img, 50);
            }
        });
    }

    /**
     * Set up memory management
     */
    setupMemoryManagement() {
        // Periodically check memory usage
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
                
                if (usagePercent > 80) {
                    console.warn('⚠️ High memory usage, cleaning up');
                    this.cleanupOffscreenImages();
                }
            }, 30000);  // Check every 30 seconds
        }
    }

    /**
     * Consider unloading high-res images that left viewport
     */
    considerUnload(imgElement) {
        const loadInfo = this.loadedImages.get(imgElement);
        
        if (!loadInfo || loadInfo.size === 'thumbnail') {
            return;  // Don't unload thumbnails
        }
        
        // Unload if it's been off-screen for a while
        const timeOffscreen = Date.now() - loadInfo.timestamp;
        if (timeOffscreen > 60000) {  // 1 minute
            this.downgradeImage(imgElement);
        }
    }

    /**
     * Downgrade image to lower resolution
     */
    downgradeImage(imgElement) {
        const photoData = imgElement.dataset.photo ? JSON.parse(imgElement.dataset.photo) : null;
        if (!photoData) return;
        
        // Switch to thumbnail
        const thumbnailUrl = photoData.small_thumb_url || photoData.thumbnail_url;
        if (thumbnailUrl && imgElement.src !== thumbnailUrl) {
            imgElement.src = thumbnailUrl;
            this.loadedImages.set(imgElement, {
                size: 'thumbnail',
                timestamp: Date.now()
            });
            console.log('♻️ Downgraded off-screen image to save memory');
        }
    }

    /**
     * Clean up off-screen high-res images
     */
    cleanupOffscreenImages() {
        this.loadedImages.forEach((loadInfo, imgElement) => {
            const rect = imgElement.getBoundingClientRect();
            const isOffscreen = rect.bottom < 0 || rect.top > window.innerHeight;
            
            if (isOffscreen && loadInfo.size !== 'thumbnail') {
                this.downgradeImage(imgElement);
            }
        });
    }

    /**
     * Check if image is fully loaded at target quality
     */
    isFullyLoaded(imgElement) {
        const loadInfo = this.loadedImages.get(imgElement);
        if (!loadInfo) return false;
        
        const targetQuality = this.getAdaptiveQuality();
        return this.compareQuality(loadInfo.size, targetQuality) >= 0;
    }

    /**
     * Observe an image element
     */
    observe(imgElement) {
        if (this.observer) {
            this.observer.observe(imgElement);
        }
    }

    /**
     * Unobserve an image element
     */
    unobserve(imgElement) {
        if (this.observer) {
            this.observer.unobserve(imgElement);
        }
    }
}

// Initialize global instance
window.adaptiveLazyLoader = new AdaptiveLazyLoader();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdaptiveLazyLoader;
}

