/**
 * Galerly - Client Gallery View (Read-Only)
 * Load and display gallery for clients
 * NO upload, NO settings, NO delete
 */
// Load gallery data on page load
document.addEventListener('DOMContentLoaded', async function() {
    // Get gallery ID or token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const galleryId = urlParams.get('id');
    const shareToken = urlParams.get('token');
    // Store whether this is public access (via token)
    window.isPublicGalleryAccess = !!shareToken;
    if (!galleryId && !shareToken) {
        showError('No gallery ID or share token provided');
        return;
    }
    // If we have a token, fetch by token; otherwise use ID
    if (shareToken) {
        await loadGalleryDataByToken(shareToken);
    } else {
    await loadGalleryData(galleryId);
    }
});
/**
 * Hide features for public/external viewers (viewing via token)
 */
function hidePublicAccessFeatures() {
    // Hide Comments card in modal AND adjust layout
    const commentsCard = document.getElementById('commentsCard');
    if (commentsCard) {
        commentsCard.style.display = 'none';
        // Adjust the modal-container layout to remove empty space
        const modalContainer = document.querySelector('.modal-container');
        if (modalContainer) {
            // Change from 2-column grid to single column when comments are hidden
            modalContainer.style.gridTemplateColumns = '1fr';
            modalContainer.style.maxWidth = '1200px'; // Adjust max width for single column
        }
        // Adjust image card to take full width
        const imageCard = document.querySelector('.modal-image-card');
        if (imageCard) {
            imageCard.style.maxWidth = '100%';
            imageCard.style.width = '100%';
            // Add close button to the image card since comments card is hidden
            // Match the exact style and position of auth users' close button
            if (!document.getElementById('publicViewerCloseBtn')) {
                const closeButtonOverlay = document.createElement('div');
                closeButtonOverlay.className = 'modal-close-overlay';
                closeButtonOverlay.style.cssText = `
                    position: absolute;
                    top: var(--size-m, 16px);
                    right: var(--size-m, 16px);
                    z-index: 10;
                `;
                const closeButton = document.createElement('button');
                closeButton.id = 'publicViewerCloseBtn';
                closeButton.className = 'modal-close-btn';
                closeButton.onclick = () => window.closePhotoModal && window.closePhotoModal();
                closeButton.textContent = 'Close';
                closeButton.style.cssText = `
                    cursor: pointer;
                    display: inline-flex;
                    padding: var(--size-xs) var(--size-s);
                    border-radius: var(--border-radius-m);
                    justify-content: center;
                    align-items: center;
                    gap: var(--size-xs);
                    background: transparent;
                    border: 1px solid var(--primary-100);
                    font-family: var(--pp-neue-font);
                    font-size: 0.875rem;
                    font-weight: 400;
                    line-height: 1.25rem;
                    color: var(--text-primary);
                    transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
                `;
                closeButton.onmouseover = function() { 
                    this.style.background = 'var(--primary-5070)';
                    this.style.borderColor = 'var(--primary-200)';
                    this.style.transform = 'translateY(-1px)';
                    this.style.boxShadow = '0 2px 6px rgba(0, 11, 23, 0.06)';
                };
                closeButton.onmouseout = function() { 
                    this.style.background = 'transparent';
                    this.style.borderColor = 'var(--primary-100)';
                    this.style.transform = 'translateY(0)';
                    this.style.boxShadow = 'none';
                };
                closeButtonOverlay.appendChild(closeButton);
                imageCard.style.position = 'relative';
                imageCard.appendChild(closeButtonOverlay);
            }
        }
    }
    // Hide comment input wrapper
    const commentInputWrapper = document.getElementById('commentInputWrapper');
    if (commentInputWrapper) {
        commentInputWrapper.style.display = 'none';
    }
    // Hide Feedback button from navigation
    const feedbackBtn = document.getElementById('feedbackNavBtn');
    if (feedbackBtn) {
        feedbackBtn.style.display = 'none';
    }
    // Hide Favorite button in photo modal
    const favoriteBtn = document.getElementById('favoritePhotoBtn');
    if (favoriteBtn) {
        favoriteBtn.style.display = 'none';
    }
    // Hide Approve button (public viewers cannot approve photos)
    const approveButtons = document.querySelectorAll('.action-btn-simple.approve, button[onclick="approvePhoto()"]');
    approveButtons.forEach(btn => {
        if (btn) btn.style.display = 'none';
    });
    // ISSUE #2: Hide the status indicator completely (Pending/Approved status)
    const statusIndicator = document.getElementById('statusIndicator');
    if (statusIndicator) {
        statusIndicator.style.display = 'none';
    }
    // Hide Logout button (public viewers aren't logged in)
    const logoutButtons = document.querySelectorAll('button[onclick="logout()"]');
    logoutButtons.forEach(btn => {
        if (btn) btn.style.display = 'none';
    });
    // ISSUE #4: Hide "My Galleries" link in both desktop and mobile menus
    const myGalleriesLinks = document.querySelectorAll('a[href="client-dashboard"]');
    myGalleriesLinks.forEach(link => {
        if (link && link.textContent.includes('My Galleries')) {
            const parent = link.closest('li');
            if (parent) {
                parent.style.display = 'none';
            } else {
                // If no parent li, hide the link itself
                link.style.display = 'none';
            }
        }
    });
    // Hide mobile menu for public viewers
    const mobileMenus = document.querySelectorAll('.background-16.input-5, .container-11.background-5');
    mobileMenus.forEach(menu => {
        if (menu) menu.style.display = 'none';
    });
}
/**
 * Apply gallery permissions (downloads, comments) based on settings
 */
