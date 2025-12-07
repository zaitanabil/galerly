/**
 * White Label / Branding Configuration Component
 * Allows photographers to customize branding visibility based on their plan
 */
import { useState, useEffect } from 'react';
import { Eye, EyeOff, Palette, Image, Type, Lock, Sparkles } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface BrandingSettings {
  hide_galerly_branding: boolean;
  custom_branding: {
    enabled: boolean;
    logo_url: string;
    business_name: string;
    tagline: string;
    footer_text: string;
  };
  theme_customization: {
    enabled: boolean;
    primary_color: string;
    secondary_color: string;
    font_family: string;
  };
}

export default function WhiteLabelConfig() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<BrandingSettings>({
    hide_galerly_branding: false,
    custom_branding: {
      enabled: false,
      logo_url: '',
      business_name: '',
      tagline: '',
      footer_text: ''
    },
    theme_customization: {
      enabled: false,
      primary_color: '#0066CC',
      secondary_color: '#FFD700',
      font_family: 'Inter'
    }
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasWhiteLabelAccess, setHasWhiteLabelAccess] = useState(false);

  useEffect(() => {
    loadSettings();
    checkAccess();
  }, []);

  const checkAccess = () => {
    const plan = user?.plan || 'free';
    // White label available on Plus, Pro, Ultimate
    setHasWhiteLabelAccess(['plus', 'pro', 'ultimate'].includes(plan));
  };

  const loadSettings = async () => {
    try {
      const response = await api.get('/profile/branding-settings');
      if (response.success && response.data) {
        setSettings(response.data);
      }
    } catch (error) {
      console.error('Error loading branding settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!hasWhiteLabelAccess) {
      toast.error('White label branding is available on Plus, Pro, and Ultimate plans');
      return;
    }

    setSaving(true);
    try {
      const response = await api.put('/profile/branding-settings', settings);
      
      if (response.success) {
        toast.success('Branding settings saved successfully');
      } else {
        toast.error(response.error || 'Failed to save settings');
      }
    } catch (error: any) {
      console.error('Error saving branding settings:', error);
      toast.error(error.response?.data?.error || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Logo file must be less than 2MB');
      return;
    }

    try {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const base64Data = event.target?.result as string;
        
        const uploadResponse = await api.post('/profile/branding-logo', {
          file_data: base64Data,
          filename: file.name
        });

        if (uploadResponse.success && uploadResponse.data?.url) {
          setSettings(prev => ({
            ...prev,
            custom_branding: {
              ...prev.custom_branding,
              logo_url: uploadResponse.data.url
            }
          }));
          toast.success('Logo uploaded successfully');
        } else {
          toast.error('Failed to upload logo');
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading logo:', error);
      toast.error('Failed to upload logo');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!hasWhiteLabelAccess) {
    return (
      <div className="border border-blue-100 bg-blue-50/30 rounded-2xl p-6">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Lock className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              White Label Branding
            </h3>
            <p className="text-xs text-blue-700 mb-4">
              Remove "Powered by Galerly" branding and replace it with your own custom branding. 
              Available on Plus, Pro, and Ultimate plans.
            </p>
            <a 
              href="/billing" 
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Upgrade to Remove Branding
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hide Galerly Branding Toggle */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <label className="flex items-center gap-2 text-sm font-medium text-[#1D1D1F] mb-2">
              {settings.hide_galerly_branding ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              Remove "Powered by Galerly" Branding
            </label>
            <p className="text-xs text-[#1D1D1F]/60">
              Hide the Galerly footer branding from all public gallery pages
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.hide_galerly_branding}
              onChange={(e) => setSettings({
                ...settings,
                hide_galerly_branding: e.target.checked
              })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {settings.hide_galerly_branding && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-xl">
            <p className="text-xs text-green-800 flex items-center gap-2">
              <EyeOff className="w-4 h-4" />
              Galerly branding will be hidden on all your public galleries
            </p>
          </div>
        )}
      </div>

      {/* Custom Branding */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-sm font-semibold text-[#1D1D1F] mb-1 flex items-center gap-2">
              <Image className="w-4 h-4" />
              Custom Branding
            </h3>
            <p className="text-xs text-[#1D1D1F]/60">
              Replace with your own logo and branding
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.custom_branding.enabled}
              onChange={(e) => setSettings({
                ...settings,
                custom_branding: {
                  ...settings.custom_branding,
                  enabled: e.target.checked
                }
              })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {settings.custom_branding.enabled && (
          <div className="space-y-4">
            {/* Logo Upload */}
            <div>
              <label className="block text-xs font-medium text-[#1D1D1F]/70 mb-2">
                Your Logo
              </label>
              <div className="flex items-center gap-4">
                {settings.custom_branding.logo_url && (
                  <img 
                    src={settings.custom_branding.logo_url} 
                    alt="Custom logo" 
                    className="h-12 w-auto object-contain bg-gray-50 rounded-lg p-2 border border-gray-200"
                  />
                )}
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleLogoUpload(file);
                    }}
                    className="hidden"
                  />
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-[#1D1D1F] text-sm font-medium rounded-xl hover:bg-gray-200 transition-colors">
                    <Image className="w-4 h-4" />
                    Upload Logo
                  </span>
                </label>
              </div>
            </div>

            {/* Business Name */}
            <div>
              <label className="block text-xs font-medium text-[#1D1D1F]/70 mb-2">
                Business Name
              </label>
              <input
                type="text"
                value={settings.custom_branding.business_name}
                onChange={(e) => setSettings({
                  ...settings,
                  custom_branding: {
                    ...settings.custom_branding,
                    business_name: e.target.value
                  }
                })}
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                placeholder="Your Photography Studio"
              />
            </div>

            {/* Tagline */}
            <div>
              <label className="block text-xs font-medium text-[#1D1D1F]/70 mb-2">
                Tagline
              </label>
              <input
                type="text"
                value={settings.custom_branding.tagline}
                onChange={(e) => setSettings({
                  ...settings,
                  custom_branding: {
                    ...settings.custom_branding,
                    tagline: e.target.value
                  }
                })}
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                placeholder="Capturing moments that last forever"
              />
            </div>

            {/* Footer Text */}
            <div>
              <label className="block text-xs font-medium text-[#1D1D1F]/70 mb-2">
                Footer Text
              </label>
              <textarea
                value={settings.custom_branding.footer_text}
                onChange={(e) => setSettings({
                  ...settings,
                  custom_branding: {
                    ...settings.custom_branding,
                    footer_text: e.target.value
                  }
                })}
                rows={3}
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                placeholder="© 2024 Your Studio. All rights reserved."
              />
            </div>
          </div>
        )}
      </div>

      {/* Theme Customization */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-sm font-semibold text-[#1D1D1F] mb-1 flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Theme Customization
            </h3>
            <p className="text-xs text-[#1D1D1F]/60">
              Customize colors and fonts for your galleries
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.theme_customization.enabled}
              onChange={(e) => setSettings({
                ...settings,
                theme_customization: {
                  ...settings.theme_customization,
                  enabled: e.target.checked
                }
              })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {settings.theme_customization.enabled && (
          <div className="space-y-4">
            {/* Primary Color */}
            <div className="flex items-center gap-4">
              <label className="flex-1 text-xs font-medium text-[#1D1D1F]/70">
                Primary Color
              </label>
              <input
                type="color"
                value={settings.theme_customization.primary_color}
                onChange={(e) => setSettings({
                  ...settings,
                  theme_customization: {
                    ...settings.theme_customization,
                    primary_color: e.target.value
                  }
                })}
                className="w-16 h-10 rounded-lg cursor-pointer"
              />
              <input
                type="text"
                value={settings.theme_customization.primary_color}
                onChange={(e) => setSettings({
                  ...settings,
                  theme_customization: {
                    ...settings.theme_customization,
                    primary_color: e.target.value
                  }
                })}
                className="w-24 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono"
              />
            </div>

            {/* Secondary Color */}
            <div className="flex items-center gap-4">
              <label className="flex-1 text-xs font-medium text-[#1D1D1F]/70">
                Secondary Color
              </label>
              <input
                type="color"
                value={settings.theme_customization.secondary_color}
                onChange={(e) => setSettings({
                  ...settings,
                  theme_customization: {
                    ...settings.theme_customization,
                    secondary_color: e.target.value
                  }
                })}
                className="w-16 h-10 rounded-lg cursor-pointer"
              />
              <input
                type="text"
                value={settings.theme_customization.secondary_color}
                onChange={(e) => setSettings({
                  ...settings,
                  theme_customization: {
                    ...settings.theme_customization,
                    secondary_color: e.target.value
                  }
                })}
                className="w-24 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono"
              />
            </div>

            {/* Font Family */}
            <div>
              <label className="block text-xs font-medium text-[#1D1D1F]/70 mb-2">
                Font Family
              </label>
              <select
                value={settings.theme_customization.font_family}
                onChange={(e) => setSettings({
                  ...settings,
                  theme_customization: {
                    ...settings.theme_customization,
                    font_family: e.target.value
                  }
                })}
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
              >
                <option value="Inter">Inter (Default)</option>
                <option value="Playfair Display">Playfair Display</option>
                <option value="Roboto">Roboto</option>
                <option value="Open Sans">Open Sans</option>
                <option value="Lato">Lato</option>
                <option value="Montserrat">Montserrat</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-[#0066CC] text-white rounded-2xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Saving...
            </>
          ) : (
            'Save Branding Settings'
          )}
        </button>
      </div>
    </div>
  );
}
