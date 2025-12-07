import { useEffect, useState } from 'react';
import { DollarSign, TrendingUp, CreditCard, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import adminAPI from '../services/api';

export default function Revenue() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const loadStats = async () => {
    try {
      const data = await adminAPI.getRevenueStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading revenue stats:', error);
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
  
  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Failed to load revenue stats</p>
      </div>
    );
  }
  
  // Prepare chart data
  const monthlyData = Object.entries(stats.monthly_revenue || {}).map(([month, revenue]) => ({
    month,
    revenue: Number(revenue),
  }));
  
  const planData = Object.entries(stats.revenue_by_plan || {}).map(([plan, revenue]) => ({
    plan,
    revenue: Number(revenue),
    transactions: stats.transactions_by_plan?.[plan] || 0,
  }));
  
  const hasHealthIssues = stats.health_issues?.orphaned_revenue > 0 || stats.health_issues?.orphaned_transactions > 0;
  
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark">Revenue Analytics</h1>
        <p className="text-gray-600 mt-1">Financial metrics and trends</p>
      </div>
      
      {/* Health Issues Alert */}
      {hasHealthIssues && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-amber-900">Revenue Data Issues</h3>
              <ul className="mt-2 space-y-1 text-sm text-amber-800">
                {stats.health_issues.orphaned_revenue > 0 && (
                  <li>• ${stats.health_issues.orphaned_revenue.toFixed(2)} in revenue from deleted user accounts</li>
                )}
                {stats.health_issues.orphaned_transactions > 0 && (
                  <li>• {stats.health_issues.orphaned_transactions} transaction(s) without valid user accounts</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            <h3 className="text-sm font-medium text-gray-600">Total Revenue</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">
            ${stats.total_revenue.toLocaleString()}
          </p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">All time</p>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-medium text-gray-600">Transactions</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">
            {stats.total_transactions.toLocaleString()}
          </p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">Total payments</p>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 sm:col-span-2 lg:col-span-1">
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="w-5 h-5 text-purple-600" />
            <h3 className="text-sm font-medium text-gray-600">Avg Transaction</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">
            ${(stats.total_revenue / stats.total_transactions || 0).toFixed(2)}
          </p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">Per payment</p>
        </div>
      </div>
      
      {/* Monthly Revenue Chart */}
      {monthlyData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 mb-6">
          <h3 className="text-base sm:text-lg font-semibold text-dark mb-4 sm:mb-6">Monthly Revenue</h3>
          <ResponsiveContainer width="100%" height={250} className="sm:h-[300px]">
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => `$${value}`} />
              <Bar dataKey="revenue" fill="#0066CC" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      
      {/* Revenue by Plan */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Revenue by Plan</h3>
        <div className="space-y-4">
          {planData.map(({ plan, revenue, transactions }) => (
            <div key={plan}>
              {/* Mobile Layout */}
              <div className="block sm:hidden">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  plan === 'free' ? 'bg-gray-100 text-gray-700' :
                  plan === 'starter' ? 'bg-blue-100 text-blue-700' :
                  plan === 'plus' ? 'bg-purple-100 text-purple-700' :
                  plan === 'pro' ? 'bg-green-100 text-green-700' :
                      plan === 'ultimate' ? 'bg-amber-100 text-amber-700' :
                      'bg-gray-100 text-gray-700'
                }`}>
                  {plan}
                </span>
              </div>
                  <span className="text-lg font-bold text-dark">
                    ${revenue.toLocaleString()}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mb-2">
                  {transactions} transaction{transactions !== 1 ? 's' : ''} • {((revenue / stats.total_revenue) * 100).toFixed(1)}%
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${(revenue / stats.total_revenue) * 100}%` }}
                  />
                </div>
              </div>
              
              {/* Desktop Layout */}
              <div className="hidden sm:flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    plan === 'free' ? 'bg-gray-100 text-gray-700' :
                    plan === 'starter' ? 'bg-blue-100 text-blue-700' :
                    plan === 'plus' ? 'bg-purple-100 text-purple-700' :
                    plan === 'pro' ? 'bg-green-100 text-green-700' :
                    plan === 'ultimate' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {plan}
                  </span>
                  <span className="text-sm text-gray-500">
                    {transactions} transaction{transactions !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32 md:w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${(revenue / stats.total_revenue) * 100}%` }}
                    />
                  </div>
                  <span className="text-lg font-bold text-dark w-20 md:w-24 text-right">
                  ${revenue.toLocaleString()}
                </span>
                  <span className="text-sm text-gray-500 w-12 md:w-16 text-right">
                  {((revenue / stats.total_revenue) * 100).toFixed(1)}%
                </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

