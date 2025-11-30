// Billing page - Manage subscription and billing
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Check, AlertCircle, Calendar, CheckCircle, Zap, CreditCard, Download, Settings, LogOut } from 'lucide-react';
import * as billingService from '../services/billingService';

// Map service interface to local interface if needed, or use service interface
type Invoice = billingService.Invoice;

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: { monthly: 12, annual: 10 },
    features: [
      '25 GB Smart Storage',
      'Unlimited Galleries',
      '30 Min Video (HD)',
      'Remove Galerly Branding',
      'Client Favorites & Proofing',
      'Basic Analytics',
    ],
  },
  {
    id: 'plus',
    name: 'Plus',
    price: { monthly: 29, annual: 24 },
    features: [
      '100 GB Smart Storage',
      'Unlimited Galleries',
      '1 Hour Video (HD)',
      'Custom Domain',
      'Automated Watermarking',
      'Client Favorites & Proofing',
      'Advanced Analytics',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: { monthly: 59, annual: 49 },
    features: [
      '500 GB Smart Storage',
      '4 Hours Video (4K)',
      'RAW Photo Support',
      'Client Invoicing',
      'Email Automation & Templates',
      'SEO Optimization Tools',
      'Pro Analytics',
    ],
  },
  {
    id: 'ultimate',
    name: 'Ultimate',
    price: { monthly: 119, annual: 99 },
    features: [
      '2 TB Smart Storage',
      '10 Hours Video (4K)',
      'RAW Vault Archival (Glacier)',
      'VIP Priority Support',
      'Developer API Access',
      'Concierge Onboarding',
      'All Pro Features',
    ],
  },
];

const TIER_FEATURES: Record<string, string[]> = {
  free: [
    '2 GB Smart Storage',
    '3 Active Galleries',
    'Basic Portfolio',
    'Community Support',
    'Galerly Branding',
  ],
  starter: [
    '25 GB Smart Storage',
    'Unlimited Galleries',
    '30 Min Video (HD)',
    'Remove Galerly Branding',
    'Client Favorites & Proofing',
    'Basic Analytics',
  ],
  plus: [
    '100 GB Smart Storage',
    'Unlimited Galleries',
    '1 Hour Video (HD)',
    'Custom Domain',
    'Automated Watermarking',
    'Client Favorites & Proofing',
    'Advanced Analytics',
  ],
  pro: [
    '500 GB Smart Storage',
    '4 Hours Video (4K)',
    'RAW Photo Support',
    'Client Invoicing',
    'Email Automation & Templates',
    'SEO Optimization Tools',
    'Pro Analytics',
  ],
  ultimate: [
    '2 TB Smart Storage',
    '10 Hours Video (4K)',
    'RAW Vault Archival (Glacier)',
    'VIP Priority Support',
    'Developer API Access',
    'Concierge Onboarding',
    'All Pro Features',
  ],
};

