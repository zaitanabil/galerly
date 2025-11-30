import { useState, useEffect, useRef, useCallback } from 'react';

export function useSlideshow(onNext: () => void, interval = 5000) {
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Memoize onNext to prevent effect re-triggering loop if onNext changes frequently (it shouldn't if stable)
  // However, we need to be careful. The onNext usually depends on state (currentIndex), so it changes.
  // We can use a ref for onNext to keep the effect stable.
  const onNextRef = useRef(onNext);
  useEffect(() => {
    onNextRef.current = onNext;
  }, [onNext]);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        onNextRef.current();
      }, interval);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, interval]);

  const togglePlay = useCallback(() => setIsPlaying(prev => !prev), []);
  const stop = useCallback(() => setIsPlaying(false), []);
  const start = useCallback(() => setIsPlaying(true), []);

  return { isPlaying, togglePlay, stop, start };
}

