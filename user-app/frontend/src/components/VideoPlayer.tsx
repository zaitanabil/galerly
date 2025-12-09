import React, { useEffect, useRef, useState } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { api } from '../utils/api';

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

  useEffect(() => {
    // Make sure Video.js player is only initialized once
    if (!playerRef.current) {
      const videoElement = document.createElement("video-js");

      videoElement.classList.add('vjs-big-play-centered');
      videoRef.current?.appendChild(videoElement);

      const player = playerRef.current = videojs(videoElement, options, () => {
        videojs.log('player is ready');
        
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
      
      {/* Quality indicator overlay - displays current resolution */}
      {enableQualitySelector && currentQuality && currentQuality !== 'auto' && (
        <div className="absolute top-4 right-4 bg-black/70 text-white px-3 py-1 rounded-lg text-xs font-semibold backdrop-blur-sm z-10 pointer-events-none">
          {currentQuality}
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;
