/**
 * Authentication Check and UI Update
 * This script verifies authentication with the backend (HttpOnly cookie)
 * and updates UI accordingly (Sign In vs Logout button)
 * Handles both desktop header button and mobile menu
 * Shows/hides Dashboard links based on authentication
 * Shows/hides Email Templates nav link for Pro users
 * 
 * SECURITY: localStorage is ONLY for UI hints. Authorization via backend API.
 */
(function() {
    function getUserRole() {
        // UI hint for dashboard routing
        // Backend should always provide a valid role
        try {
            const userData = localStorage.getItem('galerly_user_data');
            if (userData) {
                const user = JSON.parse(userData);
                return user.role;
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
        return null;
    }
    
    function getUserPlan() {
        // UI HINT ONLY - actual authorization via backend API
        try {
            const userData = localStorage.getItem('galerly_user_data');
            if (userData) {
                const user = JSON.parse(userData);
                return (user.plan || '').toLowerCase();
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
        return '';
    }
    
    function isProUser() {
        // UI HINT ONLY - actual authorization via backend API
        const plan = getUserPlan();
        return plan === 'pro';
    }
    
    function updateEmailTemplatesNav() {
        // UI hint to show/hide nav link
        // Backend API enforces actual access control
        const emailTemplatesNav = document.getElementById('email-templates-nav');
        const mobileEmailTemplatesNav = document.getElementById('mobile-email-templates-nav');
        
        if (isProUser()) {
            if (emailTemplatesNav) emailTemplatesNav.style.display = '';
            if (mobileEmailTemplatesNav) mobileEmailTemplatesNav.style.display = '';
        } else {
            if (emailTemplatesNav) emailTemplatesNav.style.display = 'none';
            if (mobileEmailTemplatesNav) mobileEmailTemplatesNav.style.display = 'none';
        }
    }
    
    // Make updateEmailTemplatesNav globally accessible so billing.js can call it
    window.updateEmailTemplatesNav = updateEmailTemplatesNav;
    
    function updateDashboardLinks(isAuthenticated) {
        const userRole = getUserRole();
        
        // Get all dashboard links (both desktop and mobile)
        const photographerDashboardLinks = document.querySelectorAll('a[href="dashboard"]');
        const clientDashboardLinks = document.querySelectorAll('a[href="client-dashboard"]');
        
        if (isAuthenticated) {
            // User is authenticated, show correct dashboard based on role
            if (userRole === 'client') {
                // Show client dashboard links, hide photographer dashboard links
                clientDashboardLinks.forEach(link => {
                    link.style.display = '';
                    if (link.parentElement && link.parentElement.tagName === 'LI') {
                        link.parentElement.style.display = '';
                    }
                });
                photographerDashboardLinks.forEach(link => {
                    link.style.display = 'none';
                    if (link.parentElement && link.parentElement.tagName === 'LI') {
                        link.parentElement.style.display = 'none';
                    }
                });
            } else {
                // Show photographer dashboard links, hide client dashboard links
                photographerDashboardLinks.forEach(link => {
                    link.style.display = '';
                    if (link.parentElement && link.parentElement.tagName === 'LI') {
                        link.parentElement.style.display = '';
                    }
                });
                clientDashboardLinks.forEach(link => {
                    link.style.display = 'none';
                    if (link.parentElement && link.parentElement.tagName === 'LI') {
                        link.parentElement.style.display = 'none';
                    }
                });
            }
            
            // Update Email Templates nav visibility for authenticated Pro users
            updateEmailTemplatesNav();
        } else {
            // User is not authenticated, hide all dashboard links
            photographerDashboardLinks.forEach(link => {
                link.style.display = 'none';
                if (link.parentElement && link.parentElement.tagName === 'LI') {
                    link.parentElement.style.display = 'none';
                }
            });
            clientDashboardLinks.forEach(link => {
                link.style.display = 'none';
                if (link.parentElement && link.parentElement.tagName === 'LI') {
                    link.parentElement.style.display = 'none';
                }
            });
        }
    }
    
    async function updateAuthButtons() {
        // Verify authentication with backend (HttpOnly cookie)
        let isAuth = false;
        try {
            if (typeof window.isAuthenticated === 'function') {
                isAuth = await window.isAuthenticated();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            isAuth = false;
        }
        
        // Update dashboard link visibility
        updateDashboardLinks(isAuth);
        
        // Update mobile menu button
        const mobileSignInButton = document.querySelector('.item-15.subtitle-6 a[href="auth"]');
        if (isAuth && mobileSignInButton) {
            const logoutButton = document.createElement('button');
            logoutButton.setAttribute('aria-label', 'Logout');
            logoutButton.style.cssText = mobileSignInButton.style.cssText;
            logoutButton.style.background = 'none';
            logoutButton.style.border = 'none';
            logoutButton.style.color = 'inherit';
            logoutButton.style.font = 'inherit';
            logoutButton.style.cursor = 'pointer';
            logoutButton.style.padding = '0';
            logoutButton.style.width = '100%';
            logoutButton.style.textAlign = 'left';
            logoutButton.textContent = 'Logout';
            logoutButton.onclick = function() {
                if (window.logout) {
                    window.logout();
                } else {
                    localStorage.removeItem('galerly_user_data');
                    window.location.href = '/';
                }
            };
            
            mobileSignInButton.parentNode.replaceChild(logoutButton, mobileSignInButton);
        }
        
        // Update desktop header button
        const desktopAuthButton = document.getElementById('desktop-auth-button');
        if (desktopAuthButton) {
            if (isAuth) {
                // User is logged in, show Logout button
                desktopAuthButton.setAttribute('aria-label', 'Logout');
                desktopAuthButton.removeAttribute('href');
                desktopAuthButton.style.cursor = 'pointer';
                desktopAuthButton.style.background = 'var(--color-blue)';
                desktopAuthButton.style.color = 'var(--color-white)';
                desktopAuthButton.querySelector('.subtitle-18').textContent = 'Logout';
                desktopAuthButton.onclick = function(e) {
                    e.preventDefault();
                    if (window.logout) {
                        window.logout();
                    } else {
                        localStorage.removeItem('galerly_user_data');
                        window.location.href = '/';
                    }
            };
            } else {
                // User is not logged in, show Sign In button
                desktopAuthButton.setAttribute('aria-label', 'Sign In');
                desktopAuthButton.setAttribute('href', 'auth');
                desktopAuthButton.style.background = 'var(--color-blue)';
                desktopAuthButton.style.color = 'var(--color-white)';
                desktopAuthButton.querySelector('.subtitle-18').textContent = 'Sign In';
                desktopAuthButton.onclick = null;
            }
            
            // Show/hide based on screen size
            updateDesktopButtonVisibility();
        }
    }
    
    function updateDesktopButtonVisibility() {
        const desktopAuthButton = document.getElementById('desktop-auth-button');
        const mobileMenu = document.querySelector('.icon-15.hero-6.animation-9');
        const mobileMenuToggle = document.querySelector('.link-16.feature-1.main-10');
        
        if (desktopAuthButton) {
            // Check if mobile menu OR mobile menu toggle is visible
            let shouldHideButton = false;
            
            if (mobileMenu) {
                const mobileMenuStyle = window.getComputedStyle(mobileMenu);
                shouldHideButton = mobileMenuStyle.display !== 'none';
            }
            
            if (!shouldHideButton && mobileMenuToggle) {
                const mobileToggleStyle = window.getComputedStyle(mobileMenuToggle);
                shouldHideButton = mobileToggleStyle.display !== 'none';
            }
            
            // Show desktop button only when both mobile menu and toggle are hidden
            if (shouldHideButton) {
                desktopAuthButton.style.display = 'none';
            } else {
                desktopAuthButton.style.display = 'flex';
                desktopAuthButton.style.background = 'var(--color-blue)';
                desktopAuthButton.style.color = 'var(--color-white)';
            }
        }
    }
    
    // Run immediately if DOM is already loaded, or wait for DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            updateAuthButtons();
            // Update visibility on window resize
            window.addEventListener('resize', updateDesktopButtonVisibility);
        });
    } else {
        updateAuthButtons();
        // Update visibility on window resize
        window.addEventListener('resize', updateDesktopButtonVisibility);
    }
})();



