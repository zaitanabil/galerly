// Gallery Template Selector Component
import { useState } from 'react';
import { Heart, Camera, Briefcase, Users, Sparkles, Check } from 'lucide-react';

interface GalleryTemplate {
  id: string;
  name: string;
  description: string;
  icon: any;
  settings: {
    expiry_days: number;
    download_enabled: boolean;
    watermark_enabled: boolean;
    client_favorites_enabled: boolean;
    email_notification: boolean;
  };
}

interface GalleryTemplateSelectorProps {
  onSelect: (template: GalleryTemplate) => void;
  onSkip: () => void;
}

export default function GalleryTemplateSelector({ onSelect, onSkip }: GalleryTemplateSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const templates: GalleryTemplate[] = [
    {
      id: 'wedding',
      name: 'Wedding',
      description: 'Long-term sharing with favorites and proofing',
      icon: Heart,
      settings: {
        expiry_days: 365,
        download_enabled: true,
        watermark_enabled: false,
        client_favorites_enabled: true,
        email_notification: true
      }
    },
    {
      id: 'portrait',
      name: 'Portrait Session',
      description: 'Quick turnaround with client selection',
      icon: Camera,
      settings: {
        expiry_days: 30,
        download_enabled: true,
        watermark_enabled: true,
        client_favorites_enabled: true,
        email_notification: true
      }
    },
    {
      id: 'event',
      name: 'Event Coverage',
      description: 'Mass sharing with watermarks',
      icon: Users,
      settings: {
        expiry_days: 90,
        download_enabled: true,
        watermark_enabled: true,
        client_favorites_enabled: false,
        email_notification: true
      }
    },
    {
      id: 'commercial',
      name: 'Commercial',
      description: 'Professional delivery without watermarks',
      icon: Briefcase,
      settings: {
        expiry_days: 180,
        download_enabled: true,
        watermark_enabled: false,
        client_favorites_enabled: false,
        email_notification: false
      }
    },
    {
      id: 'custom',
      name: 'Custom',
      description: 'Start from scratch with your own settings',
      icon: Sparkles,
      settings: {
        expiry_days: 90,
        download_enabled: true,
        watermark_enabled: true,
        client_favorites_enabled: true,
        email_notification: true
      }
    }
  ];

  const handleSelect = () => {
    const template = templates.find(t => t.id === selectedTemplate);
    if (template) {
      onSelect(template);
    }
  };

  return (
    <div className="py-6">
      <h3 className="text-lg font-medium text-[#1D1D1F] mb-2 text-center">
        Choose a Template
      </h3>
      <p className="text-sm text-[#1D1D1F]/60 mb-6 text-center">
        Start with a preset or customize everything yourself
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {templates.map((template) => {
          const Icon = template.icon;
          const isSelected = selectedTemplate === template.id;

          return (
            <button
              key={template.id}
              onClick={() => setSelectedTemplate(template.id)}
              className={`text-left p-5 rounded-xl border-2 transition-all ${
                isSelected
                  ? 'border-[#0066CC] bg-blue-50/50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isSelected ? 'bg-[#0066CC] text-white' : 'bg-gray-100 text-[#1D1D1F]/60'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>
                {isSelected && (
                  <div className="w-6 h-6 bg-[#0066CC] rounded-full flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>

              <h4 className="font-medium text-[#1D1D1F] mb-1">{template.name}</h4>
              <p className="text-sm text-[#1D1D1F]/60 mb-3">{template.description}</p>

              {/* Template Settings Preview */}
              <div className="space-y-1.5 text-xs text-[#1D1D1F]/60">
                <div className="flex items-center gap-2">
                  <Check className="w-3 h-3" />
                  <span>{template.settings.expiry_days} days expiry</span>
                </div>
                {template.settings.download_enabled && (
                  <div className="flex items-center gap-2">
                    <Check className="w-3 h-3" />
                    <span>Downloads enabled</span>
                  </div>
                )}
                {template.settings.client_favorites_enabled && (
                  <div className="flex items-center gap-2">
                    <Check className="w-3 h-3" />
                    <span>Client favorites</span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-center">
        <button
          onClick={onSkip}
          className="px-6 py-2.5 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors"
        >
          Skip
        </button>
        <button
          onClick={handleSelect}
          disabled={!selectedTemplate}
          className="px-8 py-2.5 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Use Template
        </button>
      </div>
    </div>
  );
}
