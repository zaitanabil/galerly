/**
 * Galerly - Client Dashboard
 * Load all galleries accessible to the client
 */

document.addEventListener('DOMContentLoaded', function() {
    loadClientGalleries();
});

/**
 * Load all galleries where client has access
 */
async function loadClientGalleries() {
    try {
        
        // Fetch galleries accessible to this client
        const data = await apiRequest('client/galleries');
        
        const galleries = data.galleries || [];
        
        // Update stats
        updateClientStats(galleries);
        
        // Display galleries
        displayClientGalleries(galleries);
        
    } catch (error) {
        console.error('❌ Error loading client galleries:', error);
        showError('Failed to load galleries. Please try again.');
    }
}

/**
 * Update client stats
 */
function updateClientStats(galleries) {
    const totalGalleries = galleries.length;
    const totalPhotos = galleries.reduce((sum, g) => sum + (g.photo_count || 0), 0);
    const pendingPhotos = galleries.reduce((sum, g) => {
        const pending = (g.photos || []).filter(p => p.status === 'pending').length;
        return sum + pending;
    }, 0);
    const photographerCount = new Set(galleries.map(g => g.photographer_id || g.user_id)).size;
    
    // Update galleries stat
    const galleriesCountEl = document.getElementById('client-stat-galleries-count');
    const galleriesLabelEl = document.getElementById('client-stat-galleries-label');
    if (galleriesCountEl) galleriesCountEl.textContent = totalGalleries;
    if (galleriesLabelEl) galleriesLabelEl.textContent = totalGalleries === 1 ? 'gallery' : 'galleries';
    
    // Update photos stat
    const photosCountEl = document.getElementById('client-stat-photos-count');
    const photosLabelEl = document.getElementById('client-stat-photos-label');
    const photosDescEl = document.getElementById('client-stat-photos-desc');
    if (photosCountEl) photosCountEl.textContent = totalPhotos;
    if (photosLabelEl) photosLabelEl.textContent = totalPhotos === 1 ? 'photo' : 'photos';
    if (photosDescEl) {
        if (pendingPhotos > 0) {
            photosDescEl.textContent = `${pendingPhotos} ${pendingPhotos === 1 ? 'photo' : 'photos'} awaiting your approval`;
            photosDescEl.style.color = '#FFA500';
            photosDescEl.style.fontWeight = '600';
        } else {
            photosDescEl.textContent = 'All photos approved';
            photosDescEl.style.color = '';
            photosDescEl.style.fontWeight = '';
        }
    }
    
    // Update photographers stat
    const photographersCountEl = document.getElementById('client-stat-photographers-count');
    const photographersLabelEl = document.getElementById('client-stat-photographers-label');
    if (photographersCountEl) photographersCountEl.textContent = photographerCount;
    if (photographersLabelEl) photographersLabelEl.textContent = photographerCount === 1 ? 'photographer' : 'photographers';
}

/**
 * Display client galleries
 */
