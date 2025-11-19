/**
 * Analytics and Insights
 */

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
    
    if (totalViewsEl) {
        totalViewsEl.textContent = analytics.total_views || 0;
    }
    
    if (totalPhotoViewsEl) {
        totalPhotoViewsEl.textContent = analytics.total_photo_views || 0;
    }
    
    if (totalDownloadsEl) {
        totalDownloadsEl.textContent = analytics.total_downloads || 0;
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
    
    const labels = ['Gallery Views', 'Photo Views', 'Downloads'];
    const data = [
        analytics.total_views || 0,
        analytics.total_photo_views || 0,
        analytics.total_downloads || 0
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
                    'rgba(0, 136, 255, 0.8)'
                ],
                borderColor: [
                    'rgba(0, 102, 204, 1)',
                    'rgba(0, 119, 255, 1)',
                    'rgba(0, 136, 255, 1)'
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
    if (!window.isAuthenticated || !window.isAuthenticated()) {
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
window.trackGalleryShare = trackGalleryShare;
window.trackPhotoShare = trackPhotoShare;
window.displayOverallAnalytics = displayOverallAnalytics;



