import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function MouseFollower() {
  const cursorRef = useRef<HTMLDivElement>(null);
  const followerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cursor = cursorRef.current;
    const follower = followerRef.current;
    
    // Only run on desktop/devices with hover
    const mediaQuery = window.matchMedia("(pointer: fine)");
    if (!mediaQuery.matches) return;
    
    if (!cursor || !follower) return;

    // Center the elements initially
    gsap.set(cursor, { xPercent: -50, yPercent: -50, scale: 0 });
    gsap.set(follower, { xPercent: -50, yPercent: -50, scale: 0 });

    // Fade in
    gsap.to([cursor, follower], { scale: 1, duration: 0.5, ease: "back.out" });

    const onMouseMove = (e: MouseEvent) => {
      // Immediate movement for the small dot
      gsap.to(cursor, { 
        x: e.clientX, 
        y: e.clientY, 
        duration: 0.1,
        overwrite: true
      });
      
      // Smoother movement for the larger circle (lag effect)
      gsap.to(follower, { 
        x: e.clientX, 
        y: e.clientY, 
        duration: 0.6,
        ease: "power3.out",
        overwrite: true
      });
    };
    
    // Add hover effects for clickable elements
    const onMouseEnterLink = () => {
      gsap.to(cursor, { scale: 0, duration: 0.2 });
      gsap.to(follower, { 
        scale: 1.5, 
        backgroundColor: "rgba(0, 102, 204, 0.1)", 
        borderColor: "transparent",
        duration: 0.3 
      });
    };
    
    const onMouseLeaveLink = () => {
      gsap.to(cursor, { scale: 1, duration: 0.2 });
      gsap.to(follower, { 
        scale: 1, 
        backgroundColor: "transparent", 
        borderColor: "rgba(29, 29, 31, 0.3)",
        duration: 0.3 
      });
    };

    window.addEventListener('mousemove', onMouseMove);
    
    // Attach listeners to interactive elements
    const links = document.querySelectorAll('a, button, [role="button"]');
    links.forEach(link => {
      link.addEventListener('mouseenter', onMouseEnterLink);
      link.addEventListener('mouseleave', onMouseLeaveLink);
    });

    // Observer for new elements (optional, but good for dynamic content)
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length) {
           const newLinks = document.querySelectorAll('a, button, [role="button"]');
           newLinks.forEach(link => {
             // Basic check to avoid double binding (could be improved)
             link.removeEventListener('mouseenter', onMouseEnterLink);
             link.removeEventListener('mouseleave', onMouseLeaveLink);
             link.addEventListener('mouseenter', onMouseEnterLink);
             link.addEventListener('mouseleave', onMouseLeaveLink);
           });
        }
      });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      links.forEach(link => {
        link.removeEventListener('mouseenter', onMouseEnterLink);
        link.removeEventListener('mouseleave', onMouseLeaveLink);
      });
      observer.disconnect();
    };
  }, []);

  return (
    <>
      {/* Main cursor dot (small) */}
      <div 
        ref={cursorRef}
        className="fixed top-0 left-0 w-2 h-2 bg-[#1D1D1F] rounded-full pointer-events-none z-[9999]"
      />
      {/* Follower circle (larger, delayed) */}
      <div 
        ref={followerRef}
        className="fixed top-0 left-0 w-10 h-10 border border-[#1D1D1F]/30 rounded-full pointer-events-none z-[9998] transition-colors duration-300"
      />
    </>
  );
}

