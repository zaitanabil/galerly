import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Features() {
  const sectionRef = useRef<HTMLDivElement>(null);

  const features = [
    {
      title: "Galleries That Breathe",
      description: "Clean lines. Full resolution. Nothing but your work.",
      glow: "rgba(0, 102, 204, 0.3)"
    },
    {
      title: "Share with Confidence",
      description: "One link. Secure sharing. No login required.",
      glow: "rgba(99, 102, 241, 0.3)"
    },
    {
      title: "Complete Feedback Loop",
      description: "Favorites. Comments. Downloads. Real-time.",
      glow: "rgba(236, 72, 153, 0.3)"
    },
    {
      title: "Made for Artists",
      description: "Your brand. Your colors. Your voice.",
      glow: "rgba(249, 115, 22, 0.3)"
    }
  ];

  useEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    const ctx = gsap.context(() => {
      gsap.from('[data-feature-card]', {
        opacity: 0,
        y: 60,
        stagger: 0.1,
        duration: 1,
        ease: "power2.out",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 80%",
          end: "top 40%",
          toggleActions: "play none none reverse"
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      id="features"
      ref={sectionRef}
      className="min-h-screen py-24 relative bg-white z-20"
    >
      
      <div className="relative z-10 w-full max-w-[1400px] mx-auto px-6">
        
        {/* Header */}
        <div className="mb-16 lg:mb-20 text-center">
          <div className="inline-block glass-ultra px-6 py-2 rounded-full mb-6">
            <span className="text-xs font-semibold tracking-[0.15em] uppercase text-[#0066CC]">
              Core Features
            </span>
          </div>
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl md:text-5xl lg:text-7xl font-light tracking-tight text-[#1D1D1F] leading-[1.1] mb-6">
              Professional tools
              <br />
              <span className="text-[#0066CC]">
                that scale.
              </span>
            </h2>
            <p className="text-lg md:text-xl lg:text-2xl font-light text-[#1D1D1F]/60">
              Everything you need. Nothing you don't.
            </p>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group relative"
              data-feature-card
            >
              <div className="glass-strong p-8 md:p-10 rounded-[32px] md:rounded-[40px] glass-hover h-full flex flex-col justify-center relative overflow-hidden min-h-[250px]">
                
                {/* Glow effect on hover */}
                <div 
                  className="absolute -bottom-20 -right-20 w-64 h-64 rounded-full blur-[100px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"
                  style={{ background: feature.glow }}
                />

                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F] mb-4 relative z-10">
                  {feature.title}
                </h3>

                <p className="text-lg md:text-xl font-light text-[#1D1D1F]/60 relative z-10">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
