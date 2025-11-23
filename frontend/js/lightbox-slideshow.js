/**
 * Lightbox Slideshow
 * Full-screen slideshow mode for galleries
 */

let slideshowMode = false;
let slideshowAutoAdvance = false;
let slideshowAutoAdvanceInterval = null;
let slideshowAutoAdvanceDelay = 5000; // 5 seconds default

// Image cache for instant navigation
const slideshowImageCache = new Map();

/**
 * Preload adjacent images for instant slideshow navigation
 */
function preloadSlideshowImages(currentIndex) {
    const photos = window.galleryPhotos || [];
    if (!photos.length) return;
    
    // Preload current, next 2, and previous 2 images (5 total) - same as modal
    const indicesToPreload = [
        currentIndex,
        (currentIndex + 1) % photos.length,
        (currentIndex + 2) % photos.length,
        (currentIndex - 1 + photos.length) % photos.length,
        (currentIndex - 2 + photos.length) % photos.length
    ];
    
    indicesToPreload.forEach(index => {
        const photo = photos[index];
        if (!photo) return;
        
        const mediumUrl = getImageUrl(photo.medium_url || photo.url);
        
        // Skip if already cached
        if (slideshowImageCache.has(mediumUrl)) return;
        
        // Preload in background
        const img = new Image();
        img.onload = () => {
            slideshowImageCache.set(mediumUrl, img);
            console.log(`✅ Preloaded slideshow image ${index + 1}: ${photo.filename || ''}`);
        };
        img.onerror = () => {
            console.warn(`⚠️  Failed to preload slideshow image ${index + 1}: ${photo.filename || ''}`);
        };
        img.src = mediumUrl;
    });
}

/**
 * Initialize lightbox slideshow
 */
function initLightboxSlideshow() {
    // Add slideshow button to gallery grid if it doesn't exist
    addSlideshowButtonToGallery();
}

/**
 * Add slideshow button to gallery grid
 */
function addSlideshowButtonToGallery() {
    // Check if we're on a gallery page
    const galleryGrid = document.querySelector('.gallery-grid');
    if (!galleryGrid) return;
    
    // Check if button already exists
    if (document.getElementById('startSlideshowBtn')) return;
    
    // Create slideshow button
    const slideshowBtn = document.createElement('button');
    slideshowBtn.id = 'startSlideshowBtn';
    slideshowBtn.className = 'slideshow-start-btn';
    slideshowBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Start Slideshow</span>
    `;
    slideshowBtn.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        padding: 14px 24px;
        background: var(--button-primary-fill, #0066CC);
        color: white;
        border: none;
        border-radius: 50px;
        cursor: pointer;
        font-size: 15px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
        z-index: 1000;
        transition: all 0.3s ease;
    `;
    slideshowBtn.onmouseover = () => {
        slideshowBtn.style.transform = 'translateY(-2px)';
        slideshowBtn.style.boxShadow = '0 6px 16px rgba(0, 102, 204, 0.4)';
    };
    slideshowBtn.onmouseout = () => {
        slideshowBtn.style.transform = 'translateY(0)';
        slideshowBtn.style.boxShadow = '0 4px 12px rgba(0, 102, 204, 0.3)';
    };
    slideshowBtn.onclick = () => startSlideshow(0);
    
    document.body.appendChild(slideshowBtn);
}

/**
 * Start slideshow from a specific photo index
 */
window.startSlideshow = function(startIndex = 0) {
    const photos = window.galleryPhotos || [];
    if (photos.length === 0) {
        showNotification('No photos to display in slideshow', 'error');
        return;
    }
    
    slideshowMode = true;
    window.slideshowMode = true;
    
    // Close photo modal if open
    const photoModal = document.getElementById('photoModal');
    if (photoModal && photoModal.classList.contains('active')) {
        if (typeof closePhotoModal === 'function') {
            closePhotoModal();
        }
    }
    
    // Hide slideshow start button
    const startBtn = document.getElementById('startSlideshowBtn');
    if (startBtn) startBtn.style.display = 'none';
    
    // Create slideshow container
    createSlideshowContainer(startIndex);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Track slideshow start (analytics)
    if (typeof window.trackGalleryView === 'function' && window.currentGalleryId) {
        try {
            window.trackGalleryView(window.currentGalleryId, {
                slideshow: true,
                user_agent: navigator.userAgent
            });
        } catch (err) {
        }
    }
};

/**
 * Create slideshow container
 */
