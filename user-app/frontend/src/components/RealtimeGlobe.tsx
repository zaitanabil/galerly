import { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import { ActiveViewer } from '../services/viewerService';

interface RealtimeGlobeProps {
  viewers: ActiveViewer[];
  totalActive: number;
  byCountry: Record<string, number>; // Kept for future use
}

interface GlobePoint {
  lat: number;
  lng: number;
  size: number;
  color: string;
  label: string;
  viewers: ActiveViewer[];
}

export default function RealtimeGlobe({ viewers, totalActive }: RealtimeGlobeProps) {
  const globeEl = useRef<any>();
  
  // Cluster nearby viewers (within 100km radius)
  const clusteredPoints = useMemo(() => {
    const clusters: Map<string, GlobePoint> = new Map();
    const CLUSTER_RADIUS = 1; // degrees (roughly 100km)
    
    viewers.forEach(viewer => {
      const lat = viewer.location.latitude;
      const lng = viewer.location.longitude;
      
      // Find existing cluster nearby
      let foundCluster = false;
      for (const cluster of clusters.values()) {
        const distance = Math.sqrt(
          Math.pow(cluster.lat - lat, 2) + Math.pow(cluster.lng - lng, 2)
        );
        
        if (distance < CLUSTER_RADIUS) {
          // Add to existing cluster
          cluster.viewers.push(viewer);
          cluster.size = Math.min(1.2, 0.4 + cluster.viewers.length * 0.15);
          cluster.label = `${cluster.viewers.length} viewers`;
          foundCluster = true;
          break;
        }
      }
      
      if (!foundCluster) {
        // Create new cluster
        const key = `${lat.toFixed(1)},${lng.toFixed(1)}`;
        clusters.set(key, {
          lat,
          lng,
          size: 0.4,
          color: '#00D4FF',
          label: viewer.location.city || viewer.location.country,
          viewers: [viewer]
        });
      }
    });
    
    return Array.from(clusters.values());
  }, [viewers]);
  
  // Setup globe with premium smooth interactions
  useEffect(() => {
    if (globeEl.current) {
      const controls = globeEl.current.controls();
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.4;
      controls.enableZoom = true;
      controls.minDistance = 180;
      controls.maxDistance = 500;
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.rotateSpeed = 0.5;
      
      // Initial camera position
      globeEl.current.pointOfView({ altitude: 2.5 }, 0);
    }
  }, []);
  
  // Smooth camera transitions when new viewers appear
  useEffect(() => {
    if (globeEl.current && clusteredPoints.length > 0) {
      // Smoothly focus on newest viewer location
      const point = clusteredPoints[clusteredPoints.length - 1];
      globeEl.current.pointOfView(
        { lat: point.lat, lng: point.lng, altitude: 2.5 },
        1500 // 1.5 second smooth transition
      );
    }
  }, [clusteredPoints.length]);
  
  // Premium tooltip with city/region (never IPs)
  const pointLabel = (point: any) => {
    if (!point || !point.viewers) return '';
    
    const viewerList = point.viewers.map((v: ActiveViewer) => 
      `${v.location.city || 'Unknown'}, ${v.location.region || v.location.country}`
    ).join('<br/>');
    
    return `
      <div style="
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.98) 0%, rgba(20, 20, 25, 0.98) 100%);
        backdrop-filter: blur(40px);
        -webkit-backdrop-filter: blur(40px);
        color: white;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: -0.02em;
        box-shadow: 
          0 8px 32px rgba(0, 212, 255, 0.2),
          0 4px 16px rgba(0, 0, 0, 0.4),
          inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.2);
      ">
        <div style="
          font-size: 15px;
          font-weight: 600;
          margin-bottom: 6px;
          color: #00D4FF;
          text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        ">
          ${point.viewers.length} ${point.viewers.length === 1 ? 'viewer' : 'viewers'}
        </div>
        <div style="font-size: 11px; opacity: 0.7; font-weight: 400; line-height: 1.4;">
          ${viewerList}
        </div>
      </div>
    `;
  };
  
  return (
    <div className="relative rounded-[32px] overflow-hidden" style={{
      background: 'linear-gradient(135deg, #000000 0%, #0a0a0f 50%, #000000 100%)',
      boxShadow: `
        0 20px 60px rgba(0, 0, 0, 0.6),
        0 8px 24px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        inset 0 -1px 0 rgba(0, 0, 0, 0.5)
      `
    }}>
      {/* Premium glass overlay border */}
      <div className="absolute inset-0 rounded-[32px] pointer-events-none" style={{
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.1)'
      }} />
      
      {/* Ambient light effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] pointer-events-none" style={{
        background: 'radial-gradient(ellipse at center, rgba(0, 212, 255, 0.15) 0%, transparent 70%)',
        filter: 'blur(60px)'
      }} />
      
      {/* Premium Stats Display - with pointer-events-none to allow interaction through it */}
      <div className="absolute top-8 left-8 z-10 pointer-events-none">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-white/40 mb-2">
          Live Audience
        </div>
        <div className="flex items-baseline gap-2">
          <div className="text-6xl font-extralight text-white tracking-tighter" style={{
            textShadow: '0 0 40px rgba(0, 212, 255, 0.4)'
          }}>
            {totalActive}
          </div>
          <div className="text-sm font-medium text-white/50">
            {totalActive === 1 ? 'viewer' : 'viewers'}
          </div>
        </div>
      </div>
      
      {/* Globe Container - Responsive and Centered */}
      <div className="w-full h-[600px] flex items-center justify-center">
        <Globe
          ref={globeEl}
          width={1200}
          height={600}
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
          backgroundColor="rgba(0,0,0,0)"
          
          // Premium glowing markers with smooth transitions
          pointsData={clusteredPoints}
          pointLat="lat"
          pointLng="lng"
          pointColor={() => '#00D4FF'}
          pointAltitude={0.02}
          pointRadius="size"
          pointLabel={pointLabel}
          pointsTransitionDuration={1500} // Smooth 1.5s transitions
          
          // Premium atmosphere with cyan glow
          atmosphereColor="#00D4FF"
          atmosphereAltitude={0.2}
          
          // Smooth interactions
          enablePointerInteraction={true}
          
          // Enhanced lighting
          showAtmosphere={true}
        />
      </div>
      
      {/* Premium Empty State - with pointer-events-none to allow interaction */}
      {totalActive === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center px-8 py-6 rounded-2xl backdrop-blur-sm" style={{
            background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(20, 20, 25, 0.8) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)'
          }}>
            <div className="text-white/70 text-[15px] font-medium mb-1">
              No active viewers
            </div>
            <div className="text-white/40 text-[13px]">
              Share your galleries to see your audience
            </div>
          </div>
        </div>
      )}
      
      {/* Premium Interaction Hint - with pointer-events-none */}
      <div className="absolute bottom-6 right-6 z-10 pointer-events-none">
        <div className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
          Drag • Zoom • Explore
        </div>
      </div>
      
      {/* Bottom ambient glow */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[200px] pointer-events-none" style={{
        background: 'radial-gradient(ellipse at center, rgba(0, 212, 255, 0.1) 0%, transparent 70%)',
        filter: 'blur(50px)'
      }} />
    </div>
  );
}
