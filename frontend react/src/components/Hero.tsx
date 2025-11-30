import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ArrowRight, Play } from 'lucide-react';

export default function Hero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const visualRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Setup initial states
      gsap.set('.hero-text-element', { y: 50, opacity: 0 });
      gsap.set('.hero-card', { rotationY: 0, rotationX: 0 });
      
      // Entrance Timeline
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.to('.hero-text-element', {
        y: 0,
        opacity: 1,
        duration: 1,
        stagger: 0.15,
        delay: 0.2
      })
      .from('.hero-visual-bg', {
        scale: 0.8,
        opacity: 0,
        duration: 1.2,
        ease: "power2.out"
      }, "-=0.8")
      .from('.hero-card', {
        y: 100,
        opacity: 0,
        duration: 1,
        stagger: 0.1
      }, "-=0.8");

      // Slideshow Animation
      const slides = gsap.utils.toArray('.hero-slide') as HTMLElement[];
      const loop = gsap.timeline({
        repeat: -1,
        paused: false,
        defaults: { ease: "power2.inOut" }
      });

      slides.forEach((slide, i) => {
        const nextSlide = slides[i + 1] || slides[0];
        
        // Initial state for all slides except first
        if (i !== 0) {
          gsap.set(slide, { opacity: 0, scale: 1.1, zIndex: 0 });
        } else {
          gsap.set(slide, { opacity: 1, scale: 1, zIndex: 1 });
        }
        
        // Sequence
        const t = gsap.timeline()
          .to(slide, { 
            scale: 1.05, 
            duration: 4, 
            ease: "none" 
          })
          .to(slide, { 
            opacity: 0, 
            duration: 1.5 
          }, "-=1.5")
          .to(nextSlide, { 
            opacity: 1, 
            scale: 1,
            zIndex: 1,
            duration: 1.5 
          }, "-=1.5")
          .set(slide, { zIndex: 0, scale: 1.1 }); // Reset for next loop

        loop.add(t);
      });

      // Mouse Movement Parallax & Tilt (Desktop Only)
      const handleMouseMove = (e: MouseEvent) => {
        if (!containerRef.current || window.innerWidth < 1024) return;
        
        const { clientX, clientY } = e;
        const { innerWidth, innerHeight } = window;
        
        // Calculate normalized position (-1 to 1)
        const xPos = (clientX / innerWidth - 0.5) * 2;
        const yPos = (clientY / innerHeight - 0.5) * 2;

        // Tilt Cards
        gsap.to('.hero-card-main', {
          rotationY: xPos * 5, // Rotate Y based on X position
          rotationX: -yPos * 5, // Rotate X based on Y position
          duration: 1,
          ease: "power2.out"
        });

        // Parallax Floating Elements
        gsap.to('.float-element-1', {
          x: xPos * 30,
          y: yPos * 30,
          duration: 1.5,
          ease: "power2.out"
        });
        
        gsap.to('.float-element-2', {
          x: -xPos * 20,
          y: -yPos * 20,
          duration: 1.5,
          ease: "power2.out"
        });
        
        gsap.to('.hero-visual-bg', {
          x: -xPos * 10,
          y: -yPos * 10,
          duration: 2,
          ease: "power2.out"
        });
      };

      window.addEventListener('mousemove', handleMouseMove);

      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
      };
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={containerRef} 
      className="relative min-h-[100vh] flex items-center pt-32 pb-20 lg:pt-20 lg:pb-12 overflow-hidden"
    >
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Text Content */}
          <div ref={textRef} className="max-w-2xl mx-auto lg:mx-0 text-center lg:text-left">
            {/* Badge */}
            <div className="hero-text-element inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-100 mb-8">
              <span className="flex h-2 w-2 rounded-full bg-[#0066CC]"></span>
              <span className="text-sm font-medium text-[#0066CC] tracking-wide uppercase">For Professional Photographers</span>
            </div>

            {/* Headline */}
            <h1 className="hero-text-element text-5xl md:text-7xl lg:text-8xl font-normal text-[#1D1D1F] leading-[1.1] lg:leading-[0.95] tracking-tight mb-8">
              Share art, <br />
              <span className="font-medium bg-clip-text text-transparent bg-gradient-to-r from-[#0066CC] to-[#00A3FF]">
                not files.
              </span>
            </h1>

            {/* Description */}
            <p className="hero-text-element text-lg md:text-xl text-[#1D1D1F]/70 leading-relaxed mb-10 max-w-lg mx-auto lg:mx-0">
              Beautiful galleries. Simple delivery. Real moments.
              Experience the photography platform designed for artists, not just users.
            </p>

            {/* Buttons */}
            <div className="hero-text-element flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <button className="group relative px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium overflow-hidden transition-all hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25">
                <span className="relative z-10 flex items-center justify-center gap-2">
                  Start Free
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
              
              <button className="group px-8 py-4 bg-white border border-gray-200 text-[#1D1D1F] rounded-full font-medium transition-all hover:bg-gray-50 hover:border-gray-300 flex items-center justify-center gap-2">
                <Play className="w-4 h-4 fill-current" />
                View Demo Gallery
              </button>
            </div>
            
            {/* Trust Indicator */}
            <div className="hero-text-element mt-12 flex items-center justify-center lg:justify-start gap-4 text-sm text-gray-500">
              <div className="flex -space-x-2">
                {[1,2,3,4].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-[10px] overflow-hidden">
                    <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-300" />
                  </div>
                ))}
              </div>
              <p>Trusted by photographers worldwide</p>
            </div>
          </div>

          {/* Right Column: Interactive Visuals */}
          <div ref={visualRef} className="relative h-[500px] md:h-[600px] flex items-center justify-center perspective-[1000px] mt-8 lg:mt-0">
             {/* Abstract Background Blob */}
             <div className="hero-visual-bg absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-gradient-to-br from-blue-100/40 via-purple-100/30 to-transparent rounded-full blur-[80px]" />

             {/* Main Card (Gallery Slideshow) */}
             <div 
               ref={cardRef}
               className="hero-card hero-card-main relative w-full max-w-[320px] md:max-w-[400px] aspect-[4/5] bg-white rounded-2xl shadow-2xl overflow-hidden border-[8px] border-white z-20"
               style={{ transformStyle: 'preserve-3d' }}
             >
                <div className="relative w-full h-full overflow-hidden rounded-lg bg-gray-100">
                  {/* Slides */}
                  <div className="hero-slide absolute inset-0 w-full h-full">
                    <img 
                      src="https://images.unsplash.com/photo-1492633423870-43d1cd2775eb?q=80&w=1000&auto=format&fit=crop" 
                      alt="Emotion - Portrait" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-60" />
                    <div className="absolute bottom-6 left-6 text-white transform translate-z-10">
                      <p className="text-sm font-medium tracking-wider uppercase opacity-90">Emotion</p>
                      <p className="text-2xl font-serif italic">Real Connection</p>
                    </div>
                </div>
                
                  <div className="hero-slide absolute inset-0 w-full h-full opacity-0">
                    <img 
                      src="https://images.unsplash.com/photo-1511795409834-ef04bbd61622?q=80&w=1000&auto=format&fit=crop" 
                      alt="Event - Celebration" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-60" />
                    <div className="absolute bottom-6 left-6 text-white transform translate-z-10">
                      <p className="text-sm font-medium tracking-wider uppercase opacity-90">Event</p>
                      <p className="text-2xl font-serif italic">Unforgettable</p>
                    </div>
                </div>
                
                  <div className="hero-slide absolute inset-0 w-full h-full opacity-0">
                    <img 
                      src="https://images.unsplash.com/photo-1605656100868-b3cb24ccb50a?q=80&w=1000&auto=format&fit=crop" 
                      alt="Memory - Nostalgia" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-60" />
                    <div className="absolute bottom-6 left-6 text-white transform translate-z-10">
                      <p className="text-sm font-medium tracking-wider uppercase opacity-90">Memory</p>
                      <p className="text-2xl font-serif italic">Timeless</p>
                      </div>
                   </div>
                </div>
             </div>

             {/* Floating Elements (Parallax) */}
             <div className="hero-card float-element-1 absolute top-[15%] -right-[5%] w-40 h-48 bg-white rounded-lg shadow-xl border-[6px] border-white transform rotate-6 z-30 hidden md:block">
               <div className="w-full h-full overflow-hidden rounded bg-gray-100">
                 <img 
                   src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=400&auto=format&fit=crop" 
                   alt="Portrait" 
                   className="w-full h-full object-cover"
                 />
               </div>
             </div>

             <div className="hero-card float-element-2 absolute bottom-[20%] -left-[10%] w-32 h-32 bg-white rounded-lg shadow-xl border-[6px] border-white transform -rotate-12 z-10 hidden md:block">
               <div className="w-full h-full overflow-hidden rounded bg-gray-100">
                  <img 
                   src="https://images.unsplash.com/photo-1519225448520-45c1a74f4944?q=80&w=400&auto=format&fit=crop" 
                   alt="Detail" 
                   className="w-full h-full object-cover"
                 />
               </div>
             </div>
          </div>
        </div>
      </div>
    </section>
  );
}