function applyGalleryPermissions() {
    const gallery = window.currentGalleryData;
    if (!gallery) {
        return;
    }
    // Check downloads permission (standardized to plural)
    const downloadsAllowed = gallery.allow_downloads !== false;
    const commentsAllowed = gallery.allow_comments !== false;
    // Handle DOWNLOADS permission
    if (!downloadsAllowed) {
        // Hide single photo download button
        const downloadPhotoBtn = document.getElementById('downloadPhotoBtn');
        if (downloadPhotoBtn) {
            downloadPhotoBtn.style.display = 'none';
        }
        // Hide batch download toolbar
        const selectionToolbar = document.getElementById('selectionToolbar');
        if (selectionToolbar) {
            selectionToolbar.style.display = 'none';
        }
        // Hide all checkboxes for photo selection
        const checkboxWrappers = document.querySelectorAll('.photo-checkbox-wrapper');
        checkboxWrappers.forEach(wrapper => {
            wrapper.style.display = 'none';
        });
        // Clear selections
        if (typeof window.clearSelections === 'function') {
            window.clearSelections();
        }
    } else {
        // Show download features
        const downloadPhotoBtn = document.getElementById('downloadPhotoBtn');
        if (downloadPhotoBtn) {
            downloadPhotoBtn.style.display = 'inline-block';
        }
        const selectionToolbar = document.getElementById('selectionToolbar');
        if (selectionToolbar) {
            selectionToolbar.style.display = 'flex';
        }
        const checkboxWrappers = document.querySelectorAll('.photo-checkbox-wrapper');
        checkboxWrappers.forEach(wrapper => {
            wrapper.style.display = 'flex';
        });
    }
    // Handle COMMENTS permission
    if (!commentsAllowed) {
        // COMPLETELY HIDE the comments card (entire tab)
        const commentsCard = document.getElementById('commentsCard');
        if (commentsCard) {
            commentsCard.style.display = 'none';
            // Adjust modal layout to single column
            const modalContainer = document.querySelector('.modal-container');
            if (modalContainer) {
                modalContainer.style.gridTemplateColumns = '1fr';
                modalContainer.style.maxWidth = '1200px';
            }
            // Add close button to the image card (like the one in comments tab)
            const imageCard = document.querySelector('.modal-image-card');
            if (imageCard && !document.getElementById('noCommentsCloseBtn')) {
                const closeButtonOverlay = document.createElement('div');
                closeButtonOverlay.className = 'modal-close-overlay';
                closeButtonOverlay.id = 'noCommentsCloseBtn';
                closeButtonOverlay.style.cssText = `
                    position: absolute;
                    top: var(--size-m, 16px);
                    right: var(--size-m, 16px);
                    z-index: 10;
                `;
                const closeButton = document.createElement('button');
                closeButton.className = 'modal-close-btn';
                closeButton.onclick = () => window.closePhotoModal && window.closePhotoModal();
                closeButton.textContent = 'Close';
                closeButton.style.cssText = `
                    cursor: pointer;
                    display: inline-flex;
                    padding: var(--size-xs) var(--size-s);
                    border-radius: var(--border-radius-m);
                    justify-content: center;
                    align-items: center;
                    gap: var(--size-xs);
                    background: transparent;
                    border: 1px solid var(--primary-100);
                    font-family: var(--pp-neue-font);
                    font-size: 0.875rem;
                    font-weight: 400;
                    line-height: 1.25rem;
                    color: var(--text-primary);
                    transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
                `;
                closeButton.onmouseover = function() { 
                    this.style.background = 'var(--primary-5070)';
                    this.style.borderColor = 'var(--primary-200)';
                    this.style.transform = 'translateY(-1px)';
                    this.style.boxShadow = '0 2px 6px rgba(0, 11, 23, 0.06)';
                };
                closeButton.onmouseout = function() { 
                    this.style.background = 'transparent';
                    this.style.borderColor = 'var(--primary-100)';
                    this.style.transform = 'translateY(0)';
                    this.style.boxShadow = 'none';
                };
                closeButtonOverlay.appendChild(closeButton);
                imageCard.style.position = 'relative';
                imageCard.appendChild(closeButtonOverlay);
            }
        }
        // Hide comment input wrapper
        const commentInputWrapper = document.getElementById('commentInputWrapper');
        if (commentInputWrapper) {
            commentInputWrapper.style.display = 'none';
        }
        // Show message that comments are disabled (if comments list exists)
        const commentsList = document.getElementById('commentsList');
        if (commentsList && commentsList.children.length === 0) {
            commentsList.innerHTML = '<p style="text-align: center; opacity: 0.5; padding: 40px 20px;">Comments have been disabled for this gallery.</p>';
        }
    } else {
        // Remove the close button from image card if it exists
        const noCommentsCloseBtn = document.getElementById('noCommentsCloseBtn');
        if (noCommentsCloseBtn) {
            noCommentsCloseBtn.remove();
        }
        // Show comments card
        const commentsCard = document.getElementById('commentsCard');
        if (commentsCard) {
            commentsCard.style.display = 'flex';
            // Restore modal layout to two columns
            const modalContainer = document.querySelector('.modal-container');
            if (modalContainer) {
                modalContainer.style.gridTemplateColumns = '1fr 400px';
                modalContainer.style.maxWidth = '100%';
            }
        }
        // Show comment input
        const commentInputWrapper = document.getElementById('commentInputWrapper');
        if (commentInputWrapper) {
            commentInputWrapper.style.display = 'block';
        }
    }
}
// Make functions globally available
window.hidePublicAccessFeatures = hidePublicAccessFeatures;
window.applyGalleryPermissions = applyGalleryPermissions;
/**
 * Load gallery data for client view
 */
