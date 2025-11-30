import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function GalleryShowcase() {
  const sectionRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    // Use gsap.context for scoping
    const ctx = gsap.context(() => {
      const mm = gsap.matchMedia();
      
      // Desktop/Tablet: Staggered animation
      mm.add("(min-width: 768px)", () => {
        // Select elements within the scope of sectionRef
        const cards = gsap.utils.toArray('[data-showcase-card]');
        
        if (cards.length > 0) {
        // Set initial state
        gsap.set(cards, { opacity: 0, y: 50 });
        
          // Create scroll trigger
        gsap.to(cards, {
          opacity: 1,
          y: 0,
          stagger: 0.2,
          duration: 1.2,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
            toggleActions: "play none none none",
            once: true
          }
        });
        }
      });

      // Mobile: Individual card animations
      mm.add("(max-width: 767px)", () => {
        const cards = gsap.utils.toArray('[data-showcase-card]') as Element[];
        
        cards.forEach((card) => {
          gsap.set(card, { opacity: 0, y: 50 });
          
          gsap.to(card, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power3.out",
            scrollTrigger: {
              trigger: card,
              start: "top 85%",
              toggleActions: "play none none none",
              once: true
            }
          });
        });
      });

      return () => {
        // Cleanup matchMedia when context reverts
        // mm.revert(); // Not strictly necessary as context revert handles it, but good practice if mixed
      };
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={sectionRef}
      className="min-h-screen w-full flex flex-col py-24 px-6 md:px-12 relative overflow-hidden"
    >
      
      <div className="relative z-10 w-full max-w-[1400px] mx-auto">
        
        {/* Header */}
        <div className="text-center mb-16 md:mb-20">
          <span className="text-xs font-semibold tracking-[0.2em] uppercase text-[#0066CC] mb-6 block">
            Showcase
          </span>
          <h2 className="text-4xl md:text-5xl lg:text-8xl font-light tracking-tight text-[#1D1D1F] leading-[1.1] mb-6">
            Your work,
            <br />
            <span className="text-[#0066CC]">beautifully presented.</span>
          </h2>
        </div>

        {/* Visual Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          
          {/* Card 1 - Wedding */}
          <div 
            className="lg:col-span-2 h-[400px] md:h-[500px] glass-panel relative overflow-hidden group cursor-pointer"
            data-showcase-card
          >
            <div className="absolute inset-0 bg-gray-50 transition-transform duration-700 ease-out group-hover:scale-105 flex items-center justify-center">
               <div className="w-full h-full bg-gradient-to-br from-blue-50/50 to-purple-50/50" />
               <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-24 h-24 md:w-32 md:h-32 rounded-full border border-[#1D1D1F]/5 group-hover:scale-110 transition-transform duration-700" />
               </div>
               <span className="absolute text-xl md:text-2xl font-light text-[#1D1D1F]/20 group-hover:text-[#1D1D1F]/40 transition-colors z-10">Wedding Portfolio</span>
            </div>
             <div className="absolute bottom-6 left-6 md:bottom-8 md:left-8 z-20">
                <div className="bg-white/90 backdrop-blur-md px-4 py-2 rounded-full border border-white/50">
                  <h3 className="text-xs md:text-sm font-medium text-[#1D1D1F]">Wedding Collection</h3>
                </div>
             </div>
          </div>

          {/* Card 2 - Editorial */}
          <div 
            className="h-[400px] md:h-[500px] glass-panel relative overflow-hidden group cursor-pointer"
            data-showcase-card
          >
             <div className="absolute inset-0 bg-gray-50 transition-transform duration-700 ease-out group-hover:scale-105 flex items-center justify-center">
               <div className="w-full h-full bg-gradient-to-br from-amber-50/50 to-orange-50/50" />
               <span className="absolute text-xl md:text-2xl font-light text-[#1D1D1F]/20 group-hover:text-[#1D1D1F]/40 transition-colors z-10">Editorial</span>
            </div>
             <div className="absolute bottom-6 left-6 md:bottom-8 md:left-8 z-20">
                <div className="bg-white/90 backdrop-blur-md px-4 py-2 rounded-full border border-white/50">
                   <h3 className="text-xs md:text-sm font-medium text-[#1D1D1F]">Editorial</h3>
                </div>
             </div>
          </div>

          {/* Card 3 - Portrait */}
          <div 
            className="h-[350px] md:h-[400px] glass-panel relative overflow-hidden group cursor-pointer"
            data-showcase-card
          >
             <div className="absolute inset-0 bg-gray-50 transition-transform duration-700 ease-out group-hover:scale-105 flex items-center justify-center">
               <div className="w-full h-full bg-gradient-to-br from-emerald-50/50 to-teal-50/50" />
               <span className="absolute text-xl md:text-2xl font-light text-[#1D1D1F]/20 group-hover:text-[#1D1D1F]/40 transition-colors z-10">Portrait</span>
            </div>
             <div className="absolute bottom-6 left-6 md:bottom-8 md:left-8 z-20">
                <div className="bg-white/90 backdrop-blur-md px-4 py-2 rounded-full border border-white/50">
                   <h3 className="text-xs md:text-sm font-medium text-[#1D1D1F]">Portrait</h3>
                </div>
             </div>
          </div>

          {/* Card 4 - Commercial */}
          <div 
            className="lg:col-span-2 h-[350px] md:h-[400px] glass-panel relative overflow-hidden group cursor-pointer"
            data-showcase-card
          >
             <div className="absolute inset-0 bg-gray-50 transition-transform duration-700 ease-out group-hover:scale-105 flex items-center justify-center">
               <div className="w-full h-full bg-gradient-to-br from-gray-100 to-slate-200" />
               <div className="absolute w-[80%] h-[1px] bg-[#1D1D1F]/10 transform -rotate-12" />
               <div className="absolute w-[80%] h-[1px] bg-[#1D1D1F]/10 transform rotate-12" />
               <span className="absolute text-xl md:text-2xl font-light text-[#1D1D1F]/20 group-hover:text-[#1D1D1F]/40 transition-colors z-10">Commercial</span>
            </div>
             <div className="absolute bottom-6 left-6 md:bottom-8 md:left-8 z-20">
                 <div className="bg-white/90 backdrop-blur-md px-4 py-2 rounded-full border border-white/50">
                   <h3 className="text-xs md:text-sm font-medium text-[#1D1D1F]">Commercial Projects</h3>
                </div>
             </div>
          </div>
        </div>
      </div>
    </section>
  );
}