import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import adminAPI from '../services/api';

export default function Activity() {
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24);
  
  useEffect(() => {
    loadActivity();
  }, [timeRange]);
  
  const loadActivity = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getActivity({ hours: timeRange, limit: 100 });
      setActivities(data.activities);
    } catch (error) {
      console.error('Error loading activity:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark">Activity</h1>
        <p className="text-gray-600 mt-1">Recent platform activity</p>
      </div>
      
      {/* Time Range Filter */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4">
          <Clock className="w-5 h-5 text-gray-400" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value={1}>Last 1 hour</option>
            <option value={6}>Last 6 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={72}>Last 3 days</option>
            <option value={168}>Last 7 days</option>
          </select>
          <button
            onClick={loadActivity}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
      
      {/* Activity Feed */}
      <div className="bg-white rounded-xl border border-gray-200">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No activity in the selected time range</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {activities.map((activity, index) => (
              <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <div className="w-3 h-3 rounded-full bg-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-dark">{activity.action}</p>
                        {activity.details && (
                          <p className="text-sm text-gray-600 mt-1">
                            {JSON.stringify(activity.details)}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 mt-2">
                          User ID: {activity.user_id}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {new Date(activity.timestamp).toLocaleString()}
                      </span>
                    </div>
                    {activity.ip_address && (
                      <p className="text-xs text-gray-500 mt-2">
                        IP: {activity.ip_address}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Summary */}
      {!loading && activities.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          Showing {activities.length} activities
        </div>
      )}
    </div>
  );
}