function createSlideshowContainer(startIndex) {
    // Remove existing slideshow if any
    const existing = document.getElementById('lightboxSlideshow');
    if (existing) existing.remove();
    
    const photos = window.galleryPhotos || [];
    const slideshow = document.createElement('div');
    slideshow.id = 'lightboxSlideshow';
    slideshow.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #000;
        z-index: 10000;
        display: flex;
        flex-direction: column;
    `;
    
    // Slideshow header
    const header = document.createElement('div');
    header.style.cssText = `
        padding: 16px 24px;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    `;
    
    header.innerHTML = `
        <div style="display: flex; align-items: center; gap: 16px;">
            <h3 style="color: white; margin: 0; font-size: 18px; font-weight: 600;">Slideshow</h3>
            <span id="slideshowPhotoInfo" style="color: rgba(255, 255, 255, 0.7); font-size: 14px;">
                ${startIndex + 1} / ${photos.length}
            </span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <button id="toggleAutoAdvance" onclick="toggleSlideshowAutoAdvance()" style="
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            ">
                <span id="autoAdvanceLabel">Auto: Off</span>
            </button>
            <button onclick="exitSlideshow()" style="
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            ">
                Exit
            </button>
        </div>
    `;
    
    // Slideshow content area
    const content = document.createElement('div');
    content.style.cssText = `
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    `;
    
    // Image container
    const imageContainer = document.createElement('div');
    imageContainer.id = 'slideshowImageContainer';
    imageContainer.style.cssText = `
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    const img = document.createElement('img');
    img.id = 'slideshowImage';
    img.style.cssText = `
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transition: opacity 0.3s ease;
    `;
    
    imageContainer.appendChild(img);
    content.appendChild(imageContainer);
    
    // Navigation buttons
    const prevBtn = document.createElement('button');
    prevBtn.id = 'slideshowPrevBtn';
    prevBtn.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
    `;
    prevBtn.style.cssText = `
        position: absolute;
        left: 24px;
        top: 50%;
        transform: translateY(-50%);
        width: 56px;
        height: 56px;
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        transition: all 0.2s;
        z-index: 10;
    `;
    prevBtn.onmouseover = () => {
        prevBtn.style.background = 'rgba(255, 255, 255, 0.2)';
        prevBtn.style.borderColor = 'rgba(255, 255, 255, 0.5)';
    };
    prevBtn.onmouseout = () => {
        prevBtn.style.background = 'rgba(255, 255, 255, 0.1)';
        prevBtn.style.borderColor = 'rgba(255, 255, 255, 0.3)';
    };
    prevBtn.onclick = () => navigateSlideshow(-1);
    
    const nextBtn = document.createElement('button');
    nextBtn.id = 'slideshowNextBtn';
    nextBtn.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
    `;
    nextBtn.style.cssText = `
        position: absolute;
        right: 24px;
        top: 50%;
        transform: translateY(-50%);
        width: 56px;
        height: 56px;
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        transition: all 0.2s;
        z-index: 10;
    `;
    nextBtn.onmouseover = () => {
        nextBtn.style.background = 'rgba(255, 255, 255, 0.2)';
        nextBtn.style.borderColor = 'rgba(255, 255, 255, 0.5)';
    };
    nextBtn.onmouseout = () => {
        nextBtn.style.background = 'rgba(255, 255, 255, 0.1)';
        nextBtn.style.borderColor = 'rgba(255, 255, 255, 0.3)';
    };
    nextBtn.onclick = () => navigateSlideshow(1);
    
    content.appendChild(prevBtn);
    content.appendChild(nextBtn);
    
    // Assemble slideshow
    slideshow.appendChild(header);
    slideshow.appendChild(content);
    document.body.appendChild(slideshow);
    
    // Set current photo index
    window.slideshowCurrentIndex = startIndex;
    
    // Load first photo
    loadSlideshowPhoto(startIndex);
    
    // Keyboard navigation
    setupSlideshowKeyboard();
    
    // Click on image to advance
    img.onclick = () => navigateSlideshow(1);
    
    // Click on background to exit
    content.onclick = (e) => {
        if (e.target === content || e.target === imageContainer) {
            exitSlideshow();
        }
    };
}

/**
 * Load photo in slideshow
 */
function loadSlideshowPhoto(index) {
    const photos = window.galleryPhotos || [];
    if (index < 0 || index >= photos.length) return;
    
    const photo = photos[index];
    const img = document.getElementById('slideshowImage');
    const info = document.getElementById('slideshowPhotoInfo');
    
    if (!img || !photo) return;
    
    // Use pre-generated medium-res rendition for slideshow
    // Original file used only for downloads
    const mediumUrl = photo.medium_url || photo.url;
    
    // Check if image is already cached for instant display
    if (slideshowImageCache.has(getImageUrl(mediumUrl))) {
        // INSTANT: Use cached image
        img.style.opacity = '0';
        setTimeout(() => {
            img.src = slideshowImageCache.get(getImageUrl(mediumUrl)).src;
            img.alt = photo.title || `Photo ${index + 1}`;
            img.style.opacity = '1';
            
            // Update info
            if (info) {
                info.textContent = `${index + 1} / ${photos.length}`;
            }
        }, 150);
    } else {
        // Load image with fade transition
        img.style.opacity = '0';
        
        setTimeout(() => {
            img.src = getImageUrl(mediumUrl);
            img.alt = photo.title || `Photo ${index + 1}`;
            
            // Fade in
            img.onload = () => {
                slideshowImageCache.set(getImageUrl(mediumUrl), img.cloneNode());
                img.style.opacity = '1';
            };
            
            // Fallback to original if medium fails
            img.onerror = () => {
                console.warn('⚠️  Slideshow medium rendition failed, using original');
                const originalUrl = getImageUrl(photo.url);
                img.src = originalUrl;
                img.onload = () => {
                    slideshowImageCache.set(getImageUrl(mediumUrl), img.cloneNode());
                    img.style.opacity = '1';
                };
                img.onerror = () => {
                    console.error('❌ Slideshow original also failed for photo:', photo.id);
                    img.style.opacity = '1';
                };
            };
            
            // Update info
            if (info) {
                info.textContent = `${index + 1} / ${photos.length}`;
            }
        }, 150);
    }
    
    // Preload adjacent images for instant navigation
    preloadSlideshowImages(index);
    
    // Track photo view
    if (typeof window.trackPhotoView === 'function' && window.currentGalleryId) {
        try {
            window.trackPhotoView(photo.id, window.currentGalleryId, {
                slideshow: true,
                user_agent: navigator.userAgent
            });
        } catch (err) {
        }
    }
}

