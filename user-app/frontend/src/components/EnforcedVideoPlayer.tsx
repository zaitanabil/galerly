/**
 * Video Quality Enforcement Component
 * Enforces plan-based video quality limits (HD vs 4K)
 */
import React, { useEffect, useRef, useState } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { api } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { Lock, Info } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VideoJsPlayer = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VideoJsOptions = any;

interface EnforcedVideoPlayerProps {
  src: string;
  poster?: string;
  className?: string;
  photoId?: string;
  galleryId?: string;
  enableAnalytics?: boolean;
  maxQuality?: '720p' | '1080p' | '2160p'; // Plan-based limit
}

export const EnforcedVideoPlayer: React.FC<EnforcedVideoPlayerProps> = ({
  src,
  poster,
  className,
  photoId,
  galleryId,
  enableAnalytics = true,
  maxQuality
}) => {
  const { user } = useAuth();
  const videoRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<VideoJsPlayer>(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const analyticsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastReportedTimeRef = useRef(0);
  const [qualityWarning, setQualityWarning] = useState<string | null>(null);

  // Determine max quality based on user plan
  const getMaxQualityForPlan = () => {
    if (maxQuality) return maxQuality;
    
    if (!user) return '720p'; // Default for non-logged in
    
    const plan = user.plan || 'free';
    
    // Plan quality limits based on pricing page
    const qualityLimits: Record<string, '720p' | '1080p' | '2160p'> = {
      'free': '720p',      // 30 min HD
      'starter': '1080p',  // 1 Hour HD
      'plus': '1080p',     // 1 Hour HD
      'pro': '2160p',      // 4 Hours 4K
      'ultimate': '2160p'  // 10 Hours 4K
    };
    
    return qualityLimits[plan] || '720p';
  };

  const maxAllowedQuality = getMaxQualityForPlan();

  // Filter quality levels based on plan
  const filterQualityLevels = (sources: any[]) => {
    const qualityOrder: Record<string, number> = {
      '360p': 1,
      '480p': 2,
      '720p': 3,
      '1080p': 4,
      '2160p': 5
    };

    const maxLevel = qualityOrder[maxAllowedQuality];

    return sources.filter(source => {
      const label = source.label || '';
      const level = qualityOrder[label] || 1;
      return level <= maxLevel;
    });
  };

  // Track video analytics
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

  useEffect(() => {
    if (!playerRef.current && videoRef.current) {
      const videoElement = document.createElement('video-js');
      videoElement.classList.add('vjs-big-play-centered');
      videoRef.current.appendChild(videoElement);

      // Prepare sources with quality filtering
      let sources = [];
      
      // Check if src has multiple quality levels (HLS/DASH)
      if (src.includes('.m3u8') || src.includes('.mpd')) {
        // Adaptive streaming - video.js will handle quality selection
        sources = [{ src, type: src.includes('.m3u8') ? 'application/x-mpegURL' : 'application/dash+xml' }];
      } else {
        // Single source
        sources = [{ src, type: 'video/mp4' }];
      }

      const options: VideoJsOptions = {
        controls: true,
        responsive: true,
        fluid: true,
        poster: poster,
        sources: sources,
        playbackRates: [0.5, 1, 1.5, 2],
        controlBar: {
          qualitySelector: true,
          pictureInPictureToggle: true
        },
        html5: {
          vhs: {
            // Limit max resolution based on plan
            maxPlaylistResolution: maxAllowedQuality === '2160p' ? 3840 : 
                                   maxAllowedQuality === '1080p' ? 1920 : 1280
          }
        }
      };

      const player = playerRef.current = videojs(videoElement, options, () => {
        console.log('Video player ready with quality limit:', maxAllowedQuality);

        // Set up analytics
        if (enableAnalytics && photoId && galleryId) {
          player.on('play', () => {
            console.log('Video started playing');
          });

          // Track watch time every 10 seconds
          analyticsIntervalRef.current = setInterval(() => {
            if (!player.paused()) {
              const currentTime = player.currentTime();
              const duration = player.duration();
              const quality = player.currentResolution?.()?.label || 'auto';

              if (currentTime - lastReportedTimeRef.current >= 5) {
                trackVideoView(currentTime, duration, quality);
                lastReportedTimeRef.current = currentTime;
              }
            }
          }, 10000);

          player.on('pause', () => {
            const currentTime = player.currentTime();
            const duration = player.duration();
            const quality = player.currentResolution?.()?.label || 'auto';
            trackVideoView(currentTime, duration, quality);
          });

          player.on('ended', () => {
            const duration = player.duration();
            const quality = player.currentResolution?.()?.label || 'auto';
            trackVideoView(duration, duration, quality);
          });
        }

        // Monitor quality selection and enforce limits
        player.on('resolutionchange', () => {
          const currentResolution = player.currentResolution?.();
          if (currentResolution) {
            const currentQuality = currentResolution.label;
            const qualityOrder: Record<string, number> = {
              '360p': 1,
              '480p': 2,
              '720p': 3,
              '1080p': 4,
              '2160p': 5
            };

            const currentLevel = qualityOrder[currentQuality] || 1;
            const maxLevel = qualityOrder[maxAllowedQuality];

            if (currentLevel > maxLevel) {
              // User tried to select quality above their plan limit
              setQualityWarning(`Your plan supports up to ${maxAllowedQuality} quality. Upgrade for higher quality.`);
              
              // Force downgrade to max allowed quality
              setTimeout(() => {
                const qualities = player.qualityLevels?.();
                if (qualities) {
                  for (let i = 0; i < qualities.length; i++) {
                    const level = qualities[i];
                    const levelQuality = level.height + 'p';
                    if (levelQuality === maxAllowedQuality) {
                      level.enabled = true;
                    } else if (qualityOrder[levelQuality] > maxLevel) {
                      level.enabled = false;
                    }
                  }
                }
              }, 100);
            }
          }
        });
      });
    }

    return () => {
      if (analyticsIntervalRef.current) {
        clearInterval(analyticsIntervalRef.current);
      }

      const player = playerRef.current;
      if (player && enableAnalytics && photoId && galleryId) {
        try {
          const currentTime = player.currentTime();
          const duration = player.duration();
          const quality = player.currentResolution?.()?.label || 'auto';
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
  }, [src, poster, maxAllowedQuality, enableAnalytics, photoId, galleryId, sessionId]);

  // Hide warning after 5 seconds
  useEffect(() => {
    if (qualityWarning) {
      const timer = setTimeout(() => {
        setQualityWarning(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [qualityWarning]);

  return (
    <div className="relative">
      {/* Quality Limit Info Badge */}
      {user && (
        <div className="absolute top-4 right-4 z-10 px-3 py-1.5 bg-black/70 backdrop-blur-sm rounded-lg text-xs text-white font-medium flex items-center gap-2">
          {maxAllowedQuality === '2160p' ? (
            <>
              <span className="text-blue-400">4K</span>
              <span>Available</span>
            </>
          ) : (
            <>
              <Lock className="w-3 h-3" />
              <span>Max: {maxAllowedQuality.toUpperCase()}</span>
            </>
          )}
        </div>
      )}

      {/* Quality Warning Toast */}
      {qualityWarning && (
        <div className="absolute top-4 left-4 right-4 z-20 animate-in fade-in slide-in-from-top-2">
          <div className="bg-orange-500 text-white px-4 py-3 rounded-xl shadow-lg flex items-start gap-3">
            <Info className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium">{qualityWarning}</p>
              <a 
                href="/billing" 
                className="text-xs underline hover:no-underline mt-1 inline-block"
              >
                View Plans →
              </a>
            </div>
          </div>
        </div>
      )}

      <div data-vjs-player className={className}>
        <div ref={videoRef} className="w-full h-full" />
      </div>

      {/* Upgrade Prompt for lower plans */}
      {user && maxAllowedQuality !== '2160p' && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-xl">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Lock className="w-4 h-4 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900 mb-1">
                Upgrade for 4K Quality
              </p>
              <p className="text-xs text-blue-700">
                Pro and Ultimate plans support 4K video streaming for the best viewing experience.
              </p>
              <a 
                href="/billing" 
                className="inline-block mt-2 text-xs font-medium text-blue-600 hover:underline"
              >
                Upgrade Now →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnforcedVideoPlayer;
