import { useEffect, useRef } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import analyticsService from '../services/analyticsService';

export function useVisitorTracking() {
  const location = useLocation();
  const { galleryId } = useParams<{ galleryId: string }>();
  
  // Use ref to track previous path to avoid double counting on strict mode
  const prevPathRef = useRef<string | null>(null);
  const sessionStartedRef = useRef(false);

  // Initialize session on mount
  useEffect(() => {
    if (!sessionStartedRef.current) {
      // Create session or track visit start
      analyticsService.trackVisit(galleryId || 'general', {
        path: location.pathname,
        referrer: document.referrer,
        screen_width: window.screen.width,
        screen_height: window.screen.height,
      }).catch(err => console.error('Tracking error:', err));
      
      sessionStartedRef.current = true;
    }

    // Handle session end on unmount/page hide
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Ideally we'd have the session ID from the trackVisit response
        // But for now we just fire the end event
        // analyticsService.trackSessionEnd(sessionId);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Track page views on route change
  useEffect(() => {
    if (prevPathRef.current === location.pathname) return;
    prevPathRef.current = location.pathname;

    // Determine context (gallery or general)
    // Extract gallery ID from path if possible
    const pathParts = location.pathname.split('/');
    let currentGalleryId = galleryId || 'general';
    
    if (location.pathname.includes('/client-gallery/')) {
       const idIndex = pathParts.indexOf('client-gallery') + 1;
       if (pathParts[idIndex]) currentGalleryId = pathParts[idIndex];
    } else if (location.pathname.includes('/gallery/')) {
        const idIndex = pathParts.indexOf('gallery') + 1;
        if (pathParts[idIndex]) currentGalleryId = pathParts[idIndex];
    }

    // Track event: page_view
    analyticsService.trackEvent(currentGalleryId, 'page_view', {
      path: location.pathname,
      title: document.title,
    }).catch(err => console.error('Page view tracking error:', err));

  }, [location.pathname, galleryId]);
}

