import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function CookieConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const consented = localStorage.getItem('cookie_consent');
    if (!consented) {
      setShow(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie_consent', 'true');
    setShow(false);
  };

  const handleDecline = () => {
    // We still store consent as declined to stop showing the banner
    // Real implementation would disable tracking scripts here
    localStorage.setItem('cookie_consent', 'declined');
    setShow(false);
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white/90 backdrop-blur-md border-t border-gray-200 shadow-lg animate-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-sm text-[#1D1D1F]/80 text-center sm:text-left">
          <p>
            We use cookies to enhance your experience, analyze site traffic, and serve personalized content. 
            By continuing to use our site, you agree to our use of cookies. 
            <Link to="/privacy" className="text-[#0066CC] hover:underline ml-1">
              Learn more
            </Link>
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleDecline}
            className="px-4 py-2 text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
          >
            Decline
          </button>
          <button
            onClick={handleAccept}
            className="px-6 py-2 bg-[#0066CC] text-white text-sm font-medium rounded-full hover:bg-[#0052A3] transition-all shadow-md shadow-blue-500/20"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}

