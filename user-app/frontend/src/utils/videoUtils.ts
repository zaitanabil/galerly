/**
 * Video utilities for frontend
 * Extract duration and validate video files
 */

/**
 * Extract video duration from a File object
 * Returns duration in seconds
 */
export const getVideoDuration = (file: File): Promise<number> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';

    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src);
      resolve(video.duration);
    };

    video.onerror = () => {
      window.URL.revokeObjectURL(video.src);
      reject(new Error('Failed to load video metadata'));
    };

    video.src = URL.createObjectURL(file);
  });
};

/**
 * Check if file is a video
 */
export const isVideoFile = (file: File): boolean => {
  return file.type.startsWith('video/');
};

/**
 * Format duration in seconds to readable format
 */
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

/**
 * Convert minutes to seconds
 */
export const minutesToSeconds = (minutes: number): number => {
  return minutes * 60;
};

/**
 * Convert seconds to minutes
 */
export const secondsToMinutes = (seconds: number): number => {
  return seconds / 60;
};

/**
 * Check if video duration exceeds plan limit
 * Returns { allowed: boolean, message?: string }
 */
export const checkVideoDurationLimit = (
  durationSeconds: number,
  planLimitMinutes: number
): { allowed: boolean; message?: string } => {
  if (planLimitMinutes === -1) {
    // Unlimited
    return { allowed: true };
  }

  const planLimitSeconds = minutesToSeconds(planLimitMinutes);

  if (durationSeconds > planLimitSeconds) {
    return {
      allowed: false,
      message: `Video duration (${formatDuration(durationSeconds)}) exceeds your plan limit of ${planLimitMinutes} minutes. Please upgrade or use a shorter video.`
    };
  }

  return { allowed: true };
};

/**
 * Get video quality limits based on plan
 */
export const getVideoQualityForPlan = (plan: string): '720p' | '1080p' | '2160p' => {
  const qualityLimits: Record<string, '720p' | '1080p' | '2160p'> = {
    'free': '720p',      // 30 min HD
    'starter': '1080p',  // 1 Hour HD
    'plus': '1080p',     // 1 Hour HD
    'pro': '2160p',      // 4 Hours 4K
    'ultimate': '2160p'  // 10 Hours 4K
  };

  return qualityLimits[plan] || '720p';
};

/**
 * Get video duration limit for plan (in minutes)
 */
export const getVideoDurationLimitForPlan = (plan: string): number => {
  const durationLimits: Record<string, number> = {
    'free': 30,        // 30 minutes HD
    'starter': 60,     // 1 Hour HD
    'plus': 60,        // 1 Hour HD
    'pro': 240,        // 4 Hours 4K
    'ultimate': 600    // 10 Hours 4K
  };

  return durationLimits[plan] || 30;
};
