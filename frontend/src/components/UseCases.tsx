import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import ScrollTrigger from 'gsap/ScrollTrigger';
import { ArrowRight, Camera, Users, Briefcase, Home, Calendar } from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function UseCases() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  const useCases = [
    { 
      category: "Weddings", 
      title: "Wedding Photographers", 
      description: "Deliver 500-2000 photos per event. Share with couples and families instantly.",
      icon: Users,
      color: "from-pink-500 to-rose-500"
    },
    { 
      category: "Portraits", 
      title: "Portrait Photographers", 
      description: "Quick turnaround for family portraits. Professional client galleries.",
      icon: Camera,
      color: "from-blue-500 to-cyan-500"
    },
    { 
      category: "Events", 
      title: "Event Photographers", 
      description: "Share with multiple attendees quickly. Easy bulk downloads.",
      icon: Calendar,
      color: "from-purple-500 to-indigo-500"
    },
    { 
      category: "Commercial", 
      title: "Commercial", 
      description: "Professional delivery to business clients. Secure sharing and approval.",
      icon: Briefcase,
      color: "from-green-500 to-emerald-500"
    },
    { 
      category: "Real Estate", 
      title: "Real Estate", 
      description: "Fast turnaround for property photos. MLS-ready delivery.",
      icon: Home,
      color: "from-orange-500 to-amber-500"
    }
  ];

  useEffect(() => {
    if (!sectionRef.current || !trackRef.current || typeof window === 'undefined') return;

    const section = sectionRef.current;
    const track = trackRef.current;

    const mm = gsap.matchMedia();

    const ctx = gsap.context(() => {
      
      mm.add("(min-width: 1024px)", () => {
        // Desktop: Horizontal Scroll
        const getScrollAmount = () => {
          const trackWidth = track.scrollWidth;
          return -(trackWidth - window.innerWidth);
        };

        const tween = gsap.to(track, {
          x: getScrollAmount,
          duration: 3,
          ease: "none",
        });

        ScrollTrigger.create({
          trigger: section,
          start: "top top",
          end: () => `+=${-getScrollAmount()}`,
          pin: true,
          animation: tween,
          scrub: 1,
          invalidateOnRefresh: true
        });
      });

      // Tablet and Mobile: Fade in cards as they scroll into view
      mm.add("(max-width: 1023px)", () => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        gsap.utils.toArray('.use-case-card').forEach((card: any) => {
          gsap.fromTo(card, 
            {
              opacity: 0,
              y: 40,
              scale: 0.95
            },
            {
              opacity: 1,
              y: 0,
              scale: 1,
              duration: 0.6,
              ease: "power2.out",
              scrollTrigger: {
                trigger: card,
                start: "top 85%",
                end: "top 60%",
                scrub: 1
              }
            }
          );
        });
      });

    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      id="use-cases"
      ref={sectionRef}
      className="relative min-h-screen bg-transparent overflow-hidden flex flex-col justify-center py-24 lg:py-32"
    >
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#0066CC]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#0066CC]/5 rounded-full blur-[120px]" />
      </div>

      {/* Header */}
      <div className="w-full max-w-7xl mx-auto px-6 mb-12 lg:mb-16 relative z-10">
        <div className="max-w-4xl">
          <span className="text-xs font-semibold tracking-[0.2em] uppercase text-[#0066CC] mb-6 block">
            Use Cases
          </span>
          <h2 className="text-4xl md:text-5xl lg:text-7xl font-light text-[#1D1D1F] mb-6 leading-tight">
            Built for every<br />photography workflow
          </h2>
          <p className="text-lg md:text-xl text-[#1D1D1F]/60 leading-relaxed">
            From weddings to real estate, Galerly adapts to your needs
          </p>
        </div>
      </div>

      {/* Desktop: Horizontal Scroll Track */}
      <div className="hidden lg:block relative z-10">
        <div 
          ref={trackRef}
          className="flex gap-8 px-6 lg:px-12"
        >
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            
            return (
              <div
                key={index}
                className="flex-shrink-0 w-[420px] group"
              >
                <div className="glass-panel p-10 h-full transition-all duration-500 hover:shadow-2xl hover:-translate-y-2">
                  {/* Icon with gradient background */}
                  <div className="relative mb-8">
                    <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${useCase.color} p-0.5`}>
                      <div className="w-full h-full bg-white rounded-2xl flex items-center justify-center">
                        <Icon className="w-10 h-10 text-[#1D1D1F]" />
                      </div>
                    </div>
                  </div>

                  {/* Category Badge */}
                  <div className="mb-6">
                    <span className="inline-block px-4 py-2 rounded-full bg-[#0066CC]/10 text-xs font-semibold uppercase text-[#0066CC] tracking-wider">
                      {useCase.category}
                    </span>
                  </div>

                  {/* Content */}
                  <h3 className="text-3xl font-light text-[#1D1D1F] mb-4 leading-tight">
                    {useCase.title}
                  </h3>

                  <p className="text-lg text-[#1D1D1F]/70 leading-relaxed mb-8">
                    {useCase.description}
                  </p>

                  {/* CTA */}
                  <button className="inline-flex items-center gap-2 text-sm font-medium text-[#0066CC] hover:gap-3 transition-all duration-300">
                    <span>Learn more</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile & Tablet: Vertical Stack */}
      <div className="lg:hidden relative z-10 px-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            
            return (
              <div
                key={index}
                className="use-case-card"
              >
                <div className="glass-panel p-6 md:p-8 transition-all duration-300 active:scale-[0.98]">
                  {/* Top section: Icon and Category */}
                  <div className="flex items-start gap-4 mb-6">
                    {/* Icon */}
                    <div className={`flex-shrink-0 w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-gradient-to-br ${useCase.color} p-0.5`}>
                      <div className="w-full h-full bg-white rounded-2xl flex items-center justify-center">
                        <Icon className="w-8 h-8 md:w-10 md:h-10 text-[#1D1D1F]" />
                      </div>
                    </div>

                    {/* Category Badge */}
                    <div className="flex-1 pt-2">
                      <span className="inline-block px-3 py-1.5 rounded-full bg-[#0066CC]/10 text-xs font-semibold uppercase text-[#0066CC] tracking-wider">
                        {useCase.category}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F] mb-3 leading-tight">
                    {useCase.title}
                  </h3>

                  <p className="text-base md:text-lg text-[#1D1D1F]/70 leading-relaxed mb-6">
                    {useCase.description}
                  </p>

                  {/* CTA */}
                  <button className="inline-flex items-center gap-2 text-sm font-medium text-[#0066CC] hover:gap-3 transition-all duration-300">
                    <span>Learn more</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scroll Indicator (Desktop only) */}
      <div className="hidden lg:block absolute bottom-12 left-1/2 -translate-x-1/2 z-20">
        <div className="flex items-center gap-2 text-sm text-[#1D1D1F]/40">
          <span>Scroll to explore</span>
          <ArrowRight className="w-4 h-4 animate-pulse" />
        </div>
      </div>
    </section>
  );
}
