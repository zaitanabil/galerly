// CRM Dashboard Page - Lead and client management
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users, TrendingUp, Star, Clock, Phone, Mail, Calendar,
  Tag, Settings, LogOut, Filter, Search, Plus, MessageSquare
} from 'lucide-react';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';

interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string;
  service_type: string;
  budget: string;
  timeline: string;
  message: string;
  status: string;
  quality: 'hot' | 'warm' | 'cold' | 'low';
  score: number;
  created_at: string;
  last_contacted_at?: string;
  follow_up_count: number;
  tags: string[];
  notes: Array<{ id: string; text: string; created_at: string }>;
}

interface Stats {
  total: number;
  hot: number;
  warm: number;
  new: number;
}

export default function CRMPage() {
  const { logout } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, hot: 0, warm: 0, new: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  useEffect(() => {
    fetchLeads();
  }, [filter]);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      // Build query string for filters
      const queryParams = new URLSearchParams({ limit: '100' });
      
      if (filter !== 'all') {
        if (['hot', 'warm', 'cold'].includes(filter)) {
          queryParams.append('quality', filter);
        } else {
          queryParams.append('status', filter);
        }
      }

      const response = await api.get(`/crm/leads?${queryParams.toString()}`);
      if (response.success) {
        setLeads(response.data.leads || []);
        setStats(response.data.stats || { total: 0, hot: 0, warm: 0, new: 0 });
      }
    } catch (error) {
      console.error('Error fetching leads:', error);
      toast.error('Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'hot': return 'bg-red-100 text-red-700 border-red-200';
      case 'warm': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'cold': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const filteredLeads = leads.filter(lead =>
    search === '' ||
    lead.name.toLowerCase().includes(search.toLowerCase()) ||
    lead.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Dashboard</Link>
              <Link to="/crm" className="text-sm font-medium text-[#1D1D1F]">CRM</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Analytics</Link>
              <Link to="/billing" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Billing</Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full transition-all">
              <Settings className="w-5 h-5" />
            </Link>
            <button onClick={logout} className="p-2 text-[#1D1D1F]/60 hover:text-red-600 hover:bg-red-50 rounded-full transition-all">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">CRM & Leads</h1>
            <p className="text-[#1D1D1F]/60">Manage your client pipeline and relationships</p>
          </div>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full hover:bg-black transition-all">
            <Plus className="w-4 h-4" />
            Request Testimonial
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                <Users className="w-5 h-5 text-[#0066CC]" />
              </div>
              <span className="text-2xl font-bold text-[#1D1D1F]">{stats.total}</span>
            </div>
            <p className="text-sm text-[#1D1D1F]/60">Total Leads</p>
          </div>

          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-red-600" />
              </div>
              <span className="text-2xl font-bold text-[#1D1D1F]">{stats.hot}</span>
            </div>
            <p className="text-sm text-[#1D1D1F]/60">Hot Leads</p>
          </div>

          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center">
                <Star className="w-5 h-5 text-orange-600" />
              </div>
              <span className="text-2xl font-bold text-[#1D1D1F]">{stats.warm}</span>
            </div>
            <p className="text-sm text-[#1D1D1F]/60">Warm Leads</p>
          </div>

          <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
                <Clock className="w-5 h-5 text-green-600" />
              </div>
              <span className="text-2xl font-bold text-[#1D1D1F]">{stats.new}</span>
            </div>
            <p className="text-sm text-[#1D1D1F]/60">New This Week</p>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="glass-panel p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
              <input
                type="text"
                placeholder="Search leads by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-[#1D1D1F]/60" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
              >
                <option value="all">All Leads</option>
                <option value="hot">Hot</option>
                <option value="warm">Warm</option>
                <option value="cold">Cold</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
              </select>
            </div>
          </div>
        </div>

        {/* Leads Table */}
        <div className="glass-panel p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-sm text-[#1D1D1F]/60">Loading leads...</p>
            </div>
          ) : filteredLeads.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-[#1D1D1F]/20 mx-auto mb-4" />
              <p className="text-[#1D1D1F]/60">No leads found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Lead</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Service</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Quality</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Score</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Status</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Created</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[#1D1D1F]/40 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLeads.map((lead) => (
                    <tr
                      key={lead.id}
                      className="border-b border-gray-50 hover:bg-blue-50/20 transition-colors cursor-pointer"
                      onClick={() => setSelectedLead(lead)}
                    >
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-[#1D1D1F]">{lead.name}</p>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-xs text-[#1D1D1F]/60 flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              {lead.email}
                            </span>
                            {lead.phone && (
                              <span className="text-xs text-[#1D1D1F]/60 flex items-center gap-1">
                                <Phone className="w-3 h-3" />
                                {lead.phone}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-[#1D1D1F] capitalize">{lead.service_type || 'Not specified'}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getQualityColor(lead.quality)}`}>
                          {lead.quality.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-100 rounded-full h-2">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
                              style={{ width: `${lead.score}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-[#1D1D1F]">{lead.score}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-[#1D1D1F] capitalize">{lead.status}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-1 text-xs text-[#1D1D1F]/60">
                          <Calendar className="w-3 h-3" />
                          {new Date(lead.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedLead(lead);
                          }}
                          className="text-[#0066CC] hover:text-[#0052A3] text-sm font-medium"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Lead Detail Modal */}
        {selectedLead && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-2xl font-medium text-[#1D1D1F]">{selectedLead.name}</h2>
                    <div className="flex items-center gap-4 mt-2">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getQualityColor(selectedLead.quality)}`}>
                        {selectedLead.quality.toUpperCase()} - Score: {selectedLead.score}/100
                      </span>
                      <span className="text-sm text-[#1D1D1F]/60 capitalize">{selectedLead.status}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedLead(null)}
                    className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase mb-3">Contact Information</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-[#1D1D1F]/40" />
                      <span className="text-[#1D1D1F]">{selectedLead.email}</span>
                    </div>
                    {selectedLead.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-[#1D1D1F]/40" />
                        <span className="text-[#1D1D1F]">{selectedLead.phone}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase mb-3">Inquiry Details</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-[#1D1D1F]/60 mb-1">Service Type</p>
                      <p className="text-[#1D1D1F] capitalize">{selectedLead.service_type || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-[#1D1D1F]/60 mb-1">Budget</p>
                      <p className="text-[#1D1D1F]">{selectedLead.budget || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-[#1D1D1F]/60 mb-1">Timeline</p>
                      <p className="text-[#1D1D1F] capitalize">{selectedLead.timeline?.replace('_', ' ') || 'Not specified'}</p>
                    </div>
                    <div>
                      <p className="text-[#1D1D1F]/60 mb-1">Follow-ups</p>
                      <p className="text-[#1D1D1F]">{selectedLead.follow_up_count || 0} sent</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase mb-3">Message</h3>
                  <p className="text-[#1D1D1F] leading-relaxed">{selectedLead.message}</p>
                </div>

                {selectedLead.tags && selectedLead.tags.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase mb-3">Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedLead.tags.map((tag, idx) => (
                        <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                          <Tag className="w-3 h-3" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedLead.notes && selectedLead.notes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase mb-3">Notes</h3>
                    <div className="space-y-3">
                      {selectedLead.notes.map((note) => (
                        <div key={note.id} className="bg-gray-50 rounded-xl p-4">
                          <p className="text-[#1D1D1F] text-sm mb-2">{note.text}</p>
                          <p className="text-xs text-[#1D1D1F]/40">{new Date(note.created_at).toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-3 pt-4 border-t border-gray-100">
                  <button className="flex-1 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all flex items-center justify-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    Send Follow-up
                  </button>
                  <button className="px-6 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-50 transition-all">
                    Add Note
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
