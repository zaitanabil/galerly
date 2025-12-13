import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Plus, Edit2, Trash2, Eye, Copy, Settings, Zap } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import { useBrandedModal } from '../components/BrandedModal';

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  type: 'gallery_shared' | 'new_photos' | 'custom' | 'reminder' | 'welcome';
  created_at: string;
  updated_at: string;
  usage_count?: number;
}

const TEMPLATE_TYPES = [
  { value: 'gallery_shared', label: 'Gallery Shared', description: 'When sharing a new gallery' },
  { value: 'new_photos', label: 'New Photos Added', description: 'When adding photos to existing gallery' },
  { value: 'reminder', label: 'Selection Reminder', description: 'Remind clients to select photos' },
  { value: 'welcome', label: 'Welcome Email', description: 'First contact with new clients' },
  { value: 'custom', label: 'Custom', description: 'General purpose template' }
];

const DEFAULT_VARIABLES = [
  '{client_name}',
  '{photographer_name}',
  '{gallery_name}',
  '{gallery_url}',
  '{photo_count}',
  '{business_name}'
];

export default function EmailTemplatesPage() {
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
  const [previewMode, setPreviewMode] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    type: 'custom' as const,
    subject: '',
    body: ''
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await api.get('/email-templates');
      if (response.success && response.data) {
        setTemplates(response.data.templates || []);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Email Templates is a Pro/Ultimate feature');
      } else {
        toast.error('Failed to load templates');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim() || !formData.subject.trim() || !formData.body.trim()) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      const response = editingTemplate
        ? await api.put(`/email-templates/${editingTemplate.id}`, formData)
        : await api.post('/email-templates', formData);

      if (response.success) {
        toast.success(editingTemplate ? 'Template updated' : 'Template created');
        setShowForm(false);
        setEditingTemplate(null);
        resetForm();
        loadTemplates();
      } else {
        toast.error(response.error || 'Failed to save template');
      }
    } catch (error) {
      toast.error('Failed to save template');
    }
  };

  const handleEdit = (template: EmailTemplate) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      type: template.type,
      subject: template.subject,
      body: template.body
    });
    setShowForm(true);
  };

  const handleDelete = async (template: EmailTemplate) => {
    const confirmed = await showConfirm(
      'Delete Template',
      `Delete "${template.name}"? This cannot be undone.`,
      'Delete',
      'Cancel'
    );

    if (!confirmed) return;

    try {
      const response = await api.delete(`/email-templates/${template.id}`);
      if (response.success) {
        toast.success('Template deleted');
        loadTemplates();
      } else {
        toast.error('Failed to delete template');
      }
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const handleDuplicate = (template: EmailTemplate) => {
    setFormData({
      name: `${template.name} (Copy)`,
      type: template.type,
      subject: template.subject,
      body: template.body
    });
    setShowForm(true);
  };

  const handlePreview = async (template: EmailTemplate) => {
    try {
      const response = await api.post(`/email-templates/${template.id}/preview`, {
        client_name: 'John Doe',
        photographer_name: 'Jane Smith',
        gallery_name: 'Wedding Photos',
        gallery_url: 'https://galerly.com/gallery/example',
        photo_count: 42,
        business_name: 'Jane Smith Photography'
      });

      if (response.success && response.data) {
        // Show preview in a modal or new window
        const previewWindow = window.open('', '_blank', 'width=600,height=800');
        if (previewWindow) {
          previewWindow.document.write(`
            <html>
              <head>
                <title>Email Preview: ${template.name}</title>
                <style>
                  body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
                  .email-container { background: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto; }
                  .subject { font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #333; }
                  .body { line-height: 1.6; color: #555; white-space: pre-wrap; }
                </style>
              </head>
              <body>
                <div class="email-container">
                  <div class="subject">Subject: ${response.data.subject}</div>
                  <div class="body">${response.data.body}</div>
                </div>
              </body>
            </html>
          `);
        }
      }
    } catch (error) {
      toast.error('Failed to generate preview');
    }
  };

  const insertVariable = (variable: string) => {
    const textarea = document.querySelector('textarea[name="body"]') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = formData.body;
      const newText = text.substring(0, start) + variable + text.substring(end);
      setFormData({ ...formData, body: newText });
      
      // Set cursor position after inserted variable
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + variable.length, start + variable.length);
      }, 0);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'custom',
      subject: '',
      body: ''
    });
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingTemplate(null);
    resetForm();
  };

  const getTypeLabel = (type: string) => {
    return TEMPLATE_TYPES.find(t => t.value === type)?.label || type;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {ModalComponent}

      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Dashboard</Link>
              <Link to="/email-templates" className="text-sm font-medium text-[#1D1D1F]">Email Templates</Link>
              <Link to="/email-automation" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Automation</Link>
            </nav>
          </div>
          <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-medium text-[#1D1D1F]">Email Templates</h1>
              <span className="px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">Pro</span>
            </div>
            <p className="text-[#1D1D1F]/60">Create custom email templates with variables for client communications</p>
          </div>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
            >
              <Plus className="w-4 h-4" />
              New Template
            </button>
          )}
        </div>

        {/* Template Form */}
        {showForm && (
          <div className="bg-white rounded-3xl border border-gray-200 p-8 mb-8">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">
              {editingTemplate ? 'Edit Template' : 'New Template'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Welcome Email"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Template Type *
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {TEMPLATE_TYPES.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label} - {type.description}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Email Subject *
                </label>
                <input
                  type="text"
                  required
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Your Gallery is Ready!"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-[#1D1D1F]">
                    Email Body *
                  </label>
                  <div className="flex gap-2">
                    {DEFAULT_VARIABLES.map(variable => (
                      <button
                        key={variable}
                        type="button"
                        onClick={() => insertVariable(variable)}
                        className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono hover:bg-blue-100"
                        title={`Insert ${variable}`}
                      >
                        {variable}
                      </button>
                    ))}
                  </div>
                </div>
                <textarea
                  name="body"
                  required
                  rows={12}
                  value={formData.body}
                  onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono"
                  placeholder="Hi {client_name},&#10;&#10;Your gallery {gallery_name} is ready! View it here:&#10;{gallery_url}&#10;&#10;Thanks,&#10;{photographer_name}"
                />
                <p className="text-xs text-[#1D1D1F]/40 mt-2">
                  Use variables like {'{client_name}'}, {'{gallery_url}'}, {'{photo_count}'} which will be replaced with actual values
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
                >
                  {editingTemplate ? 'Update Template' : 'Create Template'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-6 py-2.5 bg-gray-100 text-[#1D1D1F] rounded-full text-sm font-medium hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Templates List */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
          {templates.length === 0 ? (
            <div className="p-12 text-center">
              <Mail className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No templates yet</h3>
              <p className="text-[#1D1D1F]/60 mb-6">Create custom email templates to streamline client communications.</p>
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
              >
                Create First Template
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {templates.map((template) => (
                <div key={template.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F]">{template.name}</h3>
                        <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                          {getTypeLabel(template.type)}
                        </span>
                      </div>

                      <p className="text-sm text-[#1D1D1F]/60 mb-3">
                        <strong>Subject:</strong> {template.subject}
                      </p>

                      <p className="text-sm text-[#1D1D1F]/70 mb-3 line-clamp-2">
                        {template.body.substring(0, 150)}...
                      </p>

                      <div className="flex gap-4 text-xs text-[#1D1D1F]/40">
                        <span>Created {new Date(template.created_at).toLocaleDateString()}</span>
                        {template.usage_count !== undefined && (
                          <span>Used {template.usage_count} times</span>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handlePreview(template)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-full transition-all"
                        title="Preview"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDuplicate(template)}
                        className="p-2 text-purple-600 hover:bg-purple-50 rounded-full transition-all"
                        title="Duplicate"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(template)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-all"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(template)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-all"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Link to Automation */}
        <div className="mt-8 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">Automate Your Emails</h3>
              <p className="text-sm text-[#1D1D1F]/70 mb-4">
                Set up automated email workflows that use your templates to send perfectly timed messages to clients.
              </p>
              <Link
                to="/email-automation"
                className="inline-block px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
              >
                Go to Email Automation
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
