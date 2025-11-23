/**
 * Billing and Subscription Management
 */

// Initialize Stripe (will be loaded from CDN)
let stripe = null;
let stripeElements = null;
let stripeCardElement = null;

// Load Stripe.js
function loadStripe() {
    return new Promise((resolve, reject) => {
        if (window.Stripe) {
            stripe = window.Stripe(window.GalerlyConfig.STRIPE_PUBLISHABLE_KEY);
            resolve(stripe);
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://js.stripe.com/v3/';
        script.onload = () => {
            stripe = window.Stripe(window.GalerlyConfig.STRIPE_PUBLISHABLE_KEY);
            resolve(stripe);
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// ==========================================
// REUSABLE MODAL UTILITY FUNCTIONS
// ==========================================

// Base modal styles
const MODAL_BASE_STYLES = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.2s ease;
`;

const MODAL_CONTENT_STYLES = `
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 40px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    animation: slideUp 0.3s ease;
`;

const MODAL_ANIMATIONS = `
    <style>
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { 
                opacity: 0;
                transform: translateY(20px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
`;

// Show custom alert modal (replaces alert())
function showAlert(message, title = 'Notice', icon = 'ℹ️') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.style.cssText = MODAL_BASE_STYLES;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = MODAL_CONTENT_STYLES + 'text-align: center;';
        
        modalContent.innerHTML = `
            ${MODAL_ANIMATIONS}
            <div style="font-size: 3rem; margin-bottom: 16px;">${icon}</div>
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.75rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 16px 0;
                letter-spacing: -0.02em;
            ">${title}</h2>
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1rem;
                color: #6B6B6B;
                line-height: 1.6;
                margin: 0 0 24px 0;
                white-space: pre-line;
            ">${message}</p>
            <button id="alert-ok-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #0066CC;
                color: white;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#0055AA'" onmouseout="this.style.background='#0066CC'">
                OK
            </button>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        const closeModal = () => {
            modal.remove();
            resolve();
        };
        
        modalContent.querySelector('#alert-ok-btn').addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    });
}

// Show custom confirm modal (replaces confirm())
function showConfirm(message, title = 'Confirm', confirmText = 'Confirm', cancelText = 'Cancel') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.style.cssText = MODAL_BASE_STYLES;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = MODAL_CONTENT_STYLES;
        
        modalContent.innerHTML = `
            ${MODAL_ANIMATIONS}
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.75rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 16px 0;
                letter-spacing: -0.02em;
            ">${title}</h2>
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1rem;
                color: #6B6B6B;
                line-height: 1.6;
                margin: 0 0 32px 0;
                white-space: pre-line;
            ">${message}</p>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button id="confirm-cancel-btn" style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    padding: 12px 32px;
                    background: #F5F5F7;
                    color: #1D1D1F;
                    border: none;
                    border-radius: 980px;
                    cursor: pointer;
                    font-weight: 500;
                    font-size: 1rem;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
                    ${cancelText}
                </button>
                <button id="confirm-ok-btn" style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    padding: 12px 32px;
                    background: #0066CC;
                    color: white;
                    border: none;
                    border-radius: 980px;
                    cursor: pointer;
                    font-weight: 500;
                    font-size: 1rem;
                    transition: all 0.2s ease;
                " onmouseover="this.style.background='#0055AA'" onmouseout="this.style.background='#0066CC'">
                    ${confirmText}
                </button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        const closeModal = (result) => {
            modal.remove();
            resolve(result);
        };
        
        modalContent.querySelector('#confirm-ok-btn').addEventListener('click', () => closeModal(true));
        modalContent.querySelector('#confirm-cancel-btn').addEventListener('click', () => closeModal(false));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal(false);
        });
    });
}

// Show custom error alert
function showError(message, title = 'Error') {
    return showAlert(message, title, '✕');
}

// Show custom success alert
function showSuccess(message, title = 'Success') {
    return showAlert(message, title, '✓');
}

// Open URL in branded modal iframe (replaces window.open for PDFs)
function openInModal(url, title = 'Document') {
    const modal = document.createElement('div');
    modal.style.cssText = MODAL_BASE_STYLES;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 24px;
        max-width: 90vw;
        max-height: 90vh;
        width: 900px;
        height: 80vh;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.3s ease;
        display: flex;
        flex-direction: column;
    `;
    
    modalContent.innerHTML = `
        ${MODAL_ANIMATIONS}
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        ">
            <h3 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.25rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0;
            ">${title}</h3>
            <button id="modal-close-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 8px 20px;
                background: #F5F5F7;
                color: #1D1D1F;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 0.875rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
                Close
            </button>
        </div>
        <iframe 
            src="${url}" 
            style="
                width: 100%;
                height: 100%;
                border: none;
                border-radius: 12px;
                background: white;
            "
        ></iframe>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    const closeModal = () => modal.remove();
    
    modalContent.querySelector('#modal-close-btn').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
}

// Load subscription data
async function loadSubscription() {
    try {
        const data = await window.apiRequest('billing/subscription');
        return data;
    } catch (error) {
        console.error('Error loading subscription:', error);
        throw error;
    }
}

// Load usage data
async function loadUsage() {
    try {
        const data = await window.apiRequest('subscription/usage');
        return data;
    } catch (error) {
        console.error('Error loading usage:', error);
        throw error;
    }
}

// Load billing history
async function loadBillingHistory() {
    try {
        const data = await window.apiRequest('billing/history');
        return data;
    } catch (error) {
        console.error('Error loading billing history:', error);
        throw error;
    }
}

// Change plan between paid plans (Business <-> Professional)
async function changePlan(planId) {
    try {
        const data = await window.apiRequest('billing/subscription/change-plan', {
            method: 'POST',
            body: JSON.stringify({ plan: planId })
        });
        return data;
    } catch (error) {
        console.error('Error changing plan:', error);
        throw error;
    }
}

// Create checkout session
async function createCheckoutSession(planId) {
    try {
        const data = await window.apiRequest('billing/checkout', {
            method: 'POST',
            body: JSON.stringify({ plan: planId })
        });
        return data;
    } catch (error) {
        console.error('Error creating checkout session:', error);
        throw error;
    }
}

// Check downgrade limits
async function checkDowngradeLimits(targetPlan = 'free') {
    try {
        const data = await window.apiRequest(`billing/subscription/check-downgrade?target_plan=${targetPlan}`);
        return data;
    } catch (error) {
        console.error('Error checking downgrade limits:', error);
        throw error;
    }
}

// Downgrade subscription with selected galleries to delete
async function downgradeSubscription(galleriesToDelete = []) {
    try {
        const data = await window.apiRequest('billing/subscription/downgrade', {
            method: 'POST',
            body: JSON.stringify({ galleries_to_delete: galleriesToDelete })
        });
        return data;
    } catch (error) {
        console.error('Error downgrading subscription:', error);
        throw error;
    }
}

// Cancel subscription - Show custom modal
async function cancelSubscription() {
    showCancelSubscriptionModal();
}

// Show cancel subscription modal
function showCancelSubscriptionModal() {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
    `;
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <style>
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from { 
                    opacity: 0;
                    transform: translateY(20px);
                }
                to { 
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        </style>
        <h2 style="
            font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.75rem;
            font-weight: 600;
            color: #1D1D1F;
            margin: 0 0 16px 0;
            letter-spacing: -0.02em;
        ">Cancel Subscription</h2>
        
        <p style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1rem;
            color: #6B6B6B;
            line-height: 1.6;
            margin: 0 0 32px 0;
        ">
            Your subscription will be canceled at the end of your billing period. 
            You'll continue to have access to all features until then.
        </p>
        
        <div style="
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        ">
            <button id="cancel-modal-cancel-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #F5F5F7;
                color: #1D1D1F;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
                Keep Subscription
            </button>
            <button id="cancel-modal-confirm-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #FF6F61;
                color: white;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#E65F51'" onmouseout="this.style.background='#FF6F61'">
                Cancel Subscription
            </button>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Keep subscription button
    modalContent.querySelector('#cancel-modal-cancel-btn').addEventListener('click', () => {
        modal.remove();
    });
    
    // Confirm cancel button
    modalContent.querySelector('#cancel-modal-confirm-btn').addEventListener('click', async () => {
        const confirmBtn = modalContent.querySelector('#cancel-modal-confirm-btn');
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Processing...';
        confirmBtn.style.opacity = '0.6';
        
        try {
            await window.apiRequest('billing/subscription/cancel', {
                method: 'POST'
            });
            
            // Show success message
            modalContent.innerHTML = `
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 3rem; margin-bottom: 16px;">✓</div>
                    <h3 style="
                        font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 1.5rem;
                        font-weight: 600;
                        color: #1D1D1F;
                        margin: 0 0 12px 0;
                    ">Subscription Canceled</h3>
                    <p style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 1rem;
                        color: #6B6B6B;
                        line-height: 1.6;
                        margin: 0;
                    ">
                        You'll continue to have access until the end of your billing period.
                    </p>
                </div>
            `;
            
            setTimeout(() => {
                modal.remove();
                location.reload();
            }, 2000);
        } catch (error) {
            console.error('Error canceling subscription:', error);
            
            // Show error message
            modalContent.innerHTML = `
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 3rem; margin-bottom: 16px; color: #FF3B30;">✕</div>
                    <h3 style="
                        font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 1.5rem;
                        font-weight: 600;
                        color: #1D1D1F;
                        margin: 0 0 12px 0;
                    ">Cancellation Failed</h3>
                    <p style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 1rem;
                        color: #6B6B6B;
                        line-height: 1.6;
                        margin: 0 0 24px 0;
                    ">
                        ${error.message || 'An error occurred. Please try again.'}
                    </p>
                    <button onclick="this.closest('[style*=\\'position: fixed\\']').remove()" style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        padding: 12px 32px;
                        background: #F5F5F7;
                        color: #1D1D1F;
                        border: none;
                        border-radius: 980px;
                        cursor: pointer;
                        font-weight: 500;
                        font-size: 1rem;
                    ">Close</button>
                </div>
            `;
        }
    });
}

// Show modal for selecting galleries to delete before downgrade
function showDowngradeSelectionModal(checkData) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center; padding: 20px;';
    
    const issues = checkData.issues || [];
    const galleries = checkData.galleries || [];
    
    let modalContent = `
        <div style="background: white; border-radius: 12px; max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 32px; position: relative;">
            <h2 style="margin-top: 0; margin-bottom: 24px; font-size: 24px; font-weight: 700;">Downgrade to Starter Plan</h2>
            
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <p style="margin: 0 0 12px 0; font-weight: 600;">⚠️ You need to free up resources before downgrading:</p>
                <ul style="margin: 0; padding-left: 20px;">
                    ${issues.map(issue => `<li style="margin-bottom: 8px;">${issue.message}</li>`).join('')}
                </ul>
            </div>
            
            <div style="margin-bottom: 24px;">
                <h3 style="margin-bottom: 16px; font-size: 18px; font-weight: 600;">Select galleries to delete:</h3>
                <div id="gallery-selection-list" style="max-height: 400px; overflow-y: auto;">
    `;
    
    galleries.forEach(gallery => {
        const date = new Date(gallery.created_at).toLocaleDateString();
        modalContent += `
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 4px;">${gallery.name}</div>
                    <div style="font-size: 14px; color: #6b7280;">
                        ${gallery.photo_count} photos • ${gallery.storage_gb.toFixed(2)} GB • Created ${date}
                    </div>
                </div>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" value="${gallery.id}" class="gallery-checkbox" style="width: 20px; height: 20px; margin-right: 8px;">
                    <span>Delete</span>
                </label>
            </div>
        `;
    });
    
    modalContent += `
                </div>
            </div>
            
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button id="cancel-downgrade-btn" style="padding: 12px 24px; background: #f3f4f6; color: #374151; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    Cancel
                </button>
                <button id="confirm-downgrade-btn" style="padding: 12px 24px; background: #ef4444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    Downgrade & Delete Selected
                </button>
            </div>
        </div>
    `;
    
    modal.innerHTML = modalContent;
    document.body.appendChild(modal);
    
    // Cancel button
    modal.querySelector('#cancel-downgrade-btn').addEventListener('click', () => {
        modal.remove();
    });
    
    // Confirm button
    modal.querySelector('#confirm-downgrade-btn').addEventListener('click', async () => {
        const selectedGalleries = Array.from(modal.querySelectorAll('.gallery-checkbox:checked')).map(cb => cb.value);
        
        if (selectedGalleries.length === 0) {
            showAlert('Please select at least one gallery to delete.', 'Selection Required', '⚠️');
            return;
        }
        
        // Verify selection meets requirements
        let totalStorageToFree = 0;
        let galleriesToDeleteCount = 0;
        
        selectedGalleries.forEach(galleryId => {
            const gallery = galleries.find(g => g.id === galleryId);
            if (gallery) {
                totalStorageToFree += gallery.storage_gb;
                galleriesToDeleteCount++;
            }
        });
        
        const storageIssue = issues.find(i => i.type === 'storage');
        const galleryIssue = issues.find(i => i.type === 'galleries');
        
        let canProceed = true;
        let warningMessage = '';
        
        if (storageIssue && totalStorageToFree < storageIssue.excess) {
            canProceed = false;
            warningMessage += `You need to free up at least ${storageIssue.excess} GB, but selected galleries only free ${totalStorageToFree.toFixed(2)} GB. `;
        }
        
        if (galleryIssue && galleriesToDeleteCount < galleryIssue.excess) {
            canProceed = false;
            warningMessage += `You need to delete at least ${galleryIssue.excess} gallery(ies), but only selected ${galleriesToDeleteCount}. `;
        }
        
        if (!canProceed) {
            showAlert(warningMessage + 'Please select more galleries.', 'Cannot Proceed', '⚠️');
            return;
        }
        
        // Confirm deletion
        const confirmed = await showConfirm(
            `Are you sure you want to delete ${selectedGalleries.length} gallery(ies) and schedule downgrade to Starter plan?\n\nYou will be downgraded at the end of your current billing period.\n\nThis action cannot be undone.`,
            'Confirm Downgrade & Deletion',
            'Delete & Downgrade',
            'Cancel'
        );
        if (!confirmed) {
            return;
        }
        
        // Disable button
        const confirmBtn = modal.querySelector('#confirm-downgrade-btn');
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Processing...';
        
        try {
            const result = await downgradeSubscription(selectedGalleries);
            await showSuccess(`Downgrade scheduled successfully!\n\n${result.message || `Deleted ${result.deleted_galleries} galleries and ${result.deleted_photos} photos. Freed ${result.freed_storage_gb} GB.\n\nYou will be downgraded to Starter plan at the end of your current billing period.`}`);
            modal.remove();
            location.reload();
        } catch (error) {
            console.error('Error downgrading:', error);
            showError('Failed to downgrade: ' + (error.message || 'Unknown error'), 'Downgrade Failed');
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Downgrade & Delete Selected';
        }
    });
}

// Display subscription info
async function displaySubscription(subscription) {
    const container = document.getElementById('subscription-info');
    if (!container) return;
    
    const plan = subscription.plan_details || {};
    const currentPlan = subscription.plan || 'free';
        const status = currentPlan === 'free' ? 'free' : (subscription.status || 'active');
    
    // Check for pending plan change
    const pendingPlan = subscription.pending_plan;
    const pendingPlanChangeAt = subscription.pending_plan_change_at;
    const pendingPlanName = pendingPlan ? (pendingPlan === 'free' ? 'Starter' : pendingPlan === 'plus' ? 'Plus' : 'Pro') : null;
    
    let html = `
        <div style="
            display: flex;
            align-items: baseline;
            gap: 16px;
            margin-bottom: 24px;
        ">
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 3rem;
                font-weight: 800;
                line-height: 1;
                color: #1D1D1F;
                margin: 0;
                letter-spacing: -0.02em;
            ">${plan.name || (currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1))}</h2>
            ${pendingPlan ? `<span style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1rem;
                color: #86868B;
                font-weight: 500;
            ">→ ${pendingPlanName}</span>` : ''}
        </div>
        <p style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 0.9375rem;
            color: #86868B;
            margin-bottom: 32px;
        ">
            <span style="color: ${status === 'active' ? '#34C759' : status === 'canceled' ? '#FF6F61' : '#86868B'}; font-weight: 500;">
                ${status === 'free' ? 'Starter Plan' : status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        </p>
    `;
    
    // Check for pending refund
    try {
        const refundStatus = await window.apiRequest('billing/refund/status');
        
        if (refundStatus && refundStatus.has_pending_refund) {
            html += `
                <div style="
                    background: #FFF9E6;
                    border: 1px solid #FFE082;
                    border-radius: 16px;
                    padding: 20px;
                    margin-bottom: 32px;
                ">
                    <p style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 0.9375rem;
                        color: #856404;
                        margin: 0 0 8px 0;
                        font-weight: 600;
                    ">Refund Request ${refundStatus.status === 'approved' ? 'Approved' : 'Pending'}</p>
                    <p style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 0.875rem;
                        color: #856404;
                        margin: 0;
                        line-height: 1.6;
                    ">
                        Reference: <strong>${refundStatus.refund_id ? refundStatus.refund_id.substring(0, 8) : 'N/A'}</strong> • 
                        ${refundStatus.created_at ? new Date(refundStatus.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
                    </p>
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Error checking refund status:', error);
    }
    
    html += `
    `;
    
    // Show message if subscription is canceled
    if (status === 'canceled' && currentPlan !== 'free') {
        const changeDate = pendingPlanChangeAt ? new Date(pendingPlanChangeAt * 1000).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null;
        html += `
            <div style="
                background: #FFF9E6;
                border-left: 3px solid #FFE082;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 32px;
            ">
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.9375rem;
                    color: #856404;
                    margin: 0 0 8px 0;
                    font-weight: 600;
                ">Subscription Canceled</p>
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.875rem;
                    color: #856404;
                    margin: 0;
                    line-height: 1.6;
                ">
                    ${changeDate ? `Ends ${changeDate}. ` : ''}Access continues until then.
                </p>
            </div>
        `;
    }
    
    // Show message if there's a pending plan change
    if (pendingPlan && pendingPlanChangeAt && status !== 'canceled') {
        const changeDate = new Date(pendingPlanChangeAt * 1000).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        html += `
            <div style="
                background: #E8F4FD;
                border-left: 3px solid #0066CC;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 32px;
            ">
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.9375rem;
                    color: #0055AA;
                    margin: 0 0 8px 0;
                    font-weight: 600;
                ">Plan Change Scheduled</p>
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.875rem;
                    color: #0055AA;
                    margin: 0;
                    line-height: 1.6;
                ">
                    Switching to ${pendingPlanName} on ${changeDate}.
                </p>
            </div>
        `;
    }
    
    // Features list
    if (plan.features && plan.features.length > 0) {
        html += `<ul style="
            list-style: none;
            padding: 0;
            margin: 32px 0;
        ">`;
        plan.features.forEach(feature => {
            html += `
                <li style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.9375rem;
                    color: #1D1D1F;
                    margin-bottom: 12px;
                    display: flex;
                    align-items: center;
                ">
                    <span style="color: #0066CC; margin-right: 12px; font-weight: 600;">✓</span>
                    ${feature}
                </li>
            `;
        });
        html += `</ul>`;
    }
    
    // Action buttons
    if (status === 'active' && subscription.subscription && currentPlan !== 'free') {
        html += `
            <div style="
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 12px;
                margin-top: 32px;
            ">
                <a href="#" onclick="checkRefundEligibility(); return false;" aria-label="Request Refund" 
                    class="image-18 nav-6 container-0" 
                    style="background: #FF6F61; width: 100%;">
                    <div class="title-18 main-6">
                        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Request Refund<span class="text-18 feature-7">
                            <svg width="17" height="14" viewBox="0 0 17 14" fill="none" color="white">
                                <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" 
                                    stroke="currentColor" stroke-linecap="round"></path>
                                <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                            </svg>
                        </span></span>
                    </div>
                </a>
                <a href="#" onclick="cancelSubscription(); return false;" aria-label="Cancel Subscription" 
                    class="logo-18 list-5"
                    style="width: 100%;">
                    <div class="title-18 main-6">
                        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Cancel<span class="text-18 feature-7">
                            <svg width="17" height="14" viewBox="0 0 17 14" fill="none" color="var(--text-on-button-secondary)">
                                <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" 
                                    stroke="currentColor" stroke-linecap="round"></path>
                                <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                            </svg>
                        </span></span>
                    </div>
                </a>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Display usage info
function displayUsage(usage) {
    const container = document.getElementById('usage-info');
    if (!container) return;
    
    const plan = usage.plan || {};
    const galleryLimit = usage.gallery_limit || {};
    const storageLimit = usage.storage_limit || {};
    
    const galleryPercent = galleryLimit.limit !== -1 ? Math.min(100, ((galleryLimit.used || 0) / galleryLimit.limit) * 100) : 0;
    const storagePercent = storageLimit.limit_gb !== -1 ? Math.min(100, storageLimit.usage_percent || 0) : 0;
    
    const galleryLimitText = galleryLimit.limit === -1 ? 'Unlimited' : galleryLimit.limit;
    const storageLimitText = storageLimit.limit_gb === -1 ? 'Unlimited' : `${storageLimit.limit_gb} GB`;
    
    let html = `
        <!-- Gallery Limit -->
        <div class="card-18 hero-10 animation-11 textarea-7">
            <div class="button-18 list-7">
                <div class="container-15 item-7">
                    <h3 class="grid-15 animation-7">Monthly Galleries</h3>
                    <div class="input-15 background-7">
                        <div style="
                            display: flex;
                            align-items: baseline;
                            margin: 24px 0;
                        ">
                            <span style="
                                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 3rem;
                                font-weight: 800;
                                line-height: 1;
                                color: #1D1D1F;
                            ">${galleryLimit.used || 0}</span>
                            <span style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 1rem;
                                color: #86868B;
                                margin-left: 8px;
                            ">/ ${galleryLimitText}</span>
                        </div>
                        ${galleryLimit.limit !== -1 ? `
                            <div style="
                                height: 6px;
                                background: rgba(0, 0, 0, 0.06);
                                border-radius: 3px;
                                overflow: hidden;
                                margin-top: 16px;
                            ">
                                <div style="
                                    height: 100%;
                                    background: #0066CC;
                                    width: ${galleryPercent}%;
                                    transition: width 0.3s ease;
                                    border-radius: 3px;
                                "></div>
                            </div>
                        ` : ''}
                        <p style="
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 0.875rem;
                            color: #86868B;
                            margin-top: 16px;
                            margin-bottom: 0;
                        ">
                            ${galleryLimit.limit === -1 ? 'Unlimited galleries' : `${galleryLimit.remaining || 0} remaining`}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Storage Limit -->
        <div class="card-18 hero-10 animation-11 textarea-7">
            <div class="button-18 list-7">
                <div class="container-15 item-7">
                    <h3 class="grid-15 animation-7">Storage</h3>
                    <div class="input-15 background-7">
                        <div style="
                            display: flex;
                            align-items: baseline;
                            margin: 24px 0;
                        ">
                            <span style="
                                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 3rem;
                                font-weight: 800;
                                line-height: 1;
                                color: #1D1D1F;
                            ">${(storageLimit.used_gb || 0).toFixed(1)}</span>
                            <span style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 1rem;
                                color: #86868B;
                                margin-left: 8px;
                            ">GB / ${storageLimitText}</span>
                        </div>
                        ${storageLimit.limit_gb !== -1 ? `
                            <div style="
                                height: 6px;
                                background: rgba(0, 0, 0, 0.06);
                                border-radius: 3px;
                                overflow: hidden;
                                margin-top: 16px;
                            ">
                                <div style="
                                    height: 100%;
                                    background: #0066CC;
                                    width: ${storagePercent}%;
                                    transition: width 0.3s ease;
                                    border-radius: 3px;
                                "></div>
                            </div>
                        ` : ''}
                        <p style="
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 0.875rem;
                            color: #86868B;
                            margin-top: 16px;
                            margin-bottom: 0;
                        ">
                            ${storageLimit.limit_gb === -1 ? 'Unlimited storage' : `${((storageLimit.limit_gb || 0) - (storageLimit.used_gb || 0)).toFixed(1)} GB available`}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Warning if approaching limits
    if (galleryLimit.remaining === 0 || (storageLimit.usage_percent && storageLimit.usage_percent >= 90)) {
        const currentPlan = usage.plan?.id || 'free';
        let upgradePlan = currentPlan === 'plus' ? 'pro' : 'plus';
        let upgradePlanName = currentPlan === 'plus' ? 'Pro' : 'Plus';
        
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7" style="
                border-left: 3px solid #FFE082;
                background: #FFF9E6;
            ">
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <h3 class="grid-15 animation-7" style="color: #856404;">Approaching Limits</h3>
                        <div class="input-15 background-7">
                            <p style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.9375rem;
                                color: #856404;
                                margin-bottom: 20px;
                            ">
                                ${galleryLimit.remaining === 0 ? 'Gallery limit reached. ' : ''}
                                ${storageLimit.usage_percent >= 90 ? 'Storage almost full. ' : ''}
                                Upgrade to ${upgradePlanName} for more resources.
                            </p>
                            <a href="#plans-section" onclick="document.getElementById('plans-section').scrollIntoView({behavior: 'smooth'}); return false;" 
                                class="image-18 nav-6 container-0" 
                                style="display: inline-flex; background: #0066CC;">
                                <div class="title-18 main-6">
                                    <span>Upgrade to ${upgradePlanName}<span class="text-18 feature-7">
                                        <svg width="17" height="14" viewBox="0 0 17 14" fill="none" color="white">
                                            <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" 
                                                stroke="currentColor" stroke-linecap="round"></path>
                                            <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                                        </svg>
                                    </span></span>
                                </div>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Display billing history
function displayBillingHistory(history) {
    const container = document.getElementById('billing-history');
    if (!container) return;
    
    const invoices = history.invoices || [];
    
    if (invoices.length === 0) {
        container.innerHTML = `
            <div style="
                padding: 48px 24px;
                text-align: center;
            ">
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.9375rem;
                    color: #86868B;
                    margin: 0;
                ">No billing history.</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div style="display: flex; flex-direction: column; gap: 0;">
    `;
    
    invoices.forEach((invoice, index) => {
        const date = new Date(invoice.created_at).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        const invoiceNumber = invoice.invoice_number || invoice.stripe_invoice_id || 'N/A';
        const showButton = (invoice.status === 'paid' && invoice.stripe_invoice_id);
        
        html += `
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 20px 0;
                ${index < invoices.length - 1 ? 'border-bottom: 1px solid rgba(0, 0, 0, 0.06);' : ''}
            ">
                <!-- Left: Invoice details -->
                <div style="flex: 1; min-width: 0;">
                    <div style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 1rem;
                        font-weight: 600;
                        color: #1D1D1F;
                        margin-bottom: 4px;
                    ">${invoiceNumber}</div>
                    <div style="
                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 0.875rem;
                        color: #86868B;
                    ">
                        ${date} • $${invoice.amount?.toFixed(2) || '0.00'} • 
                        <span style="color: ${invoice.status === 'paid' ? '#34C759' : '#86868B'};">
                            ${invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                        </span>
                    </div>
                </div>
                
                <!-- Right: Download button -->
                <div>
                    ${showButton ? `
                        <button 
                            onclick="downloadInvoice('${invoice.stripe_invoice_id}', '${invoiceNumber}')"
                            aria-label="Download invoice"
                            style="
                                display: inline-flex;
                                align-items: center;
                                justify-content: center;
                                width: 40px;
                                height: 40px;
                                background: transparent;
                                border: none;
                                border-radius: 50%;
                                color: #0066CC;
                                cursor: pointer;
                                transition: all 0.15s ease;
                            "
                            onmouseover="this.style.background='rgba(0, 102, 204, 0.1)'"
                            onmouseout="this.style.background='transparent'"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                        </button>
                    ` : `
                        <span style="
                            width: 40px;
                            height: 40px;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            color: #D1D1D6;
                        ">—</span>
                    `}
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    
    container.innerHTML = html;
}

// Download invoice PDF
async function downloadInvoice(stripeInvoiceId, invoiceNumber) {
    try {
        console.log(`📄 Downloading invoice ${stripeInvoiceId} (${invoiceNumber})...`);
        
        // Call backend endpoint which will redirect to Stripe PDF
        // Note: API_BASE_URL already includes /v1
        const apiUrl = window.GalerlyConfig?.API_BASE_URL || window.API_BASE_URL || '';
        const url = `${apiUrl}/billing/invoice/${stripeInvoiceId}/pdf`;
        
        console.log(`📄 Opening PDF URL: ${url}`);
        
        // Open in branded modal - backend will redirect to Stripe PDF
        openInModal(url, `Invoice ${invoiceNumber}`);
        
    } catch (error) {
        console.error('❌ Error downloading invoice:', error);
        showError('Failed to download invoice. Please try again or contact support.', 'Download Failed');
    }
}

// Initialize billing page
async function initBillingPage() {
    console.log('🎬 Initializing billing page...');
    
    // Verify authentication with backend (HttpOnly cookie)
    const isAuth = window.isAuthenticated ? await window.isAuthenticated() : false;
    console.log('🔐 Authentication status:', isAuth);
    
    if (!isAuth) {
        console.log('❌ Not authenticated, redirecting to login...');
        window.location.href = window.GalerlyConfig.LOGIN_PAGE;
        return;
    }
    
    // Check for success/cancel parameters from Stripe redirect
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const canceled = urlParams.get('canceled');
    
    // Remove query parameters from URL
    if (success || canceled) {
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Show success message if redirected from successful checkout
    if (success === 'true') {
        // Show success notification
        const successMsg = document.createElement('div');
        successMsg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10000; max-width: 400px;';
        successMsg.innerHTML = '<strong>✅ Payment successful!</strong><br>Your subscription is being activated. Please wait a moment...';
        document.body.appendChild(successMsg);
        
        // Wait a bit for webhook to process, then reload data
        setTimeout(async () => {
            try {
                // Reload subscription data
                const [subscription, usage] = await Promise.all([
                    loadSubscription(),
                    loadUsage()
                ]);
                
                await displaySubscription(subscription);
                displayUsage(usage);
                
                // Update success message
                successMsg.innerHTML = '<strong>✅ Subscription activated!</strong><br>Your plan has been upgraded successfully.';
                successMsg.style.background = '#10b981';
                
                // Remove success message after 5 seconds
                setTimeout(() => {
                    successMsg.style.transition = 'opacity 0.5s';
                    successMsg.style.opacity = '0';
                    setTimeout(() => successMsg.remove(), 500);
                }, 5000);
            } catch (error) {
                console.error('Error reloading subscription:', error);
                successMsg.innerHTML = '<strong>⚠️ Payment received</strong><br>Please refresh the page to see your updated subscription.';
                successMsg.style.background = '#f59e0b';
            }
        }, 2000); // Wait 2 seconds for webhook to process
    }
    
    // Show cancel message if user canceled checkout
    if (canceled === 'true') {
        const cancelMsg = document.createElement('div');
        cancelMsg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #6b7280; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10000; max-width: 400px;';
        cancelMsg.innerHTML = '<strong>ℹ️ Checkout canceled</strong><br>No charges were made.';
        document.body.appendChild(cancelMsg);
        
        setTimeout(() => {
            cancelMsg.style.transition = 'opacity 0.5s';
            cancelMsg.style.opacity = '0';
            setTimeout(() => cancelMsg.remove(), 500);
        }, 3000);
    }
    
    try {
        // Load subscription and usage
        console.log('📊 Loading subscription and usage...');
        const [subscription, usage] = await Promise.all([
            loadSubscription(),
            loadUsage()
        ]);
        console.log('✅ Subscription loaded:', subscription);
        console.log('✅ Usage loaded:', usage);
        
        await displaySubscription(subscription);
        displayUsage(usage);
        
        // Load billing history if on billing page
        if (document.getElementById('billing-history')) {
            console.log('📋 Found billing-history element, loading history...');
            const history = await loadBillingHistory();
            console.log('✅ Billing history loaded:', history);
            console.log('📋 Number of invoices:', history.invoices?.length || 0);
            if (history.invoices && history.invoices.length > 0) {
                console.log('📋 First invoice:', history.invoices[0]);
            }
            displayBillingHistory(history);
        } else {
            console.log('⚠️  No billing-history element found on page');
        }
        
        // Display all plans with current plan highlighted
        const currentPlanId = subscription.plan || 'free';
        await displayAllPlans(currentPlanId, subscription);
        
        // Setup upgrade buttons (legacy - for backward compatibility)
        setupUpgradeButtons();
    } catch (error) {
        console.error('Error initializing billing page:', error);
        document.getElementById('subscription-info').innerHTML = '<p class="error">Failed to load subscription information.</p>';
    }
}

// Display all plans with current plan highlighted
async function displayAllPlans(currentPlanId, subscriptionData = null) {
    const container = document.getElementById('plans-container');
    if (!container) return;
    
    let pendingPlan = null;
    if (subscriptionData) {
        pendingPlan = subscriptionData.pending_plan || null;
    }
    
    const plans = [
        {
            id: 'free',
            name: 'Starter',
            price: 0,
            description: 'Perfect for getting started.',
            features: [
                '5 galleries per month',
                '5 GB storage',
                'Client downloads',
                'Photo approval',
                'Comments',
                'Email notifications',
                'Public profile',
                'Basic analytics'
            ]
        },
        {
            id: 'plus',
            name: 'Plus',
            price: 12,
            badge: 'BEST VALUE',
            description: 'For growing photographers.',
            features: [
                'Unlimited galleries',
                '50 GB storage',
                'Video support (30 min, HD)',
                'Priority email support',
                'Batch uploads',
                'Advanced analytics',
                'Custom notifications'
            ]
        },
        {
            id: 'pro',
            name: 'Pro',
            price: 24,
            description: 'For professionals.',
            features: [
                'Unlimited galleries',
                '200 GB storage',
                'Video support (2 hours, 4K)',
                'Priority support (12-24h)',
                'Dedicated support',
                'Custom email branding',
                'Analytics exports',
                'Gallery templates'
            ]
        }
    ];
    
    let html = '';
    
    plans.forEach(plan => {
        const isCurrentPlan = plan.id === currentPlanId;
        const isFree = plan.id === 'free';
        
        const planPrices = { 'free': 0, 'plus': 12, 'pro': 24 };
        const currentPrice = planPrices[currentPlanId] || 0;
        const targetPrice = planPrices[plan.id] || 0;
        
        const isUpgrade = !isCurrentPlan && !isFree && currentPlanId !== 'free' && targetPrice > currentPrice;
        const isDowngrade = !isCurrentPlan && currentPlanId !== 'free' && (targetPrice < currentPrice || plan.id === 'free');
        
        const isReactivation = (pendingPlan === 'free' && isCurrentPlan && (plan.id === 'plus' || plan.id === 'pro'));
        
        let buttonText = '';
        let buttonClass = 'image-18 nav-6 container-0 change-plan-btn';
        
        if (isReactivation) {
            buttonText = `Reactivate`;
        } else if (isCurrentPlan) {
            buttonText = 'Current Plan';
            buttonClass = 'logo-18 list-5 current-plan-btn';
        } else if (isUpgrade || (currentPlanId === 'free' && !isFree)) {
            buttonText = `Upgrade`;
        } else if (isDowngrade) {
            buttonText = `Downgrade`;
            buttonClass = 'logo-18 list-5 change-plan-btn';
        }
        
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7" ${isCurrentPlan ? 'style="border: 2px solid #0066CC; box-shadow: 0 4px 16px rgba(0, 102, 204, 0.1);"' : ''}>
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
                            <h3 class="grid-15 animation-7" style="margin: 0;">${plan.name}</h3>
                            ${plan.badge ? `<span style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.75rem;
                                font-weight: 600;
                                padding: 4px 12px;
                                background: #0066CC;
                                color: white;
                                border-radius: 12px;
                            ">${plan.badge}</span>` : ''}
                            ${isCurrentPlan ? `<span style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.75rem;
                                font-weight: 600;
                                color: #0066CC;
                            ">(Current)</span>` : ''}
                        </div>
                        <div class="input-15 background-7">
                            <div style="display: flex; align-items: baseline; margin-bottom: 16px;">
                                <span style="
                                    font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                                    font-size: 3rem;
                                    font-weight: 800;
                                    line-height: 1;
                                    color: #1D1D1F;
                                ">$${plan.price}</span>
                                ${plan.price > 0 ? `<span style="
                                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                    font-size: 1rem;
                                    color: #86868B;
                                    margin-left: 8px;
                                ">/month</span>` : ''}
                            </div>
                            <p style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.9375rem;
                                color: #86868B;
                                margin-bottom: 32px;
                            ">${plan.description}</p>
                            <ul style="list-style: none; padding: 0; margin: 32px 0;">
                                ${plan.features.map(feature => `
                                    <li style="
                                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                        font-size: 0.9375rem;
                                        color: #1D1D1F;
                                        margin-bottom: 12px;
                                        display: flex;
                                        align-items: center;
                                    ">
                                        <span style="color: #0066CC; margin-right: 12px; font-weight: 600;">✓</span>
                                        ${feature}
                                    </li>
                                `).join('')}
                            </ul>
                            ${buttonText ? `
                                <a aria-label="${buttonText}" class="${buttonClass}" href="#" data-plan="${plan.id}" 
                                    ${isCurrentPlan && !isReactivation ? 'onclick="return false;" style="pointer-events: none; opacity: 0.5;"' : ''}>
                                    <div class="title-18 main-6">
                                        <span>${buttonText}<span class="text-18 feature-7">
                                            <svg width="17" height="14" viewBox="0 0 17 14" fill="none" color="currentColor">
                                                <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" 
                                                    stroke="currentColor" stroke-linecap="round"></path>
                                                <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                                            </svg>
                                        </span></span>
                                    </div>
                                </a>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    setupPlanChangeButtons();
}

// Setup plan change buttons (upgrade/downgrade)
function setupPlanChangeButtons() {
    const changeButtons = document.querySelectorAll('.change-plan-btn:not(.current-plan-btn)');
    
    changeButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const planId = button.dataset.plan || 'plus';
            const buttonText = button.querySelector('.main-6 span') || button;
            const originalText = buttonText.textContent;
            
            // Get current plan and pending plan from subscription
            let currentPlanId = 'free';
            let pendingPlan = null;
            try {
                const subscription = await loadSubscription();
                currentPlanId = subscription.plan || 'free';
                pendingPlan = subscription.pending_plan || null;
            } catch (error) {
                console.error('Error loading subscription:', error);
            }
            
            // Check if this is a reactivation (user has pending_plan='free' but wants to return to current plan)
            const isReactivation = (
                pendingPlan === 'free' && 
                currentPlanId === planId && 
                (planId === 'plus' || planId === 'pro')
            );
            
            // If reactivation, use changePlan endpoint
            if (isReactivation) {
                try {
                    button.disabled = true;
                    buttonText.textContent = 'Reactivating...';
                    
                    const result = await changePlan(planId);
                    
                    await showSuccess(`Subscription reactivated successfully!\n\n${result.message || `Your ${planId} plan is now active again.`}`);
                    location.reload();
                    return;
                } catch (error) {
                    console.error('Error reactivating subscription:', error);
                    const errorMessage = error.message || 'Unknown error';
                    const errorDetails = error.details?.message || '';
                    await showError(`Failed to reactivate subscription:\n\n${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`, 'Reactivation Failed');
                    button.disabled = false;
                    buttonText.textContent = originalText;
                    return;
                }
            }
            
            // Check if downgrading to free
            if (planId === 'free') {
                // Check downgrade limits first
                try {
                    const checkResponse = await window.apiRequest(`billing/subscription/check-downgrade?target_plan=free`);
                    
                    if (!checkResponse.can_downgrade) {
                        // Show modal to select galleries to delete
                        showDowngradeSelectionModal(checkResponse);
                        return;
                    } else {
                        // Can downgrade without deletion
                        const confirmed = await showConfirm(
                            'Are you sure you want to downgrade to Starter plan?\n\nYou will be downgraded at the end of your current billing period. You will continue to have access to premium features until then.\n\nYou can upgrade again anytime.',
                            'Confirm Downgrade',
                            'Downgrade',
                            'Cancel'
                        );
                        if (!confirmed) {
                            return;
                        }
                        // Downgrade without deletion
                        try {
                            const result = await downgradeSubscription([]);
                            await showSuccess(`Downgrade scheduled successfully!\n\n${result.message || 'You will be downgraded to Starter plan at the end of your current billing period.'}`);
                            location.reload();
                            return;
                        } catch (error) {
                            console.error('Error downgrading:', error);
                            showError('Failed to downgrade: ' + error.message, 'Downgrade Failed');
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error checking downgrade limits:', error);
                    showError('Failed to check downgrade requirements: ' + error.message, 'Check Failed');
                    return;
                }
            }
            
            // Check if changing between paid plans (Plus <-> Pro)
            // Also allow if user has pending_plan and wants to change to a different paid plan
            const isPaidPlanChange = (
                (currentPlanId === 'plus' || currentPlanId === 'pro') && 
                (planId === 'plus' || planId === 'pro') && 
                (currentPlanId !== planId || (pendingPlan && pendingPlan !== planId))
            );
            
            if (isPaidPlanChange) {
                // Determine if this is a downgrade (lower price)
                const planPrices = { 'free': 0, 'plus': 12, 'pro': 24 };
                const currentPrice = planPrices[currentPlanId] || 0;
                const targetPrice = planPrices[planId] || 0;
                const isDowngrade = targetPrice < currentPrice;
                
                // If downgrade, check limits first
                if (isDowngrade) {
                    try {
                        button.disabled = true;
                        buttonText.textContent = 'Checking limits...';
                        
                        const checkResponse = await checkDowngradeLimits(planId);
                        
                        if (!checkResponse.can_downgrade) {
                            // Show warning modal about exceeding limits
                            const issues = checkResponse.issues || [];
                            const issuesText = issues.map(i => i.message).join('\n\n');
                            const targetPlanName = checkResponse.target_plan_name || planId;
                            const currentUsage = checkResponse.current_usage || {};
                            const targetLimits = checkResponse.target_limits || {};
                            
                            let warningMessage = `⚠️ Cannot Downgrade to ${targetPlanName}\n\n`;
                            warningMessage += `You exceed the limits for ${targetPlanName} plan:\n\n`;
                            warningMessage += issuesText;
                            warningMessage += `\n\nCurrent Usage:\n`;
                            warningMessage += `• Storage: ${currentUsage.total_storage_gb || 0} GB\n`;
                            if (currentUsage.galleries_this_month !== undefined) {
                                warningMessage += `• Galleries this month: ${currentUsage.galleries_this_month}\n`;
                            }
                            warningMessage += `\n${targetPlanName} Plan Limits:\n`;
                            warningMessage += `• Storage: ${targetLimits.storage_gb === -1 ? 'Unlimited' : targetLimits.storage_gb + ' GB'}\n`;
                            if (targetLimits.galleries_per_month !== -1) {
                                warningMessage += `• Galleries: ${targetLimits.galleries_per_month}/month\n`;
                            }
                            warningMessage += `\n💡 Please delete some galleries or photos to free up resources, then try again.`;
                            
                            showAlert(warningMessage, 'Cannot Downgrade', '⚠️');
                            
                            button.disabled = false;
                            buttonText.textContent = originalText;
                            return;
                        }
                        
                        // Limits OK, confirm downgrade
                        const targetPlanName = checkResponse.target_plan_name || planId;
                        const confirmed = await showConfirm(
                            `Are you sure you want to downgrade to ${targetPlanName} plan?\n\nYou will be downgraded at the end of your current billing period. You will continue to have access to your current plan features until then.`,
                            'Confirm Downgrade',
                            'Downgrade',
                            'Cancel'
                        );
                        if (!confirmed) {
                            button.disabled = false;
                            buttonText.textContent = originalText;
                            return;
                        }
                        
                        buttonText.textContent = 'Processing...';
                    } catch (error) {
                        console.error('Error checking downgrade limits:', error);
                        showError('Failed to check downgrade requirements. Please try again.', 'Check Failed');
                        button.disabled = false;
                        buttonText.textContent = originalText;
                        return;
                    }
                }
                
                // Use plan change endpoint (modifies existing subscription with proration)
                try {
                    if (!button.disabled) {
                        button.disabled = true;
                        buttonText.textContent = 'Processing...';
                    }
                    
                    const result = await changePlan(planId);
                    
                    // Check if this is a scheduled change (downgrade) or immediate (upgrade)
                    if (result.scheduled) {
                        await showSuccess(`Plan change scheduled!\n\n${result.message || `You will be downgraded to ${planId} at the end of your current billing period.`}`);
                    } else {
                        await showSuccess(`Plan changed successfully!\n\n${result.message || `Changed from ${currentPlanId} to ${planId}.`}\n\n${result.prorated ? 'The difference has been prorated automatically.' : ''}`);
                    }
                    location.reload();
                    return;
                } catch (error) {
                    console.error('Error changing plan:', error);
                    const errorMessage = error.message || 'Unknown error';
                    const errorDetails = error.details?.message || '';
                    
                    // Show user-friendly error message
                    let alertMessage = `Failed to change plan: ${errorMessage}`;
                    if (errorDetails) {
                        alertMessage += `\n\n${errorDetails}`;
                    }
                    // If backend also caught the limit issue, show that
                    if (errorMessage.includes('exceed') || errorMessage.includes('limit')) {
                        alertMessage += `\n\n💡 Tip: Delete some galleries or photos to free up resources.`;
                    }
                    
                    showAlert(alertMessage, 'Downgrade Limits Exceeded', '⚠️');
                    button.disabled = false;
                    buttonText.textContent = originalText;
                    return;
                }
            }
            
            // For new subscriptions or upgrades from free, use checkout
            try {
                button.disabled = true;
                buttonText.textContent = 'Processing...';
                
                const checkout = await createCheckoutSession(planId);
                
                if (checkout.url) {
                    window.location.href = checkout.url;
                } else {
                    throw new Error('No checkout URL received');
                }
            } catch (error) {
                console.error('Error creating checkout:', error);
                
                // Handle 409 Conflict (race condition)
                if (error.status === 409) {
                    showAlert('Another subscription change is in progress.\n\nPlease wait a moment and try again.', 'Operation in Progress', '⚠️');
                } else {
                    const errorMessage = error.message || 'Unknown error';
                    const errorDetails = error.details?.message || '';
                    showError(`Failed to change plan:\n\n${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`, 'Plan Change Failed');
                }
                
                button.disabled = false;
                buttonText.textContent = originalText;
            }
        });
    });
}

// Setup upgrade buttons (legacy - for backward compatibility)
async function setupUpgradeButtons() {
    const upgradeButtons = document.querySelectorAll('.upgrade-plan-btn');
    
    upgradeButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const planId = button.dataset.plan || 'plus';
            
            try {
                button.disabled = true;
                const buttonText = button.querySelector('.main-6 span') || button;
                buttonText.textContent = 'Processing...';
                
                const checkout = await createCheckoutSession(planId);
                
                if (checkout.url) {
                    window.location.href = checkout.url;
                } else {
                    throw new Error('No checkout URL received');
                }
            } catch (error) {
                console.error('Error creating checkout:', error);
                const errorMessage = error.message || 'Unknown error';
                const errorDetails = error.details?.message || '';
                showError(`Failed to start checkout:\n\n${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`, 'Checkout Failed');
                button.disabled = false;
                const buttonText = button.querySelector('.main-6 span') || button;
                buttonText.textContent = buttonText.textContent.replace('Processing...', 'Upgrade');
            }
        });
    });
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBillingPage);
} else {
    initBillingPage();
}

// Export functions for global use
window.loadSubscription = loadSubscription;
window.loadUsage = loadUsage;
window.loadBillingHistory = loadBillingHistory;
window.createCheckoutSession = createCheckoutSession;
window.changePlan = changePlan;
window.cancelSubscription = cancelSubscription;
window.checkDowngradeLimits = checkDowngradeLimits;
window.downgradeSubscription = downgradeSubscription;
window.displaySubscription = displaySubscription;
window.displayUsage = displayUsage;
window.displayBillingHistory = displayBillingHistory;

// Refund functionality - Show custom modal
async function checkRefundEligibility() {
    // Show loading state
    const loadingModal = showLoadingModal('Checking refund eligibility...');
    
    try {
        const result = await window.apiRequest('billing/refund/check');
        loadingModal.remove();
        
        if (result.eligible) {
            const details = result.details || {};
            showRefundEligibleModal(details);
        } else {
            const details = result.details || {};
            let detailsText = '';
            if (details.days_since_purchase) {
                detailsText += `\n• Days since purchase: ${details.days_since_purchase} days (limit: 14 days)`;
            }
            if (details.total_storage_gb !== undefined) {
                detailsText += `\n• Storage used: ${details.total_storage_gb} GB`;
            }
            if (details.galleries_since_purchase !== undefined) {
                detailsText += `\n• Galleries created: ${details.galleries_since_purchase}`;
            }
            
            showRefundIneligibleModal(`${result.reason}${detailsText}`);
        }
    } catch (error) {
        loadingModal.remove();
        console.error('Error checking refund eligibility:', error);
        showErrorModal('Failed to check refund eligibility. Please contact support at support@galerly.com');
    }
}

// Show loading modal
function showLoadingModal(message) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    `;
    
    modalContent.innerHTML = `
        <div style="
            width: 48px;
            height: 48px;
            border: 4px solid #F5F5F7;
            border-top-color: #0066CC;
            border-radius: 50%;
            margin: 0 auto 24px;
            animation: spin 1s linear infinite;
        "></div>
        <style>
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
        <p style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1rem;
            color: #6B6B6B;
            margin: 0;
        ">${message}</p>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    return modal;
}

// Show refund eligible modal
function showRefundEligibleModal(details) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">✓</div>
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.75rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 16px 0;
                letter-spacing: -0.02em;
            ">You're Eligible for a Refund</h2>
        </div>
        
        <div style="
            background: #F5F5F7;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        ">
            <div style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                color: #6B6B6B;
                line-height: 1.8;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Purchase Date:</span>
                    <strong style="color: #1D1D1F;">${new Date(details.purchase_date).toLocaleDateString()}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Days Since Purchase:</span>
                    <strong style="color: #1D1D1F;">${details.days_since_purchase} days</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Storage Used:</span>
                    <strong style="color: #1D1D1F;">${details.total_storage_gb} GB</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Galleries Created:</span>
                    <strong style="color: #1D1D1F;">${details.galleries_since_purchase}</strong>
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 24px;">
            <label style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                font-weight: 500;
                color: #1D1D1F;
                display: block;
                margin-bottom: 8px;
            ">Reason for refund request (minimum 10 characters):</label>
            <textarea id="refund-reason-input" placeholder="Please tell us why you'd like a refund..." style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                width: 100%;
                min-height: 120px;
                padding: 12px;
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                font-size: 1rem;
                resize: vertical;
                box-sizing: border-box;
            "></textarea>
            <div id="reason-error" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                color: #FF3B30;
                margin-top: 8px;
                display: none;
            ">Please provide at least 10 characters.</div>
        </div>
        
        <div style="
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        ">
            <button id="refund-modal-cancel-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #F5F5F7;
                color: #1D1D1F;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
                Cancel
            </button>
            <button id="refund-modal-submit-btn" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #0066CC;
                color: white;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#0055AA'" onmouseout="this.style.background='#0066CC'">
                Submit Request
            </button>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Cancel button
    modalContent.querySelector('#refund-modal-cancel-btn').addEventListener('click', () => {
        modal.remove();
    });
    
    // Submit button
    modalContent.querySelector('#refund-modal-submit-btn').addEventListener('click', async () => {
        const reasonInput = modalContent.querySelector('#refund-reason-input');
        const errorDiv = modalContent.querySelector('#reason-error');
        const reason = reasonInput.value.trim();
        
        if (reason.length < 10) {
            errorDiv.style.display = 'block';
            reasonInput.style.borderColor = '#FF3B30';
            return;
        }
        
        const submitBtn = modalContent.querySelector('#refund-modal-submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        submitBtn.style.opacity = '0.6';
        
        try {
            await submitRefundRequest(reason);
            modal.remove();
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Request';
            submitBtn.style.opacity = '1';
            errorDiv.textContent = error.message || 'Failed to submit request. Please try again.';
            errorDiv.style.display = 'block';
        }
    });
}

// Show refund ineligible modal
function showRefundIneligibleModal(detailsText) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 3rem; margin-bottom: 16px; color: #FF9500;">⚠</div>
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.75rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 16px 0;
                letter-spacing: -0.02em;
            ">Not Eligible for Refund</h2>
        </div>
        
        <div style="
            background: #FFF8E1;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        ">
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                color: #6B6B6B;
                line-height: 1.6;
                margin: 0;
                white-space: pre-line;
            ">${detailsText}</p>
        </div>
        
        <div style="
            background: #F5F5F7;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
        ">
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 8px 0;
            ">Refund Policy:</p>
            <ul style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                color: #6B6B6B;
                line-height: 1.8;
                margin: 0;
                padding-left: 20px;
            ">
                <li>Available within 14 days of purchase</li>
                <li>No refund if > 5GB or > 5 galleries used (Starter limits)</li>
                <li>No refund if > 50GB used (Plus limits)</li>
            </ul>
        </div>
        
        <p style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 0.875rem;
            color: #86868B;
            line-height: 1.6;
            margin: 0 0 24px 0;
            text-align: center;
        ">
            If you believe this is an error, please contact support at 
            <a href="mailto:support@galerly.com" style="color: #0066CC; text-decoration: none;">support@galerly.com</a>
        </p>
        
        <div style="text-align: center;">
            <button onclick="this.closest('[style*=\\'position: fixed\\']').remove()" style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                padding: 12px 32px;
                background: #F5F5F7;
                color: #1D1D1F;
                border: none;
                border-radius: 980px;
                cursor: pointer;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.2s ease;
            " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
                Close
            </button>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Show error modal
function showErrorModal(message) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.3s ease;
        text-align: center;
    `;
    
    modalContent.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 16px; color: #FF3B30;">✕</div>
        <h2 style="
            font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.75rem;
            font-weight: 600;
            color: #1D1D1F;
            margin: 0 0 16px 0;
            letter-spacing: -0.02em;
        ">Error</h2>
        <p style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1rem;
            color: #6B6B6B;
            line-height: 1.6;
            margin: 0 0 24px 0;
        ">${message}</p>
        <button onclick="this.closest('[style*=\\'position: fixed\\']').remove()" style="
            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 12px 32px;
            background: #F5F5F7;
            color: #1D1D1F;
            border: none;
            border-radius: 980px;
            cursor: pointer;
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.2s ease;
        " onmouseover="this.style.background='#E8E8ED'" onmouseout="this.style.background='#F5F5F7'">
            Close
        </button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

async function submitRefundRequest(reason) {
    try {
        const result = await window.apiRequest('billing/refund/request', {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
        
        // Show success modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.2s ease;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        `;
        
        modalContent.innerHTML = `
            <div style="font-size: 3rem; margin-bottom: 16px;">✓</div>
            <h2 style="
                font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1.75rem;
                font-weight: 600;
                color: #1D1D1F;
                margin: 0 0 16px 0;
                letter-spacing: -0.02em;
            ">Refund Request Submitted</h2>
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 1rem;
                color: #6B6B6B;
                line-height: 1.6;
                margin: 0 0 16px 0;
            ">${result.message}</p>
            <div style="
                background: #F5F5F7;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 24px;
            ">
                <p style="
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.875rem;
                    color: #6B6B6B;
                    margin: 0;
                ">Reference ID: <strong style="color: #1D1D1F;">${result.refund_id.substring(0, 8)}</strong></p>
            </div>
            <p style="
                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.875rem;
                color: #86868B;
                line-height: 1.6;
                margin: 0;
            ">Our team will review your request and respond within 2-3 business days via email.</p>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        setTimeout(() => {
            modal.remove();
            location.reload();
        }, 3000);
    } catch (error) {
        console.error('Error submitting refund request:', error);
        const errorMsg = error.message || error.error || 'Unknown error';
        throw new Error(errorMsg);
    }
}

window.checkRefundEligibility = checkRefundEligibility;
window.submitRefundRequest = submitRefundRequest;

// Handle upgrade from warning card
async function upgradeFromWarning(planId) {
    try {
        // Scroll to plans section
        const plansContainer = document.getElementById('plans-container');
        if (plansContainer) {
            plansContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // Find and click the corresponding plan button
        const planButton = document.querySelector(`.change-plan-btn[data-plan="${planId}"]`);
        if (planButton) {
            // Highlight the plan card briefly
            const planCard = planButton.closest('.card-18');
            if (planCard) {
                planCard.style.transition = 'transform 0.3s, box-shadow 0.3s';
                planCard.style.transform = 'scale(1.02)';
                planCard.style.boxShadow = '0 8px 24px rgba(0, 102, 204, 0.2)';
                
                setTimeout(() => {
                    planCard.style.transform = 'scale(1)';
                    planCard.style.boxShadow = '';
                }, 600);
            }
            
            // Trigger the upgrade
            setTimeout(() => {
                planButton.click();
            }, 300);
        } else {
            // Fallback: redirect to checkout directly
            const checkout = await createCheckoutSession(planId);
            if (checkout.url) {
                window.location.href = checkout.url;
            }
        }
    } catch (error) {
        console.error('Error upgrading from warning:', error);
        showError('Failed to start upgrade process. Please try again.', 'Upgrade Failed');
    }
}

window.upgradeFromWarning = upgradeFromWarning;

