import { useState, useEffect } from 'react';
import { Droplet, Upload, Check, AlertCircle, Image as ImageIcon, Sliders } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface WatermarkConfigProps {
  onUpdate?: () => void;
}

interface WatermarkSettings {
  watermark_s3_key: string;
  watermark_enabled: boolean;
  watermark_position: string;
  watermark_opacity: number;
  watermark_size_percent: number;
}

export default function WatermarkConfig({ onUpdate }: WatermarkConfigProps) {
  const [settings, setSettings] = useState<WatermarkSettings>({
    watermark_s3_key: '',
    watermark_enabled: false,
    watermark_position: 'bottom-right',
    watermark_opacity: 0.7,
    watermark_size_percent: 15
  });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/profile/watermark-settings');
      if (response.success && response.data) {
        setSettings(response.data);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Watermarking is available on Plus, Pro, and Ultimate plans');
      } else {
        console.error('Failed to load watermark settings:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Logo file must be less than 2MB');
      return;
    }

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload a PNG, JPG, or WebP image');
      return;
    }

    setUploading(true);
    const toastId = toast.loading('Uploading watermark logo...');

    try {
      // Read file as base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target?.result as string;

        try {
          const response = await api.post('/profile/watermark-logo', {
            file_data: base64Data,
            filename: file.name
          });

          if (response.success && response.data) {
            toast.success('Watermark logo uploaded successfully!', { id: toastId });
            setSettings(prev => ({ ...prev, watermark_s3_key: response.data.s3_key }));
            setPreviewUrl(base64Data);
            
            if (onUpdate) {
              onUpdate();
            }
          } else {
            toast.error(response.error || 'Failed to upload logo', { id: toastId });
          }
        } catch (error: any) {
          const errorMsg = error.response?.data?.error || 'Failed to upload logo';
          toast.error(errorMsg, { id: toastId });
        } finally {
          setUploading(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error('Failed to read file', { id: toastId });
      setUploading(false);
    }
  };

  const handleSettingsUpdate = async () => {
    setSaving(true);
    const toastId = toast.loading('Saving watermark settings...');

    try {
      const response = await api.put('/profile/watermark-settings', {
        watermark_enabled: settings.watermark_enabled,
        watermark_position: settings.watermark_position,
        watermark_opacity: settings.watermark_opacity,
        watermark_size_percent: settings.watermark_size_percent
      });

      if (response.success) {
        toast.success('Watermark settings saved successfully!', { id: toastId });
        
        if (onUpdate) {
          onUpdate();
        }
      } else {
        toast.error(response.error || 'Failed to save settings', { id: toastId });
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to save settings';
      toast.error(errorMsg, { id: toastId });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const positions = [
    { value: 'top-left', label: 'Top Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'bottom-right', label: 'Bottom Right' },
    { value: 'center', label: 'Center' }
  ];

  return (
    <div className="space-y-8">
      {/* Enable/Disable Toggle */}
      <div className="bg-white/50 backdrop-blur-lg border border-gray-200 rounded-3xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-50 rounded-2xl">
              <Droplet className="w-6 h-6 text-[#0066CC]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[#1D1D1F] mb-1">
                Automatic Watermarking
              </h3>
              <p className="text-sm text-[#1D1D1F]/60">
                Apply your watermark to all uploaded photos automatically
              </p>
            </div>
          </div>
          
          <button
            type="button"
            onClick={() => setSettings(prev => ({ ...prev, watermark_enabled: !prev.watermark_enabled }))}
            className={`
              relative w-14 h-8 rounded-full transition-colors duration-300
              ${settings.watermark_enabled ? 'bg-[#0066CC]' : 'bg-gray-300'}
            `}
            disabled={!settings.watermark_s3_key}
          >
            <div
              className={`
                absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition-transform duration-300
                ${settings.watermark_enabled ? 'translate-x-6' : 'translate-x-0'}
              `}
            />
          </button>
        </div>

        {!settings.watermark_s3_key && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-100 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800">
              Upload a watermark logo below to enable automatic watermarking
            </p>
          </div>
        )}
      </div>

      {/* Logo Upload */}
      <div className="bg-white/50 backdrop-blur-lg border border-gray-200 rounded-3xl p-6">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-4 flex items-center gap-2">
          <ImageIcon className="w-5 h-5" />
          Watermark Logo
        </h3>

        <div className="space-y-4">
          {previewUrl || settings.watermark_s3_key ? (
            <div className="flex items-start gap-4">
              <div className="w-32 h-32 bg-gray-100 rounded-2xl border-2 border-gray-200 flex items-center justify-center overflow-hidden">
                {previewUrl ? (
                  <img src={previewUrl} alt="Watermark preview" className="max-w-full max-h-full object-contain" />
                ) : (
                  <ImageIcon className="w-12 h-12 text-gray-400" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-green-700">Logo uploaded</span>
                </div>
                <p className="text-xs text-[#1D1D1F]/60 mb-4">
                  Your watermark logo is ready to use
                </p>
                <label className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-[#1D1D1F] hover:bg-gray-50 transition-colors cursor-pointer">
                  <Upload className="w-4 h-4" />
                  Replace Logo
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={handleLogoUpload}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
              </div>
            </div>
          ) : (
            <label className="block w-full border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center hover:border-[#0066CC] hover:bg-blue-50/30 transition-all cursor-pointer">
              <div className="flex flex-col items-center">
                <div className="p-4 bg-blue-50 rounded-2xl mb-4">
                  <Upload className="w-8 h-8 text-[#0066CC]" />
                </div>
                <h4 className="text-sm font-semibold text-[#1D1D1F] mb-1">
                  Upload Watermark Logo
                </h4>
                <p className="text-xs text-[#1D1D1F]/60 mb-4">
                  PNG, JPG, or WebP • Max 2MB
                </p>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#0066CC] text-white rounded-xl text-sm font-medium">
                  Choose File
                </div>
              </div>
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={handleLogoUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>
          )}

          {uploading && (
            <div className="flex items-center gap-2 text-sm text-[#0066CC]">
              <div className="w-4 h-4 border-2 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
              Uploading...
            </div>
          )}
        </div>
      </div>

      {/* Watermark Configuration */}
      {settings.watermark_s3_key && (
        <div className="bg-white/50 backdrop-blur-lg border border-gray-200 rounded-3xl p-6">
          <h3 className="text-lg font-semibold text-[#1D1D1F] mb-6 flex items-center gap-2">
            <Sliders className="w-5 h-5" />
            Watermark Configuration
          </h3>

          <div className="space-y-6">
            {/* Position */}
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-3">
                Position
              </label>
              <div className="grid grid-cols-5 gap-2">
                {positions.map((pos) => (
                  <button
                    key={pos.value}
                    type="button"
                    onClick={() => setSettings(prev => ({ ...prev, watermark_position: pos.value }))}
                    className={`
                      px-3 py-2 rounded-xl text-xs font-medium transition-all
                      ${settings.watermark_position === pos.value
                        ? 'bg-[#0066CC] text-white'
                        : 'bg-white border border-gray-200 text-[#1D1D1F] hover:border-[#0066CC]'
                      }
                    `}
                  >
                    {pos.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Opacity */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-[#1D1D1F]">
                  Opacity
                </label>
                <span className="text-sm font-semibold text-[#0066CC]">
                  {Math.round(settings.watermark_opacity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.watermark_opacity}
                onChange={(e) => setSettings(prev => ({ ...prev, watermark_opacity: parseFloat(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0066CC]"
              />
              <div className="flex justify-between text-xs text-[#1D1D1F]/40 mt-1">
                <span>Transparent</span>
                <span>Opaque</span>
              </div>
            </div>

            {/* Size */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-[#1D1D1F]">
                  Size
                </label>
                <span className="text-sm font-semibold text-[#0066CC]">
                  {settings.watermark_size_percent}%
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={settings.watermark_size_percent}
                onChange={(e) => setSettings(prev => ({ ...prev, watermark_size_percent: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0066CC]"
              />
              <div className="flex justify-between text-xs text-[#1D1D1F]/40 mt-1">
                <span>Small (5%)</span>
                <span>Large (50%)</span>
              </div>
            </div>

            {/* Save Button */}
            <button
              type="button"
              onClick={handleSettingsUpdate}
              disabled={saving}
              className="w-full py-3 bg-[#0066CC] text-white rounded-2xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  Save Watermark Settings
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-2xl">
        <h4 className="text-sm font-semibold text-[#1D1D1F] mb-2">
          How Watermarking Works
        </h4>
        <ul className="text-xs text-[#1D1D1F]/70 space-y-1">
          <li>• Watermarks are applied automatically to all new photo uploads</li>
          <li>• Original photos without watermarks are stored separately for downloads</li>
          <li>• Changes take effect immediately for new uploads</li>
          <li>• You can batch-apply watermarks to existing photos from the gallery page</li>
        </ul>
      </div>
    </div>
  );
}
