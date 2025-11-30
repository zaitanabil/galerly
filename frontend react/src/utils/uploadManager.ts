/* eslint-disable @typescript-eslint/no-explicit-any */
// Upload manager - handles photo uploads with progress tracking, multipart support, and retries
import { config, apiBaseUrl } from '../config/env';
import * as photoService from '../services/photoService';

// Add heic2any type definition if needed, or use any
// declare global {
//   interface Window {
//     heic2any: any;
//   }
// }

export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  photoId?: string;
}

export interface UploadOptions {
  galleryId: string;
  onProgress?: (progress: UploadProgress[]) => void;
  onComplete?: (photoIds: string[]) => void;
  onError?: (error: string) => void;
}

class UploadManager {
  private uploads: Map<string, UploadProgress> = new Map();
  private activeUploads = 0;
  private maxConcurrent = config.upload.maxConcurrentUploads || 3;
  private CHUNK_SIZE = 10 * 1024 * 1024; // 10MB chunks
  private MAX_RETRIES = 3;
  private RETRY_DELAY = 1000;

  // Upload files with progress tracking
  async uploadFiles(files: File[], options: UploadOptions): Promise<string[]> {
    this.uploads.clear();
    const newQueue: { file: File, id: string }[] = [];
    
    // 1. Initialize all progress entries immediately
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileId = `${file.name}-${Date.now()}-${i}`;
        
        this.uploads.set(fileId, {
          fileId,
          fileName: file.name,
          progress: 0,
          status: 'pending',
        });
        
        // Pass raw file to queue. Processing will happen in uploadSingleFile
        newQueue.push({ file, id: fileId });
    }

    this.notifyProgress(options.onProgress);
    
    // Trigger uploads
    this.uploadQueueWithIds(newQueue, options);
    
    // Wait for completion (simplified polling)
    await new Promise<void>((resolve) => {
        const checkInterval = setInterval(() => {
            const pendingOrUploading = Array.from(this.uploads.values())
                .some(p => p.status === 'pending' || p.status === 'uploading' || p.status === 'processing');
            
            if (!pendingOrUploading && this.activeUploads === 0) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 500);
    });

    const successfulIds = Array.from(this.uploads.values())
        .filter(p => p.status === 'completed' && p.photoId)
        .map(p => p.photoId!);
    
    if (options.onComplete) {
      options.onComplete(successfulIds);
    }
    
    return successfulIds;
  }

  // Helper to handle queue processing with explicit IDs
  private async uploadQueueWithIds(queueItems: { file: File, id: string }[], options: UploadOptions) {
      const promises: Promise<void>[] = [];
      
      const processNext = () => {
          while (this.activeUploads < this.maxConcurrent && queueItems.length > 0) {
              const item = queueItems.shift();
              if (item) {
                  const promise = this.uploadSingleFile(item.file, item.id, options)
                      .then(() => { processNext(); })
                      .catch(() => { processNext(); });
                  promises.push(promise);
              }
          }
      };
      
      processNext();
  }

