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

// Cancel subscription
async function cancelSubscription() {
    if (!confirm('Are you sure you want to cancel your subscription? You will continue to have access until the end of your billing period.')) {
        return;
    }
    
    try {
        await window.apiRequest('billing/subscription/cancel', {
            method: 'POST'
        });
        alert('Subscription canceled successfully. You will continue to have access until the end of your billing period.');
        location.reload();
    } catch (error) {
        console.error('Error canceling subscription:', error);
        alert('Failed to cancel subscription: ' + error.message);
    }
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
            alert('Please select at least one gallery to delete.');
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
            alert(warningMessage + 'Please select more galleries.');
            return;
        }
        
        // Confirm deletion
        if (!confirm(`Are you sure you want to delete ${selectedGalleries.length} gallery(ies) and schedule downgrade to Starter plan? You will be downgraded at the end of your current billing period. This action cannot be undone.`)) {
            return;
        }
        
        // Disable button
        const confirmBtn = modal.querySelector('#confirm-downgrade-btn');
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Processing...';
        
        try {
            const result = await downgradeSubscription(selectedGalleries);
            alert(`Downgrade scheduled successfully! ${result.message || `Deleted ${result.deleted_galleries} galleries and ${result.deleted_photos} photos. Freed ${result.freed_storage_gb} GB. You will be downgraded to Starter plan at the end of your current billing period.`}`);
            modal.remove();
            location.reload();
        } catch (error) {
            console.error('Error downgrading:', error);
            alert('Failed to downgrade: ' + (error.message || 'Unknown error'));
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Downgrade & Delete Selected';
        }
    });
}

