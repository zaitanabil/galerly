import { useState, useEffect, useRef } from 'react';
import { sendViewerHeartbeat, notifyViewerDisconnect, getActiveViewers, ActiveViewersResponse } from '../services/viewerService';

/**
 * Hook to track current viewer presence (for gallery/portfolio pages)
 * Sends heartbeat every 30 seconds to maintain active status
 */
export function useViewerTracking(params: {
  gallery_id?: string;
  page_type: 'gallery' | 'portfolio' | 'client_gallery';
  gallery_name?: string;
  enabled?: boolean;
}) {
  const [viewerId, setViewerId] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  useEffect(() => {
    if (!params.enabled) return;
    
    let currentViewerId: string | null = null;
    
    // Send initial heartbeat
    const initHeartbeat = async () => {
      const response = await sendViewerHeartbeat({
        gallery_id: params.gallery_id,
        page_type: params.page_type,
        gallery_name: params.gallery_name
      });
      
      if (response.success && response.data?.viewer_id) {
        currentViewerId = response.data.viewer_id;
        setViewerId(currentViewerId);
      }
    };
    
    initHeartbeat();
    
    // Send heartbeat every 30 seconds
    intervalRef.current = setInterval(async () => {
      if (currentViewerId) {
        await sendViewerHeartbeat({
          viewer_id: currentViewerId,
          gallery_id: params.gallery_id,
          page_type: params.page_type,
          gallery_name: params.gallery_name
        });
      }
    }, 30000); // 30 seconds
    
    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (currentViewerId) {
        notifyViewerDisconnect(currentViewerId);
      }
    };
  }, [params.gallery_id, params.page_type, params.gallery_name, params.enabled]);
  
  return { viewerId };
}

/**
 * Hook to poll active viewers (for photographers on dashboard)
 * Fetches active viewers every 5 seconds
 */
export function useActiveViewers(enabled: boolean = true) {
  const [data, setData] = useState<ActiveViewersResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  useEffect(() => {
    if (!enabled) return;
    
    const fetchViewers = async () => {
      setLoading(true);
      const viewers = await getActiveViewers();
      setData(viewers);
      setLoading(false);
    };
    
    // Initial fetch
    fetchViewers();
    
    // Poll every 5 seconds
    intervalRef.current = setInterval(fetchViewers, 5000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled]);
  
  return { data, loading };
}
