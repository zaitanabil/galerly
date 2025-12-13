import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, Plus, User, Mail, Phone, CheckCircle, XCircle, Settings } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface Appointment {
  id: string;
  client_name: string;
  client_email: string;
  phone?: string;
  start_time: string;
  end_time: string;
  service_type: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  notes?: string;
  source?: string;
  created_at: string;
}

export default function SchedulerPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'list' | 'calendar'>('list');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      const response = await api.get('/appointments');
      if (response.success && response.data) {
        setAppointments(response.data.appointments || []);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Scheduler is an Ultimate plan feature');
      } else {
        toast.error('Failed to load appointments');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (appointmentId: string, newStatus: string) => {
    try {
      const response = await api.put(`/appointments/${appointmentId}`, { status: newStatus });
      if (response.success) {
        toast.success(`Appointment ${newStatus}`);
        loadAppointments();
      } else {
        toast.error('Failed to update appointment');
      }
    } catch (error) {
      toast.error('Failed to update appointment');
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: Clock },
      confirmed: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle },
      cancelled: { color: 'bg-gray-100 text-gray-800 border-gray-200', icon: XCircle }
    };
    
    const badge = badges[status as keyof typeof badges] || badges.pending;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
        <Icon className="w-3.5 h-3.5" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const groupedAppointments = appointments.reduce((acc, apt) => {
    const date = new Date(apt.start_time).toLocaleDateString();
    if (!acc[date]) acc[date] = [];
    acc[date].push(apt);
    return acc;
  }, {} as Record<string, Appointment[]>);

  const filteredAppointments = appointments.filter(apt => {
    if (filterStatus === 'all') return true;
    return apt.status === filterStatus;
  });

  const stats = {
    total: appointments.length,
    pending: appointments.filter(a => a.status === 'pending').length,
    confirmed: appointments.filter(a => a.status === 'confirmed').length,
    today: appointments.filter(a => {
      const aptDate = new Date(a.start_time).toDateString();
      const today = new Date().toDateString();
      return aptDate === today;
    }).length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading appointments...</p>
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
              <Link to="/scheduler" className="text-sm font-medium text-[#1D1D1F]">Scheduler</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
            </nav>
          </div>
          <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Scheduler</h1>
            <p className="text-[#1D1D1F]/60">Manage your appointments and bookings</p>
          </div>
          <div className="flex gap-3">
            <Link
              to="/availability/settings"
              className="flex items-center gap-2 px-5 py-2.5 bg-white text-[#1D1D1F] border border-gray-200 rounded-full text-sm font-medium hover:bg-gray-50"
            >
              <Settings className="w-4 h-4" />
              Availability
            </Link>
            <button className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black">
              <Plus className="w-4 h-4" />
              New Appointment
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total', value: stats.total, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: 'Today', value: stats.today, color: 'text-purple-600', bg: 'bg-purple-50' },
            { label: 'Pending', value: stats.pending, color: 'text-yellow-600', bg: 'bg-yellow-50' },
            { label: 'Confirmed', value: stats.confirmed, color: 'text-green-600', bg: 'bg-green-50' }
          ].map((stat, i) => (
            <div key={i} className="bg-white p-5 rounded-3xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">{stat.label}</span>
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <Calendar className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-3xl font-medium text-[#1D1D1F]">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* View Toggle & Filter */}
        <div className="bg-white rounded-3xl border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row justify-between gap-4">
            <div className="flex gap-2">
              <button
                onClick={() => setView('list')}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  view === 'list'
                    ? 'bg-[#1D1D1F] text-white'
                    : 'bg-gray-100 text-[#1D1D1F]/60 hover:bg-gray-200'
                }`}
              >
                List View
              </button>
              <button
                onClick={() => setView('calendar')}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  view === 'calendar'
                    ? 'bg-[#1D1D1F] text-white'
                    : 'bg-gray-100 text-[#1D1D1F]/60 hover:bg-gray-200'
                }`}
              >
                Calendar View
              </button>
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Appointments List */}
        {view === 'list' ? (
          <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
            {filteredAppointments.length === 0 ? (
              <div className="p-12 text-center">
                <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No appointments yet</h3>
                <p className="text-[#1D1D1F]/60 mb-6">Booking requests from your portfolio will appear here.</p>
                <button className="px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black">
                  Create First Appointment
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {Object.entries(groupedAppointments).map(([date, apts]) => (
                  <div key={date} className="p-6">
                    <h3 className="text-sm font-semibold text-[#1D1D1F]/40 uppercase tracking-wider mb-4">{date}</h3>
                    <div className="space-y-4">
                      {apts.map((apt) => (
                        <div key={apt.id} className="p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h4 className="text-lg font-medium text-[#1D1D1F]">{apt.client_name}</h4>
                                {getStatusBadge(apt.status)}
                              </div>
                              <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-[#1D1D1F]/60">
                                <div className="flex items-center gap-1.5">
                                  <Clock className="w-4 h-4" />
                                  {formatDateTime(apt.start_time)}
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <Mail className="w-4 h-4" />
                                  {apt.client_email}
                                </div>
                                {apt.phone && (
                                  <div className="flex items-center gap-1.5">
                                    <Phone className="w-4 h-4" />
                                    {apt.phone}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2 mb-3">
                            <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                              {apt.service_type}
                            </span>
                            {apt.source && (
                              <span className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-xs font-medium">
                                {apt.source}
                              </span>
                            )}
                          </div>
                          
                          {apt.notes && (
                            <p className="text-sm text-[#1D1D1F]/70 mb-3">{apt.notes}</p>
                          )}
                          
                          {apt.status === 'pending' && (
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleStatusUpdate(apt.id, 'confirmed')}
                                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700"
                              >
                                Confirm
                              </button>
                              <button
                                onClick={() => handleStatusUpdate(apt.id, 'cancelled')}
                                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-300"
                              >
                                Decline
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-gray-200 p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">Calendar View Coming Soon</h3>
            <p className="text-[#1D1D1F]/60">Interactive calendar with drag-and-drop will be available soon.</p>
          </div>
        )}
      </main>
    </div>
  );
}
