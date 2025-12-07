import { useEffect, useState } from 'react';
import { Users, Image, CreditCard, DollarSign, TrendingUp, Calendar } from 'lucide-react';
import { 
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import adminAPI from '../services/api';

const COLORS = {
  free: '#9CA3AF',
  starter: '#3B82F6',
  plus: '#8B5CF6',
  pro: '#10B981',
  ultimate: '#F59E0B',
  active: '#10B981',
  canceled: '#EF4444',
  monthly: '#3B82F6',
  annual: '#8B5CF6'
};

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const loadStats = async () => {
    try {
      const data = await adminAPI.getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
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
        <p className="text-gray-500">Failed to load dashboard stats</p>
      </div>
    );
  }
  
  // Prepare chart data
  const planDistributionData = Object.entries(stats.subscriptions_by_plan || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: Number(value),
    color: COLORS[name as keyof typeof COLORS] || COLORS.free
  }));
  
  const statusBreakdownData = [
    { name: 'Active', value: stats.active_subscriptions, color: COLORS.active },
    { name: 'Canceled', value: stats.canceled_subscriptions, color: COLORS.canceled }
  ];
  
  const billingIntervalData = [
    { name: 'Monthly', value: stats.monthly_subscriptions, color: COLORS.monthly },
    { name: 'Annual', value: stats.annual_subscriptions, color: COLORS.annual }
  ];
  
  const planComparisonData = ['starter', 'plus', 'pro', 'ultimate'].map(plan => ({
    plan: plan.charAt(0).toUpperCase() + plan.slice(1),
    active: stats.active_by_plan?.[plan] || 0,
    canceled: stats.canceled_by_plan?.[plan] || 0,
    monthly: stats.monthly_by_plan?.[plan] || 0,
    annual: stats.annual_by_plan?.[plan] || 0
  }));
  
  const monthlyRevenueData = Object.entries(stats.monthly_revenue_trend || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-6)
    .map(([month, revenue]) => ({
      month: new Date(month + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      revenue: Number(revenue)
    }));
  
  return (
    <div>
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-dark">Dashboard</h1>
        <p className="text-sm sm:text-base text-gray-600 mt-1">Platform overview and analytics</p>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-5 h-5 text-blue-600" />
            <h3 className="text-xs sm:text-sm font-medium text-gray-600">Total Users</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">{stats.total_users}</p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            {stats.total_photographers} photographers, {stats.total_clients} clients
          </p>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <Image className="w-5 h-5 text-purple-600" />
            <h3 className="text-xs sm:text-sm font-medium text-gray-600">Content</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">{stats.total_galleries}</p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            {stats.total_photos.toLocaleString()} photos
          </p>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="w-5 h-5 text-green-600" />
            <h3 className="text-xs sm:text-sm font-medium text-gray-600">Subscriptions</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">{stats.total_subscriptions}</p>
          <p className="text-xs sm:text-sm text-green-600 mt-1">
            {stats.active_subscriptions} active
          </p>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="w-5 h-5 text-amber-600" />
            <h3 className="text-xs sm:text-sm font-medium text-gray-600">MRR</h3>
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-dark">
            ${stats.monthly_recurring_revenue.toLocaleString()}
          </p>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            ${stats.annual_recurring_revenue.toLocaleString()} ARR
          </p>
        </div>
      </div>
      
      {/* Revenue Trend */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp className="w-5 h-5 text-primary" />
          <h3 className="text-base sm:text-lg font-semibold text-dark">Revenue Trend (Last 6 Months)</h3>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={monthlyRevenueData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => `$${value}`} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="revenue" 
              stroke={COLORS.ultimate} 
              strokeWidth={2}
              name="Revenue"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Subscription Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Status Breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Subscription Status</h3>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={statusBreakdownData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1">
              <div className="space-y-3">
                {statusBreakdownData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-gray-600">{item.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-dark">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Billing Interval */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Billing Interval</h3>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={billingIntervalData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {billingIntervalData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1">
              <div className="space-y-3">
                {billingIntervalData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-gray-600">{item.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-dark">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Plan Distribution */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 mb-6">
        <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Subscriptions by Plan</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={planDistributionData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {planDistributionData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      {/* Plan Comparison */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6 mb-6">
        <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Active vs Canceled by Plan</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={planComparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="plan" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="active" fill={COLORS.active} name="Active" />
            <Bar dataKey="canceled" fill={COLORS.canceled} name="Canceled" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Billing Interval by Plan */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-dark mb-4">Monthly vs Annual by Plan</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={planComparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="plan" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="monthly" fill={COLORS.monthly} name="Monthly" />
            <Bar dataKey="annual" fill={COLORS.annual} name="Annual" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
