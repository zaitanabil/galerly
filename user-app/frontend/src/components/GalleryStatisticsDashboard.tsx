import { useState, useEffect } from 'react';
import { 
  TrendingUp, Users, Eye, Heart, Download, MapPin, 
  Smartphone, Monitor, BarChart3, Calendar, ArrowUp, 
  ArrowDown, AlertCircle, CheckCircle, Globe
} from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface GalleryStatistics {
  gallery_id: string;
  gallery_name: string;
  overview: {
    total_views: number;
    unique_visitors: number;
    total_photos: number;
    performance_score: number;
    engagement_rate: number;
    avg_time_spent_seconds: number;
  };
  trends: {
    views_last_7_days: number;
    views_last_30_days: number;
    daily_views: Array<{ date: string; views: number }>;
  };
  top_photos: Array<{
    photo_id: string;
    filename: string;
    views: number;
    favorites: number;
    downloads: number;
    thumbnail_url: string;
  }>;
  client_activity: {
    total_favorites: number;
    total_downloads: number;
    photos_with_favorites: number;
    photos_with_downloads: number;
  };
  geography: {
    top_countries: Array<{ country: string; views: number }>;
  };
  devices: {
    desktop: number;
    mobile: number;
    tablet: number;
    unknown: number;
  };
  referrers: Array<{ source: string; visits: number }>;
  recommendations: Array<{
    type: string;
    priority: string;
    title: string;
    description: string;
    actions: string[];
  }>;
}

interface GalleryStatisticsDashboardProps {
  galleryId: string;
}

export default function GalleryStatisticsDashboard({ galleryId }: GalleryStatisticsDashboardProps) {
  const [statistics, setStatistics] = useState<GalleryStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    loadStatistics();
  }, [galleryId]);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/galleries/${galleryId}/statistics`);
      if (response.data) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('Failed to load gallery statistics:', error);
      toast.error('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getPriorityBadge = (priority: string) => {
    const styles = {
      high: 'bg-red-100 text-red-700 border-red-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      low: 'bg-blue-100 text-blue-700 border-blue-200',
      info: 'bg-green-100 text-green-700 border-green-200'
    };
    return styles[priority as keyof typeof styles] || styles.info;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No statistics available</p>
      </div>
    );
  }

  const { overview, trends, top_photos, client_activity, geography, devices, referrers, recommendations } = statistics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">{statistics.gallery_name}</h2>
          <div className={`px-4 py-2 rounded-lg border-2 font-bold text-2xl ${getScoreColor(overview.performance_score)}`}>
            {overview.performance_score}/100
          </div>
        </div>
        <p className="text-gray-600">Performance Score</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Views */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Eye className="w-8 h-8 text-blue-600" />
            <span className="text-sm text-gray-500">Last 30d: {trends.views_last_30_days}</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{overview.total_views}</p>
          <p className="text-sm text-gray-600">Total Views</p>
        </div>

        {/* Unique Visitors */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Users className="w-8 h-8 text-green-600" />
            <span className="text-sm text-gray-500">Unique</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{overview.unique_visitors}</p>
          <p className="text-sm text-gray-600">Visitors</p>
        </div>

        {/* Engagement Rate */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-8 h-8 text-purple-600" />
            <span className="text-sm text-gray-500">Avg: {formatTime(overview.avg_time_spent_seconds)}</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{overview.engagement_rate}%</p>
          <p className="text-sm text-gray-600">Engagement</p>
        </div>

        {/* Total Photos */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="w-8 h-8 text-orange-600" />
            <span className="text-sm text-gray-500">In Gallery</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{overview.total_photos}</p>
          <p className="text-sm text-gray-600">Photos</p>
        </div>
      </div>

      {/* Client Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Heart className="w-5 h-5 text-red-500" />
          Client Activity
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-2xl font-bold text-gray-900">{client_activity.total_favorites}</p>
            <p className="text-sm text-gray-600">Total Favorites</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{client_activity.total_downloads}</p>
            <p className="text-sm text-gray-600">Total Downloads</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{client_activity.photos_with_favorites}</p>
            <p className="text-sm text-gray-600">Photos Favorited</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{client_activity.photos_with_downloads}</p>
            <p className="text-sm text-gray-600">Photos Downloaded</p>
          </div>
        </div>
      </div>

      {/* Top Photos */}
      {top_photos.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Photos</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {top_photos.slice(0, 5).map((photo) => (
              <div key={photo.photo_id} className="relative group">
                <img 
                  src={photo.thumbnail_url} 
                  alt={photo.filename}
                  className="w-full h-32 object-cover rounded-lg"
                />
                <div className="absolute inset-0 bg-black bg-opacity-60 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity p-2 flex flex-col justify-end text-white text-xs">
                  <div className="flex items-center gap-2 mb-1">
                    <Eye className="w-3 h-3" />
                    <span>{photo.views} views</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <Heart className="w-3 h-3" />
                    <span>{photo.favorites} favorites</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Download className="w-3 h-3" />
                    <span>{photo.downloads} downloads</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Geography and Devices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Countries */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            Top Countries
          </h3>
          <div className="space-y-3">
            {geography.top_countries.map((country, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-gray-700">{country.country}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(country.views / overview.total_views) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-12 text-right">{country.views}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Device Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-purple-600" />
            Devices
          </h3>
          <div className="space-y-3">
            {Object.entries(devices).map(([device, count]) => (
              <div key={device} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {device === 'mobile' && <Smartphone className="w-4 h-4 text-gray-600" />}
                  {device === 'desktop' && <Monitor className="w-4 h-4 text-gray-600" />}
                  <span className="text-gray-700 capitalize">{device}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${(count / overview.total_views) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-12 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Recommendations
          </h3>
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900">{rec.title}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getPriorityBadge(rec.priority)}`}>
                    {rec.priority}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-3">{rec.description}</p>
                <ul className="space-y-1">
                  {rec.actions.map((action, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

