// New Gallery Form Functionality
// Uses config.js for API configuration

// Global array to store client emails
let clientEmails = [];

/**
 * Populate expiration options based on photographer's plan
 * FREE PLAN: 1-7 days MAXIMUM (NO "NEVER" OPTION)
 * PLUS PLAN: 30 days - 1 year + Never
 * PRO PLAN: 30 days - 1 year + Never
 */
async function populateExpiryOptionsNewGallery() {
    const expirySelect = document.querySelector('[name="expiry"]');
    if (!expirySelect) return;
    
    try {
        // Get current user's subscription info
        const response = await apiRequest('subscription/usage');
        const plan = response?.plan;
        
        // Define expiry options per plan
        const expiryOptions = {
            free: [
                // ⚠️ FREE PLAN RESTRICTION: MAXIMUM 7 DAYS (HARD LIMIT)
                { value: '1', label: '1 day' },
                { value: '3', label: '3 days' },
                { value: '7', label: '7 days (Maximum)' }
            ],
            plus: [
                { value: 'never', label: 'Never' },
                { value: '30', label: '30 days' },
                { value: '60', label: '60 days' },
                { value: '90', label: '90 days' },
                { value: '180', label: '6 months' },
                { value: '365', label: '1 year' }
            ],
            pro: [
                { value: 'never', label: 'Never' },
                { value: '30', label: '30 days' },
                { value: '60', label: '60 days' },
                { value: '90', label: '90 days' },
                { value: '180', label: '6 months' },
                { value: '365', label: '1 year' }
            ]
        };
        
        // Get options for current plan (default to free)
        const options = expiryOptions[plan] || expiryOptions.free;
        
        // Clear existing options
        expirySelect.innerHTML = '';
        
        // Populate options
        options.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option.value;
            optionEl.textContent = option.label;
            expirySelect.appendChild(optionEl);
        });
        
        // Set default value based on plan
        if (plan === 'free') {
            // Default to 7 days (maximum) for free users
            expirySelect.value = '7';
        } else {
            // Default to "never" for paid users
            expirySelect.value = 'never';
        }
        
        // Show restriction notice for free users
        if (plan === 'free') {
            const expiryField = expirySelect.closest('.settings-field');
            if (expiryField) {
                const existingNotice = expiryField.querySelector('.plan-restriction-notice');
                if (!existingNotice) {
                    const notice = document.createElement('p');
                    notice.className = 'plan-restriction-notice';
                    notice.style.cssText = `
                        font-size: 13px;
                        color: var(--color-red, #FF3B30);
                        margin-top: 8px;
                        padding: 8px 12px;
                        background: rgba(255, 59, 48, 0.05);
                        border-radius: 32px;
                        border: 1px solid rgba(255, 59, 48, 0.2);
                        line-height: 1.4;
                        font-weight: 500;
                    `;
                    notice.innerHTML = `<strong>Free Plan Limitation:</strong> All galleries expire after 7 days maximum. Upgrade to <strong>Plus</strong> or <strong>Pro</strong> for unlimited gallery lifetime and longer expiration options.`;
                    expiryField.appendChild(notice);
                }
            }
        }
        
    } catch (error) {
        console.error('Error loading expiry options:', error);
        // Fallback to basic free plan options (1-7 days max)
        expirySelect.innerHTML = `
            <option value="1">1 day</option>
            <option value="3">3 days</option>
            <option value="7">7 days (Maximum)</option>
        `;
        expirySelect.value = '7';
    }
}

/**
 * Add a new client email to the list
 */
function addClientEmail() {
    const input = document.getElementById('newClientEmail');
    const email = input.value.trim().toLowerCase();
    
    // Validate email
    if (!email) {
        return; // Silently ignore empty input
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address');
        input.focus();
        return;
    }
    
    // Check for duplicates
    if (clientEmails.includes(email)) {
        alert('This email is already added');
        input.value = '';
        input.focus();
        return;
    }
    
    // Add to array
    clientEmails.push(email);
    
    // Clear input and focus for next entry
    input.value = '';
    input.focus();
    
    // Re-render list
    renderClientEmailsList();
    
    // Show brief success indicator
    input.style.borderColor = '#4CAF50';
    setTimeout(() => {
        input.style.borderColor = '';
    }, 500);
}

