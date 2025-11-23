/**
 * Pricing Page - Display plans with consistent design
 * 
 * SUBSCRIPTION STATE TRANSITIONS
 * ================================
 * 
 * Plans: Starter (free), Plus ($12), Pro ($24)
 * Actions: Subscribe, Upgrade, Downgrade, Cancel, Refund, Reactivate
 * 
 * 1. INITIAL SUBSCRIPTIONS:
 *    - No subscription → Starter (free, default)
 *    - No subscription → Plus ($12/month)
 *    - No subscription → Pro ($24/month)
 * 
 * 2. UPGRADES (immediate effect):
 *    - Starter → Plus
 *    - Starter → Pro
 *    - Plus → Pro
 * 
 * 3. DOWNGRADES (effective at period end):
 *    - Pro → Plus
 *    - Pro → Starter
 *    - Plus → Starter
 * 
 * 4. CANCELLATION:
 *    - Any paid plan → Cancel → Reverts to Starter at period end
 *    - Cancel → Reactivate → Restores original plan
 * 
 * 5. REFUNDS:
 *    - Any paid plan → Request refund → Pending approval
 *    - Refund approved → Subscription cancelled immediately
 *    - Refund denied → Subscription continues
 * 
 * 6. COMMON USER JOURNEYS:
 * 
 *    From Starter:
 *    - Starter → Plus
 *    - Starter → Plus → Cancel → Reactivate
 *    - Starter → Plus → Pro
 *    - Starter → Plus → Pro → Cancel
 *    - Starter → Pro
 *    - Starter → Pro → Cancel
 *    - Starter → Pro → Plus (downgrade)
 * 
 *    From Plus:
 *    - Plus → Pro
 *    - Plus → Pro → Cancel → Reactivate
 *    - Plus → Starter (downgrade)
 *    - Plus → Cancel → Starter (at period end)
 *    - Plus → Refund → Starter (immediate)
 * 
 *    From Pro:
 *    - Pro → Plus (downgrade)
 *    - Pro → Plus → Cancel
 *    - Pro → Plus → Starter (downgrade)
 *    - Pro → Starter (downgrade)
 *    - Pro → Cancel → Starter (at period end)
 *    - Pro → Refund → Starter (immediate)
 * 
 * 7. COMPLEX MULTI-STEP TRANSITIONS:
 *    - Plan A → Plan B → Plan C
 *    - Plan A → Plan B → Cancel → Reactivate
 *    - Plan A → Plan B → Refund → Cancel
 *    - Plan A → Cancel → Reactivate → Plan B
 *    - Plan A → Downgrade to Plan B (scheduled) → Cancel downgrade → Stay on Plan A
 * 
 * 8. EDGE CASES:
 *    - Pending downgrade + Cancel = Downgrade cancelled, subscription ends at period end
 *    - Pending downgrade + Upgrade = New upgrade applied immediately, downgrade cancelled
 *    - Active paid plan + Refund request = Subscription continues until refund approved
 *    - Cancelled subscription + Reactivate = Original plan restored with same billing date
 * 
 * BUTTON STATES ON PRICING PAGE:
 * - Not authenticated: "Start Free" or "Start Free Trial" → /auth
 * - Authenticated (any plan): All buttons show "View Billing" → /billing
 * 
 * This keeps the pricing page simple - authenticated users manage everything from billing page.
 */

// Display all plans with the same design as billing page
async function displayPricingPlans() {
    const container = document.getElementById('plans-container');
    if (!container) return;
    
    // Check if user is authenticated
    const isAuth = window.isAuthenticated ? await window.isAuthenticated() : false;
    
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
                'All Starter features',
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
                'All Plus features',
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
    
    // Responsive sizing
    const isSmallMobile = window.innerWidth < 400;
    const priceSize = isSmallMobile ? '2.5rem' : '3rem';
    const featureSize = isSmallMobile ? '0.875rem' : '0.9375rem';
    
    plans.forEach(plan => {
        const isFree = plan.id === 'free';
        
        // Determine button text and action
        let buttonText = '';
        let buttonHref = '#';
        let buttonClass = 'image-18 nav-6 container-0'; // Primary button style
        
        if (!isAuth) {
            // Not authenticated - show signup/trial buttons
            buttonText = isFree ? 'Start Free' : 'Start Free Trial';
            buttonHref = 'auth';
        } else {
            // Authenticated - all buttons go to billing page
            buttonText = 'View Billing';
            buttonClass = 'logo-18 list-5'; // Secondary button style
            buttonHref = 'billing';
        }
        
        html += `
            <div class="card-18 hero-10 animation-11 textarea-7">
                <div class="button-18 list-7">
                    <div class="container-15 item-7">
                        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
                            <h3 class="grid-15 animation-7" style="margin: 0;">${plan.name}</h3>
                            ${plan.badge ? `<span style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.6875rem;
                                font-weight: 600;
                                padding: 3px 10px;
                                background: #0066CC;
                                color: white;
                                border-radius: 10px;
                            ">${plan.badge}</span>` : ''}
                        </div>
                        <div class="input-15 background-7">
                            <div style="display: flex; align-items: baseline; margin-bottom: 12px;">
                                <span style="
                                    font-family: SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif;
                                    font-size: ${priceSize};
                                    font-weight: 800;
                                    line-height: 1;
                                    color: #1D1D1F;
                                ">$${plan.price}</span>
                                ${plan.price > 0 ? `<span style="
                                    font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                    font-size: 0.875rem;
                                    color: #86868B;
                                    margin-left: 6px;
                                ">/month</span>` : ''}
                            </div>
                            <p style="
                                font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                font-size: 0.875rem;
                                color: #86868B;
                                margin-bottom: 24px;
                            ">${plan.description}</p>
                            <ul style="list-style: none; padding: 0; margin: 24px 0;">
                                ${plan.features.map(feature => `
                                    <li style="
                                        font-family: SF Pro Text, -apple-system, BlinkMacSystemFont, sans-serif;
                                        font-size: ${featureSize};
                                        color: #1D1D1F;
                                        margin-bottom: 10px;
                                        display: flex;
                                        align-items: flex-start;
                                    ">
                                        <img src="/img/checkmark.svg" alt="checkmark" style="width: 16px; height: 16px; margin-right: 10px; flex-shrink: 0; margin-top: 2px;" />
                                        <span style="flex: 1;">${feature}</span>
                                    </li>
                                `).join('')}
                            </ul>
                            <a aria-label="${buttonText}" 
                                class="${buttonClass}" 
                                href="${buttonHref}">
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
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', displayPricingPlans);
} else {
    displayPricingPlans();
}

// Re-render on window resize for responsive text
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(displayPricingPlans, 250);
});

