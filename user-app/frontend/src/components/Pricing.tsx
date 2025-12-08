import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import { Check, ArrowRight } from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Pricing() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('annual');

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: { monthly: 0, annual: 0 },
      period: 'forever',
      description: 'For hobbyists',
      features: [
        '2 GB Smart Storage',
        '3 Active Galleries',
        'Basic Portfolio',
        'Community Support',
        'Galerly Branding'
      ],
      highlight: false,
      cta: 'Start Free'
    },
    {
      id: 'starter',
      name: 'Starter',
      price: { monthly: 10, annual: 8 },
      period: '/mo',
      description: 'For new pros',
      features: [
        '25 GB Smart Storage',
        'Unlimited Galleries',
        '30 Min Video (HD)',
        'Remove Galerly Branding',
        'Client Favorites & Proofing',
        'Basic Analytics'
      ],
      highlight: false,
      cta: 'Get Started'
    },
    {
      id: 'plus',
      name: 'Plus',
      price: { monthly: 24, annual: 19 },
      badge: 'BEST VALUE',
      period: '/mo',
      description: 'Most popular',
      features: [
        '100 GB Smart Storage',
        'Unlimited Galleries',
        '1 Hour Video (HD)',
        'Custom Domain',
        'Automated Watermarking',
        'Client Favorites & Proofing',
        'Advanced Analytics'
      ],
      highlight: true,
      cta: 'Get Plus'
    },
    {
      id: 'pro',
      name: 'Pro',
      price: { monthly: 49, annual: 39 },
      period: '/mo',
      description: 'For studios',
      features: [
        '500 GB Smart Storage',
        '4 Hours Video (4K)',
        'RAW Photo Support',
        'Client Invoicing',
        'Email Automation & Templates',
        'SEO Optimization Tools',
        'Pro Analytics'
      ],
      highlight: false,
      cta: 'Go Pro'
    },
    {
      id: 'ultimate',
      name: 'Ultimate',
      price: { monthly: 99, annual: 79 },
      period: '/mo',
      description: 'Max power',
      features: [
        '2 TB Smart Storage',
        '10 Hours Video (4K)',
        'RAW Vault Archival (Glacier)',
        'Scheduler',
        'eSignatures',
        'All Pro Features'
      ],
      highlight: false,
      cta: 'Go Ultimate'
    }
  ];

  useEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    const mm = gsap.matchMedia();

    const ctx = gsap.context(() => {
      
      mm.add("(min-width: 1024px)", () => {
        // Desktop: Staggered batch animation
        const planCards = gsap.utils.toArray('[data-plan]');
        
        // Set initial state
        gsap.set(planCards, { opacity: 0, y: 50 });
        
        // Create scroll trigger for each card with stagger
        planCards.forEach((card, index) => {
          gsap.to(card as Element, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power3.out",
            delay: index * 0.15,
            scrollTrigger: {
              trigger: card as Element,
              start: "top 85%",
              once: true,
              toggleActions: "play none none none"
            }
          });
        });
      });

      mm.add("(max-width: 1023px)", () => {
        // Mobile/Tablet: Reveal each card individually
        const planCards = gsap.utils.toArray('[data-plan]') as Element[];
        
        planCards.forEach((card) => {
          gsap.set(card, { opacity: 0, y: 50 });
          
          gsap.to(card, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
              trigger: card,
              start: "top 90%",
              end: "top 60%",
              scrub: 1
            }
          });
        });
      });

    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const getSavingsText = (plan: typeof plans[0]) => {
    if (plan.price.monthly === 0) return null;
    const annualTotal = plan.price.annual * 12;
    const monthlyTotal = plan.price.monthly * 12;
    const savings = monthlyTotal - annualTotal;
    return savings > 0 ? `Save $${savings}/year` : null;
  };

  return (
    <section 
      id="pricing" 
      ref={sectionRef} 
      className="min-h-screen bg-transparent relative overflow-visible py-24 lg:py-32"
    >
      <div className="w-full max-w-7xl mx-auto px-6">
        
        {/* Header */}
        <div className="text-center mb-12 lg:mb-20">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-[#0066CC]/10 text-[#0066CC] mb-8">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              Plans & Pricing
            </span>
          </div>
          
          <h2 className="text-4xl md:text-6xl lg:text-8xl font-light text-[#1D1D1F] mb-6 leading-tight">
            Simple. Transparent.
            <br />
            <span className="text-[#0066CC]">No hidden fees.</span>
          </h2>
          
          <p className="text-lg md:text-xl lg:text-2xl text-[#1D1D1F]/60 max-w-3xl mx-auto leading-relaxed mb-8">
            Start for free. Upgrade when you're ready to scale.
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

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 items-start relative z-10 max-w-6xl mx-auto">
          {plans.map((plan, i) => {
            const displayPrice = billingPeriod === 'monthly' ? plan.price.monthly : plan.price.annual;
            const savingsText = billingPeriod === 'annual' ? getSavingsText(plan) : null;

            return (
              <div 
                key={i}
                data-plan
                className={`
                  relative flex flex-col rounded-3xl lg:rounded-[40px] transition-all duration-500 group
                  ${plan.highlight 
                    ? 'bg-white/90 backdrop-blur-xl shadow-2xl shadow-[#0066CC]/10 border-2 border-[#0066CC]/30 lg:scale-105 md:col-span-2 lg:col-span-1 md:row-start-1 lg:row-auto' 
                    : 'bg-white/60 backdrop-blur-lg border border-[#1D1D1F]/10 hover:bg-white/80 hover:shadow-xl'
                  }
                `}
              >
                {/* Badge */}
                {plan.badge && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-[#0066CC] text-white px-6 py-2 rounded-full text-xs font-semibold uppercase tracking-wider shadow-lg whitespace-nowrap">
                    {plan.badge}
                  </div>
                )}

                <div className="p-6 md:p-8 lg:p-10 flex flex-col flex-grow">
                  {/* Header */}
                  <div className="mb-8">
                    <h3 className="text-2xl md:text-3xl font-medium text-[#1D1D1F] mb-3">
                      {plan.name}
                    </h3>
                    <p className="text-[#1D1D1F]/60 text-sm md:text-base leading-relaxed">
                      {plan.description}
                    </p>
                  </div>

                  {/* Price */}
                  <div className="mb-8">
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className="text-5xl md:text-6xl lg:text-7xl font-light text-[#1D1D1F] tracking-tight">
                        {displayPrice === 0 ? 'Free' : `$${displayPrice}`}
                      </span>
                      {displayPrice !== 0 && (
                        <span className="text-lg md:text-xl text-[#1D1D1F]/40">
                          {plan.period}
                        </span>
                      )}
                    </div>
                    {savingsText && (
                      <p className="text-sm text-green-600 font-medium">
                        {savingsText}
                      </p>
                    )}
                    {billingPeriod === 'annual' && displayPrice !== 0 && (
                      <p className="text-xs text-[#1D1D1F]/40 mt-1">
                        Billed ${displayPrice * 12} annually
                      </p>
                    )}
                  </div>

                  {/* Features */}
                  <div className="flex-grow mb-8">
                    <ul className="space-y-3 md:space-y-4">
                      {plan.features.map((feature, idx) => (
                        <li 
                          key={idx} 
                          className="flex items-start gap-3 text-[#1D1D1F]/80 group-hover:text-[#1D1D1F] transition-colors"
                        >
                          <div className={`
                            mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center
                            ${plan.highlight 
                              ? 'bg-[#0066CC]/10' 
                              : 'bg-[#1D1D1F]/5'
                            }
                          `}>
                            <Check className={`
                              w-3 h-3
                              ${plan.highlight ? 'text-[#0066CC]' : 'text-[#1D1D1F]/40'}
                            `} strokeWidth={3} />
                          </div>
                          <span className="text-sm md:text-base font-light leading-relaxed">
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* CTA Button */}
                  <Link
                    to={`/register?plan=${plan.id}`}
                    className={`
                      w-full py-4 md:py-5 rounded-full text-base md:text-lg font-medium 
                      transition-all duration-300 flex items-center justify-center gap-2
                      ${plan.highlight
                        ? 'bg-[#0066CC] text-white hover:bg-[#0052a3] shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-100'
                        : 'bg-[#1D1D1F] text-white hover:bg-[#000000] hover:shadow-lg hover:scale-[1.02] active:scale-100'
                      }
                    `}
                  >
                    <span>{plan.cta}</span>
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>

        {/* Trust Section */}
        <div className="mt-16 lg:mt-24 text-center relative z-10">
          <div className="inline-block glass-panel px-8 py-6 md:px-12 md:py-8">
            <p className="text-[#1D1D1F]/40 text-xs md:text-sm uppercase tracking-widest font-medium mb-2">
              Trusted by 5,000+ Photographers
            </p>
            <p className="text-[#1D1D1F]/60 text-sm">
              All plans include 14-day money-back guarantee
            </p>
          </div>
        </div>

      </div>
    </section>
  );
}
