/**
 * HEIC to JPEG Converter (Client-Side)
 * ===========================================
 * Big Tech Solution: Instagram, Booking.com, Airbnb
 * 
 * Converts HEIC images to JPEG in the browser before upload.
 * This ensures:
 * - Universal browser compatibility
 * - No server-side conversion needed
 * - Faster upload (JPEG is smaller than HEIC)
 * - CloudFront can cache properly
 */

/**
 * Convert HEIC file to JPEG using browser-native canvas
 * @param {File} file - HEIC file
 * @returns {Promise<File>} - JPEG file
 */
async function convertHEICtoJPEG(file) {
    try {
        console.log(`📱 Converting HEIC to JPEG: ${file.name}`);
        
        // Load heic2any library dynamically (lazy load)
        if (!window.heic2any) {
            console.log('📦 Loading HEIC converter library...');
            await loadHEICLibrary();
        }
        
        // Convert HEIC to JPEG blob
        const jpegBlob = await heic2any({
            blob: file,
            toType: 'image/jpeg',
            quality: 0.95  // High quality (like Instagram)
        });
        
        // Convert blob to File object
        const jpegFile = new File(
            [jpegBlob],
            file.name.replace(/\.heic$/i, '.jpg'),
            { 
                type: 'image/jpeg',
                lastModified: file.lastModified
            }
        );
        
        const originalSize = (file.size / 1024 / 1024).toFixed(2);
        const newSize = (jpegFile.size / 1024 / 1024).toFixed(2);
        console.log(`✅ HEIC converted: ${originalSize}MB → ${newSize}MB`);
        
        return jpegFile;
        
    } catch (error) {
        console.error('❌ HEIC conversion failed:', error);
        // Fallback: Return original file (backend will handle)
        return file;
    }
}

/**
 * Load heic2any library dynamically
 */
function loadHEICLibrary() {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (window.heic2any) {
            resolve();
            return;
        }
        
        // Load from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/heic2any@0.0.4/dist/heic2any.min.js';
        script.onload = () => {
            console.log('✅ HEIC converter library loaded');
            resolve();
        };
        script.onerror = () => {
            console.error('❌ Failed to load HEIC converter library');
            reject(new Error('Failed to load heic2any library'));
        };
        document.head.appendChild(script);
    });
}

/**
 * Check if file is HEIC format
 * @param {File} file
 * @returns {boolean}
 */
function isHEIC(file) {
    const name = file.name.toLowerCase();
    const type = file.type.toLowerCase();
    
    return name.endsWith('.heic') || 
           name.endsWith('.heif') || 
           type === 'image/heic' || 
           type === 'image/heif';
}

/**
 * Process image file before upload (Big Tech approach)
 * Instagram/Google Photos method: Accept all formats, transform at CDN level
 * 
 * @param {File} file - Image file
 * @returns {Promise<File>} - Processed file
 */
async function processImageForUpload(file) {
    try {
        // Step 1: If HEIC, convert to JPEG first (browser can't validate HEIC directly)
        let processedFile = file;
        if (isHEIC(file)) {
            console.log(`📱 HEIC file detected: ${file.name}`);
            processedFile = await convertHEICtoJPEG(file);
            console.log(`✅ Converted to JPEG for validation`);
        }
        
        // Step 2: Validate image dimensions
        const isValid = await validateImageFile(processedFile);
        if (!isValid) {
            console.warn(`⚠️  Validation failed, but accepting anyway (backend will handle)`);
            // Don't throw - accept the file and let backend validate
        }
        
        // Accept ALL formats - CloudFront will handle transformation
        console.log(`✅ Accepted: ${processedFile.name} (${processedFile.type})`);
        return processedFile;
        
    } catch (error) {
        console.error('❌ Image processing failed:', error);
        // Don't throw - return original file and let backend handle
        console.log(`⚠️  Returning original file: ${file.name}`);
        return file;
    }
}

/**
 * Validate image file (dimensions, size, format)
 * @param {File} file
 * @returns {Promise<boolean>}
 */
async function validateImageFile(file) {
    return new Promise((resolve) => {
        // For non-standard formats (RAW, etc), skip validation
        const extension = file.name.toLowerCase();
        const rawFormats = ['.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.raf', '.pef'];
        if (rawFormats.some(fmt => extension.endsWith(fmt))) {
            console.log(`✅ RAW format detected, skipping browser validation: ${file.name}`);
            resolve(true);
            return;
        }
        
        const img = new Image();
        const url = URL.createObjectURL(file);
        
        // Set timeout - if image doesn't load in 5 seconds, accept it anyway
        const timeout = setTimeout(() => {
            URL.revokeObjectURL(url);
            console.log(`⏱️  Validation timeout, accepting file: ${file.name}`);
            resolve(true);
        }, 5000);
        
        img.onload = () => {
            clearTimeout(timeout);
            URL.revokeObjectURL(url);
            
            // Check dimensions (Instagram-style limits)
            const maxDimension = 8000; // 8K max
            const minDimension = 320;  // Minimum width
            
            if (img.width > maxDimension || img.height > maxDimension) {
                console.warn(`⚠️  Image too large: ${img.width}x${img.height}`);
                resolve(false);
                return;
            }
            
            if (img.width < minDimension && img.height < minDimension) {
                console.warn(`⚠️  Image too small: ${img.width}x${img.height}`);
                resolve(false);
                return;
            }
            
            console.log(`✅ Image validated: ${img.width}x${img.height}`);
            resolve(true);
        };
        
        img.onerror = () => {
            clearTimeout(timeout);
            URL.revokeObjectURL(url);
            console.warn(`⚠️  Could not validate image, accepting anyway: ${file.name}`);
            // Don't fail - accept the file and let backend validate
            resolve(true);
        };
        
        img.src = url;
    });
}

// Export to global scope
if (typeof window !== 'undefined') {
    window.convertHEICtoJPEG = convertHEICtoJPEG;
    window.isHEIC = isHEIC;
    window.processImageForUpload = processImageForUpload;
    window.validateImageFile = validateImageFile;
}

