/**
 * Photo Deletion Management
 * Handles single and batch photo deletion for photographers
 */

// Track selected photos for deletion
window.selectedPhotosForDeletion = new Set();

/**
 * Initialize photo deletion UI
 */
function initializePhotoDeletion() {
    // Add checkboxes to photos
    addPhotoCheckboxes();
    
    // Add bulk action toolbar
    addBulkActionToolbar();
    
    // Add delete buttons to photo modal
    addModalDeleteButton();
}

/**
 * Add selection checkboxes to gallery photos
 */
function addPhotoCheckboxes() {
    const photos = document.querySelectorAll('.gallery-photo');
    
    photos.forEach((photoEl, index) => {
        // Skip if checkbox already exists
        if (photoEl.querySelector('.photo-checkbox-wrapper-delete')) {
            return;
        }
        
        const photoId = photoEl.querySelector('img')?.getAttribute('data-photo-id');
        if (!photoId) return;
        
        // Create checkbox wrapper
        const checkboxWrapper = document.createElement('div');
        checkboxWrapper.className = 'photo-checkbox-wrapper-delete';
        checkboxWrapper.setAttribute('data-photo-id', photoId);
        checkboxWrapper.style.cssText = `
            position: absolute;
            top: 12px;
            left: 12px;
            width: 24px;
            height: 24px;
            z-index: 10;
            cursor: pointer;
        `;
        
        // Create visual checkbox (circle)
        const checkbox = document.createElement('div');
        checkbox.className = 'photo-checkbox-delete';
        checkbox.style.cssText = `
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.95);
            border: 1.5px solid rgba(0, 0, 0, 0.15);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            position: relative;
        `;
        
        checkboxWrapper.appendChild(checkbox);
        
        // Add click handler
        checkboxWrapper.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent photo modal from opening
            e.preventDefault();
            
            const isSelected = window.selectedPhotosForDeletion.has(photoId);
            togglePhotoSelection(photoId, !isSelected);
            updateCheckboxVisual(photoId);
        });
        
        photoEl.style.position = 'relative';
        photoEl.appendChild(checkboxWrapper);
    });
}

/**
 * Update checkbox visual state
 */
