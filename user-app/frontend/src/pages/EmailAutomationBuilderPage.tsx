import { useState, useEffect } from 'react';
import { 
  Mail, 
  Clock, 
  Users, 
  Plus, 
  Trash2, 
  Save, 
  Play,
  Eye,
  Calendar,
  MessageSquare,
  Download,
  CheckCircle,
  ArrowRight,
  Settings,
  Copy
} from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  type: 'selection_reminder' | 'download_reminder' | 'custom';
}

interface AutomationRule {
  id: string;
  name: string;
  trigger: {
    type: 'gallery_created' | 'selection_deadline' | 'days_after_creation' | 'client_action';
    value?: number; // days
    condition?: string;
  };
  action: {
    type: 'send_email';
    template_id: string;
    template_name?: string;
    delay?: number; // days
  };
  active: boolean;
  created_at: string;
}

interface WorkflowNode {
  id: string;
  type: 'trigger' | 'delay' | 'email' | 'condition';
  data: any;
  position: { x: number; y: number };
}

export default function EmailAutomationBuilder() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [automations, setAutomations] = useState<AutomationRule[]>([]);
  const [selectedAutomation, setSelectedAutomation] = useState<AutomationRule | null>(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'builder' | 'templates' | 'history'>('builder');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [templatesRes, automationsRes] = await Promise.all([
        api.get('/email-templates'),
        api.get('/email-automation/rules')
      ]);

      if (templatesRes.success) setTemplates(templatesRes.data.templates || []);
      if (automationsRes.success) setAutomations(automationsRes.data.rules || []);
    } catch (error) {
      console.error('Failed to load automation data:', error);
      toast.error('Failed to load email automation data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAutomation = async (automation: Partial<AutomationRule>) => {
    setSaving(true);
    const toastId = toast.loading('Creating automation...');

    try {
      const response = await api.post('/email-automation/create-rule', automation);

      if (response.success) {
        toast.success('Automation created successfully!', { id: toastId });
        await loadData();
      } else {
        toast.error(response.error || 'Failed to create automation', { id: toastId });
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to create automation', { id: toastId });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleAutomation = async (automationId: string, active: boolean) => {
    try {
      const response = await api.put(`/email-automation/rule/${automationId}`, { active });

      if (response.success) {
        setAutomations(prev =>
          prev.map(auto =>
            auto.id === automationId ? { ...auto, active } : auto
          )
        );
        toast.success(active ? 'Automation enabled' : 'Automation disabled');
      } else {
        toast.error(response.error || 'Failed to update automation');
      }
    } catch (error) {
      toast.error('Failed to update automation');
    }
  };

  const handleDeleteAutomation = async (automationId: string) => {
    if (!confirm('Are you sure you want to delete this automation?')) return;

    try {
      const response = await api.delete(`/email-automation/rule/${automationId}`);

      if (response.success) {
        setAutomations(prev => prev.filter(auto => auto.id !== automationId));
        toast.success('Automation deleted');
      } else {
        toast.error(response.error || 'Failed to delete automation');
      }
    } catch (error) {
      toast.error('Failed to delete automation');
    }
  };

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case 'gallery_created':
        return Calendar;
      case 'selection_deadline':
        return Clock;
      case 'days_after_creation':
        return Clock;
      case 'client_action':
        return Users;
      default:
        return Mail;
    }
  };

  const getTriggerLabel = (trigger: AutomationRule['trigger']) => {
    switch (trigger.type) {
      case 'gallery_created':
        return 'When gallery is created';
      case 'selection_deadline':
        return `${trigger.value || 3} days before selection deadline`;
      case 'days_after_creation':
        return `${trigger.value || 7} days after gallery creation`;
      case 'client_action':
        return `When client ${trigger.condition || 'views gallery'}`;
      default:
        return 'Unknown trigger';
    }
  };

  const AutomationCard = ({ automation }: { automation: AutomationRule }) => {
    const TriggerIcon = getTriggerIcon(automation.trigger.type);
    const template = templates.find(t => t.id === automation.action.template_id);

    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="p-3 bg-blue-50 rounded-xl">
              <TriggerIcon className="w-5 h-5 text-[#0066CC]" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-[#1D1D1F] mb-1">
                {automation.name}
              </h3>
              <p className="text-sm text-[#1D1D1F]/60 mb-2">
                {getTriggerLabel(automation.trigger)}
              </p>
              <div className="flex items-center gap-2 text-xs text-[#1D1D1F]/50">
                <Mail className="w-3 h-3" />
                <span>{template?.name || 'Unknown template'}</span>
                {automation.action.delay && (
                  <>
                    <ArrowRight className="w-3 h-3" />
                    <Clock className="w-3 h-3" />
                    <span>+{automation.action.delay} days</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleToggleAutomation(automation.id, !automation.active)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                automation.active ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  automation.active ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
            <button
              onClick={() => handleDeleteAutomation(automation.id)}
              className="p-2 hover:bg-red-50 rounded-lg transition-colors text-[#1D1D1F]/40 hover:text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div className={`px-2 py-1 rounded-full ${
            automation.active 
              ? 'bg-green-100 text-green-700' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {automation.active ? 'Active' : 'Inactive'}
          </div>
          <div className="text-[#1D1D1F]/40">
            Created {new Date(automation.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>
    );
  };

  const AutomationBuilder = () => {
    const [builderState, setBuilderState] = useState({
      name: '',
      triggerType: 'days_after_creation',
      triggerValue: 7,
      templateId: '',
      delay: 0
    });

    const handleCreate = () => {
      if (!builderState.name || !builderState.templateId) {
        toast.error('Please fill in all required fields');
        return;
      }

      const newAutomation: Partial<AutomationRule> = {
        name: builderState.name,
        trigger: {
          type: builderState.triggerType as any,
          value: builderState.triggerValue
        },
        action: {
          type: 'send_email',
          template_id: builderState.templateId,
          delay: builderState.delay
        },
        active: true
      };

      handleCreateAutomation(newAutomation);
      
      // Reset form
      setBuilderState({
        name: '',
        triggerType: 'days_after_creation',
        triggerValue: 7,
        templateId: '',
        delay: 0
      });
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-[#1D1D1F] mb-6">
            Create New Automation
          </h2>

          <div className="space-y-6">
            {/* Automation Name */}
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Automation Name
              </label>
              <input
                type="text"
                value={builderState.name}
                onChange={(e) => setBuilderState(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Welcome Email Sequence"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent"
              />
            </div>

            {/* Trigger */}
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                When should this automation run?
              </label>
              <select
                value={builderState.triggerType}
                onChange={(e) => setBuilderState(prev => ({ ...prev, triggerType: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent"
              >
                <option value="gallery_created">When gallery is created</option>
                <option value="days_after_creation">X days after gallery creation</option>
                <option value="selection_deadline">Before selection deadline</option>
              </select>
            </div>

            {/* Trigger Value */}
            {(builderState.triggerType === 'days_after_creation' || 
              builderState.triggerType === 'selection_deadline') && (
              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  {builderState.triggerType === 'selection_deadline' 
                    ? 'Days before deadline' 
                    : 'Days after creation'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="90"
                  value={builderState.triggerValue}
                  onChange={(e) => setBuilderState(prev => ({ ...prev, triggerValue: parseInt(e.target.value) }))}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent"
                />
              </div>
            )}

            {/* Email Template */}
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Email Template
              </label>
              <select
                value={builderState.templateId}
                onChange={(e) => setBuilderState(prev => ({ ...prev, templateId: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent"
              >
                <option value="">Select a template...</option>
                {templates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Additional Delay */}
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Additional Delay (Optional)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="0"
                  max="30"
                  value={builderState.delay}
                  onChange={(e) => setBuilderState(prev => ({ ...prev, delay: parseInt(e.target.value) }))}
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent"
                />
                <span className="text-sm text-[#1D1D1F]/60">days</span>
              </div>
              <p className="text-xs text-[#1D1D1F]/50 mt-1">
                Add extra days after the trigger before sending email
              </p>
            </div>

            {/* Create Button */}
            <button
              onClick={handleCreate}
              disabled={saving}
              className="w-full py-3 bg-[#0066CC] text-white rounded-xl font-semibold hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-5 h-5" />
                  Create Automation
                </>
              )}
            </button>
          </div>
        </div>

        {/* Pre-built Templates */}
        <div className="bg-blue-50 rounded-2xl p-6 border border-blue-100">
          <h3 className="font-semibold text-[#1D1D1F] mb-3 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-[#0066CC]" />
            Quick Start Templates
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              onClick={() => {
                setBuilderState({
                  name: 'Selection Reminder - 3 Days Before',
                  triggerType: 'selection_deadline',
                  triggerValue: 3,
                  templateId: templates.find(t => t.type === 'selection_reminder')?.id || '',
                  delay: 0
                });
              }}
              className="p-4 bg-white rounded-xl text-left hover:shadow-sm transition-all"
            >
              <div className="font-medium text-[#1D1D1F] mb-1">Selection Reminder</div>
              <div className="text-xs text-[#1D1D1F]/60">Remind clients 3 days before deadline</div>
            </button>
            <button
              onClick={() => {
                setBuilderState({
                  name: 'Download Reminder - 14 Days',
                  triggerType: 'days_after_creation',
                  triggerValue: 14,
                  templateId: templates.find(t => t.type === 'download_reminder')?.id || '',
                  delay: 0
                });
              }}
              className="p-4 bg-white rounded-xl text-left hover:shadow-sm transition-all"
            >
              <div className="font-medium text-[#1D1D1F] mb-1">Download Reminder</div>
              <div className="text-xs text-[#1D1D1F]/60">Remind clients to download after 14 days</div>
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50/30 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#1D1D1F] mb-2">
              Email Automation
            </h1>
            <p className="text-[#1D1D1F]/60">
              Set up automated email workflows for your clients
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="px-4 py-2 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {['builder', 'templates', 'history'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-6 py-3 rounded-xl font-medium transition-all capitalize ${
                activeTab === tab
                  ? 'bg-white text-[#0066CC] shadow-sm'
                  : 'text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-white/50'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'builder' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AutomationBuilder />
            </div>
            <div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-6">
                <h3 className="font-semibold text-[#1D1D1F] mb-4">Active Automations</h3>
                <div className="text-center py-8">
                  <div className="text-4xl font-bold text-[#0066CC] mb-2">
                    {automations.filter(a => a.active).length}
                  </div>
                  <div className="text-sm text-[#1D1D1F]/60">
                    Currently running
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-[#0066CC] to-[#0052A3] rounded-2xl p-6 text-white">
                <Play className="w-8 h-8 mb-3" />
                <h3 className="font-semibold mb-2">Pro Tip</h3>
                <p className="text-sm text-white/90">
                  Combine multiple automations to create sophisticated email sequences that nurture client relationships automatically.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {templates.length === 0 ? (
              <div className="lg:col-span-2 bg-white rounded-2xl p-12 text-center">
                <Mail className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-[#1D1D1F] mb-2">
                  No Templates Yet
                </h3>
                <p className="text-[#1D1D1F]/60 mb-4">
                  Create your first email template to get started
                </p>
                <button
                  onClick={() => setShowTemplateModal(true)}
                  className="px-6 py-2 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors"
                >
                  Create Template
                </button>
              </div>
            ) : (
              templates.map(template => (
                <div key={template.id} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-[#1D1D1F] mb-1">
                        {template.name}
                      </h3>
                      <p className="text-sm text-[#1D1D1F]/60">
                        {template.subject}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Eye className="w-4 h-4 text-[#1D1D1F]/60" />
                      </button>
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Copy className="w-4 h-4 text-[#1D1D1F]/60" />
                      </button>
                    </div>
                  </div>
                  <div className="text-xs text-[#1D1D1F]/50 bg-gray-50 rounded-lg p-3">
                    {template.body.substring(0, 100)}...
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <h2 className="text-xl font-semibold text-[#1D1D1F] mb-6">
                Your Automations
              </h2>
              {automations.length === 0 ? (
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-[#1D1D1F] mb-2">
                    No Automations Yet
                  </h3>
                  <p className="text-[#1D1D1F]/60 mb-4">
                    Create your first automation to start saving time
                  </p>
                  <button
                    onClick={() => setActiveTab('builder')}
                    className="px-6 py-2 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors"
                  >
                    Create Automation
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {automations.map(automation => (
                    <AutomationCard key={automation.id} automation={automation} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

