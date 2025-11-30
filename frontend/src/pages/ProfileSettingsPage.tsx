// Profile Settings page
import { useState, FormEvent, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth, User } from '../contexts/AuthContext';
import { api } from '../utils/api';
import {
  ArrowLeft,
  User as UserIcon,
  Mail,
  MapPin,
  AlertCircle,
  Check,
  Bell,
  Code,
  Globe,
  Key,
  Copy,
  Search,
  Layout,
  Stamp,
  Download
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import CityAutocomplete from '../components/CityAutocomplete';

interface NotificationPreferences {
  client_notifications: {
    gallery_shared: boolean;
    new_photos_added: boolean;
    gallery_ready: boolean;
    selection_reminder: boolean;
    gallery_expiring: boolean;
    custom_messages: boolean;
  };
  photographer_notifications: {
    client_selected_photos: boolean;
    client_feedback_received: boolean;
  };
}

interface PortfolioSettings {
  custom_domain: string;
  seo_settings: {
    title: string;
    description: string;
    keywords: string;
    og_image: string;
  };
}

export default function ProfileSettingsPage() {
  const { user, refreshUser } = useAuth();
  const dashboardLink = user?.role === 'client' ? '/client-dashboard' : '/dashboard';
  const [formData, setFormData] = useState({
    name: user?.name || '',
    username: user?.username || '',
    bio: user?.bio || '',
    city: user?.city || '',
  });
  
  // Notification state
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    client_notifications: {
        gallery_shared: true,
        new_photos_added: true,
        gallery_ready: true,
        selection_reminder: true,
        gallery_expiring: true,
        custom_messages: true
    },
    photographer_notifications: {
        client_selected_photos: true,
        client_feedback_received: true
    }
  });

  // Portfolio & SEO State
  const [portfolioSettings, setPortfolioSettings] = useState<PortfolioSettings>({
    custom_domain: '',
    seo_settings: {
      title: '',
      description: '',
      keywords: '',
      og_image: ''
    }
  });
  const [verifyingDomain, setVerifyingDomain] = useState(false);

  // Watermark State
  const [watermarkSettings, setWatermarkSettings] = useState({
    watermark_enabled: false,
    watermark_text: '',
    watermark_position: 'bottom-right',
    watermark_opacity: 0.5
  });

  // API Key state
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  const [message, setMessage] = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('');

  useEffect(() => {
    loadPreferences();
    loadPortfolioSettings();
    loadWatermarkSettings();
    loadApiKey();
  }, []);

  const loadPreferences = async () => {
    try {
        const response = await api.get<{ preferences: NotificationPreferences }>('/notifications/preferences');
        if (response.success && response.data?.preferences) {
            setPreferences(response.data.preferences);
        }
    } catch (error) {
        console.error('Failed to load preferences:', error);
    }
  };

  const loadPortfolioSettings = async () => {
    try {
      const response = await api.get<PortfolioSettings>('/portfolio/settings');
      if (response.success && response.data) {
        setPortfolioSettings({
          custom_domain: response.data.custom_domain || '',
          seo_settings: {
            title: response.data.seo_settings?.title || '',
            description: response.data.seo_settings?.description || '',
            keywords: response.data.seo_settings?.keywords || '',
            og_image: response.data.seo_settings?.og_image || ''
          }
        });
      }
    } catch (error) {
      console.error('Failed to load portfolio settings:', error);
    }
  };

  const loadWatermarkSettings = async () => {
    try {
        // Fetch from /auth/me to get latest user settings including watermark
        // Note: The main useAuth user object might be stale until refresh
        const response = await api.get<User>('/auth/me');
        if (response.success && response.data) {
            setWatermarkSettings({
                watermark_enabled: response.data.watermark_enabled || false,
                watermark_text: response.data.watermark_text || '',
                watermark_position: response.data.watermark_position || 'bottom-right',
                watermark_opacity: response.data.watermark_opacity ?? 0.5
            });
        }
    } catch {
        console.error('Failed to load watermark settings');
    }
  };

  const loadApiKey = async () => {
    try {
        const response = await api.get<{ api_key: string }>('/auth/api-key');
        if (response.success) {
            setApiKey(response.data?.api_key || null);
        }
    } catch {
        // Ignore auth errors or plan restrictions
    }
  };

  const generateApiKey = async () => {
    if (!confirm('Generate a new API Key? This will invalidate any existing keys.')) return;
    try {
        const response = await api.post<{ api_key: string }>('/auth/api-key', {});
        if (response.success) {
            setApiKey(response.data?.api_key || null);
            setShowApiKey(true);
            toast.success('API Key generated');
        } else {
            toast.error(response.error || 'Failed to generate API key');
        }
    } catch {
        toast.error('Failed to generate API key');
    }
  };

  const copyApiKey = () => {
    if (apiKey) {
        navigator.clipboard.writeText(apiKey);
        toast.success('Copied to clipboard');
    }
  };

  const handleVerifyDomain = async () => {
    if (!portfolioSettings.custom_domain) return;
    setVerifyingDomain(true);
    try {
      const response = await api.post('/portfolio/verify-domain', { 
        domain: portfolioSettings.custom_domain 
      });
      if (response.success) {
        toast.success('Domain verified successfully!');
      } else {
        toast.error(response.error || 'Domain verification failed');
      }
    } catch {
      toast.error('Failed to verify domain');
    } finally {
      setVerifyingDomain(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    setLoading(true);

    try {
      // Update profile (including watermark settings)
      const profilePromise = api.put('/profile', {
        name: formData.name,
        username: formData.username,
        bio: formData.bio,
        city: formData.city,
        ...watermarkSettings // Include watermark settings
      });

      // Update preferences
      const prefsPromise = api.put('/notifications/preferences', preferences);

      // Update portfolio settings
      const portfolioPromise = api.put('/portfolio/settings', portfolioSettings);

      const [profileRes, prefsRes, portfolioRes] = await Promise.all([
        profilePromise, 
        prefsPromise,
        portfolioPromise
      ]);

      if (profileRes.success && prefsRes.success && portfolioRes.success) {
        setMessage({ type: 'success', text: 'Settings updated successfully!' });
        await refreshUser();
      } else {
        setMessage({ 
          type: 'error', 
          text: profileRes.error || prefsRes.error || portfolioRes.error || 'Failed to update settings' 
        });
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to update settings. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmationText.toLowerCase() !== 'delete my account') {
      alert('Please type "delete my account" to confirm.');
      return;
    }

    if (!confirm('Are you absolutely sure? This action cannot be undone.')) return;

    try {
      const response = await api.delete('/auth/delete-account');
      if (response.success) {
        window.location.href = '/';
      } else {
        alert(response.error || 'Failed to delete account');
      }
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('An error occurred while deleting your account.');
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={dashboardLink}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                Profile Settings
              </h1>
            </div>
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        {message.text && (
          <div
            className={`mb-6 p-4 rounded-2xl flex items-start gap-3 ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-100'
                : 'bg-red-50 border border-red-100'
            }`}
          >
            {message.type === 'success' ? (
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            )}
            <p
              className={`text-sm ${
                message.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}
            >
              {message.text}
            </p>
          </div>
        )}

        <div className="glass-panel p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Basic Information */}
            <div>
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Basic Information
              </h2>
              
              <div className="space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Full Name
                  </label>
                  <div className="relative">
                    <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                    <input
                      id="name"
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                      placeholder="John Doe"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Username
                  </label>
                  <input
                    id="username"
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                    placeholder="johndoe"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                    <input
                      id="email"
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className="w-full pl-12 pr-4 py-3.5 bg-gray-100 border border-gray-200 rounded-2xl text-[#1D1D1F]/60 cursor-not-allowed"
                    />
                  </div>
                  <p className="mt-2 text-sm text-[#1D1D1F]/60">
                    Contact support to change your email
                  </p>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Location
              </h2>
              
                <div>
                  <label htmlFor="city" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    City
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40 z-10" />
                    <CityAutocomplete
                      value={formData.city}
                      onChange={(val) => setFormData({ ...formData, city: val })}
                      placeholder="San Francisco"
                      className="w-full"
                    />
                  </div>
                </div>
            </div>

            {/* Bio */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Bio
              </h2>
              
              <textarea
                id="bio"
                value={formData.bio}
                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                rows={6}
                className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all resize-none"
                placeholder="Tell clients about yourself and your photography style..."
              />
            </div>

            {/* Portfolio & SEO Settings (Plus/Pro/Ultimate) */}
            {(user?.plan !== 'free') && (
                <div className="border-t border-gray-200 pt-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-indigo-50 rounded-lg">
                            <Layout className="w-5 h-5 text-indigo-600" />
                        </div>
                        <h2 className="text-lg font-medium text-[#1D1D1F]">
                            Portfolio Website
                        </h2>
                    </div>

                    <div className="space-y-6">
                        {/* Custom Domain */}
                        <div>
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                                Custom Domain
                            </label>
                            <div className="flex gap-2">
                                <div className="relative flex-1">
                                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                                    <input
                                        type="text"
                                        value={portfolioSettings.custom_domain}
                                        onChange={(e) => setPortfolioSettings({ ...portfolioSettings, custom_domain: e.target.value })}
                                        className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                                        placeholder="www.yourphotography.com"
                                    />
                                </div>
                                <button
                                    type="button"
                                    onClick={handleVerifyDomain}
                                    disabled={verifyingDomain || !portfolioSettings.custom_domain}
                                    className="px-6 bg-white border border-gray-200 rounded-2xl font-medium text-[#1D1D1F] hover:bg-gray-50 transition-all disabled:opacity-50"
                                >
                                    {verifyingDomain ? 'Verifying...' : 'Verify'}
                                </button>
                            </div>
                            <p className="mt-2 text-xs text-gray-500">
                                Enter your domain name. Configure a CNAME record pointing to <code>cdn.galerly.com</code> in your DNS provider.
                            </p>
                        </div>

                        {/* SEO Settings */}
                        <div>
                            <div className="flex items-center gap-2 mb-4 mt-8">
                                <Search className="w-4 h-4 text-gray-500" />
                                <h3 className="text-sm font-medium text-[#1D1D1F]">SEO Optimization</h3>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 mb-1">
                                        Meta Title
                                    </label>
                                    <input
                                        type="text"
                                        value={portfolioSettings.seo_settings.title}
                                        onChange={(e) => setPortfolioSettings({
                                            ...portfolioSettings,
                                            seo_settings: { ...portfolioSettings.seo_settings, title: e.target.value }
                                        })}
                                        className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm"
                                        placeholder="Your Name - Professional Photographer"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 mb-1">
                                        Meta Description
                                    </label>
                                    <textarea
                                        value={portfolioSettings.seo_settings.description}
                                        onChange={(e) => setPortfolioSettings({
                                            ...portfolioSettings,
                                            seo_settings: { ...portfolioSettings.seo_settings, description: e.target.value }
                                        })}
                                        rows={3}
                                        className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm resize-none"
                                        placeholder="Brief description of your photography business for search engines."
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 mb-1">
                                        Keywords (comma separated)
                                    </label>
                                    <input
                                        type="text"
                                        value={portfolioSettings.seo_settings.keywords}
                                        onChange={(e) => setPortfolioSettings({
                                            ...portfolioSettings,
                                            seo_settings: { ...portfolioSettings.seo_settings, keywords: e.target.value }
                                        })}
                                        className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm"
                                        placeholder="photography, wedding, portrait, san francisco"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Watermark Settings (Plus/Pro/Ultimate) */}
            {(user?.plan !== 'free') && (
                <div className="border-t border-gray-200 pt-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-orange-50 rounded-lg">
                            <Stamp className="w-5 h-5 text-orange-600" />
                        </div>
                        <h2 className="text-lg font-medium text-[#1D1D1F]">
                            Watermarking
                        </h2>
                    </div>

                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-medium text-[#1D1D1F]">Enable Watermark</label>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    className="sr-only peer"
                                    checked={watermarkSettings.watermark_enabled}
                                    onChange={(e) => setWatermarkSettings({ ...watermarkSettings, watermark_enabled: e.target.checked })}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066CC]"></div>
                            </label>
                        </div>

                        {watermarkSettings.watermark_enabled && (
                            <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
                                <div>
                                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Watermark Text</label>
                                    <input
                                        type="text"
                                        value={watermarkSettings.watermark_text}
                                        onChange={(e) => setWatermarkSettings({ ...watermarkSettings, watermark_text: e.target.value })}
                                        className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm"
                                        placeholder="© Your Name"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Position</label>
                                        <select
                                            value={watermarkSettings.watermark_position}
                                            onChange={(e) => setWatermarkSettings({ ...watermarkSettings, watermark_position: e.target.value })}
                                            className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm"
                                        >
                                            <option value="bottom-right">Bottom Right</option>
                                            <option value="bottom-left">Bottom Left</option>
                                            <option value="top-right">Top Right</option>
                                            <option value="top-left">Top Left</option>
                                            <option value="center">Center</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Opacity ({Math.round(watermarkSettings.watermark_opacity * 100)}%)</label>
                                        <input
                                            type="range"
                                            min="0.1"
                                            max="1.0"
                                            step="0.1"
                                            value={watermarkSettings.watermark_opacity}
                                            onChange={(e) => setWatermarkSettings({ ...watermarkSettings, watermark_opacity: parseFloat(e.target.value) })}
                                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Notification Preferences */}
            <div className="border-t border-gray-200 pt-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-50 rounded-lg">
                    <Bell className="w-5 h-5 text-[#0066CC]" />
                </div>
                <h2 className="text-lg font-medium text-[#1D1D1F]">
                    Notification Settings
                </h2>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Client Notifications */}
                <div>
                    <h3 className="text-sm font-medium text-[#1D1D1F] mb-4 uppercase tracking-wider text-opacity-60">
                        Notify Clients When...
                    </h3>
                    <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.client_notifications.gallery_shared}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    client_notifications: { ...preferences.client_notifications, gallery_shared: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Gallery is shared</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.client_notifications.gallery_ready}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    client_notifications: { ...preferences.client_notifications, gallery_ready: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Gallery is ready</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.client_notifications.selection_reminder}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    client_notifications: { ...preferences.client_notifications, selection_reminder: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Reminder sent</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.client_notifications.gallery_expiring}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    client_notifications: { ...preferences.client_notifications, gallery_expiring: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Gallery expiring soon</span>
                        </label>
                    </div>
                </div>

                {/* Photographer Notifications */}
                <div>
                    <h3 className="text-sm font-medium text-[#1D1D1F] mb-4 uppercase tracking-wider text-opacity-60">
                        Notify Me When...
                    </h3>
                    <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.photographer_notifications.client_selected_photos}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    photographer_notifications: { ...preferences.photographer_notifications, client_selected_photos: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Client selects photos</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={preferences.photographer_notifications.client_feedback_received}
                                onChange={(e) => setPreferences({
                                    ...preferences,
                                    photographer_notifications: { ...preferences.photographer_notifications, client_feedback_received: e.target.checked }
                                })}
                                className="w-5 h-5 text-[#0066CC] rounded focus:ring-[#0066CC]"
                            />
                            <span className="text-sm text-[#1D1D1F]">Client submits feedback</span>
                        </label>
                    </div>
                </div>
              </div>
            </div>

            {/* Developer Settings (Pro/Ultimate only) */}
            {(user?.plan === 'pro' || user?.plan === 'ultimate') && (
                <div className="border-t border-gray-200 pt-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-purple-50 rounded-lg">
                            <Code className="w-5 h-5 text-purple-600" />
                        </div>
                        <h2 className="text-lg font-medium text-[#1D1D1F]">
                            Developer API
                        </h2>
                    </div>
                    
                    <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
                        <p className="text-sm text-gray-600 mb-4">
                            Access your data programmatically. Keep this key secret.
                        </p>
                        
                        {apiKey ? (
                            <div className="flex gap-2">
                                <div className="flex-1 relative">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2">
                                        <Key className="w-4 h-4 text-gray-400" />
                                    </div>
                                    <input 
                                        type={showApiKey ? "text" : "password"}
                                        value={apiKey}
                                        readOnly
                                        className="w-full pl-10 pr-20 py-3 bg-white border border-gray-200 rounded-xl text-sm font-mono"
                                    />
                                    <button 
                                        type="button"
                                        onClick={() => setShowApiKey(!showApiKey)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-blue-600 hover:underline"
                                    >
                                        {showApiKey ? 'Hide' : 'Show'}
                                    </button>
                                </div>
                                <button
                                    type="button"
                                    onClick={copyApiKey}
                                    className="p-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 text-gray-600"
                                    title="Copy to clipboard"
                                >
                                    <Copy className="w-4 h-4" />
                                </button>
                                <button
                                    type="button"
                                    onClick={generateApiKey}
                                    className="px-4 py-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 text-sm font-medium"
                                >
                                    Regenerate
                                </button>
                            </div>
                        ) : (
                            <button
                                type="button"
                                onClick={generateApiKey}
                                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-xl font-medium hover:bg-black transition-colors flex items-center gap-2"
                            >
                                <Key className="w-4 h-4" /> Generate API Key
                            </button>
                        )}
                        
                        <div className="mt-4 text-xs text-gray-500 flex items-center justify-between">
                            <a href="#" className="underline hover:text-blue-600">Read API Documentation</a>
                            <a href="/downloads/galerly-lightroom-plugin.zip" download className="underline hover:text-blue-600 flex items-center gap-1">
                                Download Lightroom Plugin <Download className="w-3 h-3" />
                            </a>
                        </div>
                    </div>
                </div>
            )}

            {/* Concierge Onboarding & VIP Support (Ultimate Only) */}
            {user?.plan === 'ultimate' && (
                <div className="border-t border-gray-200 pt-8">
                    <div className="bg-black text-white rounded-2xl p-8 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-10">
                            <Stamp className="w-32 h-32" />
                        </div>
                        <div className="relative z-10 grid md:grid-cols-2 gap-8">
                            <div>
                                <h2 className="text-xl font-medium mb-2">Concierge Onboarding</h2>
                                <p className="text-white/70 mb-6">
                                    Our priority onboarding team will help you migrate your portfolio, set up your domain, and customize your branding.
                                </p>
                                <button
                                    type="button"
                                    onClick={() => window.location.href = 'mailto:concierge@galerly.com?subject=Concierge%20Onboarding%20Request'}
                                    className="px-6 py-3 bg-white text-black rounded-full font-medium hover:bg-gray-100 transition-colors inline-flex items-center gap-2"
                                >
                                    <Mail className="w-4 h-4" />
                                    Request Onboarding
                                </button>
                            </div>
                            <div className="border-t md:border-t-0 md:border-l border-white/10 pt-8 md:pt-0 md:pl-8">
                                <h2 className="text-xl font-medium mb-2">VIP Priority Support</h2>
                                <p className="text-white/70 mb-6">
                                    Skip the queue. Your tickets are routed directly to our senior support team for immediate resolution.
                                </p>
                                <div className="flex gap-4">
                                    <button
                                        type="button"
                                        onClick={() => window.location.href = 'mailto:vip-support@galerly.com?subject=Priority%20Support%20Request'}
                                        className="px-6 py-3 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-full font-medium hover:bg-white/20 transition-colors inline-flex items-center gap-2"
                                    >
                                        <Mail className="w-4 h-4" />
                                        Contact VIP Support
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="border-t border-gray-200 pt-8 flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
              <Link
                to={dashboardLink}
                className="px-8 py-4 bg-white/50 border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-white transition-all"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>

        {/* Delete Account Section */}
        <div className="glass-panel p-8 border border-red-100 bg-red-50/30">
          <h2 className="text-lg font-medium text-red-600 mb-2">Delete Account</h2>
          <p className="text-sm text-[#1D1D1F]/70 mb-6">
            Permanently delete your account, galleries, and all data. This action cannot be undone.
          </p>
          
          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-6 py-3 border border-red-200 text-red-600 rounded-full font-medium hover:bg-red-50 transition-all"
            >
              Delete Account
            </button>
          ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
              <p className="text-sm font-medium text-[#1D1D1F]">
                Type "delete my account" to confirm:
              </p>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={deleteConfirmationText}
                  onChange={(e) => setDeleteConfirmationText(e.target.value)}
                  className="flex-1 px-4 py-3 bg-white border border-red-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
                  placeholder="delete my account"
                />
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteConfirmationText.toLowerCase() !== 'delete my account'}
                  className="px-6 py-3 bg-red-600 text-white rounded-xl font-medium hover:bg-red-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Confirm Delete
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmationText('');
                  }}
                  className="px-6 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-white transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}