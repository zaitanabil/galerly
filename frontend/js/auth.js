// Auth Page JavaScript - Backend Integration & Enhanced UX
// Uses config.js for API configuration

// Role selection function (no longer needed with dropdown, kept for compatibility)
function selectRole(role) {
    const selectElement = document.querySelector('select[name="role"]');
    if (selectElement) {
        selectElement.value = role;
    }
}

// Tab switching with smooth animations
function switchTab(tab) {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('login_form');
    const registerForm = document.getElementById('register_form');
    
    if (!loginTab || !registerTab || !loginForm || !registerForm) return;
    
    if (tab === 'login') {
        // Update tab button styles
        loginTab.className = 'logo-18 grid-4 hero-11 form-4 container-0';
        loginTab.style.flex = '1';
        loginTab.style.opacity = '1';
        
        registerTab.className = 'logo-18 hero-7';
        registerTab.style.flex = '1';
        registerTab.style.opacity = '0.6';
        
        // Show login, hide register
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
        
        // Focus first input
        const firstInput = loginForm.querySelector('input');
        if (firstInput) setTimeout(() => firstInput.focus(), 100);
        
    } else {
        // Update tab button styles
        registerTab.className = 'logo-18 grid-4 hero-11 form-4 container-0';
        registerTab.style.flex = '1';
        registerTab.style.opacity = '1';
        
        loginTab.className = 'logo-18 hero-7';
        loginTab.style.flex = '1';
        loginTab.style.opacity = '0.6';
        
        // Show register, hide login
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        
        // Focus first input
        const firstInput = registerForm.querySelector('select, input');
        if (firstInput) setTimeout(() => firstInput.focus(), 100);
    }
}

