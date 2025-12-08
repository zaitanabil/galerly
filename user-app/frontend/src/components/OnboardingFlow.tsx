// Onboarding Flow - First-time user setup wizard
import { useState } from 'react';
import { Check, ArrowRight, Camera, Globe, Palette, Upload, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface OnboardingFlowProps {
  onComplete: () => void;
}

export default function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    businessName: '',
    photography_type: '',
    city: '',
    country: '',
    website: '',
    instagram: '',
    bio: '',
    logo: null as File | null
  });

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to Galerly',
      description: 'Let\'s set up your photography business in minutes'
    },
    {
      id: 'business',
      title: 'Business Information',
      description: 'Tell us about your photography business'
    },
    {
      id: 'portfolio',
      title: 'Portfolio Setup',
      description: 'Configure your public portfolio'
    },
    {
      id: 'branding',
      title: 'Branding',
      description: 'Upload your logo and set your brand colors'
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      description: 'Ready to upload your first gallery'
    }
  ];

  const handleNext = async () => {
    if (currentStep === steps.length - 2) {
      // Save all data before final step
      try {
        await api.put('/profile', {
          business_name: formData.businessName,
          photography_type: formData.photography_type,
          city: formData.city,
          country: formData.country,
          website: formData.website,
          instagram: formData.instagram,
          bio: formData.bio
        });
        
        // Mark onboarding as complete
        await api.put('/profile', { onboarding_completed: true });
        
        setCurrentStep(currentStep + 1);
      } catch (error) {
        toast.error('Failed to save profile');
      }
    } else if (currentStep === steps.length - 1) {
      // Complete onboarding
      onComplete();
      navigate('/dashboard');
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleSkip = () => {
    if (currentStep === steps.length - 1) {
      onComplete();
      navigate('/dashboard');
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Welcome
        return (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gradient-to-br from-[#0066CC] to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-serif font-medium text-[#1D1D1F] mb-4">
              Welcome to Galerly
            </h2>
            <p className="text-lg text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
              Let's get your photography business set up in just a few steps. This will only take a couple of minutes.
            </p>
            <div className="grid grid-cols-2 gap-4 max-w-md mx-auto text-left">
              <div className="p-4 bg-blue-50 rounded-xl">
                <Camera className="w-6 h-6 text-[#0066CC] mb-2" />
                <h3 className="font-medium text-[#1D1D1F] mb-1">Upload Photos</h3>
                <p className="text-sm text-[#1D1D1F]/60">Share galleries with clients</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-xl">
                <Globe className="w-6 h-6 text-purple-600 mb-2" />
                <h3 className="font-medium text-[#1D1D1F] mb-1">Public Portfolio</h3>
                <p className="text-sm text-[#1D1D1F]/60">Showcase your work</p>
              </div>
            </div>
          </div>
        );

      case 1: // Business Info
        return (
          <div className="py-8">
            <div className="max-w-md mx-auto space-y-6">
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Business Name *
                </label>
                <input
                  type="text"
                  value={formData.businessName}
                  onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                  placeholder="John Doe Photography"
                  className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Photography Type *
                </label>
                <select
                  value={formData.photography_type}
                  onChange={(e) => setFormData({ ...formData, photography_type: e.target.value })}
                  className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                >
                  <option value="">Select type</option>
                  <option value="wedding">Wedding</option>
                  <option value="portrait">Portrait</option>
                  <option value="event">Event</option>
                  <option value="commercial">Commercial</option>
                  <option value="product">Product</option>
                  <option value="real-estate">Real Estate</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="New York"
                    className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Country
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    placeholder="USA"
                    className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 2: // Portfolio
        return (
          <div className="py-8">
            <div className="max-w-md mx-auto space-y-6">
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Website URL
                </label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  placeholder="https://yourwebsite.com"
                  className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Instagram Handle
                </label>
                <div className="flex items-center">
                  <span className="px-4 py-3 bg-gray-50 border border-r-0 border-gray-200 rounded-l-xl text-[#1D1D1F]/60">
                    @
                  </span>
                  <input
                    type="text"
                    value={formData.instagram}
                    onChange={(e) => setFormData({ ...formData, instagram: e.target.value })}
                    placeholder="yourhandle"
                    className="flex-1 px-4 py-3 bg-white/50 border border-gray-200 rounded-r-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Bio
                </label>
                <textarea
                  value={formData.bio}
                  onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  placeholder="Tell potential clients about yourself..."
                  rows={4}
                  className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 resize-none"
                />
              </div>
            </div>
          </div>
        );

      case 3: // Branding
        return (
          <div className="py-8">
            <div className="max-w-md mx-auto space-y-6">
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Upload Logo (Optional)
                </label>
                <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-[#0066CC] transition-colors">
                  <Upload className="w-8 h-8 text-[#1D1D1F]/40 mx-auto mb-3" />
                  <p className="text-sm text-[#1D1D1F]/60 mb-2">
                    Drag and drop or click to upload
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setFormData({ ...formData, logo: e.target.files?.[0] || null })}
                    className="hidden"
                    id="logo-upload"
                  />
                  <label
                    htmlFor="logo-upload"
                    className="inline-block px-4 py-2 bg-[#0066CC] text-white text-sm rounded-lg cursor-pointer hover:bg-[#0052A3] transition-colors"
                  >
                    Choose File
                  </label>
                  {formData.logo && (
                    <p className="text-sm text-green-600 mt-2">
                      {formData.logo.name}
                    </p>
                  )}
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-xl">
                <Palette className="w-5 h-5 text-[#0066CC] mb-2" />
                <p className="text-sm text-[#1D1D1F]/70">
                  You can customize colors and branding later in Settings → Branding
                </p>
              </div>
            </div>
          </div>
        );

      case 4: // Complete
        return (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-3xl font-serif font-medium text-[#1D1D1F] mb-4">
              You're All Set!
            </h2>
            <p className="text-lg text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
              Your account is ready. Start uploading your first gallery or explore your dashboard.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => navigate('/new-gallery')}
                className="px-6 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all"
              >
                Upload First Gallery
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-50 transition-all"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return formData.businessName && formData.photography_type;
      default:
        return true;
    }
  };

  return (
    <div className="fixed inset-0 bg-[#F5F5F7] z-50 overflow-y-auto">
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </div>
            <div className="text-sm text-[#1D1D1F]/60">
              Step {currentStep + 1} of {steps.length}
            </div>
          </div>
        </header>

        {/* Progress Bar */}
        <div className="bg-white border-b border-gray-100">
          <div className="max-w-5xl mx-auto px-6 py-4">
            <div className="flex items-center gap-2">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`flex-1 h-2 rounded-full transition-all ${
                    index <= currentStep ? 'bg-[#0066CC]' : 'bg-gray-200'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <main className="flex-1 flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-3xl">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-medium text-[#1D1D1F] mb-2">
                {steps[currentStep].title}
              </h1>
              <p className="text-[#1D1D1F]/60">
                {steps[currentStep].description}
              </p>
            </div>

            <div className="glass-panel p-8 mb-6">
              {renderStepContent()}
            </div>

            {/* Navigation */}
            {currentStep < steps.length - 1 && (
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleSkip}
                  className="px-6 py-3 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
                >
                  Skip
                </button>
                <button
                  onClick={handleNext}
                  disabled={!isStepValid()}
                  className="px-8 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {currentStep === 0 ? 'Get Started' : 'Continue'}
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
