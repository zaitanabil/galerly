/**
 * Galerly - Newsletter Subscription Handler
 * Handles newsletter form submission and validation
 */
(function() {
    'use strict';
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNewsletter);
    } else {
        initNewsletter();
    }
    function initNewsletter() {
        const form = document.getElementById('newsletter_form');
        if (!form) {
            return;
        }
        form.addEventListener('submit', handleNewsletterSubmit);
    }
    async function handleNewsletterSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        const firstNameInput = form.querySelector('input[name="firstName"]');
        const emailInput = form.querySelector('input[name="email"]');
        // Validate inputs
        const firstName = firstNameInput?.value.trim();
        const email = emailInput?.value.trim();
        if (!firstName || !email) {
            showMessage('Please fill in all fields', 'error');
            return;
        }
        // Validate email format
        if (!validateEmail(email)) {
            showMessage('Please enter a valid email address', 'error');
            return;
        }
        // Disable form during submission
        setFormState(form, submitButton, true);
        try {
            // Submit to API
            const response = await fetch(getApiUrl('newsletter/subscribe'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    firstName: firstName,
                    email: email
                })
            });
            const data = await response.json();
            if (response.ok) {
                // Success
                if (data.already_subscribed) {
                    showMessage('You\'re already subscribed! Thank you for your interest.', 'info');
                } else if (data.reactivated) {
                    showMessage('Welcome back! Your subscription has been reactivated.', 'success');
                } else {
                    showMessage('Thank you for subscribing! Welcome to the Galerly community.', 'success');
                }
                // Reset form after successful submission
                form.reset();
                // Track subscription (if analytics enabled)
                if (window.GalerlyConfig?.ENABLE_ANALYTICS && typeof gtag !== 'undefined') {
                    gtag('event', 'newsletter_subscription', {
                        'event_category': 'engagement',
                        'event_label': 'footer_newsletter'
                    });
                }
            } else {
                // Error from API
                const errorMessage = data.error || data.message || 'Failed to subscribe. Please try again.';
                showMessage(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Newsletter subscription error:', error);
            showMessage('Network error. Please check your connection and try again.', 'error');
        } finally {
            // Re-enable form
            setFormState(form, submitButton, false);
        }
    }
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    function setFormState(form, submitButton, isDisabled) {
        const inputs = form.querySelectorAll('input, button');
        inputs.forEach(input => {
            input.disabled = isDisabled;
        });
        if (submitButton) {
            const buttonText = submitButton.querySelector('.title-18 span:first-child');
            if (buttonText) {
                buttonText.textContent = isDisabled ? 'Submitting...' : 'Confirm';
            }
        }
    }
    function showMessage(message, type = 'info') {
        // Remove existing message if any
        const existingMessage = document.querySelector('.newsletter-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `newsletter-message newsletter-message-${type}`;
        messageDiv.style.cssText = `
            margin-top: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.5;
            animation: slideDown 0.3s ease-out;
        `;
        // Set colors based on type
        switch (type) {
            case 'success':
                messageDiv.style.backgroundColor = '#d4edda';
                messageDiv.style.color = '#155724';
                messageDiv.style.border = '1px solid #c3e6cb';
                break;
            case 'error':
                messageDiv.style.backgroundColor = '#f8d7da';
                messageDiv.style.color = '#721c24';
                messageDiv.style.border = '1px solid #f5c6cb';
                break;
            case 'info':
                messageDiv.style.backgroundColor = '#d1ecf1';
                messageDiv.style.color = '#0c5460';
                messageDiv.style.border = '1px solid #bee5eb';
                break;
        }
        messageDiv.textContent = message;
        // Insert after the form
        const form = document.getElementById('newsletter_form');
        if (form && form.parentNode) {
            form.parentNode.insertBefore(messageDiv, form.nextSibling);
        }
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.style.animation = 'slideUp 0.3s ease-out';
                setTimeout(() => messageDiv.remove(), 300);
            }
        }, 5000);
    }
    // Add CSS animations
    if (!document.getElementById('newsletter-animations')) {
        const style = document.createElement('style');
        style.id = 'newsletter-animations';
        style.textContent = `
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            @keyframes slideUp {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px);
                }
            }
        `;
        document.head.appendChild(style);
    }
})();