function updateCheckboxVisual(photoId) {
    const checkboxWrapper = document.querySelector(`.photo-checkbox-wrapper-delete[data-photo-id="${photoId}"]`);
    if (!checkboxWrapper) return;
    
    const checkbox = checkboxWrapper.querySelector('.photo-checkbox-delete');
    if (!checkbox) return;
    
    const isSelected = window.selectedPhotosForDeletion.has(photoId);
    
    // Remove existing checkmark if present
    const existingCheckmark = checkboxWrapper.querySelector('.checkbox-checkmark-delete');
    if (existingCheckmark) {
        existingCheckmark.remove();
    }
    
    if (isSelected) {
        // Blue filled circle
        checkbox.style.background = '#007AFF';  // Apple blue
        checkbox.style.borderColor = '#007AFF';
        
        // Add white checkmark in center
        const checkmark = document.createElement('div');
        checkmark.className = 'checkbox-checkmark-delete';
        checkmark.innerHTML = `
            <svg width="14" height="11" viewBox="0 0 14 11" fill="none" xmlns="http://www.w3.org/2000/svg" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                <path d="M1 5.5L5 9.5L13 1.5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
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
        // White/light gray circle with border
        checkbox.style.background = 'rgba(255, 255, 255, 0.95)';
        checkbox.style.borderColor = 'rgba(0, 0, 0, 0.15)';
    }
}

/**
 * Update all checkboxes visual state
 */
function updateAllCheckboxesVisual() {
    window.selectedPhotosForDeletion.forEach(photoId => {
        updateCheckboxVisual(photoId);
    });
    
    // Also update unchecked ones
    const allCheckboxes = document.querySelectorAll('.photo-checkbox-wrapper-delete');
    allCheckboxes.forEach(wrapper => {
        const photoId = wrapper.getAttribute('data-photo-id');
        if (!window.selectedPhotosForDeletion.has(photoId)) {
            updateCheckboxVisual(photoId);
        }
    });
}

/**
 * Toggle photo selection
 */
function togglePhotoSelection(photoId, selected) {
    if (selected) {
        window.selectedPhotosForDeletion.add(photoId);
    } else {
        window.selectedPhotosForDeletion.delete(photoId);
    }
    
    updateBulkActionToolbar();
}

/**
 * Select all photos
 */
function selectAllPhotos() {
    // Get ALL photos from window.galleryPhotos (includes hidden/not-yet-loaded photos)
    if (window.galleryPhotos && Array.isArray(window.galleryPhotos)) {
        window.galleryPhotos.forEach(photo => {
            if (photo.id) {
                window.selectedPhotosForDeletion.add(photo.id);
            }
        });
    } else {
        // Fallback to visible checkboxes if galleryPhotos not available
        const allWrappers = document.querySelectorAll('.photo-checkbox-wrapper-delete');
        allWrappers.forEach(wrapper => {
            const photoId = wrapper.getAttribute('data-photo-id');
            if (photoId) {
                window.selectedPhotosForDeletion.add(photoId);
            }
        });
    }
    
    updateAllCheckboxesVisual();
    updateBulkActionToolbar();
}

/**
 * Deselect all photos
 */
function deselectAllPhotos() {
    window.selectedPhotosForDeletion.clear();
    updateAllCheckboxesVisual();
    updateBulkActionToolbar();
}

/**
 * Add bulk action toolbar
 */
function addBulkActionToolbar() {
    // Check if toolbar already exists
    if (document.getElementById('bulkActionToolbar')) {
        return;
    }
    
    const galleryGrid = document.querySelector('.gallery-grid');
    if (!galleryGrid) return;
    
    const toolbar = document.createElement('div');
    toolbar.id = 'bulkActionToolbar';
    toolbar.style.cssText = `
        grid-column: 1/-1;
        display: none;
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
        <div style="display: flex; align-items: center; gap: var(--size-m);">
            <button onclick="selectAllPhotos()" style="
                padding: var(--size-xs) var(--size-m);
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: var(--border-radius-s);
                color: var(--color-text-primary);
                cursor: pointer;
                font-size: 0.875rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='rgba(255,255,255,0.1)'" 
               onmouseout="this.style.background='transparent'">
                Select All
            </button>
            <button onclick="deselectAllPhotos()" style="
                padding: var(--size-xs) var(--size-m);
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: var(--border-radius-s);
                color: var(--color-text-primary);
                cursor: pointer;
                font-size: 0.875rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='rgba(255,255,255,0.1)'" 
               onmouseout="this.style.background='transparent'">
                Deselect All
            </button>
            <span id="selectedCount" style="
                font-size: 0.875rem;
                opacity: 0.7;
                margin-left: var(--size-s);
            ">0 photos selected</span>
        </div>
        <div style="display: flex; align-items: center; gap: var(--size-m);">
            <button id="deleteSelectedBtn" onclick="confirmBulkDelete()" style="
                padding: var(--size-xs) var(--size-m);
                background: #FF3B30;
                border: none;
                border-radius: var(--border-radius-s);
                color: white;
                cursor: pointer;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            " onmouseover="this.style.opacity='0.9'" 
               onmouseout="this.style.opacity='1'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Delete Selected (<span id="deleteCount">0</span>)
            </button>
        </div>
    `;
    
    // Insert toolbar before gallery grid
    galleryGrid.parentNode.insertBefore(toolbar, galleryGrid);
    
    // Make functions globally available
    window.selectAllPhotos = selectAllPhotos;
    window.deselectAllPhotos = deselectAllPhotos;
    window.confirmBulkDelete = confirmBulkDelete;
}

/**
 * Update bulk action toolbar visibility and count
 */
function updateBulkActionToolbar() {
    const toolbar = document.getElementById('bulkActionToolbar');
    const selectedCount = document.getElementById('selectedCount');
    const deleteCount = document.getElementById('deleteCount');
    
    if (!toolbar || !selectedCount) return;
    
    const count = window.selectedPhotosForDeletion.size;
    
    if (count > 0) {
        toolbar.style.display = 'flex';
        selectedCount.textContent = `${count} ${count === 1 ? 'photo' : 'photos'} selected`;
        if (deleteCount) {
            deleteCount.textContent = count;
        }
    } else {
        toolbar.style.display = 'none';
    }
}

/**
 * Add delete button to photo modal
 */
function addModalDeleteButton() {
    // This will be called when modal opens
    // We'll add it dynamically in the modal open function
}

/**
 * Confirm bulk delete with modal
 */
function confirmBulkDelete() {
    const count = window.selectedPhotosForDeletion.size;
    if (count === 0) return;
    
    // Create confirmation modal
    const modal = document.createElement('div');
    modal.id = 'deleteConfirmModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-sizing: border-box;
        animation: fadeIn 0.2s ease-out;
    `;
    
    modal.innerHTML = `
        <div style="
            background: var(--background-secondary, #ffffff);
            border-radius: var(--border-radius-xl, 28px);
            padding: var(--size-xl, 32px);
            max-width: 480px;
            width: 100%;
            box-shadow: var(--shadow-default, 0 8px 32px rgba(0, 0, 0, 0.15));
            border: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
        ">
            <div style="text-align: center; margin-bottom: var(--size-l, 24px);">
                <div style="
                    width: 64px;
                    height: 64px;
                    margin: 0 auto var(--size-m, 16px);
                    background: rgba(255, 59, 48, 0.1);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        <line x1="10" y1="11" x2="10" y2="17"></line>
                        <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                </div>
                <h2 style="
                    margin: 0 0 var(--size-s, 12px) 0;
                    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 24px;
                    font-weight: 600;
                    color: var(--text-primary, #1D1D1F);
                ">Delete ${count} ${count === 1 ? 'Photo' : 'Photos'}?</h2>
                <p style="
                    margin: 0;
                    font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 15px;
                    color: var(--text-secondary, #86868B);
                    line-height: 1.5;
                ">This action cannot be undone. ${count === 1 ? 'This photo' : 'These photos'} will be permanently deleted from our databases.</p>
            </div>
            
            <div style="display: flex; gap: var(--size-m, 16px);">
                <button onclick="closeDeleteConfirmModal()" style="
                    flex: 1;
                    padding: 14px;
                    background: var(--background-primary, #F5F5F7);
                    color: var(--text-primary, #1D1D1F);
                    border: none;
                    border-radius: var(--border-radius-s, 12px);
                    cursor: pointer;
                    font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 15px;
                    font-weight: 600;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='var(--primary-200, #E0E0E0)';" 
                   onmouseout="this.style.background='var(--background-primary, #F5F5F7)';">
                    Cancel
                </button>
                
                <button onclick="executeBulkDelete()" style="
                    flex: 1;
                    padding: 14px;
                    background: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: var(--border-radius-s, 12px);
                    cursor: pointer;
                    font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 15px;
                    font-weight: 600;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='#D70015';" onmouseout="this.style.background='#FF3B30';">
                    Delete
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeDeleteConfirmModal();
        }
    });
    
    // Close on Escape key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeDeleteConfirmModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Make functions globally available
    window.closeDeleteConfirmModal = closeDeleteConfirmModal;
    window.executeBulkDelete = executeBulkDelete;
}

/**
 * Close delete confirmation modal
 */
function closeDeleteConfirmModal() {
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) {
        modal.style.animation = 'fadeIn 0.2s ease-out reverse';
        setTimeout(() => {
            modal.remove();
        }, 200);
    }
}

/**
 * Execute bulk delete
 */
async function executeBulkDelete() {
    const photoIds = Array.from(window.selectedPhotosForDeletion);
    if (photoIds.length === 0) return;
    
    closeDeleteConfirmModal();
    
    // Show loading state
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            <span>Deleting...</span>
        `;
    }
    
    try {
        // Get gallery ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const galleryId = urlParams.get('id');
        
        if (!galleryId) {
            throw new Error('Gallery ID not found');
        }
        
        // Call delete API
        const response = await window.apiRequest(`galleries/${galleryId}/photos/delete`, {
            method: 'DELETE',
            body: JSON.stringify({ photo_ids: photoIds })
        });
        
        // Show success message
        showNotification(
            `Successfully deleted ${response.deleted_count} photo(s)`,
            'success'
        );
        
        // Remove deleted photos from UI
        photoIds.forEach(photoId => {
            const photoEl = document.querySelector(`img[data-photo-id="${photoId}"]`)?.closest('.gallery-photo');
            if (photoEl) {
                photoEl.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => photoEl.remove(), 300);
            }
        });
        
        // Clear selection
        window.selectedPhotosForDeletion.clear();
        updateBulkActionToolbar();
        
        // Reload gallery data to update count
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error deleting photos:', error);
        showNotification('Failed to delete photos. Please try again.', 'error');
        
        // Reset button
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                <span>Delete Selected</span>
            `;
        }
    }
}

/**
 * Delete single photo (from modal)
 */
async function deleteSinglePhoto(photoId) {
    if (!photoId) return;
    
    // Use the same confirmation and delete flow
    window.selectedPhotosForDeletion.clear();
    window.selectedPhotosForDeletion.add(photoId);
    confirmBulkDelete();
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
        background: ${type === 'success' ? '#34C759' : '#FF3B30'};
        color: white;
        padding: 16px 24px;
        border-radius: var(--border-radius-m, 16px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10001;
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 15px;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Export functions globally
window.initializePhotoDeletion = initializePhotoDeletion;
window.togglePhotoSelection = togglePhotoSelection;
window.deleteSinglePhoto = deleteSinglePhoto;