  // Validate file client-side
  private async validateFile(file: File): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];
    
    // Type check (basic)
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
        // Allow raw extensions if mime type is missing/generic
        const ext = file.name.split('.').pop()?.toLowerCase();
        const allowedExtensions = ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'orf', 'mp4', 'mov', 'avi', 'webm'];
        if (!ext || !allowedExtensions.includes(ext)) {
             errors.push('File type not supported');
        }
    }

    return { valid: errors.length === 0, errors };
  }

  // Upload a single file
  private async uploadSingleFile(
    file: File,
    fileId: string,
    options: UploadOptions
  ): Promise<string | null> {
    this.activeUploads++;
    
    try {
      // Process file (convert if needed)
      if (this.isHEIC(file)) {
          this.updateProgress(fileId, { status: 'processing', progress: 1 });
          this.notifyProgress(options.onProgress);
          
          file = await this.convertHEICtoJPEG(file);
          
          this.updateProgress(fileId, { fileName: file.name });
      }
      
      // Validate
      const validation = await this.validateFile(file);
      if (!validation.valid) {
          throw new Error(validation.errors.join(', '));
      }

      this.updateProgress(fileId, { status: 'uploading', progress: 1 });
      this.notifyProgress(options.onProgress);

      let photoId: string | undefined;

      // Determine upload strategy based on size
      if (file.size > this.CHUNK_SIZE) {
        photoId = await this.uploadLargeFile(file, fileId, options);
      } else {
        photoId = await this.uploadSmallFile(file, fileId, options);
      }

      if (photoId) {
        this.updateProgress(fileId, { status: 'completed', progress: 100, photoId });
        this.notifyProgress(options.onProgress);
        return photoId;
      }
      return null;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      this.updateProgress(fileId, { status: 'error', error: errorMessage });
      this.notifyProgress(options.onProgress);
      
      if (options.onError) {
        options.onError(`${file.name}: ${errorMessage}`);
      }
      
      return null;
    } finally {
      this.activeUploads--;
    }
  }

  // Calculate SHA-256 hash of file
  private async calculateFileHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Strategy 1: Small File Upload (< 10MB)
  private async uploadSmallFile(file: File, fileId: string, options: UploadOptions): Promise<string> {
      // Calculate hash early for consistency
      const fileHash = await this.calculateFileHash(file);

      // Get presigned URL
      const urlResponse = await photoService.getUploadUrl(
        options.galleryId,
        file.name,
        file.size,
        file.type
      );

      if (!urlResponse.success || !urlResponse.data) {
        throw new Error(urlResponse.error || 'Failed to get upload URL');
      }

      const { upload_url, photo_id, s3_key } = urlResponse.data as any;

      // Upload to S3 (or direct backend if LocalStack)
      await this.uploadWithRetry(async () => {
          // Check if direct upload (LocalStack hack)
          if (upload_url.includes('/direct-upload') || (urlResponse.data as any).use_direct_upload) {
             // LocalStack direct upload using XHR for progress
             const reader = new FileReader();
             const fileData = await new Promise<string>((resolve, reject) => {
                 reader.onload = () => resolve(reader.result as string);
                 reader.onerror = reject;
                 reader.readAsDataURL(file);
             });
             const base64Data = fileData.split(',')[1];
             
             // Construct JSON body manually
             const payload = JSON.stringify({
                 photo_id, s3_key, filename: file.name, file_data: base64Data
             });

             const xhr = new XMLHttpRequest();
             return new Promise<void>((resolve, reject) => {
                 xhr.upload.onprogress = (e) => {
                     if (e.lengthComputable) {
                         // Map 0-100% of upload to 0-90% of overall progress
                         const percent = Math.round((e.loaded / e.total) * 90);
                         this.updateProgress(fileId, { progress: percent });
                         this.notifyProgress(options.onProgress);
                     }
                 };
                 
                 xhr.onload = () => {
                     if (xhr.status >= 200 && xhr.status < 300) {
                         resolve();
                     } else {
                         reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                     }
                 };
                 
                 xhr.onerror = () => reject(new Error('Network error'));
                 
                 // Since api.post handles auth, we should ideally use it, but it doesn't support progress.
                 // We need to replicate auth header logic or rely on cookie (which backend uses).
                 // The backend uses cookies for auth, so credentials: include is key.
                 
                 // If URL is relative (LocalStack direct upload), prepend API base URL
                 const finalUrl = upload_url.startsWith('http') 
                    ? upload_url 
                    : `${apiBaseUrl}/${upload_url.replace(/^\//, '')}`;
                 
                 xhr.open('POST', finalUrl);
                 xhr.setRequestHeader('Content-Type', 'application/json');
                 xhr.withCredentials = true; // Important for cookies
                 xhr.send(payload);
             });
          }

          // S3 Upload
          const xhr = new XMLHttpRequest();
          return new Promise<void>((resolve, reject) => {
              xhr.upload.onprogress = (e) => {
                  if (e.lengthComputable) {
                      // Map 0-100% of upload to 0-90% of overall progress (10% for finalization)
                      const percent = Math.round((e.loaded / e.total) * 90);
                      this.updateProgress(fileId, { progress: percent });
                      this.notifyProgress(options.onProgress);
                  }
              };
              
              xhr.onload = () => {
                  if (xhr.status >= 200 && xhr.status < 300) resolve();
                  else reject(new Error(`Upload failed: ${xhr.status}`));
              };
              
              xhr.onerror = () => reject(new Error('Network error'));
              xhr.open('PUT', upload_url);
              xhr.setRequestHeader('Content-Type', file.type);
              xhr.send(file);
          });
      });

      // Confirm upload
      this.updateProgress(fileId, { status: 'processing', progress: 95 });
      this.notifyProgress(options.onProgress);
      
      const confirmRes = await photoService.confirmUpload(
          photo_id, options.galleryId, s3_key, file.name, file.size, fileHash
      );

      if (!confirmRes.success) throw new Error(confirmRes.error || 'Failed to confirm upload');
      
      return photo_id;
  }

  // Strategy 2: Large File Upload (> 10MB) - Multipart
  private async uploadLargeFile(file: File, fileId: string, options: UploadOptions): Promise<string> {
      // Calculate hash for verification
      const fileHash = await this.calculateFileHash(file);

      // Initialize multipart
      const initRes = await photoService.initializeMultipartUpload(
          options.galleryId, file.name, file.size, file.type
      );

      if (!initRes.success || !initRes.data) throw new Error(initRes.error || 'Failed to init multipart upload');
      
      const data = initRes.data as any;
      const upload_id = data.multipart_upload_id || data.upload_id;
      const photo_id = data.photo_id;
      const parts = data.upload_parts || data.parts || [];
      const s3_key = data.s3_key; // Capture s3_key from init response
      
      const totalParts = Math.ceil(file.size / this.CHUNK_SIZE);
      const uploadedParts: { PartNumber: number; ETag: string }[] = [];
      let uploadedBytes = 0;

      // Upload parts
      for (let i = 0; i < totalParts; i++) {
          const partNumber = i + 1;
          const start = i * this.CHUNK_SIZE;
          const end = Math.min(start + this.CHUNK_SIZE, file.size);
          const chunk = file.slice(start, end);
          
          const partData = (parts as any[]).find(p => (p.part_number || p.PartNumber) === partNumber);
          const uploadUrl = partData?.url || partData?.UploadUrl;
          
          if (!partData || !uploadUrl) throw new Error(`Missing URL for part ${partNumber}`);

          const etag = await this.uploadWithRetry(async () => {
              // LocalStack fix for multipart URL
              let finalUrl = uploadUrl;
              
              // 1. Handle relative URLs (prepend API base)
              if (!finalUrl.startsWith('http')) {
                  finalUrl = `${apiBaseUrl}/${finalUrl.replace(/^\//, '')}`;
              }
              
              // 2. Handle 'localstack' hostname (replace with localhost for browser)
              if (finalUrl.includes('localstack')) {
                  finalUrl = finalUrl.replace('localstack', 'localhost');
              }

              const response = await fetch(finalUrl, {
                  method: 'PUT',
                  body: chunk,
              });
              if (!response.ok) throw new Error(`Part ${partNumber} failed: ${response.status}`);
              return response.headers.get('ETag')?.replace(/"/g, ''); // Strip quotes
          });

          if (!etag) throw new Error(`No ETag for part ${partNumber}`);
          
          uploadedParts.push({ PartNumber: partNumber, ETag: etag });
          uploadedBytes += chunk.size;
          
          const percent = Math.round((uploadedBytes / file.size) * 90);
          this.updateProgress(fileId, { progress: percent });
          this.notifyProgress(options.onProgress);
      }

      // Complete multipart
      this.updateProgress(fileId, { status: 'processing', progress: 95 });
      this.notifyProgress(options.onProgress);

      const completeRes = await photoService.completeMultipartUpload(
          options.galleryId, upload_id, photo_id, uploadedParts, fileHash, s3_key
      );

      if (!completeRes.success) throw new Error(completeRes.error || 'Failed to complete multipart upload');

      return photo_id;
  }

  // Retry wrapper
  private async uploadWithRetry<T>(fn: () => Promise<T>): Promise<T> {
      let lastError: any;
      for (let attempt = 0; attempt < this.MAX_RETRIES; attempt++) {
          try {
              return await fn();
          } catch (err) {
              lastError = err;
              console.warn(`Retry attempt ${attempt + 1} failed:`, err);
              if (attempt < this.MAX_RETRIES - 1) {
                  const delay = this.RETRY_DELAY * Math.pow(2, attempt);
                  await new Promise(r => setTimeout(r, delay));
              }
          }
      }
      throw lastError;
  }

  // Update progress for a file
  private updateProgress(fileId: string, updates: Partial<UploadProgress>) {
    const current = this.uploads.get(fileId);
    if (current) {
      this.uploads.set(fileId, { ...current, ...updates });
    }
  }

  // Notify progress callback
  private notifyProgress(callback?: (progress: UploadProgress[]) => void) {
    if (callback) {
      callback(Array.from(this.uploads.values()));
    }
  }

  // Check if file is HEIC
  private isHEIC(file: File): boolean {
    const name = file.name.toLowerCase();
    const type = file.type.toLowerCase();
    return name.endsWith('.heic') || name.endsWith('.heif') || type === 'image/heic' || type === 'image/heif';
  }

  // Convert HEIC to JPEG
  private async convertHEICtoJPEG(file: File): Promise<File> {
    try {
        // Dynamic import to keep initial bundle size low
        const heic2anyModule = await import('heic2any');
        const heic2any = heic2anyModule.default;
        
        const jpegBlob = await heic2any({
            blob: file,
            toType: 'image/jpeg',
            quality: 0.95
        });
        
        // heic2any can return a single blob or array of blobs
        const blob = Array.isArray(jpegBlob) ? jpegBlob[0] : jpegBlob;
        
        return new File(
            [blob],
            file.name.replace(/\.heic$/i, '.jpg').replace(/\.heif$/i, '.jpg'),
            { 
                type: 'image/jpeg',
                lastModified: file.lastModified
            }
        );
    } catch (error) {
        console.error('HEIC conversion failed:', error);
        return file; // Return original if conversion fails
    }
  }

  // Get current upload progress
  getProgress(): UploadProgress[] {
    return Array.from(this.uploads.values());
  }

  // Clear completed uploads
  clearCompleted() {
    Array.from(this.uploads.entries()).forEach(([fileId, progress]) => {
      if (progress.status === 'completed') {
        this.uploads.delete(fileId);
      }
    });
  }

  // Cancel all uploads
  cancelAll() {
    this.uploads.clear();
    this.activeUploads = 0;
  }
}

// Export singleton instance
export const uploadManager = new UploadManager();

export default uploadManager;
