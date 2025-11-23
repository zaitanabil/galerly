/**
 * Analytics and Insights
 */

// Version check for cache-busting
console.log('📊 analytics.js v2.2 loaded - Enhanced tracking debugging');

let activityChart = null;

// Load overall analytics
async function loadOverallAnalytics() {
    try {
        const data = await window.apiRequest('analytics');
        return data;
    } catch (error) {
        console.error('Error loading analytics:', error);
        throw error;
    }
}

// Load gallery analytics
async function loadGalleryAnalytics(galleryId) {
    try {
        const data = await window.apiRequest(`analytics/galleries/${galleryId}`);
        return data;
    } catch (error) {
        console.error('Error loading gallery analytics:', error);
        throw error;
    }
}

// Track gallery view
async function trackGalleryView(galleryId, metadata = {}) {
    try {
        await window.apiRequest(`analytics/track/gallery/${galleryId}`, {
            method: 'POST',
            body: JSON.stringify({ metadata })
        });
    } catch (error) {
        console.error('Error tracking gallery view:', error);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Track photo view
async function trackPhotoView(photoId, galleryId, metadata = {}) {
    try {
        await window.apiRequest(`analytics/track/photo/${photoId}`, {
            method: 'POST',
            body: JSON.stringify({ gallery_id: galleryId, metadata })
        });
    } catch (error) {
        console.error('Error tracking photo view:', error);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Track photo download
async function trackPhotoDownload(photoId, galleryId, metadata = {}) {
    try {
        await window.apiRequest(`analytics/track/download/${photoId}`, {
            method: 'POST',
            body: JSON.stringify({ gallery_id: galleryId, metadata })
        });
    } catch (error) {
        console.error('Error tracking photo download:', error);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Track bulk download
async function trackBulkDownload(galleryId, metadata = {}) {
    console.log('🎯 trackBulkDownload called with:', { galleryId, metadata });
    try {
        const url = `analytics/track/bulk-download/${galleryId}`;
        console.log('🎯 Making request to:', url);
        console.log('🎯 window.apiRequest available?', typeof window.apiRequest);
        
        const result = await window.apiRequest(url, {
            method: 'POST',
            body: JSON.stringify({ metadata })
        });
        
        console.log('🎯 trackBulkDownload result:', result);
        return result;
    } catch (error) {
        console.error('❌ trackBulkDownload error:', error);
        console.error('❌ Error message:', error.message);
        console.error('❌ Error stack:', error.stack);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Track gallery share
async function trackGalleryShare(galleryId, platform, metadata = {}) {
    try {
        await window.apiRequest(`analytics/track/share/gallery/${galleryId}`, {
            method: 'POST',
            body: JSON.stringify({ platform, metadata })
        });
    } catch (error) {
        console.error('Error tracking gallery share:', error);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Track photo share
async function trackPhotoShare(photoId, platform, metadata = {}) {
    try {
        await window.apiRequest(`analytics/track/share/photo/${photoId}`, {
            method: 'POST',
            body: JSON.stringify({ platform, metadata })
        });
    } catch (error) {
        console.error('Error tracking photo share:', error);
        // Don't throw - tracking failures shouldn't break the app
    }
}

// Display overall analytics
function displayOverallAnalytics(analytics) {
    // Update metric cards
    const totalViewsEl = document.getElementById('total-views');
    const totalPhotoViewsEl = document.getElementById('total-photo-views');
    const totalDownloadsEl = document.getElementById('total-downloads');
    const totalBulkDownloadsEl = document.getElementById('total-bulk-downloads');
    
    if (totalViewsEl) {
        totalViewsEl.textContent = analytics.total_views || 0;
    }
    
    if (totalPhotoViewsEl) {
        totalPhotoViewsEl.textContent = analytics.total_photo_views || 0;
    }
    
    if (totalDownloadsEl) {
        totalDownloadsEl.textContent = analytics.total_downloads || 0;
    }
    
    if (totalBulkDownloadsEl) {
        totalBulkDownloadsEl.textContent = analytics.total_bulk_downloads || 0;
    }
    
    // Display top galleries
    displayTopGalleries(analytics.gallery_stats || []);
    
    // Create activity chart if we have daily stats
    // Note: We'll need to aggregate daily stats from gallery_stats
    // For now, we'll create a simple chart with overall metrics
    createActivityChart(analytics);
}

// Display top galleries
function displayTopGalleries(galleryStats) {
    const container = document.getElementById('top-galleries-container');
    if (!container) return;
    
    if (galleryStats.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;"><p style="font-size: 18px; margin-bottom: 12px;">No gallery analytics available yet</p><p style="font-size: 14px;">Create and share galleries to see analytics.</p></div>';
        return;
    }
    
    let html = '';
    
    galleryStats.forEach((gallery, index) => {
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7">
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
                            <div>
                                <h3 class="grid-15 animation-7" style="margin: 0 0 8px 0;">
                                    ${index + 1}. ${gallery.gallery_name || 'Unnamed Gallery'}
                                </h3>
                                <p style="opacity: 0.7; font-size: 14px; margin: 0;">${gallery.views || 0} total views</p>
                            </div>
                        </div>
                        <div class="input-15 background-7">
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 32px; margin-top: 16px;">
                                <div>
                                    <div style="display: flex; align-items: baseline; margin-bottom: 8px;">
                                        <span style="font-size: 36px; font-weight: 800; line-height: 1;">${gallery.views || 0}</span>
                                    </div>
                                    <p style="opacity: 0.7; font-size: 14px; margin: 0;">Gallery Views</p>
                                </div>
                                <div>
                                    <div style="display: flex; align-items: baseline; margin-bottom: 8px;">
                                        <span style="font-size: 36px; font-weight: 800; line-height: 1;">${gallery.photo_views || 0}</span>
                                    </div>
                                    <p style="opacity: 0.7; font-size: 14px; margin: 0;">Photo Views</p>
                                </div>
                                <div>
                                    <div style="display: flex; align-items: baseline; margin-bottom: 8px;">
                                        <span style="font-size: 36px; font-weight: 800; line-height: 1;">${gallery.downloads || 0}</span>
                                    </div>
                                    <p style="opacity: 0.7; font-size: 14px; margin: 0;">Downloads</p>
                                </div>
                                <div>
                                    <div style="display: flex; align-items: baseline; margin-bottom: 8px;">
                                        <span style="font-size: 36px; font-weight: 800; line-height: 1;">${gallery.bulk_downloads || 0}</span>
                                    </div>
                                    <p style="opacity: 0.7; font-size: 14px; margin: 0;">Bulk Downloads</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Create activity chart
function createActivityChart(analytics) {
    const canvas = document.getElementById('activity-chart');
    if (!canvas) return;
    
    // Destroy existing chart if it exists
    if (activityChart) {
        activityChart.destroy();
    }
    
    // For now, create a simple bar chart with overall metrics
    // In the future, we can add daily_stats from individual galleries
    const ctx = canvas.getContext('2d');
    
    const labels = ['Gallery Views', 'Photo Views', 'Downloads', 'Bulk Downloads'];
    const data = [
        analytics.total_views || 0,
        analytics.total_photo_views || 0,
        analytics.total_downloads || 0,
        analytics.total_bulk_downloads || 0
    ];
    
    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Activity (Last 30 Days)',
                data: data,
                backgroundColor: [
                    'rgba(0, 102, 204, 0.8)',
                    'rgba(0, 119, 255, 0.8)',
                    'rgba(0, 136, 255, 0.8)',
                    'rgba(0, 153, 255, 0.8)'
                ],
                borderColor: [
                    'rgba(0, 102, 204, 1)',
                    'rgba(0, 119, 255, 1)',
                    'rgba(0, 136, 255, 1)',
                    'rgba(0, 153, 255, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 60,
                maxBarThickness: 80
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 30,
                    bottom: 30,
                    left: 20,
                    right: 20
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 13,
                            weight: '500'
                        },
                        color: 'rgba(0, 0, 0, 0.7)',
                        padding: 10
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.08)',
                        drawBorder: false,
                        lineWidth: 1
                    },
                    border: {
                        display: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 13,
                            weight: '500'
                        },
                        color: 'rgba(0, 0, 0, 0.7)',
                        padding: 12
                    },
                    grid: {
                        display: false
                    },
                    border: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    padding: 14,
                    titleFont: {
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13
                    },
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + ' ' + context.label.toLowerCase();
                        }
                    }
                }
            }
        }
    });
}

// Initialize analytics in dashboard
async function initDashboardAnalytics() {
    // Verify authentication with backend (HttpOnly cookie)
    const isAuth = window.isAuthenticated ? await window.isAuthenticated() : false;
    if (!isAuth) {
        return;
    }
    
    // Wait for galleries to load first (gallery-loader.js loads them)
    // Check if loadDashboardData exists and wait for it
    let retries = 0;
    const maxRetries = 10;
    while (retries < maxRetries && typeof window.loadDashboardData === 'undefined') {
        await new Promise(resolve => setTimeout(resolve, 200));
        retries++;
    }
    
    // Additional delay to ensure galleries are loaded
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
        const analytics = await loadOverallAnalytics();
        displayOverallAnalytics(analytics);
    } catch (error) {
        console.error('Error loading analytics:', error);
        // Don't show error - analytics are optional
        const container = document.getElementById('top-galleries-container');
        if (container) {
            container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;"><p style="font-size: 18px; margin-bottom: 12px;">No analytics data available yet</p><p style="font-size: 14px;">Create and share galleries to see analytics.</p></div>';
        }
    }
}

// Initialize on page load - only for dashboard page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.location.pathname.includes('dashboard')) {
            // Wait a bit for other scripts to load
            setTimeout(initDashboardAnalytics, 500);
        }
    });
} else {
    if (window.location.pathname.includes('dashboard')) {
        setTimeout(initDashboardAnalytics, 500);
    }
}

