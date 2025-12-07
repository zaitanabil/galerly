// Email Templates page - Manage email templates for galleries
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, Check, AlertCircle, RotateCcw, Eye, Save, X, ChevronRight } from 'lucide-react';
import { api } from '../utils/api';
import { useBrandedModal } from '../components/BrandedModal';

interface TemplateSummary {
  type: string;
  customized: boolean;
  variables: string[];
  last_updated?: string;
}

interface TemplateDetails {
  user_id?: string;
  template_type: string;
  subject: string;
  html_body: string;
  text_body?: string;
  is_default?: boolean;
}

const TEMPLATE_LABELS: Record<string, string> = {
  gallery_ready: 'Gallery Ready',
  gallery_shared_with_account: 'Gallery Shared (Existing User)',
  gallery_shared_no_account: 'Gallery Shared (New User)',
  new_photos_added: 'New Photos Added',
  selection_reminder: 'Selection Reminder',
  custom_message: 'Custom Message',
  client_selected_photos: 'Client Selected Photos',
  client_feedback_received: 'Client Feedback Received',
};

export default function EmailTemplatesPage() {
  const { showAlert, showConfirm, ModalComponent } = useBrandedModal();
  
  // List state
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  
  // Editor state
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [editorData, setEditorData] = useState<TemplateDetails | null>(null);
  const [loadingEditor, setLoadingEditor] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Preview state
  const [previewData, setPreviewData] = useState<{ subject: string; html: string } | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // Messages
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadTemplatesList();
  }, []);

  const loadTemplatesList = async () => {
    setLoadingList(true);
    try {
      const response = await api.get<{ templates: TemplateSummary[] }>('/email-templates');
      if (response.success && response.data) {
        setTemplates(response.data.templates || []);
      }
    } catch (error) {
      console.error('Failed to load templates list:', error);
    } finally {
      setLoadingList(false);
    }
  };

  const loadTemplateDetails = async (type: string) => {
    setLoadingEditor(true);
    setEditorData(null);
    setMessage({ type: '', text: '' });
    
    try {
      const response = await api.get<{ template: TemplateDetails; is_custom: boolean }>(`/email-templates/${type}`);
      if (response.success && response.data) {
        const tpl = response.data.template;
        // Map backend response to editor format
        setEditorData({
            template_type: type,
            subject: tpl.subject || '',
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            html_body: tpl.html_body || (tpl as any).html || '', // Backend might return html_body or html
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            text_body: tpl.text_body || (tpl as any).text || '',
            is_default: response.data.is_custom === false
        });
      } else {
        setMessage({ type: 'error', text: 'Failed to load template details' });
      }
    } catch (error) {
      console.error('Failed to load template:', error);
      setMessage({ type: 'error', text: 'An error occurred loading the template' });
    } finally {
      setLoadingEditor(false);
    }
  };

  const handleSelectTemplate = (type: string) => {
    setSelectedType(type);
    loadTemplateDetails(type);
    setShowPreview(false);
    setPreviewData(null);
  };

  const handleBack = () => {
    setSelectedType(null);
    setEditorData(null);
    setMessage({ type: '', text: '' });
  };

  const handleSave = async () => {
    if (!selectedType || !editorData) return;
    
    setSaving(true);
    setMessage({ type: '', text: '' });
    
    try {
      const response = await api.put(`/email-templates/${selectedType}`, {
        subject: editorData.subject,
        html_body: editorData.html_body,
        text_body: editorData.text_body || editorData.html_body.replace(/<[^>]*>?/gm, '') // Fallback text
      });

      if (response.success) {
        setMessage({ type: 'success', text: 'Template saved successfully!' });
        // Update list to show "Customized"
        loadTemplatesList();
        // Refresh editor to confirm state
        loadTemplateDetails(selectedType);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to save template' });
      }
    } catch (error) {
      console.error('Error saving template:', error);
      setMessage({ type: 'error', text: 'An error occurred while saving.' });
    } finally {
      setSaving(false);
    }
  };

  const handleRevert = async () => {
    if (!selectedType) return;
    const confirmed = await showConfirm(
      'Revert to Default',
      'Are you sure you want to revert to the default template?\n\nThis cannot be undone.',
      'Revert',
      'Cancel',
      'danger'
    );
    
    if (!confirmed) return;
    
    setSaving(true);
    try {
      const response = await api.delete(`/email-templates/${selectedType}`);
      if (response.success) {
        setMessage({ type: 'success', text: 'Reverted to default template.' });
        loadTemplatesList();
        loadTemplateDetails(selectedType);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to revert template' });
      }
    } catch (error) {
        console.error('Error reverting template:', error);
    } finally {
        setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!selectedType || !editorData) return;
    
    setSaving(true); // Reuse loading state
    try {
        const response = await api.post<{ preview: { subject: string; html: string } }>(`/email-templates/${selectedType}/preview`, {
            subject: editorData.subject,
            html_body: editorData.html_body,
            text_body: editorData.text_body
        });
        
        if (response.success && response.data?.preview) {
            setPreviewData({
                subject: response.data.preview.subject,
                html: response.data.preview.html
            });
            setShowPreview(true);
        } else {
            await showAlert('Error', 'Failed to generate preview: ' + response.error, 'error');
        }
    } catch (error) {
        console.error('Preview error:', error);
    } finally {
        setSaving(false);
    }
  };

  const getVariables = (type: string) => {
    const t = templates.find(t => t.type === type);
    return t?.variables || [];
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={selectedType ? "#" : "/dashboard"}
                onClick={selectedType ? handleBack : undefined}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                {selectedType ? (TEMPLATE_LABELS[selectedType] || selectedType) : 'Email Templates'}
              </h1>
            </div>
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {message.text && (
          <div
            className={`mb-6 p-4 rounded-2xl flex items-start gap-3 max-w-3xl mx-auto ${
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
            <p className={`text-sm ${message.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              {message.text}
            </p>
          </div>
        )}

        {!selectedType ? (
          // LIST VIEW
          <div className="max-w-4xl mx-auto">
            <div className="flex items-start gap-4 mb-8">
              <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center">
                <Mail className="w-6 h-6 text-[#0066CC]" />
              </div>
              <div>
                <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-2">
                  Customize Email Templates
                </h2>
                <p className="text-[#1D1D1F]/60">
                  Personalize the automated emails sent to your clients.
                </p>
              </div>
            </div>

            {loadingList ? (
               <div className="flex justify-center py-12">
                  <div className="w-8 h-8 border-2 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
               </div>
            ) : (
              <div className="grid gap-4">
                {templates.map((template) => (
                  <button
                    key={template.type}
                    onClick={() => handleSelectTemplate(template.type)}
                    className="w-full glass-panel p-6 flex items-center justify-between group hover:shadow-lg transition-all text-left"
                  >
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h3 className="text-lg font-medium text-[#1D1D1F]">
                                {TEMPLATE_LABELS[template.type] || template.type}
                            </h3>
                            {template.customized && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                                    Customized
                                </span>
                            )}
                        </div>
                        <p className="text-sm text-[#1D1D1F]/60">
                            {template.variables.length} variables available
                        </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-[#0066CC] transition-colors" />
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          // EDITOR VIEW
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
             {/* Left Column: Editor */}
             <div className="lg:col-span-2 space-y-6">
                {loadingEditor || !editorData ? (
                    <div className="glass-panel p-12 flex justify-center">
                        <div className="w-8 h-8 border-2 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <div className="glass-panel p-8">
                        {/* Subject */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Subject Line</label>
                            <input
                                type="text"
                                value={editorData.subject}
                                onChange={(e) => setEditorData({ ...editorData, subject: e.target.value })}
                                className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                            />
                        </div>

                        {/* HTML Body */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                                Email Body (HTML)
                            </label>
                            <textarea
                                value={editorData.html_body}
                                onChange={(e) => setEditorData({ ...editorData, html_body: e.target.value })}
                                rows={15}
                                className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] font-mono text-sm"
                            />
                            <p className="mt-2 text-xs text-gray-500">
                                Supports standard HTML tags. Use variables to insert dynamic content.
                            </p>
                        </div>
                    </div>
                )}
             </div>

             {/* Right Column: Variables & Actions */}
             <div className="space-y-6">
                {/* Actions */}
                <div className="glass-panel p-6">
                    <h3 className="text-sm font-medium text-[#1D1D1F] mb-4">Actions</h3>
                    <div className="space-y-3">
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="w-full py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? 'Saving...' : 'Save Template'}
                        </button>
                        <button
                            onClick={handlePreview}
                            disabled={saving}
                            className="w-full py-3 bg-white border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                        >
                            <Eye className="w-4 h-4" />
                            Preview
                        </button>
                        
                        {!editorData?.is_default && (
                             <button
                                onClick={handleRevert}
                                disabled={saving}
                                className="w-full py-3 bg-red-50 text-red-600 rounded-xl font-medium hover:bg-red-100 transition-all flex items-center justify-center gap-2"
                            >
                                <RotateCcw className="w-4 h-4" />
                                Revert to Default
                            </button>
                        )}
                    </div>
                </div>

                {/* Variables */}
                <div className="glass-panel p-6">
                    <h3 className="text-sm font-medium text-[#1D1D1F] mb-4">Available Variables</h3>
                    <div className="flex flex-wrap gap-2">
                        {getVariables(selectedType).map((variable) => (
                            <code
                                key={variable}
                                className="px-2 py-1 bg-blue-50 text-[#0066CC] rounded text-xs font-mono border border-blue-100 cursor-pointer hover:bg-blue-100 transition-colors"
                                onClick={() => {
                                    // Could implement insert at cursor logic here
                                    navigator.clipboard.writeText(`{{${variable}}}`);
                                }}
                                title="Click to copy"
                            >
                                {`{{${variable}}}`}
                            </code>
                        ))}
                    </div>
                    <p className="mt-4 text-xs text-gray-500">
                        Click a variable to copy it to clipboard. Paste it into your subject or body.
                    </p>
                </div>
             </div>
          </div>
        )}

        {/* Preview Modal */}
        {showPreview && previewData && (
            <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-6">
                <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl">
                    <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                        <h3 className="text-lg font-medium">Preview: {previewData.subject}</h3>
                        <button onClick={() => setShowPreview(false)} className="p-2 hover:bg-gray-100 rounded-full">
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-8 bg-gray-50">
                        <div className="bg-white p-8 rounded-xl shadow-sm mx-auto max-w-2xl" dangerouslySetInnerHTML={{ __html: previewData.html }} />
                    </div>
                </div>
            </div>
        )}

      </main>

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}
