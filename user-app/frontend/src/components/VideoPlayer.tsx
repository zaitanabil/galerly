import React, { useEffect, useRef, useState } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { api } from '../utils/api';
import { Settings } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VideoJsPlayer = any; 
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VideoJsOptions = any;

interface VideoPlayerProps {
  options: VideoJsOptions;
  onReady?: (player: VideoJsPlayer) => void;
  className?: string;
  photoId?: string;
  galleryId?: string;
  enableAnalytics?: boolean;
  enableQualitySelector?: boolean;
}

interface QualityLevel {
  label: string;
  height: number;
  bitrate?: number;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  options, 
  onReady, 
  className,
  photoId,
  galleryId,
  enableAnalytics = true,
  enableQualitySelector = true
}) => {
  const videoRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<VideoJsPlayer>(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [currentQuality, setCurrentQuality] = useState<string>('auto');
  const [availableQualities, setAvailableQualities] = useState<QualityLevel[]>([]);
  const [showQualityMenu, setShowQualityMenu] = useState(false);
  const analyticsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastReportedTimeRef = useRef(0);

  // Analytics tracking
  const trackVideoView = async (durationWatched: number, totalDuration: number, quality: string) => {
    if (!enableAnalytics || !photoId || !galleryId) return;

    try {
      await api.post('/videos/track-view', {
        photo_id: photoId,
        gallery_id: galleryId,
        duration_watched: Math.round(durationWatched),
        total_duration: Math.round(totalDuration),
        quality: quality,
        session_id: sessionId
      });
    } catch (error) {
      console.error('Failed to track video view:', error);
    }
  };

  // Get current quality label
  const getCurrentQuality = (player: VideoJsPlayer): string => {
    try {
      // Try to get from quality levels plugin
      const qualityLevels = player.qualityLevels?.();
      if (qualityLevels && qualityLevels.selectedIndex >= 0) {
        const selectedLevel = qualityLevels[qualityLevels.selectedIndex];
        if (selectedLevel && selectedLevel.height) {
          if (selectedLevel.height >= 2160) return '4K';
          if (selectedLevel.height >= 1080) return '1080p';
          if (selectedLevel.height >= 720) return '720p';
          return `${selectedLevel.height}p`;
        }
      }
      
      // Fallback: try to detect from video element
      const videoElement = player.el()?.querySelector('video');
      if (videoElement) {
        const height = videoElement.videoHeight;
        if (height >= 2160) return '4K';
        if (height >= 1080) return '1080p';
        if (height >= 720) return '720p';
        if (height > 0) return `${height}p`;
      }
    } catch (error) {
      console.error('Error getting current quality:', error);
    }
    return 'auto';
  };

  // Detect available quality levels
  const detectQualityLevels = (player: VideoJsPlayer) => {
    try {
      const qualityLevels = player.qualityLevels?.();
      if (qualityLevels && qualityLevels.length > 0) {
        const qualities: QualityLevel[] = [];
        
        for (let i = 0; i < qualityLevels.length; i++) {
          const level = qualityLevels[i];
          if (level && level.height) {
            let label = 'Auto';
            if (level.height >= 2160) label = '4K (2160p)';
            else if (level.height >= 1080) label = '1080p (Full HD)';
            else if (level.height >= 720) label = '720p (HD)';
            else label = `${level.height}p`;
            
            qualities.push({
              label,
              height: level.height,
              bitrate: level.bitrate
            });
          }
        }
        
        // Sort by height (highest first)
        qualities.sort((a, b) => b.height - a.height);
        
        // Add auto option
        qualities.unshift({ label: 'Auto (Recommended)', height: -1 });
        
        setAvailableQualities(qualities);
      } else {
        // Fallback: detect from video element
        const videoElement = player.el()?.querySelector('video');
        if (videoElement && videoElement.videoHeight > 0) {
          const height = videoElement.videoHeight;
          let label = 'Auto';
          if (height >= 2160) label = '4K (2160p)';
          else if (height >= 1080) label = '1080p (Full HD)';
          else if (height >= 720) label = '720p (HD)';
          else label = `${height}p`;
          
          setAvailableQualities([
            { label: 'Auto (Recommended)', height: -1 },
            { label, height }
          ]);
        }
      }
    } catch (error) {
      console.error('Error detecting quality levels:', error);
    }
  };

  // Change quality level
  const changeQuality = (height: number) => {
    const player = playerRef.current;
    if (!player) return;

    try {
      const qualityLevels = player.qualityLevels?.();
      if (qualityLevels) {
        // Disable all levels first
        for (let i = 0; i < qualityLevels.length; i++) {
          qualityLevels[i].enabled = false;
        }

        if (height === -1) {
          // Auto mode: enable all
          for (let i = 0; i < qualityLevels.length; i++) {
            qualityLevels[i].enabled = true;
          }
          setCurrentQuality('auto');
        } else {
          // Enable specific quality
          for (let i = 0; i < qualityLevels.length; i++) {
            if (qualityLevels[i].height === height) {
              qualityLevels[i].enabled = true;
              const label = getCurrentQuality(player);
              setCurrentQuality(label);
              break;
            }
          }
        }
        
        // Save preference to localStorage
        try {
          localStorage.setItem('video_quality_preference', height.toString());
        } catch (e) {
          // Ignore localStorage errors
        }
      }
    } catch (error) {
      console.error('Error changing quality:', error);
    }

    setShowQualityMenu(false);
  };

  useEffect(() => {
    // Make sure Video.js player is only initialized once
    if (!playerRef.current) {
      const videoElement = document.createElement("video-js");

      videoElement.classList.add('vjs-big-play-centered');
      videoRef.current?.appendChild(videoElement);

      const player = playerRef.current = videojs(videoElement, options, () => {
        videojs.log('player is ready');
        
        // Detect available quality levels
        if (enableQualitySelector) {
          // Wait a bit for quality levels to be detected
          setTimeout(() => {
            detectQualityLevels(player);
            const quality = getCurrentQuality(player);
            setCurrentQuality(quality);
            
            // Load saved quality preference
            try {
              const savedQuality = localStorage.getItem('video_quality_preference');
              if (savedQuality) {
                const height = parseInt(savedQuality, 10);
                changeQuality(height);
              }
            } catch (e) {
              // Ignore localStorage errors
            }
          }, 1000);
        }
        
        // Set up analytics tracking
        if (enableAnalytics && photoId && galleryId) {
          // Track on play
          player.on('play', () => {
            console.log('Video started playing');
          });

          // Track watch time every 10 seconds
          analyticsIntervalRef.current = setInterval(() => {
            if (!player.paused()) {
              const currentTime = player.currentTime();
              const duration = player.duration();
              const quality = getCurrentQuality(player);
              
              // Only report if watched at least 5 more seconds
              if (currentTime - lastReportedTimeRef.current >= 5) {
                trackVideoView(currentTime, duration, quality);
                lastReportedTimeRef.current = currentTime;
              }
            }
          }, 10000);

          // Track on pause/end
          player.on('pause', () => {
            const currentTime = player.currentTime();
            const duration = player.duration();
            const quality = getCurrentQuality(player);
            trackVideoView(currentTime, duration, quality);
          });

          player.on('ended', () => {
            const duration = player.duration();
            const quality = getCurrentQuality(player);
            trackVideoView(duration, duration, quality);
          });
        }

        if (onReady) {
          onReady(player);
        }
      });

    } else {
      const player = playerRef.current;
      player.autoplay(options.autoplay);
      player.src(options.sources);
    }
  }, [options, onReady, enableAnalytics, enableQualitySelector, photoId, galleryId, sessionId]);

  // Dispose the Video.js player when the functional component unmounts
  useEffect(() => {
    const player = playerRef.current;

    return () => {
      // Cleanup analytics interval
      if (analyticsIntervalRef.current) {
        clearInterval(analyticsIntervalRef.current);
      }

      // Final analytics report before unmount
      if (player && !player.isDisposed() && enableAnalytics && photoId && galleryId) {
        try {
          const currentTime = player.currentTime();
          const duration = player.duration();
          const quality = getCurrentQuality(player);
          if (currentTime > 0) {
            trackVideoView(currentTime, duration, quality);
          }
        } catch (error) {
          console.error('Error tracking final video view:', error);
        }
      }

      if (player && !player.isDisposed()) {
        player.dispose();
        playerRef.current = null;
      }
    };
  }, [playerRef, enableAnalytics, photoId, galleryId]);

  return (
    <div data-vjs-player className={`${className} relative`}>
      <div ref={videoRef} className="w-full h-full" />
      
      {/* Quality selector button and menu */}
      {enableQualitySelector && availableQualities.length > 1 && (
        <div className="absolute bottom-4 right-4 z-20">
          {/* Quality menu */}
          {showQualityMenu && (
            <div className="absolute bottom-full right-0 mb-2 bg-gray-900/95 backdrop-blur-md rounded-lg shadow-xl border border-gray-700 overflow-hidden min-w-[200px]">
              <div className="px-4 py-2 border-b border-gray-700 text-white text-sm font-semibold">
                Video Quality
              </div>
              <div className="py-1">
                {availableQualities.map((quality, index) => (
                  <button
                    key={index}
                    onClick={() => changeQuality(quality.height)}
                    className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center justify-between ${
                      currentQuality === quality.label.split(' ')[0] || (currentQuality === 'auto' && quality.height === -1)
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-200 hover:bg-gray-800'
                    }`}
                  >
                    <span>{quality.label}</span>
                    {(currentQuality === quality.label.split(' ')[0] || (currentQuality === 'auto' && quality.height === -1)) && (
                      <svg className="w-4 h-4 ml-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
              <div className="px-4 py-2 border-t border-gray-700 text-xs text-gray-400">
                Higher quality uses more bandwidth
              </div>
            </div>
          )}
          
          {/* Settings button */}
          <button
            onClick={() => setShowQualityMenu(!showQualityMenu)}
            className="flex items-center gap-2 bg-gray-900/80 hover:bg-gray-800/90 text-white px-3 py-2 rounded-lg text-sm font-medium backdrop-blur-sm transition-all shadow-lg hover:shadow-xl"
            title="Video quality settings"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">{currentQuality}</span>
          </button>
        </div>
      )}
      
      {/* Quality indicator overlay - displays current resolution */}
      {enableQualitySelector && currentQuality && currentQuality !== 'auto' && !showQualityMenu && (
        <div className="absolute top-4 right-4 bg-black/70 text-white px-3 py-1 rounded-lg text-xs font-semibold backdrop-blur-sm z-10 pointer-events-none">
          {currentQuality}
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;