// Export functions for global use
window.loadOverallAnalytics = loadOverallAnalytics;
window.loadGalleryAnalytics = loadGalleryAnalytics;
window.trackGalleryView = trackGalleryView;
window.trackPhotoView = trackPhotoView;
window.trackPhotoDownload = trackPhotoDownload;
window.trackBulkDownload = trackBulkDownload;
window.trackGalleryShare = trackGalleryShare;
window.trackPhotoShare = trackPhotoShare;
window.displayOverallAnalytics = displayOverallAnalytics;


// Bulk download modal functionality
async function openBulkDownloadModal() {
    const modal = document.getElementById('bulkDownloadModal');
    const body = document.body;
    
    // Show modal with animation
    modal.style.display = 'flex';
    body.style.overflow = 'hidden'; // Prevent background scrolling
    
    // Load logs
    await loadBulkDownloadLogs();
}

function closeBulkDownloadModal() {
    const modal = document.getElementById('bulkDownloadModal');
    const body = document.body;
    
    modal.style.display = 'none';
    body.style.overflow = ''; // Restore scrolling
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeBulkDownloadModal();
    }
});

async function loadBulkDownloadLogs() {
    const modalBody = document.getElementById('bulkDownloadModalBody');
    
    try {
        modalBody.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <div style="
                    width: 60px;
                    height: 60px;
                    margin: 0 auto 24px;
                    border-radius: 50%;
                    background: rgba(0, 102, 204, 0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    animation: pulse 2s infinite;
                ">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0066CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </div>
                <p style="
                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                    font-size: 16px;
                    color: #86868B;
                    margin: 0;
                ">Loading download history...</p>
            </div>
        `;
        
        // Fetch bulk download events from analytics
        const response = await window.apiRequest('analytics/bulk-downloads');
        
        if (!response || !response.events || response.events.length === 0) {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 80px 40px;">
                    <div style="
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 24px;
                        border-radius: 50%;
                        background: rgba(0, 0, 0, 0.03);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#86868B" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </div>
                    <h3 style="
                        font-family: 'SF Pro Display', -apple-system, sans-serif;
                        font-size: 24px;
                        font-weight: 300;
                        color: #1D1D1F;
                        margin: 0 0 12px 0;
                        letter-spacing: -0.3px;
                    ">No Downloads Yet</h3>
                    <p style="
                        font-family: 'SF Pro Text', -apple-system, sans-serif;
                        font-size: 16px;
                        color: #86868B;
                        margin: 0;
                        line-height: 1.5;
                    ">Download history will appear here when someone<br>downloads all photos from your galleries</p>
                </div>
            `;
            return;
        }
        
        // Display logs with simple, clean cards
        let html = '';
        
        // Simple statistics summary
        if (response.statistics) {
            const stats = response.statistics;
            html += `
                <div style="
                    display: flex;
                    gap: 32px;
                    padding: 24px 0;
                    margin-bottom: 32px;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
                ">
                    <div>
                        <p style="
                            font-family: 'SF Pro Display', -apple-system, sans-serif;
                            font-size: 32px;
                            font-weight: 300;
                            color: #1D1D1F;
                            margin: 0 0 4px 0;
                            line-height: 1;
                        ">${stats.total_downloads}</p>
                        <p style="
                            font-family: 'SF Pro Text', -apple-system, sans-serif;
                            font-size: 14px;
                            color: #86868B;
                            margin: 0;
                        ">Downloads</p>
                    </div>
                    <div>
                        <p style="
                            font-family: 'SF Pro Display', -apple-system, sans-serif;
                            font-size: 32px;
                            font-weight: 300;
                            color: #1D1D1F;
                            margin: 0 0 4px 0;
                            line-height: 1;
                        ">${stats.unique_visitors}</p>
                        <p style="
                            font-family: 'SF Pro Text', -apple-system, sans-serif;
                            font-size: 14px;
                            color: #86868B;
                            margin: 0;
                        ">Unique visitors</p>
                    </div>
                </div>
            `;
        }
        
        // Group events by visitor
        const visitorGroups = {};
        response.events.forEach(event => {
            const visitorId = event.visitor_id || 'unknown';
            if (!visitorGroups[visitorId]) {
                visitorGroups[visitorId] = [];
            }
            visitorGroups[visitorId].push(event);
        });
        
        // Display one entry per unique visitor (showing most recent download)
        Object.values(visitorGroups).forEach(events => {
            // Take the most recent event (first in array since sorted by newest)
            const event = events[0];
            const date = new Date(event.timestamp);
            const timeAgo = getTimeAgo(event.timestamp);
            const metadata = event.metadata || {};
            
            const downloaderName = metadata.downloader_name || 'Unknown';
            const downloaderType = metadata.downloader_type || 'viewer';
            const isOwner = metadata.is_owner_download || false;
            const photoCount = metadata.photo_count || 0;
            const galleryName = event.gallery_name || 'Unknown Gallery';
            const downloadCount = event.visitor_download_count || 1;
            const isRepeatVisitor = downloadCount > 1;
            
            html += `
                <div style="
                    padding: 20px 0;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.04);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                <p style="
                                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                                    font-size: 16px;
                                    font-weight: 500;
                                    color: #1D1D1F;
                                    margin: 0;
                                ">${escapeHtml(downloaderName)}</p>
                                ${isOwner ? `<span style="
                                    font-size: 10px;
                                    color: #0066CC;
                                    font-weight: 600;
                                    letter-spacing: 0.3px;
                                ">YOU</span>` : ''}
                            </div>
                            <p style="
                                font-family: 'SF Pro Text', -apple-system, sans-serif;
                                font-size: 14px;
                                color: #86868B;
                                margin: 0;
                            ">${escapeHtml(galleryName)} • ${isRepeatVisitor ? `${downloadCount} downloads` : `${photoCount} photos`}</p>
                        </div>
                        <p style="
                            font-family: 'SF Pro Text', -apple-system, sans-serif;
                            font-size: 13px;
                            color: #86868B;
                            margin: 0;
                            flex-shrink: 0;
                        ">${timeAgo}</p>
                    </div>
                </div>
            `;
        });
        
        modalBody.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading bulk download logs:', error);
        modalBody.innerHTML = `
            <div style="text-align: center; padding: 60px 40px;">
                <div style="
                    width: 60px;
                    height: 60px;
                    margin: 0 auto 24px;
                    border-radius: 50%;
                    background: rgba(239, 68, 68, 0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="15" y1="9" x2="9" y2="15"></line>
                        <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                </div>
                <p style="
                    font-family: 'SF Pro Text', -apple-system, sans-serif;
                    font-size: 16px;
                    color: #ef4444;
                    margin: 0;
                ">Failed to load download history</p>
            </div>
        `;
    }
}

// Export modal functions
window.openBulkDownloadModal = openBulkDownloadModal;
window.closeBulkDownloadModal = closeBulkDownloadModal;



