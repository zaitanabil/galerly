import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Security() {
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    const ctx = gsap.context(() => {
      gsap.from('[data-shield]', {
        scale: 0.8,
        opacity: 0,
        duration: 1.5,
        ease: "elastic.out(1, 0.7)",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 80%", // Trigger earlier on mobile
        }
      });
      
      gsap.from('[data-stat]', {
        y: 40,
        opacity: 0,
        stagger: 0.2,
        duration: 1,
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 85%",
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="py-24 md:py-32 bg-transparent relative overflow-hidden">
      <div className="max-w-[1400px] mx-auto px-6 relative z-10">
        
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          
          {/* Visual Side */}
          <div className="flex justify-center order-first lg:order-none" data-shield>
            <div className="relative w-full max-w-[320px] md:max-w-[400px] aspect-square">
               {/* Abstract Shield/Lock constructed of glass panels */}
               <div className="absolute inset-0 bg-blue-500/5 rounded-full blur-[80px]" />
               <div className="absolute inset-4 md:inset-10 glass-panel rotate-3 flex items-center justify-center">
                  <div className="w-24 h-32 md:w-32 md:h-40 border-4 border-[#0066CC]/20 rounded-2xl flex items-center justify-center">
                    <div className="w-4 h-4 bg-[#0066CC] rounded-full shadow-[0_0_20px_rgba(0,102,204,0.5)]" />
                  </div>
               </div>
               <div className="absolute top-0 right-0 md:right-10 glass-ultra px-4 py-2 md:px-6 md:py-3 animate-bounce" style={{ animationDuration: '3s' }}>
                 <span className="text-xs md:text-sm font-medium text-[#0066CC]">AES-256</span>
               </div>
               <div className="absolute bottom-4 left-0 glass-ultra px-4 py-2 md:px-6 md:py-3 animate-bounce" style={{ animationDuration: '4s' }}>
                 <span className="text-xs md:text-sm font-medium text-[#0066CC]">GDPR Ready</span>
               </div>
            </div>
          </div>

          {/* Text Side */}
          <div className="text-center lg:text-left">
            <h2 className="text-4xl md:text-7xl font-light text-[#1D1D1F] mb-6 md:mb-8 leading-tight">
              Your work. <br/>
              <span className="text-[#0066CC]">Locked tight.</span>
            </h2>
            <p className="text-lg md:text-xl text-[#1D1D1F]/60 mb-8 md:mb-12 max-w-lg mx-auto lg:mx-0 leading-relaxed">
              Enterprise-grade security comes standard. We use the same infrastructure as the world's largest banks to keep your photography safe.
            </p>

            <div className="grid grid-cols-2 gap-8">
              <div data-stat>
                <div className="text-3xl md:text-4xl font-light text-[#1D1D1F] mb-2">99.9%</div>
                <div className="text-xs md:text-sm text-[#1D1D1F]/40 uppercase tracking-wider">Uptime SLA</div>
              </div>
              <div data-stat>
                <div className="text-3xl md:text-4xl font-light text-[#1D1D1F] mb-2">AWS</div>
                <div className="text-xs md:text-sm text-[#1D1D1F]/40 uppercase tracking-wider">Infrastructure</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
