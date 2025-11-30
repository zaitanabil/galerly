// FOOTER - Fully Responsive Design for All Devices
// Enhanced design with better visual hierarchy and mobile-first approach

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import * as newsletterService from '../services/newsletterService';
import { Loader, Check, AlertCircle } from 'lucide-react';

export default function Footer() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleNewsletterSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const firstName = formData.get('firstName') as string;
    const email = formData.get('email') as string;
    
    if (!email) return;

    setLoading(true);
    setStatus('idle');
    setMessage('');

    try {
      const response = await newsletterService.subscribeToNewsletter(email, firstName);
      if (response.success) {
        setStatus('success');
        setMessage('Thanks for subscribing!');
        (e.target as HTMLFormElement).reset();
      } else {
        setStatus('error');
        setMessage(response.error || 'Subscription failed. Please try again.');
      }
    } catch (error) {
      console.error('Newsletter error:', error);
      setStatus('error');
      setMessage('An error occurred. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <footer className="relative py-16 sm:py-20 md:py-28 lg:py-40 bg-transparent text-[#1D1D1F] overflow-hidden">
      
      {/* Enhanced subtle accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] sm:w-[800px] lg:w-[1000px] h-[300px] sm:h-[400px] lg:h-[500px] bg-[#0066CC] opacity-[0.03] blur-[100px] sm:blur-[150px] lg:blur-[180px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] sm:w-[500px] lg:w-[600px] h-[300px] sm:h-[350px] lg:h-[400px] bg-[#0066CC] opacity-[0.02] blur-[100px] sm:blur-[120px] lg:blur-[150px] rounded-full pointer-events-none" />

      <div className="relative z-10 w-full max-w-[1600px] mx-auto px-4 sm:px-6 md:px-8 lg:px-16">
        
        {/* Newsletter Section - Responsive Grid */}
        <div className="mb-12 sm:mb-16 md:mb-20 lg:mb-28 pb-12 sm:pb-14 md:pb-16 lg:pb-20 border-b border-[#1D1D1F]/5">
          <div className="grid grid-cols-1 lg:grid-cols-[1.2fr,1fr] gap-8 sm:gap-10 md:gap-12 lg:gap-16 items-start lg:items-center">
            {/* Left: Text - Responsive Typography */}
            <div className="space-y-4 sm:space-y-5 md:space-y-6">
              <div>
                <h3 className="text-3xl sm:text-4xl md:text-5xl lg:text-5xl xl:text-6xl font-light text-[#1D1D1F] inline-block">
                  Stay
                </h3>
                <span className="text-3xl sm:text-4xl md:text-5xl lg:text-5xl xl:text-6xl font-light text-[#1D1D1F]/50 italic ml-2 sm:ml-3">
                  — Connected
                </span>
              </div>
              <p className="text-sm sm:text-base lg:text-lg text-[#1D1D1F]/60 leading-relaxed max-w-md">
                <span className="text-[#1D1D1F] font-medium">Join creators worldwide</span>
                <br />
                Get updates, stories, and early access to new features
              </p>
            </div>

            {/* Right: Newsletter Form - Responsive Layout */}
            <div className="w-full">
              <form 
                id="newsletter_form" 
                onSubmit={handleNewsletterSubmit}
                className="space-y-3"
              >
                <div>
                  <input 
                    type="text"
                    name="firstName"
                    placeholder="Your name"
                    required
                    disabled={loading || status === 'success'}
                    className="w-full px-4 sm:px-5 md:px-6 py-3 sm:py-3.5 md:py-4 text-sm sm:text-base rounded-full bg-[#1D1D1F]/5 backdrop-blur-sm border border-[#1D1D1F]/10 text-[#1D1D1F] placeholder:text-[#1D1D1F]/40 focus:outline-none focus:bg-[#1D1D1F]/10 focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all duration-200 disabled:opacity-50"
                  />
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <input 
                    type="email"
                    name="email"
                    placeholder="Your e-mail"
                    required
                    disabled={loading || status === 'success'}
                    className="flex-1 px-4 sm:px-5 md:px-6 py-3 sm:py-3.5 md:py-4 text-sm sm:text-base rounded-full bg-[#1D1D1F]/5 backdrop-blur-sm border border-[#1D1D1F]/10 text-[#1D1D1F] placeholder:text-[#1D1D1F]/40 focus:outline-none focus:bg-[#1D1D1F]/10 focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all duration-200 disabled:opacity-50"
                  />
                  <button 
                    type="submit"
                    disabled={loading || status === 'success'}
                    aria-label="Confirm"
                    className="w-full sm:w-auto px-6 sm:px-7 md:px-8 py-3 sm:py-3.5 md:py-4 text-sm sm:text-base rounded-full bg-[#0066CC] text-white font-medium hover:bg-[#0052A3] hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2 group whitespace-nowrap shadow-lg shadow-[#0066CC]/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <Loader className="w-4 h-4 animate-spin" />
                    ) : status === 'success' ? (
                      <>
                        <span>Joined</span>
                        <Check className="w-4 h-4" />
                      </>
                    ) : (
                      <>
                        <span>Confirm</span>
                        <svg 
                          width="17" 
                          height="14" 
                          viewBox="0 0 17 14" 
                          fill="none"
                          className="transition-transform duration-200 group-hover:translate-x-1 w-4 h-4 sm:w-[17px] sm:h-[14px]"
                        >
                          <path 
                            d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" 
                            stroke="currentColor" 
                            strokeLinecap="round"
                            strokeWidth="1.5"
                          />
                          <path 
                            d="M1 7L16 7" 
                            stroke="currentColor" 
                            strokeLinecap="round"
                            strokeWidth="1.5"
                          />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
                {message && (
                  <div className={`flex items-center gap-2 text-sm ${status === 'success' ? 'text-green-600' : 'text-red-500'} animate-in fade-in slide-in-from-top-1`}>
                    {status === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <p>{message}</p>
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>

        {/* Tagline and Links Section - Responsive Layout */}
        <div className="flex flex-col lg:flex-row gap-10 sm:gap-12 md:gap-14 lg:gap-12 mb-12 sm:mb-16 md:mb-20 lg:mb-28">
          
          {/* Tagline - Responsive Typography */}
          <div className="lg:w-[60%] flex items-start lg:items-center">
            <h2 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-light text-[#1D1D1F] tracking-tight leading-[1.1]">
              SHARE ART,
              <br />
              <span className="text-[#0066CC]">NOT FILES</span>
            </h2>
          </div>

          {/* Links - Responsive Grid */}
          <div className="lg:w-[40%] grid grid-cols-2 gap-8 sm:gap-10 md:gap-12 lg:gap-16">
            
            {/* Galerly Links */}
            <div>
              <h4 className="text-xs sm:text-sm font-semibold uppercase tracking-wider text-[#1D1D1F]/90 mb-4 sm:mb-5 md:mb-6 pb-2 border-b border-[#1D1D1F]/10">
                Galerly
              </h4>
              <ul className="space-y-2.5 sm:space-y-3 md:space-y-3.5">
                <li>
                  <Link to="/" className="text-[#1D1D1F]/50 hover:text-[#0066CC] hover:translate-x-0.5 transition-all duration-200 text-xs sm:text-sm inline-block">
                    Platform
                  </Link>
                </li>
                <li>
                  <Link to="/pricing" className="text-[#1D1D1F]/50 hover:text-[#0066CC] hover:translate-x-0.5 transition-all duration-200 text-xs sm:text-sm inline-block">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link to="/faq" className="text-[#1D1D1F]/50 hover:text-[#0066CC] hover:translate-x-0.5 transition-all duration-200 text-xs sm:text-sm inline-block">
                    FAQ
                  </Link>
                </li>
                <li>
                  <Link to="/contact" className="text-[#1D1D1F]/50 hover:text-[#0066CC] hover:translate-x-0.5 transition-all duration-200 text-xs sm:text-sm inline-block">
                    Support
                  </Link>
                </li>
              </ul>
            </div>

            {/* Social Links */}
            <div>
              <h4 className="text-xs sm:text-sm font-semibold uppercase tracking-wider text-[#1D1D1F]/90 mb-4 sm:mb-5 md:mb-6 pb-2 border-b border-[#1D1D1F]/10">
                Follow us
              </h4>
              <ul className="space-y-2.5 sm:space-y-3 md:space-y-3.5">
                <li>
                  <a 
                    href="https://www.instagram.com/withgalerly" 
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Instagram"
                    className="text-[#1D1D1F]/50 hover:text-[#0066CC] transition-all duration-200 text-xs sm:text-sm inline-flex items-center gap-1.5 sm:gap-2 group"
                  >
                    <span className="group-hover:translate-x-0.5 transition-transform duration-200">Instagram</span>
                    <svg 
                      width="12" 
                      height="12" 
                      viewBox="0 0 12 12" 
                      fill="none"
                      className="opacity-40 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-200 w-2.5 h-2.5 sm:w-3 sm:h-3"
                    >
                      <path 
                        d="M11.0435 9.88557L9.48515 9.89576V3.43836L1.12313 11.8004L0.00276604 10.68L8.36478 2.318L1.91758 2.32818V0.759669H11.0435V9.88557Z" 
                        fill="currentColor"
                      />
                    </svg>
                  </a>
                </li>
                <li>
                  <a 
                    href="https://www.tiktok.com/@withgalerly" 
                    target="_blank"
                    rel="noopener noreferrer"
                    title="TikTok"
                    className="text-[#1D1D1F]/50 hover:text-[#0066CC] transition-all duration-200 text-xs sm:text-sm inline-flex items-center gap-1.5 sm:gap-2 group"
                  >
                    <span className="group-hover:translate-x-0.5 transition-transform duration-200">TikTok</span>
                    <svg 
                      width="12" 
                      height="12" 
                      viewBox="0 0 12 12" 
                      fill="none"
                      className="opacity-40 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-200 w-2.5 h-2.5 sm:w-3 sm:h-3"
                    >
                      <path 
                        d="M11.0435 9.88557L9.48515 9.89576V3.43836L1.12313 11.8004L0.00276604 10.68L8.36478 2.318L1.91758 2.32818V0.759669H11.0435V9.88557Z" 
                        fill="currentColor"
                      />
                    </svg>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer Bottom - Responsive Layout */}
        <div className="pt-6 sm:pt-8 md:pt-10 border-t border-[#1D1D1F]/5">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 sm:gap-5 md:gap-6 text-xs sm:text-sm">
            <div className="flex items-center gap-4 sm:gap-6 md:gap-8 flex-wrap justify-center sm:justify-start">
              <Link to="/legal" className="text-[#1D1D1F]/40 hover:text-[#0066CC] transition-colors duration-200">
                Legal notice
              </Link>
              <Link to="/privacy" className="text-[#1D1D1F]/40 hover:text-[#0066CC] transition-colors duration-200">
                Privacy policy
              </Link>
            </div>
            <div className="text-[#1D1D1F]/30 font-light tracking-wide">
              2025 © Galerly
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
