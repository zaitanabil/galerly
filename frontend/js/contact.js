/**
 * Galerly - Contact Form Handler
 * Handles contact/support form submission
 */
(function() {
    'use strict';
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initContactForm);
    } else {
        initContactForm();
    }
    function initContactForm() {
        const form = document.getElementById('main_contact_form');
        if (!form) {
            return;
        }
        form.addEventListener('submit', handleContactSubmit);
    }
    async function handleContactSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        const nameInput = form.querySelector('input[name="Name"]');
        const emailInput = form.querySelector('input[name="email"]');
        const issueTypeSelect = form.querySelector('select[name="issueType"]');
        const messageTextarea = form.querySelector('textarea');
        // Validate inputs
        const name = nameInput?.value.trim();
        const email = emailInput?.value.trim();
        const issueType = issueTypeSelect?.value;
        const message = messageTextarea?.value.trim();
        if (!name || !email || !issueType || !message) {
            showMessage('Please fill in all required fields', 'error');
            return;
        }
        // Validate email format
        if (!validateEmail(email)) {
            showMessage('Please enter a valid email address', 'error');
            return;
        }
        // Validate message length
        if (message.length < 10) {
            showMessage('Please provide a more detailed description (min 10 characters)', 'error');
            return;
        }
        // Disable form during submission
        setFormState(form, submitButton, true);
        try {
            // Submit to API
            const response = await fetch(getApiUrl('contact/submit'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    issueType: issueType,
                    message: message
                })
            });
            const data = await response.json();
            if (response.ok) {
                // Success
                showMessage(
                    'Thank you for contacting us! We\'ll get back to you shortly via email.',
                    'success'
                );
                // Reset form after successful submission
                form.reset();
                // Track submission (if analytics enabled)
                if (window.GalerlyConfig?.ENABLE_ANALYTICS && typeof gtag !== 'undefined') {
                    gtag('event', 'contact_submission', {
                        'event_category': 'support',
                        'event_label': issueType
                    });
                }
            } else {
                // Error from API
                const errorMessage = data.error || data.message || 'Failed to submit. Please try again.';
                showMessage(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Contact form error:', error);
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
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = isDisabled;
        });
        if (submitButton) {
            const buttonText = submitButton.querySelector('.title-18 span:first-child');
            if (buttonText) {
                buttonText.textContent = isDisabled ? 'Submitting...' : 'Submit';
            }
        }
    }
    function showMessage(message, type = 'info') {
        // Remove existing message if any
        const existingMessage = document.querySelector('.contact-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `contact-message contact-message-${type}`;
        messageDiv.style.cssText = `
            margin-top: 16px;
            padding: 16px 20px;
            border-radius: 12px;
            font-size: 15px;
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
        const form = document.getElementById('main_contact_form');
        if (form && form.parentNode) {
            form.parentNode.insertBefore(messageDiv, form.nextSibling);
        }
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.style.animation = 'slideUp 0.3s ease-out';
                setTimeout(() => messageDiv.remove(), 300);
            }
        }, 8000);
    }
    // Add CSS animations
    if (!document.getElementById('contact-animations')) {
        const style = document.createElement('style');
        style.id = 'contact-animations';
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