function displayClientGalleries(galleries) {
    const container = document.getElementById('client-galleries-container');
    if (!container) {
        console.error('Gallery container not found!');
        return;
    }
    
    // Clear loading message
    container.innerHTML = '';
    
    if (galleries.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px;">
                <h3 style="font-size: 20px; margin-bottom: 12px;">No Galleries Yet</h3>
                <p style="font-size: 14px; opacity: 0.6;">Galleries shared with you will appear here.</p>
            </div>
        `;
        return;
    }
    
    // Group galleries by photographer
    const groupedGalleries = galleries.reduce((groups, gallery) => {
        const photographerId = gallery.photographer_id || 'unknown';
        if (!groups[photographerId]) {
            groups[photographerId] = {
                photographer_name: gallery.photographer_name || 'Unknown Photographer',
                galleries: []
            };
        }
        groups[photographerId].galleries.push(gallery);
        return groups;
    }, {});
    
    // Render galleries grouped by photographer
    Object.values(groupedGalleries).forEach(group => {
        // Add photographer header
        const header = document.createElement('div');
        header.style.cssText = 'grid-column: 1/-1; margin-top: 40px; margin-bottom: 20px;';
        header.innerHTML = `
            <h3 style="font-size: 18px; font-weight: 600; opacity: 0.8;">
                ${group.photographer_name}
            </h3>
        `;
        container.appendChild(header);
        
        // Render galleries
        group.galleries.forEach(gallery => {
            const card = createGalleryCard(gallery);
            container.appendChild(card);
        });
    });
}

/**
 * Create gallery card
 */
function createGalleryCard(gallery) {
    const card = document.createElement('div');
    card.className = 'card-18 hero-10 animation-11 textarea-7';
    card.style.cursor = 'pointer';
    card.onclick = () => window.location.href = `client-gallery?id=${gallery.id}`;
    
    // Get cover image
    const coverImage = gallery.cover_image || 
                      (gallery.photos && gallery.photos[0] && gallery.photos[0].url) ||
                      'https://via.placeholder.com/400x300?text=No+Photos';
    
    // Count pending photos
    const pendingCount = (gallery.photos || []).filter(p => p.status === 'pending').length;
    
    card.innerHTML = `
        <div class="button-18 list-7" style="height: 100%;">
            <!-- Cover Image -->
            <div style="width: 100%; height: 240px; overflow: hidden; border-radius: var(--border-radius-m); margin-bottom: var(--size-l); position: relative;">
                <img 
                    src="${getImageUrl(coverImage)}" 
                    alt="${gallery.name}" 
                    style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;"
                    onmouseover="this.style.transform='scale(1.05)'"
                    onmouseout="this.style.transform='scale(1)'"
                    onerror="this.src='https://via.placeholder.com/400x300?text=No+Photos'"
                />
                <div style="position: absolute; top: var(--size-m); right: var(--size-m); background: rgba(0, 0, 0, 0.7); color: white; padding: var(--size-xs) var(--size-s); border-radius: var(--border-radius-s); font-size: 0.875rem; backdrop-filter: blur(8px);">
                    ${gallery.photo_count || 0} ${(gallery.photo_count || 0) === 1 ? 'photo' : 'photos'}
                </div>
                ${pendingCount > 0 ? `
                    <div style="position: absolute; top: var(--size-m); left: var(--size-m); background: #FFA500; color: white; padding: var(--size-xs) var(--size-s); border-radius: var(--border-radius-s); font-size: 0.875rem; font-weight: 600;">
                        ${pendingCount} pending
                    </div>
                ` : ''}
            </div>
            
            <!-- Gallery Info -->
            <div class="container-15 item-7">
                <h3 class="grid-15 animation-7" style="margin-bottom: var(--size-s);">
                    ${gallery.name || 'Untitled Gallery'}
                </h3>
                
                <div class="input-15 background-7">
                    ${gallery.description ? `
                        <p style="margin-bottom: var(--size-m); line-height: 1.6; color: var(--color-text-secondary);">
                            ${gallery.description}
                        </p>
                    ` : ''}
                    
                    <p style="color: var(--color-text-secondary); font-size: 0.875rem; margin-bottom: var(--size-s);">
                        Created ${formatDate(gallery.created_at)}
                    </p>
                    
                    <div style="display: flex; gap: var(--size-s); margin-top: var(--size-m);">
                        ${gallery.allow_downloads ? `
                            <span style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.8125rem; color: var(--color-text-secondary);">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7 10 12 15 17 10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                                Download allowed
                            </span>
                        ` : ''}
                        ${gallery.allow_comments ? `
                            <span style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.8125rem; color: var(--color-text-secondary);">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                                </svg>
                                Comments enabled
                            </span>
                        ` : ''}
                    </div>
                    
                    <div style="margin-top: var(--size-l);">
                        <a 
                            href="client-gallery?id=${gallery.id}" 
                            onclick="event.stopPropagation();"
                            style="display: inline-flex; align-items: center; gap: var(--size-xs); color: var(--color-primary); font-weight: 600; text-decoration: none; transition: gap 0.2s ease;"
                            onmouseover="this.style.gap='var(--size-s)'"
                            onmouseout="this.style.gap='var(--size-xs)'"
                        >
                            View Gallery
                            <svg width="17" height="14" viewBox="0 0 17 14" fill="none">
                                <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" stroke="currentColor" stroke-linecap="round"></path>
                                <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'today';
        if (diffDays === 1) return 'yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return `${Math.floor(diffDays / 365)} years ago`;
    } catch (e) {
        return 'Unknown date';
    }
}


/**
 * Show error message
 */
function showError(message) {
    const container = document.getElementById('client-galleries-container');
    if (container) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px;">
                <p style="font-size: 18px; margin-bottom: 12px; color: var(--color-error);">⚠️ ${message}</p>
            </div>
        `;
    }
}

