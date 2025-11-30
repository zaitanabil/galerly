// Image utility functions - handles image processing and optimization
import { config, getImageUrl as getImageUrlFromConfig } from '../config/env';

// Re-export getImageUrl for convenience
export { getImageUrl } from '../config/env';

// Image size variations
export enum ImageSize {
  THUMBNAIL = 'thumbnail',
  MEDIUM = 'medium',
  LARGE = 'large',
  ORIGINAL = 'original',
}

// Get image URL with specific size
export function getImageUrlWithSize(photo: { 
  thumbnail_url?: string; 
  medium_url?: string; 
  url: string;
}, size: ImageSize = ImageSize.MEDIUM): string {
  switch (size) {
    case ImageSize.THUMBNAIL:
      return getImageUrlFromConfig(photo.thumbnail_url || photo.url);
    case ImageSize.MEDIUM:
      return getImageUrlFromConfig(photo.medium_url || photo.url);
    case ImageSize.LARGE:
    case ImageSize.ORIGINAL:
      return getImageUrlFromConfig(photo.url);
    default:
      return getImageUrlFromConfig(photo.url);
  }
}

// Validate image file
export function validateImageFile(file: File): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Check file type
  if (!config.allowedImageTypes.includes(file.type)) {
    errors.push(`${file.name} is not a valid image type. Supported types: JPEG, PNG, GIF, WebP, TIFF, HEIC`);
  }
  
  // Check file size (if max size is set)
  const maxSize = 100 * 1024 * 1024; // 100MB default
  if (file.size > maxSize) {
    errors.push(`${file.name} is too large. Maximum size: ${formatFileSize(maxSize)}`);
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

// Validate multiple image files
export function validateImageFiles(files: File[]): { valid: boolean; errors: string[]; validFiles: File[] } {
  const allErrors: string[] = [];
  const validFiles: File[] = [];
  
  files.forEach(file => {
    const { valid, errors } = validateImageFile(file);
    if (valid) {
      validFiles.push(file);
    } else {
      allErrors.push(...errors);
    }
  });
  
  return {
    valid: validFiles.length > 0,
    errors: allErrors,
    validFiles,
  };
}

// Format file size for display
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Calculate image hash (for duplicate detection)
export async function calculateImageHash(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        const arrayBuffer = e.target?.result as ArrayBuffer;
        const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        resolve(hashHex);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsArrayBuffer(file);
  });
}

// Preload image
export function preloadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = url;
  });
}

// Get image dimensions
export function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve({ width: img.width, height: img.height });
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };
    
    img.src = url;
  });
}

// Create thumbnail from file
export function createThumbnail(
  file: File,
  maxWidth: number = 300,
  maxHeight: number = 300,
  quality: number = 0.8
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    
    img.onload = () => {
      URL.revokeObjectURL(url);
      
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Failed to get canvas context'));
        return;
      }
      
      let width = img.width;
      let height = img.height;
      
      // Calculate new dimensions
      if (width > height) {
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
      } else {
        if (height > maxHeight) {
          width = (width * maxHeight) / height;
          height = maxHeight;
        }
      }
      
      canvas.width = width;
      canvas.height = height;
      
      ctx.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create thumbnail'));
          }
        },
        'image/jpeg',
        quality
      );
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };
    
    img.src = url;
  });
}

// Convert HEIC to JPEG (placeholder - requires heic2any library)
export async function convertHeicToJpeg(file: File): Promise<File> {
  // Check if file is HEIC
  if (!file.type.includes('heic') && !file.name.toLowerCase().endsWith('.heic')) {
    return file;
  }
  
  try {
    // Import heic2any dynamically if needed
    const heic2anyModule = await import('heic2any');
    const heic2any = heic2anyModule.default;
    const convertedBlob = await heic2any({
      blob: file,
      toType: 'image/jpeg',
      quality: 0.9,
    });
    
    const blob = Array.isArray(convertedBlob) ? convertedBlob[0] : convertedBlob;
    return new File([blob], file.name.replace(/\.heic$/i, '.jpg'), {
      type: 'image/jpeg',
    });
  } catch (error) {
    console.warn('HEIC conversion not available or failed, using original file:', error);
    return file;
  }
}

export default {
  getImageUrlWithSize,
  validateImageFile,
  validateImageFiles,
  formatFileSize,
  calculateImageHash,
  preloadImage,
  getImageDimensions,
  createThumbnail,
  convertHeicToJpeg,
};