async function loadGalleryData(galleryId) {
    try {
        // Fetch gallery details - USE CLIENT ENDPOINT
        const gallery = await apiRequest(`client/galleries/${galleryId}`);
        // Update page title
        document.title = `${gallery.name} — Galerly`;
        // Update hero section
        const heroTitle = document.querySelector('.subtitle-14.nav-7');
        if (heroTitle) {
            heroTitle.textContent = gallery.name.toUpperCase();
        }
        const heroTagline = document.querySelector('.grid-17.main-7 p');
        if (heroTagline) {
            heroTagline.textContent = gallery.photographer_name ? 
                `By ${gallery.photographer_name} • View and enjoy` : 
                'View and enjoy your photos';
        }
        // Update description
        const descriptionTitle = document.getElementById('galleryDescriptionTitle');
        const descriptionText = document.getElementById('galleryDescriptionText');
        if (descriptionTitle && descriptionText) {
            if (gallery.description) {
                descriptionTitle.textContent = gallery.description;
                descriptionText.textContent = 'Your gallery is ready to view.';
            } else {
                descriptionTitle.textContent = gallery.name;
                descriptionText.textContent = 'View your photos below.';
            }
        }
        // HIDE upload section (clients cannot upload)
        const uploadSection = document.getElementById('uploadSection');
        if (uploadSection) {
            uploadSection.remove();
        }
        // HIDE settings button (clients cannot edit settings)
        const settingsBtn = document.querySelector('a[aria-label="Gallery Settings"]');
        if (settingsBtn) {
            settingsBtn.parentElement.remove();
        }
        // Store gallery data globally (before loading photos)
        window.currentGalleryId = galleryId;
        window.currentGalleryData = gallery;
        // Add feedback button to navigation
        addFeedbackButton(galleryId);
        // Load and display photos
        await loadGalleryPhotos(galleryId, gallery.photos);
        // Apply gallery permissions (downloads, comments) - wait for DOM to be ready
        setTimeout(() => {
            applyGalleryPermissions();
        }, 500);
        // Check if URL has photo parameter for deep linking
        const urlParams = new URLSearchParams(window.location.search);
        const photoParam = urlParams.get('photo');
        if (photoParam && gallery.photos && gallery.photos.length > 0) {
            const photoIndex = gallery.photos.findIndex(p => p.id === photoParam);
            if (photoIndex !== -1 && typeof window.openPhotoModal === 'function') {
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    window.openPhotoModal(photoIndex);
                }, 500);
            }
        }
        // Track gallery view (analytics)
        if (typeof window.trackGalleryView === 'function') {
            try {
                await window.trackGalleryView(galleryId, {
                    ip: '', // Will be set by backend if needed
                    user_agent: navigator.userAgent,
                    referrer: document.referrer
                });
            } catch (err) {
            }
        }
    } catch (error) {
        console.error('❌ Error loading gallery:', error);
        showError('Failed to load gallery. Please check your access.');
    }
}
/**
 * Load gallery data by share token
 */
