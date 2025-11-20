/**
 * Galerly - Client Gallery Interactions (Read-Only)
 * Photo modal and comments for clients
 * NO approve, NO upload, NO settings
 */

let currentPhotoIndex = 0;

// Image preloading cache for instant navigation
const imageCache = new Map();
const preloadQueue = [];
let isPreloading = false;

/**
 * Aggressive preloader: Preload current, next, and previous images
 * This ensures instant navigation on mobile
 */
function preloadImages(centerIndex) {
    const photos = window.galleryPhotos || [];
    if (!photos.length) return;
    
    // Preload current, next 2, and previous 2 images (5 total)
    const indicesToPreload = [
        centerIndex,
        (centerIndex + 1) % photos.length,
        (centerIndex + 2) % photos.length,
        (centerIndex - 1 + photos.length) % photos.length,
        (centerIndex - 2 + photos.length) % photos.length
    ];
    
    indicesToPreload.forEach((index, priority) => {
        const photo = photos[index];
        if (!photo) return;
        
        // Preload MEDIUM-RES (not full-res)
        const mediumUrl = getImageUrl(photo.medium_url || photo.url);
        
        // Skip if already cached
        if (imageCache.has(mediumUrl)) return;
        
        // Add to preload queue (higher priority = lower number)
        preloadQueue.push({ url: mediumUrl, priority });
    });
    
    // Start preloading if not already running
    if (!isPreloading) {
        processPreloadQueue();
    }
}

/**
 * Process preload queue in priority order
 */
function processPreloadQueue() {
    if (preloadQueue.length === 0) {
        isPreloading = false;
        return;
    }
    
    isPreloading = true;
    
    // Sort by priority (lower number = higher priority)
    preloadQueue.sort((a, b) => a.priority - b.priority);
    
    // Take next 3 images to preload in parallel
    const batch = preloadQueue.splice(0, 3);
    
    const promises = batch.map(item => {
        return new Promise((resolve) => {
            if (imageCache.has(item.url)) {
                resolve();
                return;
            }
            
            const img = new Image();
            img.onload = () => {
                imageCache.set(item.url, img);
                console.log(`✅ Preloaded: ${item.url.split('/').pop()}`);
                resolve();
            };
            img.onerror = () => {
                console.warn(`⚠️  Failed to preload: ${item.url.split('/').pop()}`);
                resolve(); // Continue anyway
            };
            img.src = item.url;
        });
    });
    
    // Continue processing queue
    Promise.all(promises).then(() => {
        if (preloadQueue.length > 0) {
            processPreloadQueue();
        } else {
            isPreloading = false;
        }
    });
}

function openPhotoModal(index) {
    currentPhotoIndex = index;
    const modal = document.getElementById('photoModal');
    const modalImage = document.getElementById('modalImage');
    
    const photos = window.galleryPhotos || [];
    if (!photos[index]) {
        console.error('Photo not found at index:', index);
        return;
    }
    
    const photo = photos[index];
    // Use MEDIUM-RES for viewing (500KB-1MB) instead of FULL-RES (9MB)
    // Full-res is only for downloads
    const mediumUrl = getImageUrl(photo.medium_url || photo.url);
    const thumbUrl = getImageUrl(photo.thumbnail_url || photo.url);
    
    // Show thumbnail immediately for instant feedback
    modalImage.src = thumbUrl;
    modalImage.style.filter = 'blur(5px)';
    modalImage.style.transition = 'filter 0.3s ease';
    
    // Load medium-res (from cache if available, otherwise download)
    if (imageCache.has(mediumUrl)) {
        modalImage.src = imageCache.get(mediumUrl).src;
        modalImage.style.filter = 'none';
    } else {
        const mediumImg = new Image();
        mediumImg.onload = () => {
            imageCache.set(mediumUrl, mediumImg);
            modalImage.src = mediumUrl;
            modalImage.style.filter = 'none';
        };
        mediumImg.src = mediumUrl;
    }
    
    updateModalContent();
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Aggressively preload adjacent images
    preloadImages(index);
    
    // Hide public access features if this is a public viewer
    if (window.isPublicGalleryAccess && typeof window.hidePublicAccessFeatures === 'function') {
        // Small delay to ensure modal DOM is fully rendered
        setTimeout(() => {
            window.hidePublicAccessFeatures();
        }, 50);
    }
    
    // Track photo view (analytics)
    if (typeof window.trackPhotoView === 'function' && window.currentGalleryId) {
        try {
            window.trackPhotoView(photo.id, window.currentGalleryId, {
                ip: '', // Will be set by backend if needed
                user_agent: navigator.userAgent
            });
        } catch (err) {
        }
    }
}

