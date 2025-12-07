import { useEffect, useState } from 'react';
import { CreditCard, Check, X, AlertTriangle, Users } from 'lucide-react';
import adminAPI from '../services/api';

export default function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [stats, setStats] = useState<any>(null);
  
  useEffect(() => {
    loadSubscriptions();
  }, [statusFilter]);
  
  const loadSubscriptions = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getSubscriptions(statusFilter);
      setSubscriptions(data.subscriptions);
      setStats(data);
    } catch (error) {
      console.error('Error loading subscriptions:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark">Subscriptions</h1>
        <p className="text-gray-600 mt-1">Monitor active and canceled subscriptions</p>
      </div>
      
      {/* Health Issues Alert */}
      {stats && (stats.orphaned_count > 0 || Object.keys(stats.duplicate_emails || {}).length > 0) && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-amber-900">Data Integrity Issues Detected</h3>
              <ul className="mt-2 space-y-1 text-sm text-amber-800">
                {stats.orphaned_count > 0 && (
                  <li>• {stats.orphaned_count} orphaned subscription(s) without matching user accounts</li>
                )}
                {Object.keys(stats.duplicate_emails || {}).length > 0 && (
                  <li>• {Object.keys(stats.duplicate_emails).length} email(s) with multiple subscriptions</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
      
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mb-6">
          {Object.entries(stats.by_plan || {}).map(([plan, count]: [string, any]) => (
            <div key={plan} className="bg-white rounded-xl border border-gray-200 p-3 sm:p-4">
              <p className="text-xs sm:text-sm text-gray-600 capitalize">{plan}</p>
              <p className="text-xl sm:text-2xl font-bold text-dark mt-1">{count}</p>
            </div>
          ))}
          {stats.orphaned_count > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 sm:p-4">
              <p className="text-xs sm:text-sm text-amber-700 font-medium">Orphaned</p>
              <p className="text-xl sm:text-2xl font-bold text-amber-900 mt-1">{stats.orphaned_count}</p>
            </div>
          )}
        </div>
      )}
      
      {/* Status Filter */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4">
          <CreditCard className="w-5 h-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="canceled">Canceled</option>
          </select>
        </div>
      </div>
      
      {/* Subscriptions Table - Desktop */}
      <div className="hidden md:block bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : subscriptions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No subscriptions found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  User Email
                </th>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    User Status
                  </th>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Plan
                </th>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Status
                </th>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Created
                </th>
                  <th className="px-4 lg:px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Stripe ID
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {subscriptions.map((sub) => (
                  <tr 
                    key={sub.id} 
                    className={`hover:bg-gray-50 transition-colors ${sub.is_orphaned ? 'bg-amber-50' : ''}`}
                  >
                    <td className="px-4 lg:px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-dark">{sub.user_email}</span>
                        {!sub.user_exists && (
                          <AlertTriangle className="w-4 h-4 text-amber-600" title="User account not found" />
                        )}
                      </div>
                      {sub.user_name && (
                        <div className="text-xs text-gray-500 mt-1">{sub.user_name}</div>
                      )}
                    </td>
                    <td className="px-4 lg:px-6 py-4">
                      {sub.user_exists ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                          <Check className="w-3 h-3" />
                          Active User
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-amber-100 text-amber-700">
                          <X className="w-3 h-3" />
                          No User
                        </span>
                      )}
                  </td>
                    <td className="px-4 lg:px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      sub.plan === 'free' ? 'bg-gray-100 text-gray-700' :
                      sub.plan === 'starter' ? 'bg-blue-100 text-blue-700' :
                      sub.plan === 'plus' ? 'bg-purple-100 text-purple-700' :
                      sub.plan === 'pro' ? 'bg-green-100 text-green-700' :
                      'bg-amber-100 text-amber-700'
                    }`}>
                      {sub.plan}
                    </span>
                  </td>
                    <td className="px-4 lg:px-6 py-4">
                    <div className="flex items-center gap-2">
                      {sub.status === 'active' ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <X className="w-4 h-4 text-red-600" />
                      )}
                      <span className={`text-sm font-medium ${
                        sub.status === 'active' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {sub.status}
                      </span>
                    </div>
                  </td>
                    <td className="px-4 lg:px-6 py-4 text-sm text-gray-600">
                    {new Date(sub.created_at).toLocaleDateString()}
                  </td>
                    <td className="px-4 lg:px-6 py-4 text-sm text-gray-600 font-mono">
                    {sub.stripe_subscription_id?.substring(0, 20)}...
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>
      
      {/* Subscriptions Cards - Mobile */}
      <div className="md:hidden space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : subscriptions.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-gray-500">No subscriptions found</p>
          </div>
        ) : (
          subscriptions.map((sub) => (
            <div 
              key={sub.id} 
              className={`bg-white rounded-xl border border-gray-200 p-4 ${
                sub.is_orphaned ? 'border-amber-300 bg-amber-50' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-dark truncate">{sub.user_email}</span>
                    {!sub.user_exists && (
                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    )}
                  </div>
                  {sub.user_name && (
                    <p className="text-xs text-gray-500">{sub.user_name}</p>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Plan</p>
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    sub.plan === 'free' ? 'bg-gray-100 text-gray-700' :
                    sub.plan === 'starter' ? 'bg-blue-100 text-blue-700' :
                    sub.plan === 'plus' ? 'bg-purple-100 text-purple-700' :
                    sub.plan === 'pro' ? 'bg-green-100 text-green-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {sub.plan}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Status</p>
                  <div className="flex items-center gap-1">
                    {sub.status === 'active' ? (
                      <Check className="w-3 h-3 text-green-600" />
                    ) : (
                      <X className="w-3 h-3 text-red-600" />
                    )}
                    <span className={`text-xs font-medium ${
                      sub.status === 'active' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {sub.status}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-gray-500 mb-1">User Account</p>
                  {sub.user_exists ? (
                    <span className="inline-flex items-center gap-1 text-green-700">
                      <Check className="w-3 h-3" />
                      Exists
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-amber-700">
                      <X className="w-3 h-3" />
                      Missing
                    </span>
                  )}
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Created</p>
                  <p className="text-dark">{new Date(sub.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Stripe ID</p>
                <p className="text-xs font-mono text-gray-600 truncate">{sub.stripe_subscription_id}</p>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Summary */}
      {!loading && subscriptions.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          Showing {subscriptions.length} subscriptions
          {stats?.by_status && (
            <span className="ml-2">
              ({Object.entries(stats.by_status).map(([status, count]) => `${count} ${status}`).join(', ')})
            </span>
          )}
        </div>
      )}
    </div>
  );
}

