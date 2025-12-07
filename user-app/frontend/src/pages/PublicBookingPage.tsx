import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Clock, Mail, Check, Calendar } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import AvailabilityCalendar from '../components/AvailabilityCalendar';
import { api } from '../utils/api';
import { useBrandedModal } from '../components/BrandedModal';

interface Photographer {
  name: string;
  business_name?: string;
  email: string;
}

export default function PublicBookingPage() {
  const { userId } = useParams<{ userId: string }>();
  const { showAlert, ModalComponent } = useBrandedModal();
  const [photographer, setPhotographer] = useState<Photographer | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    client_name: '',
    client_email: '',
    service_type: 'Portrait Session',
    notes: ''
  });
  
  const [selectedSlot, setSelectedSlot] = useState<{ start: string; end: string } | null>(null);

  const loadPhotographer = useCallback(async () => {
    if (!userId) return;
    try {
      const response = await api.get<Photographer>(`/photographers/${userId}`);
      if (response.success && response.data) {
        setPhotographer(response.data);
      } else {
        setError('Photographer not found');
      }
    } catch (err) {
      console.error('Error loading photographer:', err);
      setError('Failed to load booking page');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadPhotographer();
  }, [loadPhotographer]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId) return;

    try {
      // Calculate ISO start/end times
      const startDateTime = new Date(`${formData.date}T${formData.time}`);
      const endDateTime = new Date(startDateTime.getTime() + formData.duration * 60000);

      const payload = {
        client_name: formData.client_name,
        client_email: formData.client_email,
        service_type: formData.service_type,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        notes: formData.notes
      };

      const response = await api.post(`/public/photographers/${userId}/appointments`, payload);
      
      if (response.success) {
        setSubmitted(true);
      } else {
        await showAlert('Error', response.error || 'Failed to submit booking request', 'error');
      }
    } catch (error) {
      console.error('Error submitting booking:', error);
      await showAlert('Error', 'An error occurred. Please try again.', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !photographer) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-gray-600 mb-4">{error || 'Photographer not found'}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#F5F5F7]">
        <Header />
        <main className="pt-32 pb-20 px-6 max-w-xl mx-auto">
          <div className="bg-white rounded-3xl p-12 text-center shadow-lg">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-10 h-10 text-green-600" />
            </div>
            <h1 className="text-3xl font-serif font-medium text-[#1D1D1F] mb-4">Request Sent!</h1>
            <p className="text-[#1D1D1F]/70 mb-8">
              Your booking request has been sent to <strong>{photographer.business_name || photographer.name}</strong>.
              <br />
              You will receive a confirmation email once your appointment is approved.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="text-[#0066CC] hover:underline"
            >
              Book Another Session
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <Header />
      
      <main className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Info Side */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-3xl p-8 shadow-sm sticky top-32">
              <h2 className="text-xl font-bold text-[#1D1D1F] mb-2">Book a Session</h2>
              <p className="text-sm text-gray-500 mb-6">with {photographer.business_name || photographer.name}</p>
              
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-gray-600">
                  <Mail className="w-5 h-5 text-[#0066CC]" />
                  <span className="text-sm truncate">{photographer.email}</span>
                </div>
                <div className="flex items-center gap-3 text-gray-600">
                  <Clock className="w-5 h-5 text-[#0066CC]" />
                  <span className="text-sm">Session Duration: {formData.duration} mins</span>
                </div>
              </div>
            </div>
          </div>

          {/* Form Side */}
          <div className="md:col-span-2">
            <div className="bg-white rounded-3xl p-8 shadow-sm">
              <h1 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-8">
                Enter Your Details
              </h1>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                    <input
                      type="text"
                      required
                      value={formData.client_name}
                      onChange={e => setFormData({...formData, client_name: e.target.value})}
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                    <input
                      type="email"
                      required
                      value={formData.client_email}
                      onChange={e => setFormData({...formData, client_email: e.target.value})}
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                      placeholder="john@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Service Type</label>
                  <select
                    value={formData.service_type}
                    onChange={e => setFormData({...formData, service_type: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  >
                    <option>Portrait Session</option>
                    <option>Wedding Consultation</option>
                    <option>Family Shoot</option>
                    <option>Event Coverage</option>
                    <option>Commercial Shoot</option>
                  </select>
                </div>

                {/* Availability Calendar */}
                  <div>
                  <label className="block text-sm font-medium text-gray-700 mb-4 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Select Date & Time
                  </label>
                  <AvailabilityCalendar
                    photographerId={userId!}
                    selectedSlot={selectedSlot}
                    onSlotSelect={(slot) => setSelectedSlot(slot)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Notes / Special Requests</label>
                  <textarea
                    value={formData.notes}
                    onChange={e => setFormData({...formData, notes: e.target.value})}
                    rows={4}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                    placeholder="Tell us more about your session..."
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-4 bg-[#1D1D1F] text-white rounded-xl font-bold hover:bg-black transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                  Request Appointment
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}

