// Enhanced Email Preview Component
import { useState, useEffect } from 'react';
import { Mail, Eye, Code, RefreshCw, Send, X, Smartphone, Monitor } from 'lucide-react';
import { api } from '../utils/api';

interface EmailPreviewProps {
  templateType: 'gallery_share' | 'appointment_confirmation' | 'invoice' | 'payment_reminder' | 'welcome' | 'follow_up';
  data?: Record<string, any>;
  onClose?: () => void;
}

export default function EmailPreview({ templateType, data = {}, onClose }: EmailPreviewProps) {
  const [view, setView] = useState<'preview' | 'html'>('preview');
  const [device, setDevice] = useState<'desktop' | 'mobile'>('desktop');
  const [htmlContent, setHtmlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadPreview();
  }, [templateType, data]);

  const loadPreview = async () => {
    setLoading(true);
    try {
      const response = await api.post('/email-templates/preview', {
        template_type: templateType,
        data: {
          photographer_name: data.photographer_name || 'John Doe',
          client_name: data.client_name || 'Jane Smith',
          gallery_name: data.gallery_name || 'Wedding Gallery',
          gallery_url: data.gallery_url || 'https://galerly.com/gallery/demo',
          ...data
        }
      });
      
      if (response.success) {
        setHtmlContent(response.data.html);
      }
    } catch (error) {
      console.error('Failed to load preview:', error);
      setHtmlContent('<p>Failed to load email preview</p>');
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    setSending(true);
    try {
      const response = await api.post('/email-templates/test', {
        template_type: templateType,
        data
      });
      
      if (response.success) {
        alert('Test email sent successfully!');
      }
    } catch (error) {
      alert('Failed to send test email');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-6xl w-full h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex items-center justify-center">
                <Mail className="w-5 h-5 text-[#0066CC]" />
              </div>
              <div>
                <h2 className="text-xl font-medium text-[#1D1D1F] dark:text-white">
                  Email Preview
                </h2>
                <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">
                  {templateType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* View Toggle */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setView('preview')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    view === 'preview'
                      ? 'bg-white dark:bg-gray-700 text-[#1D1D1F] dark:text-white shadow-sm'
                      : 'text-[#1D1D1F]/60 dark:text-gray-400'
                  }`}
                >
                  <Eye className="w-4 h-4 inline mr-1" />
                  Preview
                </button>
                <button
                  onClick={() => setView('html')}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    view === 'html'
                      ? 'bg-white dark:bg-gray-700 text-[#1D1D1F] dark:text-white shadow-sm'
                      : 'text-[#1D1D1F]/60 dark:text-gray-400'
                  }`}
                >
                  <Code className="w-4 h-4 inline mr-1" />
                  HTML
                </button>
              </div>

              {/* Device Toggle (Preview only) */}
              {view === 'preview' && (
                <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                  <button
                    onClick={() => setDevice('desktop')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      device === 'desktop'
                        ? 'bg-white dark:bg-gray-700 text-[#1D1D1F] dark:text-white shadow-sm'
                        : 'text-[#1D1D1F]/60 dark:text-gray-400'
                    }`}
                  >
                    <Monitor className="w-4 h-4 inline mr-1" />
                    Desktop
                  </button>
                  <button
                    onClick={() => setDevice('mobile')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      device === 'mobile'
                        ? 'bg-white dark:bg-gray-700 text-[#1D1D1F] dark:text-white shadow-sm'
                        : 'text-[#1D1D1F]/60 dark:text-gray-400'
                    }`}
                  >
                    <Smartphone className="w-4 h-4 inline mr-1" />
                    Mobile
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={loadPreview}
                className="px-4 py-2 text-sm border border-gray-200 dark:border-gray-700 text-[#1D1D1F] dark:text-white rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <RefreshCw className="w-4 h-4 inline mr-1" />
                Refresh
              </button>
              <button
                onClick={sendTestEmail}
                disabled={sending}
                className="px-4 py-2 text-sm bg-[#0066CC] text-white rounded-lg hover:bg-[#0052A3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4 inline mr-1" />
                {sending ? 'Sending...' : 'Send Test'}
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden p-6 bg-gray-50 dark:bg-gray-800">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm text-[#1D1D1F]/60 dark:text-gray-400">Loading preview...</p>
              </div>
            </div>
          ) : view === 'preview' ? (
            <div className={`mx-auto bg-white dark:bg-gray-900 rounded-lg shadow-lg overflow-auto h-full ${
              device === 'mobile' ? 'max-w-[375px]' : 'max-w-3xl'
            }`}>
              <iframe
                srcDoc={htmlContent}
                className="w-full h-full border-0"
                title="Email Preview"
                sandbox="allow-same-origin"
              />
            </div>
          ) : (
            <div className="h-full overflow-auto">
              <pre className="bg-gray-900 text-gray-100 p-6 rounded-lg text-sm overflow-x-auto">
                <code>{htmlContent}</code>
              </pre>
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-sm text-[#1D1D1F]/60 dark:text-gray-400">
          <div className="flex items-center justify-between">
            <div>
              Preview using sample data. Actual emails will use real client information.
            </div>
            <div className="flex items-center gap-4">
              <span>Template: <strong>{templateType}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