// Display subscription info
function displaySubscription(subscription) {
    const container = document.getElementById('subscription-info');
    if (!container) return;
    
    const plan = subscription.plan_details || {};
    const currentPlan = subscription.plan || 'free';
    // Status should reflect the actual plan, not Stripe subscription status
    // If plan is 'free', status is 'free' regardless of subscription record
    const status = currentPlan === 'free' ? 'free' : (subscription.status || 'active');
    const statusClass = status === 'active' ? 'status-active' : status === 'canceled' ? 'status-canceled' : 'status-free';
    
    // Check for pending plan change
    const pendingPlan = subscription.pending_plan;
    const pendingPlanChangeAt = subscription.pending_plan_change_at;
    const pendingPlanName = pendingPlan ? (pendingPlan === 'free' ? 'Starter' : pendingPlan === 'plus' ? 'Plus' : 'Pro') : null;
    
    let html = `
        <div style="display: flex; align-items: baseline; margin: 24px 0;">
            <span style="font-size: 48px; font-weight: 800; line-height: 1;">${plan.name || subscription.plan}</span>
            ${pendingPlan ? `<span style="font-size: 18px; color: #6b7280; margin-left: 16px; font-weight: 500;">→ ${pendingPlanName}</span>` : ''}
        </div>
        <p style="margin-bottom: 24px;">
            Status: <span class="${statusClass}" style="color: ${status === 'active' ? '#10b981' : status === 'canceled' ? '#ef4444' : '#6b7280'}; font-weight: 600;">${status === 'free' ? 'Starter Plan' : status.charAt(0).toUpperCase() + status.slice(1)}</span>
        </p>
    `;
    
    // Show message if subscription is canceled but user still has access
    if (status === 'canceled' && currentPlan !== 'free') {
        const changeDate = pendingPlanChangeAt ? new Date(pendingPlanChangeAt * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : null;
        html += `
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <p style="margin: 0; font-weight: 600; color: #856404;">⚠️ Subscription Canceled</p>
                <p style="margin: 8px 0 0 0; color: #856404;">
                    Your subscription is scheduled to cancel${changeDate ? ` on ${changeDate}` : ''} at the end of your billing period. 
                    ${pendingPlan ? `You will be moved to the <strong>${pendingPlanName}</strong> plan. ` : ''}
                    You will continue to have access to all current plan features until then.
                </p>
            </div>
        `;
    }
    
    // Show message if there's a pending plan change (not cancellation)
    if (pendingPlan && pendingPlanChangeAt && status !== 'canceled') {
        const changeDate = new Date(pendingPlanChangeAt * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        const changeTime = new Date(pendingPlanChangeAt * 1000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        html += `
            <div style="background: #e0f2fe; border-left: 4px solid #0284c7; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <p style="margin: 0; font-weight: 600; color: #0c4a6e;">📅 Plan Change Scheduled</p>
                <p style="margin: 8px 0 0 0; color: #0c4a6e;">
                    <strong>Current Plan:</strong> ${plan.name || subscription.plan}<br>
                    <strong>Future Plan:</strong> ${pendingPlanName}<br>
                    <strong>Effective Date:</strong> ${changeDate} at ${changeTime}
                </p>
                <p style="margin: 12px 0 0 0; color: #0c4a6e; font-size: 14px;">
                    Your plan will change to <strong>${pendingPlanName}</strong> at the end of your current billing period. 
                    You will continue to have access to your current plan features until then.
                </p>
            </div>
        `;
    }
    
    if (plan.features && plan.features.length > 0) {
        html += `<ul style="list-style: none; padding: 0; margin: 24px 0;">`;
        plan.features.forEach(feature => {
            html += `<li style="margin-bottom: 12px;">→ ${feature}</li>`;
        });
        html += `</ul>`;
    }
    
    // Only show cancel button if user has an active paid subscription
    if (status === 'active' && subscription.subscription && currentPlan !== 'free') {
        // Add refund check button
        html += `
            <button onclick="checkRefundEligibility()" class="item-5 idtTuz submit-btn" style="margin-top: 24px; width: 100%; background: #f97316; color: white;">
                <div class="main-6 jpIyal">
                    <span>Request Refund</span>
                </div>
            </button>
        `;
        
        html += `
            <button onclick="cancelSubscription()" class="item-5 idtTuz submit-btn" style="margin-top: 12px; width: 100%; background: #f3f4f6; color: #374151;">
                <div class="main-6 jpIyal">
                    <span>Cancel Subscription</span>
                </div>
            </button>
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
        <!-- Gallery Limit Card -->
        <div class="card-18 hero-10 animation-11 textarea-7">
            <div class="button-18 list-7">
                <div class="container-15 item-7">
                    <h3 class="grid-15 animation-7">
                        Monthly Galleries
                    </h3>
                    <div class="input-15 background-7">
                        <div style="display: flex; align-items: baseline; margin: 24px 0;">
                            <span style="font-size: 48px; font-weight: 800; line-height: 1;">${galleryLimit.used || 0}</span>
                            <span style="font-size: 18px; margin-left: 8px; opacity: 0.7;">/ ${galleryLimitText}</span>
                        </div>
                        ${galleryLimit.limit !== -1 ? `
                            <div style="height: 8px; background: rgba(0, 0, 0, 0.08); border-radius: 4px; overflow: hidden; margin-top: 16px;">
                                <div style="height: 100%; background: linear-gradient(90deg, #0066CC, #0077FF); width: ${galleryPercent}%; transition: width 0.3s ease; border-radius: 4px;"></div>
                            </div>
                        ` : ''}
                        <p style="margin-top: 16px; margin-bottom: 0;">
                            ${galleryLimit.limit === -1 ? 'Unlimited galleries per month' : `${galleryLimit.remaining || 0} remaining this month`}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Storage Limit Card -->
        <div class="card-18 hero-10 animation-11 textarea-7">
            <div class="button-18 list-7">
                <div class="container-15 item-7">
                    <h3 class="grid-15 animation-7">
                        Storage
                    </h3>
                    <div class="input-15 background-7">
                        <div style="display: flex; align-items: baseline; margin: 24px 0;">
                            <span style="font-size: 48px; font-weight: 800; line-height: 1;">${(storageLimit.used_gb || 0).toFixed(1)}</span>
                            <span style="font-size: 18px; margin-left: 8px; opacity: 0.7;">GB / ${storageLimitText}</span>
                        </div>
                        ${storageLimit.limit_gb !== -1 ? `
                            <div style="height: 8px; background: rgba(0, 0, 0, 0.08); border-radius: 4px; overflow: hidden; margin-top: 16px;">
                                <div style="height: 100%; background: linear-gradient(90deg, #0066CC, #0077FF); width: ${storagePercent}%; transition: width 0.3s ease; border-radius: 4px;"></div>
                            </div>
                        ` : ''}
                        <p style="margin-top: 16px; margin-bottom: 0;">
                            ${storageLimit.limit_gb === -1 ? 'Unlimited storage' : `${((storageLimit.limit_gb || 0) - (storageLimit.used_gb || 0)).toFixed(1)} GB available`}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add warning card if approaching limits
    if (galleryLimit.remaining === 0 || (storageLimit.usage_percent && storageLimit.usage_percent >= 90)) {
        // Determine which plan to upgrade to based on current plan
        const currentPlan = usage.plan?.id || 'free';
        let upgradePlan = 'plus'; // Default: Starter → Plus
        let upgradePlanName = 'Plus';
        
        if (currentPlan === 'plus' || currentPlan === 'pro') {
            // Plus user approaching limits → upgrade to Pro
            upgradePlan = 'pro';
            upgradePlanName = 'Pro';
        }
        
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7" style="grid-column: 1/-1; border-left: 4px solid #ffc107; background: #fffbf0;">
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <h3 class="grid-15 animation-7" style="color: #856404;">
                            ⚠️ Approaching Limits
                        </h3>
                        <div class="input-15 background-7">
                            <p style="margin-bottom: 20px; color: #856404;">
                                ${galleryLimit.remaining === 0 ? 'You\'ve reached your monthly gallery limit. ' : ''}
                                ${storageLimit.usage_percent >= 90 ? 'Your storage is almost full. ' : ''}
                                Upgrade to ${upgradePlanName} to get more resources.
                            </p>
                            <button onclick="upgradeFromWarning('${upgradePlan}')" class="item-5 idtTuz submit-btn" style="display: inline-block; background: linear-gradient(90deg, #0066CC, #0077FF); color: white; border: none; cursor: pointer;">
                                <div class="main-6 jpIyal">
                                    <span>Upgrade to ${upgradePlanName}</span>
                                </div>
                            </button>
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
    console.log('🎨 displayBillingHistory called with:', history);
    const container = document.getElementById('billing-history');
    console.log('🎨 Container element:', container);
    
    if (!container) {
        console.error('❌ No billing-history container found!');
        return;
    }
    
    const invoices = history.invoices || [];
    console.log('🎨 Number of invoices to display:', invoices.length);
    
    if (invoices.length === 0) {
        console.log('⚠️  No invoices, showing empty message');
        container.innerHTML = `
            <div style="
                padding: 48px 24px;
                text-align: center;
            ">
                <p style="
                    margin: 0;
                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 0.9375rem;
                    color: #86868B;
                    font-weight: 400;
                ">No billing history yet.</p>
            </div>
        `;
        return;
    }
    
    // Apple-style minimal design with subtle dividers
    let html = `
        <style>
            @media (max-width: 640px) {
                .billing-invoice-card {
                    grid-template-columns: 1fr !important;
                    gap: 12px !important;
                    padding: 16px 0 !important;
                }
                .billing-invoice-info {
                    gap: 12px !important;
                }
                .billing-invoice-meta {
                    flex-direction: column !important;
                    align-items: flex-start !important;
                    gap: 8px !important;
                }
                .billing-invoice-action {
                    justify-content: flex-start !important;
                }
                .billing-download-icon {
                    width: 36px !important;
                    height: 36px !important;
                }
            }
        </style>
        <div style="
            display: flex;
            flex-direction: column;
            margin-top: 24px;
        ">
    `;
    
    invoices.forEach(invoice => {
        const date = new Date(invoice.created_at).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        const invoiceNumber = invoice.invoice_number || invoice.stripe_invoice_id || 'N/A';
        const showButton = (invoice.status === 'paid' && invoice.stripe_invoice_id);
        
        console.log(`📋 Invoice: status="${invoice.status}", stripe_invoice_id="${invoice.stripe_invoice_id}", showButton: ${showButton}`);
        
        html += `
            <div class="billing-invoice-card" style="
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 24px;
                align-items: center;
                padding: 20px 0;
                border-bottom: 1px solid rgba(0, 0, 0, 0.08);
                transition: all 0.15s ease;
            "
            onmouseover="this.style.background='rgba(0, 0, 0, 0.02)'; this.style.marginLeft='-24px'; this.style.marginRight='-24px'; this.style.paddingLeft='24px'; this.style.paddingRight='24px'; this.style.borderRadius='12px'"
            onmouseout="this.style.background='transparent'; this.style.marginLeft='0'; this.style.marginRight='0'; this.style.paddingLeft='0'; this.style.paddingRight='0'; this.style.borderRadius='0'">
                
                <!-- Left side: Invoice info -->
                <div class="billing-invoice-info" style="display: flex; flex-direction: column; gap: 6px; min-width: 0;">
                    <!-- Invoice number and date -->
                    <div style="display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;">
                        <span style="
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 1.0625rem;
                            font-weight: 600;
                            color: #1D1D1F;
                            letter-spacing: -0.015em;
                        ">${invoiceNumber}</span>
                        <span style="
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 0.8125rem;
                            color: #86868B;
                            font-weight: 400;
                        ">${date}</span>
                    </div>
                    
                    <!-- Amount and status -->
                    <div class="billing-invoice-meta" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <span style="
                            font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 0.9375rem;
                            font-weight: 400;
                            color: #1D1D1F;
                            letter-spacing: -0.01em;
                        ">$${invoice.amount?.toFixed(2) || '0.00'}</span>
                        
                        <span style="
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-weight: 400;
                            font-size: 0.8125rem;
                            color: ${invoice.status === 'paid' ? '#34C759' : '#86868B'};
                        ">${invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}</span>
                    </div>
                </div>
                
                <!-- Right side: Action icon -->
                <div class="billing-invoice-action" style="display: flex; align-items: center; justify-content: flex-end;">
                    ${showButton ? `
                        <button 
                            class="billing-download-icon"
                            onclick="downloadInvoice('${invoice.stripe_invoice_id}', '${invoiceNumber}')"
                            aria-label="Download invoice PDF"
                            style="
                                display: inline-flex;
                                align-items: center;
                                justify-content: center;
                                width: 40px;
                                height: 40px;
                                padding: 0;
                                background: transparent;
                                border: none;
                                border-radius: 50%;
                                color: #0066CC;
                                cursor: pointer;
                                transition: all 0.15s ease;
                            "
                            onmouseover="this.style.background='rgba(0, 102, 204, 0.1)'; this.style.transform='scale(1.05)'"
                            onmouseout="this.style.background='transparent'; this.style.transform='scale(1)'"
                        >
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
                            font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                            font-size: 1rem;
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
        
        // Open in new tab - backend will redirect to Stripe PDF
        window.open(url, '_blank');
        
    } catch (error) {
        console.error('❌ Error downloading invoice:', error);
        alert('Failed to download invoice. Please try again or contact support.');
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
                
                displaySubscription(subscription);
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
        
        displaySubscription(subscription);
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
    
    // Get pending_plan from subscription data if provided, otherwise load it
    let pendingPlan = null;
    if (subscriptionData) {
        pendingPlan = subscriptionData.pending_plan || null;
    } else {
        try {
            const subscription = await loadSubscription();
            pendingPlan = subscription.pending_plan || null;
        } catch (error) {
            console.error('Error loading subscription for display:', error);
        }
    }
    
    // Debug logging
    
    const plans = [
        {
            id: 'free',
            name: 'Starter',
            price: 0,
            features: [
                '5 galleries per month',
                '5 GB storage',
                'Client downloads',
                'Photo approval',
                'Comments & feedback',
                'Email notifications',
                'Public profile',
                'Basic analytics'
            ]
        },
        {
            id: 'plus',
            name: 'Plus',
            price: 12,
            features: [
                'Unlimited galleries',
                '50 GB storage',
                'Video support (30 min, up to HD)',
                'Priority email support',
                'All Starter features',
                'Batch photo uploads',
                'Advanced analytics',
                'Custom notifications'
            ]
        },
        {
            id: 'pro',
            name: 'Pro',
            price: 24,
            features: [
                'Unlimited galleries',
                '200 GB storage',
                'Video support (2 hours, up to 4K)',
                'Priority support (12-24h)',
                'Dedicated support',
                'All Plus features',
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
        
        // Define plan pricing for upgrade/downgrade logic
        const planPrices = { 'free': 0, 'plus': 12, 'pro': 24 };
        const currentPrice = planPrices[currentPlanId] || 0;
        const targetPrice = planPrices[plan.id] || 0;
        
        // Determine if upgrade or downgrade based on price
        const isUpgrade = !isCurrentPlan && !isFree && currentPlanId !== 'free' && targetPrice > currentPrice;
        const isDowngrade = !isCurrentPlan && currentPlanId !== 'free' && (targetPrice < currentPrice || plan.id === 'free');
        
        // Check if this is a reactivation scenario (pending_plan='free' but user wants current plan)
        const isReactivation = (
            pendingPlan === 'free' && 
            isCurrentPlan && 
            (plan.id === 'plus' || plan.id === 'pro')
        );
        
        // Debug logging for reactivation detection
        if (isCurrentPlan && (plan.id === 'plus' || plan.id === 'pro')) {
        }
        
        let buttonText = '';
        let buttonClass = 'item-5 idtTuz submit-btn change-plan-btn';
        let buttonStyle = 'margin-top: 24px; width: 100%;';
        
        if (isReactivation) {
            // Show reactivate button instead of "Current Plan"
            buttonText = `Reactivate ${plan.name}`;
            buttonStyle += ' background: linear-gradient(90deg, #0066CC, #0077FF); color: white;';
        } else if (isCurrentPlan) {
            buttonText = 'Current Plan';
            buttonStyle += ' background: #e5e7eb; color: #6b7280; cursor: not-allowed;';
            buttonClass += ' current-plan-btn';
        } else if (isUpgrade || (currentPlanId === 'free' && !isFree)) {
            buttonText = `Upgrade to ${plan.name}`;
            buttonStyle += ' background: linear-gradient(90deg, #0066CC, #0077FF); color: white;';
        } else if (isDowngrade) {
            buttonText = `Downgrade to ${plan.name}`;
            buttonStyle += ' background: #f3f4f6; color: #374151;';
        }
        
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7" ${isCurrentPlan ? 'style="border: 2px solid #0066CC; box-shadow: 0 4px 12px rgba(0,102,204,0.15);"' : ''}>
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <h3 class="grid-15 animation-7">
                            ${plan.name}
                            ${isCurrentPlan ? '<span style="font-size: 14px; color: #0066CC; margin-left: 8px;">(Current)</span>' : ''}
                        </h3>
                        <div class="input-15 background-7">
                            <div style="display: flex; align-items: baseline; margin: 24px 0;">
                                <span style="font-size: 48px; font-weight: 800; line-height: 1;">$${plan.price}</span>
                                <span style="margin-left: 8px; opacity: 0.6;">${plan.price === 0 ? '' : '/month'}</span>
                            </div>
                            <p style="margin-bottom: 32px;">
                                ${plan.id === 'free' ? 'Perfect for getting started' : plan.id === 'plus' ? 'Everything you need to grow' : 'Built for teams and professionals'}
                            </p>
                            <ul style="list-style: none; padding: 0; margin: 24px 0;">
                                ${plan.features.map(feature => `<li style="margin-bottom: 12px;">→ ${feature}</li>`).join('')}
                            </ul>
                            ${buttonText ? `
                                <button type="button" class="${buttonClass}" data-plan="${plan.id}" 
                                    style="${buttonStyle}" ${isCurrentPlan && !isReactivation ? 'disabled' : ''}>
                                    <div class="main-6 jpIyal">
                                        <span>${buttonText}</span>
                                    </div>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Setup event listeners for plan change buttons
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
                    
                    alert(`Subscription reactivated successfully! ${result.message || `Your ${planId} plan is now active again.`}`);
                    location.reload();
                    return;
                } catch (error) {
                    console.error('Error reactivating subscription:', error);
                    const errorMessage = error.message || 'Unknown error';
                    const errorDetails = error.details?.message || '';
                    alert(`Failed to reactivate subscription: ${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`);
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
                        if (!confirm('Are you sure you want to downgrade to Starter plan? You will be downgraded at the end of your current billing period. You will continue to have access to premium features until then. You can upgrade again anytime.')) {
                            return;
                        }
                        // Downgrade without deletion
                        try {
                            const result = await downgradeSubscription([]);
                            alert(`Downgrade scheduled successfully! ${result.message || 'You will be downgraded to Starter plan at the end of your current billing period.'}`);
                            location.reload();
                            return;
                        } catch (error) {
                            console.error('Error downgrading:', error);
                            alert('Failed to downgrade: ' + error.message);
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error checking downgrade limits:', error);
                    alert('Failed to check downgrade requirements: ' + error.message);
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
                            
                            alert(warningMessage);
                            
                            button.disabled = false;
                            buttonText.textContent = originalText;
                            return;
                        }
                        
                        // Limits OK, confirm downgrade
                        const targetPlanName = checkResponse.target_plan_name || planId;
                        if (!confirm(`Are you sure you want to downgrade to ${targetPlanName} plan?\n\nYou will be downgraded at the end of your current billing period. You will continue to have access to your current plan features until then.`)) {
                            button.disabled = false;
                            buttonText.textContent = originalText;
                            return;
                        }
                        
                        buttonText.textContent = 'Processing...';
                    } catch (error) {
                        console.error('Error checking downgrade limits:', error);
                        alert('Failed to check downgrade requirements. Please try again.');
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
                        alert(`Plan change scheduled! ${result.message || `You will be downgraded to ${planId} at the end of your current billing period.`}`);
                    } else {
                        alert(`Plan changed successfully! ${result.message || `Changed from ${currentPlanId} to ${planId}.`} ${result.prorated ? 'The difference has been prorated automatically.' : ''}`);
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
                    
                    alert(alertMessage);
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
                    alert('⚠️ Another subscription change is in progress.\n\nPlease wait a moment and try again.');
                } else {
                    const errorMessage = error.message || 'Unknown error';
                    const errorDetails = error.details?.message || '';
                    alert(`Failed to change plan: ${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`);
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
                alert(`Failed to start checkout: ${errorMessage}${errorDetails ? '\n\n' + errorDetails : ''}`);
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

// Refund functionality
async function checkRefundEligibility() {
    try {
        const result = await window.apiRequest('billing/refund/check');
        
        if (result.eligible) {
            const details = result.details || {};
            const message = `✅ You are eligible for a refund!\n\n` +
                `Purchase Date: ${new Date(details.purchase_date).toLocaleDateString()}\n` +
                `Days since purchase: ${details.days_since_purchase} days\n` +
                `Current usage: ${details.total_storage_gb} GB, ${details.galleries_since_purchase} galleries\n\n` +
                `Would you like to submit a refund request?`;
            
            if (confirm(message)) {
                const reason = prompt('Please provide a detailed reason for your refund request (minimum 10 characters):');
                if (reason && reason.length >= 10) {
                    await submitRefundRequest(reason);
                } else if (reason !== null) {
                    alert('❌ Please provide a reason with at least 10 characters.');
                }
            }
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
            
            alert(`❌ Not Eligible for Refund\n\n${result.reason}${detailsText}\n\nRefund Policy:\n• Available within 14 days of purchase\n• No refund if > 5GB or > 5 galleries used (Starter limits)\n• No refund if > 50GB used (Plus limits)`);
        }
    } catch (error) {
        console.error('Error checking refund eligibility:', error);
        alert('Failed to check refund eligibility. Please try again later or contact support.');
    }
}

async function submitRefundRequest(reason) {
    try {
        const result = await window.apiRequest('billing/refund/request', {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
        
        alert(`✅ Refund Request Submitted\n\n${result.message}\n\nReference ID: ${result.refund_id.substring(0, 8)}\n\nOur team will review your request and respond within 2-3 business days via email.`);
        location.reload();
    } catch (error) {
        console.error('Error submitting refund request:', error);
        const errorMsg = error.message || error.error || 'Unknown error';
        alert(`❌ Failed to submit refund request\n\n${errorMsg}\n\nPlease contact support if the problem persists.`);
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
        alert('Failed to start upgrade process. Please try again.');
    }
}

window.upgradeFromWarning = upgradeFromWarning;

