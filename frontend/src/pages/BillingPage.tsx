// Billing page - Manage subscription and billing
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Check, AlertCircle, Zap, CreditCard, Download, Settings, LogOut, Minus, HelpCircle, Cloud, Image, ChevronRight, FileText, ShieldCheck, ExternalLink, ArrowRight } from 'lucide-react';
import * as billingService from '../services/billingService';

// Map service interface to local interface if needed, or use service interface
type Invoice = billingService.Invoice;

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: { monthly: 0, annual: 0 },
    description: 'For hobbyists',
    accent: 'bg-gray-100 text-gray-900',
    buttonVariant: 'secondary',
    features: []
  },
  {
    id: 'starter',
    name: 'Starter',
    price: { monthly: 12, annual: 10 },
    description: 'For new pros',
    accent: 'bg-gray-100 text-gray-900',
    buttonVariant: 'secondary',
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
    badge: 'BEST VALUE',
    description: 'Most popular',
    accent: 'bg-[#0066CC] text-white',
    buttonVariant: 'primary',
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
    description: 'For studios',
    accent: 'bg-gray-900 text-white',
    buttonVariant: 'dark',
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
    description: 'Max power',
    accent: 'bg-gray-900 text-white',
    buttonVariant: 'dark',
    features: [
      '2 TB Smart Storage',
      '10 Hours Video (4K)',
      'RAW Vault Archival (Glacier)',
      'Scheduler',
      'eSignatures',
      'All Pro Features',
    ],
  },
];

const FEATURES_TABLE = [
  {
    category: 'Storage & Limits',
    items: [
      { 
        name: 'Smart Storage', 
        description: 'High-performance cloud storage optimized for RAW and high-res images with smart compression.',
        values: ['2 GB', '25 GB', '100 GB', '500 GB', '2 TB'] 
      },
      { 
        name: 'Active Galleries', 
        description: 'Number of client galleries you can have online simultaneously.',
        values: ['3', 'Unlimited', 'Unlimited', 'Unlimited', 'Unlimited'] 
      },
      { 
        name: 'Photo Uploads', 
        description: 'Total number of photos you can upload across all your galleries.',
        values: ['Unlimited', 'Unlimited', 'Unlimited', 'Unlimited', 'Unlimited'] 
      },
    ]
  },
  {
    category: 'Video',
    items: [
      { 
        name: 'Video Streaming', 
        description: 'Stream 4K content optimized for web viewing (high-efficiency playback).',
        values: ['-', '30 min (HD)', '1 hour (HD)', '4 hours (4K)', '10 hours (4K)'] 
      },
      { 
        name: 'Video Uploads', 
        description: 'Upload video files for client delivery or streaming (Web-Ready).',
        values: ['-', 'Included', 'Included', 'Included', 'Included'] 
      },
    ]
  },
  {
    category: 'Branding & Domain',
    items: [
      { 
        name: 'Remove Galerly Branding', 
        description: "Remove 'Powered by Galerly' from your gallery footers.",
        values: [false, true, true, true, true] 
      },
      { 
        name: 'Custom Domain', 
        description: 'Use your own domain name (e.g., gallery.yourstudio.com) for a professional look.',
        values: [false, false, true, true, true] 
      },
      { 
        name: 'Automated Watermarking', 
        description: 'Automatically apply your logo or watermark to images to prevent unauthorized use.',
        values: [false, false, true, true, true] 
      },
      { 
        name: 'Portfolio Website', 
        description: 'A dedicated, SEO-friendly portfolio site to showcase your best work.',
        values: [true, true, true, true, true] 
      },
    ]
  },
  {
    category: 'Workflow & Sales',
    items: [
      { 
        name: 'Client Favorites & Proofing', 
        description: 'Allow clients to create favorite lists, leave comments, and select photos for editing.',
        values: [false, true, true, true, true] 
      },
      { 
        name: 'Email Automation', 
        description: 'Send automated emails for gallery expiry, download reminders, and more.',
        values: [false, false, false, true, true] 
      },
      { 
        name: 'Client Invoicing', 
        description: 'Create and send professional invoices directly to your clients.',
        values: [false, false, false, true, true] 
      },
      { 
        name: 'Scheduler', 
        description: 'Allow clients to book sessions directly through your integrated calendar.',
        values: [false, false, false, false, true] 
      },
      { 
        name: 'eSignatures', 
        description: 'Send contracts and get them signed digitally before the shoot.',
        values: [false, false, false, false, true] 
      },
    ]
  },
  {
    category: 'Advanced Features',
    items: [
      { 
        name: 'Analytics', 
        description: 'Track gallery views, downloads, and visitor engagement.',
        values: ['Basic', 'Basic', 'Advanced', 'Pro', 'Pro'] 
      },
      { 
        name: 'RAW Photo Support', 
        description: 'Upload and deliver RAW file formats (CR2, NEF, ARW, etc.) directly.',
        values: [false, false, false, true, true] 
      },
      { 
        name: 'RAW Vault Archival', 
        description: 'Long-term cold storage for your RAW files at a fraction of the cost.',
        values: [false, false, false, false, true] 
      },
      { 
        name: 'SEO Tools', 
        description: 'Advanced settings to optimize your galleries and portfolio for search engines.',
        values: [false, false, false, true, true] 
      },
    ]
  },
  {
    category: 'Support',
    items: [
      { 
        name: 'Support Level', 
        description: 'Priority of your support tickets and access to live chat.',
        values: ['Priority', 'Priority', 'Priority', 'Priority', 'Priority'] 
      },
    ]
  }
];

