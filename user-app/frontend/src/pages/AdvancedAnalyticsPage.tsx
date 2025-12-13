import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, Eye, Download, Share2, Globe, Users, Calendar, 
  Clock, MapPin, Settings, ChevronRight, ArrowUp, ArrowDown,
  Filter, RefreshCw
} from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import RealtimeGlobe from '../components/RealtimeGlobe';

interface AnalyticsData {
  overall: {
    total_views: number;
    total_downloads: number;
    total_shares: number;
    avg_view_duration: number;
    unique_visitors: number;
    returning_visitors: number;
  };
  timeline: Array<{
    date: string;
    views: number;
    downloads: number;
    shares: number;
  }>;
  galleries: Array<{
    id: string;
    name: string;
    views: number;
    downloads: number;
    shares: number;
    engagement_rate: number;
  }>;
  geographic: Array<{
    country: string;
    city: string;
    visits: number;
    percentage: number;
  }>;
  devices: {
    desktop: number;
    mobile: number;
    tablet: number;
  };
  browsers: Array<{
    name: string;
    percentage: number;
  }>;
  traffic_sources: Array<{
    source: string;
    visits: number;
    percentage: number;
  }>;
}

export default function AdvancedAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/analytics/advanced?range=${timeRange}`);
      if (response.success && response.data) {
        setAnalytics(response.data);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Advanced analytics is a Pro feature');
      } else {
        toast.error('Failed to load analytics');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
    toast.success('Analytics refreshed');
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center p-8">
          <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No analytics data yet</h3>
          <p className="text-[#1D1D1F]/60 mb-6">Start sharing galleries to see analytics</p>
          <Link
            to="/dashboard"
            className="inline-block px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1800px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Dashboard</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
              <Link to="/analytics/advanced" className="text-sm font-medium text-[#1D1D1F]">Advanced</Link>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full disabled:opacity-50"
              title="Refresh analytics"
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
              <Settings className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-6 py-8">
        {/* Page Header with Time Range Filter */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-medium text-[#1D1D1F]">Advanced Analytics</h1>
              <span className="px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">Pro</span>
            </div>
            <p className="text-[#1D1D1F]/60">Deep insights into your portfolio performance</p>
          </div>
          <div className="flex items-center gap-2">
            {['7d', '30d', '90d', 'all'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  timeRange === range
                    ? 'bg-[#1D1D1F] text-white'
                    : 'bg-white text-[#1D1D1F]/60 hover:text-[#1D1D1F] border border-gray-200'
                }`}
              >
                {range === '7d' && 'Last 7 days'}
                {range === '30d' && 'Last 30 days'}
                {range === '90d' && 'Last 90 days'}
                {range === 'all' && 'All Time'}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Views', value: analytics.overall.total_views, color: 'text-blue-600', bg: 'bg-blue-50', icon: Eye },
            { label: 'Downloads', value: analytics.overall.total_downloads, color: 'text-green-600', bg: 'bg-green-50', icon: Download },
            { label: 'Shares', value: analytics.overall.total_shares, color: 'text-purple-600', bg: 'bg-purple-50', icon: Share2 },
            { label: 'Unique Visitors', value: analytics.overall.unique_visitors, color: 'text-orange-600', bg: 'bg-orange-50', icon: Users }
          ].map((stat, i) => (
            <div key={i} className="bg-white p-5 rounded-3xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">{stat.label}</span>
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-3xl font-medium text-[#1D1D1F]">{formatNumber(stat.value)}</div>
            </div>
          ))}
        </div>

        {/* Realtime Globe */}
        <div className="bg-white rounded-3xl border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-medium text-[#1D1D1F] mb-1">Global Visitors</h2>
              <p className="text-sm text-[#1D1D1F]/60">Real-time visitor tracking</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs font-medium text-green-700">Live</span>
            </div>
          </div>
          <div className="h-[400px] bg-gray-50 rounded-2xl overflow-hidden">
            <RealtimeGlobe />
          </div>
        </div>

        {/* Top Galleries */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden mb-8">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-medium text-[#1D1D1F]">Top Performing Galleries</h2>
          </div>
          <div className="divide-y divide-gray-100">
            {analytics.galleries.slice(0, 5).map((gallery, index) => (
              <div key={gallery.id} className="p-6 hover:bg-gray-50 transition-colors group">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="text-2xl font-bold text-[#1D1D1F]/20">#{index + 1}</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">{gallery.name}</h3>
                      <div className="flex items-center gap-6 text-sm text-[#1D1D1F]/60">
                        <div className="flex items-center gap-1.5">
                          <Eye className="w-4 h-4" />
                          {formatNumber(gallery.views)} views
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Download className="w-4 h-4" />
                          {formatNumber(gallery.downloads)} downloads
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Share2 className="w-4 h-4" />
                          {formatNumber(gallery.shares)} shares
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm text-[#1D1D1F]/40 mb-1">Engagement</div>
                      <div className="text-xl font-medium text-[#1D1D1F]">{gallery.engagement_rate}%</div>
                    </div>
                    <Link
                      to={`/gallery/${gallery.id}/analytics`}
                      className="p-2 opacity-0 group-hover:opacity-100 transition-opacity text-[#0066CC] hover:bg-blue-50 rounded-full"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Geographic Data */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-medium text-[#1D1D1F]">Top Locations</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {analytics.geographic.slice(0, 5).map((location, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="font-medium text-[#1D1D1F]">{location.city}</div>
                        <div className="text-sm text-[#1D1D1F]/60">{location.country}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-[#1D1D1F]">{formatNumber(location.visits)}</div>
                      <div className="text-sm text-[#1D1D1F]/60">{location.percentage.toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-medium text-[#1D1D1F]">Traffic Sources</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {analytics.traffic_sources.map((source, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-[#1D1D1F]">{source.source}</span>
                      <span className="text-sm text-[#1D1D1F]/60">{source.percentage.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{ width: `${source.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Device & Browser Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl border border-gray-200 p-6">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">Device Types</h2>
            <div className="space-y-4">
              {Object.entries(analytics.devices).map(([device, count]) => {
                const total = analytics.devices.desktop + analytics.devices.mobile + analytics.devices.tablet;
                const percentage = (count / total) * 100;
                return (
                  <div key={device}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-[#1D1D1F] capitalize">{device}</span>
                      <span className="text-sm text-[#1D1D1F]/60">{percentage.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-600 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-gray-200 p-6">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">Top Browsers</h2>
            <div className="space-y-4">
              {analytics.browsers.slice(0, 4).map((browser, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-[#1D1D1F]">{browser.name}</span>
                    <span className="text-sm text-[#1D1D1F]/60">{browser.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 rounded-full"
                      style={{ width: `${browser.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
