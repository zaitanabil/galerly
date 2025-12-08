// Notification Preferences Page
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Bell, Mail, MessageSquare, Calendar, DollarSign, Users, CheckCircle } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface NotificationPreference {
  id: string;
  title: string;
  description: string;
  icon: any;
  email: boolean;
  inApp: boolean;
}

export default function NotificationPreferencesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState<Record<string, NotificationPreference>>({});

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await api.get('/notification-preferences');
      if (response.success && response.data) {
        // Convert API response to preferences format
        const prefs: Record<string, NotificationPreference> = {
          gallery_shared: {
            id: 'gallery_shared',
            title: 'Gallery Shared',
            description: 'When you share a gallery with a client',
            icon: MessageSquare,
            email: response.data.gallery_shared_email ?? true,
            inApp: response.data.gallery_shared_inapp ?? true
          },
          client_favorite: {
            id: 'client_favorite',
            title: 'Client Favorites',
            description: 'When a client marks photos as favorites',
            icon: CheckCircle,
            email: response.data.client_favorite_email ?? true,
            inApp: response.data.client_favorite_inapp ?? true
          },
          appointment_booking: {
            id: 'appointment_booking',
            title: 'Appointment Bookings',
            description: 'When a client requests an appointment',
            icon: Calendar,
            email: response.data.appointment_booking_email ?? true,
            inApp: response.data.appointment_booking_inapp ?? true
          },
          payment_received: {
            id: 'payment_received',
            title: 'Payment Received',
            description: 'When you receive an invoice payment',
            icon: DollarSign,
            email: response.data.payment_received_email ?? true,
            inApp: response.data.payment_received_inapp ?? true
          },
          new_lead: {
            id: 'new_lead',
            title: 'New Leads',
            description: 'When someone submits a contact form',
            icon: Users,
            email: response.data.new_lead_email ?? true,
            inApp: response.data.new_lead_inapp ?? true
          },
          subscription_updates: {
            id: 'subscription_updates',
            title: 'Subscription Updates',
            description: 'Plan changes, renewals, and billing updates',
            icon: Bell,
            email: response.data.subscription_updates_email ?? true,
            inApp: response.data.subscription_updates_inapp ?? false
          },
          marketing: {
            id: 'marketing',
            title: 'Marketing & Tips',
            description: 'Product updates, tips, and photography resources',
            icon: Mail,
            email: response.data.marketing_email ?? false,
            inApp: response.data.marketing_inapp ?? false
          }
        };
        setPreferences(prefs);
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      // Set defaults if loading fails
      setPreferences({
        gallery_shared: {
          id: 'gallery_shared',
          title: 'Gallery Shared',
          description: 'When you share a gallery with a client',
          icon: MessageSquare,
          email: true,
          inApp: true
        },
        client_favorite: {
          id: 'client_favorite',
          title: 'Client Favorites',
          description: 'When a client marks photos as favorites',
          icon: CheckCircle,
          email: true,
          inApp: true
        },
        appointment_booking: {
          id: 'appointment_booking',
          title: 'Appointment Bookings',
          description: 'When a client requests an appointment',
          icon: Calendar,
          email: true,
          inApp: true
        },
        payment_received: {
          id: 'payment_received',
          title: 'Payment Received',
          description: 'When you receive an invoice payment',
          icon: DollarSign,
          email: true,
          inApp: true
        },
        new_lead: {
          id: 'new_lead',
          title: 'New Leads',
          description: 'When someone submits a contact form',
          icon: Users,
          email: true,
          inApp: true
        },
        subscription_updates: {
          id: 'subscription_updates',
          title: 'Subscription Updates',
          description: 'Plan changes, renewals, and billing updates',
          icon: Bell,
          email: true,
          inApp: false
        },
        marketing: {
          id: 'marketing',
          title: 'Marketing & Tips',
          description: 'Product updates, tips, and photography resources',
          icon: Mail,
          email: false,
          inApp: false
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const togglePreference = (prefId: string, channel: 'email' | 'inApp') => {
    setPreferences(prev => ({
      ...prev,
      [prefId]: {
        ...prev[prefId],
        [channel]: !prev[prefId][channel]
      }
    }));
  };

  const savePreferences = async () => {
    setSaving(true);
    try {
      // Convert preferences to API format
      const apiPrefs: Record<string, boolean> = {};
      Object.entries(preferences).forEach(([key, value]) => {
        apiPrefs[`${key}_email`] = value.email;
        apiPrefs[`${key}_inapp`] = value.inApp;
      });

      const response = await api.put('/notification-preferences', apiPrefs);
      if (response.success) {
        toast.success('Notification preferences saved');
      } else {
        toast.error(response.error || 'Failed to save preferences');
      }
    } catch (error) {
      toast.error('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <Header />

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Back Button */}
        <Link
          to="/settings"
          className="inline-flex items-center gap-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Settings
        </Link>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] mb-3">
            Notification Preferences
          </h1>
          <p className="text-lg text-[#1D1D1F]/60">
            Choose how and when you want to be notified
          </p>
        </div>

        {loading ? (
          <div className="glass-panel p-12 text-center">
            <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#1D1D1F]/60">Loading preferences...</p>
          </div>
        ) : (
          <>
            {/* Preferences Table */}
            <div className="glass-panel p-6 mb-6">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-4 px-2 text-xs font-semibold text-[#1D1D1F]/40 uppercase">
                        Notification Type
                      </th>
                      <th className="text-center py-4 px-2 text-xs font-semibold text-[#1D1D1F]/40 uppercase w-24">
                        Email
                      </th>
                      <th className="text-center py-4 px-2 text-xs font-semibold text-[#1D1D1F]/40 uppercase w-24">
                        In-App
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(preferences).map(([key, pref]) => (
                      <tr key={key} className="border-b border-gray-50 last:border-0">
                        <td className="py-4 px-2">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                              <pref.icon className="w-5 h-5 text-[#0066CC]" />
                            </div>
                            <div>
                              <div className="font-medium text-[#1D1D1F] mb-1">{pref.title}</div>
                              <div className="text-sm text-[#1D1D1F]/60">{pref.description}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-2 text-center">
                          <button
                            onClick={() => togglePreference(key, 'email')}
                            className={`w-12 h-6 rounded-full transition-colors relative ${
                              pref.email ? 'bg-[#0066CC]' : 'bg-gray-200'
                            }`}
                          >
                            <span
                              className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                                pref.email ? 'translate-x-7' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </td>
                        <td className="py-4 px-2 text-center">
                          <button
                            onClick={() => togglePreference(key, 'inApp')}
                            className={`w-12 h-6 rounded-full transition-colors relative ${
                              pref.inApp ? 'bg-[#0066CC]' : 'bg-gray-200'
                            }`}
                          >
                            <span
                              className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                                pref.inApp ? 'translate-x-7' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => {
                  const allOn = Object.fromEntries(
                    Object.entries(preferences).map(([key, pref]) => [
                      key,
                      { ...pref, email: true, inApp: true }
                    ])
                  );
                  setPreferences(allOn);
                }}
                className="px-4 py-2 text-sm border border-gray-200 text-[#1D1D1F] rounded-xl hover:bg-gray-50 transition-colors"
              >
                Enable All
              </button>
              <button
                onClick={() => {
                  const allOff = Object.fromEntries(
                    Object.entries(preferences).map(([key, pref]) => [
                      key,
                      { ...pref, email: false, inApp: false }
                    ])
                  );
                  setPreferences(allOff);
                }}
                className="px-4 py-2 text-sm border border-gray-200 text-[#1D1D1F] rounded-xl hover:bg-gray-50 transition-colors"
              >
                Disable All
              </button>
            </div>

            {/* Save Button */}
            <div className="flex gap-3">
              <button
                onClick={savePreferences}
                disabled={saving}
                className="flex-1 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Preferences'}
              </button>
              <button
                onClick={() => navigate('/settings')}
                className="px-6 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-50 transition-all"
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}
