/**
 * Cookie Consent Manager
 * Handles cookie consent popup and preferences
 */
// Cookie utility functions
const CookieManager = {
    // Set a cookie
    set: function(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + (value || '') + expires + '; path=/; SameSite=Lax';
    },
    // Get a cookie
    get: function(name) {
        const nameEQ = name + '=';
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    },
    // Delete a cookie
    delete: function(name) {
        document.cookie = name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }
};
// Cookie consent preferences
const CookieConsent = {
    COOKIE_NAME: 'galerly_cookie_consent',
    COOKIE_DURATION: 365, // 1 year
    init: function() {
        const consent = this.getConsent();
        if (!consent) {
            // No consent yet, show popup
            this.showPopup();
        } else {
            // Apply existing preferences
            this.applyPreferences(consent);
        }
        // Attach event listeners
        this.attachEventListeners();
    },
    showPopup: function() {
        const popup = document.querySelector('.main-16.grid-5.animation-9');
        if (popup) {
            // Animate popup in
            if (typeof gsap !== 'undefined') {
                gsap.to(popup, {
                    opacity: 1,
                    y: 0,
                    duration: 0.6,
                    ease: 'power2.out',
                    pointerEvents: 'auto',
                    delay: 1
                });
            } else {
                popup.style.opacity = '1';
                popup.style.transform = 'translateY(0)';
                popup.style.pointerEvents = 'auto';
            }
        }
    },
    hidePopup: function() {
        const popup = document.querySelector('.main-16.grid-5.animation-9');
        if (popup) {
            // Animate popup out
            if (typeof gsap !== 'undefined') {
                gsap.to(popup, {
                    opacity: 0,
                    y: 100,
                    duration: 0.4,
                    ease: 'power2.in',
                    onComplete: () => {
                        popup.style.pointerEvents = 'none';
                    }
                });
            } else {
                popup.style.opacity = '0';
                popup.style.transform = 'translateY(100px)';
                popup.style.pointerEvents = 'none';
            }
        }
    },
    attachEventListeners: function() {
        // Accept all button
        const acceptBtn = document.querySelector('button[aria-label="Accept all"]');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', () => {
                this.acceptAll();
            });
        }
        // Deny all button
        const denyBtn = document.querySelector('button[aria-label="Deny all"]');
        if (denyBtn) {
            denyBtn.addEventListener('click', () => {
                this.denyAll();
            });
        }
        // Customize button
        const customizeBtn = document.querySelector('button[aria-label="Customize"]');
        if (customizeBtn) {
            customizeBtn.addEventListener('click', () => {
                this.showCustomizeModal();
            });
        }
    },
    acceptAll: function() {
        const preferences = {
            necessary: true,
            analytics: true,
            marketing: true,
            preferences: true
        };
        this.saveConsent(preferences);
        this.applyPreferences(preferences);
        this.hidePopup();
    },
    denyAll: function() {
        const preferences = {
            necessary: true, // Always required
            analytics: false,
            marketing: false,
            preferences: false
        };
        this.saveConsent(preferences);
        this.applyPreferences(preferences);
        this.hidePopup();
    },
    showCustomizeModal: function() {
        // Hide the main popup
        this.hidePopup();
        // Create modal overlay
        const modalHTML = `
            <div id="cookieCustomizeModal" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
            ">
                <div style="
                    background: white;
                    border-radius: 24px;
                    padding: 40px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    transform: translateY(20px);
                    transition: transform 0.3s ease;
                ">
                    <h2 style="
                        margin: 0 0 24px 0;
                        font-size: 28px;
                        font-weight: 600;
                        color: #1d1d1f;
                    ">Customize Cookie Preferences</h2>
                    <p style="
                        margin: 0 0 32px 0;
                        color: #6e6e73;
                        font-size: 16px;
                        line-height: 1.6;
                    ">Choose which types of cookies you want to allow. Necessary cookies are always enabled as they are required for the website to function properly.</p>
                    <!-- Necessary Cookies (Always On) -->
                    <div style="
                        padding: 20px;
                        background: #f5f5f7;
                        border-radius: 12px;
                        margin-bottom: 16px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #1d1d1f;">
                                    Necessary Cookies
                                </h3>
                                <p style="margin: 0; color: #6e6e73; font-size: 14px; line-height: 1.5;">
                                    Required for the website to function. Cannot be disabled.
                                </p>
                            </div>
                            <div style="
                                width: 50px;
                                height: 28px;
                                background: #34c759;
                                border-radius: 14px;
                                position: relative;
                                margin-left: 16px;
                                flex-shrink: 0;
                            ">
                                <div style="
                                    position: absolute;
                                    top: 3px;
                                    right: 3px;
                                    width: 22px;
                                    height: 22px;
                                    background: white;
                                    border-radius: 50%;
                                "></div>
                            </div>
                        </div>
                    </div>
                    <!-- Analytics Cookies -->
                    <div style="
                        padding: 20px;
                        background: #f5f5f7;
                        border-radius: 12px;
                        margin-bottom: 16px;
                        cursor: pointer;
                    " onclick="CookieConsent.toggleCookieOption(this, 'analytics')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #1d1d1f;">
                                    Analytics Cookies
                                </h3>
                                <p style="margin: 0; color: #6e6e73; font-size: 14px; line-height: 1.5;">
                                    Help us understand how visitors interact with our website.
                                </p>
                            </div>
                            <div class="cookie-toggle" data-enabled="true" style="
                                width: 50px;
                                height: 28px;
                                background: #34c759;
                                border-radius: 14px;
                                position: relative;
                                margin-left: 16px;
                                flex-shrink: 0;
                                transition: background 0.3s ease;
                            ">
                                <div style="
                                    position: absolute;
                                    top: 3px;
                                    right: 3px;
                                    width: 22px;
                                    height: 22px;
                                    background: white;
                                    border-radius: 50%;
                                    transition: transform 0.3s ease;
                                "></div>
                            </div>
                        </div>
                    </div>
                    <!-- Marketing Cookies -->
                    <div style="
                        padding: 20px;
                        background: #f5f5f7;
                        border-radius: 12px;
                        margin-bottom: 16px;
                        cursor: pointer;
                    " onclick="CookieConsent.toggleCookieOption(this, 'marketing')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #1d1d1f;">
                                    Marketing Cookies
                                </h3>
                                <p style="margin: 0; color: #6e6e73; font-size: 14px; line-height: 1.5;">
                                    Used to deliver personalized ads and measure campaign effectiveness.
                                </p>
                            </div>
                            <div class="cookie-toggle" data-enabled="true" style="
                                width: 50px;
                                height: 28px;
                                background: #34c759;
                                border-radius: 14px;
                                position: relative;
                                margin-left: 16px;
                                flex-shrink: 0;
                                transition: background 0.3s ease;
                            ">
                                <div style="
                                    position: absolute;
                                    top: 3px;
                                    right: 3px;
                                    width: 22px;
                                    height: 22px;
                                    background: white;
                                    border-radius: 50%;
                                    transition: transform 0.3s ease;
                                "></div>
                            </div>
                        </div>
                    </div>
                    <!-- Preference Cookies -->
                    <div style="
                        padding: 20px;
                        background: #f5f5f7;
                        border-radius: 12px;
                        margin-bottom: 32px;
                        cursor: pointer;
                    " onclick="CookieConsent.toggleCookieOption(this, 'preferences')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #1d1d1f;">
                                    Preference Cookies
                                </h3>
                                <p style="margin: 0; color: #6e6e73; font-size: 14px; line-height: 1.5;">
                                    Remember your settings and preferences for a better experience.
                                </p>
                            </div>
                            <div class="cookie-toggle" data-enabled="true" style="
                                width: 50px;
                                height: 28px;
                                background: #34c759;
                                border-radius: 14px;
                                position: relative;
                                margin-left: 16px;
                                flex-shrink: 0;
                                transition: background 0.3s ease;
                            ">
                                <div style="
                                    position: absolute;
                                    top: 3px;
                                    right: 3px;
                                    width: 22px;
                                    height: 22px;
                                    background: white;
                                    border-radius: 50%;
                                    transition: transform 0.3s ease;
                                "></div>
                            </div>
                        </div>
                    </div>
                    <!-- Buttons -->
                    <div style="display: flex; gap: 12px; justify-content: flex-end;">
                        <button onclick="CookieConsent.closeCustomizeModal()" style="
                            font-family: var(--pp-neue-font, 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif);
                            padding: var(--size-m, 14px) var(--size-l, 32px);
                            border: 1px solid var(--text-on-button-tertiary, #1d1d1f);
                            background: transparent;
                            color: var(--text-on-button-tertiary, #1d1d1f);
                            border-radius: var(--border-radius-xl, 980px);
                            font-size: 1.125rem;
                            font-weight: 400;
                            line-height: 1.5rem;
                            cursor: pointer;
                            transition: all 0.2s ease;
                        " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                            Cancel
                        </button>
                        <button onclick="CookieConsent.saveCustomPreferences()" style="
                            font-family: var(--pp-neue-font, 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif);
                            padding: var(--size-m, 14px) var(--size-l, 32px);
                            border: none;
                            background: var(--button-primary-fill, #0071e3);
                            color: var(--text-on-button-primary, white);
                            border-radius: var(--border-radius-xl, 980px);
                            font-size: 1.125rem;
                            font-weight: 500;
                            line-height: 1.5rem;
                            cursor: pointer;
                            transition: all 0.2s ease;
                        " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                            Save Preferences
                        </button>
                    </div>
                </div>
            </div>
        `;
        // Insert modal into body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        // Animate in
        setTimeout(() => {
            const modal = document.getElementById('cookieCustomizeModal');
            if (modal) {
                modal.style.opacity = '1';
                const content = modal.querySelector('div > div');
                if (content) {
                    content.style.transform = 'translateY(0)';
                }
            }
        }, 10);
    },
    toggleCookieOption: function(element, type) {
        const toggle = element.querySelector('.cookie-toggle');
        const isEnabled = toggle.dataset.enabled === 'true';
        const newState = !isEnabled;
        toggle.dataset.enabled = newState;
        toggle.style.background = newState ? '#34c759' : '#d1d1d6';
        const circle = toggle.querySelector('div');
        if (circle) {
            circle.style.transform = newState ? 'translateX(0)' : 'translateX(-22px)';
        }
    },
    saveCustomPreferences: function() {
        const modal = document.getElementById('cookieCustomizeModal');
        if (!modal) return;
        // Get toggle states
        const toggles = modal.querySelectorAll('.cookie-toggle');
        const preferences = {
            necessary: true, // Always true
            analytics: false,
            marketing: false,
            preferences: false
        };
        toggles.forEach((toggle, index) => {
            const isEnabled = toggle.dataset.enabled === 'true';
            const types = ['analytics', 'marketing', 'preferences'];
            if (index < types.length) {
                preferences[types[index]] = isEnabled;
            }
        });
        // Save and apply
        this.saveConsent(preferences);
        this.applyPreferences(preferences);
        this.closeCustomizeModal();
    },
    closeCustomizeModal: function() {
        const modal = document.getElementById('cookieCustomizeModal');
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.remove();
                // Show the main popup again
                this.showPopup();
            }, 300);
        }
    },
    saveConsent: function(preferences) {
        const consentData = {
            ...preferences,
            timestamp: new Date().toISOString(),
            version: '1.0'
        };
        CookieManager.set(this.COOKIE_NAME, JSON.stringify(consentData), this.COOKIE_DURATION);
    },
    getConsent: function() {
        const consentStr = CookieManager.get(this.COOKIE_NAME);
        if (!consentStr) return null;
        try {
            return JSON.parse(consentStr);
        } catch (e) {
            console.error('Failed to parse cookie consent:', e);
            return null;
        }
    },
    applyPreferences: function(preferences) {
        // Apply analytics cookies
        if (preferences.analytics) {
            this.enableAnalytics();
        } else {
            this.disableAnalytics();
        }
        // Apply marketing cookies
        if (preferences.marketing) {
            this.enableMarketing();
        } else {
            this.disableMarketing();
        }
        // Apply preference cookies
        if (preferences.preferences) {
            this.enablePreferences();
        } else {
            this.disablePreferences();
        }
    },
    enableAnalytics: function() {
        // Enable Google Analytics or other analytics
        // Example: Initialize Google Analytics
        // if (typeof gtag !== 'undefined') {
        //     gtag('consent', 'update', {
        //         'analytics_storage': 'granted'
        //     });
        // }
    },
    disableAnalytics: function() {
        // Example: Disable Google Analytics
        // if (typeof gtag !== 'undefined') {
        //     gtag('consent', 'update', {
        //         'analytics_storage': 'denied'
        //     });
        // }
    },
    enableMarketing: function() {
        // Example: Enable marketing pixels
        // if (typeof fbq !== 'undefined') {
        //     fbq('consent', 'grant');
        // }
    },
    disableMarketing: function() {
    },
    enablePreferences: function() {
    },
    disablePreferences: function() {
    },
    // Method to reset consent (for testing)
    reset: function() {
        CookieManager.delete(this.COOKIE_NAME);
        location.reload();
    }
};
// Initialize cookie consent when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        CookieConsent.init();
    });
} else {
    CookieConsent.init();
}
// Export for use in console (optional)
window.CookieConsent = CookieConsent;