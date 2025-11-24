/**
 * Infinite Scroll Pagination for Client Gallery View
 * Responsive loading indicators for all device sizes
 * Includes favorite functionality
 */

class InfiniteScrollClientGallery {
    constructor(galleryId, containerId = 'galleryGrid') {
        this.galleryId = galleryId;
        this.container = document.getElementById(containerId) || document.querySelector('.gallery-grid');
        this.photos = [];
        this.nextKey = null;
        this.hasMore = true;
        this.loading = false;
        this.pageSize = 50;
        
        // Responsive breakpoints
        this.breakpoints = {
            mobile: 480,
            tablet: 768,
            desktop: 1024
        };
        
        this.init();
    }
    
    init() {
        // Initial load
        this.loadMore();
        
        // Set up intersection observer for infinite scroll
        this.setupIntersectionObserver();
        
        // Handle window resize for responsive layout
        window.addEventListener('resize', () => this.updateLoaderSize());
    }
    
    async loadMore() {
        if (this.loading || !this.hasMore) return;
        
        this.loading = true;
        this.showLoader();
        
        try {
            // Build API URL with pagination params
            let url = `client/galleries/${this.galleryId}?page_size=${this.pageSize}`;
            if (this.nextKey) {
                url += `&last_key=${encodeURIComponent(JSON.stringify(this.nextKey))}`;
            }
            
            const response = await window.apiRequest(url);
            
            // Process response
            const newPhotos = response.photos || [];
            this.photos.push(...newPhotos);
            
            // Update pagination state
            if (response.pagination) {
                this.hasMore = response.pagination.has_more;
                this.nextKey = response.pagination.next_key;
            } else {
                // No pagination metadata = all photos loaded
                this.hasMore = false;
            }
            
            // Render new photos
            this.renderPhotos(newPhotos);
            
        } catch (error) {
            console.error('Error loading photos:', error);
            this.showError();
        } finally {
            this.loading = false;
            this.hideLoader();
        }
    }
    
    renderPhotos(photos) {
        if (!this.container) return;
        
        photos.forEach((photo, index) => {
            const photoElement = this.createPhotoElement(photo, this.photos.length - photos.length + index);
            this.container.appendChild(photoElement);
        });
        
        // Trigger any photo initialization callbacks
        if (typeof window.initPhotoSelection === 'function') {
            window.initPhotoSelection();
        }
    }
    
    createPhotoElement(photo, index) {
        const photoCard = document.createElement('div');
        photoCard.className = 'gallery-photo';
        photoCard.onclick = () => {
            if (typeof window.openPhotoModal === 'function') {
                window.openPhotoModal(index);
            }
        };
        
        const isPending = photo.status === 'pending';
        const isFavorite = photo.is_favorite === true;
        const thumbnailUrl = window.getImageUrl ? window.getImageUrl(photo.thumbnail_url || photo.url) : (photo.thumbnail_url || photo.url);
        
        // Show favorite indicator only if not public gallery
        const showFavoriteIndicator = !window.isPublicGalleryAccess && isFavorite;
        
        photoCard.innerHTML = `
            <img 
                src="${thumbnailUrl}" 
                alt="${photo.title || 'Photo'}"
                loading="lazy"
                style="${isPending ? 'opacity: 0.7; border: 3px solid #FFA500;' : ''}"
                crossorigin="anonymous"
            />
            ${showFavoriteIndicator ? `
                <div style="
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    z-index: 10;
                    width: 32px;
                    height: 32px;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    pointer-events: none;
                ">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="#FF0000">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                </div>
            ` : ''}
        `;
        
        return photoCard;
    }
    
