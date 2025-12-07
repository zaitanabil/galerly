// Pricing page - Detailed table layout
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, ArrowRight, Minus, HelpCircle } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('annual');

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: { monthly: 0, annual: 0 },
      description: 'For hobbyists',
      accent: 'bg-gray-100 text-gray-900',
      buttonVariant: 'secondary'
    },
    {
      id: 'starter',
      name: 'Starter',
      price: { monthly: 12, annual: 10 },
      description: 'For new pros',
      accent: 'bg-gray-100 text-gray-900',
      buttonVariant: 'secondary'
    },
    {
      id: 'plus',
      name: 'Plus',
      price: { monthly: 29, annual: 24 },
      badge: 'BEST VALUE',
      description: 'Most popular',
      accent: 'bg-[#0066CC] text-white',
      buttonVariant: 'primary'
    },
    {
      id: 'pro',
      name: 'Pro',
      price: { monthly: 59, annual: 49 },
      description: 'For studios',
      accent: 'bg-gray-900 text-white',
      buttonVariant: 'dark'
    },
    {
      id: 'ultimate',
      name: 'Ultimate',
      price: { monthly: 119, annual: 99 },
      description: 'Max power',
      accent: 'bg-gray-900 text-white',
      buttonVariant: 'dark'
    }
  ];

  const features = [
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
          description: 'Send automated emails for selection reminders, download notifications, and custom messages.',
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

  const getSavingsText = (plan: typeof plans[0]) => {
    if (plan.price.monthly === 0) return null;
    const annualTotal = plan.price.annual * 12;
    const monthlyTotal = plan.price.monthly * 12;
    const savings = monthlyTotal - annualTotal;
    return savings > 0 ? `Save $${savings}/year` : null;
  };

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-4 md:px-6">
        <div className="max-w-[1400px] mx-auto">
          
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-6xl font-medium text-[#1D1D1F] mb-6 tracking-tight">
              Pricing & Plans
            </h1>
            
            <p className="text-xl text-[#1D1D1F]/60 max-w-2xl mx-auto mb-10">
              Choose the perfect plan for your photography business.
              <br className="hidden md:block" /> Upgrade, downgrade, or cancel anytime.
            </p>

            {/* Billing Toggle */}
            <div className="inline-flex items-center gap-1 p-1.5 rounded-full bg-[#F5F5F7] border border-[#1D1D1F]/5">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`
                  px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300
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
                  px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300
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

          {/* Pricing Table - Desktop */}
          <div className="hidden lg:block pb-12">
            <div className="border border-gray-200 rounded-3xl bg-white shadow-sm overflow-visible">
              {/* Non-sticky Plan Header */}
              <div className="bg-white/95 backdrop-blur-xl border-b border-gray-200 overflow-visible">
                <div className="grid grid-cols-[240px_repeat(5,1fr)] overflow-visible">
                  <div className="col-span-1 p-6 flex items-end border-r border-gray-100">
                    <span className="text-xs font-bold text-[#1D1D1F]/40 uppercase tracking-[0.2em]">Features</span>
                  </div>
                  {plans.map((plan) => {
                    const savings = getSavingsText(plan);
                    return (
                    <div key={plan.id} className={`col-span-1 flex flex-col items-center text-center relative p-6 border-r border-gray-100 last:border-r-0 overflow-visible ${plan.id === 'plus' ? 'bg-blue-50/30' : ''}`}>
                      {plan.badge && (
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#0066CC] to-[#0099ff] text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-lg shadow-blue-500/30 z-10">
                          {plan.badge}
                        </div>
                      )}
                      <h3 className={`text-lg font-bold mb-1 ${plan.id === 'plus' ? 'text-[#0066CC]' : 'text-[#1D1D1F]'}`}>{plan.name}</h3>
                      <div className="mb-4 flex flex-col items-center justify-center min-h-[60px]">
                        <div className="flex items-baseline mb-1">
                          <span className="text-2xl font-bold text-[#1D1D1F]">
                            ${billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual}
                          </span>
                          <span className="text-xs text-[#1D1D1F]/60 ml-0.5">{plan.price.monthly > 0 ? '/mo' : ''}</span>
                        </div>
                        <div className="h-[16px] flex items-center justify-center">
                          {billingPeriod === 'annual' && savings ? (
                            <span className="text-[10px] font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">{savings}</span>
                          ) : null}
                        </div>
                      </div>
                      <Link
                        to={`/register?plan=${plan.id}&interval=${billingPeriod}`}
                        className={`
                          w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center
                          ${plan.id === 'plus' 
                            ? 'bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white hover:shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5' 
                            : plan.id === 'pro' || plan.id === 'ultimate'
                              ? 'bg-[#1D1D1F] text-white hover:bg-black hover:shadow-lg hover:-translate-y-0.5'
                              : 'bg-gray-100 text-[#1D1D1F] hover:bg-gray-200'
                          }
                        `}
                      >
                        {plan.price.monthly === 0 ? 'Start Free' : 'Choose'}
                      </Link>
                    </div>
                  )})}
                </div>
              </div>

              {/* Table Body with Categories */}
              {features.map((category, categoryIndex) => (
                <div key={category.category}>
                  {/* Category Header */}
                  <div className="bg-[#F5F5F7] border-y border-gray-200">
                    <div className="grid grid-cols-[240px_repeat(5,1fr)] px-6 py-4">
                      <h4 className="col-span-6 font-bold text-[#1D1D1F] text-sm uppercase tracking-wider">{category.category}</h4>
                    </div>
                  </div>
                  
                  {/* Feature Rows */}
                  {category.items.map((feature, featIndex) => (
                    <div 
                      key={feature.name} 
                      className={`
                        grid grid-cols-[240px_repeat(5,1fr)] items-center transition-colors hover:bg-gray-50
                        ${featIndex !== category.items.length - 1 || categoryIndex !== features.length - 1 ? 'border-b border-gray-100' : ''}
                      `}
                    >
                      <div className="col-span-1 flex items-center gap-2 p-6 pr-4 border-r border-gray-100">
                        <span className="text-sm font-medium text-[#1D1D1F] leading-snug">{feature.name}</span>
                        <div className="group/tooltip relative cursor-help">
                          <HelpCircle className="w-3.5 h-3.5 text-gray-300 hover:text-[#0066CC] transition-colors" />
                          <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-56 p-3 bg-[#1D1D1F] text-white text-xs leading-relaxed rounded-xl opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                            {feature.description}
                          </div>
                        </div>
                      </div>
                      {feature.values.map((val, i) => (
                        <div key={i} className={`col-span-1 flex justify-center text-center p-6 h-full items-center border-r border-gray-100 last:border-r-0 ${i === 2 ? 'bg-blue-50/10' : ''}`}>
                          {typeof val === 'boolean' ? (
                            val ? (
                              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center shadow-sm">
                                <Check className="w-3.5 h-3.5 text-[#0066CC]" strokeWidth={3} />
                              </div>
                            ) : (
                              <Minus className="w-4 h-4 text-gray-200" />
                            )
                          ) : val === '-' ? (
                            <Minus className="w-4 h-4 text-gray-200" />
                          ) : (
                            <span className="text-sm font-medium text-[#1D1D1F]">{val}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}

              {/* Bottom CTA */}
              <div className="bg-gray-50/50 border-t border-gray-200">
                <div className="grid grid-cols-[240px_repeat(5,1fr)] p-0">
                  <div className="col-span-1 border-r border-gray-100"></div>
                  {plans.map((plan) => (
                    <div key={plan.id} className={`col-span-1 text-center p-6 border-r border-gray-100 last:border-r-0 ${plan.id === 'plus' ? 'bg-blue-50/30' : ''}`}>
                      <Link
                        to={`/register?plan=${plan.id}&interval=${billingPeriod}`}
                        className={`
                          inline-flex items-center gap-2 text-sm font-bold hover:underline justify-center
                          ${plan.id === 'plus' ? 'text-[#0066CC]' : 'text-[#1D1D1F]'}
                        `}
                      >
                        Choose {plan.name} <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Mobile View - Cards with expanded details */}
          <div className="lg:hidden space-y-8">
            {plans.map((plan) => {
              const savings = getSavingsText(plan);
              return (
              <div 
                key={plan.id}
                className={`
                  rounded-3xl border p-6 relative overflow-hidden
                  ${plan.id === 'plus' ? 'border-[#0066CC] shadow-xl shadow-blue-900/5 ring-1 ring-[#0066CC]/20 bg-white' : 'border-gray-200 bg-white'}
                `}
              >
                {plan.badge && (
                  <div className="absolute top-0 right-0 bg-[#0066CC] text-white text-[10px] font-bold px-4 py-1.5 rounded-bl-xl uppercase tracking-wider">
                    {plan.badge}
                  </div>
                )}
                
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-[#1D1D1F] mb-2">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-4xl font-bold text-[#1D1D1F]">
                      ${billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual}
                    </span>
                    <span className="text-[#1D1D1F]/60">/mo</span>
                  </div>
                  {billingPeriod === 'annual' && savings && (
                    <p className="text-xs font-semibold text-green-600 bg-green-50 px-2.5 py-1 rounded-full inline-block mb-2">{savings}</p>
                  )}
                  <p className="text-[#1D1D1F]/60 text-sm">{plan.description}</p>
                </div>

                <Link
                  to={`/register?plan=${plan.id}&interval=${billingPeriod}`}
                  className={`
                    w-full py-3.5 rounded-full text-center font-semibold block mb-8 transition-all
                    ${plan.id === 'plus' 
                      ? 'bg-[#0066CC] text-white hover:bg-[#0052A3] shadow-lg shadow-blue-500/20' 
                      : 'bg-[#1D1D1F] text-white hover:bg-black'}
                  `}
                >
                  {plan.price.monthly === 0 ? 'Start Free' : 'Get Started'}
                </Link>

                <div className="space-y-6">
                  {features.map((category) => (
                    <div key={category.category}>
                      <h4 className="text-xs font-bold text-[#1D1D1F]/40 uppercase tracking-widest mb-3 border-b border-gray-100 pb-2">
                        {category.category}
                      </h4>
                      <div className="space-y-3">
                        {category.items.map((feature, i) => {
                          // Find index of current plan
                          const planIndex = plans.findIndex(p => p.id === plan.id);
                          const value = feature.values[planIndex];
                          
                          if (!value || value === '-') return null;

                          return (
                            <div key={i} className="flex justify-between items-center text-sm">
                              <span className="text-[#1D1D1F]/80">{feature.name}</span>
                              <span className="font-medium text-[#1D1D1F]">
                                {value === true ? <Check className="w-4 h-4 text-green-600" /> : value}
                              </span>
                </div>
              );
            })}
          </div>
                    </div>
                  ))}
                </div>
            </div>
            )})}
          </div>

          {/* FAQ Section */}
          <div className="mt-20 glass-panel p-8 md:p-12">
            <div className="mb-8">
              <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-[#1D1D1F]/60 mb-4">
                QUESTIONS — WE HAVE ANSWERS
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl">
              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  Which Galerly plan is right for me?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed mb-4">
                  It depends on your needs:
                </p>
                <ul className="text-sm text-[#1D1D1F]/70 space-y-2 list-disc pl-4">
                  <li><strong>Free:</strong> To test basic features risk-free.</li>
                  <li><strong>Starter:</strong> For new photographers with moderate needs.</li>
                  <li><strong>Plus:</strong> For growing businesses needing branding and video.</li>
                  <li><strong>Pro:</strong> For established studios with high volume and workflow needs.</li>
                  <li><strong>Ultimate:</strong> For agencies and large-scale operations requiring maximum power and support.</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  Do you offer a free trial?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed">
                  No need. The Free plan is free forever, no credit card required, allowing you to test all essential features and upgrade only when you're ready.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  What happens if I exceed my limits?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed mb-2">
                  It depends on your plan:
                </p>
                <ul className="text-sm text-[#1D1D1F]/70 space-y-2 list-disc pl-4">
                  <li><strong>Free & Starter:</strong> Limited by storage and active galleries. If reached, you'll need to upgrade to add more.</li>
                  <li><strong>Plus & above:</strong> Unlimited galleries and significantly more storage. Upgrade to higher tiers for massive storage needs or advanced features.</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  Can I cancel anytime?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed">
                  Yes, absolutely. You can cancel instantly at any time. Your access will remain active until the end of your current billing period.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  Do you offer discounts?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed">
                  Yes. By choosing annual billing, you save approximately 17% compared to the monthly price.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-3">
                  How can I contact you?
                </h3>
                <p className="text-sm text-[#1D1D1F]/70 leading-relaxed">
                  You can email us anytime at <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">support@galerly.com</a>. We'll get back to you quickly! 🙌
                </p>
              </div>
            </div>
          </div>

        </div>
      </main>
      
      <Footer />
    </div>
  );
}

