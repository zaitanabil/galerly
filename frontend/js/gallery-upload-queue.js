/**
 * Gallery Upload Queue Manager
 * Handles accumulating files from multiple selections and processing them sequentially
 * Allows photographers to add files while upload is in progress (e.g., 125 files + 1 more = 126)
 */

class UploadQueue {
    constructor(galleryId) {
        this.galleryId = galleryId;
        this.queue = [];
        this.isProcessing = false;
        this.uploadedCount = 0;
        this.skippedCount = 0;
        this.failedCount = 0;
        this.totalAdded = 0;
    }

    /**
     * Add files to the upload queue
     * @param {File[]} files - Array of File objects to add
     */
    addFiles(files) {
        const newFiles = Array.from(files);
        this.queue.push(...newFiles);
        this.totalAdded += newFiles.length;
        
        console.log(`📥 Added ${newFiles.length} files to queue. Total in queue: ${this.queue.length}, Total added: ${this.totalAdded}`);
        
        // Update UI to show new total
        this.updateProgressLabel();
        
        // Start processing if not already running
        if (!this.isProcessing) {
            this.processQueue();
        }
    }

    /**
     * Update progress label to show current total
     */
    updateProgressLabel() {
        const progressLabel = document.getElementById('progressLabel');
        const progressCounter = document.getElementById('progressCounter');
        
        if (progressLabel) {
            const total = this.uploadedCount + this.skippedCount + this.failedCount + this.queue.length;
            progressLabel.textContent = `Uploading ${total} ${total === 1 ? 'file' : 'files'}`;
        }
        
        if (progressCounter) {
            const completed = this.uploadedCount + this.skippedCount + this.failedCount;
            const total = completed + this.queue.length;
            progressCounter.textContent = `${completed} / ${total}`;
        }
    }

    /**
     * Process all files in the queue
     */
    async processQueue() {
        if (this.isProcessing) {
            console.log('⏳ Already processing queue');
            return;
        }

        this.isProcessing = true;
        
        // Show/create progress UI
        this.initializeProgressUI();

        // Process each file in the queue
        while (this.queue.length > 0) {
            const file = this.queue.shift(); // Take first file from queue
            await this.uploadFile(file);
        }

        // All files processed
        this.isProcessing = false;
        this.finalizeUpload();
    }

    /**
     * Initialize or update progress UI
     */
    initializeProgressUI() {
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadFilesList = document.getElementById('uploadFilesList');
        
        if (uploadProgress) {
            uploadProgress.style.display = 'block';
        }

        let progressContainer = document.getElementById('overallProgress');
        
        if (!progressContainer) {
            // Create new progress container
            if (uploadFilesList) {
                uploadFilesList.innerHTML = '';
            }
            
            progressContainer = document.createElement('div');
            progressContainer.id = 'overallProgress';
            progressContainer.style.cssText = `
                grid-column: 1/-1;
                width: 100%;
                padding: var(--size-l) var(--size-xl);
                background: var(--background-secondary);
                border-radius: 999px;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-default);
                font-family: var(--pp-neue-font);
                transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
                margin-bottom: var(--size-l);
            `;
            
            const total = this.uploadedCount + this.skippedCount + this.failedCount + this.queue.length;
            progressContainer.innerHTML = `
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--size-m);
                ">
                    <span id="progressLabel" style="
                        font-family: 'SF Pro Text', -apple-system, sans-serif;
                        font-weight: 500;
                        font-size: 0.9375rem;
                        color: var(--text-primary);
                        letter-spacing: -0.01em;
                    ">Uploading ${total} ${total === 1 ? 'file' : 'files'}</span>
                    <span id="progressCounter" style="
                        font-family: 'SF Pro Text', -apple-system, sans-serif;
                        font-weight: 600;
                        font-size: 0.875rem;
                        color: var(--text-secondary);
                    ">0 / ${total}</span>
                </div>
                <div style="
                    width: 100%;
                    height: 8px;
                    background: var(--neutral-100);
                    border-radius: 999px;
                    overflow: hidden;
                    position: relative;
                ">
                    <div id="progressBarFill" style="
                        width: 0%;
                        height: 100%;
                        background: var(--color-blue);
                        border-radius: 999px;
                        transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1), background 0.3s ease;
                    "></div>
                </div>
            `;
            
            if (uploadFilesList) {
                uploadFilesList.appendChild(progressContainer);
            }
        }
    }

