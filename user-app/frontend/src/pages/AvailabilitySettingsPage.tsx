import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, Plus, Trash2, Settings, Link as LinkIcon } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface TimeSlot {
  day: string;
  enabled: boolean;
  start_time: string;
  end_time: string;
}

interface AvailabilitySettings {
  timezone: string;
  booking_buffer_minutes: number;
  max_advance_days: number;
  min_notice_hours: number;
  weekly_schedule: TimeSlot[];
  booking_url?: string;
}

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function AvailabilitySettingsPage() {
  const [settings, setSettings] = useState<AvailabilitySettings>({
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    booking_buffer_minutes: 30,
    max_advance_days: 60,
    min_notice_hours: 24,
    weekly_schedule: DAYS_OF_WEEK.map(day => ({
      day,
      enabled: day !== 'Saturday' && day !== 'Sunday',
      start_time: '09:00',
      end_time: '17:00'
    }))
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/availability/settings');
      if (response.success && response.data) {
        setSettings({
          ...settings,
          ...response.data,
          booking_url: response.data.booking_url
        });
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Scheduler is an Ultimate plan feature');
      } else {
        toast.error('Failed to load availability settings');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      const response = await api.put('/availability/settings', settings);
      if (response.success) {
        toast.success('Availability settings saved');
        if (response.data?.booking_url) {
          setSettings({ ...settings, booking_url: response.data.booking_url });
        }
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateSchedule = (index: number, updates: Partial<TimeSlot>) => {
    const newSchedule = [...settings.weekly_schedule];
    newSchedule[index] = { ...newSchedule[index], ...updates };
    setSettings({ ...settings, weekly_schedule: newSchedule });
  };

  const copyBookingUrl = () => {
    if (settings.booking_url) {
      navigator.clipboard.writeText(settings.booking_url);
      toast.success('Booking URL copied to clipboard');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading settings...</p>
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
              <Link to="/scheduler" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Scheduler</Link>
              <Link to="/availability" className="text-sm font-medium text-[#1D1D1F]">Availability</Link>
            </nav>
          </div>
          <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Availability Settings</h1>
          <p className="text-[#1D1D1F]/60">Configure when clients can book appointments with you</p>
        </div>

        <div className="space-y-6">
          {/* Booking URL */}
          {settings.booking_url && (
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-3xl border border-blue-200 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <LinkIcon className="w-5 h-5 text-blue-600" />
                    <h3 className="text-lg font-medium text-[#1D1D1F]">Public Booking URL</h3>
                  </div>
                  <p className="text-sm text-[#1D1D1F]/70 mb-3">
                    Share this link with clients to let them book appointments directly
                  </p>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={settings.booking_url}
                      readOnly
                      className="flex-1 px-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-mono"
                    />
                    <button
                      onClick={copyBookingUrl}
                      className="px-4 py-2.5 bg-[#1D1D1F] text-white rounded-xl text-sm font-medium hover:bg-black"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* General Settings */}
          <div className="bg-white rounded-3xl border border-gray-200 p-6">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">General Settings</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Timezone
                </label>
                <select
                  value={settings.timezone}
                  onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Buffer Between Appointments (minutes)
                </label>
                <input
                  type="number"
                  min="0"
                  max="120"
                  step="15"
                  value={settings.booking_buffer_minutes}
                  onChange={(e) => setSettings({ ...settings, booking_buffer_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Minimum Notice (hours)
                </label>
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={settings.min_notice_hours}
                  onChange={(e) => setSettings({ ...settings, min_notice_hours: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-[#1D1D1F]/60 mt-1">
                  Clients must book at least this many hours in advance
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Maximum Advance Booking (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={settings.max_advance_days}
                  onChange={(e) => setSettings({ ...settings, max_advance_days: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-[#1D1D1F]/60 mt-1">
                  How far in advance clients can book
                </p>
              </div>
            </div>
          </div>

          {/* Weekly Schedule */}
          <div className="bg-white rounded-3xl border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-50 rounded-xl">
                <Calendar className="w-5 h-5 text-purple-600" />
              </div>
              <h2 className="text-xl font-medium text-[#1D1D1F]">Weekly Schedule</h2>
            </div>

            <div className="space-y-3">
              {settings.weekly_schedule.map((slot, index) => (
                <div
                  key={slot.day}
                  className={`p-4 rounded-2xl border transition-colors ${
                    slot.enabled ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 flex-shrink-0 w-32">
                      <input
                        type="checkbox"
                        checked={slot.enabled}
                        onChange={(e) => updateSchedule(index, { enabled: e.target.checked })}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-[#1D1D1F]">{slot.day}</span>
                    </label>

                    {slot.enabled && (
                      <>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <input
                            type="time"
                            value={slot.start_time}
                            onChange={(e) => updateSchedule(index, { start_time: e.target.value })}
                            className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-500">to</span>
                          <input
                            type="time"
                            value={slot.end_time}
                            onChange={(e) => updateSchedule(index, { end_time: e.target.value })}
                            className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </>
                    )}

                    {!slot.enabled && (
                      <span className="text-sm text-gray-500">Unavailable</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="px-8 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Availability Settings'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
