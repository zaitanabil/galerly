// Plan Comparison Modal Component
import { X, Check, Zap, Crown, Rocket } from 'lucide-react';
import { useState } from 'react';

interface PlanComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan?: string;
  onSelectPlan?: (planId: string, interval: 'monthly' | 'annual') => void;
}

export default function PlanComparisonModal({ isOpen, onClose, currentPlan = 'free', onSelectPlan }: PlanComparisonModalProps) {
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'annual'>('monthly');

  if (!isOpen) return null;

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      icon: Zap,
      price: { monthly: 10, annual: 8 },
      color: 'gray',
      description: 'For new pros',
      features: [
        '25 GB Smart Storage',
        'Unlimited Galleries',
        '30 Min Video (HD)',
        'Remove Galerly Branding',
        'Client Favorites & Proofing',
        'Basic Analytics'
      ]
    },
    {
      id: 'plus',
      name: 'Plus',
      icon: Check,
      price: { monthly: 24, annual: 20 },
      color: 'blue',
      description: 'For growing businesses',
      features: [
        'Everything in Starter',
        '100 GB Smart Storage',
        '2 Hours Video (4K)',
        'Custom Branding',
        'Client Management',
        'Advanced Analytics',
        'Email Automation'
      ],
      popular: true
    },
    {
      id: 'pro',
      name: 'Pro',
      icon: Crown,
      price: { monthly: 49, annual: 41 },
      color: 'purple',
      description: 'For professionals',
      features: [
        'Everything in Plus',
        '500 GB Smart Storage',
        '10 Hours Video (4K)',
        'RAW File Storage (10 GB)',
        'Client Invoicing',
        'Digital Contracts',
        'Lead Scoring & CRM',
        'Photo Sales & Packages',
        'Payment Reminders'
      ]
    },
    {
      id: 'ultimate',
      name: 'Ultimate',
      icon: Rocket,
      price: { monthly: 99, annual: 83 },
      color: 'gradient',
      description: 'For studios',
      features: [
        'Everything in Pro',
        '2 TB Smart Storage',
        'Unlimited Video (4K)',
        'RAW File Storage (100 GB)',
        'Priority Support',
        'Scheduler & Booking',
        'Custom Domain',
        'White Label',
        'Onboarding Automation',
        'Multi-user Access'
      ]
    }
  ];

  const getColorClasses = (color: string, isSelected: boolean) => {
    if (isSelected) {
      return {
        border: 'border-2 border-[#0066CC]',
        button: 'bg-[#0066CC] text-white hover:bg-[#0052A3]',
        badge: 'bg-[#0066CC] text-white'
      };
    }
    
    switch (color) {
      case 'blue':
        return {
          border: 'border border-blue-200',
          button: 'bg-[#0066CC] text-white hover:bg-[#0052A3]',
          badge: 'bg-blue-100 text-blue-700'
        };
      case 'purple':
        return {
          border: 'border border-purple-200',
          button: 'bg-purple-600 text-white hover:bg-purple-700',
          badge: 'bg-purple-100 text-purple-700'
        };
      case 'gradient':
        return {
          border: 'border border-purple-300',
          button: 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700',
          badge: 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700'
        };
      default:
        return {
          border: 'border border-gray-200',
          button: 'bg-[#1D1D1F] text-white hover:bg-black',
          badge: 'bg-gray-100 text-gray-700'
        };
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-6xl w-full my-8">
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-medium text-[#1D1D1F]">Choose Your Plan</h2>
            <p className="text-sm text-[#1D1D1F]/60 mt-1">Select the plan that fits your needs</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Billing Toggle */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-center gap-4">
            <span className={`text-sm font-medium ${billingInterval === 'monthly' ? 'text-[#1D1D1F]' : 'text-[#1D1D1F]/40'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingInterval(billingInterval === 'monthly' ? 'annual' : 'monthly')}
              className="relative w-14 h-7 bg-[#0066CC] rounded-full transition-colors"
            >
              <span
                className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                  billingInterval === 'annual' ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm font-medium ${billingInterval === 'annual' ? 'text-[#1D1D1F]' : 'text-[#1D1D1F]/40'}`}>
              Annual
            </span>
            {billingInterval === 'annual' && (
              <span className="ml-2 px-3 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-full">
                Save up to 17%
              </span>
            )}
          </div>
        </div>

        {/* Plans Grid */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {plans.map((plan) => {
              const isCurrentPlan = plan.id === currentPlan;
              const colors = getColorClasses(plan.color, isCurrentPlan);
              const Icon = plan.icon;
              const price = billingInterval === 'monthly' ? plan.price.monthly : plan.price.annual;

              return (
                <div
                  key={plan.id}
                  className={`relative p-6 rounded-2xl ${colors.border} ${plan.popular ? 'ring-2 ring-blue-200' : ''}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-4 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
                        Most Popular
                      </span>
                    </div>
                  )}

                  {isCurrentPlan && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-4 py-1 bg-[#0066CC] text-white text-xs font-medium rounded-full">
                        Current Plan
                      </span>
                    </div>
                  )}

                  {/* Plan Header */}
                  <div className="mb-6">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${colors.badge}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-medium text-[#1D1D1F] mb-1">{plan.name}</h3>
                    <p className="text-sm text-[#1D1D1F]/60 mb-4">{plan.description}</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-[#1D1D1F]">${price}</span>
                      <span className="text-sm text-[#1D1D1F]/60">/mo</span>
                    </div>
                    {billingInterval === 'annual' && (
                      <p className="text-xs text-[#1D1D1F]/40 mt-1">
                        ${price * 12}/year
                      </p>
                    )}
                  </div>

                  {/* Features */}
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-[#1D1D1F]/70">
                        <Check className="w-4 h-4 text-[#0066CC] flex-shrink-0 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA Button */}
                  <button
                    onClick={() => {
                      if (onSelectPlan) {
                        onSelectPlan(plan.id, billingInterval);
                      }
                    }}
                    disabled={isCurrentPlan}
                    className={`w-full py-3 rounded-xl font-medium transition-all ${colors.button} disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {isCurrentPlan ? 'Current Plan' : 'Select Plan'}
                  </button>
                </div>
              );
            })}
          </div>

          {/* Footer Note */}
          <div className="mt-6 text-center text-sm text-[#1D1D1F]/60">
            <p>All plans include 14-day free trial. No credit card required.</p>
            <p className="mt-1">Cancel anytime. Pro-rated refunds available.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