/**
 * Remove a client email from the list
 */
function removeClientEmail(email) {
    clientEmails = clientEmails.filter(e => e !== email);
    renderClientEmailsList();
}

/**
 * Render the list of client emails
 */
function renderClientEmailsList() {
    const container = document.getElementById('clientEmailsList');
    if (!container) return;
    
    if (clientEmails.length === 0) {
        container.innerHTML = '<p style="opacity: 0.6; font-size: 14px; padding: 12px 0; font-family: var(--pp-neue-font);">No clients added yet. Add client emails below to share this gallery.</p>';
        return;
    }
    
    container.innerHTML = clientEmails.map(email => `
        <div class="client-email-item" style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--background-secondary, #F5F5F7);
            border-radius: var(--border-radius-m, 8px);
            margin-bottom: 8px;
            animation: slideIn 0.2s ease-out;
        ">
            <span style="font-size: 14px; color: var(--text-primary); font-family: var(--pp-neue-font);">${escapeHtml(email)}</span>
            <button 
                type="button" 
                onclick="removeClientEmail('${email}')" 
                class="btn-text-danger"
                style="
                    background: none;
                    border: none;
                    color: var(--color-error, #FF3B30);
                    cursor: pointer;
                    padding: 6px 12px;
                    font-size: 13px;
                    font-family: var(--pp-neue-font);
                    font-weight: 500;
                    border-radius: 6px;
                    transition: background 0.2s;
                "
                onmouseover="this.style.background='rgba(255, 59, 48, 0.1)'"
                onmouseout="this.style.background='none'"
            >
                Remove
            </button>
        </div>
    `).join('');
}

/**
 * Handle Enter key press in client email input
 */
function handleClientEmailKeyPress(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent form submission
        addClientEmail();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally available
window.addClientEmail = addClientEmail;
window.removeClientEmail = removeClientEmail;
window.handleClientEmailKeyPress = handleClientEmailKeyPress;

// Form submission
document.addEventListener('DOMContentLoaded', function() {
    // Populate expiry options based on user's plan
    populateExpiryOptionsNewGallery();
    
    const newGalleryForm = document.getElementById('new_gallery_form');
    
    if (!newGalleryForm) {
        console.error('Form not found');
        return;
    }

    newGalleryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            name: newGalleryForm.querySelector('[name="galleryName"]').value,
            clientName: newGalleryForm.querySelector('[name="clientName"]').value,
            clientEmails: clientEmails,  // Send array of client emails
            description: newGalleryForm.querySelector('[name="description"]').value,
            privacy: 'private',
            allowDownload: newGalleryForm.querySelector('[name="allowDownloads"]').checked,
            allowComments: newGalleryForm.querySelector('[name="allowComments"]').checked,
            expiry: newGalleryForm.querySelector('[name="expiry"]').value
        };
    
    // Show loading state
    const submitButton = newGalleryForm.querySelector('button[type="submit"]');
    const originalText = submitButton.querySelector('span').textContent;
    submitButton.querySelector('span').textContent = 'Creating...';
    submitButton.disabled = true;
    
    try {
            // API call to create gallery
            const data = await apiRequest('galleries', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
            // Show success and redirect
            alert('Gallery created successfully! Redirecting...');
        
        // Redirect to the new gallery after a short delay
        setTimeout(() => {
                window.location.href = `gallery?id=${data.id || data.galleryId}`;
            }, 500);
        
    } catch (error) {
        console.error('Error creating gallery:', error);
            alert(error.message || 'Failed to create gallery. Please try again.');
        
        // Reset button
        submitButton.querySelector('span').textContent = originalText;
        submitButton.disabled = false;
    }
});
});

