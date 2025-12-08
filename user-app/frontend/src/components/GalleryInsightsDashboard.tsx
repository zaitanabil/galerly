import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Eye, 
  Clock, 
  Heart,
  Download,
  Video,
  Image as ImageIcon,
  BarChart3,
  PieChart,
  Award,
  Zap
} from 'lucide-react';
import { ClientEngagementSummary, ClientPreferences } from '../services/analyticsService';
import * as analyticsService from '../services/analyticsService';

interface GalleryInsightsDashboardProps {
  galleryId: string;
  photos: Array<{
    id: string;
    filename: string;
    thumbnail_url?: string;
    url: string;
    type?: 'image' | 'video';
  }>;
}

// Dashboard showing gallery-wide insights and comparisons
export default function GalleryInsightsDashboard({ galleryId, photos }: GalleryInsightsDashboardProps) {
  const [engagementData, setEngagementData] = useState<ClientEngagementSummary[]>([]);
  const [clientPrefs, setClientPrefs] = useState<ClientPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'top' | 'preferences'>('overview');

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [engagement, prefs] = await Promise.all([
          analyticsService.getGalleryEngagement(galleryId),
          analyticsService.getClientPreferences(galleryId)
        ]);
        setEngagementData(engagement);
        setClientPrefs(prefs);
      } catch (error) {
        console.error('Failed to load gallery insights:', error);
      }
      setLoading(false);
    };
    
    loadData();
  }, [galleryId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // If no data available yet, show empty state
  if (!engagementData || engagementData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <BarChart3 className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">No Insights Yet</h3>
        <p className="text-sm text-gray-500 max-w-md">
          Insights will appear once clients start viewing and interacting with your gallery.
          Share your gallery link with clients to begin collecting data.
        </p>
      </div>
    );
  }

  // Calculate summary stats
  const totalViews = engagementData.reduce((sum, item) => sum + item.total_views, 0);
  const totalTime = engagementData.reduce((sum, item) => sum + item.total_time_spent, 0);
  const totalFavorites = engagementData.reduce((sum, item) => sum + item.favorite_count, 0);
  const totalDownloads = engagementData.reduce((sum, item) => sum + item.download_count, 0);
  
  // Top performers
  const topByEngagement = [...engagementData]
    .sort((a, b) => b.engagement_score - a.engagement_score)
    .slice(0, 5);
  
  const topByViews = [...engagementData]
    .sort((a, b) => b.total_views - a.total_views)
    .slice(0, 5);
  
  const topByTime = [...engagementData]
    .sort((a, b) => b.total_time_spent - a.total_time_spent)
    .slice(0, 5);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const getPhotoName = (photoId: string) => {
    const photo = photos.find(p => p.id === photoId);
    return photo?.filename || 'Unknown';
  };

  const getPhotoThumb = (photoId: string) => {
    const photo = photos.find(p => p.id === photoId);
    return photo?.thumbnail_url || photo?.url;
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'overview'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('top')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'top'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Top Performers
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === 'preferences'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Client Preferences
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
              <div className="flex items-center gap-2 text-blue-700 text-sm mb-2">
                <Eye className="w-4 h-4" />
                <span className="font-medium">Total Views</span>
              </div>
              <div className="text-2xl font-bold text-blue-900">{totalViews}</div>
              <div className="text-xs text-blue-600 mt-1">
                Avg: {Math.round(totalViews / photos.length)} per photo
              </div>
            </div>

            <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
              <div className="flex items-center gap-2 text-purple-700 text-sm mb-2">
                <Clock className="w-4 h-4" />
                <span className="font-medium">Time Engaged</span>
              </div>
              <div className="text-2xl font-bold text-purple-900">{formatTime(totalTime)}</div>
              <div className="text-xs text-purple-600 mt-1">
                Avg: {formatTime(totalTime / photos.length)} per photo
              </div>
            </div>

            <div className="p-4 bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl border border-pink-200">
              <div className="flex items-center gap-2 text-pink-700 text-sm mb-2">
                <Heart className="w-4 h-4 fill-current" />
                <span className="font-medium">Favorites</span>
              </div>
              <div className="text-2xl font-bold text-pink-900">{totalFavorites}</div>
              <div className="text-xs text-pink-600 mt-1">
                {Math.round((totalFavorites / photos.length) * 100)}% of photos
              </div>
            </div>

            <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
              <div className="flex items-center gap-2 text-green-700 text-sm mb-2">
                <Download className="w-4 h-4" />
                <span className="font-medium">Downloads</span>
              </div>
              <div className="text-2xl font-bold text-green-900">{totalDownloads}</div>
              <div className="text-xs text-green-600 mt-1">
                {Math.round((totalDownloads / photos.length) * 100)}% of photos
              </div>
            </div>
          </div>

          {/* Quick Insights */}
          <div className="p-4 bg-gradient-to-r from-orange-50 to-yellow-50 rounded-xl border border-orange-200">
            <div className="flex items-center gap-2 text-orange-700 font-medium mb-3">
              <Zap className="w-5 h-5 fill-current" />
              <span>Quick Insights</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <TrendingUp className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">
                  <strong>{topByEngagement[0] && getPhotoName(topByEngagement[0].photo_id)}</strong> has the highest engagement score ({topByEngagement[0]?.engagement_score}/100)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Eye className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">
                  <strong>{topByViews[0] && getPhotoName(topByViews[0].photo_id)}</strong> was viewed the most ({topByViews[0]?.total_views} times)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">
                  Clients spent the most time on <strong>{topByTime[0] && getPhotoName(topByTime[0].photo_id)}</strong> ({formatTime(topByTime[0]?.total_time_spent || 0)})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Performers Tab */}
      {activeTab === 'top' && (
        <div className="space-y-6">
          {/* Top by Engagement Score */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-yellow-500 fill-current" />
              Highest Engagement
            </h3>
            <div className="space-y-3">
              {topByEngagement.map((item, idx) => (
                <div key={item.photo_id} className="flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 transition-colors">
                  <div className="text-2xl font-bold text-gray-400 w-8">#{idx + 1}</div>
                  <div className="relative">
                    <img
                      src={getPhotoThumb(item.photo_id) || ''}
                      alt=""
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                    {/* Download badge indicator */}
                    {item.was_downloaded && (
                      <div className="absolute -top-1 -right-1 bg-green-500 rounded-full p-1 shadow-lg border-2 border-white" title={`Downloaded ${item.download_count} time${item.download_count > 1 ? 's' : ''}`}>
                        <Download className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">{getPhotoName(item.photo_id)}</div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3.5 h-3.5" />
                        {item.total_views}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {formatTime(item.total_time_spent)}
                      </span>
                      {item.favorite_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Heart className="w-3.5 h-3.5 fill-current text-pink-500" />
                          {item.favorite_count}
                        </span>
                      )}
                      {item.download_count > 0 && (
                        <span className="flex items-center gap-1 text-green-600 font-medium">
                          <Download className="w-3.5 h-3.5" />
                          {item.download_count}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">{item.engagement_score}</div>
                    <div className="text-xs text-gray-500">score</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Downloaded Items Section */}
          {engagementData.filter(item => item.was_downloaded).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Download className="w-5 h-5 text-green-600" />
                Downloaded Items
              </h3>
              <div className="space-y-3">
                {engagementData
                  .filter(item => item.was_downloaded)
                  .sort((a, b) => b.download_count - a.download_count)
                  .map((item) => (
                    <div key={item.photo_id} className="flex items-center gap-4 p-4 bg-green-50 rounded-xl border border-green-200">
                      <img
                        src={getPhotoThumb(item.photo_id) || ''}
                        alt=""
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{getPhotoName(item.photo_id)}</div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                          <span className="flex items-center gap-1 text-green-700 font-semibold">
                            <Download className="w-3.5 h-3.5" />
                            Downloaded {item.download_count} time{item.download_count > 1 ? 's' : ''}
                          </span>
                          {item.download_timestamps && item.download_timestamps.length > 0 && (
                            <span className="text-xs text-gray-500">
                              Latest: {new Date(item.download_timestamps[item.download_timestamps.length - 1]).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">{item.engagement_score}</div>
                        <div className="text-xs text-gray-500">score</div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Client Preferences Tab */}
      {activeTab === 'preferences' && clientPrefs && clientPrefs.engagement_pattern && (
        <div className="space-y-6">
          <div className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-200">
            <div className="flex items-center gap-2 text-indigo-700 font-semibold mb-4">
              <PieChart className="w-5 h-5" />
              <span>Client Behavior Pattern</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Engagement Style</h4>
                <div className="text-lg font-semibold text-indigo-900 capitalize">
                  {clientPrefs.engagement_pattern.replace('_', ' ')}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {clientPrefs.engagement_pattern === 'quick_browser' && 'Fast-paced viewing, make first impression count'}
                  {clientPrefs.engagement_pattern === 'detailed_reviewer' && 'Takes time with each photo, values details'}
                  {clientPrefs.engagement_pattern === 'selective_engager' && 'Selective but engaged, quality over quantity'}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Decision Speed</h4>
                <div className="text-lg font-semibold text-indigo-900 capitalize">
                  {clientPrefs.decision_speed}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Avg {formatTime(clientPrefs.avg_time_per_photo)} per photo
                </p>
              </div>
            </div>

            {clientPrefs.preferred_styles && clientPrefs.preferred_styles.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Preferred Styles</h4>
                <div className="flex flex-wrap gap-2">
                  {clientPrefs.preferred_styles.map(style => (
                    <span key={style} className="px-3 py-1 bg-white text-indigo-700 rounded-full text-sm font-medium border border-indigo-200">
                      {style}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {clientPrefs.favorite_photo_types && clientPrefs.favorite_photo_types.length > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <BarChart3 className="w-4 h-4 inline text-blue-600 mr-2" />
              <span className="text-sm text-blue-800">
                <strong>Recommendation:</strong> Focus on {clientPrefs.favorite_photo_types.join(', ')} shots in future sessions based on client preferences.
              </span>
            </div>
          )}
        </div>
      )}
      
      {/* Show message if no preferences data */}
      {activeTab === 'preferences' && (!clientPrefs || !clientPrefs.engagement_pattern) && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <PieChart className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Not Enough Data</h3>
          <p className="text-sm text-gray-500 max-w-md">
            Client preference insights will appear once there's enough interaction data.
          </p>
        </div>
      )}

      {/* Export Button */}
      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          onClick={() => analyticsService.exportGalleryReport(galleryId, 'pdf')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export Full Report (PDF)
        </button>
      </div>
    </div>
  );
}
