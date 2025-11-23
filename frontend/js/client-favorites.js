/**
 * Client Favorites Handler
 * Allows clients to favorite photos for easy access
 */

// Track favorite state
let favoritePhotos = new Set();

/**
 * Initialize favorites - load user's favorites
 */
async function initFavorites() {
    // Verify authentication with backend (HttpOnly cookie)
    const isAuth = window.isAuthenticated ? await window.isAuthenticated() : false;
    if (!isAuth) {
        return;
    }
    
    try {
        const response = await apiRequest('client/favorites');
        if (response.favorites) {
            favoritePhotos = new Set(response.favorites.map(f => f.photo_id));
            updateFavoriteButtons();
        }
    } catch (error) {
    }
}

/**
 * Toggle favorite status for a photo
 */
async function toggleFavorite(photoId, galleryId) {
    // Verify authentication with backend (HttpOnly cookie)
    const isAuth = window.isAuthenticated ? await window.isAuthenticated() : false;
    if (!isAuth) {
        showNotification('Please log in to favorite photos', 'warning');
        return;
    }
    
    const isFavorited = favoritePhotos.has(photoId);
    
    try {
        if (isFavorited) {
            // Remove from favorites
            await apiRequest('client/favorites', {
                method: 'DELETE',
                body: JSON.stringify({ photo_id: photoId })
            });
            favoritePhotos.delete(photoId);
            showNotification('Removed from favorites');
        } else {
            // Add to favorites
            await apiRequest('client/favorites', {
                method: 'POST',
                body: JSON.stringify({
                    photo_id: photoId,
                    gallery_id: galleryId
                })
            });
            favoritePhotos.add(photoId);
            showNotification('Added to favorites');
        }
        
        updateFavoriteButtons();
    } catch (error) {
        console.error('Error toggling favorite:', error);
        const errorMessage = error.details?.message || error.message || 'Failed to update favorite. Please try again.';
        showNotification(errorMessage, 'error');
    }
}

/**
 * Check if a photo is favorited
 */
function isPhotoFavorited(photoId) {
    return favoritePhotos.has(photoId);
}

/**
 * Update favorite buttons in the UI
 */
function updateFavoriteButtons() {
    // Update favorite button in photo modal
    const favoriteBtn = document.getElementById('favoritePhotoBtn');
    if (favoriteBtn) {
        const photos = window.galleryPhotos || [];
        const currentPhoto = photos[currentPhotoIndex];
        if (currentPhoto) {
            const isFavorited = favoritePhotos.has(currentPhoto.id);
            favoriteBtn.classList.toggle('favorited', isFavorited);
            favoriteBtn.innerHTML = isFavorited 
                ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> Favorited'
                : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> Favorite';
        }
    }
    
    // Update favorite indicators in gallery grid
    const galleryGrid = document.querySelector('.gallery-grid');
    if (galleryGrid) {
        galleryGrid.querySelectorAll('[data-photo-id]').forEach(item => {
            const photoId = item.getAttribute('data-photo-id');
            const favoriteIndicator = item.querySelector('.favorite-indicator');
            if (favoriteIndicator) {
                favoriteIndicator.style.display = favoritePhotos.has(photoId) ? 'block' : 'none';
            }
        });
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
        background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#4CAF50'};
        color: white;
        padding: 14px 28px;
        border-radius: 999px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        white-space: nowrap;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFavorites);
} else {
    initFavorites();
}