// Helper functions
function validateEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tab state
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('login_form');
    const registerForm = document.getElementById('register_form');
    
    if (loginTab && registerTab && loginForm && registerForm) {
        // Set initial state - login tab active
        loginTab.className = 'logo-18 grid-4 hero-11 form-4 container-0';
        loginTab.style.flex = '1';
        loginTab.style.opacity = '1';
        
        registerTab.className = 'logo-18 hero-7';
        registerTab.style.flex = '1';
        registerTab.style.opacity = '0.6';
    }
    
    // Handle role select display
    const roleSelect = document.getElementById('role_select');
    if (roleSelect) {
        // Store original text for all options on page load
        Array.from(roleSelect.options).forEach(option => {
            if (option.value && option.hasAttribute('data-display')) {
                option.setAttribute('data-original', option.textContent);
            }
        });
        
        // Update selected option display text
        const updateSelectedDisplay = function() {
            const selectedOption = roleSelect.options[roleSelect.selectedIndex];
            if (selectedOption.value && selectedOption.hasAttribute('data-display')) {
                selectedOption.textContent = selectedOption.getAttribute('data-display');
            }
        };
        
        // Restore all options to original text
        const restoreOriginalText = function() {
            Array.from(roleSelect.options).forEach(option => {
                if (option.hasAttribute('data-original')) {
                    option.textContent = option.getAttribute('data-original');
                }
            });
        };
        
        // When user selects an option
        roleSelect.addEventListener('change', updateSelectedDisplay);
        
        // When dropdown is about to open, restore original text
        roleSelect.addEventListener('mousedown', restoreOriginalText);
        roleSelect.addEventListener('focus', restoreOriginalText);
        
        // When dropdown closes, update selected display again
        roleSelect.addEventListener('blur', function() {
            setTimeout(updateSelectedDisplay, 10);
        });
    }
    
    // Login Form Handler with Backend Integration
    const loginFormElement = document.getElementById('login_form');
    if (loginFormElement) {
        loginFormElement.addEventListener('submit', async function(e) {
            e.preventDefault();
            const errorDiv = document.getElementById('loginError');
            hideError(errorDiv);
            
            const email = e.target.email.value.trim();
            const password = e.target.password.value;
            
            // Client-side validation
            if (!email || !password) {
                showError(errorDiv, 'Please fill in all fields.');
                return;
            }
            
            if (!validateEmail(email)) {
                showError(errorDiv, 'Please enter a valid email address.');
                return;
            }
            
            // Show loading state
            const submitBtn = e.target.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
            }
            
            try {
                // Make API call to login endpoint
                const data = await apiRequest('auth/login', {
                    method: 'POST',
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });
                
                // Cookie is set automatically by backend (HttpOnly)
                // Store user data in localStorage for UI state only
                localStorage.setItem(window.GalerlyConfig.USER_DATA_KEY, JSON.stringify(data));
                
                // Redirect based on role - PHOTOGRAPHERS and CLIENTS get different dashboards
                if (data.role === 'photographer') {
                    window.location.href = window.GalerlyConfig.DASHBOARD_PHOTOGRAPHER;
                } else if (data.role === 'client') {
                    window.location.href = 'client-dashboard';  // Client dashboard
                } else {
                    // Default to photographer dashboard for unknown roles
                    window.location.href = window.GalerlyConfig.DASHBOARD_PHOTOGRAPHER;
                }
                
            } catch (error) {
                console.error('Login error:', error);
                showError(errorDiv, error.message || 'Login failed. Please check your credentials.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                }
            }
        });
        
        // Real-time email validation
        const emailInput = loginFormElement.querySelector('#login_email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                const errorDiv = document.getElementById('loginError');
                if (this.value && !validateEmail(this.value)) {
                    this.parentElement.style.borderColor = '#ef4444';
                } else {
                    this.parentElement.style.borderColor = '';
                }
            });
        }
    }
    
    // Register Form Handler with 2-Step Email Verification
    const registerFormElement = document.getElementById('register_form');
    if (registerFormElement) {
        // Track verification state
        let verificationState = {
            step: 1, // 1 = enter email/password, 2 = enter verification code
            email: '',
            password: '',
            role: '',
            verificationToken: ''
        };

        registerFormElement.addEventListener('submit', async function(e) {
            e.preventDefault();
            const errorDiv = document.getElementById('registerError');
            const successDiv = document.getElementById('registerSuccess');
            hideError(errorDiv);
            hideSuccess(successDiv);
            
            const submitBtn = e.target.querySelector('button[type="submit"]');

            // STEP 1: Request verification code
            if (verificationState.step === 1) {
            const role = e.target.role.value;
            const email = e.target.email.value.trim();
            const password = e.target.password.value;
            
            // Client-side validation
            if (!role || !email || !password) {
                showError(errorDiv, 'Please fill in all fields.');
                return;
            }
            
            if (!validateEmail(email)) {
                showError(errorDiv, 'Please enter a valid email address.');
                return;
            }
            
            if (password.length < 8) {
                showError(errorDiv, 'Password must be at least 8 characters long.');
                return;
            }
            
                // Show loading state - update ONLY the text span, preserve SVG
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
                    const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                    if (btnSpans.length > 0) {
                        btnSpans[0].textContent = 'Sending code...';
                    }
                }

                try {
                    // Request verification code from backend
                    const data = await apiRequest('auth/request-verification', {
                        method: 'POST',
                        body: JSON.stringify({ email: email })
                    });

                    // Store form data for step 2
                    verificationState.email = email;
                    verificationState.password = password;
                    verificationState.role = role;
                    verificationState.verificationToken = data.verification_token;
                    verificationState.step = 2;

                    // Update form to show verification code input
                    showVerificationStep();

                    // Show success message
                    showSuccess(successDiv, `Verification code sent to ${email}. Please check your inbox.`);

                } catch (error) {
                    console.error('Verification request error:', error);
                    showError(errorDiv, error.message || 'Failed to send verification code. Please try again.');
                } finally {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                        const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                        if (btnSpans.length > 0) {
                            btnSpans[0].textContent = 'Continue';
                        }
                    }
                }
            }
            // STEP 2: Verify code and complete registration
            else if (verificationState.step === 2) {
                const codeInput = document.getElementById('verification_code');
                const code = codeInput ? codeInput.value.trim() : '';

                // Validation
                if (!code || code.length !== 6) {
                    showError(errorDiv, 'Please enter the 6-digit verification code.');
                    return;
                }

                // Show loading state - update ONLY the text span, preserve SVG
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.6';
                    const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                    if (btnSpans.length > 0) {
                        btnSpans[0].textContent = 'Verifying...';
                    }
            }
            
            try {
                    // Step 2a: Verify the code
                    await apiRequest('auth/verify-email', {
                        method: 'POST',
                        body: JSON.stringify({
                            verification_token: verificationState.verificationToken,
                            code: code
                        })
                    });

                    // Step 2b: Complete registration
                    const username = verificationState.email.split('@')[0].toLowerCase().replace(/[^a-z0-9]/g, '');

                    const registerData = await apiRequest('auth/register', {
                    method: 'POST',
                    body: JSON.stringify({
                            email: verificationState.email,
                        username: username,
                            password: verificationState.password,
                            role: verificationState.role,
                            verification_token: verificationState.verificationToken
                    })
                });
                
                // Show success message
                showSuccess(successDiv, 'Account created successfully! Redirecting...');
                
                // Auto-login after registration
                setTimeout(async () => {
                    try {
                        const loginData = await apiRequest('auth/login', {
                            method: 'POST',
                            body: JSON.stringify({
                                    email: verificationState.email,
                                    password: verificationState.password
                            })
                        });
                        
                        // Cookie is set automatically by backend (HttpOnly)
                        // Store user data in localStorage for UI state only
                            localStorage.setItem(window.GalerlyConfig.USER_DATA_KEY, JSON.stringify(loginData));
                        
                        // Redirect based on role
                            if (loginData.role === 'photographer') {
                            window.location.href = window.GalerlyConfig.DASHBOARD_PHOTOGRAPHER;
                        } else {
                                window.location.href = 'client-dashboard';
                        }
                    } catch (loginError) {
                        console.error('Auto-login error:', loginError);
                            // Reset state and show login form
                            resetVerificationState();
                        setTimeout(() => switchTab('login'), 1000);
                    }
                }, 1500);
                
            } catch (error) {
                    console.error('Verification/Registration error:', error);
                    showError(errorDiv, error.message || 'Invalid verification code. Please try again.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                        const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                        if (btnSpans.length > 0) {
                            btnSpans[0].textContent = 'Verify & Create Account';
                        }
                    }
                }
            }
        });

        // Function to show verification code step
        function showVerificationStep() {
            // Hide initial form fields
            const roleField = registerFormElement.querySelector('[name="role"]').parentElement;
            const emailField = registerFormElement.querySelector('[name="email"]').parentElement;
            const passwordField = registerFormElement.querySelector('[name="password"]').parentElement;

            if (roleField) roleField.style.display = 'none';
            if (emailField) emailField.style.display = 'none';
            if (passwordField) passwordField.style.display = 'none';

            // Create verification code input if it doesn't exist
            let verificationContainer = document.getElementById('verification_container');
            if (!verificationContainer) {
                // Create the wrapper div (same as roleField.parentElement)
                verificationContainer = document.createElement('div');
                verificationContainer.className = 'main-19 main-4';
                verificationContainer.id = 'verification_container';

                // Create the input element - NO custom inline styles, let CSS handle it
                verificationContainer.innerHTML = `
                    <input 
                        placeholder="Enter 6-digit verification code*"
                        type="text"
                        class="footer-19 footer-4"
                        id="verification_code"
                        name="verification_code"
                        maxlength="6"
                        pattern="[0-9]{6}"
                        inputmode="numeric"
                        required
                        autocomplete="off"
                    />
                `;

                // Insert after the password field (before error messages)
                if (passwordField && passwordField.parentElement) {
                    passwordField.parentElement.insertBefore(verificationContainer, passwordField.nextSibling);
                }

                // Add instruction text before error messages
                const errorDiv = document.getElementById('registerError');
                if (errorDiv) {
                    const instructionDiv = document.createElement('div');
                    instructionDiv.id = 'verification_instruction';
                    instructionDiv.style.cssText = 'margin: 16px 0 8px 0; text-align: center; font-size: 14px; color: var(--text-secondary, #6E6E73);';
                    instructionDiv.innerHTML = `We sent a code to <strong>${verificationState.email}</strong>. <a href="#" id="resend_code_link" style="color: var(--button-primary-fill, #007AFF); text-decoration: none; font-weight: 500;">Resend code</a>`;
                    errorDiv.parentElement.insertBefore(instructionDiv, errorDiv);

                    // Add resend code handler
                    setTimeout(() => {
                        const resendLink = document.getElementById('resend_code_link');
                        if (resendLink) {
                            resendLink.addEventListener('click', async function(e) {
                                e.preventDefault();
                                this.textContent = 'Sending...';

                                try {
                                    const data = await apiRequest('auth/request-verification', {
                                        method: 'POST',
                                        body: JSON.stringify({ email: verificationState.email })
                                    });

                                    verificationState.verificationToken = data.verification_token;

                                    const successDiv = document.getElementById('registerSuccess');
                                    showSuccess(successDiv, 'New verification code sent!');

                                    this.textContent = 'Code sent!';
                                    setTimeout(() => {
                                        this.textContent = 'Resend code';
                                    }, 3000);

                                } catch (error) {
                                    console.error('Resend error:', error);
                                    const errorDiv = document.getElementById('registerError');
                                    showError(errorDiv, 'Failed to resend code. Please try again.');
                                    this.textContent = 'Resend code';
                                }
                            });
                        }
                    }, 100);
                }

                // Auto-focus verification code input
                setTimeout(() => {
                    const codeInput = document.getElementById('verification_code');
                    if (codeInput) codeInput.focus();
                }, 100);
            }

            verificationContainer.style.display = '';

            // Update submit button text to ONLY change the first span (the text one, not the SVG)
            const submitBtn = registerFormElement.querySelector('button[type="submit"]');
            if (submitBtn) {
                const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                if (btnSpans.length > 0) {
                    // First span is the text, second is the SVG container
                    btnSpans[0].textContent = 'Verify & Create Account';
                }
            }
        }

        // Function to reset verification state
        function resetVerificationState() {
            verificationState = {
                step: 1,
                email: '',
                password: '',
                role: '',
                verificationToken: ''
            };

            // Show original form fields
            const roleField = registerFormElement.querySelector('[name="role"]').parentElement;
            const emailField = registerFormElement.querySelector('[name="email"]').parentElement;
            const passwordField = registerFormElement.querySelector('[name="password"]').parentElement;

            if (roleField) roleField.style.display = '';
            if (emailField) emailField.style.display = '';
            if (passwordField) passwordField.style.display = '';

            // Hide verification container
            const verificationContainer = document.getElementById('verification_container');
            if (verificationContainer) {
                verificationContainer.style.display = 'none';
            }

            // Remove instruction text
            const instructionDiv = document.getElementById('verification_instruction');
            if (instructionDiv) {
                instructionDiv.remove();
            }

            // Reset submit button text to ONLY change the first span (the text one, not the SVG)
            const submitBtn = registerFormElement.querySelector('button[type="submit"]');
            if (submitBtn) {
                const btnSpans = submitBtn.querySelectorAll('.title-18 span');
                if (btnSpans.length > 0) {
                    // First span is the text, second is the SVG container
                    btnSpans[0].textContent = 'Continue';
                }
            }

            // Clear form
            registerFormElement.reset();
        }

        // Add "Back" button functionality when in verification step
        registerFormElement.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && verificationState.step === 2) {
                resetVerificationState();
            }
        });
        
        // Real-time email validation
        const emailInput = registerFormElement.querySelector('#register_email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                if (this.value && !validateEmail(this.value)) {
                    this.parentElement.style.borderColor = '#ef4444';
                } else {
                    this.parentElement.style.borderColor = '';
                }
            });
        }
    }
    
    // Button animations with GSAP (if available)
    if (typeof gsap !== 'undefined') {
        // Submit button animations
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
            btn.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                    gsap.to(this, {
                        scale: 1.02,
                        duration: 0.4,
                        ease: 'power2.out'
                    });
                }
            });
            
            btn.addEventListener('mouseleave', function() {
                gsap.to(this, {
                    scale: 1,
                    duration: 0.4,
                    ease: 'power2.out'
                });
            });
        });

        // Tab button animations
        document.querySelectorAll('#loginTab, #registerTab').forEach(tab => {
            tab.addEventListener('click', function() {
                gsap.to(this, {
                    scale: 0.98,
                    duration: 0.1,
                    ease: 'power2.out',
                    onComplete: () => {
                        gsap.to(this, {
                            scale: 1,
                            duration: 0.3,
                            ease: 'elastic.out(1, 0.5)'
                        });
                    }
                });
            });
        });
    }
    
    // Auto-clear errors when user starts typing
    document.querySelectorAll('input, select, textarea').forEach(input => {
        input.addEventListener('input', function() {
            const form = this.closest('form');
            if (form) {
                const errorDiv = form.querySelector('.error-message');
                if (errorDiv && errorDiv.style.display === 'block') {
                    hideError(errorDiv);
                }
            }
        });
    });
});

// Add screen reader only class
const style = document.createElement('style');
style.textContent = `
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
    }
`;
document.head.appendChild(style);
