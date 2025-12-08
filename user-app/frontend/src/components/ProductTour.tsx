// Product Tour / Tooltips System for new features
import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronRight, ChevronLeft } from 'lucide-react';

interface TourStep {
  id: string;
  target: string; // CSS selector
  title: string;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ProductTourProps {
  tourId: string;
  steps: TourStep[];
  onComplete?: () => void;
  onSkip?: () => void;
}

export function ProductTour({ tourId, steps, onComplete, onSkip }: ProductTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check if user has completed this tour
    const completed = localStorage.getItem(`tour_completed_${tourId}`);
    if (!completed) {
      setIsActive(true);
    }
  }, [tourId]);

  useEffect(() => {
    if (!isActive) return;

    const step = steps[currentStep];
    if (!step) return;

    // Find target element
    const target = document.querySelector(step.target);
    if (!target) {
      console.warn(`Tour target not found: ${step.target}`);
      return;
    }

    // Calculate position
    const targetRect = target.getBoundingClientRect();
    const tooltipRect = tooltipRef.current?.getBoundingClientRect();

    let top = 0;
    let left = 0;

    const pos = step.position || 'bottom';
    
    if (pos === 'bottom') {
      top = targetRect.bottom + window.scrollY + 10;
      left = targetRect.left + window.scrollX + targetRect.width / 2;
      if (tooltipRect) left -= tooltipRect.width / 2;
    } else if (pos === 'top') {
      top = targetRect.top + window.scrollY - (tooltipRect?.height || 0) - 10;
      left = targetRect.left + window.scrollX + targetRect.width / 2;
      if (tooltipRect) left -= tooltipRect.width / 2;
    } else if (pos === 'right') {
      top = targetRect.top + window.scrollY + targetRect.height / 2;
      if (tooltipRect) top -= tooltipRect.height / 2;
      left = targetRect.right + window.scrollX + 10;
    } else if (pos === 'left') {
      top = targetRect.top + window.scrollY + targetRect.height / 2;
      if (tooltipRect) top -= tooltipRect.height / 2;
      left = targetRect.left + window.scrollX - (tooltipRect?.width || 0) - 10;
    }

    setPosition({ top, left });

    // Highlight target element
    target.classList.add('tour-highlight');
    return () => target.classList.remove('tour-highlight');
  }, [currentStep, isActive, steps]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem(`tour_completed_${tourId}`, 'true');
    setIsActive(false);
    if (onComplete) onComplete();
  };

  const handleSkip = () => {
    localStorage.setItem(`tour_completed_${tourId}`, 'true');
    setIsActive(false);
    if (onSkip) onSkip();
  };

  if (!isActive || !steps[currentStep]) return null;

  const step = steps[currentStep];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={handleSkip} />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-5 max-w-sm animate-fade-in"
        style={{ top: position.top, left: position.left }}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="font-medium text-[#1D1D1F] dark:text-white mb-1">
              {step.title}
            </h3>
            <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
              {step.content}
            </p>
          </div>
          <button
            onClick={handleSkip}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Button (if provided) */}
        {step.action && (
          <button
            onClick={step.action.onClick}
            className="w-full mb-3 py-2 px-4 bg-blue-50 dark:bg-blue-900/20 text-[#0066CC] rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors text-sm font-medium"
          >
            {step.action.label}
          </button>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-1">
            {steps.map((_, idx) => (
              <div
                key={idx}
                className={`h-1.5 rounded-full transition-all ${
                  idx === currentStep
                    ? 'w-6 bg-[#0066CC]'
                    : 'w-1.5 bg-gray-200 dark:bg-gray-700'
                }`}
              />
            ))}
          </div>
          
          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={handlePrevious}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={handleNext}
              className="px-4 py-2 bg-[#0066CC] text-white rounded-lg hover:bg-[#0052A3] transition-colors text-sm font-medium flex items-center gap-1"
            >
              {currentStep === steps.length - 1 ? 'Done' : 'Next'}
              {currentStep < steps.length - 1 && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Styles for highlighting */}
      <style>{`
        .tour-highlight {
          position: relative;
          z-index: 45 !important;
          box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.3) !important;
          border-radius: 8px;
        }
        
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </>
  );
}

// Feature tooltip component for inline hints
export function FeatureTooltip({ 
  children, 
  content, 
  show = true 
}: { 
  children: React.ReactNode; 
  content: string; 
  show?: boolean;
}) {
  const [isVisible, setIsVisible] = useState(show);

  if (!isVisible) return <>{children}</>;

  return (
    <div className="relative inline-block">
      {children}
      <div className="absolute -top-2 -right-2 z-10">
        <div className="relative">
          <div className="w-6 h-6 bg-[#0066CC] rounded-full flex items-center justify-center text-white text-xs font-bold animate-pulse">
            !
          </div>
          <div className="absolute top-8 right-0 bg-[#0066CC] text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
            {content}
            <button
              onClick={() => setIsVisible(false)}
              className="ml-2 hover:underline"
            >
              Got it
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Welcome tour for new users
export const welcomeTour: TourStep[] = [
  {
    id: 'dashboard',
    target: '[data-tour="dashboard"]',
    title: 'Welcome to Galerly!',
    content: 'Your dashboard shows all your key metrics and recent activity.',
    position: 'bottom'
  },
  {
    id: 'new-gallery',
    target: '[data-tour="new-gallery"]',
    title: 'Create Galleries',
    content: 'Click here to upload and share photos with your clients.',
    position: 'bottom',
    action: {
      label: 'Create Your First Gallery',
      onClick: () => window.location.href = '/new-gallery'
    }
  },
  {
    id: 'crm',
    target: '[data-tour="crm"]',
    title: 'Manage Clients',
    content: 'Track leads, follow up with clients, and manage your pipeline.',
    position: 'right'
  },
  {
    id: 'settings',
    target: '[data-tour="settings"]',
    title: 'Customize Settings',
    content: 'Configure your profile, branding, and preferences.',
    position: 'left'
  }
];
