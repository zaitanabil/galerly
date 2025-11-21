/**
 * Gallery Data Loader
 * Fetches and displays dynamic gallery data from the backend API
 * 
 * This replaces all hardcoded content with backend-managed data
 */
// Initialize gallery data loading
document.addEventListener('DOMContentLoaded', async function() {
    // Check if we're on the gallery page
    const isGalleryPage = document.getElementById('galleryDescriptionTitle') !== null;
    const isDashboardPage = document.getElementById('your-work') !== null;
    if (isGalleryPage) {
        await loadGalleryData();
    }
    if (isDashboardPage) {
        await loadDashboardData();
    }
});
/**
 * Load individual gallery data (gallery)
 */
async function loadGalleryData() {
    try {
        // Get gallery ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const galleryId = urlParams.get('id');
        if (!galleryId) {
            console.error('No gallery ID provided');
            return;
        }
        // Fetch gallery data from API
        const gallery = await apiRequest(`galleries/${galleryId}`);
        // Update page title
        document.title = `${gallery.name} — Galerly`;
        // Update gallery header
        const galleryTitle = document.querySelector('.subtitle-14.nav-7');
        if (galleryTitle) {
            galleryTitle.textContent = gallery.name.toUpperCase();
        }
        // Update client name and photo count
        const galleryMeta = document.querySelector('.grid-17.main-7 p');
        if (galleryMeta) {
            const photoCount = gallery.photos?.length || 0;
            const createdDate = new Date(gallery.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            galleryMeta.textContent = `${gallery.client_name} • ${photoCount} photos • ${createdDate}`;
        }
        // Update description
        const descriptionTitle = document.getElementById('galleryDescriptionTitle');
        const descriptionText = document.getElementById('galleryDescriptionText');
        if (gallery.description) {
            if (descriptionTitle) {
                descriptionTitle.textContent = gallery.description;
            }
            if (descriptionText) {
                descriptionText.textContent = 'Edit this description in Gallery Settings to personalize your message for clients.';
            }
        } else {
            // No description - show helpful message
            if (descriptionTitle) {
                descriptionTitle.textContent = gallery.name;
            }
            if (descriptionText) {
                descriptionText.textContent = 'Add a description in Gallery Settings to share details with your clients.';
            }
        }
        // Update settings form with gallery data
        updateSettingsForm(gallery);
        // Load and display photos
        await loadGalleryPhotos(galleryId, gallery.photos);
        // Store gallery ID globally for other functions
        window.currentGalleryId = galleryId;
        window.currentGalleryData = gallery;
        
        // Show/hide "Send Email Notification" button based on gallery state
        const notifyButton = document.getElementById('notifyClientsButton');
        const remindButton = document.getElementById('remindClientsButton');
        if (notifyButton && remindButton) {
            const hasPhotos = (gallery.photo_count || 0) > 0;
            const hasClients = (gallery.client_emails || []).length > 0;
            
            // Show buttons only if there are photos and clients
            if (hasPhotos && hasClients) {
                notifyButton.style.display = 'inline-flex';
                remindButton.style.display = 'inline-flex';
            } else {
                notifyButton.style.display = 'none';
                remindButton.style.display = 'none';
            }
        }
        
        // Check if URL has photo parameter for deep linking
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
        // Track gallery view (analytics) - backend will skip if viewer is the owner
        // Always track (backend handles owner check)
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
        console.error('❌ Error loading gallery data:', error);
        showError('Failed to load gallery. Please try again.');
    }
}
/**
 * Update settings form with gallery data
 */
async function updateSettingsForm(gallery) {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    
    // Set form values
    form.querySelector('[name="galleryName"]').value = gallery.name || '';
    form.querySelector('[name="clientName"]').value = gallery.client_name || '';
    // Note: clientEmail removed - now handled by multi-client UI in gallery.js
    form.querySelector('[name="description"]').value = gallery.description || '';
    form.querySelector('[name="privacy"]').checked = gallery.privacy === 'public';  // Public portfolio visibility
    form.querySelector('[name="allowDownloads"]').checked = gallery.allow_downloads || false;
    form.querySelector('[name="allowComments"]').checked = gallery.allow_comments || false;
    
    // ✅ POPULATE EXPIRY OPTIONS BASED ON PHOTOGRAPHER'S PLAN
    await populateExpiryOptions(gallery.expiry_days);
    
    // Load client emails into multi-client UI (handled by gallery.js)
    if (typeof window.loadGallerySettings === 'function') {
        window.loadGallerySettings(gallery);
    }
}

/**
 * Populate expiration options based on photographer's plan
 * FREE PLAN: 1-7 days MAXIMUM (NO "NEVER" OPTION)
 * PLUS PLAN: 30 days - 1 year + Never
 * PRO PLAN: 30 days - 1 year + Never
 */
async function populateExpiryOptions(currentExpiry) {
    const expirySelect = document.getElementById('expirySelect');
    if (!expirySelect) return;
    
    try {
        // Get current user's subscription info
        const response = await apiRequest('subscription/usage');
        const plan = response?.plan || 'free';
        
        // Define expiry options per plan
        const expiryOptions = {
            free: [
                // ⚠️ FREE PLAN RESTRICTION: MAXIMUM 7 DAYS (HARD LIMIT)
                { value: '1', label: '1 day' },
                { value: '3', label: '3 days' },
                { value: '7', label: '7 days (Maximum)' }
            ],
            plus: [
                { value: 'never', label: 'Never' },
                { value: '30', label: '30 days' },
                { value: '60', label: '60 days' },
                { value: '90', label: '90 days' },
                { value: '180', label: '6 months' },
                { value: '365', label: '1 year' }
            ],
            pro: [
                { value: 'never', label: 'Never' },
                { value: '30', label: '30 days' },
                { value: '60', label: '60 days' },
                { value: '90', label: '90 days' },
                { value: '180', label: '6 months' },
                { value: '365', label: '1 year' }
            ]
        };
        
        // Get options for current plan (default to free)
        const options = expiryOptions[plan] || expiryOptions.free;
        
        // Clear existing options
        expirySelect.innerHTML = '';
        
        // Populate options
        options.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option.value;
            optionEl.textContent = option.label;
            expirySelect.appendChild(optionEl);
        });
        
        // Set current value (or default to maximum for free plan)
        if (currentExpiry) {
            expirySelect.value = currentExpiry.toString();
        } else if (plan === 'free') {
            // Default to 7 days (maximum) for free users
            expirySelect.value = '7';
        }
        
        // Show restriction notice for free users
        if (plan === 'free') {
            const expiryField = expirySelect.closest('.settings-field');
            if (expiryField) {
                const existingNotice = expiryField.querySelector('.plan-restriction-notice');
                if (!existingNotice) {
                    const notice = document.createElement('p');
                    notice.className = 'plan-restriction-notice';
                    notice.style.cssText = `
                        font-size: 13px;
                        color: var(--color-red, #FF3B30);
                        margin-top: 8px;
                        padding: 8px 12px;
                        background: rgba(255, 59, 48, 0.05);
                        border-radius: var(--border-radius-s);
                        border: 1px solid rgba(255, 59, 48, 0.2);
                        line-height: 1.4;
                        font-weight: 500;
                    `;
                    notice.innerHTML = `<strong>Free Plan Limitation:</strong> All galleries expire after 7 days maximum. Upgrade to <strong>Plus</strong> or <strong>Pro</strong> for unlimited gallery lifetime and longer expiration options.`;
                    expiryField.appendChild(notice);
                }
            }
        }
        
    } catch (error) {
        console.error('Error loading expiry options:', error);
        // Fallback to basic free plan options (1-7 days max)
        expirySelect.innerHTML = `
            <option value="1">1 day</option>
            <option value="3">3 days</option>
            <option value="7">7 days (Maximum)</option>
        `;
    }
}
/**
 * Load and display gallery photos
 * With pagination - show 12 photos initially
 */
