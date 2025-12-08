// Changelog / What's New Modal
import { useState, useEffect } from 'react';
import { X, Sparkles, Check, ArrowRight } from 'lucide-react';

interface ChangelogEntry {
  version: string;
  date: string;
  type: 'feature' | 'improvement' | 'fix';
  items: {
    title: string;
    description: string;
    icon?: string;
  }[];
}

const changelog: ChangelogEntry[] = [
  {
    version: '2.5.0',
    date: 'December 7, 2025',
    type: 'feature',
    items: [
      {
        title: 'Enhanced Email Preview',
        description: 'Preview emails in desktop and mobile views before sending'
      },
      {
        title: 'Analytics Export',
        description: 'Export your analytics data in CSV or PDF format'
      },
      {
        title: 'Invoice & Contract PDFs',
        description: 'Generate professional PDFs for invoices and signed contracts'
      },
      {
        title: 'Calendar Integration',
        description: 'Subscribe to your appointment calendar in any calendar app'
      },
      {
        title: 'Product Tours',
        description: 'Interactive walkthroughs to help you discover new features'
      }
    ]
  },
  {
    version: '2.4.0',
    date: 'November 2025',
    type: 'feature',
    items: [
      {
        title: 'Client Onboarding Automation',
        description: 'Create automated email workflows for new clients'
      },
      {
        title: 'Payment Reminders',
        description: 'Automatic reminders for unpaid invoices'
      },
      {
        title: 'Photo Sales & Packages',
        description: 'Sell photos and packages directly to clients'
      }
    ]
  },
  {
    version: '2.3.0',
    date: 'October 2025',
    type: 'feature',
    items: [
      {
        title: 'CRM & Lead Scoring',
        description: 'Manage leads with automatic quality scoring'
      },
      {
        title: 'Testimonials',
        description: 'Collect and display client testimonials on your portfolio'
      },
      {
        title: 'Services Page',
        description: 'Showcase your photography services and pricing'
      }
    ]
  }
];

interface WhatsNewModalProps {
  onClose: () => void;
}

export default function WhatsNewModal({ onClose }: WhatsNewModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState(0);

  useEffect(() => {
    // Check if user has seen the latest version
    const lastSeenVersion = localStorage.getItem('last_seen_changelog_version');
    const latestVersion = changelog[0].version;

    if (lastSeenVersion !== latestVersion) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    // Mark latest version as seen
    localStorage.setItem('last_seen_changelog_version', changelog[0].version);
    setIsOpen(false);
    onClose();
  };

  if (!isOpen) return null;

  const currentChangelog = changelog[selectedVersion];

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'feature': return 'bg-blue-100 text-blue-700';
      case 'improvement': return 'bg-green-100 text-green-700';
      case 'fix': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-[#0066CC] to-purple-600 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-medium text-[#1D1D1F] dark:text-white">
                  What's New in Galerly
                </h2>
                <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
                  Discover the latest features and improvements
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-white/50 dark:hover:bg-gray-800 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar - Version List */}
          <div className="w-48 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            {changelog.map((entry, idx) => (
              <button
                key={entry.version}
                onClick={() => setSelectedVersion(idx)}
                className={`w-full text-left p-4 border-b border-gray-100 dark:border-gray-800 transition-colors ${
                  selectedVersion === idx
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-[#0066CC]'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <div className="font-medium text-[#1D1D1F] dark:text-white text-sm">
                  v{entry.version}
                </div>
                <div className="text-xs text-[#1D1D1F]/60 dark:text-gray-400 mt-1">
                  {entry.date.split(' ')[0]}
                </div>
                {idx === 0 && (
                  <div className="mt-2">
                    <span className="inline-block px-2 py-0.5 bg-[#0066CC] text-white text-xs rounded-full">
                      Latest
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Content - Version Details */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-xl font-medium text-[#1D1D1F] dark:text-white">
                  Version {currentChangelog.version}
                </h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getTypeColor(currentChangelog.type)}`}>
                  {currentChangelog.type.charAt(0).toUpperCase() + currentChangelog.type.slice(1)}
                </span>
              </div>
              <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
                {currentChangelog.date}
              </p>
            </div>

            <div className="space-y-4">
              {currentChangelog.items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Check className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-[#1D1D1F] dark:text-white mb-1">
                      {item.title}
                    </h4>
                    <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {selectedVersion === 0 && (
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl">
                <p className="text-sm text-[#1D1D1F] dark:text-white mb-3">
                  Want to learn more about these features?
                </p>
                <button className="px-4 py-2 bg-[#0066CC] text-white rounded-lg hover:bg-[#0052A3] transition-colors text-sm font-medium flex items-center gap-2">
                  Take a Tour
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
            Have feedback? Let us know!
          </p>
          <button
            onClick={handleClose}
            className="px-6 py-2 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors font-medium"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}

// Badge component to show "New" on menu items
export function NewFeatureBadge({ featureName }: { featureName: string }) {
  const [isNew, setIsNew] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(`new_feature_dismissed_${featureName}`);
    if (!dismissed) {
      setIsNew(true);
    }
  }, [featureName]);

  if (!isNew) return null;

  return (
    <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full animate-pulse">
      New
    </span>
  );
}
