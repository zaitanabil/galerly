/**
 * Gallery Upload Progress UI
 * Creates and manages upload progress cards with progress bars
 */

/**
 * Create a progress card for a file upload
 */
function createProgressCard(file, container) {
    const fileItem = document.createElement('div');
    fileItem.className = 'upload-file-item';
    fileItem.dataset.filename = file.name;
    fileItem.dataset.progress = '0';
    
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
    
    fileItem.innerHTML = `
        <div class="upload-file-preview">
            <img src="" alt="${escapeHtml(file.name)}" style="display: none;">
            <div class="upload-file-placeholder" style="
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--primary-5030);
                color: var(--text-secondary);
                font-size: 2rem;
            ">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 36V12C12 10.9 12.9 10 14 10H34C35.1 10 36 10.9 36 12V36C36 37.1 35.1 38 34 38H14C12.9 38 12 37.1 12 36Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M16 28L20 24L24 28L30 20L36 28" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="21" cy="17" r="2" fill="currentColor"/>
                </svg>
            </div>
        </div>
        <div class="upload-file-info">
            <div class="upload-file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
            <div class="upload-file-meta" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--size-xs);
            ">
                <div class="upload-file-size" style="
                    font-family: var(--pp-neue-font);
                    font-size: 0.8125rem;
                    color: var(--text-secondary);
                ">${fileSizeMB} MB</div>
                <div class="upload-file-percentage" style="
                    font-family: var(--pp-neue-font);
                    font-size: 0.8125rem;
                    font-weight: 600;
                    color: var(--color-blue);
                ">0%</div>
            </div>
            <div class="upload-file-status"></div>
            <div class="upload-progress-bar" style="
                width: 100%;
                height: 8px;
                background: var(--primary-100);
                border-radius: 999px;
                overflow: hidden;
                margin-top: var(--size-xs);
            ">
                <div class="upload-progress-fill" style="
                    height: 100%;
                    width: 0%;
                    background: var(--color-blue);
                    border-radius: 999px;
                    transition: width 0.3s ease, background 0.3s ease;
                "></div>
            </div>
        </div>
    `;
    
    // Load preview image
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = fileItem.querySelector('.upload-file-preview img');
        const placeholder = fileItem.querySelector('.upload-file-placeholder');
        if (img && placeholder) {
            img.src = e.target.result;
            img.style.display = 'block';
            placeholder.style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
    
    if (container) container.appendChild(fileItem);
    return fileItem;
}

/**
 * Update file upload progress
 */
function updateFileProgress(fileItem, status, message, progress) {
    if (!fileItem) return;
    
    fileItem.dataset.status = status;
    fileItem.dataset.progress = progress;
    
    const statusEl = fileItem.querySelector('.upload-file-status');
    const progressFill = fileItem.querySelector('.upload-progress-fill');
    const percentageEl = fileItem.querySelector('.upload-file-percentage');
    
    // Update status message
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = 'upload-file-status';
        
        // Apply status-specific styling
        switch(status) {
            case 'checking':
                statusEl.style.color = 'var(--text-secondary)';
                break;
            case 'uploading':
                statusEl.style.color = 'var(--color-blue)';
                break;
            case 'success':
                statusEl.className = 'upload-file-status success';
                break;
            case 'error':
                statusEl.className = 'upload-file-status error';
                break;
            case 'warning':
                statusEl.style.color = 'var(--semantic-warning)';
                break;
            case 'skipped':
                statusEl.style.color = 'var(--text-secondary)';
                break;
        }
    }
    
    // Update progress bar
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
        
        // Update progress bar color based on status
        switch(status) {
            case 'success':
                progressFill.style.background = 'var(--color-mint)';
                break;
            case 'error':
                progressFill.style.background = 'var(--semantic-error)';
                break;
            case 'warning':
                progressFill.style.background = 'var(--semantic-warning)';
                break;
            case 'skipped':
                progressFill.style.background = 'var(--color-gray-medium)';
                break;
            default:
                progressFill.style.background = 'var(--color-blue)';
        }
    }
    
    // Update percentage
    if (percentageEl) {
        percentageEl.textContent = `${progress}%`;
        
        // Update percentage color based on status
        switch(status) {
            case 'success':
                percentageEl.style.color = 'var(--color-mint)';
                break;
            case 'error':
                percentageEl.style.color = 'var(--semantic-error)';
                break;
            default:
                percentageEl.style.color = 'var(--color-blue)';
        }
    }
    
    // Add visual feedback for completion
    if (status === 'success') {
        fileItem.classList.add('completed');
    }
}

// Export functions globally
window.createProgressCard = createProgressCard;
window.updateFileProgress = updateFileProgress;