let paginationPhotoIndex = 0;  // Renamed to avoid conflict with gallery.js
const PHOTOS_PER_PAGE = 12;
async function loadGalleryPhotos(galleryId, photos) {
    const galleryGrid = document.querySelector('.gallery-grid');
    const uploadSection = document.getElementById('uploadSection');
    if (!galleryGrid) return;
    // Show upload section now that gallery is loaded
    if (uploadSection) {
        uploadSection.style.display = 'block';
    }
    // ⚡ IMPORTANT: Setup upload handler FIRST, before checking photos
    // This ensures upload works even when gallery is empty!
    setupPhotoUpload(galleryId);
    // Clear existing placeholder photos
    galleryGrid.innerHTML = '';
    // Update photo count - target the dynamic-photo-count span
    const photoCountEl = document.querySelector('.dynamic-photo-count');
    if (!photos || photos.length === 0) {
        if (photoCountEl) {
            photoCountEl.textContent = `— 0 IMAGES`;
        }
        // Simple message - no duplicate upload button (it's already in upload section above)
        galleryGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; opacity: 0.6;">
                <p style="font-size: 16px;">No photos yet. Use the upload section above to add your first photo!</p>
            </div>
        `;
        return;
    }
    if (photoCountEl) {
        photoCountEl.textContent = `— ${photos.length} IMAGES`;
    }
    // Update global photo data for modal
    window.galleryPhotos = photos;
    // Reset pagination
    paginationPhotoIndex = 0;
    // Render initial photos (first 12)
    renderGalleryPhotos(photos, 0, PHOTOS_PER_PAGE);
    // Add "Load More" button if there are more photos
    if (photos.length > PHOTOS_PER_PAGE) {
        addLoadMoreButton();
    }
}
/**
 * Render photos from start index to end index
 */
function renderGalleryPhotos(photos, startIndex, count) {
    const galleryGrid = document.querySelector('.gallery-grid');
    if (!galleryGrid) return;
    // Remove existing "Load More" button if present
    const existingBtn = document.getElementById('loadMoreBtn');
    if (existingBtn) {
        existingBtn.remove();
    }
    const endIndex = Math.min(startIndex + count, photos.length);
    for (let i = startIndex; i < endIndex; i++) {
        const photo = photos[i];
        const photoEl = document.createElement('div');
        photoEl.className = 'gallery-photo';
        photoEl.onclick = () => openPhotoModal(i);
        // Use thumbnail_url if available (has CloudFront transformations), otherwise fallback to url
        // For RAW images, thumbnail_url should have ?format=jpeg parameters
        const thumbnailUrl = getImageUrl(photo.thumbnail_url || photo.url);
        const fullUrl = getImageUrl(photo.url);
        
        // Debug logging for RAW images - helps diagnose CloudFront transformation issues
        if (photo.filename && /\.(dng|cr2|cr3|nef|arw|raf|orf|rw2|pef|3fr)$/i.test(photo.filename)) {
            console.log(`📸 RAW image detected: ${photo.filename}`);
            console.log(`   thumbnail_url from backend: ${photo.thumbnail_url || 'missing'}`);
            console.log(`   medium_url from backend: ${photo.medium_url || 'missing'}`);
            console.log(`   Final thumbnail URL: ${thumbnailUrl}`);
            
            // Verify transformation parameters are present
            if (thumbnailUrl && !thumbnailUrl.includes('format=jpeg')) {
                console.warn(`⚠️  WARNING: RAW image URL missing format=jpeg parameter!`);
                console.warn(`   This image may fail to load in the browser.`);
                console.warn(`   Expected: ...?format=jpeg&width=800&height=600`);
            }
        }
        const isFavorite = photo.is_favorite === true;
        const isApproved = photo.status === 'approved';
        photoEl.innerHTML = `
            <img src="${thumbnailUrl}" 
                 alt="${photo.title || `Photo ${i + 1}`}"
                 data-full="${fullUrl}"
                 data-photo-id="${photo.id}"
                 data-filename="${photo.filename || ''}"
                 loading="lazy"
                 crossorigin="anonymous"
                 style="${isApproved ? 'border: 3px solid #10b981;' : ''} filter: blur(10px); transition: filter 0.3s ease; background-color: #F5F5F7;"
                 onload="this.style.filter='none';"
                 onerror="console.error('Image load failed:', this.src); this.onerror=null; handleImageLoadError(this, '${photo.id}', '${photo.filename || ''}');">
            ${isFavorite ? `
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
            <div class="photo-overlay">
                ${photo.status === 'approved' ? '✓ Approved' : 'Click to view'}
            </div>
        `;
        galleryGrid.appendChild(photoEl);
    }
    paginationPhotoIndex = endIndex;
    // Update photo references
    window.photos = document.querySelectorAll('.gallery-photo');
    // Initialize photo deletion UI after photos are rendered
    if (typeof window.initializePhotoDeletion === 'function') {
        window.initializePhotoDeletion();
    }
}
/**
 * Add "Load More" button
 */
function addLoadMoreButton() {
    const galleryGrid = document.querySelector('.gallery-grid');
    if (!galleryGrid) return;
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
    galleryGrid.appendChild(loadMoreContainer);
}
/**
 * Load dashboard data (dashboard)
 */
async function loadDashboardData(searchParams = {}) {
    try {
        // Build query string from search params
        const queryParams = new URLSearchParams();
        if (searchParams.search) queryParams.append('search', searchParams.search);
        if (searchParams.client) queryParams.append('client', searchParams.client);
        if (searchParams.sort) queryParams.append('sort', searchParams.sort);
        const queryString = queryParams.toString();
        const url = queryString ? `galleries?${queryString}` : 'galleries';
        // Fetch user's galleries from API
        const data = await apiRequest(url);
        const galleries = data.galleries || data;
        // Fetch dashboard stats (includes storage info)
        try {
            const statsResponse = await apiRequest('dashboard/stats');
            if (statsResponse && statsResponse.stats) {
                // Update storage card with real data
                updateStorageCardFromStats(statsResponse.stats);
            }
        } catch (err) {
            console.error('Error loading dashboard stats:', err);
        }
        // Update statistics
        updateDashboardStats(galleries);
        // Load and display galleries
        loadUserGalleries(galleries);
        // Load usage information to update Storage and Galleries cards
        if (typeof window.loadUsage === 'function') {
            try {
                const usage = await window.loadUsage();
                if (usage) {
                    updateStorageCard(usage);
                    updateGalleriesCard(usage, galleries.length);
                }
            } catch (err) {
            }
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load galleries. Please try again.');
    }
}
/**
 * Perform gallery search with current filter values
 */
window.performGallerySearch = function() {
    const searchInput = document.getElementById('gallerySearchInput');
    const clientFilter = document.getElementById('clientFilterInput');
    const sortSelect = document.getElementById('gallerySortSelect');
    const searchParams = {
        search: searchInput ? searchInput.value.trim() : '',
        client: clientFilter ? clientFilter.value.trim() : '',
        sort: sortSelect ? sortSelect.value : 'date_desc'
    };
    loadDashboardData(searchParams);
};
/**
 * Clear search filters and reload all galleries
 */
window.clearGallerySearch = function() {
    const searchInput = document.getElementById('gallerySearchInput');
    const clientFilter = document.getElementById('clientFilterInput');
    const sortSelect = document.getElementById('gallerySortSelect');
    if (searchInput) searchInput.value = '';
    if (clientFilter) clientFilter.value = '';
    if (sortSelect) sortSelect.value = 'date_desc';
    loadDashboardData({});
};
/**
 * Update dashboard statistics
 */
function updateDashboardStats(galleries) {
    const galleryCount = galleries.length;
    let totalPhotos = 0;
    let totalStorage = 0;
    
    // Sum up photo counts from all galleries (ensure numeric addition)
    galleries.forEach(gallery => {
        const photoCount = parseInt(gallery.photo_count, 10) || 0;
        const storageUsed = parseFloat(gallery.storage_used) || 0;
        totalPhotos += photoCount;
        totalStorage += storageUsed;
    });
    
    // Convert bytes to GB (approximate: 2.5MB per photo)
    const storageGB = (totalPhotos * 2.5 / 1024).toFixed(1);
    
    // Update portfolio hero summary
    const heroSummary = document.getElementById('heroSummaryText');
    if (heroSummary) {
        heroSummary.textContent = `${totalPhotos} moments captured • ${galleryCount} collections • Trusted worldwide`;
    }
    
    // Update stat cards using the new IDs
    const totalGalleriesEl = document.getElementById('totalGalleries');
    const totalPhotosEl = document.getElementById('totalPhotos');
    const storageUsedEl = document.getElementById('storageUsed');
    
    if (totalGalleriesEl) {
        totalGalleriesEl.textContent = galleryCount;
    }
    if (totalPhotosEl) {
        totalPhotosEl.textContent = totalPhotos.toLocaleString(); // Format with commas for readability
    }
    if (storageUsedEl) {
        storageUsedEl.textContent = storageGB;
    }
    
    console.log(`📊 Dashboard stats updated: ${galleryCount} galleries, ${totalPhotos} photos, ${storageGB} GB storage`);
}
/**
 * Update Storage card with usage and limit information from dashboard stats
 */
function updateStorageCardFromStats(stats) {
    const usedGB = (stats.storage_used_gb || 0).toFixed(1);
    const limitGB = stats.storage_limit_gb || 5;
    const availableGB = (stats.storage_available_gb || 0).toFixed(1);
    const storagePercent = stats.storage_percent || 0;
    const storageUsedEl = document.getElementById('storageUsed');
    const storageLimitEl = document.getElementById('storageLimit');
    const storageAvailableEl = document.getElementById('storageAvailable');
    if (storageUsedEl) {
        storageUsedEl.textContent = usedGB;
    }
    if (storageLimitEl) {
        storageLimitEl.textContent = ` GB / ${limitGB} GB`;
    }
    if (storageAvailableEl) {
        storageAvailableEl.textContent = `${availableGB} GB available`;
    }
}
/**
 * Update Storage card with usage and limit information
 */
function updateStorageCard(usage) {
    const storageLimit = usage.storage_limit || {};
    const usedGB = (storageLimit.used_gb || 0).toFixed(1);
    const limitGB = storageLimit.limit_gb === -1 ? 'Unlimited' : storageLimit.limit_gb;
    const availableGB = storageLimit.limit_gb === -1 ? 'Unlimited' : ((storageLimit.limit_gb || 0) - (storageLimit.used_gb || 0)).toFixed(1);
    const storageUsedEl = document.getElementById('storageUsed');
    const storageLimitEl = document.getElementById('storageLimit');
    const storageAvailableEl = document.getElementById('storageAvailable');
    if (storageUsedEl) {
        storageUsedEl.textContent = usedGB;
    }
    if (storageLimitEl) {
        if (limitGB === 'Unlimited') {
            storageLimitEl.textContent = ' GB';
        } else {
            storageLimitEl.textContent = ` GB / ${limitGB} GB`;
        }
    }
    if (storageAvailableEl) {
        if (limitGB === 'Unlimited') {
            storageAvailableEl.textContent = 'Unlimited storage';
        } else {
            storageAvailableEl.textContent = `${availableGB} GB available`;
        }
    }
}
/**
 * Update Galleries card with usage and limit information
 */
function updateGalleriesCard(usage, galleryCount) {
    const galleryLimit = usage.gallery_limit || {};
    const limit = galleryLimit.limit === -1 ? 'Unlimited' : galleryLimit.limit;
    const galleryLimitEl = document.getElementById('galleryLimit');
    if (galleryLimitEl) {
        if (limit === 'Unlimited') {
            galleryLimitEl.textContent = '/ Unlimited';
        } else {
            galleryLimitEl.textContent = ` / ${limit}`;
        }
    }
}
/**
 * Load and display user's galleries
 */
function loadUserGalleries(galleries) {
    // Try new container ID first, fallback to old selector
    let galleriesContainer = document.getElementById('galleriesGridContainer');
    if (!galleriesContainer) {
        galleriesContainer = document.querySelector('#your-work .item-11.input-7');
    }
    if (!galleriesContainer) return;
    // Clear existing placeholder galleries
    galleriesContainer.innerHTML = '';
    if (galleries.length === 0) {
        galleriesContainer.innerHTML = `
            <div class="card-18 hero-10 animation-11 textarea-7">
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <h3 class="grid-15 animation-7">No Galleries Yet</h3>
                        <div class="input-15 background-7">
                            <p style="margin-bottom: 20px;">
                                Start sharing your artistry by creating your first gallery.
                            </p>
                            <button type="button" class="item-5 idtTuz submit-btn" onclick="window.location.href='new-gallery'">
                                <div class="main-6 jpIyal">
                                    <span>Create Your First Gallery</span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return;
    }
    // Create gallery cards
    galleries.forEach(gallery => {
        const photoCount = gallery.photo_count || 0;
        // storage_used is already in MB (from backend), convert to GB
        const storageUsedMB = gallery.storage_used || 0;
        const storageUsedGB = (storageUsedMB / 1024).toFixed(2);
        const timeAgo = getTimeAgo(gallery.created_at);
        const galleryCard = document.createElement('div');
        galleryCard.className = 'card-18 hero-10 animation-11 textarea-7';
        galleryCard.innerHTML = `
            <div class="button-18 list-7">
                <div class="container-15 item-7">
                    <h3 class="grid-15 animation-7">${escapeHtml(gallery.name)}</h3>
                    <div class="input-15 background-7">
                        <p style="margin-bottom: 8px; font-weight: 500;">
                            ${escapeHtml(gallery.client_name || 'No client name')}
                        </p>
                        <p style="font-size: 14px; opacity: 0.7; margin-bottom: 16px;">
                            ${photoCount} images • ${storageUsedGB} GB • Shared ${timeAgo}
                        </p>
                        ${gallery.description ? `
                            <p style="font-size: 13px; line-height: 1.5; margin-bottom: 20px; opacity: 0.8;">
                                ${escapeHtml(gallery.description.substring(0, 100))}${gallery.description.length > 100 ? '...' : ''}
                            </p>
                        ` : ''}
                        <button type="button" class="item-5 idtTuz submit-btn" onclick="window.location.href='gallery?id=${gallery.id}'">
                            <div class="main-6 jpIyal">
                                <span>View Collection</span>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        `;
        galleriesContainer.appendChild(galleryCard);
    });
}
/**
 * Copy gallery link to clipboard
 */
function copyGalleryLink(event) {
    const galleryId = window.currentGalleryId || new URLSearchParams(window.location.search).get('id');
    if (!galleryId) {
        alert('Gallery ID not found');
        return;
    }
    const galleryUrl = `${window.location.origin}/gallery?id=${galleryId}`;
    // Check if clipboard API is available
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
        // Fallback for older browsers or non-HTTPS
        const textArea = document.createElement('textarea');
        textArea.value = galleryUrl;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showCopySuccess(event);
        } catch (err) {
            document.body.removeChild(textArea);
            console.error('Failed to copy:', err);
            alert(`Copy this link: ${galleryUrl}`);
        }
        return;
    }
    // Modern clipboard API
    navigator.clipboard.writeText(galleryUrl).then(() => {
        showCopySuccess(event);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert(`Copy this link: ${galleryUrl}`);
    });
}
/**
 * Show copy success feedback
 */
function showCopySuccess(event) {
    const btn = event?.target?.closest('a');
    if (!btn) {
        alert('Link copied to clipboard!');
        return;
    }
    // Find the parent div with class 'title-18 main-6'
    const textDiv = btn.querySelector('.title-18.main-6');
    if (!textDiv) {
        alert('Link copied to clipboard!');
        return;
    }
    // Find the inner span that contains the text and SVG
    const innerSpan = textDiv.querySelector('span');
    if (!innerSpan) {
        alert('Link copied to clipboard!');
        return;
    }
    // Check if already showing success (prevent multiple clicks)
    if (btn.dataset.copying === 'true') {
        return;
    }
    // Mark as copying
    btn.dataset.copying = 'true';
    // Store original display
    const originalOpacity = innerSpan.style.opacity;
    const originalTransform = innerSpan.style.transform;
    // Create success message element
    const successMsg = document.createElement('span');
    successMsg.textContent = '✓ Copied!';
    successMsg.style.cssText = `
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.2s ease;
    `;
    // Make parent relative for absolute positioning
    textDiv.style.position = 'relative';
    // Add success message
    textDiv.appendChild(successMsg);
    // Animate: fade out original, fade in success
    setTimeout(() => {
        innerSpan.style.opacity = '0';
        innerSpan.style.transform = 'translateY(-5px)';
        innerSpan.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        successMsg.style.opacity = '1';
    }, 10);
    // Restore after 2 seconds
    setTimeout(() => {
        // Fade out success, fade in original
        successMsg.style.opacity = '0';
        innerSpan.style.opacity = originalOpacity || '1';
        innerSpan.style.transform = originalTransform || 'translateY(0)';
        // Remove success message after animation
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.remove();
            }
            delete btn.dataset.copying;
        }, 200);
    }, 2000);
}
/**
 * Helper: Calculate time ago
 */
function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval !== 1 ? 's' : ''} ago`;
        }
    }
    return 'just now';
}
/**
 * Helper: Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
/**
 * Helper: Show error message
 */
function showError(message) {
    // Create error notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => {
        errorDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}
// Export functions to global scope
window.loadGalleryData = loadGalleryData;
window.loadDashboardData = loadDashboardData;
window.copyGalleryLink = copyGalleryLink;
/**
 * Global function to trigger file input (called from HTML onclick)
 */
window.triggerFileUpload = function() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        try {
            fileInput.click();
        } catch (error) {
            console.error('❌ Error clicking file input:', error);
        }
    } else {
        console.error('❌ File input not found when triggered');
    }
};
/**
 * Setup photo upload functionality
 * Uses UploadQueue to accumulate files from multiple selections
 */