    setupIntersectionObserver() {
        // Create sentinel element for intersection observer
        const sentinel = document.createElement('div');
        sentinel.id = 'scroll-sentinel';
        sentinel.style.height = '1px';
        sentinel.style.width = '100%';
        
        if (this.container && this.container.parentElement) {
            this.container.parentElement.appendChild(sentinel);
        }
        
        // Set up observer
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && this.hasMore && !this.loading) {
                        this.loadMore();
                    }
                });
            },
            {
                rootMargin: '400px'  // Start loading before user reaches bottom
            }
        );
        
        observer.observe(sentinel);
        this.sentinel = sentinel;
        this.observer = observer;
    }
    
    showLoader() {
        if (this.loaderElement) return;  // Already showing
        
        const loader = this.createLoader();
        this.loaderElement = loader;
        
        if (this.sentinel) {
            this.sentinel.before(loader);
        } else if (this.container && this.container.parentElement) {
            this.container.parentElement.appendChild(loader);
        }
    }
    
    hideLoader() {
        if (this.loaderElement) {
            this.loaderElement.remove();
            this.loaderElement = null;
        }
    }
    
    createLoader() {
        const loader = document.createElement('div');
        loader.className = 'infinite-scroll-loader';
        loader.setAttribute('aria-label', 'Loading more photos');
        loader.setAttribute('role', 'status');
        
        // Responsive loader size
        const size = this.getLoaderSize();
        
        loader.innerHTML = `
            <style>
                .infinite-scroll-loader {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: ${size.padding}px 20px;
                    width: 100%;
                    min-height: ${size.minHeight}px;
                }
                
                .spinner {
                    width: ${size.spinnerSize}px;
                    height: ${size.spinnerSize}px;
                    border: ${size.borderWidth}px solid rgba(0, 0, 0, 0.1);
                    border-top-color: #007AFF;
                    border-radius: 50%;
                    animation: spinner-rotate 0.8s linear infinite;
                }
                
                @keyframes spinner-rotate {
                    to { transform: rotate(360deg); }
                }
                
                .loader-text {
                    margin-top: ${size.textMargin}px;
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: ${size.fontSize}px;
                    color: #666;
                    font-weight: 500;
                }
                
                /* Mobile optimizations */
                @media (max-width: 480px) {
                    .infinite-scroll-loader {
                        padding: 20px 15px;
                        min-height: 80px;
                    }
                    .spinner {
                        width: 28px;
                        height: 28px;
                        border-width: 3px;
                    }
                    .loader-text {
                        font-size: 13px;
                        margin-top: 10px;
                    }
                }
                
                /* Tablet */
                @media (min-width: 481px) and (max-width: 768px) {
                    .infinite-scroll-loader {
                        padding: 30px 20px;
                        min-height: 100px;
                    }
                    .spinner {
                        width: 32px;
                        height: 32px;
                        border-width: 3px;
                    }
                    .loader-text {
                        font-size: 14px;
                        margin-top: 12px;
                    }
                }
                
                /* Desktop */
                @media (min-width: 769px) {
                    .infinite-scroll-loader {
                        padding: 40px 20px;
                        min-height: 120px;
                    }
                    .spinner {
                        width: 40px;
                        height: 40px;
                        border-width: 4px;
                    }
                    .loader-text {
                        font-size: 15px;
                        margin-top: 15px;
                    }
                }
            </style>
            <div class="spinner"></div>
            <div class="loader-text">Loading more photos...</div>
        `;
        
        return loader;
    }
    
    getLoaderSize() {
        const width = window.innerWidth;
        
        if (width <= this.breakpoints.mobile) {
            // Mobile
            return {
                spinnerSize: 28,
                borderWidth: 3,
                padding: 20,
                minHeight: 80,
                textMargin: 10,
                fontSize: 13
            };
        } else if (width <= this.breakpoints.tablet) {
            // Tablet
            return {
                spinnerSize: 32,
                borderWidth: 3,
                padding: 30,
                minHeight: 100,
                textMargin: 12,
                fontSize: 14
            };
        } else {
            // Desktop
            return {
                spinnerSize: 40,
                borderWidth: 4,
                padding: 40,
                minHeight: 120,
                textMargin: 15,
                fontSize: 15
            };
        }
    }
    
    updateLoaderSize() {
        if (this.loaderElement) {
            // Recreate loader with new size
            const oldLoader = this.loaderElement;
            const newLoader = this.createLoader();
            oldLoader.replaceWith(newLoader);
            this.loaderElement = newLoader;
        }
    }
    
    showError() {
        const errorElement = document.createElement('div');
        errorElement.className = 'infinite-scroll-error';
        errorElement.innerHTML = `
            <style>
                .infinite-scroll-error {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 40px 20px;
                    text-align: center;
                }
                
                .error-icon {
                    font-size: 48px;
                    margin-bottom: 15px;
                }
                
                .error-message {
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 15px;
                    color: #666;
                    margin-bottom: 20px;
                }
                
                .retry-button {
                    padding: 10px 24px;
                    background: #007AFF;
                    color: white;
                    border: none;
                    border-radius: 100px;
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 15px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                
                .retry-button:hover {
                    background: #0051D5;
                }
                
                @media (max-width: 480px) {
                    .infinite-scroll-error {
                        padding: 30px 15px;
                    }
                    .error-icon {
                        font-size: 36px;
                    }
                    .error-message {
                        font-size: 14px;
                    }
                    .retry-button {
                        padding: 8px 20px;
                        font-size: 14px;
                    }
                }
            </style>
            <div class="error-icon">⚠️</div>
            <div class="error-message">Unable to load more photos</div>
            <button class="retry-button" onclick="window.clientGalleryScroller.loadMore()">Try Again</button>
        `;
        
        if (this.sentinel) {
            this.sentinel.before(errorElement);
            setTimeout(() => errorElement.remove(), 5000);
        }
    }
    
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        if (this.sentinel) {
            this.sentinel.remove();
        }
        this.hideLoader();
    }
}

// Make it globally accessible
window.InfiniteScrollClientGallery = InfiniteScrollClientGallery;

