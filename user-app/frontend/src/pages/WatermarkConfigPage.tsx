import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Image, Upload, Settings, Sliders, Eye, Download } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface WatermarkSettings {
  enabled: boolean;
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
  opacity: number;
  scale: number;
  logo_url?: string;
}

export default function WatermarkConfigPage() {
  const [settings, setSettings] = useState<WatermarkSettings>({
    enabled: true,
    position: 'bottom-right',
    opacity: 0.5,
    scale: 0.15
  });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/watermark/settings');
      if (response.success && response.data) {
        setSettings(response.data);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Watermarking is a Plus+ feature');
      } else {
        toast.error('Failed to load watermark settings');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUploadLogo = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Logo must be smaller than 5MB');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('logo', file);

      const response = await api.post('/watermark/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.success) {
        setSettings({ ...settings, logo_url: response.data.logo_url });
        toast.success('Logo uploaded successfully');
      } else {
        toast.error(response.error || 'Failed to upload logo');
      }
    } catch (error) {
      toast.error('Failed to upload logo');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      const response = await api.put('/watermark/settings', settings);
      if (response.success) {
        toast.success('Watermark settings saved');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const positionOptions = [
    { value: 'top-left', label: 'Top Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'bottom-right', label: 'Bottom Right' },
    { value: 'center', label: 'Center' }
  ];

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
              <Link to="/watermark" className="text-sm font-medium text-[#1D1D1F]">Watermark</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
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
          <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Watermark Configuration</h1>
          <p className="text-[#1D1D1F]/60">Protect your photos with custom watermarks</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Settings Panel */}
          <div className="space-y-6">
            {/* Logo Upload */}
            <div className="bg-white rounded-3xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-50 rounded-xl">
                  <Upload className="w-5 h-5 text-blue-600" />
                </div>
                <h2 className="text-xl font-medium text-[#1D1D1F]">Watermark Logo</h2>
              </div>

              {settings.logo_url && (
                <div className="mb-4 p-4 bg-gray-50 rounded-2xl">
                  <img
                    src={settings.logo_url}
                    alt="Watermark Logo"
                    className="max-h-32 mx-auto"
                  />
                </div>
              )}

              <label className="block">
                <div className="flex items-center justify-center w-full p-6 border-2 border-dashed border-gray-300 rounded-2xl cursor-pointer hover:border-blue-500 hover:bg-blue-50/50 transition-colors">
                  <div className="text-center">
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-[#1D1D1F]">
                      {uploading ? 'Uploading...' : 'Click to upload logo'}
                    </p>
                    <p className="text-xs text-[#1D1D1F]/60 mt-1">PNG or JPG, max 5MB</p>
                  </div>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleUploadLogo}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
            </div>

            {/* Watermark Settings */}
            <div className="bg-white rounded-3xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-50 rounded-xl">
                  <Sliders className="w-5 h-5 text-purple-600" />
                </div>
                <h2 className="text-xl font-medium text-[#1D1D1F]">Settings</h2>
              </div>

              <div className="space-y-6">
                {/* Enable/Disable */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-[#1D1D1F]">
                    Enable Watermark
                  </label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.enabled}
                      onChange={(e) => setSettings({ ...settings, enabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {/* Position */}
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Position
                  </label>
                  <select
                    value={settings.position}
                    onChange={(e) => setSettings({ ...settings, position: e.target.value as any })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {positionOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Opacity */}
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Opacity: {Math.round(settings.opacity * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.opacity}
                    onChange={(e) => setSettings({ ...settings, opacity: parseFloat(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>

                {/* Scale */}
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Size: {Math.round(settings.scale * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.5"
                    step="0.05"
                    value={settings.scale}
                    onChange={(e) => setSettings({ ...settings, scale: parseFloat(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              </div>

              <button
                onClick={handleSaveSettings}
                className="w-full mt-6 px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black transition-colors"
              >
                Save Settings
              </button>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="bg-white rounded-3xl border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-green-50 rounded-xl">
                <Eye className="w-5 h-5 text-green-600" />
              </div>
              <h2 className="text-xl font-medium text-[#1D1D1F]">Live Preview</h2>
            </div>

            <div className="aspect-video bg-gray-100 rounded-2xl relative overflow-hidden border-2 border-gray-200">
              {/* Sample image background */}
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-400 to-purple-500">
                <Image className="w-32 h-32 text-white/20" />
              </div>

              {/* Watermark preview */}
              {settings.enabled && settings.logo_url && (
                <div
                  className={`absolute ${
                    settings.position === 'top-left' ? 'top-4 left-4' :
                    settings.position === 'top-right' ? 'top-4 right-4' :
                    settings.position === 'bottom-left' ? 'bottom-4 left-4' :
                    settings.position === 'bottom-right' ? 'bottom-4 right-4' :
                    'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2'
                  }`}
                  style={{
                    opacity: settings.opacity,
                    transform: `scale(${settings.scale})`,
                    transformOrigin: settings.position.includes('center') ? 'center' : settings.position
                  }}
                >
                  <img
                    src={settings.logo_url}
                    alt="Watermark Preview"
                    className="max-w-[200px] max-h-[200px] pointer-events-none"
                  />
                </div>
              )}

              {!settings.logo_url && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <Upload className="w-12 h-12 text-white/60 mx-auto mb-3" />
                    <p className="text-white/80 text-sm">Upload a logo to see preview</p>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-2xl">
              <p className="text-sm text-blue-900">
                <strong>Tip:</strong> Use a PNG logo with transparent background for best results.
                The watermark will be applied to all new photos automatically.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
