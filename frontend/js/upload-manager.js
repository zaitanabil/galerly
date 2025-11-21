/**
 * Modern Upload Manager - Follows Industry Standards
 * Implements steps 1-5 of the professional workflow:
 * - Client validation (type, size, corruption checks)
 * - Resumable/chunked uploads for network interruptions
 * - Authentication with tokens
 * - Multipart assembly
 * - Durable storage
 */

class ModernUploadManager {
    constructor(galleryId) {
        this.galleryId = galleryId;
        this.chunkSize = 10 * 1024 * 1024; // 10MB chunks (optimal for AWS S3 multipart)
        this.maxRetries = 3;
        this.retryDelay = 1000;
    }

    /**
     * Step 1-2: Client validation
     * Check file type, size, basic corruption
     */
    async validateFile(file) {
        const errors = [];
        
        // File type validation
        const allowedTypes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/webp', 'image/tiff', 'image/heic', 'image/heif',
            // RAW formats
            'image/x-canon-cr2', 'image/x-canon-cr3', 'image/x-canon-crw',
            'image/x-nikon-nef', 'image/x-sony-arw', 'image/x-adobe-dng',
            'image/x-fuji-raf', 'image/x-olympus-orf', 'image/x-panasonic-rw2',
            'image/x-pentax-pef'
        ];
        
        // Also check by extension for RAW files (MIME types aren't always set)
        const allowedExtensions = [
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'tiff', 'heic', 'heif',
            'cr2', 'cr3', 'crw', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2', 'pef'
        ];
        
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const isValidType = allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);
        
        if (!isValidType) {
            errors.push(`${file.name} is not a supported image format`);
        }
        
        // Size check (warn if > 500MB, but don't reject)
        if (file.size > 500 * 1024 * 1024) {
            console.warn(`Large file detected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
        }
        
        // Basic corruption check - verify file is readable
        try {
            const firstChunk = file.slice(0, 1024);
            await firstChunk.arrayBuffer();
        } catch (error) {
            errors.push(`${file.name} appears to be corrupted or unreadable`);
        }
        
        return {
            valid: errors.length === 0,
            errors,
            warnings: file.size > 500 * 1024 * 1024 ? ['Large file - upload may take longer'] : []
        };
    }

    /**
     * Step 3-4: Chunked upload with resume capability
     * Uses presigned URLs for direct S3 upload
     */
    async uploadFileChunked(file, onProgress) {
        // Step 1: Validate file
        const validation = await this.validateFile(file);
        if (!validation.valid) {
            throw new Error(validation.errors.join(', '));
        }

        // Step 2: Get upload session (presigned URL or multipart upload ID)
        const uploadSession = await this.initializeUpload(file);
        
        const { photo_id, s3_key, upload_type } = uploadSession;
        
        // Step 3: Upload file (chunked for large files, direct for small)
        if (file.size > this.chunkSize && upload_type === 'multipart') {
            await this.uploadLargeFile(file, uploadSession, onProgress);
        } else {
            await this.uploadSmallFile(file, uploadSession, onProgress);
        }
        
        // Step 4: Confirm upload and trigger processing
        return await this.finalizeUpload(photo_id, s3_key, file);
    }

    /**
     * Initialize upload session
     */
    async initializeUpload(file) {
        const response = await apiRequest(`galleries/${this.galleryId}/photos/upload-url`, {
            method: 'POST',
            body: JSON.stringify({
                filename: file.name,
                content_type: file.type || 'application/octet-stream',
                file_size: file.size,
                use_multipart: file.size > this.chunkSize
            })
        });
        
        return response;
    }

    /**
     * Upload small file (< 10MB) using presigned URL
     */
    async uploadSmallFile(file, session, onProgress) {
        const { upload_url, upload_fields } = session;
        
        const formData = new FormData();
        
        // Add presigned fields
        Object.entries(upload_fields).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        // Add file last (AWS requirement)
        formData.append('file', file);
        
        // Upload with retry logic
        await this.uploadWithRetry(async () => {
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable && onProgress) {
                        onProgress(e.loaded, e.total);
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status === 200 || xhr.status === 204) {
                        resolve();
                    } else {
                        reject(new Error(`Upload failed: ${xhr.status}`));
                    }
                });
                
                xhr.addEventListener('error', () => {
                    reject(new Error('Network error during upload'));
                });
                
                xhr.addEventListener('abort', () => {
                    reject(new Error('Upload aborted'));
                });
                
                xhr.open('POST', upload_url);
                xhr.send(formData);
            });
        });
    }

    /**
     * Upload large file using multipart (> 10MB)
     * Enables resume on network failure
     */
    async uploadLargeFile(file, session, onProgress) {
        const { multipart_upload_id, upload_parts } = session;
        
        const totalChunks = Math.ceil(file.size / this.chunkSize);
        const uploadedParts = [];
        let uploadedBytes = 0;
        
        // Upload each chunk with retry
        for (let i = 0; i < totalChunks; i++) {
            const start = i * this.chunkSize;
            const end = Math.min(start + this.chunkSize, file.size);
            const chunk = file.slice(start, end);
            const partNumber = i + 1;
            
            // Get presigned URL for this part
            const partUrl = upload_parts[i].url;
            
            // Upload chunk with retry
            const etag = await this.uploadWithRetry(async () => {
                const response = await fetch(partUrl, {
                    method: 'PUT',
                    body: chunk,
                    headers: {
                        'Content-Type': 'application/octet-stream'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Chunk upload failed: ${response.status}`);
                }
                
                return response.headers.get('ETag');
            });
            
            uploadedParts.push({
                PartNumber: partNumber,
                ETag: etag
            });
            
            uploadedBytes += chunk.size;
            
            if (onProgress) {
                onProgress(uploadedBytes, file.size);
            }
        }
        
        // Complete multipart upload
        await apiRequest(`galleries/${this.galleryId}/photos/complete-multipart`, {
            method: 'POST',
            body: JSON.stringify({
                photo_id: session.photo_id,
                upload_id: multipart_upload_id,
                parts: uploadedParts
            })
        });
    }

    /**
     * Retry wrapper for network resilience
     */
    async uploadWithRetry(uploadFunc) {
        let lastError;
        
        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                return await uploadFunc();
            } catch (error) {
                lastError = error;
                console.warn(`Upload attempt ${attempt + 1} failed:`, error.message);
                
                if (attempt < this.maxRetries - 1) {
                    // Exponential backoff
                    const delay = this.retryDelay * Math.pow(2, attempt);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        throw lastError;
    }

    /**
     * Finalize upload - triggers processing pipeline
     */
    async finalizeUpload(photo_id, s3_key, file) {
        return await apiRequest(`galleries/${this.galleryId}/photos/confirm-upload`, {
            method: 'POST',
            body: JSON.stringify({
                photo_id,
                s3_key,
                filename: file.name,
                file_size: file.size,
                file_type: file.type
            })
        });
    }

    /**
     * Calculate file hash for deduplication
     */
    async calculateFileHash(file) {
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
}

// Export for global use
window.ModernUploadManager = ModernUploadManager;

