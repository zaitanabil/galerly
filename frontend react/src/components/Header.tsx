// HEADER - Fully Responsive Navigation for All Devices
// Modern glass header with mobile menu, accessibility, and adaptive layouts

import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const isHomePage = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  const navItems = [
    { label: 'Features', href: '#features', isAnchor: true },
    { label: 'How It Works', href: '#how-it-works', isAnchor: true },
    { label: 'Pricing', href: '/pricing', isAnchor: false },
    { label: 'Photographers', href: '/photographers', isAnchor: false },
  ];

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault();
      setMobileMenuOpen(false);
      
      if (isHomePage) {
        const target = document.querySelector(href);
        if (target) {
          setTimeout(() => {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 300);
        }
      } else {
        window.location.href = `/${href}`;
      }
    } else {
      setMobileMenuOpen(false);
    }
  };

  return (
    <>
      {/* Header with Integrated Menu */}
      <header
        className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 ${
          scrolled ? 'py-3 bg-white/80 backdrop-blur-md shadow-sm border-b border-white/20' : 'py-5 bg-transparent'
        }`}
      >
        <div className="w-full max-w-[1600px] mx-auto px-6">
          <nav className="relative flex items-center justify-between">
              
            {/* Logo */}
            <Link
              to="/"
              className="text-2xl font-serif font-medium tracking-tight text-[#1D1D1F] hover:text-[#0066CC] transition-colors relative z-50"
              aria-label="Galerly Home"
            >
              Galerly
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-8">
              {navItems.map((item) => (
                item.isAnchor && isHomePage ? (
                  <a
                    key={item.label}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className="text-sm font-medium text-[#1D1D1F]/70 hover:text-[#0066CC] transition-colors"
                  >
                    {item.label}
                  </a>
                ) : (
                  <Link
                    key={item.label}
                    to={item.isAnchor ? `/${item.href}` : item.href}
                    className="text-sm font-medium text-[#1D1D1F]/70 hover:text-[#0066CC] transition-colors"
                  >
                    {item.label}
                  </Link>
                )
              ))}
            </div>

            {/* Desktop CTA Buttons */}
            <div className="hidden lg:flex items-center gap-4">
              <Link
                to="/login"
                className="text-sm font-medium text-[#1D1D1F]/70 hover:text-[#0066CC] transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-5 py-2.5 bg-[#0066CC] text-white rounded-full text-sm font-medium hover:bg-[#0052A3] transition-all hover:scale-105 shadow-lg shadow-blue-500/20"
              >
                Start Free
              </Link>
            </div>

            {/* Mobile & Tablet Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden relative z-50 w-10 h-10 flex items-center justify-center text-[#1D1D1F]"
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              <div className="w-6 h-5 flex flex-col justify-between">
                <span
                  className={`w-full h-0.5 bg-current rounded-full transition-all duration-300 origin-left ${
                    mobileMenuOpen ? 'rotate-45 translate-x-px' : ''
                  }`}
                />
                <span
                  className={`w-full h-0.5 bg-current rounded-full transition-all duration-300 ${
                    mobileMenuOpen ? 'opacity-0 scale-x-0' : 'opacity-100 scale-x-100'
                  }`}
                />
                <span
                  className={`w-full h-0.5 bg-current rounded-full transition-all duration-300 origin-left ${
                    mobileMenuOpen ? '-rotate-45 translate-x-px' : ''
                  }`}
                />
              </div>
            </button>
          </nav>
        </div>
      </header>

      {/* Mobile & Tablet Menu Overlay */}
      <div
        className={`fixed inset-0 z-[90] lg:hidden transition-all duration-500 ${
          mobileMenuOpen ? 'opacity-100 visible' : 'opacity-0 invisible delay-200'
        }`}
      >
        {/* Backdrop with Blur */}
        <div 
          className="absolute inset-0 bg-white/95 backdrop-blur-xl transition-opacity duration-500"
          onClick={() => setMobileMenuOpen(false)}
        />

        {/* Menu Content */}
        <div className="absolute inset-0 flex flex-col justify-center px-6 pt-20 pb-10">
          <nav className="flex flex-col items-center space-y-8">
            {navItems.map((item, index) => (
              item.isAnchor && isHomePage ? (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={(e) => handleNavClick(e, item.href)}
                  className={`text-3xl font-normal text-[#1D1D1F] hover:text-[#0066CC] transition-all duration-500 transform ${
                     mobileMenuOpen 
                       ? 'opacity-100 translate-y-0' 
                       : 'opacity-0 translate-y-8'
                  }`}
                  style={{ transitionDelay: `${100 + index * 50}ms` }}
                >
                  {item.label}
                </a>
              ) : (
                <Link
                  key={item.label}
                  to={item.isAnchor ? `/${item.href}` : item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`text-3xl font-normal text-[#1D1D1F] hover:text-[#0066CC] transition-all duration-500 transform ${
                     mobileMenuOpen 
                       ? 'opacity-100 translate-y-0' 
                       : 'opacity-0 translate-y-8'
                  }`}
                  style={{ transitionDelay: `${100 + index * 50}ms` }}
                >
                  {item.label}
                </Link>
              )
            ))}
          </nav>

          <div className={`mt-12 flex flex-col items-center gap-4 transition-all duration-500 delay-300 ${
             mobileMenuOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}>
             <Link
                to="/register"
                className="w-full max-w-xs px-8 py-4 bg-[#0066CC] text-white rounded-full text-lg font-medium text-center shadow-xl shadow-blue-500/20 active:scale-95 transition-all"
                onClick={() => setMobileMenuOpen(false)}
              >
                Start Free
              </Link>
              <Link
                to="/login"
                className="text-lg font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Sign In
              </Link>
          </div>

          {/* Decorative Elements */}
          <div className="absolute bottom-10 left-0 right-0 text-center">
            <p className="text-sm text-[#1D1D1F]/20 font-medium tracking-widest uppercase">
              Galerly &copy; 2025
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
