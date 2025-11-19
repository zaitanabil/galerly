/**
 * Role-Based Access Control (RBAC)
 * This script checks if the user has permission to access the current page
 * and redirects to 404 if they don't have the correct role.
 */
(function() {
    'use strict';
    // Define page access rules
    const PAGE_ACCESS = {
        // Photographer-only pages
        photographer: [
            'dashboard.html',
            'dashboard',
            'new-gallery.html',
            'new-gallery',
            'billing.html',
            'billing',
            'profile-settings.html',
            'profile-settings',
            'gallery.html' // Photographers can access their own gallery pages
        ],
        // Client-only pages
        client: [
            'client-dashboard.html',
            'client-dashboard',
            'client-gallery.html',
            'client-gallery'
        ],
        // Public pages (accessible to everyone)
        public: [
            'index.html',
            '',
            '/',
            'auth.html',
            'auth',
            'contact.html',
            'contact',
            'faq.html',
            'faq',
            'photographers.html',
            'photographers',
            'portfolio.html',
            'portfolio',
            'pricing.html',
            'pricing',
            'privacy.html',
            'privacy',
            'legal-notice.html',
            'legal-notice',
            'reset-password.html',
            'reset-password',
            '404.html',
            '404'
        ]
    };
    /**
     * Get the current page path
     */
    function getCurrentPage() {
        const pathname = window.location.pathname;
        const page = pathname.split('/').pop() || 'index.html';
        // Remove .html extension for comparison
        return page.replace('.html', '');
    }
    /**
     * Get user role from localStorage
     */
    function getUserRole() {
        try {
            const userData = localStorage.getItem('galerly_user_data');
            if (userData) {
                const user = JSON.parse(userData);
                return user.role || null;
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
        return null;
    }
    /**
     * Check if user is authenticated
     */
    function isAuthenticated() {
        // Check for user data in localStorage (UI state only)
        // Actual auth is handled by HttpOnly cookie
        return localStorage.getItem('galerly_user_data') !== null;
    }
    /**
     * Check if current page is in a list
     */
    function isPageInList(currentPage, pageList) {
        return pageList.some(page => {
            const normalizedPage = page.replace('.html', '');
            return currentPage === normalizedPage || 
                   currentPage === page ||
                   (normalizedPage === '' && (currentPage === 'index' || currentPage === ''));
        });
    }
    /**
     * Check if user has access to current page
     */
    function checkAccess() {
        const currentPage = getCurrentPage();
        const userRole = getUserRole();
        const authenticated = isAuthenticated();
        // Always allow access to 404 page
        if (currentPage === '404') {
            return true;
        }
        // Allow public access to client-gallery if a share token is present
        // This allows clients to view galleries via share links without logging in
        if (currentPage === 'client-gallery') {
            const urlParams = new URLSearchParams(window.location.search);
            const hasToken = urlParams.has('token');
            // Allow access if there's a token (public share) OR if user is authenticated as client
            if (hasToken || (authenticated && userRole === 'client')) {
                return true;
            }
            // Block if no token and not a client
            return false;
        }
        // Check if it's a public page
        if (isPageInList(currentPage, PAGE_ACCESS.public)) {
            return true; // Public pages accessible to everyone
        }
        // If not authenticated, block access to protected pages
        if (!authenticated) {
            return false;
        }
        // Check photographer pages
        if (isPageInList(currentPage, PAGE_ACCESS.photographer)) {
            return userRole === 'photographer';
        }
        // Check client pages
        if (isPageInList(currentPage, PAGE_ACCESS.client)) {
            return userRole === 'client';
        }
        // If we reach here, page is not in any list - allow access by default
        return true;
    }
    /**
     * Redirect to 404 page
     */
    function redirectTo404() {
        // Prevent infinite redirect loop
        if (getCurrentPage() === '404') {
            return;
        }
        window.location.href = '/404';
    }
    /**
     * Run access control check
     */
    function runAccessControl() {
        const hasAccess = checkAccess();
        if (!hasAccess) {
            redirectTo404();
        }
    }
    // Run immediately if DOM is already loaded, or wait for DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runAccessControl);
    } else {
        runAccessControl();
    }
})();