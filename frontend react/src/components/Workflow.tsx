import { useEffect, useRef, useState, useMemo } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import { Upload, FolderKanban, Share2, ArrowRight, Sparkles } from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Workflow() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const dotsRef = useRef<(HTMLDivElement | null)[]>([]);
  const [activeStep, setActiveStep] = useState(-1);

  const steps = useMemo(() => [
    {
      number: "01",
      title: "Upload",
      tagline: "Drag. Drop. Done.",
      description: "Upload entire sessions in seconds. Full resolution preserved. Smart batch processing handles thousands of images.",
      icon: Upload,
      features: ["Batch upload", "Full resolution", "Auto-organize"]
    },
    {
      number: "02",
      title: "Organize",
      tagline: "Everything in one place.",
      description: "Create stunning galleries with a few clicks. Set permissions, add watermarks, and customize every detail.",
      icon: FolderKanban,
      features: ["Smart galleries", "Custom branding", "Access control"]
    },
    {
      number: "03",
      title: "Share",
      tagline: "One link. Pure simplicity.",
      description: "Generate secure links instantly. Clients browse, favorite, and download without any login. Track every interaction.",
      icon: Share2,
      features: ["Secure links", "Client favorites", "Analytics"]
    }
  ], []);

  useEffect(() => {
    if (!sectionRef.current || typeof window === 'undefined') return;

    const ctx = gsap.context(() => {
      const mm = gsap.matchMedia();

      // Desktop animation
      mm.add("(min-width: 1024px)", () => {
        const path = pathRef.current;
        if (!path) return;

        const pathLength = path.getTotalLength();
        
        gsap.set(path, {
          strokeDasharray: pathLength,
          strokeDashoffset: pathLength
        });

        // Main scroll animation
        ScrollTrigger.create({
          trigger: sectionRef.current,
          start: "top center",
          end: "bottom center",
          onUpdate: (self) => {
            const progress = self.progress;
            
            // Animate path
            gsap.to(path, {
              strokeDashoffset: pathLength * (1 - progress),
              duration: 0.1
            });
            
            // Update active step
            const step = Math.floor(progress * (steps.length + 0.5)) - 1;
            setActiveStep(step);
          }
        });

        // Animate individual step cards
        steps.forEach((_, index) => {
          gsap.fromTo(
            `.workflow-card-${index}`,
            {
              opacity: 0,
              y: 60,
              scale: 0.8
            },
            {
              opacity: 1,
              y: 0,
              scale: 1,
              duration: 0.8,
              ease: "power3.out",
              scrollTrigger: {
                trigger: `.workflow-card-${index}`,
                start: "top 85%",
                end: "top 50%",
                scrub: 1.5
              }
            }
          );
        });

        // Floating animation for icons
        steps.forEach((_, index) => {
          gsap.to(`.workflow-icon-${index}`, {
            y: -10,
            duration: 2,
            repeat: -1,
            yoyo: true,
            ease: "power1.inOut",
            delay: index * 0.3
          });
        });
      });

      // Mobile animation
      mm.add("(max-width: 1023px)", () => {
        steps.forEach((_, index) => {
          gsap.fromTo(
            `.workflow-mobile-${index}`,
            {
              opacity: 0,
              x: -30
            },
            {
              opacity: 1,
              x: 0,
              duration: 0.8,
              ease: "power2.out",
              scrollTrigger: {
                trigger: `.workflow-mobile-${index}`,
                start: "top 90%",
                end: "top 60%",
                scrub: 1
              }
            }
          );
        });
      });

    }, sectionRef);

    return () => ctx.revert();
  }, [steps]);

  return (
    <section 
      id="how-it-works"
      ref={sectionRef}
      className="relative bg-transparent py-32 lg:py-40 z-10 overflow-hidden"
    >
      {/* Animated Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-[#0066CC]/10 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#0066CC]/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#0066CC]/5 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <div className="max-w-7xl mx-auto px-6 relative">
        {/* Header */}
        <div className="text-center mb-24 lg:mb-32">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0066CC]/10 text-[#0066CC] mb-8">
            <Sparkles className="w-4 h-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              How It Works
            </span>
          </div>
          
          <h2 className="text-5xl md:text-6xl lg:text-8xl font-light text-[#1D1D1F] mb-8 leading-tight">
            Three steps to<br />
            <span className="text-[#0066CC]">perfection</span>
          </h2>
          
          <p className="text-xl md:text-2xl text-[#1D1D1F]/60 max-w-3xl mx-auto leading-relaxed">
            From upload to delivery, your photography workflow simplified
          </p>
        </div>

        {/* Desktop: Interactive Path */}
        <div className="hidden lg:block relative min-h-[800px]">
          {/* Animated SVG Path */}
          <svg 
            className="absolute inset-0 w-full h-full pointer-events-none"
            viewBox="0 0 1000 600"
            preserveAspectRatio="xMidYMid meet"
          >
            <defs>
              <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0066CC" stopOpacity="0.3" />
                <stop offset="50%" stopColor="#0066CC" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#0066CC" stopOpacity="0.8" />
              </linearGradient>
              
              <filter id="glow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* Background path (light) */}
            <path
              d="M 150 300 Q 333 150, 500 300 T 850 300"
              fill="none"
              stroke="#0066CC"
              strokeOpacity="0.1"
              strokeWidth="2"
              strokeLinecap="round"
            />
            
            {/* Animated path */}
            <path
              ref={pathRef}
              d="M 150 300 Q 333 150, 500 300 T 850 300"
              fill="none"
              stroke="url(#pathGradient)"
              strokeWidth="4"
              strokeLinecap="round"
              filter="url(#glow)"
            />
          </svg>

          {/* Steps */}
          <div className="relative pt-20 pb-32">
            <div className="grid grid-cols-3 gap-12">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const isActive = activeStep >= index;
                const isPast = activeStep > index;
                
                return (
                  <div
                    key={index}
                    className={`workflow-card-${index} relative flex flex-col items-center`}
                  >
                    {/* Floating Icon Container */}
                    <div className="relative mb-8">
                      {/* Glow effect */}
                      <div 
                        className={`
                          absolute inset-0 rounded-full blur-2xl transition-all duration-700
                          ${isActive ? 'bg-[#0066CC]/30 scale-150' : 'bg-[#0066CC]/0 scale-100'}
                        `}
                      />
                      
                      {/* Icon Circle */}
                      <div 
                        ref={el => dotsRef.current[index] = el}
                        className={`
                          workflow-icon-${index} relative w-32 h-32 rounded-full 
                          flex items-center justify-center transition-all duration-700
                          ${isActive 
                            ? 'bg-gradient-to-br from-[#0066CC] to-[#0052A3] text-white shadow-2xl shadow-[#0066CC]/50 scale-110' 
                            : isPast
                            ? 'bg-[#0066CC] text-white shadow-lg shadow-[#0066CC]/30'
                            : 'bg-white border-4 border-[#1D1D1F]/10 text-[#1D1D1F]/30'
                          }
                        `}
                      >
                        <Icon className="w-14 h-14" strokeWidth={1.5} />
                      </div>

                      {/* Step number badge */}
                      <div 
                        className={`
                          absolute -bottom-2 -right-2 w-10 h-10 rounded-full 
                          flex items-center justify-center text-sm font-bold
                          transition-all duration-700
                          ${isActive 
                            ? 'bg-white text-[#0066CC] shadow-lg scale-110' 
                            : 'bg-[#1D1D1F]/5 text-[#1D1D1F]/40'
                          }
                        `}
                      >
                        {step.number}
                      </div>
                    </div>

                    {/* Card Content */}
                    <div 
                      className={`
                        glass-panel p-8 w-full transition-all duration-700 text-center
                        ${isActive 
                          ? 'shadow-2xl scale-105 border-2 border-[#0066CC]/30' 
                          : isPast
                          ? 'shadow-lg'
                          : 'shadow-md opacity-60 scale-95'
                        }
                      `}
                    >
                      <h3 className="text-3xl font-light text-[#1D1D1F] mb-3">
                        {step.title}
                      </h3>
                      
                      <p className="text-xl font-medium text-[#0066CC] mb-4">
                        {step.tagline}
                      </p>
                      
                      <p className="text-[#1D1D1F]/70 leading-relaxed mb-6">
                        {step.description}
                      </p>

                      {/* Features */}
                      <div className="space-y-2 pt-6 border-t border-[#1D1D1F]/10">
                        {step.features.map((feature, fIndex) => (
                          <div 
                            key={fIndex}
                            className="flex items-center justify-center gap-2 text-sm text-[#1D1D1F]/60"
                          >
                            <div className="w-1.5 h-1.5 rounded-full bg-[#0066CC]" />
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Arrow to next step */}
                    {index < steps.length - 1 && (
                      <div 
                        className={`
                          absolute -right-6 top-16 transition-all duration-700
                          ${isPast ? 'opacity-100' : 'opacity-20'}
                        `}
                      >
                        <ArrowRight 
                          className={`
                            w-12 h-12 transition-all duration-700
                            ${isPast ? 'text-[#0066CC]' : 'text-[#1D1D1F]/20'}
                          `}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Mobile: Vertical Timeline */}
        <div className="lg:hidden relative">
          {/* Vertical line with gradient */}
          <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-[#0066CC]/20 via-[#0066CC]/50 to-[#0066CC]/20" />

          <div className="space-y-20">
            {steps.map((step, index) => {
              const Icon = step.icon;
              
              return (
                <div
                  key={index}
                  className="relative"
                >
                  <div className={`workflow-mobile-${index} relative pl-24`}>
                    {/* Icon Circle */}
                    <div className="absolute left-0 top-0 flex flex-col items-center">
                      <div className="relative">
                        {/* Glow */}
                        <div className="absolute inset-0 bg-[#0066CC]/20 rounded-full blur-xl" />
                        
                        {/* Icon */}
                        <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-[#0066CC] to-[#0052A3] text-white flex items-center justify-center shadow-lg shadow-[#0066CC]/30">
                          <Icon className="w-8 h-8" />
                        </div>
                      </div>
                      
                      {/* Number badge */}
                      <div className="mt-3 px-2 py-1 rounded-full bg-[#0066CC]/10 text-[#0066CC] text-xs font-bold">
                        {step.number}
                      </div>
                    </div>

                    {/* Card */}
                    <div className="glass-panel p-6 shadow-xl">
                      <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F] mb-2">
                        {step.title}
                      </h3>
                      
                      <p className="text-lg font-medium text-[#0066CC] mb-4">
                        {step.tagline}
                      </p>
                      
                      <p className="text-[#1D1D1F]/70 leading-relaxed mb-6">
                        {step.description}
                      </p>

                      {/* Features */}
                      <div className="space-y-2 pt-4 border-t border-[#1D1D1F]/10">
                        {step.features.map((feature, fIndex) => (
                          <div 
                            key={fIndex}
                            className="flex items-center gap-2 text-sm text-[#1D1D1F]/60"
                          >
                            <div className="w-1.5 h-1.5 rounded-full bg-[#0066CC]" />
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Arrow between steps */}
                  {index < steps.length - 1 && (
                    <div className="flex justify-center py-6 text-[#0066CC]">
                      <div className="flex items-center gap-1">
                        <div className="w-1 h-1 rounded-full bg-[#0066CC]/40" />
                        <div className="w-1 h-1 rounded-full bg-[#0066CC]/60" />
                        <ArrowRight className="w-6 h-6 rotate-90" />
                        <div className="w-1 h-1 rounded-full bg-[#0066CC]/60" />
                        <div className="w-1 h-1 rounded-full bg-[#0066CC]/40" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24">
          <div className="max-w-4xl mx-auto rounded-[40px] md:rounded-[56px] bg-gradient-to-br from-[#0066CC] to-[#0052A3] p-10 md:p-14 text-center relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
            
            {/* Content */}
            <div className="relative z-10">
              <p className="text-xl md:text-2xl text-white/90 font-light mb-8">
                Ready to transform your workflow?
              </p>
              <a
                href="/start"
                className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-white text-[#0066CC] text-lg font-medium hover:bg-white/90 transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
              >
                <span>Start for Free</span>
                <ArrowRight className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
