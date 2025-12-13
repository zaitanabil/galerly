// Dashboard page - Main dashboard for photographers
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGalleries, useDashboardStats, useBulkDownloads } from '../hooks/useApi';
import { useActiveViewers } from '../hooks/useViewerTracking';
import {
  Plus, Image as ImageIcon, Users, Settings, LogOut,
  Download, Eye, HardDrive, ChevronRight, Activity, Zap,
  FileText, Mail, Briefcase, Calendar, Archive, Workflow, Search
} from 'lucide-react';
import { getImageUrl } from '../config/env';
import RealtimeGlobe from '../components/RealtimeGlobe';

interface DashboardStats {
  stats: {
    total_galleries: number;
    total_photos: number;
    total_views: number;
    total_downloads: number;
    storage_percent: number;
    storage_used_gb: number;
    storage_limit_gb: number;
  };
  analytics: {
    daily_stats: { date: string; views: number; downloads: number }[];
  };
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

export default function DashboardPage() {
  const { user, logout } = useAuth();
  
  // Data fetching
  const { data: galleriesData, loading: galleriesLoading } = useGalleries();
  const { data: statsData, loading: statsLoading } = useDashboardStats();
  const { data: bulkDownloadsData } = useBulkDownloads();
  const { data: activeViewersData } = useActiveViewers(true);

  const galleries = galleriesData?.galleries || [];
  const loading = galleriesLoading || statsLoading;
  
  // Extract stats
  const dashboardData = statsData as unknown as DashboardStats;
  const stats = dashboardData?.stats || {
    total_galleries: 0,
    total_photos: 0,
    total_views: 0,
    total_downloads: 0,
    storage_percent: 0,
    storage_used_gb: 0,
    storage_limit_gb: 0
  };
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recentActivity = (bulkDownloadsData as any)?.events?.slice(0, 5) || [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-[#1D1D1F]/60 text-sm font-medium animate-pulse">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  // Animation delay helper
  const delay = (i: number) => ({ animationDelay: `${i * 100}ms` });

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Top Navigation */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
                Galerly
              </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]">Dashboard</Link>
              <Link to="/galleries" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Galleries</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Analytics</Link>
              <Link to="/billing" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Billing</Link>
              </nav>
            </div>
            <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-[#F5F5F7] rounded-full text-xs font-medium text-[#1D1D1F]/60 border border-[#1D1D1F]/5">
              <span className={`w-2 h-2 rounded-full ${stats.storage_percent > 90 ? 'bg-red-500' : 'bg-green-500'}`}></span>
              {stats.storage_percent}% Storage Used
            </div>
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
        {/* Welcome Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 animate-fade-in-up">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] tracking-tight mb-2">
              Overview
          </h1>
            <p className="text-[#1D1D1F]/60">
              Welcome back, {user?.name?.split(' ')[0]}. Here's what's happening today.
            </p>
          </div>
          <div className="flex gap-3">
             <Link 
              to="/analytics" 
              className="flex items-center gap-2 px-5 py-2.5 bg-white text-[#1D1D1F] border border-gray-200 rounded-full text-sm font-medium hover:bg-gray-50 transition-all shadow-sm"
            >
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">View Full Report</span>
              <span className="sm:hidden">Report</span>
            </Link>
          <Link
            to="/new-gallery"
              className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black hover:shadow-lg transition-all"
          >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">New Gallery</span>
              <span className="sm:hidden">New</span>
          </Link>
            </div>
          </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total Galleries', value: stats.total_galleries, icon: ImageIcon, color: 'text-blue-600', bg: 'bg-blue-50/50' },
            { label: 'Total Views', value: stats.total_views.toLocaleString(), icon: Eye, color: 'text-purple-600', bg: 'bg-purple-50/50' },
            { label: 'Total Downloads', value: stats.total_downloads.toLocaleString(), icon: Download, color: 'text-orange-600', bg: 'bg-orange-50/50' }
          ].map((stat, i) => (
            <div 
              key={i} 
              className="bg-white p-5 rounded-3xl border border-gray-200/60 shadow-[0_2px_12px_rgba(0,0,0,0.02)] hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all group animate-fade-in-up"
              style={delay(i)}
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-widest">{stat.label}</span>
                <div className={`p-2.5 rounded-2xl ${stat.bg} group-hover:scale-110 transition-transform duration-300`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-medium text-[#1D1D1F] tracking-tight">{stat.value}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content Column */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Real-time Globe Section */}
            <div className="animate-fade-in-up" style={delay(4)}>
              <RealtimeGlobe 
                viewers={activeViewersData?.viewers || []}
                totalActive={activeViewersData?.total_active || 0}
                byCountry={activeViewersData?.by_country || {}}
              />
            </div>

            {/* Feature Discovery Section */}
            <div className="animate-fade-in-up mb-8" style={delay(4)}>
              <h2 className="text-xl font-medium text-[#1D1D1F] mb-4">Discover Features</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <Link
                  to="/crm"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-blue-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                      <Users className="w-4 h-4 text-blue-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">Pro</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Lead Management</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Track potential clients</p>
                </Link>

                <Link
                  to="/scheduler"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-purple-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-purple-50 rounded-xl group-hover:bg-purple-100 transition-colors">
                      <Calendar className="w-4 h-4 text-purple-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full font-medium">Ultimate</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Scheduler</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Client bookings</p>
                </Link>

                <Link
                  to="/services"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-green-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-green-50 rounded-xl group-hover:bg-green-100 transition-colors">
                      <Briefcase className="w-4 h-4 text-green-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full font-medium">All</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Services</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Showcase pricing</p>
                </Link>

                <Link
                  to="/invoices"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-pink-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-pink-50 rounded-xl group-hover:bg-pink-100 transition-colors">
                      <FileText className="w-4 h-4 text-pink-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">Pro</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Invoicing</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Professional invoices</p>
                </Link>

                <Link
                  to="/email-templates"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-indigo-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-indigo-50 rounded-xl group-hover:bg-indigo-100 transition-colors">
                      <Mail className="w-4 h-4 text-indigo-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">Pro</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Email Templates</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Custom emails</p>
                </Link>

                <Link
                  to="/onboarding"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-teal-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-teal-50 rounded-xl group-hover:bg-teal-100 transition-colors">
                      <Workflow className="w-4 h-4 text-teal-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">Pro</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Onboarding</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Client workflows</p>
                </Link>

                <Link
                  to="/raw-vault"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-orange-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-orange-50 rounded-xl group-hover:bg-orange-100 transition-colors">
                      <Archive className="w-4 h-4 text-orange-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full font-medium">Ultimate</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">RAW Vault</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Glacier archive</p>
                </Link>

                <Link
                  to="/seo/dashboard"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-cyan-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-cyan-50 rounded-xl group-hover:bg-cyan-100 transition-colors">
                      <Search className="w-4 h-4 text-cyan-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">Pro</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">SEO Tools</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Optimize visibility</p>
                </Link>

                <Link
                  to="/watermark"
                  className="group bg-white border border-gray-200 rounded-2xl p-4 hover:border-amber-500 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-amber-50 rounded-xl group-hover:bg-amber-100 transition-colors">
                      <ImageIcon className="w-4 h-4 text-amber-600" />
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-medium">Plus</span>
                  </div>
                  <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">Watermarking</h3>
                  <p className="text-xs text-[#1D1D1F]/60">Protect photos</p>
                </Link>
              </div>
            </div>

            {/* Recent Galleries */}
            <div className="animate-fade-in-up" style={delay(5)}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-medium text-[#1D1D1F]">Recent Galleries</h2>
                <Link to="/galleries" className="text-sm font-medium text-[#0066CC] hover:text-[#0052A3] flex items-center gap-1 transition-colors">
                  View All <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

              {galleries.length === 0 ? (
                <div className="bg-white rounded-[32px] border border-gray-200 border-dashed p-12 text-center">
                  <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <ImageIcon className="w-8 h-8 text-gray-300" />
          </div>
                  <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No galleries yet</h3>
                  <p className="text-[#1D1D1F]/60 text-sm mb-8 max-w-sm mx-auto">Create your first gallery to start sharing your work with clients.</p>
                  <Link to="/new-gallery" className="inline-flex items-center gap-2 px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black transition-all">
                    <Plus className="w-4 h-4" /> Create Gallery
            </Link>
          </div>
        ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {galleries.slice(0, 4).map((gallery: any, index: number) => {
                    const coverImage = gallery.cover_photo || gallery.cover_photo_url || gallery.thumbnail_url;
              return (
              <Link
                  key={gallery.id}
                  to={`/gallery/${gallery.id}`}
                        className="group bg-white rounded-[24px] p-3 border border-gray-200/60 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300"
                        style={{ animationDelay: `${(index + 5) * 100}ms` }}
              >
                        <div className="flex gap-5">
                          <div className="w-28 h-28 rounded-2xl bg-gray-100 overflow-hidden flex-shrink-0 relative shadow-inner">
                    {coverImage ? (
                              <img src={getImageUrl(coverImage)} alt={gallery.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
                  ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-300 bg-gray-50">
                                <ImageIcon className="w-8 h-8 opacity-50" />
                              </div>
                            )}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors" />
                          </div>
                          <div className="flex flex-col justify-center py-2 flex-grow min-w-0">
                            <h3 className="text-lg font-medium text-[#1D1D1F] truncate mb-1 group-hover:text-[#0066CC] transition-colors">
                              {gallery.name || 'Untitled Gallery'}
                            </h3>
                            <div className="flex items-center gap-2 text-xs text-[#1D1D1F]/50 mb-4">
                              <span className="flex items-center gap-1.5 truncate"><Users className="w-3 h-3" /> {gallery.client_name || 'No Client'}</span>
                              <span className="text-gray-300">•</span>
                              <span className="flex-shrink-0">{gallery.photo_count || 0} photos</span>
                            </div>
                            <div className="flex items-center justify-between mt-auto">
                              <span className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border ${
                                gallery.status === 'published' || gallery.status === 'active' 
                                  ? 'bg-green-50 text-green-700 border-green-100' 
                                  : 'bg-yellow-50 text-yellow-700 border-yellow-100'
                              }`}>
                                {gallery.status || 'Active'}
                              </span>
                              <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-[#0066CC]">
                                <ChevronRight className="w-4 h-4" />
                              </div>
                            </div>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                    </div>
                  )}
            </div>
          </div>
                  
          {/* Right Sidebar */}
          <div className="space-y-6">
            
            {/* Storage Card */}
            <div className="bg-[#1D1D1F] text-white p-8 rounded-[32px] relative overflow-hidden shadow-2xl shadow-gray-900/10 group animate-fade-in-up" style={delay(6)}>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="font-medium text-lg">Storage</h3>
                  <div className="p-2 bg-white/10 rounded-full backdrop-blur-md">
                    <HardDrive className="w-5 h-5 text-white/80" />
                  </div>
                </div>

                <div className="mb-3 flex items-baseline gap-2">
                  <span className="text-4xl font-light tracking-tight">{stats.storage_used_gb}</span>
                  <span className="text-lg text-white/40">/ {stats.storage_limit_gb === -1 ? '∞' : stats.storage_limit_gb} GB</span>
                </div>
                
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden mb-8 backdrop-blur-sm">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ${stats.storage_percent > 90 ? 'bg-red-500' : 'bg-white'}`}
                    style={{ width: `${Math.min(stats.storage_percent, 100)}%` }}
                  />
                </div>

                <Link 
                  to="/billing" 
                  className="w-full py-3.5 bg-white text-[#1D1D1F] hover:bg-gray-100 rounded-2xl text-sm font-medium text-center block transition-all shadow-lg shadow-black/20"
                >
                  Manage Plan
                </Link>
              </div>
              
              {/* Background Decoration */}
              <div className="absolute top-[-20%] right-[-20%] w-[120%] h-[120%] bg-gradient-to-br from-[#0066CC]/20 via-transparent to-purple-600/20 rounded-full blur-3xl pointer-events-none group-hover:scale-110 transition-transform duration-1000" />
            </div>

            {/* Recent Activity */}
            <div className="bg-white p-6 rounded-[32px] border border-gray-200/60 shadow-[0_2px_12px_rgba(0,0,0,0.02)] animate-fade-in-up" style={delay(7)}>
              <div className="flex items-center justify-between mb-6 px-2">
                <h3 className="font-medium text-[#1D1D1F]">Recent Activity</h3>
                <Link to="/analytics" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                  <Activity className="w-4 h-4 text-[#1D1D1F]/40" />
                </Link>
                  </div>
                  
              <div className="space-y-1">
                {recentActivity.length > 0 ? (
                  recentActivity.map((event: BulkEvent, i: number) => (
                    <div key={i} className="flex gap-4 p-3 hover:bg-[#F5F5F7] rounded-2xl transition-colors group">
                      <div className="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        <Download className="w-4 h-4 text-orange-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm text-[#1D1D1F] leading-snug">
                          <span className="font-medium">{event.metadata?.downloader_name || 'Someone'}</span> downloaded
                          <span className="font-medium text-[#0066CC]"> {event.gallery_name || 'a gallery'}</span>
                        </p>
                        <p className="text-xs text-[#1D1D1F]/40 mt-1">
                          {new Date(event.timestamp).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: 'numeric' })}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-sm text-[#1D1D1F]/40 bg-[#F5F5F7]/50 rounded-2xl border border-dashed border-gray-200">
                    No recent activity
                  </div>
                )}
              </div>
                  </div>
                  
            {/* Pro Tip / Onboarding */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-[32px] border border-blue-100 animate-fade-in-up" style={delay(8)}>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-white rounded-xl shadow-sm">
                  <Zap className="w-5 h-5 text-amber-500 fill-amber-500" />
                  </div>
                <div>
                  <h3 className="font-medium text-[#1D1D1F] mb-1">Pro Tip</h3>
                  <p className="text-sm text-[#1D1D1F]/70 mb-3 leading-relaxed">
                    Galleries with <span className="font-medium text-[#0066CC]">Custom Domains</span> get 40% more engagement.
                  </p>
                  <Link to="/settings" className="text-sm font-medium text-[#0066CC] hover:underline flex items-center gap-1">
                    Configure Domain <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
