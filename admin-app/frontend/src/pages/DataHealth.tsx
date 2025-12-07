import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Trash2, RefreshCw } from 'lucide-react';
import adminAPI from '../services/api';

export default function DataHealth() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadHealth();
  }, []);
  
  const loadHealth = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5002/api/data-health');
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error('Error loading data health:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (!health) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Failed to load data health</p>
      </div>
    );
  }
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'red';
      case 'medium': return 'amber';
      case 'low': return 'yellow';
      default: return 'gray';
    }
  };
  
  return (
    <div>
      {/* Header */}
      <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-dark">Data Health</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">Database integrity and consistency checks</p>
        </div>
        <button
          onClick={loadHealth}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors w-full sm:w-auto"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      
      {/* Health Score */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row items-center sm:justify-between gap-4">
          <div className="text-center sm:text-left">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Overall Health Score</h3>
            <div className="flex items-center justify-center sm:justify-start gap-3">
              <div className="text-4xl sm:text-5xl font-bold text-dark">{health.health_score}</div>
              <div className="text-xl sm:text-2xl text-gray-500">/100</div>
            </div>
          </div>
          <div className={`w-24 h-24 sm:w-32 sm:h-32 rounded-full flex items-center justify-center ${
            health.health_score >= 90 ? 'bg-green-100' :
            health.health_score >= 70 ? 'bg-amber-100' :
            'bg-red-100'
          }`}>
            {health.health_score >= 90 ? (
              <CheckCircle className="w-12 h-12 sm:w-16 sm:h-16 text-green-600" />
            ) : health.health_score >= 70 ? (
              <AlertTriangle className="w-12 h-12 sm:w-16 sm:h-16 text-amber-600" />
            ) : (
              <XCircle className="w-12 h-12 sm:w-16 sm:h-16 text-red-600" />
            )}
          </div>
        </div>
      </div>
      
      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Total Issues</p>
          <p className="text-2xl font-bold text-dark mt-1">{health.total_issues}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Orphaned Subscriptions</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{health.summary.orphaned_subscriptions}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Duplicate Emails</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{health.summary.duplicate_emails}</p>
        </div>
      </div>
      
      {/* Issues List */}
      {health.total_issues === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-green-900 mb-2">All Systems Healthy</h3>
          <p className="text-green-700">No data integrity issues detected</p>
        </div>
      ) : (
        <div className="space-y-6">
          {health.issues.map((issue: any, index: number) => {
            const color = getSeverityColor(issue.severity);
            return (
              <div key={index} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4 sm:p-6`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <AlertTriangle className={`w-5 h-5 sm:w-6 sm:h-6 text-${color}-600 mt-0.5 flex-shrink-0`} />
                    <div className="min-w-0 flex-1">
                      <h3 className={`text-base sm:text-lg font-semibold text-${color}-900 mb-1`}>
                        {issue.type.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </h3>
                      <p className={`text-sm text-${color}-700`}>{issue.description}</p>
                      <p className={`text-xs text-${color}-600 mt-1`}>
                        Severity: {issue.severity.toUpperCase()} • Count: {issue.count}
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Issue Items */}
                <div className="mt-4 space-y-2">
                  {issue.items.slice(0, 5).map((item: any, itemIndex: number) => (
                    <div key={itemIndex} className={`bg-white border border-${color}-200 rounded-lg p-3 sm:p-4`}>
                      {issue.type === 'orphaned_subscriptions' && (
                        <div className="space-y-2 text-xs sm:text-sm">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                            <div className="truncate">
                              <span className="text-gray-500">Email:</span>
                              <span className="ml-2 font-medium">{item.user_email}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Plan:</span>
                              <span className="ml-2 font-medium">{item.plan}</span>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                            <div>
                              <span className="text-gray-500">Status:</span>
                              <span className="ml-2 font-medium">{item.status}</span>
                            </div>
                            <div className="truncate">
                              <span className="text-gray-500">Stripe ID:</span>
                              <span className="ml-2 font-mono text-xs">{item.stripe_subscription_id?.substring(0, 15)}...</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Missing User ID:</span>
                            <span className="ml-2 font-mono text-xs break-all">{item.user_id}</span>
                          </div>
                        </div>
                      )}
                      
                      {issue.type === 'duplicate_email_subscriptions' && (
                        <div className="text-xs sm:text-sm">
                          <div className="mb-2">
                            <span className="text-gray-500">Email:</span>
                            <span className="ml-2 font-medium break-all">{item.email}</span>
                            <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-${color}-100 text-${color}-700`}>
                              {item.count} subscriptions
                            </span>
                          </div>
                          <div className="ml-2 sm:ml-4 mt-2 space-y-1">
                            {item.subscriptions.map((sub: any, subIndex: number) => (
                              <div key={subIndex} className="text-xs text-gray-600 break-all">
                                • {sub.plan} ({sub.status}) - User: {sub.user_id?.substring(0, 8)}...
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {issue.type === 'orphaned_billing_records' && (
                        <div className="space-y-2 text-xs sm:text-sm">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                            <div>
                              <span className="text-gray-500">Amount:</span>
                              <span className="ml-2 font-medium">${item.amount}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Plan:</span>
                              <span className="ml-2 font-medium">{item.plan}</span>
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-500">Invoice:</span>
                            <span className="ml-2 font-mono text-xs break-all">{item.stripe_invoice_id}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Missing User ID:</span>
                            <span className="ml-2 font-mono text-xs break-all">{item.user_id}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {issue.items.length > 5 && (
                    <p className={`text-xs sm:text-sm text-${color}-600 mt-2`}>
                      ... and {issue.items.length - 5} more items
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
