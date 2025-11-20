/**
 * Photo Download Tool
 * Provides Download All functionality with pre-generated ZIP files
 */

/**
 * Initialize download toolbar
 */
function initPhotoSelection() {
    // Add download toolbar if it doesn't exist
    addSelectionToolbar();
}

/**
 * Add selection toolbar above gallery grid
 */
function addSelectionToolbar() {
    const gallerySection = document.querySelector('.gallery-grid')?.parentElement;
    if (!gallerySection) return;
    
    // Check if toolbar already exists
    if (document.getElementById('selectionToolbar')) return;
    
    const toolbar = document.createElement('div');
    toolbar.id = 'selectionToolbar';
    toolbar.style.cssText = `
        grid-column: 1/-1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--size-m) var(--size-l);
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius-m);
        margin-bottom: var(--size-l);
        flex-wrap: wrap;
        gap: var(--size-m);
    `;
    
    toolbar.innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--size-m); flex-wrap: wrap;">
            <!-- Download All Button - Fully Rounded -->
            <button id="downloadAllBtn" class="selection-btn-primary" onclick="downloadAllPhotos()" style="
                padding: 12px 24px;
                background: linear-gradient(135deg, #0066CC 0%, #0052A3 100%);
                border: none;
                border-radius: 9999px;
                color: white;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
                display: flex;
                align-items: center;
                gap: 8px;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 102, 204, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(0, 102, 204, 0.3)'">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>Download All Photos</span>
            </button>
        </div>
    `;
    
    // Insert before gallery grid
    const galleryGrid = document.querySelector('.gallery-grid');
    if (galleryGrid && galleryGrid.parentElement) {
        galleryGrid.parentElement.insertBefore(toolbar, galleryGrid);
    }
}

// Selection functions removed - no longer needed

/**
 * Download all photos as ZIP
 * Downloads pre-generated ZIP file from S3/CloudFront (instant download)
 * Supports both authenticated and token-based access
 */
async function downloadAllPhotos() {
    const galleryId = window.currentGalleryId;
    if (!galleryId) {
        showNotification('Gallery ID not available', 'error');
        return;
    }
    
    const downloadBtn = document.getElementById('downloadAllBtn');
    const originalText = downloadBtn ? downloadBtn.innerHTML : 'Download All Photos';
    
    if (downloadBtn) {
        downloadBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 10"></polyline>
            </svg>
            <span>Preparing download...</span>
        `;
        downloadBtn.disabled = true;
    }
    
    try {
        let response;
        
        // Check if accessing via token (public access)
        const urlParams = new URLSearchParams(window.location.search);
        const shareToken = urlParams.get('token');
        
        if (shareToken && window.isPublicGalleryAccess) {
            // Use token-based endpoint for public access
            response = await apiRequest('downloads/bulk/by-token', {
                method: 'POST',
                body: JSON.stringify({ token: shareToken })
            });
        } else {
            // Use authenticated endpoint
            response = await apiRequest(`galleries/${galleryId}/download-bulk`, {
                method: 'POST',
                body: JSON.stringify({})
            });
        }
        
        if (!response.zip_url) {
            throw new Error('ZIP URL not available');
        }
        
        // Download ZIP file directly from CloudFront
        const link = document.createElement('a');
        link.href = response.zip_url;
        link.download = response.filename || 'gallery-photos.zip';
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Track downloads
        if (typeof window.trackPhotoDownload === 'function' && window.currentGalleryId) {
            const photos = window.galleryPhotos || [];
            photos.forEach(photo => {
                try {
                    window.trackPhotoDownload(photo.id, window.currentGalleryId, {
                        ip: '',
                        user_agent: navigator.userAgent,
                        batch_download: true,
                        method: 'pre-generated-zip'
                    });
                } catch (err) {
                    console.error('Error tracking download:', err);
                }
            });
        }
        
        showNotification(`Download started! ${response.photo_count || 0} photos`);
        
    } catch (error) {
        console.error('Error downloading all photos:', error);
        showNotification('Failed to download. Please try again.', 'error');
    } finally {
        if (downloadBtn) {
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }
    }
}

// Selection persistence functions removed - no longer needed

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
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export functions to global scope
window.downloadAllPhotos = downloadAllPhotos;
window.initPhotoSelection = initPhotoSelection;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPhotoSelection);
} else {
    initPhotoSelection();
}