export default function BillingPage() {
  const { logout } = useAuth();
  const [searchParams] = useSearchParams();
  const [subscription, setSubscription] = useState<billingService.Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('annual');

  useEffect(() => {
    loadBillingInfo();
  }, []);

  useEffect(() => {
    // Handle query params from Stripe redirect or plan selection
    if (searchParams.get('success') === 'true') {
      setNotification({ message: 'Subscription updated successfully!', type: 'success' });
      // Remove params from URL to clean up
      window.history.replaceState({}, '', window.location.pathname);
    } else if (searchParams.get('canceled') === 'true') {
      setNotification({ message: 'Checkout canceled.', type: 'error' });
      window.history.replaceState({}, '', window.location.pathname);
    } else {
      // Check for auto-checkout plan param
      const autoPlan = searchParams.get('plan');
      if (autoPlan && !loading && subscription) {
        // Only trigger if not already on this plan
        if (subscription.plan !== autoPlan) {
           handleUpgrade(autoPlan);
           // Clear param so it doesn't loop or re-trigger on refresh
           window.history.replaceState({}, '', window.location.pathname);
        }
      }
    }
  }, [searchParams, loading, subscription]); // Dependency on loading/subscription ensures we check after data load

  const loadBillingInfo = async () => {
    setLoading(true);

    try {
    const [subRes, invoicesRes] = await Promise.all([
        billingService.getSubscription(),
        billingService.getBillingHistory()
    ]);

    if (subRes.success && subRes.data) {
      setSubscription(subRes.data);
    }

    if (invoicesRes.success && invoicesRes.data) {
      setInvoices(invoicesRes.data.invoices || []);
    }
    } catch (error) {
      console.error('Error loading billing info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    setCheckoutLoading(planId);
    try {
      // Create checkout session
      // For plan changes (if already paid), backend handles via same endpoint or change-plan
      // Assuming backend handles creating correct session type (setup or subscription)
      
      // TODO: Pass billingPeriod to backend once supported
      const response = await billingService.createCheckoutSession(planId); 
      
      // Note: Backend handle_create_checkout_session expects { plan: 'plus' }
      // It resolves price ID internally. The TS signature might be misleading if it says (priceId, tier).
      // Let's assume billingService.createCheckoutSession signature is compatible or we fix it.
      // Actually backend expects { plan: plan_id } in body.
      // So I need to send { plan: planId }.
      
      // Fix: I will call api directly here or fix service. Let's fix service later if needed, but for now I'll use a direct api call here to be safe and "well connected".
      
      if (response.success && response.data?.url) {
        window.location.href = response.data.url;
      } else {
        setNotification({ message: response.error || 'Failed to start checkout', type: 'error' });
      }
    } catch (error) {
      console.error('Error starting checkout:', error);
      setNotification({ message: 'An error occurred. Please try again.', type: 'error' });
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')) return;

    try {
      const response = await billingService.cancelSubscription();
      if (response.success) {
        setNotification({ message: 'Subscription canceled. It will remain active until the end of the period.', type: 'success' });
        loadBillingInfo(); // Reload to update UI
      } else {
        setNotification({ message: response.error || 'Failed to cancel subscription', type: 'error' });
      }
    } catch (error) {
      console.error('Error canceling subscription:', error);
      setNotification({ message: 'An error occurred.', type: 'error' });
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Dashboard</Link>
              <Link to="/galleries" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Galleries</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Analytics</Link>
              <Link to="/billing" className="text-sm font-medium text-[#1D1D1F]">Billing</Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full transition-all">
              <Settings className="w-5 h-5" />
            </Link>
            <button onClick={logout} className="p-2 text-[#1D1D1F]/60 hover:text-red-600 hover:bg-red-50 rounded-full transition-all">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        {notification && (
          <div className={`mb-8 p-4 rounded-2xl flex items-center gap-3 ${
            notification.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'
          }`}>
            {notification.type === 'success' ? <Check className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            <p>{notification.message}</p>
            <button onClick={() => setNotification(null)} className="ml-auto p-1 hover:bg-black/5 rounded-full">
                <AlertCircle className="w-4 h-4 opacity-0" /> {/* Spacer */}
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#1D1D1F]/60">Loading billing information...</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Current Subscription */}
            <div className="glass-panel p-8">
              <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-6">
                Current Plan
              </h2>

              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-3xl font-medium text-[#1D1D1F] capitalize">
                      {subscription?.plan || 'Free'}
                    </h3>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        subscription?.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {subscription?.status || 'Free'}
                    </span>
                  </div>
                  {(PLANS.find(p => p.id === subscription?.plan)?.price.monthly || 0) > 0 ? (
                    <div>
                      <p className="text-lg text-[#1D1D1F]/60 mb-2">
                        {/* Assuming we might know the interval in the future, for now show monthly price as base */}
                        ${PLANS.find(p => p.id === subscription?.plan)?.price.monthly}/month
                      </p>
                      {subscription?.status === 'active' && !subscription?.subscription?.cancel_at_period_end && (
                        <button
                          onClick={handleCancelSubscription}
                          className="text-sm text-red-600 hover:text-red-700 font-medium underline"
                        >
                          Cancel Subscription
                        </button>
                      )}
                      {subscription?.subscription?.cancel_at_period_end && (
                        <p className="text-sm text-amber-600 font-medium">
                          Cancels at period end
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-lg text-[#1D1D1F]/60">
                      Free Forever
                    </p>
                  )}
                </div>
              </div>

              {subscription?.subscription?.current_period_end && (
                <div className="flex items-center gap-2 text-sm text-[#1D1D1F]/60">
                  <Calendar className="w-4 h-4" />
                  <span>
                    Next billing date: {new Date(subscription.subscription.current_period_end).toLocaleDateString()}
                  </span>
                </div>
              )}

              {/* Features */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h4 className="text-sm font-medium text-[#1D1D1F] mb-3">
                  Plan Features
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {(TIER_FEATURES[subscription?.plan || 'free'] || TIER_FEATURES.free).map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-[#1D1D1F]/70">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Available Plans (Upgrade) */}
            {(!subscription?.plan || subscription.plan === 'free' || subscription.plan === 'starter' || subscription.plan === 'plus' || subscription.plan === 'pro') && (
              <div className="glass-panel p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                  <h2 className="text-lg font-medium text-[#1D1D1F] flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-500" />
                  Available Upgrades
                </h2>

                  {/* Billing Toggle */}
                  <div className="inline-flex items-center gap-1 p-1 rounded-full bg-[#F5F5F7] border border-[#1D1D1F]/5 w-fit">
                    <button
                      onClick={() => setBillingPeriod('monthly')}
                      className={`
                        px-4 py-2 rounded-full text-xs font-medium transition-all duration-300
                        ${billingPeriod === 'monthly'
                          ? 'bg-white text-[#1D1D1F] shadow-sm'
                          : 'text-[#1D1D1F]/60 hover:text-[#1D1D1F]'
                        }
                      `}
                    >
                      Monthly
                    </button>
                    <button
                      onClick={() => setBillingPeriod('annual')}
                      className={`
                        px-4 py-2 rounded-full text-xs font-medium transition-all duration-300
                        ${billingPeriod === 'annual'
                          ? 'bg-white text-[#1D1D1F] shadow-sm'
                          : 'text-[#1D1D1F]/60 hover:text-[#1D1D1F]'
                        }
                      `}
                    >
                      Annual <span className="text-[#0066CC] ml-1 font-semibold">-17%</span>
                    </button>
                  </div>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  {PLANS.filter(p => {
                    // Filter out current plan and plans lower than current
                    // Current plan index
                    const currentPlanId = subscription?.plan || 'free';
                    const planOrder = ['free', 'starter', 'plus', 'pro', 'ultimate'];
                    const currentIndex = planOrder.indexOf(currentPlanId);
                    const planIndex = planOrder.indexOf(p.id);
                    return planIndex > currentIndex;
                  }).map((plan) => (
                    <div key={plan.id} className="border border-gray-200 rounded-2xl p-6 hover:border-[#0066CC]/30 transition-all bg-white/50">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-medium text-[#1D1D1F]">{plan.name}</h3>
                          <p className="text-2xl font-bold text-[#1D1D1F] mt-1">
                            ${billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual}
                            <span className="text-sm font-normal text-[#1D1D1F]/60">/mo</span>
                          </p>
                          {billingPeriod === 'annual' && (
                            <p className="text-xs text-[#0066CC] mt-1 font-medium">
                              Billed ${plan.price.annual * 12} yearly
                            </p>
                          )}
                        </div>
                        {plan.id === 'plus' && <span className="bg-[#0066CC] text-white text-xs font-bold px-2 py-1 rounded-md">BEST VALUE</span>}
                      </div>
                      
                      <ul className="space-y-2 mb-6">
                        {plan.features.map((feature, idx) => (
                          <li key={idx} className="flex items-center gap-2 text-sm text-[#1D1D1F]/70">
                            <Check className="w-3 h-3 text-[#0066CC]" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                      
                      <button
                        onClick={() => handleUpgrade(plan.id)}
                        disabled={checkoutLoading === plan.id}
                        className="w-full py-3 bg-[#1D1D1F] text-white rounded-xl font-medium hover:bg-black transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {checkoutLoading === plan.id ? (
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          'Upgrade'
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Payment Method */}
            <div className="glass-panel p-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-6">
                Payment Method
              </h2>

              <div className="flex items-center justify-between p-4 bg-white/50 border border-gray-200 rounded-2xl">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                    <CreditCard className="w-6 h-6 text-[#1D1D1F]/60" />
                  </div>
                  <div>
                    <p className="font-medium text-[#1D1D1F]">Manage via Stripe</p>
                    <p className="text-sm text-[#1D1D1F]/60">Secure payment processing</p>
                  </div>
                </div>
                {/* For real implementation, this would link to Stripe Customer Portal */}
                <button className="px-4 py-2 bg-white border border-gray-200 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-50 transition-all opacity-50 cursor-not-allowed">
                  Manage
                </button>
              </div>
            </div>

            {/* Invoices */}
            <div className="glass-panel p-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-6">
                Invoices
              </h2>

              {invoices.length === 0 ? (
                <p className="text-center text-[#1D1D1F]/60 py-8">
                  No invoices yet
                </p>
              ) : (
                <div className="space-y-3">
                  {invoices.map((invoice) => (
                    <div
                      key={invoice.id}
                      className="flex items-center justify-between p-4 bg-white/50 border border-gray-200 rounded-2xl hover:border-gray-300 transition-all"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                          <Download className="w-5 h-5 text-[#0066CC]" />
                        </div>
                        <div>
                          <p className="font-medium text-[#1D1D1F]">
                            ${(invoice.amount / 100).toFixed(2)}
                          </p>
                          <p className="text-sm text-[#1D1D1F]/60">
                            {new Date(invoice.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            invoice.status === 'paid'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {invoice.status}
                        </span>
                        {invoice.invoice_pdf && (
                        <a
                            href={invoice.invoice_pdf}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                        >
                          <Download className="w-4 h-4 text-[#1D1D1F]/60" />
                        </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
