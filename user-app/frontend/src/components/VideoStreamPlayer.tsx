import { useRef, useEffect, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, Settings } from 'lucide-react';

interface VideoStreamPlayerProps {
  src: string;  // HLS playlist URL or MP4 URL
  poster?: string;  // Thumbnail image
  title?: string;
  autoPlay?: boolean;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  onEnded?: () => void;
}

export default function VideoStreamPlayer({
  src,
  poster,
  title,
  autoPlay = false,
  onTimeUpdate,
  onEnded
}: VideoStreamPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [quality, setQuality] = useState<string>('auto');
  const [showQualityMenu, setShowQualityMenu] = useState(false);
  const [availableQualities, setAvailableQualities] = useState<string[]>(['auto']);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Check if HLS.js is supported
    if (src.endsWith('.m3u8')) {
      loadHLS(video, src);
    } else {
      // Standard MP4 playback
      video.src = src;
    }

    // Event listeners
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleTimeUpdate = () => {
      const current = video.currentTime;
      const total = video.duration;
      setCurrentTime(current);
      setDuration(total);
      if (onTimeUpdate) onTimeUpdate(current, total);
    };
    const handleEnded = () => {
      setIsPlaying(false);
      if (onEnded) onEnded();
    };
    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [src, onTimeUpdate, onEnded]);

  const loadHLS = async (video: HTMLVideoElement, url: string) => {
    // Dynamic import of HLS.js for adaptive streaming
    try {
      // Check if HLS.js is available
      if ('Hls' in window) {
        const Hls = (window as any).Hls;
        
        if (Hls.isSupported()) {
          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: false,
            backBufferLength: 90
          });

          hls.loadSource(url);
          hls.attachMedia(video);

          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('✅ HLS manifest loaded');
            // Extract available quality levels
            const levels = hls.levels.map((level: any, index: number) => {
              const height = level.height;
              return `${height}p`;
            });
            setAvailableQualities(['auto', ...levels]);
          });

          hls.on(Hls.Events.ERROR, (_event: any, data: any) => {
            if (data.fatal) {
              console.error('❌ HLS error:', data);
              // Fallback to native playback
              video.src = url.replace('master.m3u8', '_1080p.mp4');
            }
          });

          // Store hls instance for quality switching
          (video as any).hls = hls;
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // Native HLS support (Safari)
          video.src = url;
        }
      } else {
        // Fallback to MP4
        console.warn('HLS.js not available, using fallback');
        video.src = url.replace('master.m3u8', '_1080p.mp4');
      }
    } catch (error) {
      console.error('Error loading HLS:', error);
      video.src = url;
    }
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = !video.muted;
    setIsMuted(video.muted);
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen();
    }
  };

  const changeQuality = (qualityLevel: string) => {
    const video = videoRef.current;
    if (!video || !(video as any).hls) return;

    const hls = (video as any).hls;
    
    if (qualityLevel === 'auto') {
      hls.currentLevel = -1;  // Auto
    } else {
      const levelIndex = hls.levels.findIndex((level: any) => 
        `${level.height}p` === qualityLevel
      );
      if (levelIndex !== -1) {
        hls.currentLevel = levelIndex;
      }
    }

    setQuality(qualityLevel);
    setShowQualityMenu(false);
  };

  const seek = (e: React.MouseEvent<HTMLDivElement>) => {
    const video = videoRef.current;
    if (!video) return;

    const bounds = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - bounds.left) / bounds.width;
    video.currentTime = percent * video.duration;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div 
      className="relative bg-black rounded-2xl overflow-hidden group"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(isPlaying ? false : true)}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        className="w-full aspect-video object-contain"
        poster={poster}
        autoPlay={autoPlay}
        playsInline
      />

      {/* Title Overlay */}
      {title && (
        <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
          <h3 className="text-white font-medium">{title}</h3>
        </div>
      )}

      {/* Controls Overlay */}
      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300 ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* Progress Bar */}
        <div 
          className="w-full h-1 bg-white/30 rounded-full mb-3 cursor-pointer hover:h-2 transition-all"
          onClick={seek}
        >
          <div 
            className="h-full bg-[#0066CC] rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between gap-4">
          {/* Left Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="text-white hover:text-[#0066CC] transition-colors"
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
            </button>

            <button
              onClick={toggleMute}
              className="text-white hover:text-[#0066CC] transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>

            <span className="text-white text-sm font-medium">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3">
            {/* Quality Selector */}
            {availableQualities.length > 1 && (
              <div className="relative">
                <button
                  onClick={() => setShowQualityMenu(!showQualityMenu)}
                  className="text-white hover:text-[#0066CC] transition-colors flex items-center gap-1"
                  aria-label="Quality"
                >
                  <Settings className="w-5 h-5" />
                  <span className="text-xs">{quality}</span>
                </button>

                {showQualityMenu && (
                  <div className="absolute bottom-full right-0 mb-2 bg-black/90 rounded-lg overflow-hidden">
                    {availableQualities.map((q) => (
                      <button
                        key={q}
                        onClick={() => changeQuality(q)}
                        className={`block w-full px-4 py-2 text-left text-sm hover:bg-white/10 transition-colors ${
                          quality === q ? 'text-[#0066CC]' : 'text-white'
                        }`}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              onClick={toggleFullscreen}
              className="text-white hover:text-[#0066CC] transition-colors"
              aria-label="Fullscreen"
            >
              <Maximize className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Play Button Overlay (when paused) */}
      {!isPlaying && (
        <button
          onClick={togglePlay}
          className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/30 transition-colors"
          aria-label="Play"
        >
          <div className="w-20 h-20 rounded-full bg-white/90 flex items-center justify-center hover:scale-110 transition-transform">
            <Play className="w-10 h-10 text-[#1D1D1F] ml-1" />
          </div>
        </button>
      )}
    </div>
  );
}
