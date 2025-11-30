import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import { FileX, Image, Sparkles, ArrowRight } from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Philosophy() {
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    const mm = gsap.matchMedia();

    const ctx = gsap.context(() => {
      
      // Desktop Animation (Pinned transition)
      mm.add("(min-width: 1024px)", () => {
        
        // Initial states
        gsap.set('[data-problem-content]', { opacity: 1, y: 0, scale: 1 });
        gsap.set('[data-solution-content]', { opacity: 0, y: 100, scale: 0.95 });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top top",
            end: "+=200%",
            pin: true,
            scrub: 1.5,
            anticipatePin: 1
          }
        });

        // Transition animation
        tl.to('[data-problem-content]', { 
          opacity: 0, 
          y: -100, 
          scale: 0.95,
          duration: 1, 
          ease: "power2.inOut" 
        })
        .to('[data-solution-content]', { 
          opacity: 1, 
          y: 0, 
          scale: 1,
          duration: 1, 
          ease: "power2.out" 
        }, "-=0.5");
      });

      // Mobile & Tablet Animation (Stacked)
      mm.add("(max-width: 1023px)", () => {
        const cards = gsap.utils.toArray<Element>('[data-philosophy-card]');
        
        cards.forEach((card) => {
          gsap.set(card, { opacity: 0, y: 60 });
          
          gsap.to(card, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power3.out",
            scrollTrigger: {
              trigger: card,
              start: "top 85%",
              end: "top 60%",
              scrub: 1
            }
          });
        });
      });

    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={sectionRef}
      className="relative min-h-screen bg-transparent overflow-hidden"
    >
      {/* Animated background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-red-500/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-[#0066CC]/5 rounded-full blur-[140px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-purple-500/5 rounded-full blur-[160px] animate-pulse" style={{ animationDuration: '4s' }} />
      </div>

      {/* Desktop Layout (Pinned transition) */}
      <div className="hidden lg:flex h-screen items-center justify-center relative">
        <div className="relative z-10 w-full max-w-7xl px-6">
          
          {/* Problem State */}
          <div 
            data-problem-content
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="w-full max-w-5xl text-center">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-600 mb-8">
                <FileX className="w-4 h-4" />
                <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                  The Problem
                </span>
              </div>

              {/* Heading */}
              <h2 className="text-5xl md:text-6xl lg:text-8xl font-light text-[#1D1D1F] mb-8 leading-tight">
                Stop sending files.
                <br />
                <span className="text-red-500">Start sharing art.</span>
              </h2>

              {/* Description */}
              <p className="text-xl md:text-2xl text-[#1D1D1F]/60 max-w-3xl mx-auto leading-relaxed mb-16">
                WeTransfer links expire. Email attachments break. Dropbox folders feel cold.
                <br />
                Your work deserves better than a file dump.
              </p>

              {/* Visual comparison */}
              <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
                {[
                  { label: 'WeTransfer', issue: 'Links expire' },
                  { label: 'Email', issue: 'Size limits' },
                  { label: 'Dropbox', issue: 'No context' }
                ].map((item, i) => (
                  <div 
                    key={i}
                    className="glass-panel p-8 relative group hover:border-red-500/20 transition-all duration-300"
                  >
                    <div className="absolute -top-3 -right-3 w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                      <FileX className="w-5 h-5 text-red-500" />
                    </div>
                    <div className="mb-4">
                      <div className="w-12 h-12 rounded-lg bg-[#1D1D1F]/5 mx-auto" />
                    </div>
                    <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                      {item.label}
                    </h3>
                    <p className="text-sm text-red-500">
                      {item.issue}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Solution State */}
          <div 
            data-solution-content
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="w-full max-w-6xl text-center">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0066CC]/10 border border-[#0066CC]/20 text-[#0066CC] mb-8">
                <Sparkles className="w-4 h-4" />
                <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                  The Galerly Way
                </span>
              </div>

              {/* Heading */}
              <h2 className="text-5xl md:text-6xl lg:text-8xl font-light text-[#1D1D1F] mb-8 leading-tight">
                Immersive galleries.
                <br />
                <span className="text-[#0066CC]">Zero friction.</span>
              </h2>

              {/* Description */}
              <p className="text-xl md:text-2xl text-[#1D1D1F]/60 max-w-3xl mx-auto leading-relaxed mb-16">
                Every photo deserves context. Every client deserves an experience.
                <br />
                A presentation that honors the moment you captured.
              </p>

              {/* Visual showcase */}
              <div className="relative max-w-5xl mx-auto">
                {/* Main gallery preview */}
                <div className="glass-panel p-8 md:p-12 relative overflow-hidden group">
                  {/* Gradient background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-[#0066CC]/5 via-purple-500/5 to-pink-500/5" />
                  
                  {/* Grid pattern */}
                  <div className="absolute inset-0 opacity-[0.02]" style={{
                    backgroundImage: 'linear-gradient(#1D1D1F 1px, transparent 1px), linear-gradient(90deg, #1D1D1F 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                  }} />

                  {/* Content */}
                  <div className="relative z-10">
                    {/* Mock gallery grid */}
                    <div className="grid grid-cols-3 gap-4 mb-8">
                      {[1, 2, 3].map((i) => (
                        <div 
                          key={i}
                          className="aspect-[4/3] rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center group-hover:scale-105 transition-transform duration-500"
                          style={{ transitionDelay: `${i * 100}ms` }}
                        >
                          <Image className="w-8 h-8 text-[#1D1D1F]/20" />
                        </div>
                      ))}
                    </div>

                    {/* Gallery info */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-[#0066CC]/10 flex items-center justify-center">
                          <Image className="w-5 h-5 text-[#0066CC]" />
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-medium text-[#1D1D1F]">
                            Beautiful Gallery View
                          </p>
                          <p className="text-xs text-[#1D1D1F]/60">
                            Professional presentation
                          </p>
                        </div>
                      </div>
                      <button className="px-6 py-3 rounded-full bg-[#0066CC] text-white text-sm font-medium hover:bg-[#0052A3] transition-all duration-300 flex items-center gap-2 hover:gap-3">
                        <span>View Gallery</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Features badges */}
                <div className="flex flex-wrap justify-center gap-3 mt-8">
                  {[
                    'Never expires',
                    'Client favorites',
                    'Download control',
                    'Real-time updates'
                  ].map((feature, i) => (
                    <div 
                      key={i}
                      className="px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm border border-[#1D1D1F]/10 text-sm text-[#1D1D1F]/70"
                    >
                      {feature}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Mobile/Tablet Layout (Stacked) */}
      <div className="lg:hidden py-24 px-6">
        <div className="max-w-2xl mx-auto space-y-20">
          
          {/* Problem Card */}
          <div data-philosophy-card className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-600 mb-6">
              <FileX className="w-4 h-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                The Problem
              </span>
            </div>

            <h2 className="text-4xl md:text-5xl font-light text-[#1D1D1F] mb-6 leading-tight">
              Stop sending files.
              <br />
              <span className="text-red-500">Start sharing art.</span>
            </h2>

            <p className="text-lg md:text-xl text-[#1D1D1F]/60 leading-relaxed mb-10">
              WeTransfer links expire. Email attachments break. Dropbox folders feel cold.
              Your work deserves better.
            </p>

            <div className="space-y-4">
              {[
                { label: 'WeTransfer', issue: 'Links expire' },
                { label: 'Email', issue: 'Size limits' },
                { label: 'Dropbox', issue: 'No context' }
              ].map((item, i) => (
                <div 
                  key={i}
                  className="glass-panel p-6 flex items-center justify-between"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#1D1D1F]/5" />
                    <span className="text-base font-medium text-[#1D1D1F]">
                      {item.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-red-500">{item.issue}</span>
                    <FileX className="w-5 h-5 text-red-500" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Solution Card */}
          <div data-philosophy-card className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0066CC]/10 border border-[#0066CC]/20 text-[#0066CC] mb-6">
              <Sparkles className="w-4 h-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                The Galerly Way
              </span>
            </div>

            <h2 className="text-4xl md:text-5xl font-light text-[#1D1D1F] mb-6 leading-tight">
              Immersive galleries.
              <br />
              <span className="text-[#0066CC]">Zero friction.</span>
            </h2>

            <p className="text-lg md:text-xl text-[#1D1D1F]/60 leading-relaxed mb-10">
              Every photo deserves context. Every client deserves an experience.
              A presentation that honors the moment.
            </p>

            {/* Gallery preview */}
            <div className="glass-panel p-6 md:p-8 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-[#0066CC]/5 via-purple-500/5 to-pink-500/5" />
              
              <div className="relative z-10">
                <div className="grid grid-cols-3 gap-3 mb-6">
                  {[1, 2, 3].map((i) => (
                    <div 
                      key={i}
                      className="aspect-[4/3] rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center"
                    >
                      <Image className="w-6 h-6 text-[#1D1D1F]/20" />
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#0066CC]/10 flex items-center justify-center">
                      <Image className="w-4 h-4 text-[#0066CC]" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium text-[#1D1D1F]">
                        Beautiful Gallery
                      </p>
                      <p className="text-xs text-[#1D1D1F]/60">
                        Professional
                      </p>
                    </div>
                  </div>
                  <button className="px-4 py-2 rounded-full bg-[#0066CC] text-white text-sm font-medium flex items-center gap-2">
                    <span>View</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {['Never expires', 'Client favorites', 'Download control', 'Real-time'].map((feature, i) => (
                <div 
                  key={i}
                  className="px-3 py-1.5 rounded-full bg-white/60 backdrop-blur-sm border border-[#1D1D1F]/10 text-xs text-[#1D1D1F]/70"
                >
                  {feature}
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
