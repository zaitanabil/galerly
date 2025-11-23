/**
 * Galerly Visitor Tracking - Comprehensive UX Analytics
 * Mandatory analytics for UX improvement - tracks ALL visitors
 * This is NOT related to optional cookie consent
 */
(function() {
    'use strict';
    
    // Detect LocalStack mode and disable tracking in local development
    const isLocalStack = window.GALERLY_ENV_CONFIG?.IS_LOCALSTACK || 
                        window.location.hostname === 'localhost' || 
                        window.location.hostname === '127.0.0.1';
    
    const TRACKING_CONFIG = {
        apiEndpoint: (typeof window.GalerlyConfig !== 'undefined' && window.GalerlyConfig.API_BASE_URL) || 
                    (typeof window.API_BASE_URL !== 'undefined' && window.API_BASE_URL) ||
                    'https://api.galerly.com/xb667e3fa92f9776468017a9758f31ba4/v1',
        enabled: !isLocalStack, // Disable tracking in LocalStack mode
        sessionTimeout: 30 * 60 * 1000, // 30 minutes
        heartbeatInterval: 30 * 1000, // 30 seconds (send updates every 30s)
        debounceTime: 300, // 300ms
        maxScrollDepthUpdate: 5000 // Send scroll depth update max every 5s
    };
    
    // Early return if tracking is disabled (LocalStack mode)
    if (!TRACKING_CONFIG.enabled) {
        console.log('📊 Visitor tracking disabled in LocalStack mode');
        window.VisitorTracker = null;
        return;
    }
    class VisitorTracker {
        constructor() {
            this.sessionId = this.getOrCreateSessionId();
            this.visitorId = this.getOrCreateVisitorId();
            this.currentPage = null;
            this.pageStartTime = null;
            this.sessionStartTime = this.getSessionStartTime();
            this.totalPagesViewed = this.getTotalPagesViewed();
            // Interaction tracking
            this.interactions = 0;
            this.scrollDepth = 0;
            this.maxScrollDepth = 0;
            this.clicks = 0;
            this.lastScrollUpdate = 0;
            // Form tracking
            this.formInteractions = {};
            // Performance tracking
            this.performanceData = {};
            this.isInitialized = false;
        }
        // ============================================================
        // Session & Visitor Management
        // ============================================================
        getOrCreateSessionId() {
            const sessionKey = 'galerly_session_id';
            const timestampKey = 'galerly_session_timestamp';
            const now = Date.now();
            const lastActivity = localStorage.getItem(timestampKey);
            const sessionId = localStorage.getItem(sessionKey);
            // Check if session expired (30 minutes of inactivity)
            if (sessionId && lastActivity && (now - parseInt(lastActivity) < TRACKING_CONFIG.sessionTimeout)) {
                localStorage.setItem(timestampKey, now.toString());
                return sessionId;
            }
            // Create new session
            const newSessionId = this.generateUUID();
            localStorage.setItem(sessionKey, newSessionId);
            localStorage.setItem(timestampKey, now.toString());
            localStorage.setItem('galerly_session_start', now.toString());
            localStorage.setItem('galerly_pages_viewed', '0');
            return newSessionId;
        }
        getOrCreateVisitorId() {
            const visitorKey = 'galerly_visitor_id';
            let visitorId = localStorage.getItem(visitorKey);
            if (!visitorId) {
                visitorId = this.generateUUID();
                localStorage.setItem(visitorKey, visitorId);
            }
            return visitorId;
        }
        getSessionStartTime() {
            const startTime = localStorage.getItem('galerly_session_start');
            return startTime ? parseInt(startTime) : Date.now();
        }
        getTotalPagesViewed() {
            const pages = localStorage.getItem('galerly_pages_viewed');
            return pages ? parseInt(pages) : 0;
        }
        incrementPagesViewed() {
            this.totalPagesViewed++;
            localStorage.setItem('galerly_pages_viewed', this.totalPagesViewed.toString());
        }
        generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        // ============================================================
        // Device & Location Detection
        // ============================================================
        getDeviceInfo() {
            const ua = navigator.userAgent;
            let deviceType = 'desktop';
            if (/mobile/i.test(ua)) {
                deviceType = 'mobile';
            } else if (/tablet|ipad/i.test(ua)) {
                deviceType = 'tablet';
            }
            // Detect browser
            let browser = 'unknown';
            if (ua.indexOf('Firefox') > -1) {
                browser = 'Firefox';
            } else if (ua.indexOf('Chrome') > -1) {
                browser = 'Chrome';
            } else if (ua.indexOf('Safari') > -1) {
                browser = 'Safari';
            } else if (ua.indexOf('Edge') > -1) {
                browser = 'Edge';
            }
            // Detect OS
            let os = 'unknown';
            if (ua.indexOf('Win') > -1) {
                os = 'Windows';
            } else if (ua.indexOf('Mac') > -1) {
                os = 'MacOS';
            } else if (ua.indexOf('Linux') > -1) {
                os = 'Linux';
            } else if (ua.indexOf('Android') > -1) {
                os = 'Android';
            } else if (ua.indexOf('iOS') > -1) {
                os = 'iOS';
            }
            return {
                type: deviceType,
                browser: browser,
                os: os,
                screen_resolution: `${screen.width}x${screen.height}`,
                viewport_size: `${window.innerWidth}x${window.innerHeight}`,
                pixel_ratio: window.devicePixelRatio || 1,
                touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0
            };
        }
        async getLocationInfo() {
            // Check cache first (valid for 24 hours)
            const cachedLocation = localStorage.getItem('galerly_location_cache');
            const cacheTime = localStorage.getItem('galerly_location_cache_time');
            if (cachedLocation && cacheTime) {
                const age = Date.now() - parseInt(cacheTime);
                if (age < 24 * 60 * 60 * 1000) { // 24 hours
                    return JSON.parse(cachedLocation);
                }
            }
            // Try multiple geolocation services for better accuracy
            try {
                // Try ipapi.co first (most accurate, but has rate limits)
                let response = await fetch('https://ipapi.co/json/', { timeout: 3000 });
                let data = await response.json();
                // If we hit rate limit, try alternative service
                if (data.error || !data.country_name) {
                    response = await fetch('http://ip-api.com/json/', { timeout: 3000 });
                    data = await response.json();
                    // Normalize ip-api.com format to match ipapi.co
                    if (data.status === 'success') {
                        data = {
                            country_name: data.country,
                            country_code: data.countryCode,
                            city: data.city,
                            region: data.regionName,
                            latitude: data.lat,
                            longitude: data.lon,
                            timezone: data.timezone,
                            ip: data.query
                        };
                    }
                }
                const locationData = {
                    country: data.country_name || '',
                    country_code: data.country_code || '',
                    city: data.city || '',
                    region: data.region || '',
                    latitude: data.latitude || 0,
                    longitude: data.longitude || 0,
                    timezone: data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || '',
                    ip: data.ip || '',
                    accuracy: 'ip-based' // Note: IP geolocation is approximate (city-level, ~50-200km accuracy)
                };
                // Cache for 24 hours
                localStorage.setItem('galerly_location_cache', JSON.stringify(locationData));
                localStorage.setItem('galerly_location_cache_time', Date.now().toString());
                return locationData;
            } catch (e) {
                // Fallback to browser timezone at minimum
                return {
                    country: '',
                    country_code: '',
                    city: '',
                    region: '',
                    latitude: 0,
                    longitude: 0,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
                    ip: '',
                    accuracy: 'timezone-only'
                };
            }
        }
        // ============================================================
        // Performance Metrics
        // ============================================================
        getPerformanceMetrics() {
            try {
                const perf = performance.timing;
                const pageLoadTime = perf.loadEventEnd - perf.navigationStart;
                // Get detailed performance metrics
                const domContentLoaded = perf.domContentLoadedEventEnd - perf.navigationStart;
                const domComplete = perf.domComplete - perf.navigationStart;
                const firstPaint = performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint');
                const firstContentfulPaint = performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint');
                // Improved connection type detection - REAL DATA ONLY
                let connectionType = 'unknown';
                let connectionDownlink = 0;
                let connectionRtt = 0;
                if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {
                    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                    // Priority 1: Get actual connection type (most reliable)
                    // type can be: 'bluetooth', 'cellular', 'ethernet', 'none', 'wifi', 'wimax', 'other', 'unknown'
                    if (conn.type && conn.type !== 'unknown' && conn.type !== 'other') {
                        connectionType = conn.type;
                    }
                    // Priority 2: Get effective type (4g, 3g, 2g, slow-2g)
                    else if (conn.effectiveType) {
                        connectionType = conn.effectiveType;
                    }
                    // If neither are available, leave as 'unknown'
                    // Always capture speed/latency metrics if available
                    if (conn.downlink !== undefined) {
                        connectionDownlink = conn.downlink;
                    }
                    if (conn.rtt !== undefined) {
                        connectionRtt = conn.rtt;
                    }
                }
                // No fallbacks, no estimations
                // If data is not available from browser API, it stays 'unknown' / 0
                return {
                    page_load_time: pageLoadTime > 0 ? pageLoadTime : 0,
                    dom_content_loaded: domContentLoaded > 0 ? domContentLoaded : 0,
                    dom_complete: domComplete > 0 ? domComplete : 0,
                    first_paint: firstPaint ? Math.round(firstPaint.startTime) : 0,
                    first_contentful_paint: firstContentfulPaint ? Math.round(firstContentfulPaint.startTime) : 0,
                    connection_type: connectionType,
                    connection_downlink: connectionDownlink,
                    connection_rtt: connectionRtt
                };
            } catch (e) {
                return {
                    page_load_time: 0,
                    dom_content_loaded: 0,
                    dom_complete: 0,
                    first_paint: 0,
                    first_contentful_paint: 0,
                    connection_type: 'unknown',
                    connection_downlink: 0,
                    connection_rtt: 0
                };
            }
        }
        // ============================================================
        // Page Tracking
        // ============================================================
        async trackPageView() {
            if (!TRACKING_CONFIG.enabled) return;
            const currentUrl = window.location.href;
            const previousPage = this.currentPage;
            const previousDuration = this.pageStartTime ? (Date.now() - this.pageStartTime) / 1000 : 0;
            const previousScrollDepth = this.maxScrollDepth;
            const previousClicks = this.clicks;
            // Send final update for previous page with actual interaction data
            if (previousPage && previousDuration > 1) {
                await this.sendPageUpdate(previousPage, previousDuration, previousScrollDepth, previousClicks, true);
            }
            // Reset for new page
            this.currentPage = currentUrl;
            this.pageStartTime = Date.now();
            this.interactions = 0;
            this.scrollDepth = 0;
            this.maxScrollDepth = 0;
            this.clicks = 0;
            this.incrementPagesViewed();
            const device = this.getDeviceInfo();
            const location = await this.getLocationInfo();
            const performance = this.getPerformanceMetrics();
            const data = {
                session_id: this.sessionId,
                visitor_id: this.visitorId,
                page_url: currentUrl,
                referrer: document.referrer,
                user_agent: navigator.userAgent,
                device: device,
                location: location,
                performance: performance,
                duration: 0, // Just started
                interaction: {
                    scroll_depth: 0,
                    clicks: 0
                },
                session_pages_viewed: this.totalPagesViewed
            };
            try {
                await fetch(`${TRACKING_CONFIG.apiEndpoint}/visitor/track/visit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
            } catch (e) {
            }
        }
        async sendPageUpdate(pageUrl, duration, scrollDepth, clicks, isFinal = false) {
            if (!TRACKING_CONFIG.enabled) return;
            try {
                await fetch(`${TRACKING_CONFIG.apiEndpoint}/visitor/track/event`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        visitor_id: this.visitorId,
                        event_type: isFinal ? 'page_exit' : 'page_engagement',
                        event_category: 'engagement',
                        event_label: pageUrl,
                        event_value: Math.round(duration),
                        page_url: pageUrl,
                        metadata: {
                            duration_seconds: duration,
                            scroll_depth_percent: scrollDepth,
                            total_clicks: clicks,
                            is_final: isFinal
                        }
                    })
                });
            } catch (e) {
            }
        }
        // ============================================================
        // Event Tracking
        // ============================================================
        async trackEvent(eventType, category, label, value = 0, metadata = {}) {
            if (!TRACKING_CONFIG.enabled) return;
            const data = {
                session_id: this.sessionId,
                visitor_id: this.visitorId,
                event_type: eventType,
                event_category: category,
                event_label: label,
                event_value: value,
                page_url: window.location.href,
                metadata: metadata
            };
            try {
                await fetch(`${TRACKING_CONFIG.apiEndpoint}/visitor/track/event`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
            } catch (e) {
            }
        }
        // ============================================================
        // Interaction Tracking
        // ============================================================
        trackScroll() {
            const scrollPercent = Math.min(100, Math.round(
                ((window.scrollY + window.innerHeight) / document.documentElement.scrollHeight) * 100
            ));
            this.scrollDepth = scrollPercent;
            this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollPercent);
            // Send scroll depth milestones (25%, 50%, 75%, 100%)
            const milestones = [25, 50, 75, 100];
            const milestone = milestones.find(m => scrollPercent >= m && scrollPercent < m + 5);
            if (milestone) {
                const key = `scroll_${milestone}`;
                if (!this[key]) {
                    this[key] = true;
                    this.trackEvent('scroll_milestone', 'engagement', `Scrolled ${milestone}%`, milestone);
                }
            }
            // Periodic scroll update
            const now = Date.now();
            if (now - this.lastScrollUpdate > TRACKING_CONFIG.maxScrollDepthUpdate) {
                this.lastScrollUpdate = now;
                const duration = this.pageStartTime ? (now - this.pageStartTime) / 1000 : 0;
                if (duration > 5) { // Only send if user has been on page for 5+ seconds
                    this.sendPageUpdate(this.currentPage, duration, this.maxScrollDepth, this.clicks, false);
                }
            }
        }
        trackClick(event) {
            this.clicks++;
            this.interactions++;
            const target = event.target;
            const tagName = target.tagName.toLowerCase();
            // Track specific interactions
            if (tagName === 'a') {
                const href = target.href || '';
                const text = target.textContent.substring(0, 100).trim();
                this.trackEvent('click_link', 'navigation', text, 1, {
                    href: href,
                    text: text,
                    is_external: href && !href.includes(window.location.hostname)
                });
            } else if (tagName === 'button') {
                const text = target.textContent.substring(0, 100).trim();
                const type = target.type || 'button';
                this.trackEvent('click_button', 'interaction', text, 1, {
                    text: text,
                    type: type,
                    class: target.className
                });
            } else if (tagName === 'input' && target.type === 'submit') {
                this.trackEvent('form_submit', 'conversion', `form:${target.form?.id || 'unknown'}`, 1, {
                    form_id: target.form?.id || 'unknown',
                    form_action: target.form?.action || ''
                });
            }
        }
        trackFormInteraction(formElement) {
            const formId = formElement.id || formElement.name || 'unknown';
            if (!this.formInteractions[formId]) {
                this.formInteractions[formId] = {
                    started: Date.now(),
                    fields_interacted: new Set()
                };
                this.trackEvent('form_start', 'engagement', formId, 1);
            }
        }
        trackFormFieldFocus(fieldElement) {
            const form = fieldElement.form;
            if (form) {
                this.trackFormInteraction(form);
                const formId = form.id || form.name || 'unknown';
                const fieldName = fieldElement.name || fieldElement.id || 'unknown';
                this.formInteractions[formId].fields_interacted.add(fieldName);
            }
        }
        trackFormSubmit(formElement) {
            const formId = formElement.id || formElement.name || 'unknown';
            const formData = this.formInteractions[formId];
            if (formData) {
                const duration = (Date.now() - formData.started) / 1000;
                this.trackEvent('form_complete', 'conversion', formId, Math.round(duration), {
                    duration_seconds: duration,
                    fields_count: formData.fields_interacted.size
                });
            } else {
                this.trackEvent('form_complete', 'conversion', formId, 0);
            }
        }
        // ============================================================
        // Error Tracking
        // ============================================================
        trackError(error, source) {
            this.trackEvent('javascript_error', 'error', error.message || 'Unknown error', 0, {
                error: error.message || String(error),
                stack: error.stack ? error.stack.substring(0, 500) : '',
                source: source,
                url: window.location.href
            });
        }
        // ============================================================
        // Session End Tracking
        // ============================================================
        async trackSessionEnd() {
            if (!TRACKING_CONFIG.enabled) return;
            const pageDuration = this.pageStartTime ? (Date.now() - this.pageStartTime) / 1000 : 0;
            const sessionDuration = (Date.now() - this.sessionStartTime) / 1000;
            const data = {
                session_id: this.sessionId,
                visitor_id: this.visitorId,
                total_duration: sessionDuration,
                page_duration: pageDuration,
                total_pages_viewed: this.totalPagesViewed,
                total_interactions: this.interactions,
                final_scroll_depth: this.maxScrollDepth,
                final_clicks: this.clicks,
                exit_page: window.location.href
            };
            // Use sendBeacon for reliability on page unload
            try {
                const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
                navigator.sendBeacon(`${TRACKING_CONFIG.apiEndpoint}/visitor/track/session-end`, blob);
            } catch (e) {
            }
        }
        // ============================================================
        // Initialization
        // ============================================================
        init() {
            if (this.isInitialized) return;
            this.isInitialized = true;
            // Track initial page view
            this.trackPageView();
            // Track scroll with debounce
            let scrollTimeout;
            window.addEventListener('scroll', () => {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    this.trackScroll();
                }, TRACKING_CONFIG.debounceTime);
            }, { passive: true });
            // Track clicks
            document.addEventListener('click', (e) => {
                this.trackClick(e);
            }, true);
            // Track form interactions
            document.addEventListener('focus', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                    this.trackFormFieldFocus(e.target);
                }
            }, true);
            document.addEventListener('submit', (e) => {
                if (e.target.tagName === 'FORM') {
                    this.trackFormSubmit(e.target);
                }
            }, true);
            // Track page visibility changes
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.trackEvent('visibility_change', 'engagement', 'page_hidden', 0);
                    // Send update when user leaves tab
                    const duration = this.pageStartTime ? (Date.now() - this.pageStartTime) / 1000 : 0;
                    if (duration > 2) {
                        this.sendPageUpdate(this.currentPage, duration, this.maxScrollDepth, this.clicks, false);
                    }
                } else {
                    this.trackEvent('visibility_change', 'engagement', 'page_visible', 0);
                }
            });
            // Track page unload
            window.addEventListener('beforeunload', () => {
                this.trackSessionEnd();
            });
            // Track page hide (more reliable than beforeunload on mobile)
            window.addEventListener('pagehide', () => {
                this.trackSessionEnd();
            });
            // Handle SPA navigation (if using a router)
            window.addEventListener('popstate', () => {
                this.trackPageView();
            });
            // Heartbeat to send periodic updates and keep session alive
            setInterval(() => {
                const timestampKey = 'galerly_session_timestamp';
                localStorage.setItem(timestampKey, Date.now().toString());
                // Send engagement update every 30 seconds if user is active
                const duration = this.pageStartTime ? (Date.now() - this.pageStartTime) / 1000 : 0;
                if (duration > 10) { // Only if on page for 10+ seconds
                    this.sendPageUpdate(this.currentPage, duration, this.maxScrollDepth, this.clicks, false);
                }
            }, TRACKING_CONFIG.heartbeatInterval);
            // Track JavaScript errors
            window.addEventListener('error', (event) => {
                this.trackError(event.error || { message: event.message }, 'window.onerror');
            });
            window.addEventListener('unhandledrejection', (event) => {
                this.trackError({ message: event.reason }, 'unhandledrejection');
            });
        }
    }
    // Initialize tracker when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.galerlyTracker = new VisitorTracker();
            window.galerlyTracker.init();
        });
    } else {
        window.galerlyTracker = new VisitorTracker();
        window.galerlyTracker.init();
    }
})();