    /**
     * Upload a single file
     * @param {File} file - File to upload
     */
    async uploadFile(file) {
        try {
            // 🚀 BIG TECH SOLUTION: Convert HEIC to JPEG (Instagram/Booking.com approach)
            // This happens CLIENT-SIDE before upload for universal browser compatibility
            if (typeof window.processImageForUpload === 'function') {
                console.log(`📸 Processing image: ${file.name}`);
                try {
                    file = await window.processImageForUpload(file);
                    console.log(`✅ Image processed: ${file.name}`);
                } catch (processError) {
                    console.warn(`⚠️  Image processing failed, using original:`, processError);
                    // Continue with original file
                }
            }
            
            // Step 1: Check for duplicates
            let checkResponse;
            try {
                checkResponse = await apiRequest(`galleries/${this.galleryId}/photos/check-duplicates`, {
                    method: 'POST',
                    body: JSON.stringify({
                        filename: file.name,
                        file_size: file.size
                    })
                });
            } catch (checkError) {
                console.warn('Duplicate check failed:', checkError);
                checkResponse = { has_duplicates: false };
            }

            // Step 2: Handle duplicates
            if (checkResponse.has_duplicates && checkResponse.duplicates && checkResponse.duplicates.length > 0) {
                if (typeof window.showDuplicateComparisonModal === 'function') {
                    const userDecision = await window.showDuplicateComparisonModal(
                        file,
                        null,
                        checkResponse.duplicates
                    );
                    if (userDecision === 'skip') {
                        this.skippedCount++;
                        this.updateProgress();
                        return;
                    }
                }
            }

            // Step 3: Get presigned URL
            const urlResponse = await apiRequest(`galleries/${this.galleryId}/photos/upload-url`, {
                method: 'POST',
                body: JSON.stringify({
                    filename: file.name,
                    content_type: file.type || 'image/jpeg',
                    file_size: file.size
                })
            });

            const { photo_id, s3_key, upload_url, upload_fields } = urlResponse;

            // Step 4: Upload to S3
            const formData = new FormData();
            Object.entries(upload_fields).forEach(([key, value]) => {
                formData.append(key, value);
            });
            formData.append('file', file);

            const s3Response = await fetch(upload_url, {
                method: 'POST',
                body: formData
            });

            if (!s3Response.ok && s3Response.status !== 204) {
                throw new Error(`S3 upload failed: ${s3Response.status}`);
            }

            // Step 5: Confirm upload (triggers security validation)
            const confirmResponse = await apiRequest(`galleries/${this.galleryId}/photos/confirm-upload`, {
                method: 'POST',
                body: JSON.stringify({
                    photo_id: photo_id,
                    s3_key: s3_key,
                    filename: file.name,
                    file_size: file.size
                })
            });

            this.uploadedCount++;
            console.log(`✅ Uploaded: ${file.name}`);

        } catch (error) {
            this.failedCount++;
            console.error(`❌ Failed to upload ${file.name}:`, error);
            
            // Show user-friendly error
            if (error.message && error.message.includes('Security threat detected')) {
                this.showError(`Security threat detected in ${file.name}. File rejected.`);
            }
        }

        this.updateProgress();
    }

    /**
     * Update progress bar and counter
     */
    updateProgress() {
        const completed = this.uploadedCount + this.skippedCount + this.failedCount;
        const total = completed + this.queue.length;
        const percent = total > 0 ? (completed / total) * 100 : 0;

        const progressBarFill = document.getElementById('progressBarFill');
        const progressCounter = document.getElementById('progressCounter');

        if (progressBarFill) {
            progressBarFill.style.width = `${percent}%`;
        }

        if (progressCounter) {
            progressCounter.textContent = `${completed} / ${total}`;
        }
    }

    /**
     * Finalize upload - show completion status
     */
    finalizeUpload() {
        const progressBarFill = document.getElementById('progressBarFill');
        const progressLabel = document.getElementById('progressLabel');
        const progressCounter = document.getElementById('progressCounter');

        if (this.failedCount === 0) {
            // All successful
            if (progressBarFill) {
                progressBarFill.style.background = '#34C759';
            }
            if (progressLabel) {
                progressLabel.style.color = '#1D8348';
                progressLabel.innerHTML = `<span style="font-size: 16px; font-weight: 700; margin-right: 6px;">✓</span>Upload Complete`;
            }
            if (progressCounter) {
                progressCounter.style.color = '#1D8348';
                progressCounter.textContent = `${this.uploadedCount} uploaded${this.skippedCount > 0 ? `, ${this.skippedCount} skipped` : ''}`;
            }
        } else {
            // Some failures
            if (progressBarFill) {
                progressBarFill.style.background = '#FF9500';
            }
            if (progressLabel) {
                progressLabel.style.color = '#856404';
                progressLabel.innerHTML = `<span style="font-size: 16px; font-weight: 700; margin-right: 6px;">⚠</span>Partial Upload`;
            }
            if (progressCounter) {
                progressCounter.style.color = '#856404';
                progressCounter.textContent = `${this.uploadedCount} uploaded, ${this.failedCount} failed`;
            }
        }

        // Reload gallery after delay
        setTimeout(async () => {
            const uploadProgress = document.getElementById('uploadProgress');
            if (uploadProgress) {
                uploadProgress.style.display = 'none';
            }
            if (typeof loadGalleryData === 'function') {
                await loadGalleryData();
            }
        }, 3000);

        // Reset counters for next batch
        this.uploadedCount = 0;
        this.skippedCount = 0;
        this.failedCount = 0;
        this.totalAdded = 0;
    }

    /**
     * Show error message to user
     */
    showError(message) {
        // You can enhance this with your toast/notification system
        console.error(message);
        alert(message);
    }
}

// Create global upload queue instance
window.uploadQueue = null;

// Export for use in gallery-loader.js
window.UploadQueue = UploadQueue;

