/**
 * Professional Duplicate Photo Comparison Modal
 * Modern, brand-consistent design without emojis
 * Shows existing duplicates with professional icons and styling
 */

/**
 * Show comparison of duplicate photos
 * Returns user decision: 'skip' or 'upload'
 * 
 * @param {File} newFile - The file being uploaded
 * @param {string} newFileBase64 - Base64 data (not used, kept for compatibility)
 * @param {Array} duplicates - Array of duplicate photo objects from API
 * @returns {Promise<string>} User's decision ('skip' or 'upload')
 */
function showDuplicateComparisonModal(newFile, newFileBase64, duplicates) {
    return new Promise((resolve) => {
        const isMobile = window.innerWidth <= 768;
        
        // Create modal backdrop
        const modal = document.createElement('div');
        modal.id = 'duplicateModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(16, 17, 22, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            box-sizing: border-box;
            animation: fadeIn 0.3s cubic-bezier(0.22, 1, 0.36, 1);
        `;
        
        // Build duplicate cards HTML with actual images
        const duplicateCards = duplicates.map((dup, index) => {
            const uploadDate = new Date(dup.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
            
            return `
                <div class="duplicate-card" style="
                    background: var(--background-primary, #FFFFFF);
                    border-radius: var(--border-radius-m, 16px);
                    overflow: hidden;
                    transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
                    border: 2px solid var(--border-color, rgba(0, 0, 0, 0.08));
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                " 
                onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 24px rgba(0, 0, 0, 0.12)'; this.style.borderColor='var(--color-blue, #0066CC)'" 
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)'; this.style.borderColor='var(--border-color, rgba(0, 0, 0, 0.08))'">
                    <!-- Image Preview -->
                    <div style="
                        position: relative;
                        width: 100%;
                        height: ${isMobile ? '180px' : '220px'};
                        background: linear-gradient(135deg, #F5F5F7 0%, #E8E8ED 100%);
                        overflow: hidden;
                    ">
                        <img src="${dup.url}" alt="${dup.filename}" loading="lazy" style="
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                        " onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <!-- Fallback if image fails to load -->
                        <div style="
                            display: none;
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                            align-items: center;
                            justify-content: center;
                            background: var(--neutral-100, #F5F5F7);
                        ">
                            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="8" y="12" width="32" height="24" rx="2" stroke="currentColor" stroke-width="2" fill="none" opacity="0.3"/>
                                <circle cx="18" cy="22" r="3" fill="currentColor" opacity="0.3"/>
                                <path d="M8 30L16 22L24 30L32 22L40 30" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"/>
                            </svg>
                        </div>
                        <!-- Match Badge -->
                        <div style="
                            position: absolute;
                            top: 12px;
                            right: 12px;
                            background: rgba(255, 255, 255, 0.95);
                            backdrop-filter: blur(10px);
                            padding: 6px 12px;
                            border-radius: 999px;
                            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                            border: 1px solid rgba(0, 0, 0, 0.05);
                        ">
                            <span style="
                                font-family: 'SF Pro Text', -apple-system, sans-serif;
                                font-size: 12px;
                                font-weight: 600;
                                color: var(--color-red, #FF3B30);
                                letter-spacing: 0.02em;
                                text-transform: uppercase;
                            ">Duplicate</span>
                        </div>
                    </div>
                    
                    <!-- Info Section -->
                    <div style="padding: 16px;">
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            margin-bottom: 12px;
                        ">
                            <p style="
                                font-family: 'SF Pro Text', -apple-system, sans-serif;
                                font-size: 15px;
                                font-weight: 600;
                                color: var(--text-primary, #1D1D1F);
                                margin: 0;
                                overflow: hidden;
                                text-overflow: ellipsis;
                                white-space: nowrap;
                                flex: 1;
                                padding-right: 12px;
                            ">${dup.filename}</p>
                        </div>
                        
                        <div style="
                            display: flex;
                            gap: 8px;
                            flex-wrap: wrap;
                        ">
                            <!-- File Size -->
                            <div style="
                                display: inline-flex;
                                align-items: center;
                                gap: 6px;
                                padding: 6px 10px;
                                background: var(--neutral-100, #F5F5F7);
                                border-radius: 8px;
                            ">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M7 1V13M13 7H1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
                                    <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
                                </svg>
                                <span style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 12px;
                                    font-weight: 500;
                                    color: var(--text-secondary, #86868B);
                                ">${(dup.file_size / 1024 / 1024).toFixed(2)} MB</span>
                            </div>
                            
                            <!-- Upload Date -->
                            <div style="
                                display: inline-flex;
                                align-items: center;
                                gap: 6px;
                                padding: 6px 10px;
                                background: var(--neutral-100, #F5F5F7);
                                border-radius: 8px;
                            ">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
                                    <path d="M7 4V7L9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
                                </svg>
                                <span style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 12px;
                                    font-weight: 500;
                                    color: var(--text-secondary, #86868B);
                                ">${uploadDate}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        modal.innerHTML = `
            <div style="
                background: var(--background-secondary, #FFFFFF);
                border-radius: var(--border-radius-xl, 24px);
                max-width: ${isMobile ? '100%' : '900px'};
                width: 100%;
                max-height: calc(100vh - 40px);
                overflow: hidden;
                box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 0, 0, 0.05);
                animation: slideUp 0.4s cubic-bezier(0.22, 1, 0.36, 1);
            ">
                <!-- Header -->
                <div style="
                    padding: ${isMobile ? '24px 20px' : '32px 32px 24px 32px'};
                    border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
                    background: linear-gradient(180deg, var(--background-secondary, #FFFFFF) 0%, var(--neutral-50, #FAFAFA) 100%);
                ">
                    <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
                        <div style="flex: 1;">
                            <div style="
                                display: inline-flex;
                                align-items: center;
                                gap: 8px;
                                padding: 8px 16px;
                                background: linear-gradient(135deg, rgba(255, 59, 48, 0.08) 0%, rgba(255, 149, 0, 0.08) 100%);
                                border-radius: 999px;
                                margin-bottom: 16px;
                            ">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="8" cy="8" r="7" stroke="#FF3B30" stroke-width="1.5"/>
                                    <path d="M8 4V9" stroke="#FF3B30" stroke-width="1.5" stroke-linecap="round"/>
                                    <circle cx="8" cy="11.5" r="0.75" fill="#FF3B30"/>
                                </svg>
                                <span style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 13px;
                                    font-weight: 600;
                                    color: var(--color-red, #FF3B30);
                                    letter-spacing: 0.01em;
                                ">Duplicate Detection</span>
                            </div>
                            
                            <h2 style="
                                margin: 0 0 8px 0;
                                font-family: 'SF Pro Display', -apple-system, sans-serif;
                                font-size: ${isMobile ? '24px' : '32px'};
                                font-weight: 700;
                                color: var(--text-primary, #1D1D1F);
                                letter-spacing: -0.03em;
                                line-height: 1.1;
                            ">This file already exists</h2>
                            
                            <p style="
                                margin: 0;
                                font-family: 'SF Pro Text', -apple-system, sans-serif;
                                font-size: ${isMobile ? '14px' : '16px'};
                                color: var(--text-secondary, #86868B);
                                line-height: 1.5;
                            ">We found <strong style="color: var(--text-primary)">${duplicates.length}</strong> ${duplicates.length === 1 ? 'photo' : 'photos'} with the same name and file size in your gallery.</p>
                        </div>
                        
                        <!-- Close Button -->
                        <button onclick="document.getElementById('duplicateModal').querySelector('#skipUploadBtn').click()" style="
                            width: 32px;
                            height: 32px;
                            border-radius: 50%;
                            background: var(--neutral-100, #F5F5F7);
                            border: none;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            transition: all 0.2s ease;
                            flex-shrink: 0;
                        " onmouseover="this.style.background='var(--neutral-200, #E8E8ED)'; this.style.transform='rotate(90deg)'" onmouseout="this.style.background='var(--neutral-100, #F5F5F7)'; this.style.transform='rotate(0deg)'">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <!-- Content -->
                <div style="
                    padding: ${isMobile ? '20px' : '32px'};
                    max-height: ${isMobile ? 'calc(100vh - 320px)' : '500px'};
                    overflow-y: auto;
                ">
                    <!-- New File Info -->
                    <div style="
                        background: linear-gradient(135deg, rgba(0, 102, 204, 0.05) 0%, rgba(58, 137, 230, 0.05) 100%);
                        border: 2px solid var(--color-blue, #0066CC);
                        border-radius: var(--border-radius-m, 16px);
                        padding: ${isMobile ? '16px' : '20px'};
                        margin-bottom: 24px;
                    ">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                background: var(--color-blue, #0066CC);
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                flex-shrink: 0;
                            ">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M10 4V16M16 10H4" stroke="white" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                            </div>
                            <div style="flex: 1; min-width: 0;">
                                <p style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 13px;
                                    font-weight: 600;
                                    color: var(--color-blue, #0066CC);
                                    margin: 0 0 4px 0;
                                    text-transform: uppercase;
                                    letter-spacing: 0.05em;
                                ">File You're Uploading</p>
                                <p style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 16px;
                                    font-weight: 600;
                                    color: var(--text-primary, #1D1D1F);
                                    margin: 0;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                    white-space: nowrap;
                                ">${newFile.name}</p>
                            </div>
                        </div>
                        <div style="
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                            padding: 8px 14px;
                            background: rgba(255, 255, 255, 0.8);
                            backdrop-filter: blur(10px);
                            border-radius: 999px;
                        ">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M7 1V13M13 7H1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
                                <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
                            </svg>
                            <span style="
                                font-family: 'SF Mono', Monaco, monospace;
                                font-size: 13px;
                                font-weight: 600;
                                color: var(--text-primary, #1D1D1F);
                            ">${(newFile.size / 1024 / 1024).toFixed(2)} MB</span>
                        </div>
                    </div>
                    
                    <!-- Existing Photos -->
                    <div style="margin-bottom: 8px;">
                        <h3 style="
                            font-family: 'SF Pro Text', -apple-system, sans-serif;
                            font-size: 15px;
                            font-weight: 600;
                            color: var(--text-secondary, #86868B);
                            margin: 0 0 16px 0;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        ">Existing ${duplicates.length === 1 ? 'Photo' : 'Photos'} in Gallery</h3>
                    </div>
                    
                    <div style="
                        display: grid;
                        grid-template-columns: ${isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))'};
                        gap: 16px;
                    ">
                        ${duplicateCards}
                    </div>
                </div>
                
                <!-- Actions -->
                <div style="
                    padding: ${isMobile ? '20px' : '24px 32px'};
                    border-top: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
                    background: var(--neutral-50, #FAFAFA);
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    ${isMobile ? 'flex-direction: column;' : 'justify-content: flex-end;'}
                ">
                    <button id="skipUploadBtn" style="
                        ${isMobile ? 'width: 100%;' : ''}
                        padding: 14px 28px;
                        background: var(--background-secondary, white);
                        color: var(--text-primary, #1D1D1F);
                        border: 1.5px solid var(--border-color, rgba(0, 0, 0, 0.12));
                        border-radius: var(--border-radius-m, 14px);
                        cursor: pointer;
                        font-family: 'SF Pro Text', -apple-system, sans-serif;
                        font-weight: 600;
                        font-size: 16px;
                        transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
                        ${isMobile ? 'order: 2;' : ''}
                    " onmouseover="this.style.background='var(--neutral-100, #F5F5F7)'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.08)'" onmouseout="this.style.background='var(--background-secondary, white)'; this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        Skip Upload
                    </button>
                    <button id="uploadAnywayBtn" style="
                        ${isMobile ? 'width: 100%;' : ''}
                        padding: 14px 32px;
                        background: var(--color-blue, #0066CC);
                        color: white;
                        border: none;
                        border-radius: var(--border-radius-m, 14px);
                        cursor: pointer;
                        font-family: 'SF Pro Text', -apple-system, sans-serif;
                        font-weight: 600;
                        font-size: 16px;
                        transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
                        box-shadow: 0 4px 16px rgba(0, 102, 204, 0.3);
                        ${isMobile ? 'order: 1;' : ''}
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 102, 204, 0.4)'; this.style.background='#0077ED'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 16px rgba(0, 102, 204, 0.3)'; this.style.background='var(--color-blue, #0066CC)'">
                        Upload Anyway
                    </button>
                </div>
            </div>
        `;
        
        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from { 
                    opacity: 0;
                    transform: translateY(30px) scale(0.95);
                }
                to { 
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            #duplicateModal > div > div:nth-child(2)::-webkit-scrollbar {
                width: 8px;
            }
            #duplicateModal > div > div:nth-child(2)::-webkit-scrollbar-track {
                background: transparent;
            }
            #duplicateModal > div > div:nth-child(2)::-webkit-scrollbar-thumb {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
            }
            #duplicateModal > div > div:nth-child(2)::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 0, 0, 0.25);
            }
        `;
        document.head.appendChild(style);
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        document.body.appendChild(modal);
        
        // Handle button clicks
        document.getElementById('skipUploadBtn').onclick = () => {
            modal.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
                if (document.head.contains(style)) {
                    document.head.removeChild(style);
                }
                document.body.style.overflow = '';
                resolve('skip');
            }, 200);
        };
        
        document.getElementById('uploadAnywayBtn').onclick = () => {
            modal.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => {
                if (document.body.contains(modal)) {
                    document.body.removeChild(modal);
                }
                if (document.head.contains(style)) {
                    document.head.removeChild(style);
                }
                document.body.style.overflow = '';
                resolve('upload');
            }, 200);
        };
        
        // Close on background click (default to skip)
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.getElementById('skipUploadBtn').click();
            }
        });
        
        // Keyboard support
        const handleKeyPress = (e) => {
            if (e.key === 'Escape') {
                document.getElementById('skipUploadBtn').click();
                document.removeEventListener('keydown', handleKeyPress);
            } else if (e.key === 'Enter') {
                document.getElementById('uploadAnywayBtn').click();
                document.removeEventListener('keydown', handleKeyPress);
            }
        };
        document.addEventListener('keydown', handleKeyPress);
        
        // Add fadeOut animation
        const fadeOutStyle = document.createElement('style');
        fadeOutStyle.textContent = `
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        `;
        document.head.appendChild(fadeOutStyle);
    });
}

// Export for use in other scripts
window.showDuplicateComparisonModal = showDuplicateComparisonModal;