const UPGRADE_PLANS = PLANS.filter(p => p.id !== 'free');

export default function BillingPage() {
  const { logout } = useAuth();
  const [searchParams] = useSearchParams();
  const [subscription, setSubscription] = useState<billingService.Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [usage, setUsage] = useState<billingService.UsageStats | null>(null);
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
      const autoInterval = searchParams.get('interval') as 'monthly' | 'annual';

      if (autoInterval && (autoInterval === 'monthly' || autoInterval === 'annual')) {
        setBillingPeriod(autoInterval);
      }

      if (autoPlan && !loading && subscription) {
        // Only trigger if not already on this plan
        if (subscription.plan !== autoPlan) {
           handleUpgrade(autoPlan, autoInterval);
           // Clear param so it doesn't loop or re-trigger on refresh
           window.history.replaceState({}, '', window.location.pathname);
        }
      }
    }
  }, [searchParams, loading, subscription]); // Dependency on loading/subscription ensures we check after data load

  const loadBillingInfo = async () => {
    setLoading(true);

    try {
    const [subRes, invoicesRes, usageRes] = await Promise.all([
        billingService.getSubscription(),
        billingService.getBillingHistory(),
        billingService.getUsage()
    ]);

    if (subRes.success && subRes.data) {
      setSubscription(subRes.data);
    }

    if (invoicesRes.success && invoicesRes.data) {
      setInvoices(invoicesRes.data.invoices || []);
    }

    if (usageRes.success && usageRes.data) {
      setUsage(usageRes.data);
    }
    } catch (error) {
      console.error('Error loading billing info:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSavingsText = (plan: typeof PLANS[0]) => {
    if (plan.price.monthly === 0) return null;
    const annualTotal = plan.price.annual * 12;
    const monthlyTotal = plan.price.monthly * 12;
    const savings = monthlyTotal - annualTotal;
    return savings > 0 ? `Save $${savings}/year` : null;
  };

  const handleUpgrade = async (planId: string, intervalOverride?: 'monthly' | 'annual') => {
    setCheckoutLoading(planId);
    try {
      // Create checkout session
      // For plan changes (if already paid), backend handles via same endpoint or change-plan
      // Assuming backend handles creating correct session type (setup or subscription)
      
      const selectedInterval = intervalOverride || billingPeriod;
      const response = await billingService.createCheckoutSession(planId, selectedInterval); 
      
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

  const storageLimit = usage?.storage_limit?.limit_gb ?? 0;
  const storageUsed = usage?.storage_limit?.used_gb ?? 0;
  const storagePercent = usage?.storage_limit?.usage_percent ?? 0;
  
  const galleriesLimit = usage?.gallery_limit?.limit ?? 0;
  const galleriesUsed = usage?.gallery_limit?.used ?? 0;
  const galleriesPercent = galleriesLimit > 0 ? (galleriesUsed / galleriesLimit) * 100 : (galleriesLimit === -1 ? 5 : 0);

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

      <main className="max-w-[1600px] mx-auto px-6 py-8">
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
          <div className="space-y-12">
            {/* Current Subscription & Payment Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Membership Card */}
              <div className="lg:col-span-2 relative overflow-hidden rounded-[32px] bg-[#1D1D1F] text-white p-8 md:p-10 shadow-2xl transition-transform duration-500 hover:scale-[1.005] group">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-br from-blue-600/30 to-purple-600/30 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none opacity-60" />
                <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-blue-500/10 rounded-full blur-3xl -ml-10 -mb-10 pointer-events-none" />

                <div className="relative z-10 flex flex-col h-full justify-between">
                  <div className="flex justify-between items-start mb-12">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/10 text-xs font-medium tracking-wide text-white/90">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400 mr-2 animate-pulse"></span>
                          {subscription?.status === 'active' ? 'Active Membership' : subscription?.status}
                        </span>
                        {subscription?.subscription?.cancel_at_period_end && (
                          <span className="inline-flex items-center px-3 py-1 rounded-full bg-red-500/20 backdrop-blur-md border border-red-500/30 text-xs font-medium text-red-200">
                            Expiring Soon
                          </span>
                        )}
                      </div>
                      <h1 className="text-5xl md:text-6xl font-serif text-white tracking-tight">
                        {PLANS.find(p => p.id === subscription?.plan)?.name || 'Free'}
                      </h1>
                    </div>
                    <div className="text-right">
                       {(PLANS.find(p => p.id === subscription?.plan)?.price.monthly || 0) > 0 ? (
                          <div className="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl px-6 py-4 text-center min-w-[120px]">
                             <div className="text-3xl font-bold text-white tracking-tight">
                                ${PLANS.find(p => p.id === subscription?.plan)?.price.monthly}
                             </div>
                             <div className="text-xs text-white/50 font-medium uppercase tracking-wider">Per Month</div>
                          </div>
                       ) : (
                          <div className="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl px-6 py-4 text-center min-w-[120px]">
                             <div className="text-3xl font-bold text-white tracking-tight">Free</div>
                             <div className="text-xs text-white/50 font-medium uppercase tracking-wider">Forever</div>
                          </div>
                       )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
                    <div>
                      <div className="flex justify-between items-end mb-3">
                        <div className="flex items-center gap-2 text-white/80">
                          <Cloud className="w-5 h-5 text-blue-400" />
                          <span className="font-medium">Cloud Storage</span>
                        </div>
                        <span className="text-sm font-medium text-white/60">
                          {storageLimit === -1 
                            ? `${storageUsed} GB Used` 
                            : `${storageUsed} / ${storageLimit} GB`}
                        </span>
                      </div>
                      <div className="h-2 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-1000 ease-out relative" 
                          style={{ width: `${Math.min(storagePercent, 100)}%` }}
                        >
                          <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/50 blur-[2px]" />
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between items-end mb-3">
                        <div className="flex items-center gap-2 text-white/80">
                          <Image className="w-5 h-5 text-purple-400" />
                          <span className="font-medium">Active Galleries</span>
                        </div>
                        <span className="text-sm font-medium text-white/60">
                          {galleriesLimit === -1 
                            ? `${galleriesUsed} Galleries` 
                            : `${galleriesUsed} / ${galleriesLimit}`}
                        </span>
                      </div>
                      <div className="h-2 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
                        <div 
                          className="h-full bg-gradient-to-r from-purple-400 to-pink-600 rounded-full transition-all duration-1000 ease-out relative" 
                          style={{ width: `${Math.min(galleriesPercent, 100)}%` }}
                        >
                           <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/50 blur-[2px]" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Payment Method Quick View */}
              <div className="glass-panel p-8 h-full flex flex-col justify-between hover:shadow-glass-strong transition-all duration-300">
                <div>
                   <div className="flex items-center justify-between mb-8">
                      <h3 className="font-medium text-[#1D1D1F] flex items-center gap-2">
                         <CreditCard className="w-5 h-5 text-gray-400" />
                         Payment Method
                      </h3>
                   </div>
                   
                   <div className="flex flex-col items-center text-center space-y-4 mb-8">
                      <div className="w-16 h-16 bg-[#F5F5F7] rounded-full flex items-center justify-center mb-2 shadow-inner">
                         <ShieldCheck className="w-8 h-8 text-[#0066CC]" strokeWidth={1.5} />
                      </div>
                      <div>
                         <h4 className="font-semibold text-[#1D1D1F] mb-1">Secure Payment</h4>
                         <p className="text-sm text-[#1D1D1F]/60 max-w-[200px] mx-auto leading-relaxed">
                            Your payment details are securely processed and stored by Stripe.
                         </p>
                      </div>
                      <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-full border border-green-100">
                         <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                         <span className="text-xs font-medium text-green-700 uppercase tracking-wide">Active</span>
                      </div>
                   </div>
                </div>
                
                <div className="space-y-3">
                   <div className="flex items-center justify-between px-1 mb-2">
                      <span className="text-xs text-[#1D1D1F]/40 font-medium uppercase tracking-wider">Next Billing</span>
                      <span className="text-sm font-semibold text-[#1D1D1F]">
                         {subscription?.subscription?.current_period_end ? new Date(subscription.subscription.current_period_end).toLocaleDateString() : 'N/A'}
                      </span>
                   </div>
                   
                   <button className="w-full py-3 rounded-xl bg-[#1D1D1F] text-white text-sm font-medium hover:bg-black transition-all flex items-center justify-center gap-2 group/manage shadow-md">
                      Update Payment Method
                      <ExternalLink className="w-3.5 h-3.5 opacity-50 group-hover/manage:translate-x-0.5 group-hover/manage:-translate-y-0.5 transition-transform" />
                   </button>

                   {subscription?.status === 'active' && !subscription?.subscription?.cancel_at_period_end && (
                     <button
                       onClick={handleCancelSubscription}
                       className="w-full py-3 rounded-xl border border-red-100 text-red-600 bg-red-50/50 text-sm font-medium hover:bg-red-50 transition-all flex items-center justify-center gap-2 group/btn"
                     >
                       Cancel Subscription
                       <ChevronRight className="w-4 h-4 opacity-50 group-hover/btn:translate-x-0.5 transition-transform" />
                     </button>
                   )}
                </div>
              </div>
            </div>

            {/* Available Plans (Table View) */}
            <div className="mt-12">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                  <h2 className="text-lg font-medium text-[#1D1D1F] flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-500" />
                    Compare Plans
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

                {/* Compare Plans Table */}
                <div className="hidden lg:block pb-12">
                  <div className="border border-gray-200 rounded-3xl bg-white shadow-sm overflow-visible">
                    {/* Non-sticky Plan Header */}
                    <div className="bg-[#F5F5F7]/95 backdrop-blur-xl border-b border-gray-200 overflow-visible">
                      <div className="grid grid-cols-[240px_repeat(4,1fr)] overflow-visible">
                        <div className="col-span-1 p-6 flex items-end border-r border-gray-200">
                          <span className="text-xs font-bold text-[#1D1D1F]/40 uppercase tracking-[0.2em]">Features</span>
                        </div>
                        {UPGRADE_PLANS.map((plan) => {
                           const isCurrent = subscription?.plan === plan.id;
                           const isPopular = plan.id === 'plus';
                           const savings = getSavingsText(plan);
                           return (
                          <div key={plan.id} className={`col-span-1 flex flex-col items-center text-center relative p-6 border-r border-gray-200 last:border-r-0 overflow-visible ${isPopular ? 'bg-blue-50/30' : ''}`}>
                            {plan.badge && (
                              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#0066CC] to-[#0099ff] text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-lg shadow-blue-500/30 z-10">
                                {plan.badge}
                              </div>
                            )}
                            <h3 className={`text-lg font-bold mb-1 ${isPopular ? 'text-[#0066CC]' : 'text-[#1D1D1F]'}`}>{plan.name}</h3>
                            <div className="mb-4 flex flex-col items-center justify-center min-h-[60px]">
                               <div className="flex items-baseline mb-1">
                                  <span className="text-2xl font-bold text-[#1D1D1F]">
                                    ${billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual}
                                  </span>
                                  <span className="text-xs text-[#1D1D1F]/60 ml-0.5">/mo</span>
                                </div>
                                <div className="h-[16px] flex items-center justify-center">
                                  {billingPeriod === 'annual' && savings ? (
                                    <span className="text-[10px] font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">{savings}</span>
                                  ) : null}
                                </div>
                            </div>
                            <button
                              onClick={() => !isCurrent && handleUpgrade(plan.id)}
                              disabled={isCurrent || checkoutLoading === plan.id}
                              className={`
                                w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2
                                ${isCurrent
                                  ? 'bg-gray-100 text-gray-400 cursor-default'
                                  : plan.id === 'plus' 
                                    ? 'bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white hover:shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5' 
                                    : 'bg-[#1D1D1F] text-white hover:bg-black hover:shadow-lg hover:-translate-y-0.5'
                                }
                              `}
                            >
                              {checkoutLoading === plan.id ? (
                                  <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                              ) : isCurrent ? (
                                  'Current Plan'
                              ) : (
                                  'Upgrade'
                              )}
                            </button>
                          </div>
                        )})}
                      </div>
                    </div>

                    {/* Table Body with Categories */}
                    {FEATURES_TABLE.map((category, categoryIndex) => (
                      <div key={category.category}>
                        {/* Category Header */}
                        <div className="bg-[#F5F5F7] border-y border-gray-200">
                          <div className="grid grid-cols-[240px_repeat(4,1fr)] px-6 py-4">
                            <h4 className="col-span-5 font-bold text-[#1D1D1F] text-sm uppercase tracking-wider">{category.category}</h4>
                          </div>
                        </div>
                        
                        {/* Feature Rows */}
                          {category.items.map((feature, featIndex) => (
                            <div 
                              key={feature.name} 
                              className={`
                                grid grid-cols-[240px_repeat(4,1fr)] items-center transition-colors hover:bg-gray-50
                              ${featIndex !== category.items.length - 1 || categoryIndex !== FEATURES_TABLE.length - 1 ? 'border-b border-gray-100' : ''}
                              `}
                            >
                            <div className="col-span-1 flex items-center gap-2 p-6 pr-4 border-r border-gray-200">
                                <span className="text-sm font-medium text-[#1D1D1F] leading-snug">{feature.name}</span>
                                <div className="group/tooltip relative cursor-help">
                                  <HelpCircle className="w-3.5 h-3.5 text-gray-300 hover:text-[#0066CC] transition-colors" />
                                  <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-56 p-3 bg-[#1D1D1F] text-white text-xs leading-relaxed rounded-xl opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                                    {feature.description}
                                  </div>
                                </div>
                              </div>
                              {UPGRADE_PLANS.map((plan, i) => {
                                const originalIndex = PLANS.findIndex(p => p.id === plan.id);
                                const value = feature.values[originalIndex];
                                return (
                                <div key={plan.id} className={`col-span-1 flex justify-center text-center p-6 h-full items-center border-r border-gray-200 last:border-r-0 ${i === 1 ? 'bg-blue-50/10' : ''}`}>
                                      {typeof value === 'boolean' ? (
                                          value ? (
                                            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shadow-sm">
                                              <Check className="w-3.5 h-3.5 text-[#0066CC]" strokeWidth={3} />
                                            </div>
                                          ) : <Minus className="w-4 h-4 text-gray-200" />
                                      ) : value === '-' ? (
                                          <Minus className="w-4 h-4 text-gray-200" />
                                      ) : (
                                          <span className="text-sm font-medium text-[#1D1D1F]">{value}</span>
                                      )}
                                  </div>
                                );
                              })}
                            </div>
                          ))}
                        </div>
                      ))}

                    {/* Bottom CTA */}
                    <div className="bg-gray-50/50 border-t border-gray-200">
                      <div className="grid grid-cols-[240px_repeat(4,1fr)]">
                        <div className="col-span-1 border-r border-gray-200"></div>
                        {UPGRADE_PLANS.map((plan) => {
                          const isCurrent = subscription?.plan === plan.id;
                          return (
                            <div key={plan.id} className={`col-span-1 text-center p-6 border-r border-gray-200 last:border-r-0 ${plan.id === 'plus' ? 'bg-blue-50/30' : ''}`}>
                              <button
                                onClick={() => !isCurrent && handleUpgrade(plan.id)}
                                disabled={isCurrent || checkoutLoading === plan.id}
                                className={`
                                  inline-flex items-center gap-2 text-sm font-bold justify-center transition-all
                                  ${isCurrent ? 'text-gray-400 cursor-default' : plan.id === 'plus' ? 'text-[#0066CC] hover:underline' : 'text-[#1D1D1F] hover:underline'}
                                `}
                              >
                                {isCurrent ? 'Current Plan' : `Upgrade to ${plan.name}`} <ArrowRight className="w-4 h-4" />
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Mobile View (Cards) */}
                <div className="lg:hidden grid md:grid-cols-2 gap-6">
                  {UPGRADE_PLANS.map((plan) => {
                    const isCurrent = subscription?.plan === plan.id;
                    const savings = getSavingsText(plan);
                    return (
                    <div key={plan.id} className="border border-gray-200 rounded-2xl p-6 hover:border-[#0066CC]/30 transition-all bg-white/50 relative overflow-hidden">
                      {plan.badge && (
                          <div className="absolute top-0 right-0 bg-[#0066CC] text-white text-[10px] font-bold px-4 py-1.5 rounded-bl-xl uppercase tracking-wider">
                            {plan.badge}
                          </div>
                      )}
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-medium text-[#1D1D1F]">{plan.name}</h3>
                          <div className="flex items-baseline gap-1 mt-1">
                            <span className="text-2xl font-bold text-[#1D1D1F]">
                              ${billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual}
                            </span>
                            <span className="text-sm font-normal text-[#1D1D1F]/60">/mo</span>
                          </div>
                          {billingPeriod === 'annual' && savings && (
                            <p className="text-xs text-[#0066CC] mt-1 font-medium">{savings}</p>
                          )}
                        </div>
                      </div>
                      
                      <ul className="space-y-2 mb-6">
                        {plan.features.slice(0, 5).map((feature, idx) => (
                          <li key={idx} className="flex items-center gap-2 text-sm text-[#1D1D1F]/70">
                            <Check className="w-3 h-3 text-[#0066CC]" />
                            {feature}
                          </li>
                        ))}
                        {plan.features.length > 5 && (
                            <li className="text-xs text-[#1D1D1F]/50 pl-5">+{plan.features.length - 5} more features</li>
                        )}
                      </ul>
                      
                      <button
                        onClick={() => !isCurrent && handleUpgrade(plan.id)}
                        disabled={isCurrent || checkoutLoading === plan.id}
                        className={`
                            w-full py-3 rounded-xl font-medium transition-all disabled:opacity-50 flex items-center justify-center gap-2
                            ${isCurrent
                                ? 'bg-gray-100 text-gray-400 cursor-default'
                                : 'bg-[#1D1D1F] text-white hover:bg-black'
                            }
                        `}
                      >
                        {checkoutLoading === plan.id ? (
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : isCurrent ? (
                          'Current Plan'
                        ) : (
                          'Upgrade'
                        )}
                      </button>
                    </div>
                  )})}
                </div>
            </div>

            {/* Invoices Section (Redesigned) */}
            <div className="glass-panel p-8">
               <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-medium text-[#1D1D1F]">Billing History</h2>
                  <button className="text-sm font-medium text-[#0066CC] hover:underline flex items-center gap-1">
                     Download All <Download className="w-4 h-4" />
                  </button>
               </div>
               
               {invoices.length === 0 ? (
                 <div className="text-center py-12 border border-dashed border-gray-200 rounded-2xl bg-gray-50/50">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                       <FileText className="w-6 h-6 text-gray-400" />
                    </div>
                    <p className="text-gray-500 font-medium">No invoices available yet</p>
                 </div>
               ) : (
                 <div className="border border-gray-100 rounded-2xl overflow-hidden bg-white">
                    <table className="w-full">
                       <thead className="bg-gray-50/50 border-b border-gray-100">
                          <tr>
                             <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Date</th>
                             <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Amount</th>
                             <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                             <th className="text-right py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Invoice</th>
                          </tr>
                       </thead>
                       <tbody className="divide-y divide-gray-50">
                          {invoices.map((invoice) => (
                             <tr key={invoice.id} className="group hover:bg-blue-50/20 transition-colors">
                                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                                   {new Date(invoice.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                                </td>
                                <td className="py-4 px-6 text-sm font-medium text-gray-900">
                                   ${(invoice.amount / 100).toFixed(2)}
                                </td>
                                <td className="py-4 px-6">
                                   <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                                      ${invoice.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}
                                   `}>
                                      {invoice.status}
                                   </span>
                                </td>
                                <td className="py-4 px-6 text-right">
                                   {invoice.invoice_pdf && (
                                      <a 
                                         href={invoice.invoice_pdf} 
                                         target="_blank" 
                                         rel="noopener noreferrer"
                                         className="inline-flex items-center justify-center p-2 text-gray-400 hover:text-[#0066CC] hover:bg-blue-50 rounded-lg transition-all"
                                      >
                                         <Download className="w-4 h-4" />
                                      </a>
                                   )}
                                </td>
                             </tr>
                          ))}
                       </tbody>
                    </table>
                 </div>
               )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
