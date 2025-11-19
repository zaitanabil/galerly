/**
 * Galerly - Photographer Portfolio Page
 * Display individual photographer's galleries and work
 */

let photographerId = null;

// Load photographer portfolio on page load
document.addEventListener('DOMContentLoaded', function() {
    
    // Get photographer ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    photographerId = urlParams.get('id');
    
    if (!photographerId) {
        showError('No photographer ID provided');
        return;
    }
    
    loadPortfolio();
});

// Load photographer's portfolio
async function loadPortfolio() {
    try {
        // Fetch photographer data
        const response = await fetch(`${window.GalerlyConfig.API_BASE_URL}/photographers/${photographerId}`);
        
        if (!response.ok) {
            throw new Error('Photographer not found');
        }
        
        const photographer = await response.json();
        
        // Update page title
        document.title = `${photographer.name || photographer.username} — Portfolio — Galerly`;
        
        // Update hero section
        document.getElementById('photographerName').textContent = photographer.name || photographer.username || 'Anonymous';
        document.getElementById('photographerCity').textContent = photographer.city || 'UNKNOWN LOCATION';
        document.getElementById('photographerBio').textContent = photographer.bio || 'No bio available.';
        
        // Update tagline
        const tagline = photographer.specialties && photographer.specialties.length > 0
            ? photographer.specialties.join(' • ')
            : 'Professional Photography';
        document.getElementById('photographerTagline').textContent = tagline;
        
        // Update stats
        document.getElementById('galleryCount').textContent = photographer.gallery_count || 0;
        document.getElementById('photoCount').textContent = photographer.photo_count || 0;
        
        // Load galleries
        loadGalleries(photographer.galleries || []);
        
    } catch (error) {
        console.error('Error loading portfolio:', error);
        showError(error.message || 'Failed to load portfolio');
    }
}

// Load and display galleries
function loadGalleries(galleries) {
    const grid = document.getElementById('galleriesGrid');
    
    if (!galleries || galleries.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;">
                <p style="font-size: 18px; margin-bottom: 12px;">No public galleries yet</p>
                <p style="font-size: 14px;">This photographer hasn't shared any public galleries.</p>
            </div>
        `;
        return;
    }
    
    // Clear grid
    grid.innerHTML = '';
    
    // Render gallery cards
    galleries.forEach(gallery => {
        const card = createGalleryCard(gallery);
        grid.appendChild(card);
    });
}

// Create gallery card element
function createGalleryCard(gallery) {
    const card = document.createElement('div');
    card.className = 'card-18 hero-10 animation-11 textarea-7';
    card.style.cursor = 'pointer';
    card.onclick = () => window.location.href = `gallery?id=${gallery.id}`;
    
    // Get cover image (first photo or placeholder)
    const coverImage = gallery.photos && gallery.photos[0] && gallery.photos[0].url
        ? gallery.photos[0].url
        : 'https://via.placeholder.com/400x300?text=No+Photos+Yet';
    
    const photoCount = gallery.photo_count || (gallery.photos ? gallery.photos.length : 0);
    
    card.innerHTML = `
        <div class="button-18 list-7" style="height: 100%;">
            <!-- Cover Image -->
            <div style="width: 100%; height: 240px; overflow: hidden; border-radius: var(--border-radius-m); margin-bottom: var(--size-l); position: relative;">
                <img 
                    src="${coverImage}" 
                    alt="${gallery.name}" 
                    style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;"
                    onmouseover="this.style.transform='scale(1.05)'"
                    onmouseout="this.style.transform='scale(1)'"
                    onerror="this.src='https://via.placeholder.com/400x300?text=No+Photos+Yet'"
                />
                <div style="position: absolute; top: var(--size-m); right: var(--size-m); background: rgba(0, 0, 0, 0.7); color: white; padding: var(--size-xs) var(--size-s); border-radius: var(--border-radius-s); font-size: 0.875rem; backdrop-filter: blur(8px);">
                    ${photoCount} ${photoCount === 1 ? 'photo' : 'photos'}
                </div>
            </div>
            
            <!-- Gallery Info -->
            <div class="container-15 item-7">
                <h3 class="grid-15 animation-7" style="margin-bottom: var(--size-s);">
                    ${gallery.name || 'Untitled Gallery'}
                </h3>
                
                <div class="input-15 background-7">
                    ${gallery.description ? `
                        <p style="margin-bottom: var(--size-m); line-height: 1.6; color: var(--color-text-secondary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            ${gallery.description}
                        </p>
                    ` : ''}
                    
                    <p style="color: var(--color-text-secondary); font-size: 0.875rem;">
                        Created ${formatDate(gallery.created_at)}
                    </p>
                    
                    <div style="margin-top: var(--size-l);">
                        <a 
                            href="gallery?id=${gallery.id}" 
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

// Format date for display
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

// Show error message
function showError(message) {
    const grid = document.getElementById('galleriesGrid');
    grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px;">
            <p style="font-size: 18px; margin-bottom: 12px; color: var(--color-error);">⚠️ ${message}</p>
            <p style="font-size: 14px; color: var(--color-text-secondary);">
                <a href="photographers" style="color: var(--color-primary); text-decoration: none;">
                    ← Back to photographers directory
                </a>
            </p>
        </div>
    `;
    
    // Update hero to show error
    document.getElementById('photographerName').textContent = 'Not Found';
    document.getElementById('photographerCity').textContent = 'ERROR';
    document.getElementById('photographerBio').textContent = message;
    document.getElementById('photographerTagline').textContent = '';
}

