/**
 * Gallery Expiration Handler
 * Shows expiration status and warnings for galleries
 */

(function() {
    'use strict';

    /**
     * Calculate expiration date from gallery data
     */
    function getExpirationDate(gallery) {
        if (!gallery) return null;

        const expiration = gallery.expiration || gallery.expiry_days;
        if (!expiration) return null;

        // Handle expiry_days (number of days from creation)
        if (!isNaN(expiration)) {
            const createdAt = gallery.created_at;
            if (!createdAt) return null;

            try {
                const createdDate = new Date(createdAt);
                const expiryDays = parseInt(expiration);
                const expirationDate = new Date(createdDate);
                expirationDate.setDate(expirationDate.getDate() + expiryDays);
                return expirationDate;
            } catch (e) {
                console.error('Error calculating expiration:', e);
                return null;
            }
        }

        // Handle expiration as ISO date string
        if (typeof expiration === 'string' && expiration.includes('T')) {
            try {
                return new Date(expiration);
            } catch (e) {
                console.error('Error parsing expiration date:', e);
                return null;
            }
        }

        return null;
    }

    /**
     * Check if gallery is expired
     */
    function isExpired(gallery) {
        if (gallery.archived === true) return true;
        
        const expirationDate = getExpirationDate(gallery);
        if (!expirationDate) return false;

        return new Date() > expirationDate;
    }

    /**
     * Check if gallery is expiring soon (within 7 days)
     */
    function isExpiringSoon(gallery) {
        const expirationDate = getExpirationDate(gallery);
        if (!expirationDate) return false;

        const today = new Date();
        const sevenDaysFromNow = new Date();
        sevenDaysFromNow.setDate(today.getDate() + 7);

        return today <= expirationDate && expirationDate <= sevenDaysFromNow;
    }

    /**
     * Get days until expiration
     */
    function getDaysUntilExpiration(gallery) {
        const expirationDate = getExpirationDate(gallery);
        if (!expirationDate) return null;

        const today = new Date();
        const diffTime = expirationDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return diffDays;
    }

    /**
     * Format expiration date for display
     */
    function formatExpirationDate(date) {
        if (!date) return '';
        
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    /**
     * Show expiration banner on gallery page
     */
    function showExpirationBanner(gallery) {
        // Remove existing banner
        const existingBanner = document.getElementById('expirationBanner');
        if (existingBanner) {
            existingBanner.remove();
        }

        const expired = isExpired(gallery);
        const expiringSoon = isExpiringSoon(gallery);

        if (!expired && !expiringSoon) return;

        const daysUntil = getDaysUntilExpiration(gallery);
        const expirationDate = getExpirationDate(gallery);

        // Create banner
        const banner = document.createElement('div');
        banner.id = 'expirationBanner';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            padding: var(--size-m);
            background: ${expired ? 'linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)' : 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'};
            color: white;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            animation: slideDown 0.3s ease-out;
        `;

        if (expired) {
            banner.innerHTML = `
                <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: var(--size-m); flex-wrap: wrap;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 8v4m0 4h.01"/>
                    </svg>
                    <div>
                        <strong style="font-size: 16px;">This gallery has expired</strong>
                        <p style="margin-top: 4px; opacity: 0.9; font-size: 14px;">
                            Expired on ${formatExpirationDate(expirationDate)}. Contact the photographer to extend access.
                        </p>
                    </div>
                </div>
            `;
        } else if (expiringSoon) {
            banner.innerHTML = `
                <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: var(--size-m); flex-wrap: wrap;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                    </svg>
                    <div>
                        <strong style="font-size: 16px;">Gallery expiring soon</strong>
                        <p style="margin-top: 4px; opacity: 0.9; font-size: 14px;">
                            ${daysUntil} ${daysUntil === 1 ? 'day' : 'days'} remaining until ${formatExpirationDate(expirationDate)}
                        </p>
                    </div>
                </div>
            `;
        }

        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideDown {
                from {
                    transform: translateY(-100%);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);

        // Insert banner
        document.body.insertBefore(banner, document.body.firstChild);

        // Adjust main content padding to account for banner
        const mainContent = document.querySelector('main') || document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.marginTop = `${banner.offsetHeight + 20}px`;
        }
    }

    /**
     * Show expiration indicator in gallery settings modal
     */
    function showExpirationInSettings(gallery) {
        const expirySelect = document.querySelector('[name="expiry"]');
        if (!expirySelect) return;

        const expirationDate = getExpirationDate(gallery);
        if (!expirationDate) return;

        const daysUntil = getDaysUntilExpiration(gallery);
        const expired = isExpired(gallery);

        // Find or create expiration info element
        let infoDiv = document.getElementById('expirationInfo');
        if (!infoDiv) {
            infoDiv = document.createElement('div');
            infoDiv.id = 'expirationInfo';
            infoDiv.style.cssText = `
                margin-top: var(--size-s);
                padding: var(--size-m);
                border-radius: var(--border-radius-m);
                font-size: 14px;
                line-height: 1.6;
            `;
            expirySelect.parentElement.appendChild(infoDiv);
        }

        if (expired) {
            infoDiv.style.background = 'linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.05) 100%)';
            infoDiv.style.color = '#DC2626';
            infoDiv.style.border = '1px solid rgba(220, 38, 38, 0.2)';
            infoDiv.innerHTML = `
                <strong>⚠️ This gallery has expired</strong><br>
                Expired on ${formatExpirationDate(expirationDate)}. Change the expiry setting to extend access.
            `;
        } else if (daysUntil <= 7) {
            infoDiv.style.background = 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%)';
            infoDiv.style.color = '#F59E0B';
            infoDiv.style.border = '1px solid rgba(245, 158, 11, 0.2)';
            infoDiv.innerHTML = `
                <strong>⏰ Expiring soon</strong><br>
                ${daysUntil} ${daysUntil === 1 ? 'day' : 'days'} remaining (${formatExpirationDate(expirationDate)})
            `;
        } else {
            infoDiv.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%)';
            infoDiv.style.color = '#3B82F6';
            infoDiv.style.border = '1px solid rgba(59, 130, 246, 0.2)';
            infoDiv.innerHTML = `
                <strong>ℹ️ Gallery expiration</strong><br>
                Expires on ${formatExpirationDate(expirationDate)} (${daysUntil} days remaining)
            `;
        }
    }

    /**
     * Add expiration indicator to gallery cards in dashboard
     */
    function addExpirationIndicatorToCard(cardElement, gallery) {
        if (!cardElement || !gallery) return;

        const expired = isExpired(gallery);
        const expiringSoon = isExpiringSoon(gallery);

        if (!expired && !expiringSoon) return;

        const daysUntil = getDaysUntilExpiration(gallery);

        // Check if indicator already exists
        let indicator = cardElement.querySelector('.expiration-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'expiration-indicator';
            indicator.style.cssText = `
                position: absolute;
                top: var(--size-m);
                right: var(--size-m);
                z-index: 10;
                padding: var(--size-xs) var(--size-s);
                border-radius: var(--border-radius-s);
                font-size: 12px;
                font-weight: 600;
                backdrop-filter: blur(8px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            `;
            cardElement.style.position = 'relative';
            cardElement.appendChild(indicator);
        }

        if (expired) {
            indicator.style.background = 'rgba(220, 38, 38, 0.95)';
            indicator.style.color = 'white';
            indicator.textContent = '⚠️ Expired';
        } else if (expiringSoon) {
            indicator.style.background = 'rgba(245, 158, 11, 0.95)';
            indicator.style.color = 'white';
            indicator.textContent = `⏰ ${daysUntil}d left`;
        }
    }

    /**
     * Initialize expiration checking for current gallery
     */
    function initGalleryExpiration() {
        const gallery = window.currentGalleryData;
        if (!gallery) return;

        // Show banner if expired or expiring soon
        showExpirationBanner(gallery);

        // Update settings modal if it exists
        const settingsModal = document.getElementById('settingsModal');
        if (settingsModal) {
            // Watch for modal opening
            const observer = new MutationObserver(() => {
                if (settingsModal.style.display !== 'none') {
                    showExpirationInSettings(gallery);
                }
            });
            observer.observe(settingsModal, { attributes: true, attributeFilter: ['style'] });
        }
    }

    /**
     * Initialize expiration indicators for gallery cards in dashboard
     */
    function initDashboardExpiration() {
        // Wait for galleries to load
        setTimeout(() => {
            const galleryCards = document.querySelectorAll('.gallery-card, .card-18');
            galleryCards.forEach(card => {
                const galleryId = card.getAttribute('data-gallery-id');
                if (galleryId && window.galleriesData) {
                    const gallery = window.galleriesData.find(g => g.id === galleryId);
                    if (gallery) {
                        addExpirationIndicatorToCard(card, gallery);
                    }
                }
            });
        }, 500);
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initGalleryExpiration();
            initDashboardExpiration();
        });
    } else {
        initGalleryExpiration();
        initDashboardExpiration();
    }

    // Export functions for external use
    window.GalleryExpiration = {
        isExpired,
        isExpiringSoon,
        getDaysUntilExpiration,
        getExpirationDate,
        showExpirationBanner,
        addExpirationIndicatorToCard,
        init: initGalleryExpiration
    };

})();