async function loadGalleryDataByToken(shareToken) {
    try {
        // Fetch gallery details using share token - this will get the gallery ID first
        // We need to use a public endpoint that accepts tokens
        const gallery = await apiRequest(`client/galleries/by-token/${shareToken}`);
        // Update page title
        document.title = `${gallery.name} — Galerly`;
        // Update hero section
        const heroTitle = document.querySelector('.subtitle-14.nav-7');
        if (heroTitle) {
            heroTitle.textContent = gallery.name.toUpperCase();
        }
        const heroTagline = document.querySelector('.grid-17.main-7 p');
        if (heroTagline) {
            heroTagline.textContent = gallery.photographer_name ? 
                `By ${gallery.photographer_name} • View and enjoy` : 
                'View and enjoy your photos';
        }
        // Update description
        const descriptionTitle = document.getElementById('galleryDescriptionTitle');
        const descriptionText = document.getElementById('galleryDescriptionText');
        if (descriptionTitle && descriptionText) {
            if (gallery.description) {
                descriptionTitle.textContent = gallery.description;
                descriptionText.textContent = 'Your gallery is ready to view.';
            } else {
                descriptionTitle.textContent = gallery.name;
                descriptionText.textContent = 'View your photos below.';
            }
        }
        // HIDE upload section (clients cannot upload)
        const uploadSection = document.getElementById('uploadSection');
        if (uploadSection) {
            uploadSection.remove();
        }
        // HIDE settings button (clients cannot edit settings)
        const settingsBtn = document.querySelector('a[aria-label="Gallery Settings"]');
        if (settingsBtn) {
            settingsBtn.parentElement.remove();
        }
        // Store gallery data globally (before loading photos)
        window.currentGalleryId = gallery.id;
        window.currentGalleryData = gallery;
        // Add feedback button to navigation
        addFeedbackButton(gallery.id);
        // Hide comments and feedback for public/external viewers
        if (window.isPublicGalleryAccess) {
            // Need to wait for DOM elements to be ready
            setTimeout(() => {
                hidePublicAccessFeatures();
            }, 100);
        }
        // Load and display photos
        await loadGalleryPhotos(gallery.id, gallery.photos);
        // Apply gallery permissions (downloads, comments) - wait for DOM to be ready
        setTimeout(() => {
            applyGalleryPermissions();
        }, 500);
        // Check if URL has photo parameter for deep linking
        const urlParams = new URLSearchParams(window.location.search);
        const photoParam = urlParams.get('photo');
        if (photoParam && gallery.photos && gallery.photos.length > 0) {
            const photoIndex = gallery.photos.findIndex(p => p.id === photoParam);
            if (photoIndex !== -1 && typeof window.openPhotoModal === 'function') {
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    window.openPhotoModal(photoIndex);
                }, 500);
            }
        }
        // Track gallery view (analytics)
        if (typeof window.trackGalleryView === 'function') {
            try {
                await window.trackGalleryView(gallery.id, {
                    ip: '', // Will be set by backend if needed
                    user_agent: navigator.userAgent,
                    referrer: document.referrer,
                    via_token: true
                });
            } catch (err) {
            }
        }
    } catch (error) {
        console.error('❌ Error loading gallery by token:', error);
        showError('Failed to load gallery. The link may be invalid or expired.');
    }
}
/**
 * Load and display gallery photos (client view - ALL photos for approval)
 * With pagination - show 12 photos initially
 */
