import { useEffect, useRef } from 'react';

export default function GridBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let mouseX = -1000;
    let mouseY = -1000;

    const handleResize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      ctx.scale(dpr, dpr);
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const draw = () => {
      if (!ctx || !canvas) return;
      
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      ctx.clearRect(0, 0, width, height);
      
      const gridSize = 40; 
      const baseSize = 1;
      
      // We'll iterate through the grid
      for (let x = 0; x <= width; x += gridSize) {
        for (let y = 0; y <= height; y += gridSize) {
          
          // Calculate distance to mouse
          const dx = x - mouseX;
          const dy = y - mouseY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          
          // Interaction radius
          const radius = 400;
          
          let alpha = 0.08; // Very subtle base
          let size = baseSize;
          
          // Offset calculation (push points away slightly)
          const offsetX = 0;
          const offsetY = 0;

          if (dist < radius) {
            const factor = 1 - dist / radius; // 0 to 1
            
            // Increase opacity
            alpha = 0.08 + factor * 0.3;
            
            // Increase size
            size = baseSize + factor * 1.5;
            
            // Push away effect (subtle)
            // const angle = Math.atan2(dy, dx);
            // const push = factor * 10;
            // offsetX = Math.cos(angle) * push;
            // offsetY = Math.sin(angle) * push;
          }
          
          ctx.beginPath();
          ctx.arc(x + offsetX, y + offsetY, size, 0, Math.PI * 2);
          ctx.fillStyle = '#1D1D1F';
          ctx.globalAlpha = alpha;
          ctx.fill();
        }
      }
      
      animationFrameId = requestAnimationFrame(draw);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    
    handleResize();
    draw();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[-1] bg-[#FAFAFA] pointer-events-none">
      <canvas 
        ref={canvasRef}
        className="block"
      />
      {/* Subtle vignette/gradient to soften edges */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white/60" />
    </div>
  );
}
