// Home page - Landing page with all marketing sections
import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';

import Header from '../components/Header';
import Hero from '../components/Hero';
import Philosophy from '../components/Philosophy';
import Features from '../components/Features';
import Workflow from '../components/Workflow';
import GalleryShowcase from '../components/GalleryShowcase';
import UseCases from '../components/UseCases';
import Pricing from '../components/Pricing';
import Security from '../components/Security';
import CTA from '../components/CTA';
import Footer from '../components/Footer';

gsap.registerPlugin(ScrollTrigger);

export default function HomePage() {
  const mainRef = useRef<HTMLDivElement>(null);

  // Use useLayoutEffect for GSAP initialization to prevent flash of unstyled content
  useLayoutEffect(() => {
    // Create a GSAP context for proper cleanup and scoping
    const ctx = gsap.context(() => {
      // Configure global ScrollTrigger settings for better mobile performance
      // ignoreMobileResize prevents jumps when the mobile address bar shows/hides
      ScrollTrigger.config({ 
        ignoreMobileResize: true
      });

      // Set global defaults for smoother animations
      gsap.defaults({
        ease: "power2.out",
        duration: 0.8
      });

      // Refresh ScrollTrigger after a slight delay to ensure all child components 
      // have rendered and layout is stable. This handles race conditions with images/fonts.
      const timer = setTimeout(() => {
        ScrollTrigger.refresh();
      }, 100);

      return () => clearTimeout(timer);
    }, mainRef);

    // Cleanup function: reverts all GSAP animations/triggers created in this context
    return () => ctx.revert();
  }, []);

  return (
    <>
      <Header />
      
      {/* Main container with ref for GSAP context scoping */}
      <main ref={mainRef} className="relative z-10">
        <Hero />
        <Philosophy />
        <Features />
        <Workflow />
        <GalleryShowcase />
        <UseCases />
        <Pricing />
        <Security />
        <CTA />
      </main>
      
      <Footer />
    </>
  );
}
