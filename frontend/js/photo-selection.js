/**
 * Photo Selection Tool
 * Allows clients to select photos for batch operations (download, etc.)
 */

// Track selected photos (global for access from other scripts)
window.selectedPhotos = new Set();
let selectedPhotos = window.selectedPhotos;

/**
 * Initialize photo selection mode
 */
function initPhotoSelection() {
    // Add selection toolbar if it doesn't exist
    addSelectionToolbar();
    
    // Load saved selections from localStorage
    loadSavedSelections();
    
    // Auto-select all photos by default for better UX
    // This happens after a short delay to ensure photos are loaded
    setTimeout(() => {
        // Only auto-select if no saved selections exist
        if (selectedPhotos.size === 0) {
            autoSelectAllPhotos();
        }
    }, 500);
    
    // Update UI
    updateSelectionUI();
}

/**
 * Auto-select all photos by default for better UX
 */
function autoSelectAllPhotos() {
    const photos = window.galleryPhotos || [];
    photos.forEach(photo => {
        selectedPhotos.add(photo.id);
    });
    updateSelectionUI();
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
            <!-- Prominent Download Button - Fully Rounded -->
            <button id="downloadSelectedBtn" class="selection-btn-primary" onclick="downloadSelectedPhotos()" style="
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
                <span>Download <span id="downloadCount">0</span> Photos</span>
            </button>
            
            <!-- Selection Info & Controls -->
            <div style="display: flex; align-items: center; gap: var(--size-m); flex-wrap: wrap;">
                <span id="selectionCount" style="
                    font-size: 0.95rem;
                    font-weight: 500;
                    padding: 8px 16px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                ">0 photos selected</span>
                
            <button id="selectAllBtn" class="selection-btn" onclick="selectAllPhotos()" style="
                    padding: 8px 16px;
                background: transparent;
                    border: 1.5px solid rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                color: var(--color-text-primary);
                cursor: pointer;
                font-size: 0.875rem;
                    font-weight: 500;
                transition: all 0.2s ease;
                " onmouseover="this.style.background='rgba(255,255,255,0.1)'; this.style.borderColor='rgba(255,255,255,0.5)'" onmouseout="this.style.background='transparent'; this.style.borderColor='rgba(255,255,255,0.3)'">
                Select All
            </button>
            <button id="deselectAllBtn" class="selection-btn" onclick="deselectAllPhotos()" style="
                    padding: 8px 16px;
                background: transparent;
                    border: 1.5px solid rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                color: var(--color-text-primary);
                cursor: pointer;
                font-size: 0.875rem;
                    font-weight: 500;
                transition: all 0.2s ease;
                " onmouseover="this.style.background='rgba(255,255,255,0.1)'; this.style.borderColor='rgba(255,255,255,0.5)'" onmouseout="this.style.background='transparent'; this.style.borderColor='rgba(255,255,255,0.3)'">
                Deselect All
            </button>
        </div>
        </div>
    `;
    
    // Insert before gallery grid
    const galleryGrid = document.querySelector('.gallery-grid');
    if (galleryGrid && galleryGrid.parentElement) {
        galleryGrid.parentElement.insertBefore(toolbar, galleryGrid);
    }
}

/**
 * Toggle photo selection
 */
function togglePhotoSelection(photoId) {
    if (selectedPhotos.has(photoId)) {
        selectedPhotos.delete(photoId);
    } else {
        selectedPhotos.add(photoId);
    }
    
    // Keep window.selectedPhotos in sync
    window.selectedPhotos = selectedPhotos;
    
    // Save to localStorage
    saveSelections();
    
    // Update UI
    updateSelectionUI();
    updatePhotoCheckbox(photoId);
}

/**
 * Select all photos
 */
function selectAllPhotos() {
    const photos = window.galleryPhotos || [];
    photos.forEach(photo => {
        selectedPhotos.add(photo.id);
    });
    
    // Keep window.selectedPhotos in sync
    window.selectedPhotos = selectedPhotos;
    
    saveSelections();
    updateSelectionUI();
    updateAllPhotoCheckboxes();
}

/**
 * Deselect all photos
 */
function deselectAllPhotos() {
    selectedPhotos.clear();
    window.selectedPhotos = selectedPhotos; // Keep in sync
    
    saveSelections();
    updateSelectionUI();
    updateAllPhotoCheckboxes();
}

/**
 * Update selection UI (toolbar buttons, count)
 */
function updateSelectionUI() {
    const count = selectedPhotos.size;
    const countEl = document.getElementById('selectionCount');
    const downloadCountEl = document.getElementById('downloadCount');
    const downloadBtn = document.getElementById('downloadSelectedBtn');
    
    if (countEl) {
        countEl.textContent = `${count} ${count === 1 ? 'photo' : 'photos'} selected`;
    }
    
    if (downloadCountEl) {
        downloadCountEl.textContent = count;
    }
    
    if (downloadBtn) {
        if (count > 0) {
            downloadBtn.style.opacity = '1';
            downloadBtn.style.pointerEvents = 'auto';
        } else {
            downloadBtn.style.opacity = '0.5';
            downloadBtn.style.pointerEvents = 'none';
        }
    }
}

/**
 * Update single photo checkbox
 */
function updatePhotoCheckbox(photoId) {
    const checkboxWrapper = document.querySelector(`[data-photo-id="${photoId}"] .photo-checkbox-wrapper`);
    if (!checkboxWrapper) return;
    
    const checkbox = checkboxWrapper.querySelector('.photo-checkbox');
    if (!checkbox) return;
    
    const isSelected = selectedPhotos.has(photoId);
    checkbox.checked = isSelected;
    
    // Remove existing checkmark if present
    const existingCheckmark = checkboxWrapper.querySelector('.checkbox-checkmark');
    if (existingCheckmark) {
        existingCheckmark.remove();
    }
    
    // Update visual style for rounded checkbox - ONLY CHECKMARK, NO DOT
    if (isSelected) {
        // Blue filled circle
        checkbox.style.background = '#007AFF';  // Apple blue
        checkbox.style.borderColor = '#007AFF';
        
        // Add white checkmark SVG (NO DOT!)
        const checkmark = document.createElement('div');
        checkmark.className = 'checkbox-checkmark';
        checkmark.innerHTML = `
            <svg width="16" height="13" viewBox="0 0 16 13" fill="none" xmlns="http://www.w3.org/2000/svg" style="
                position: absolute; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%);
            ">
                <path d="M2 6.5L6 10.5L14 2.5" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
        checkmark.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        `;
        checkboxWrapper.appendChild(checkmark);
    } else {
        // White/light gray circle with border (empty)
        checkbox.style.background = 'rgba(255, 255, 255, 0.95)';
        checkbox.style.borderColor = 'rgba(0, 0, 0, 0.15)';
    }
}

/**
 * Update all photo checkboxes
 */
function updateAllPhotoCheckboxes() {
    const photos = window.galleryPhotos || [];
    photos.forEach(photo => {
        updatePhotoCheckbox(photo.id);
    });
}

/**
 * Download selected photos as ZIP
 * NEW: Server-side ZIP generation for 10x faster downloads
 */
async function downloadSelectedPhotos() {
    const photos = window.galleryPhotos || [];
    const selected = photos.filter(p => selectedPhotos.has(p.id));
    
    if (selected.length === 0) {
        showNotification('No photos selected', 'warning');
        return;
    }
    
    const downloadBtn = document.getElementById('downloadSelectedBtn');
    const originalText = downloadBtn ? downloadBtn.textContent : 'Download';
    
    if (downloadBtn) {
        downloadBtn.textContent = `Preparing download...`;
        downloadBtn.disabled = true;
    }
    
    try {
        // NEW: Use backend ZIP generation (10x faster!)
        const photo_ids = selected.map(p => p.id);
        const gallery_id = window.currentGalleryId;
        
        const response = await window.apiRequest(`galleries/${gallery_id}/photos/download-bulk`, {
            method: 'POST',
            body: JSON.stringify({ photo_ids })
        });
        
        // The backend returns the ZIP as base64-encoded binary
        // API Gateway with binary support will automatically decode it
        // Download the file
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        const galleryName = (window.currentGalleryData?.name || 'galerly-photos').replace(/[^a-z0-9]/gi, '-');
        const filename = `${galleryName}-${selected.length}-photos.zip`;
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        
        showNotification(`Successfully prepared download of ${selected.length} ${selected.length === 1 ? 'photo' : 'photos'}!`);
        
        // Track downloads
        if (typeof window.trackPhotoDownload === 'function' && window.currentGalleryId) {
            selected.forEach(photo => {
                try {
                    window.trackPhotoDownload(photo.id, window.currentGalleryId, {
                        ip: '',
                        user_agent: navigator.userAgent,
                        batch_download: true
                    });
                } catch (err) {
                    console.error('Error tracking download:', err);
                }
            });
        }
        
    } catch (error) {
        console.error('Error creating download:', error);
        
        // Fallback to client-side ZIP if backend fails
        if (error.message && error.message.includes('500')) {
            showNotification('Server busy, trying alternative method...', 'warning');
            await downloadSelectedPhotosClientSide(selected);
        } else {
            showNotification('Failed to prepare download. Please try again.', 'error');
        }
    } finally {
        if (downloadBtn) {
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
        }
    }
}

/**
 * Fallback: Client-side ZIP generation
 * Slower but works if backend fails
 */
async function downloadSelectedPhotosClientSide(selected) {
    try {
        // Dynamically load JSZip if not already loaded
        if (typeof JSZip === 'undefined') {
            await loadJSZip();
        }
        
        const zip = new JSZip();
        const galleryName = (window.currentGalleryData?.name || 'galerly-photos').replace(/[^a-z0-9]/gi, '-');
        
        // Track used filenames to handle duplicates
        const usedFilenames = new Map();
        
        // Fetch and add all photos to ZIP
        for (let i = 0; i < selected.length; i++) {
            const photo = selected[i];
            
            try {
                const imageUrl = window.getImageUrl(photo.url);
                const response = await fetch(imageUrl, {
                    method: 'GET',
                    mode: 'cors',
                    cache: 'no-cache',
                    credentials: 'omit'
                });
                
                if (!response.ok) throw new Error(`Failed to fetch: ${response.status}`);
                
                const blob = await response.blob();
                let baseFilename = photo.filename || `photo-${photo.id}.jpg`;
                
                // Handle duplicate filenames
                let finalFilename = baseFilename;
                if (usedFilenames.has(baseFilename)) {
                    const lastDotIndex = baseFilename.lastIndexOf('.');
                    const nameWithoutExt = lastDotIndex > 0 ? baseFilename.substring(0, lastDotIndex) : baseFilename;
                    const extension = lastDotIndex > 0 ? baseFilename.substring(lastDotIndex) : '';
                    
                    const timestamp = photo.created_at 
                        ? new Date(photo.created_at).getTime() 
                        : Date.now() + i;
                    
                    finalFilename = `${nameWithoutExt}_${timestamp}${extension}`;
                    
                    let counter = 1;
                    while (usedFilenames.has(finalFilename)) {
                        finalFilename = `${nameWithoutExt}_${timestamp}_${counter}${extension}`;
                        counter++;
                    }
                }
                
                usedFilenames.set(finalFilename, (usedFilenames.get(finalFilename) || 0) + 1);
                zip.file(finalFilename, blob);
            } catch (error) {
                console.error(`Error fetching photo ${photo.id}:`, error);
            }
        }
        
        // Generate ZIP
        const zipBlob = await zip.generateAsync({ 
            type: 'blob',
            compression: 'DEFLATE',
            compressionOptions: { level: 6 }
        });
        
        // Download ZIP file
        const zipUrl = URL.createObjectURL(zipBlob);
        const link = document.createElement('a');
        link.href = zipUrl;
        link.download = `${galleryName}-${selected.length}-photos.zip`;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        setTimeout(() => URL.revokeObjectURL(zipUrl), 1000);
        
        showNotification(`Successfully downloaded ${selected.length} ${selected.length === 1 ? 'photo' : 'photos'} as ZIP!`);
        
    } catch (error) {
        console.error('Error creating client-side ZIP:', error);
        showNotification('Failed to create ZIP. Please try again.', 'error');
    }
}

/**
 * Load JSZip library dynamically
 */
function loadJSZip() {
    return new Promise((resolve, reject) => {
        if (typeof JSZip !== 'undefined') {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
        script.onload = resolve;
        script.onerror = () => reject(new Error('Failed to load JSZip'));
        document.head.appendChild(script);
    });
}

/**
 * Save selections to localStorage
 */
function saveSelections() {
    const galleryId = window.currentGalleryId;
    if (!galleryId) return;
    
    const key = `selected_photos_${galleryId}`;
    localStorage.setItem(key, JSON.stringify(Array.from(selectedPhotos)));
}

/**
 * Load saved selections from localStorage
 */
function loadSavedSelections() {
    const galleryId = window.currentGalleryId;
    if (!galleryId) return;
    
    const key = `selected_photos_${galleryId}`;
    const saved = localStorage.getItem(key);
    
    if (saved) {
        try {
            selectedPhotos = new Set(JSON.parse(saved));
            window.selectedPhotos = selectedPhotos; // Keep in sync
        } catch (e) {
            console.error('Error loading saved selections:', e);
            selectedPhotos = new Set();
            window.selectedPhotos = selectedPhotos;
        }
    }
}

/**
 * Clear selections for current gallery
 */
function clearSelections() {
    selectedPhotos.clear();
    window.selectedPhotos = selectedPhotos; // Keep in sync
    
    const galleryId = window.currentGalleryId;
    if (galleryId) {
        const key = `selected_photos_${galleryId}`;
        localStorage.removeItem(key);
    }
    updateSelectionUI();
    updateAllPhotoCheckboxes();
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
window.togglePhotoSelection = togglePhotoSelection;
window.selectAllPhotos = selectAllPhotos;
window.deselectAllPhotos = deselectAllPhotos;
window.downloadSelectedPhotos = downloadSelectedPhotos;
window.initPhotoSelection = initPhotoSelection;
window.clearSelections = clearSelections;
window.autoSelectAllPhotos = autoSelectAllPhotos;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPhotoSelection);
} else {
    initPhotoSelection();
}

