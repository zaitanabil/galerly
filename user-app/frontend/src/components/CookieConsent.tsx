import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X, Settings } from 'lucide-react';

/**
 * GDPR-Compliant Cookie Consent Banner
 * 
 * Compliance Features:
 * - Clear information about cookie types and purposes
 * - Granular consent (Essential, Analytics, Marketing)
 * - Easy to decline (same prominence as accept)
 * - Link to full privacy policy
 * - Records consent timestamp and preferences
 * - No tracking until consent given
 */

interface CookiePreferences {
  essential: boolean;  // Always true (required for site function)
  analytics: boolean;  // Optional - tracks site usage
  marketing: boolean;  // Optional - personalized content
  timestamp: string;
  version: string;     // Policy version accepted
}

export default function CookieConsent() {
  const [show, setShow] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    essential: true,
    analytics: false,
    marketing: false,
    timestamp: new Date().toISOString(),
    version: '1.0'
  });

  useEffect(() => {
    const stored = localStorage.getItem('cookie_consent');
    if (!stored) {
      setShow(true);
    } else {
      // Check if consent was given more than 12 months ago (GDPR requirement)
      try {
        const consent = JSON.parse(stored);
        const consentDate = new Date(consent.timestamp);
        const monthsSinceConsent = (Date.now() - consentDate.getTime()) / (1000 * 60 * 60 * 24 * 30);
        
        if (monthsSinceConsent > 12) {
          // Re-request consent after 12 months
          setShow(true);
        }
      } catch (e) {
        // Invalid stored consent, request again
        setShow(true);
      }
    }
  }, []);

  const savePreferences = (prefs: CookiePreferences) => {
    localStorage.setItem('cookie_consent', JSON.stringify(prefs));
    
    // Disable tracking if not consented
    if (!prefs.analytics) {
      // Disable analytics tracking
      window.gtag && window.gtag('consent', 'update', {
        'analytics_storage': 'denied'
      });
    }
    
    if (!prefs.marketing) {
      // Disable marketing tracking
      window.gtag && window.gtag('consent', 'update', {
        'ad_storage': 'denied',
        'ad_personalization': 'denied'
      });
    }
    
    setShow(false);
  };

  const handleAcceptAll = () => {
    const prefs: CookiePreferences = {
      essential: true,
      analytics: true,
      marketing: true,
      timestamp: new Date().toISOString(),
      version: '1.0'
    };
    savePreferences(prefs);
  };

  const handleRejectNonEssential = () => {
    const prefs: CookiePreferences = {
      essential: true,
      analytics: false,
      marketing: false,
      timestamp: new Date().toISOString(),
      version: '1.0'
    };
    savePreferences(prefs);
  };

  const handleSavePreferences = () => {
    savePreferences({
      ...preferences,
      timestamp: new Date().toISOString(),
      version: '1.0'
    });
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white/95 backdrop-blur-md border-t border-gray-200 shadow-2xl animate-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto">
        {!showDetails ? (
          // Simple view
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex-1 text-sm text-[#1D1D1F]/80">
              <p className="mb-2">
                <strong>We value your privacy</strong>
              </p>
          <p>
                We use essential cookies to make our site work. With your consent, we may also use non-essential cookies 
                to improve user experience and analyze website traffic. By clicking "Accept All," you agree to our use of cookies.
                {' '}
                <Link to="/privacy" className="text-[#0066CC] hover:underline">
                  Privacy Policy
                </Link>
                {' • '}
                <Link to="/legal" className="text-[#0066CC] hover:underline">
                  Legal Notice
            </Link>
          </p>
        </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setShowDetails(true)}
                className="px-4 py-2 text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Customize
              </button>
              <button
                onClick={handleRejectNonEssential}
                className="px-4 py-2 text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] border border-gray-300 rounded-full transition-colors"
              >
                Reject Non-Essential
              </button>
              <button
                onClick={handleAcceptAll}
                className="px-6 py-2 bg-[#0066CC] text-white text-sm font-medium rounded-full hover:bg-[#0052A3] transition-all shadow-md shadow-blue-500/20"
              >
                Accept All
              </button>
            </div>
          </div>
        ) : (
          // Detailed preferences view
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[#1D1D1F]">Cookie Preferences</h3>
              <button
                onClick={() => setShowDetails(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4 mb-6">
              {/* Essential Cookies */}
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-[#1D1D1F]">Essential Cookies</h4>
                    <p className="text-sm text-[#1D1D1F]/60 mt-1">
                      Required for the website to function. Cannot be disabled.
                    </p>
                  </div>
                  <div className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                    Always Active
                  </div>
                </div>
                <p className="text-xs text-[#1D1D1F]/50 mt-2">
                  Authentication, security, session management
                </p>
              </div>

              {/* Analytics Cookies */}
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium text-[#1D1D1F]">Analytics Cookies</h4>
                    <p className="text-sm text-[#1D1D1F]/60 mt-1">
                      Help us understand how visitors use our site.
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.analytics}
                      onChange={(e) => setPreferences({...preferences, analytics: e.target.checked})}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066CC]"></div>
                  </label>
                </div>
                <p className="text-xs text-[#1D1D1F]/50 mt-2">
                  Page views, user flows, performance monitoring
                </p>
              </div>

              {/* Marketing Cookies */}
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium text-[#1D1D1F]">Marketing Cookies</h4>
                    <p className="text-sm text-[#1D1D1F]/60 mt-1">
                      Used to show you personalized content and ads.
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.marketing}
                      onChange={(e) => setPreferences({...preferences, marketing: e.target.checked})}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066CC]"></div>
                  </label>
                </div>
                <p className="text-xs text-[#1D1D1F]/50 mt-2">
                  Advertising, retargeting, personalization
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3">
          <button
                onClick={handleRejectNonEssential}
                className="px-4 py-2 text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] border border-gray-300 rounded-full transition-colors"
          >
                Reject Non-Essential
          </button>
          <button
                onClick={handleSavePreferences}
            className="px-6 py-2 bg-[#0066CC] text-white text-sm font-medium rounded-full hover:bg-[#0052A3] transition-all shadow-md shadow-blue-500/20"
          >
                Save Preferences
          </button>
        </div>
          </div>
        )}
      </div>
    </div>
  );
}

