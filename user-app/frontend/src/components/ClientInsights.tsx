import { useState, useEffect } from 'react';
import { 
  Eye, 
  Clock, 
  Heart, 
  Download, 
  Share2, 
  TrendingUp,
  AlertCircle,
  BarChart3,
  Zap,
  Repeat
} from 'lucide-react';
import { ClientEngagementSummary, HotMoment } from '../services/analyticsService';
import VideoAttentionTimeline from './VideoAttentionTimeline';

interface ClientInsightsProps {
  photoId: string;
  engagement: ClientEngagementSummary | null;
  isVideo: boolean;
  videoDuration?: number; // Duration in seconds for timeline
  currentVideoTime?: number; // Current playback time
  onSeekVideo?: (time: number) => void; // Seek callback for timeline
}

// Component that shows photographer valuable insights about client engagement
export default function ClientInsights({ 
  photoId, 
  engagement, 
  isVideo, 
  videoDuration, 
  currentVideoTime, 
  onSeekVideo 
}: ClientInsightsProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (!engagement) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>No engagement data yet</span>
        </div>
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getEngagementLevel = (score: number): { label: string; color: string; icon: JSX.Element } => {
    if (score >= 80) return { label: 'High Interest', color: 'text-green-600 bg-green-50 border-green-200', icon: <TrendingUp className="w-4 h-4" /> };
    if (score >= 50) return { label: 'Moderate', color: 'text-blue-600 bg-blue-50 border-blue-200', icon: <Eye className="w-4 h-4" /> };
    return { label: 'Low', color: 'text-gray-600 bg-gray-50 border-gray-200', icon: <Eye className="w-4 h-4" /> };
  };

  const engagementLevel = getEngagementLevel(engagement.engagement_score);

  return (
    <div className="space-y-3">
      {/* Engagement Score Header */}
      <div className={`p-3 rounded-lg border ${engagementLevel.color} transition-all duration-200`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {engagementLevel.icon}
            <span className="font-medium text-sm">{engagementLevel.label}</span>
            <span className="text-xs opacity-70">({engagement.engagement_score}/100)</span>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs underline opacity-70 hover:opacity-100 transition-opacity"
          >
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 gap-2">
        {/* Views */}
        <div className="p-3 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
            <Eye className="w-3.5 h-3.5" />
            <span>Views</span>
          </div>
          <div className="text-lg font-semibold text-gray-900">{engagement.total_views}</div>
        </div>

        {/* Time Spent */}
        <div className="p-3 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Time Spent</span>
          </div>
          <div className="text-lg font-semibold text-gray-900">{formatDuration(engagement.total_time_spent)}</div>
        </div>

        {isVideo && engagement.rewatch_count > 0 && (
          <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 text-purple-600 text-xs mb-1">
              <Repeat className="w-3.5 h-3.5" />
              <span>Rewatches</span>
            </div>
            <div className="text-lg font-semibold text-purple-900">{engagement.rewatch_count}</div>
            <div className="text-xs text-purple-600 mt-1">High interest!</div>
          </div>
        )}

        {/* Favorites */}
        {engagement.favorite_count > 0 && (
          <div className="p-3 bg-pink-50 rounded-lg border border-pink-200">
            <div className="flex items-center gap-2 text-pink-600 text-xs mb-1">
              <Heart className="w-3.5 h-3.5 fill-current" />
              <span>Favorited</span>
            </div>
            <div className="text-lg font-semibold text-pink-900">{engagement.favorite_count}</div>
          </div>
        )}

        {/* Downloads */}
        {engagement.download_count > 0 && (
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 text-blue-600 text-xs mb-1">
              <Download className="w-3.5 h-3.5" />
              <span>Downloads</span>
            </div>
            <div className="text-lg font-semibold text-blue-900">{engagement.download_count}</div>
          </div>
        )}

        {/* Shares */}
        {engagement.share_count > 0 && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 text-green-600 text-xs mb-1">
              <Share2 className="w-3.5 h-3.5" />
              <span>Shared</span>
            </div>
            <div className="text-lg font-semibold text-green-900">{engagement.share_count}</div>
          </div>
        )}
      </div>

      {/* Hot Moments (Videos Only) */}
      {showDetails && isVideo && engagement.hot_moments && engagement.hot_moments.length > 0 && (
        <div className="space-y-4">
          {/* Interactive Timeline Visualization */}
          {videoDuration && videoDuration > 0 && (
            <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
              <div className="flex items-center gap-2 text-indigo-700 text-sm font-medium mb-3">
                <BarChart3 className="w-4 h-4" />
                <span>Attention Timeline</span>
                <span className="text-xs opacity-70">(Click to jump)</span>
              </div>
              <VideoAttentionTimeline
                duration={videoDuration}
                hotMoments={engagement.hot_moments}
                currentTime={currentVideoTime}
                onSeek={onSeekVideo}
              />
            </div>
          )}

          {/* Hot Moments List */}
          <div className="p-3 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg border border-orange-200">
            <div className="flex items-center gap-2 text-orange-700 text-sm font-medium mb-3">
              <Zap className="w-4 h-4 fill-current" />
              <span>Hot Moments</span>
              <span className="text-xs opacity-70">(Paused/Rewatched)</span>
            </div>
            <div className="space-y-2">
            {engagement.hot_moments.slice(0, 3).map((moment, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <div className="flex-shrink-0 w-12 h-8 bg-gradient-to-r from-orange-400 to-red-400 rounded flex items-center justify-center text-white text-xs font-bold">
                  {Math.floor(moment.start_time / 60)}:{String(Math.floor(moment.start_time % 60)).padStart(2, '0')}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="h-1.5 bg-gray-200 rounded-full flex-1 overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full"
                        style={{ width: `${moment.intensity}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-orange-700">{moment.intensity}%</span>
                  </div>
                  <div className="text-xs text-gray-600">
                    {moment.event_count} interactions • Client {moment.events.includes('rewind') ? 'rewatched' : 'paused'} here
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 p-2 bg-white/80 rounded-lg text-xs text-gray-700">
            <BarChart3 className="w-3.5 h-3.5 inline mr-1" />
            <strong>Insight:</strong> These moments captured the client's attention. Consider similar shots in future sessions.
          </div>
        </div>
        </div>
      )}

      {/* Detailed Stats */}
      {showDetails && (
        <div className="p-3 bg-white rounded-lg border border-gray-200 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Average view time</span>
            <span className="font-medium text-gray-900">{formatDuration(engagement.avg_view_duration)}</span>
          </div>
          {engagement.client_comments && engagement.client_comments > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-600">Client comments</span>
              <span className="font-medium text-gray-900">{engagement.client_comments}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-600">Last viewed</span>
            <span className="font-medium text-gray-900">
              {new Date(engagement.last_viewed).toLocaleDateString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