let paginationPhotoIndex = 0;  // Renamed to avoid conflict with client-gallery.js
const PHOTOS_PER_PAGE = 12;
async function loadGalleryPhotos(galleryId, photos) {
    const grid = document.querySelector('.gallery-grid');
    if (!grid) return;
    // Show ALL photos (pending + approved) - clients need to approve them
    const allPhotos = photos || [];
    // Update photo count
    const photoCountEl = document.querySelector('.dynamic-photo-count');
    if (photoCountEl) {
        const pendingCount = allPhotos.filter(p => p.status === 'pending').length;
        const approvedCount = allPhotos.filter(p => p.status === 'approved').length;
        // Only show pending count for AUTHENTICATED users (clients and photographers)
        // Hide approval status from public/non-authenticated viewers
        if (window.isPublicGalleryAccess) {
            // Public viewers - just show total count, no approval status
            photoCountEl.textContent = `— ${allPhotos.length} ${allPhotos.length === 1 ? 'IMAGE' : 'IMAGES'}`;
        } else {
            // Authenticated clients - show pending count
        if (pendingCount > 0) {
            photoCountEl.textContent = `— ${allPhotos.length} ${allPhotos.length === 1 ? 'IMAGE' : 'IMAGES'} (${pendingCount} pending approval)`;
        } else {
            photoCountEl.textContent = `— ${allPhotos.length} ${allPhotos.length === 1 ? 'IMAGE' : 'IMAGES'}`;
            }
        }
    }
    // Clear grid
    grid.innerHTML = '';
    if (allPhotos.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;">
                <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin: 0 auto 20px;">
                    <circle cx="40" cy="40" r="38" stroke="currentColor" stroke-width="1.5" opacity="0.2"/>
                    <path d="M32 36l8 8 8-8M40 28v16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <h3 style="font-size: 20px; margin-bottom: 12px;">No Photos Yet</h3>
                <p style="font-size: 14px;">Photos will appear here once the photographer shares them.</p>
            </div>
        `;
        return;
    }
    // Store photos globally for modal
    window.galleryPhotos = allPhotos;
    // Reset pagination
    paginationPhotoIndex = 0;
    // Render initial photos (first 12)
    renderPhotos(allPhotos, 0, PHOTOS_PER_PAGE);
    // Add "Load More" button if there are more photos
    if (allPhotos.length > PHOTOS_PER_PAGE) {
        addLoadMoreButton();
    }
}
/**
 * Render photos from start index to end index
 */
function renderPhotos(photos, startIndex, count) {
    const grid = document.querySelector('.gallery-grid');
    if (!grid) return;
    // Remove existing "Load More" button if present
    const existingBtn = document.getElementById('loadMoreBtn');
    if (existingBtn) {
        existingBtn.remove();
    }
    const endIndex = Math.min(startIndex + count, photos.length);
    for (let i = startIndex; i < endIndex; i++) {
        const photo = photos[i];
        const photoCard = document.createElement('div');
        photoCard.className = 'gallery-photo-card';
        photoCard.setAttribute('data-photo-id', photo.id);
        // Handle click - open modal (but allow checkbox clicks)
        photoCard.onclick = (e) => {
            // Don't open modal if clicking checkbox
            if (e.target.type === 'checkbox' || e.target.closest('.photo-checkbox-wrapper')) {
                e.stopPropagation();
                return;
            }
            openPhotoModal(i);
        };
        // Add visual indicator for pending photos
        // Hide pending status from public/non-authenticated viewers
        const isPending = !window.isPublicGalleryAccess && photo.status === 'pending';
        const isFavorite = photo.is_favorite === true;
        // Check if photo is selected (wait for photo-selection.js to initialize)
        const isSelected = (window.selectedPhotos && typeof window.selectedPhotos.has === 'function' && window.selectedPhotos.has(photo.id)) || false;
        // Show favorite indicator ONLY for authenticated users (not public viewers)
        const showFavoriteIndicator = !window.isPublicGalleryAccess && isFavorite;
        photoCard.innerHTML = `
            <!-- Selection Checkbox -->
            <div class="photo-checkbox-wrapper" onclick="event.stopPropagation(); togglePhotoSelection('${photo.id}')" style="
                position: absolute;
                top: 10px;
                left: 10px;
                z-index: 10;
                width: 36px;
                height: 36px;
                background: transparent;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='rgba(255, 255, 255, 0.2)'" onmouseout="this.style.background='transparent'">
                <input 
                    type="checkbox" 
                    class="photo-checkbox" 
                    data-photo-id="${photo.id}"
                    ${isSelected ? 'checked' : ''}
                    onclick="event.stopPropagation(); togglePhotoSelection('${photo.id}')"
                    style="
                        width: 24px;
                        height: 24px;
                        cursor: pointer;
                        border-radius: 50%;
                        appearance: none;
                        -webkit-appearance: none;
                        background: ${isSelected ? 'var(--color-blue)' : 'rgba(255, 255, 255, 0.9)'};
                        border: 2px solid ${isSelected ? 'var(--color-blue)' : 'rgba(0, 0, 0, 0.2)'};
                        position: relative;
                        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
                    "
                />
            </div>
            <img 
                src="${getImageUrl(photo.thumbnail_url || photo.url)}" 
                alt="${photo.title || 'Photo'}"
                loading="lazy"
                data-full="${getImageUrl(photo.url)}"
                style="${isPending ? 'opacity: 0.7; border: 3px solid #FFA500;' : ''}${isSelected ? 'opacity: 0.8; outline: 3px solid var(--button-primary-fill); outline-offset: -3px;' : ''}"
                onerror="this.src='https://via.placeholder.com/400x300?text=Image+Not+Available'"
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
            ${isSelected ? `
                <div style="position: absolute; inset: 0; background: rgba(0, 102, 204, 0.2); pointer-events: none; z-index: 1;"></div>
            ` : ''}
        `;
        grid.appendChild(photoCard);
    }
    paginationPhotoIndex = endIndex;
    // Initialize photo selection if not already done
    if (typeof window.initPhotoSelection === 'function') {
        window.initPhotoSelection();
    }
    // Auto-select ALL photos (including newly loaded ones from "Load More")
    setTimeout(() => {
        if (typeof window.selectAllPhotos === 'function') {
            window.selectAllPhotos(); // This will select ALL photos in window.galleryPhotos
        }
    }, 300);
}
/**
 * Add "Load More" button
 */
function addLoadMoreButton() {
    const grid = document.querySelector('.gallery-grid');
    if (!grid) return;
    const loadMoreContainer = document.createElement('div');
    loadMoreContainer.id = 'loadMoreBtn';
    loadMoreContainer.style.cssText = 'grid-column: 1/-1; display: flex; justify-content: center; margin-top: var(--size-l);';
    loadMoreContainer.innerHTML = `
        <a aria-label="Load More Photos" class="image-18 hero-7" href="#load-more"
          onclick="loadMorePhotos(); return false;">
          <div class="title-18 main-6 container-0">
            <span>Load More Photos <span class="text-18 feature-7">
                <svg width="17" height="14" viewBox="0 0 17 14" fill="none">
                  <path
                    d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896"
                    stroke-linecap="round"></path>
                  <path d="M1 7L16 7" stroke-linecap="round">
                  </path>
                </svg>
              </span>
            </span>
          </div>
        </a>
    `;
    grid.appendChild(loadMoreContainer);
}
/**
 * Load more photos (called by button)
 */
function loadMorePhotos() {
    const photos = window.galleryPhotos || [];
    const remainingPhotos = photos.length - paginationPhotoIndex;
    if (remainingPhotos > 0) {
        // Render next batch
        renderPhotos(photos, paginationPhotoIndex, PHOTOS_PER_PAGE);
        // Re-add "Load More" button if there are still more photos
        if (paginationPhotoIndex < photos.length) {
            addLoadMoreButton();
        }
    }
}
/**
 * Add feedback button to navigation
 */
function addFeedbackButton(galleryId) {
    // Find navigation area
    const nav = document.querySelector('.item-15.subtitle-6');
    if (!nav) return;
    // Check if feedback button already exists
    if (document.getElementById('feedbackNavBtn')) return;
    // Create feedback button
    const feedbackLink = document.createElement('a');
    feedbackLink.id = 'feedbackNavBtn';
    feedbackLink.href = '#';
    feedbackLink.onclick = (e) => {
        e.preventDefault();
        if (typeof window.showFeedbackForm === 'function') {
            window.showFeedbackForm(galleryId);
        }
    };
    feedbackLink.innerHTML = `
        <div class="hero-17 feature-5 nav-16 image-6">
            <span>Feedback</span>
        </div>
    `;
    // Insert after "Share" link
    const shareLink = nav.querySelector('a[href="#share"]');
    if (shareLink && shareLink.parentElement) {
        shareLink.parentElement.insertAdjacentElement('afterend', feedbackLink);
    } else {
        nav.appendChild(feedbackLink);
    }
}
/**
 * Show error message
 */
function showError(message) {
    const heroTitle = document.querySelector('.subtitle-14.nav-7');
    if (heroTitle) {
        heroTitle.textContent = 'ERROR';
    }
    const descriptionTitle = document.getElementById('galleryDescriptionTitle');
    const descriptionText = document.getElementById('galleryDescriptionText');
    if (descriptionTitle && descriptionText) {
        descriptionTitle.textContent = 'Gallery Not Available';
        descriptionText.textContent = message;
    }
    const grid = document.querySelector('.gallery-grid');
    if (grid) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px;">
                <p style="font-size: 18px; margin-bottom: 12px; color: var(--color-error);">⚠️ ${message}</p>
                <p style="font-size: 14px; color: var(--color-text-secondary);">
                    <a href="client-dashboard" style="color: var(--color-primary); text-decoration: none;">
                        ← Back to my galleries
                    </a>
                </p>
            </div>
        `;
    }
}
/**
 * Show gallery share modal from navigation button
 */
window.showGalleryShareFromNav = function() {
    const galleryId = window.currentGalleryId;
    if (!galleryId) {
        console.error('No gallery ID available for sharing');
        return;
    }
    // Check if sharing.js is loaded
    if (typeof window.showGalleryShareModal === 'function') {
        // Always use authenticated=false for public gallery views
        window.showGalleryShareModal(galleryId, false);
    } else {
        console.error('Sharing module not loaded');
    }
};