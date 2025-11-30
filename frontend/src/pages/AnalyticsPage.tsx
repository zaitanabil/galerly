// Analytics page - Full detailed reports
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  useOverallAnalytics, 
  useGalleryAnalytics,
  useBulkDownloads, 
  useGalleries,
  useVisitorAnalytics
} from '../hooks/useApi';
import { 
  Calendar, Download, Eye, Users, 
  Globe, Smartphone, Filter, ChevronDown, Image as ImageIcon,
  Clock, Settings, LogOut, Lock
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, PieChart, Pie, Cell
} from 'recharts';

interface DailyStat {
  date: string;
  views: number;
  downloads: number;
}

interface TopPhoto {
  name: string;
  thumbnail_url?: string;
  views: number;
  avg_time_seconds: number;
}

interface BulkEvent {
  timestamp: string;
  gallery_name: string;
  metadata?: {
    downloader_name?: string;
    photo_count?: number;
    ip?: string;
    is_owner_download?: boolean;
  };
}

interface GalleryStat {
  gallery_name: string;
  views: number;
  downloads: number;
  photo_views: number;
}

export default function AnalyticsPage() {
  const { logout, user } = useAuth();
  const [dateRange, setDateRange] = useState('30'); // '7', '30', '90', '365'
  const [selectedGalleryId, setSelectedGalleryId] = useState<string>('all');
  
  // Plan check
  const hasAdvancedAnalytics = ['plus', 'pro', 'ultimate'].includes(user?.plan || '');
  
  // Calculate dates based on range
  const endDate = new Date().toISOString();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - parseInt(dateRange));
  const startDateStr = startDate.toISOString();
  
  // Data fetching hooks
  const { data: galleriesData } = useGalleries();
  const galleries = galleriesData?.galleries || [];

  // Conditional analytics fetching based on gallery selection
  const { data: overallData, loading: overallLoading } = useOverallAnalytics(
    startDateStr, endDate
  );
  
  const { data: gallerySpecificData, loading: galleryLoading } = useGalleryAnalytics(
    selectedGalleryId === 'all' ? undefined : selectedGalleryId, 
    startDateStr, 
    endDate
  );

  const { data: bulkDownloadsData } = useBulkDownloads(
    selectedGalleryId === 'all' ? undefined : selectedGalleryId
  );

  const { data: visitorData } = useVisitorAnalytics(
    selectedGalleryId === 'all' ? undefined : selectedGalleryId
  );

  const loading = selectedGalleryId === 'all' ? overallLoading : galleryLoading;
  
  // Determine active dataset
  const activeData = selectedGalleryId === 'all' ? overallData : gallerySpecificData;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const metrics = (activeData?.metrics || activeData || {}) as any; // Handle different response shapes if any

  // Process data for charts
  const dailyStats = activeData?.daily_stats || activeData?.daily_stats_list || [];
  
  const chartData = (Array.isArray(dailyStats) ? dailyStats : []).map((d: DailyStat | { date: string; views: number; downloads: number }) => {
    // Handle both object key format and list format
    const date = d.date;
    return {
      name: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      date: date,
      views: d.views || 0,
      downloads: d.downloads || 0
    };
  });

  const galleryStats = overallData?.gallery_stats || [];
  const topGalleries = [...galleryStats].sort((a: GalleryStat, b: GalleryStat) => b.views - a.views).slice(0, 5);
  
  // NEW: Get top photos
  const topPhotos = activeData?.top_photos || []; 

  const bulkDownloadsAny = bulkDownloadsData as unknown as { events: BulkEvent[] };
  const bulkEvents = bulkDownloadsAny?.events || [];

  // Visitor Analytics Processing
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const visitorSummary = (visitorData as any)?.summary || {};
  
  // Device Breakdown (Real Data)
  const deviceBreakdown = visitorSummary.device_breakdown || {};
  const deviceData = Object.entries(deviceBreakdown).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
    color: name === 'mobile' ? '#0066CC' : name === 'desktop' ? '#F97316' : '#8B5CF6'
  })).sort((a, b) => b.value - a.value);

  // Fallback if no data
  if (deviceData.length === 0) {
    deviceData.push({ name: 'No Data', value: 1, color: '#E5E5E5' });
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-[#1D1D1F]/60 text-sm font-medium animate-pulse">Generating Report...</p>
        </div>
      </div>
    );
  }

  // Advanced feature overlay component
  const UpgradeOverlay = () => (
    <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-10 flex items-center justify-center rounded-[32px] border border-gray-100">
      <div className="text-center p-6 bg-white rounded-2xl shadow-xl border border-gray-100 max-w-sm mx-4">
        <div className="w-10 h-10 bg-black text-white rounded-full flex items-center justify-center mx-auto mb-3">
          <Lock className="w-5 h-5" />
        </div>
        <h3 className="text-lg font-bold text-[#1D1D1F] mb-1">Advanced Analytics</h3>
        <p className="text-sm text-[#1D1D1F]/60 mb-4">
          Upgrade to Plus or Pro to see detailed charts, device breakdowns, and top photos.
        </p>
        <Link 
          to="/billing"
          className="inline-flex items-center justify-center px-4 py-2 bg-[#0066CC] text-white text-sm font-medium rounded-full hover:bg-[#0052A3] transition-colors"
        >
          View Plans
        </Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Dashboard</Link>
              <Link to="/galleries" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Galleries</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]">Analytics</Link>
              <Link to="/billing" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Billing</Link>
            </nav>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Gallery Filter */}
            <div className="relative group hidden md:block">
              <div className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-[#1D1D1F] hover:bg-gray-50 transition-colors cursor-pointer">
                <Filter className="w-4 h-4 text-[#1D1D1F]/60" />
                <select 
                  value={selectedGalleryId}
                  onChange={(e) => setSelectedGalleryId(e.target.value)}
                  className="bg-transparent border-none focus:ring-0 cursor-pointer text-sm font-medium text-[#1D1D1F] pr-8 appearance-none outline-none"
                  style={{ backgroundImage: 'none' }}
                >
                  <option value="all">All Galleries</option>
                  {galleries.map((g) => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-[#1D1D1F]/40 absolute right-4 pointer-events-none" />
              </div>
            </div>

            {/* Date Range Filter */}
            <div className="relative group">
              <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-[#1D1D1F] hover:bg-gray-50 transition-colors">
                <Calendar className="w-4 h-4 text-[#1D1D1F]/60" />
                <span>Last {dateRange} Days</span>
                <ChevronDown className="w-3.5 h-3.5 text-[#1D1D1F]/40" />
              </button>
              
              <div className="absolute right-0 top-full mt-2 w-40 bg-white rounded-2xl border border-gray-200 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right z-50">
                <div className="p-1.5">
                  {[
                    { label: 'Last 7 Days', value: '7' },
                    { label: 'Last 30 Days', value: '30' },
                    { label: 'Last 90 Days', value: '90' },
                    { label: 'Last Year', value: '365' },
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setDateRange(option.value)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-sm transition-colors ${
                        dateRange === option.value 
                          ? 'bg-[#F5F5F7] text-[#1D1D1F] font-medium' 
                          : 'text-[#1D1D1F]/60 hover:bg-gray-50 hover:text-[#1D1D1F]'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            <button className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-gray-100 rounded-full transition-colors" title="Export Report">
              <Download className="w-5 h-5" />
            </button>
            <div className="h-6 w-px bg-gray-200 mx-1"></div>
            <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full transition-all">
              <Settings className="w-5 h-5" />
            </Link>
            <button onClick={logout} className="p-2 text-[#1D1D1F]/60 hover:text-red-600 hover:bg-red-50 rounded-full transition-all">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        
        {/* Mobile Filter (Visible only on small screens) */}
        <div className="md:hidden mb-6">
          <select 
            value={selectedGalleryId}
            onChange={(e) => setSelectedGalleryId(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-[#1D1D1F] focus:ring-2 focus:ring-[#0066CC]/20"
          >
            <option value="all">All Galleries</option>
            {galleries.map((g) => (
              <option key={g.id} value={g.id}>{g.name}</option>
            ))}
          </select>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { 
              label: 'Total Views', 
              value: (metrics.total_views || metrics.views || 0).toLocaleString(), 
              icon: Eye,
              color: 'text-blue-600',
              bg: 'bg-blue-50'
            },
            { 
              label: 'Downloads', 
              value: (metrics.total_downloads || metrics.downloads || 0).toLocaleString(), 
              icon: Download,
              color: 'text-orange-600',
              bg: 'bg-orange-50'
            },
            { 
              label: 'Unique Visitors', 
              value: (visitorSummary.unique_visitors || 0).toLocaleString(), 
              icon: Users,
              color: 'text-purple-600',
              bg: 'bg-purple-50'
            },
            { 
              label: 'Avg. Session', 
              value: visitorSummary.avg_session_duration_seconds ? `${Math.round(visitorSummary.avg_session_duration_seconds)}s` : '0s', 
              icon: Clock,
              color: 'text-green-600',
              bg: 'bg-green-50'
            },
          ].map((stat, i) => (
            <div key={i} className="bg-white p-6 rounded-3xl border border-gray-200/60 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2.5 rounded-2xl ${stat.bg}`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </div>
              <h3 className="text-3xl font-medium text-[#1D1D1F] mb-1 tracking-tight">{stat.value}</h3>
              <p className="text-sm text-[#1D1D1F]/60">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8 relative">
          
          {/* Main Chart */}
          <div className="lg:col-span-2 bg-white p-8 rounded-[32px] border border-gray-200/60 shadow-sm relative overflow-hidden">
            {!hasAdvancedAnalytics && <UpgradeOverlay />}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-lg font-medium text-[#1D1D1F]">Traffic Overview</h2>
                <p className="text-sm text-[#1D1D1F]/60">Views vs Downloads over time</p>
              </div>
            </div>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0066CC" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#0066CC" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorDownloads" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F97316" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E5E5" opacity={0.5} />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#1D1D1F', fontSize: 11, opacity: 0.4 }} 
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#1D1D1F', fontSize: 11, opacity: 0.4 }} 
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '16px', 
                      border: 'none', 
                      boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
                      fontSize: '12px',
                      padding: '12px'
                    }}
                  />
                  <Legend iconType="circle" verticalAlign="top" height={36} />
                  <Area type="monotone" name="Views" dataKey="views" stroke="#0066CC" strokeWidth={2.5} fillOpacity={1} fill="url(#colorViews)" />
                  <Area type="monotone" name="Downloads" dataKey="downloads" stroke="#F97316" strokeWidth={2.5} fillOpacity={1} fill="url(#colorDownloads)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Device Breakdown */}
          <div className="bg-white p-8 rounded-[32px] border border-gray-200/60 shadow-sm flex flex-col relative overflow-hidden">
             {!hasAdvancedAnalytics && <UpgradeOverlay />}
            <h2 className="text-lg font-medium text-[#1D1D1F] mb-1">Devices</h2>
            <p className="text-sm text-[#1D1D1F]/60 mb-8">Where your clients view from</p>
            
            <div className="h-[250px] w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deviceData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {deviceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              
              {/* Center Text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <Smartphone className="w-6 h-6 text-[#1D1D1F]/20" />
              </div>
            </div>

            <div className="mt-auto space-y-3">
              {deviceData.map((device, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: device.color }}></span>
                    <span className="text-[#1D1D1F]/80">{device.name}</span>
                  </div>
                  <span className="font-medium text-[#1D1D1F]">{device.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Photos & Locations Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Top Photos */}
          <div className="bg-white p-8 rounded-[32px] border border-gray-200/60 shadow-sm relative overflow-hidden">
             {!hasAdvancedAnalytics && <UpgradeOverlay />}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-[#1D1D1F]">Most Viewed Photos</h2>
              <ImageIcon className="w-4 h-4 text-[#1D1D1F]/40" />
            </div>
            
            {topPhotos.length > 0 ? (
              <div className="space-y-4">
                {topPhotos.map((photo: TopPhoto, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 hover:bg-[#F5F5F7] rounded-xl transition-colors group">
                    <div className="flex items-center gap-4 overflow-hidden">
                      <span className="w-6 text-center text-sm font-medium text-[#1D1D1F]/40">{i + 1}</span>
                      {/* Thumbnail */}
                      <div className="w-10 h-10 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0 border border-gray-200">
                        {photo.thumbnail_url ? (
                          <img src={photo.thumbnail_url} alt={photo.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-[#1D1D1F]/20">
                            <ImageIcon className="w-4 h-4" />
                          </div>
                        )}
                      </div>
                      
                      <div className="truncate">
                        <p className="text-sm font-medium text-[#1D1D1F] truncate" title={photo.name}>{photo.name}</p>
                        <p className="text-xs text-[#1D1D1F]/40 flex items-center gap-1">
                           <Clock className="w-3 h-3" /> {photo.avg_time_seconds > 0 ? `${photo.avg_time_seconds}s avg` : '--'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-sm font-medium text-[#1D1D1F]">
                      {photo.views.toLocaleString()} <span className="text-[#1D1D1F]/40 font-normal">views</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-[#1D1D1F]/40 text-sm border-2 border-dashed border-gray-100 rounded-xl">
                No photo view data yet
              </div>
            )}
          </div>

          {/* Recent Bulk Downloads */}
          <div className="bg-white p-8 rounded-[32px] border border-gray-200/60 shadow-sm relative overflow-hidden">
             {!hasAdvancedAnalytics && <UpgradeOverlay />}
            <h2 className="text-lg font-medium text-[#1D1D1F] mb-6">Recent Bulk Downloads</h2>
            
            {bulkEvents.length > 0 ? (
              <div className="space-y-4 relative">
                <div className="absolute left-[19px] top-4 bottom-4 w-px bg-gray-100"></div>
                
                {bulkEvents.slice(0, 5).map((event: BulkEvent, i: number) => (
                  <div key={i} className="relative flex gap-4 pl-2">
                    <div className="w-10 h-10 rounded-full bg-white border border-gray-100 flex items-center justify-center z-10 shadow-sm flex-shrink-0">
                      <Download className="w-4 h-4 text-orange-500" />
                    </div>
                    <div className="flex-grow pt-1 pb-4">
                      <div className="flex justify-between items-start mb-1">
                        <p className="text-sm font-medium text-[#1D1D1F]">
                          {event.metadata?.downloader_name || 'Visitor'}
                        </p>
                        <span className="text-xs text-[#1D1D1F]/40">
                          {new Date(event.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-[#1D1D1F]/60 mb-2">
                        Downloaded <span className="text-[#1D1D1F] font-medium">{event.gallery_name}</span>
                        {event.metadata?.photo_count && ` (${event.metadata.photo_count} photos)`}
                      </p>
                      
                      <div className="flex gap-2">
                        {event.metadata?.ip && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-gray-50 text-[#1D1D1F]/50 border border-gray-100">
                            <Globe className="w-2.5 h-2.5" /> {event.metadata.ip}
                          </span>
                        )}
                        {event.metadata?.is_owner_download && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 border border-blue-100">
                            Owner Download
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-[#1D1D1F]/40 text-sm border-2 border-dashed border-gray-100 rounded-xl">
                No bulk downloads yet
              </div>
            )}
          </div>
        </div>

        {/* Top Galleries Table (Only shown when viewing 'All Galleries') */}
        {selectedGalleryId === 'all' && (
          <div className="bg-white p-8 rounded-[32px] border border-gray-200/60 shadow-sm mb-8 relative overflow-hidden">
             {!hasAdvancedAnalytics && <UpgradeOverlay />}
            <h2 className="text-lg font-medium text-[#1D1D1F] mb-6">Top Performing Galleries</h2>
            
            {topGalleries.length > 0 ? (
              <div className="space-y-4">
                {topGalleries.map((gallery: GalleryStat, i: number) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-[#F5F5F7]/50 rounded-2xl hover:bg-[#F5F5F7] transition-colors">
                    <div className="flex items-center gap-4">
                      <span className="w-6 text-center text-sm font-medium text-[#1D1D1F]/40">{i + 1}</span>
                      <div className="w-10 h-10 rounded-lg bg-gray-200 overflow-hidden">
                        <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-[#1D1D1F]/20">
                          <ImageIcon className="w-4 h-4" />
                        </div>
                      </div>
                      <div>
                        <p className="font-medium text-[#1D1D1F] text-sm">{gallery.gallery_name}</p>
                        <p className="text-xs text-[#1D1D1F]/40">{gallery.views.toLocaleString()} views</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex flex-col items-end">
                        <span className="font-medium text-[#1D1D1F]">{gallery.downloads}</span>
                        <span className="text-[10px] text-[#1D1D1F]/40 uppercase tracking-wide">Downloads</span>
                      </div>
                      <div className="w-px h-8 bg-gray-200"></div>
                      <div className="flex flex-col items-end w-12">
                        <span className="font-medium text-green-600">
                          {gallery.views > 0 ? Math.round(((gallery.downloads + gallery.photo_views) / gallery.views) * 100) : 0}%
                        </span>
                        <span className="text-[10px] text-[#1D1D1F]/40 uppercase tracking-wide">Conv.</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-[#1D1D1F]/40 text-sm border-2 border-dashed border-gray-100 rounded-xl">
                No gallery data available yet
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
