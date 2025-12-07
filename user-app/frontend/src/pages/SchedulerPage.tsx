import { useState, useEffect } from 'react';
import { Plus, Calendar as CalendarIcon, Clock, User, Trash2, X, Download } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useBrandedModal } from '../components/BrandedModal';

interface Appointment {
  id: string;
  client_name: string;
  client_email: string;
  service_type: string;
  start_time: string;
  end_time: string;
  status: 'confirmed' | 'cancelled' | 'pending';
  notes: string;
  source?: string;
}

export default function SchedulerPage() {
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New Appointment Form
  const [newAppt, setNewAppt] = useState({
    client_name: '',
    client_email: '',
    service_type: 'Portrait Session',
    date: '',
    time: '',
    duration: 60, // minutes
    notes: ''
  });

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const response = await api.get('/appointments');
      setAppointments(response.data.appointments);
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const generateICS = (appointment: Appointment) => {
    const formatTime = (dateStr: string) => {
        return dateStr.replace(/[-:]/g, '').split('.')[0] + 'Z';
    };
    
    const start = formatTime(appointment.start_time);
    const end = formatTime(appointment.end_time);
    
    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Galerly//Scheduler//EN
BEGIN:VEVENT
UID:${appointment.id}@galerly.com
DTSTAMP:${formatTime(new Date().toISOString())}
DTSTART:${start}
DTEND:${end}
SUMMARY:${appointment.service_type} with ${appointment.client_name}
DESCRIPTION:${appointment.notes || ''}
STATUS:${appointment.status.toUpperCase()}
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.setAttribute('download', `appointment-${appointment.id}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCreateAppointment = async () => {
    try {
      if (!newAppt.client_email || !newAppt.date || !newAppt.time) {
        toast.error('Please fill in required fields');
        return;
      }

      // Calculate ISO start/end times
      const startDateTime = new Date(`${newAppt.date}T${newAppt.time}`);
      const endDateTime = new Date(startDateTime.getTime() + newAppt.duration * 60000);

      const payload = {
        client_name: newAppt.client_name,
        client_email: newAppt.client_email,
        service_type: newAppt.service_type,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        notes: newAppt.notes
      };

      const response = await api.post('/appointments', payload);
      
      if (response.success) {
        toast.success('Appointment scheduled');
        setShowCreateModal(false);
        fetchAppointments();
        setNewAppt({
          client_name: '',
          client_email: '',
          service_type: 'Portrait Session',
          date: '',
          time: '',
          duration: 60,
          notes: ''
        });
      } else {
        toast.error(response.error || 'Failed to schedule appointment');
      }
    } catch (error) {
      console.error('Error creating appointment:', error);
      toast.error('An unexpected error occurred');
    }
  };

  const handleUpdateStatus = async (id: string, status: 'confirmed' | 'cancelled') => {
    try {
      await api.put(`/appointments/${id}`, { status });
      toast.success(`Appointment ${status}`);
      setAppointments(prev => prev.map(a => a.id === id ? { ...a, status } : a));
    } catch (error) {
      console.error('Error updating appointment:', error);
      toast.error('Failed to update status');
    }
  };

  // Group appointments by date for list view
  const groupedAppointments = appointments.reduce((acc, appt) => {
    const date = new Date(appt.start_time).toLocaleDateString();
    if (!acc[date]) acc[date] = [];
    acc[date].push(appt);
    return acc;
  }, {} as Record<string, Appointment[]>);

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <Header />
      
      <main className="pt-24 pb-20 px-4 md:px-6 max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-[#1D1D1F]">Scheduler</h1>
            <p className="text-[#1D1D1F]/60 mt-1">Manage your photography sessions</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full hover:bg-black transition-colors"
          >
            <Plus className="w-4 h-4" /> New Appointment
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upcoming List */}
          <div className="lg:col-span-2 space-y-6">
            {loading ? (
              <div className="text-center py-12 text-gray-400">Loading schedule...</div>
            ) : Object.keys(groupedAppointments).length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-gray-100">
                <CalendarIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900">No appointments scheduled</h3>
                <p className="text-gray-500 mt-2">Get started by adding a new session.</p>
              </div>
            ) : (
              Object.entries(groupedAppointments).sort().map(([date, dayAppts]) => (
                <div key={date} className="bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm">
                  <div className="bg-gray-50/50 px-6 py-3 border-b border-gray-100 font-medium text-[#1D1D1F]">
                    {new Date(dayAppts[0].start_time).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                  </div>
                  <div className="divide-y divide-gray-100">
                    {dayAppts.map(appt => (
                      <div key={appt.id} className={`p-6 flex items-start gap-4 transition-colors ${appt.status === 'pending' ? 'bg-yellow-50/50' : 'hover:bg-gray-50/30'}`}>
                        <div className="flex-shrink-0 w-16 text-center">
                          <div className="text-lg font-bold text-[#1D1D1F]">
                            {new Date(appt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                          <div className="text-xs text-gray-500 uppercase">
                            {new Date(appt.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-[#1D1D1F] text-lg">{appt.service_type}</h3>
                            {appt.status === 'pending' && (
                                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium">Pending Request</span>
                            )}
                            {appt.status === 'cancelled' && (
                                <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full font-medium">Cancelled</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-gray-600 mt-1">
                            <User className="w-4 h-4" />
                            <span>{appt.client_name || 'No Name'}</span>
                            <span className="text-gray-400">•</span>
                            <span className="text-sm">{appt.client_email}</span>
                          </div>
                          {appt.notes && (
                            <p className="mt-2 text-sm text-gray-500 bg-white/50 p-2 rounded-lg inline-block">
                              {appt.notes}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                            <button 
                                onClick={() => generateICS(appt)}
                                className="p-2 text-gray-400 hover:text-[#1D1D1F] hover:bg-gray-100 rounded-full transition-colors"
                                title="Export to Calendar"
                            >
                                <Download className="w-4 h-4" />
                            </button>
                            {appt.status === 'pending' && (
                                <button 
                                    onClick={() => handleUpdateStatus(appt.id, 'confirmed')}
                                    className="px-3 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded-full text-sm font-medium transition-colors"
                                >
                                    Confirm
                                </button>
                            )}
                            {appt.status !== 'cancelled' && (
                                <button 
                                onClick={async () => {
                                    const confirmed = await showConfirm(
                                      'Cancel Appointment',
                                      'Cancel this appointment?',
                                      'Cancel Appointment',
                                      'Keep Appointment',
                                      'danger'
                                    );
                                    if(confirmed) handleUpdateStatus(appt.id, 'cancelled');
                                }}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                                title="Cancel Appointment"
                                >
                                <Trash2 className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Mini Calendar / Summary Side */}
          <div className="lg:col-span-1">
             <div className="bg-[#1D1D1F] text-white rounded-3xl p-6 shadow-xl sticky top-24">
               <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                 <Clock className="w-5 h-5" /> Quick Stats
               </h3>
               <div className="space-y-4">
                 <div className="bg-white/10 rounded-2xl p-4">
                   <div className="text-sm opacity-60">Total Appointments</div>
                   <div className="text-2xl font-bold">{appointments.length}</div>
                 </div>
                 <div className="bg-white/10 rounded-2xl p-4">
                   <div className="text-sm opacity-60">Upcoming This Week</div>
                   <div className="text-2xl font-bold">
                     {appointments.filter(a => {
                       const d = new Date(a.start_time);
                       const now = new Date();
                       const nextWeek = new Date();
                       nextWeek.setDate(now.getDate() + 7);
                       return d >= now && d <= nextWeek;
                     }).length}
                   </div>
                 </div>
               </div>
               
               <div className="mt-8 pt-8 border-t border-white/10">
                 <p className="text-sm opacity-60 leading-relaxed">
                   Sync your appointments with Google Calendar or iCal coming soon in the next update.
                 </p>
               </div>
             </div>
          </div>
        </div>
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl w-full max-w-lg shadow-2xl">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center">
              <h2 className="text-xl font-bold text-[#1D1D1F]">Schedule Session</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Type</label>
                <select
                  value={newAppt.service_type}
                  onChange={e => setNewAppt({...newAppt, service_type: e.target.value})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200"
                >
                  <option>Portrait Session</option>
                  <option>Wedding Consultation</option>
                  <option>Family Shoot</option>
                  <option>Event Coverage</option>
                  <option>Commercial Shoot</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input
                    type="date"
                    value={newAppt.date}
                    onChange={e => setNewAppt({...newAppt, date: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                  <input
                    type="time"
                    value={newAppt.time}
                    onChange={e => setNewAppt({...newAppt, time: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  value={newAppt.duration}
                  onChange={e => setNewAppt({...newAppt, duration: Number(e.target.value)})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Name</label>
                  <input
                    type="text"
                    value={newAppt.client_name}
                    onChange={e => setNewAppt({...newAppt, client_name: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Email *</label>
                  <input
                    type="email"
                    value={newAppt.client_email}
                    onChange={e => setNewAppt({...newAppt, client_email: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={newAppt.notes}
                  onChange={e => setNewAppt({...newAppt, notes: e.target.value})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  rows={3}
                />
              </div>

              <button
                onClick={handleCreateAppointment}
                className="w-full py-3 bg-[#1D1D1F] text-white rounded-full font-bold hover:bg-black transition-all mt-2"
              >
                Confirm Booking
              </button>
            </div>
          </div>
        </div>
      )}

      <Footer />

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}

