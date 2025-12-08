import { useRef, useEffect } from 'react';
import { HotMoment } from '../services/analyticsService';

interface VideoAttentionTimelineProps {
  duration: number; // Video duration in seconds
  hotMoments: HotMoment[];
  currentTime?: number; // Current playback time
  onSeek?: (time: number) => void; // Callback when user clicks timeline
}

// Visual timeline showing where clients pause, rewind, and pay attention in videos
export default function VideoAttentionTimeline({ 
  duration, 
  hotMoments, 
  currentTime = 0,
  onSeek 
}: VideoAttentionTimelineProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw background gradient
    const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
    bgGradient.addColorStop(0, '#f0f9ff');
    bgGradient.addColorStop(1, '#e0f2fe');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);

    // Draw time markers
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 1;
    const numMarkers = 5;
    for (let i = 0; i <= numMarkers; i++) {
      const x = (i / numMarkers) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Draw hot moments as gradient bars
    hotMoments.forEach(moment => {
      const startX = (moment.start_time / duration) * width;
      const endX = (moment.end_time / duration) * width;
      const barWidth = Math.max(endX - startX, 4);

      // Heat map color based on intensity
      const intensity = moment.intensity / 100;
      const gradient = ctx.createLinearGradient(startX, 0, startX, height);
      
      if (intensity >= 0.8) {
        // High intensity - red/orange
        gradient.addColorStop(0, `rgba(239, 68, 68, ${intensity})`);
        gradient.addColorStop(1, `rgba(249, 115, 22, ${intensity})`);
      } else if (intensity >= 0.5) {
        // Medium intensity - orange/yellow
        gradient.addColorStop(0, `rgba(249, 115, 22, ${intensity})`);
        gradient.addColorStop(1, `rgba(251, 191, 36, ${intensity})`);
      } else {
        // Low intensity - yellow/green
        gradient.addColorStop(0, `rgba(251, 191, 36, ${intensity})`);
        gradient.addColorStop(1, `rgba(34, 197, 94, ${intensity})`);
      }

      ctx.fillStyle = gradient;
      ctx.fillRect(startX, 0, barWidth, height);

      // Add glow effect for high intensity moments
      if (intensity >= 0.7) {
        ctx.shadowColor = intensity >= 0.8 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(249, 115, 22, 0.6)';
        ctx.shadowBlur = 10;
        ctx.fillRect(startX, 0, barWidth, height);
        ctx.shadowBlur = 0;
      }

      // Draw event markers (pauses, rewinds)
      moment.events.forEach((event, idx) => {
        const markerX = startX + (barWidth * (idx / moment.events.length));
        ctx.fillStyle = event === 'rewind' ? '#8b5cf6' : '#3b82f6';
        ctx.beginPath();
        ctx.arc(markerX, height / 2, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    });

    // Draw current time indicator
    if (currentTime > 0 && currentTime <= duration) {
      const currentX = (currentTime / duration) * width;
      
      // Playhead line
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(currentX, 0);
      ctx.lineTo(currentX, height);
      ctx.stroke();

      // Playhead circle
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(currentX, height / 2, 5, 0, 2 * Math.PI);
      ctx.fill();
      
      // White border
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw border
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, width, height);
  }, [duration, hotMoments, currentTime]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onSeek) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clickTime = (x / rect.width) * duration;
    onSeek(clickTime);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-3">
      {/* Timeline Canvas */}
      <div className="relative">
        <canvas
          ref={canvasRef}
          className="w-full h-20 rounded-lg cursor-pointer hover:ring-2 hover:ring-blue-300 transition-all"
          onClick={handleClick}
        />
        
        {/* Time labels */}
        <div className="flex justify-between text-xs text-gray-500 mt-1 px-1">
          <span>0:00</span>
          <span>{formatTime(duration / 2)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-600 px-2">
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-red-500 to-orange-500"></div>
          <span>High Attention</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-orange-500 to-yellow-500"></div>
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-yellow-500 to-green-500"></div>
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1.5 ml-auto">
          <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          <span>Pause</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-purple-500"></div>
          <span>Rewind</span>
        </div>
      </div>

      {/* Hot Moments List */}
      {hotMoments.length > 0 && (
        <div className="text-sm text-gray-700 px-2">
          <strong>{hotMoments.length} hot moment{hotMoments.length !== 1 ? 's' : ''}</strong> detected where client showed high interest
        </div>
      )}
    </div>
  );
}
