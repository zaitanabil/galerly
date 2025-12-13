import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Mail, Phone, Calendar, DollarSign, TrendingUp, Filter, Search, ChevronRight } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface Lead {
  id: string;
  name: string;
  email: string;
  phone?: string;
  service_type?: string;
  budget?: string;
  timeline?: string;
  message?: string;
  source: string;
  score: number;
  quality: string;
  status: string;
  created_at: string;
  last_contacted?: string;
}

export default function CRMPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      const response = await api.get('/leads');
      if (response.success && response.data) {
        setLeads(response.data.leads || []);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Lead Management is a Pro/Ultimate feature');
      } else {
        toast.error('Failed to load leads');
      }
    } finally {
      setLoading(false);
    }
  };

  const getQualityBadge = (quality: string, score: number) => {
    const badges = {
      hot: { color: 'bg-red-100 text-red-800 border-red-200', label: 'Hot' },
      warm: { color: 'bg-orange-100 text-orange-800 border-orange-200', label: 'Warm' },
      cold: { color: 'bg-blue-100 text-blue-800 border-blue-200', label: 'Cold' }
    };
    
    const badge = badges[quality as keyof typeof badges] || badges.cold;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
        {badge.label} ({score})
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      new: { color: 'bg-purple-100 text-purple-800', label: 'New' },
      contacted: { color: 'bg-blue-100 text-blue-800', label: 'Contacted' },
      qualified: { color: 'bg-green-100 text-green-800', label: 'Qualified' },
      converted: { color: 'bg-emerald-100 text-emerald-800', label: 'Converted' },
      lost: { color: 'bg-gray-100 text-gray-800', label: 'Lost' }
    };
    
    const badge = badges[status as keyof typeof badges] || badges.new;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  const filteredLeads = leads.filter(lead => {
    if (filterStatus !== 'all' && lead.status !== filterStatus) return false;
    if (searchQuery && !lead.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !lead.email.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Statistics
  const stats = {
    total: leads.length,
    hot: leads.filter(l => l.quality === 'hot').length,
    warm: leads.filter(l => l.quality === 'warm').length,
    converted: leads.filter(l => l.status === 'converted').length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading leads...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Dashboard</Link>
              <Link to="/leads" className="text-sm font-medium text-[#1D1D1F]">CRM</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Lead Management</h1>
            <p className="text-[#1D1D1F]/60">Manage and track your photography leads</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Leads', value: stats.total, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: 'Hot Leads', value: stats.hot, icon: TrendingUp, color: 'text-red-600', bg: 'bg-red-50' },
            { label: 'Warm Leads', value: stats.warm, icon: Mail, color: 'text-orange-600', bg: 'bg-orange-50' },
            { label: 'Converted', value: stats.converted, icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50' }
          ].map((stat, i) => (
            <div key={i} className="bg-white p-5 rounded-3xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">{stat.label}</span>
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-3xl font-medium text-[#1D1D1F]">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white rounded-3xl border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search leads by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="converted">Converted</option>
                <option value="lost">Lost</option>
              </select>
            </div>
          </div>
        </div>

        {/* Leads List */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
          {filteredLeads.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No leads yet</h3>
              <p className="text-[#1D1D1F]/60">Leads from your portfolio and booking requests will appear here.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filteredLeads.map((lead) => (
                <div key={lead.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F] group-hover:text-[#0066CC]">
                          {lead.name}
                        </h3>
                        {getQualityBadge(lead.quality, lead.score)}
                        {getStatusBadge(lead.status)}
                      </div>
                      
                      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-[#1D1D1F]/60 mb-3">
                        <div className="flex items-center gap-1.5">
                          <Mail className="w-4 h-4" />
                          {lead.email}
                        </div>
                        {lead.phone && (
                          <div className="flex items-center gap-1.5">
                            <Phone className="w-4 h-4" />
                            {lead.phone}
                          </div>
                        )}
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-4 h-4" />
                          {new Date(lead.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      
                      {lead.message && (
                        <p className="text-sm text-[#1D1D1F]/70 line-clamp-2 mb-3">{lead.message}</p>
                      )}
                      
                      <div className="flex gap-2">
                        {lead.service_type && (
                          <span className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                            {lead.service_type}
                          </span>
                        )}
                        {lead.budget && (
                          <span className="px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">
                            {lead.budget}
                          </span>
                        )}
                        {lead.timeline && (
                          <span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                            {lead.timeline}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <button className="p-2 text-[#1D1D1F]/40 hover:text-[#0066CC] hover:bg-blue-50 rounded-full transition-all opacity-0 group-hover:opacity-100">
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