function closePhotoModal() {
    const modal = document.getElementById('photoModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
    
    // Stop polling when modal closes
    if (typeof window.stopCommentsPolling === 'function') {
        window.stopCommentsPolling();
    }
}

function navigatePhoto(direction) {
    const photos = window.galleryPhotos || [];
    currentPhotoIndex += direction;
    if (currentPhotoIndex < 0) currentPhotoIndex = photos.length - 1;
    if (currentPhotoIndex >= photos.length) currentPhotoIndex = 0;
    
    // Stop polling for previous photo
    if (typeof window.stopCommentsPolling === 'function') {
        window.stopCommentsPolling();
    }
    
    const modalImage = document.getElementById('modalImage');
    const photo = photos[currentPhotoIndex];
    const mediumUrl = getImageUrl(photo.medium_url || photo.url);
    const thumbUrl = getImageUrl(photo.thumbnail_url || photo.url);
    
    // Instant navigation: Show cached medium-res if available, otherwise show thumbnail then load medium-res
    if (imageCache.has(mediumUrl)) {
        // INSTANT: Image already cached
        modalImage.src = imageCache.get(mediumUrl).src;
        modalImage.style.filter = 'none';
    } else {
        // Show thumbnail immediately with blur
        modalImage.src = thumbUrl;
        modalImage.style.filter = 'blur(5px)';
        modalImage.style.transition = 'filter 0.3s ease';
        
        // Load medium-res in background
        const mediumImg = new Image();
        mediumImg.onload = () => {
            imageCache.set(mediumUrl, mediumImg);
            modalImage.src = mediumUrl;
            modalImage.style.filter = 'none';
        };
        mediumImg.src = mediumUrl;
    }
    
    updateModalContent();
    
    // Preload next images for instant navigation
    preloadImages(currentPhotoIndex);
}

function updateModalContent() {
    const photos = window.galleryPhotos || [];
    const data = photos[currentPhotoIndex] || { status: 'approved', comments: [] };
    const statusIndicator = document.getElementById('statusIndicator');
    const actionButtons = document.getElementById('actionButtonsSimple');
    const photoNumber = document.getElementById('photoNumber');
    
    // Update status - clients can see pending or approved
    statusIndicator.className = `status-indicator ${data.status}`;
    const statusText = data.status === 'pending' ? 'Pending Approval' : 'Approved';
    statusIndicator.querySelector('span:last-child').textContent = statusText;
    
    // Update photo number
    photoNumber.textContent = `Photo ${currentPhotoIndex + 1} of ${photos.length}`;
    
    // Apply gallery permissions (use global function from client-gallery-loader.js)
    if (typeof window.applyGalleryPermissions === 'function') {
        window.applyGalleryPermissions();
    }
    
    // Show/hide APPROVE button based on status - CLIENTS CAN APPROVE
    const approveBtn = actionButtons.querySelector('.approve');
    if (approveBtn) {
        if (data.status === 'approved') {
            approveBtn.style.display = 'none';
        } else {
            approveBtn.style.display = 'inline-block';
        }
    }
    
    // Show action bar if there are buttons to show
    const downloadBtn = document.getElementById('downloadPhotoBtn');
    const shareBtn = document.getElementById('sharePhotoBtn');
    const favoriteBtn = document.getElementById('favoritePhotoBtn');
    const hasDownload = downloadBtn && downloadBtn.style.display !== 'none';
    const hasApprove = approveBtn && approveBtn.style.display !== 'none';
    const hasShare = shareBtn && shareBtn.style.display !== 'none';
    const hasFavorite = favoriteBtn && favoriteBtn.style.display !== 'none';
    
    if (hasDownload || hasApprove || hasShare || hasFavorite) {
        actionButtons.style.display = 'flex';
    } else {
        actionButtons.style.display = 'none';
    }
    
    // Re-apply public access hiding if needed (for navigation between photos)
    if (window.isPublicGalleryAccess && typeof window.hidePublicAccessFeatures === 'function') {
        window.hidePublicAccessFeatures();
    }
    
    // Load comments
    loadPhotoComments();
}

// Add approve function for clients
async function approvePhoto() {
    const photos = window.galleryPhotos || [];
    const photoId = photos[currentPhotoIndex]?.id;
    
    if (!photoId) {
        console.error('No photo ID found');
        return;
    }
    
    try {
        
        await apiRequest(`photos/${photoId}`, {
            method: 'PUT',
            body: JSON.stringify({ status: 'approved' })
        });
        
        // Update local data
        photos[currentPhotoIndex].status = 'approved';
        updateModalContent();
        
        // Update the gallery grid thumbnail status badge without refresh
        const galleryCard = document.querySelector(`.gallery-photo-card[data-photo-id="${photoId}"]`);
        if (galleryCard) {
            // Find and remove the "PENDING" badge (it's an inline styled div)
            const img = galleryCard.querySelector('img');
            if (img) {
                // Remove the orange border from pending photos
                img.style.border = 'none';
                img.style.opacity = '1';
            }
            // Remove the PENDING badge div (it's the div that contains "PENDING" text)
            const allDivs = galleryCard.querySelectorAll('div');
            allDivs.forEach(div => {
                if (div.textContent.trim() === 'PENDING') {
                    div.remove();
                }
            });
        }
        
        // Show success animation
        const statusIndicator = document.getElementById('statusIndicator');
        statusIndicator.style.transition = 'all 0.5s ease';
        statusIndicator.style.transform = 'scale(1.1)';
        setTimeout(() => {
            statusIndicator.style.transform = 'scale(1)';
        }, 500);
        
        showNotification('Photo approved successfully!');
        
    } catch (error) {
        console.error('Error approving photo:', error);
        alert('Failed to approve photo. Please try again.');
    }
}

function loadPhotoComments() {
    const photos = window.galleryPhotos || [];
    const photo = photos[currentPhotoIndex];
    
    if (!photo || !photo.id) return;
    
    // Get current user and gallery info for permissions
    const currentUser = getUserData();
    const currentUserId = currentUser ? currentUser.id : null;
    const gallery = window.currentGalleryData || {};
    const isGalleryOwner = currentUserId === gallery.user_id;
    
    // Use enhanced comments rendering if available, otherwise fallback to simple
    if (typeof window.renderEnhancedComments === 'function') {
        window.renderEnhancedComments(photo.comments || [], photo.id, currentUserId, isGalleryOwner);
    } else {
        // Fallback to simple rendering
    const commentsList = document.getElementById('commentsList');
        if (!commentsList) return;
    
    commentsList.innerHTML = '';
    const comments = photo?.comments || [];
    
    if (comments.length === 0) {
        commentsList.innerHTML = '<p style="text-align: center; opacity: 0.5; padding: 40px 20px;">No comments yet. Be the first to comment!</p>';
        return;
    }
    
        comments.forEach(comment => {
        const commentEl = document.createElement('div');
        commentEl.className = 'comment-item-simple';
        commentEl.innerHTML = `
            <div class="comment-header">
                    <span class="comment-author-simple">${escapeHtml(comment.author || 'Anonymous')}</span>
                <span class="comment-time-simple">${formatCommentTime(comment.created_at)}</span>
            </div>
            <p class="comment-text-simple">${escapeHtml(comment.text)}</p>
        `;
        commentsList.appendChild(commentEl);
    });
    }
}

function formatCommentTime(timestamp) {
    if (!timestamp) return 'Just now';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMs < 0) return 'Just now';
        if (diffMins < 1) return 'Just now';
        if (diffMins === 1) return '1 minute ago';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        if (diffHours === 1) return '1 hour ago';
        if (diffHours < 24) return `${diffHours} hours ago`;
        if (diffDays === 1) return '1 day ago';
        if (diffDays < 7) return `${diffDays} days ago`;
        
        return date.toLocaleDateString(undefined, { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    } catch (e) {
        return 'Just now';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Share current photo from modal
function shareCurrentPhoto() {
    const photos = window.galleryPhotos || [];
    const photo = photos[currentPhotoIndex];
    if (photo && photo.id && typeof showPhotoShareModal === 'function') {
        showPhotoShareModal(photo.id, false); // authenticated = false for clients
    } else {
        console.error('Photo not found or sharing not available');
    }
}

// Make function globally available
window.shareCurrentPhoto = shareCurrentPhoto;

async function addComment() {
    const commentInput = document.getElementById('commentInput');
    const commentText = commentInput.value.trim();
    
    if (!commentText) return;
    
    const photos = window.galleryPhotos || [];
    const photo = photos[currentPhotoIndex];
    
    if (!photo || !photo.id) {
        console.error('No photo ID found');
        return;
    }
    
    const originalPlaceholder = commentInput.placeholder;
    commentInput.placeholder = 'Posting comment...';
    commentInput.disabled = true;
    
    try {
        // Use enhanced comment system if available, otherwise use simple
        if (typeof window.addEnhancedComment === 'function') {
            await window.addEnhancedComment(photo.id, commentText, null);
        } else {
            // Fallback to simple comment system
        const response = await apiRequest(`photos/${photo.id}/comments`, {
            method: 'POST',
            body: JSON.stringify({
                    text: commentText
            })
        });
        
        if (!photo.comments) {
            photo.comments = [];
        }
        
            photo.comments.push(response);
        }
        
        commentInput.value = '';
        commentInput.placeholder = originalPlaceholder;
        commentInput.disabled = false;
        
        loadPhotoComments();
        showNotification('Comment added successfully!');
        
    } catch (error) {
        console.error('Error adding comment:', error);
        commentInput.placeholder = originalPlaceholder;
        commentInput.disabled = false;
        const errorMsg = error.details?.message || error.message || 'Failed to add comment. Please try again.';
        alert(errorMsg);
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('photoModal');
    if (!modal.classList.contains('active')) return;
    
    // Don't navigate photos if user is typing in an input/textarea
    const activeElement = document.activeElement;
    const isTyping = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
    );
    
    if (isTyping) return; // Let the user type normally
    
    if (e.key === 'Escape') closePhotoModal();
    if (e.key === 'ArrowLeft') navigatePhoto(-1);
    if (e.key === 'ArrowRight') navigatePhoto(1);
});

// Close modal on background click
document.getElementById('photoModal').addEventListener('click', function(e) {
    if (e.target === this) closePhotoModal();
});

// Download photo
async function downloadPhoto() {
    const photos = window.galleryPhotos || [];
    const photo = photos[currentPhotoIndex];
    
    if (!photo) return;
    
    try {
        const downloadBtn = document.getElementById('downloadPhotoBtn');
        const originalText = downloadBtn ? downloadBtn.textContent : 'Download';
        if (downloadBtn) {
            downloadBtn.textContent = 'Downloading...';
            downloadBtn.disabled = true;
        }
        
        const imageUrl = getImageUrl(photo.url);
        const filename = photo.filename || `galerly-photo-${Date.now()}.jpg`;
        
        // Force download using fetch + blob (works with CORS configured)
        try {
            const response = await fetch(imageUrl, {
                method: 'GET',
                mode: 'cors',
                cache: 'no-cache',
                credentials: 'omit'
            });
        if (!response.ok) throw new Error(`Failed to fetch image: ${response.status}`);
        
        const blob = await response.blob();
            
            // Create blob URL and force download
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
            link.download = filename;
            link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
            // Clean up blob URL after a short delay
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
        
        if (downloadBtn) {
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
        }
        
        // Track photo download (analytics)
        if (typeof window.trackPhotoDownload === 'function' && window.currentGalleryId) {
            try {
                window.trackPhotoDownload(photo.id, window.currentGalleryId, {
                    ip: '', // Will be set by backend if needed
                    user_agent: navigator.userAgent
                });
            } catch (err) {
            }
        }
        
        showNotification('Photo downloaded successfully!');
            
        } catch (fetchError) {
            console.error('Fetch failed:', fetchError);
            console.error('Image URL:', imageUrl);
            console.error('Error details:', {
                name: fetchError.name,
                message: fetchError.message,
                stack: fetchError.stack
            });
            
            // Reset button state
            if (downloadBtn) {
                downloadBtn.textContent = originalText;
                downloadBtn.disabled = false;
            }
            
            // Don't show alert - just fail silently and log to console
            throw fetchError;
        }
        
    } catch (error) {
        console.error('Error downloading photo:', error);
        const downloadBtn = document.getElementById('downloadPhotoBtn');
        if (downloadBtn) {
            downloadBtn.textContent = 'Download';
            downloadBtn.disabled = false;
        }
        // Error already shown in inner catch
    }
}

/**
 * Show/hide CTA section based on authentication status
 * CTA section should only be visible for non-authenticated viewers
 */
async function updateCtaSectionVisibility() {
    const ctaSection = document.getElementById('viewerCtaSection');
    if (!ctaSection) return;

    try {
        // Check authentication status
        let isAuthenticated = false;
        if (typeof window.isAuthenticated === 'function') {
            isAuthenticated = await window.isAuthenticated();
        } else if (window.currentUser) {
            // Fallback: check if currentUser exists
            isAuthenticated = !!window.currentUser;
        }

        // Show CTA section only if user is NOT authenticated (viewer mode)
        if (!isAuthenticated) {
            ctaSection.style.display = '';
        } else {
            ctaSection.style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking authentication for CTA section:', error);
        // On error, show CTA section (safer to show than hide)
        ctaSection.style.display = '';
    }
}

// Initialize CTA section visibility when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Wait a bit for auth-check.js to initialize
        setTimeout(updateCtaSectionVisibility, 100);
    });
} else {
    // DOM already loaded, wait for auth-check.js
    setTimeout(updateCtaSectionVisibility, 100);
}

// Also update when authentication state might change
window.addEventListener('auth-state-changed', updateCtaSectionVisibility);

// Handle favorite button click
function handleFavoriteClick() {
    const photos = window.galleryPhotos || [];
    const photo = photos[currentPhotoIndex];
    if (photo && window.currentGalleryId) {
        toggleFavorite(photo.id, window.currentGalleryId);
    }
}

// Override updateModalContent to update favorite button
// This runs after DOM is ready to ensure updateModalContent is defined
(function() {
    const originalUpdateModalContent = updateModalContent;
    updateModalContent = function () {
        originalUpdateModalContent();
        if (typeof updateFavoriteButtons === 'function') {
            updateFavoriteButtons();
        }
    };
})();

// Share gallery function
function shareGallery() {
    if (window.currentGalleryId && typeof window.showGalleryShareModal === 'function') {
        // Check if user is authenticated
        const isAuthenticated = !!window.currentUser;
        window.showGalleryShareModal(window.currentGalleryId, isAuthenticated);
    } else {
        console.error('Gallery ID not available or share modal function not loaded');
    }
}

// Make functions globally available
window.handleFavoriteClick = handleFavoriteClick;
window.shareGallery = shareGallery;