function setupPhotoUpload(galleryId) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) {
        console.error('❌ File input not found in setupPhotoUpload');
        return;
    }
    
    // Initialize upload queue (or use existing one)
    if (!window.uploadQueue) {
        window.uploadQueue = new window.UploadQueue(galleryId);
    }
    
    // IMPORTANT: Don't clone! Just add the listener directly
    // Cloning removes the element and breaks the onclick reference
    // First, remove any existing change listeners by setting a flag
    if (fileInput._uploadHandlerAttached) {
        return;
    }
    // Add upload handler - uses queue to accumulate files
    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) {
            return;
        }
        
        // Add files to queue (handles accumulation and processing)
        window.uploadQueue.addFiles(files);
        
        // Clear input to allow re-selecting same files if needed
        e.target.value = '';
    });
    
    // Mark as attached
    fileInput._uploadHandlerAttached = true;
}

/**
 * Read file as base64 WITHOUT any compression or modification
 * Preserves original quality, size, and dimensions
 */
async function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Extract base64 data (remove data:image/xxx;base64, prefix)
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        // Read file as Data URL (base64)
        reader.readAsDataURL(file);
    });
}
/**
 * Handle image load error - log details for debugging
 */
async function handleImageLoadError(img, photoId, filename) {
    const failedUrl = img.src;
    console.error(`❌ Image load failed for photo ${photoId}`);
    console.error(`   Filename: ${filename}`);
    console.error(`   Failed URL: ${failedUrl}`);
    
    // Check if it's a RAW format
    const isRAW = filename && /\.(dng|cr2|cr3|nef|arw|raf|orf|rw2|pef|3fr)$/i.test(filename);
    
    if (isRAW) {
        console.warn(`⚠️  RAW image failed to load. CloudFront transformation may not be configured.`);
        console.warn(`   Expected: URL with ?format=jpeg parameters`);
        console.warn(`   Actual: ${failedUrl}`);
        
        // Try loading the original URL directly (might work if CloudFront is configured)
        // But browsers can't display RAW, so this will likely fail too
        console.log(`   Note: Browsers cannot display RAW formats directly.`);
        console.log(`   Solution: Lambda@Edge must process ?format=jpeg parameters.`);
    }
    
    // Show visual error indicator
    img.style.border = '2px solid #ef4444';
    img.style.opacity = '0.5';
    img.alt = 'Image failed to load - check console for details';
    
    // Add error overlay
    const errorOverlay = document.createElement('div');
    errorOverlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(239, 68, 68, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ef4444;
        font-size: 12px;
        font-weight: 500;
    `;
    errorOverlay.textContent = 'Load Error';
    img.parentElement.style.position = 'relative';
    img.parentElement.appendChild(errorOverlay);
}

/**
 * Load more photos (called by button)
 */
function loadMorePhotos() {
    const photos = window.galleryPhotos || [];
    const remainingPhotos = photos.length - paginationPhotoIndex;
    if (remainingPhotos > 0) {
        // Render next batch
        renderGalleryPhotos(photos, paginationPhotoIndex, PHOTOS_PER_PAGE);
        // Re-add "Load More" button if there are still more photos
        if (paginationPhotoIndex < photos.length) {
            addLoadMoreButton();
        }
    }
}
// Export new functions
window.setupPhotoUpload = setupPhotoUpload;
window.loadMorePhotos = loadMorePhotos;

/**
 * Send batch email notification to all clients about new photos
 * Called from "Send Email" button in gallery.html
 */
window.sendBatchEmailNotification = async function() {
    try {
        const galleryId = window.currentGalleryId || new URLSearchParams(window.location.search).get('id');
        if (!galleryId) {
            showError('Gallery ID not found');
            return;
        }

        const notifyButton = document.getElementById('notifyClientsButton');
        if (notifyButton) {
            notifyButton.disabled = true;
            const originalText = notifyButton.querySelector('.title-18 span').innerHTML;
            notifyButton.querySelector('.title-18 span').innerHTML = 'Sending...';
        }

        // Send batch notification via API
        const response = await apiRequest(`galleries/${galleryId}/photos/notify-clients`, {
            method: 'POST'
        });

        if (response && response.success) {
            // Show success message
            if (notifyButton) {
                notifyButton.querySelector('.title-18 span').innerHTML = '✓ Sent!';
                notifyButton.style.background = 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)';
                notifyButton.style.color = '#0d5c1f';

                // Reset after 3 seconds
                setTimeout(() => {
                    notifyButton.querySelector('.title-18 span').innerHTML = originalText;
                    notifyButton.style.background = '';
                    notifyButton.style.color = '';
                    notifyButton.disabled = false;
                }, 3000);
            }
        } else {
            throw new Error(response?.error || 'Failed to send notification');
        }
    } catch (error) {
        console.error('Error sending batch notification:', error);
        showError(error.message || 'Failed to send notification. Please try again.');
        
        // Reset button on error
        const notifyButton = document.getElementById('notifyClientsButton');
        if (notifyButton) {
            notifyButton.disabled = false;
            const originalText = notifyButton.querySelector('.title-18 span').textContent;
            notifyButton.querySelector('.title-18 span').innerHTML = originalText;
        }
    }
};

/**
 * Send selection reminder to all clients
 * Called from "Remind Clients" button in gallery.html
 * Photographer has FULL CONTROL - manual trigger only
 */
window.sendSelectionReminder = async function() {
    try {
        const galleryId = window.currentGalleryId || new URLSearchParams(window.location.search).get('id');
        if (!galleryId) {
            showError('Gallery ID not found');
            return;
        }

        const remindButton = document.getElementById('remindClientsButton');
        let originalText = 'Remind Clients'; // Default fallback
        if (remindButton) {
            remindButton.disabled = true;
            originalText = remindButton.querySelector('.title-18 span').innerHTML;
            remindButton.querySelector('.title-18 span').innerHTML = 'Sending...';
        }

        // Send selection reminder via API
        const response = await apiRequest(`notifications/send-selection-reminder`, {
            method: 'POST',
            body: JSON.stringify({
                gallery_id: galleryId,
                message: '' // Optional custom message
            })
        });

        if (response && response.success) {
            // Show success message
            if (remindButton) {
                remindButton.querySelector('.title-18 span').innerHTML = '✓ Sent!';
                remindButton.style.border = '2px solid #28a745';
                remindButton.style.color = '#0d5c1f';

                // Reset after 3 seconds
                setTimeout(() => {
                    remindButton.querySelector('.title-18 span').innerHTML = originalText;
                    remindButton.style.background = '';
                    remindButton.style.border = '';
                    remindButton.style.color = '';
                    remindButton.disabled = false;
                }, 3000);
            }
        } else {
            throw new Error(response?.error || 'Failed to send reminder');
        }
    } catch (error) {
        console.error('Error sending selection reminder:', error);
        showError(error.message || 'Failed to send reminder. Please try again.');
        
        // Reset button on error
        const remindButton = document.getElementById('remindClientsButton');
        if (remindButton) {
            remindButton.disabled = false;
            // Get the original text from the beginning
            remindButton.querySelector('.title-18 span').innerHTML = 'Remind Clients';
            remindButton.style.background = '';
            remindButton.style.border = '';
            remindButton.style.color = '';
        }
    }
};