/**
 * Navigate slideshow
 */
window.navigateSlideshow = function(direction) {
    const photos = window.galleryPhotos || [];
    if (photos.length === 0) return;
    
    let currentIndex = window.slideshowCurrentIndex || 0;
    currentIndex += direction;
    
    // Loop around
    if (currentIndex < 0) currentIndex = photos.length - 1;
    if (currentIndex >= photos.length) currentIndex = 0;
    
    window.slideshowCurrentIndex = currentIndex;
    loadSlideshowPhoto(currentIndex);
    
    // Reset auto-advance timer if active
    if (slideshowAutoAdvance) {
        resetAutoAdvanceTimer();
    }
};

/**
 * Toggle auto-advance
 */
window.toggleSlideshowAutoAdvance = function() {
    slideshowAutoAdvance = !slideshowAutoAdvance;
    const label = document.getElementById('autoAdvanceLabel');
    
    if (slideshowAutoAdvance) {
        if (label) label.textContent = 'Auto: On';
        startAutoAdvance();
    } else {
        if (label) label.textContent = 'Auto: Off';
        stopAutoAdvance();
    }
};

/**
 * Start auto-advance timer
 */
function startAutoAdvance() {
    stopAutoAdvance(); // Clear any existing timer
    
    slideshowAutoAdvanceInterval = setInterval(() => {
        navigateSlideshow(1);
    }, slideshowAutoAdvanceDelay);
}

/**
 * Stop auto-advance timer
 */
function stopAutoAdvance() {
    if (slideshowAutoAdvanceInterval) {
        clearInterval(slideshowAutoAdvanceInterval);
        slideshowAutoAdvanceInterval = null;
    }
}

/**
 * Reset auto-advance timer
 */
function resetAutoAdvanceTimer() {
    if (slideshowAutoAdvance) {
        stopAutoAdvance();
        startAutoAdvance();
    }
}

/**
 * Exit slideshow
 */
window.exitSlideshow = function() {
    slideshowMode = false;
    window.slideshowMode = false;
    
    // Stop auto-advance
    stopAutoAdvance();
    
    // Remove slideshow container
    const slideshow = document.getElementById('lightboxSlideshow');
    if (slideshow) {
        slideshow.style.opacity = '0';
        slideshow.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            slideshow.remove();
        }, 300);
    }
    
    // Show slideshow start button
    const startBtn = document.getElementById('startSlideshowBtn');
    if (startBtn) startBtn.style.display = 'flex';
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Remove keyboard listeners
    document.removeEventListener('keydown', handleSlideshowKeyboard);
};

/**
 * Setup keyboard navigation for slideshow
 */
function setupSlideshowKeyboard() {
    document.addEventListener('keydown', handleSlideshowKeyboard);
}

/**
 * Handle keyboard events in slideshow
 */
function handleSlideshowKeyboard(e) {
    if (!slideshowMode) return;
    
    // Don't handle if typing in input
    const activeElement = document.activeElement;
    const isTyping = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
    );
    
    if (isTyping) return;
    
    switch (e.key) {
        case 'Escape':
            exitSlideshow();
            break;
        case 'ArrowLeft':
            navigateSlideshow(-1);
            break;
        case 'ArrowRight':
        case ' ': // Spacebar
            navigateSlideshow(1);
            break;
        case 'a':
        case 'A':
            toggleSlideshowAutoAdvance();
            break;
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        padding: 14px 28px;
        border-radius: 999px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10001;
        font-size: 14px;
        white-space: nowrap;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLightboxSlideshow);
} else {
    initLightboxSlideshow();
}

// Export functions
window.startSlideshow = startSlideshow;
window.exitSlideshow = exitSlideshow;
window.navigateSlideshow = navigateSlideshow;
window.toggleSlideshowAutoAdvance = toggleSlideshowAutoAdvance;

