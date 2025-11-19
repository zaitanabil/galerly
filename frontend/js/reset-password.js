// Helper functions
function validateEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function showError(errorDiv, message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => hideError(errorDiv), 5000);
}

function hideError(errorDiv) {
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';
}

function showSuccess(successDiv, message) {
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    successDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideSuccess(successDiv) {
    successDiv.style.display = 'none';
    successDiv.textContent = '';
}

// Get token from URL
function getTokenFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('token');
}

// Show reset form (with new password fields)
function showResetForm() {
    const form = document.getElementById('reset_password_form');
    
    // Update title and description
    const titleDiv = form.querySelector('.feature-11');
    const descDiv = form.querySelector('p');
    
    if (titleDiv) titleDiv.textContent = 'Create new password';
    if (descDiv) descDiv.textContent = 'Enter your new password below. It must be at least 8 characters long.';
    
    // Replace email field with password fields
    const emailFieldContainer = form.querySelector('.main-19.main-4').parentElement;
    emailFieldContainer.innerHTML = `
        <div style="margin-bottom: 16px;">
            <div class="main-19 main-4">
                <input placeholder="New password*" type="password"
                    autocomplete="new-password" required
                    class="footer-19 footer-4" id="new_password"
                    name="password" style="padding: 18px 20px; font-size: 16px;" />
            </div>
        </div>
        <div>
            <div class="main-19 main-4">
                <input placeholder="Confirm password*" type="password"
                    autocomplete="new-password" required
                    class="footer-19 footer-4" id="confirm_password"
                    name="confirmPassword" style="padding: 18px 20px; font-size: 16px;" />
            </div>
        </div>
    `;
    
    // Update button text
    const submitBtn = form.querySelector('button[type="submit"]');
    const btnSpans = submitBtn.querySelectorAll('.title-18 span');
    if (btnSpans.length > 0) {
        btnSpans[0].textContent = 'Reset Password';
    }
    
    return true;
}

// Reset Password Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const resetForm = document.getElementById('reset_password_form');
    const token = getTokenFromUrl();
    
    // If token exists, show reset form instead of request form
    if (token) {
        showResetForm();
    }
    
    if (resetForm) {
        resetForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const errorDiv = document.getElementById('resetError');
            const successDiv = document.getElementById('resetSuccess');
            hideError(errorDiv);
            hideSuccess(successDiv);
            
            const submitBtn = e.target.querySelector('button[type="submit"]');
            
            // Handle token-based reset (new password)
            if (token) {
                const newPassword = document.getElementById('new_password').value;
                const confirmPassword = document.getElementById('confirm_password').value;
                
                // Validation
                if (!newPassword || !confirmPassword) {
                    showError(errorDiv, 'Please fill in all fields.');
                    return;
                }
                
                if (newPassword !== confirmPassword) {
                    showError(errorDiv, 'Passwords do not match.');
                    return;
                }
                
                if (!validatePassword(newPassword)) {
                    showError(errorDiv, 'Password must be at least 8 characters long.');
                    return;
                }
                
                // Show loading state
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.6';
                    const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                    if (btnSpans.length > 0) {
                        btnSpans[0].textContent = 'Resetting...';
                    }
                }
                
                try {
                    // Call reset password endpoint
                    await apiRequest('auth/reset-password', {
                        method: 'POST',
                        body: JSON.stringify({
                            token: token,
                            password: newPassword
                        })
                    });
                    
                    // Show success message
                    showSuccess(successDiv, 'Password reset successful! Redirecting to login...');
                    
                    // Redirect to login after 2 seconds
                    setTimeout(() => {
                        window.location.href = 'auth';
                    }, 2000);
                    
                } catch (error) {
                    console.error('Password reset error:', error);
                    showError(errorDiv, error.message || 'Failed to reset password. The link may have expired.');
                    
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                        const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                        if (btnSpans.length > 0) {
                            btnSpans[0].textContent = 'Reset Password';
                        }
                    }
                }
                
            } else {
                // Handle request reset link (email)
                const email = e.target.email.value.trim();
            
            // Validation
            if (!email) {
                showError(errorDiv, 'Please enter your email address.');
                return;
            }
            
            if (!validateEmail(email)) {
                showError(errorDiv, 'Please enter a valid email address.');
                return;
            }
            
                // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
                const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                if (btnSpans.length > 0) {
                    btnSpans[0].textContent = 'Sending...';
                }
            }
            
            try {
                // Call password reset endpoint
                await apiRequest('auth/forgot-password', {
                    method: 'POST',
                    body: JSON.stringify({ email: email })
                });
                
                // Show success message
                showSuccess(successDiv, 'Password reset link sent! Please check your email. Redirecting...');
                
                // Clear form
                e.target.reset();
                
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    window.location.href = 'auth';
                }, 3000);
                
            } catch (error) {
                console.error('Password reset error:', error);
                showError(errorDiv, error.message || 'Failed to send reset link. Please try again.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                    const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                    if (btnSpans.length > 0) {
                        btnSpans[0].textContent = 'Send Reset Link';
                        }
                    }
                }
            }
        });

        // Real-time validation for email input (only if no token)
        if (!token) {
        const emailInput = resetForm.querySelector('#reset_email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                if (this.value && !validateEmail(this.value)) {
                    this.parentElement.style.borderColor = '#ef4444';
                } else {
                    this.parentElement.style.borderColor = '';
                }
            });

            // Auto-clear errors when user starts typing
            emailInput.addEventListener('input', function() {
                const errorDiv = document.getElementById('resetError');
                if (errorDiv && errorDiv.style.display === 'block') {
                    hideError(errorDiv);
                }
            });
            }
        } else {
            // Real-time validation for password fields
            const newPasswordInput = document.getElementById('new_password');
            const confirmPasswordInput = document.getElementById('confirm_password');
            
            if (confirmPasswordInput) {
                confirmPasswordInput.addEventListener('blur', function() {
                    const newPassword = newPasswordInput ? newPasswordInput.value : '';
                    if (this.value && this.value !== newPassword) {
                        this.parentElement.style.borderColor = '#ef4444';
                    } else {
                        this.parentElement.style.borderColor = '';
                    }
                });
                
                confirmPasswordInput.addEventListener('input', function() {
                    const errorDiv = document.getElementById('resetError');
                    if (errorDiv && errorDiv.style.display === 'block') {
                        hideError(errorDiv);
                    }
                });
            }
        }
    }

    // GSAP animations (if available)
    if (typeof gsap !== 'undefined') {
        // Submit button animations
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                    gsap.to(this, {
                        scale: 1.02,
                        duration: 0.4,
                        ease: 'power2.out'
                    });
                }
            });
            
            submitBtn.addEventListener('mouseleave', function() {
                gsap.to(this, {
                    scale: 1,
                    duration: 0.4,
                    ease: 'power2.out'
                });
            });
        }
    }
});