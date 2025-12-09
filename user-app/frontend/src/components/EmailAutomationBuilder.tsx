import { useState } from 'react';
import {
  Mail, Clock, Users, Zap, Plus, Trash2, Save, Play,
  ChevronDown, ChevronRight, Calendar, MessageSquare
} from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface AutomationStep {
  id: string;
  type: 'trigger' | 'delay' | 'email' | 'condition';
  config: {
    trigger?: string;
    delayDays?: number;
    emailTemplate?: string;
    subject?: string;
    condition?: string;
  };
}

interface AutomationWorkflow {
  id: string;
  name: string;
  description: string;
  active: boolean;
  steps: AutomationStep[];
}

const TRIGGER_OPTIONS = [
  { value: 'gallery_created', label: 'When gallery is created', icon: Users },
  { value: 'gallery_shared', label: 'When gallery is shared with client', icon: Mail },
  { value: 'client_views', label: 'When client views gallery', icon: Play },
  { value: 'photos_favorited', label: 'When client favorites photos', icon: MessageSquare },
  { value: 'no_activity', label: 'When client has no activity', icon: Clock }
];

const EMAIL_TEMPLATES = [
  { value: 'welcome', label: 'Welcome Email', description: 'Introduce your services' },
  { value: 'selection_reminder', label: 'Selection Reminder', description: 'Remind to select favorites' },
  { value: 'download_reminder', label: 'Download Reminder', description: 'Remind to download photos' },
  { value: 'thank_you', label: 'Thank You', description: 'Thank client for their business' },
  { value: 'review_request', label: 'Review Request', description: 'Ask for a testimonial' },
  { value: 'custom', label: 'Custom Email', description: 'Write your own message' }
];

export default function EmailAutomationBuilder() {
  const [workflows, setWorkflows] = useState<AutomationWorkflow[]>([
    {
      id: '1',
      name: 'New Client Onboarding',
      description: 'Automated welcome sequence for new clients',
      active: true,
      steps: [
        {
          id: 's1',
          type: 'trigger',
          config: { trigger: 'gallery_shared' }
        },
        {
          id: 's2',
          type: 'email',
          config: {
            emailTemplate: 'welcome',
            subject: 'Welcome! Your photos are ready'
          }
        },
        {
          id: 's3',
          type: 'delay',
          config: { delayDays: 3 }
        },
        {
          id: 's4',
          type: 'email',
          config: {
            emailTemplate: 'selection_reminder',
            subject: 'Don\'t forget to select your favorites'
          }
        }
      ]
    }
  ]);

  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>('1');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);

  const currentWorkflow = workflows.find(w => w.id === selectedWorkflow);

  const addStep = (type: AutomationStep['type']) => {
    if (!currentWorkflow) return;

    const newStep: AutomationStep = {
      id: `s${Date.now()}`,
      type,
      config: {}
    };

    setWorkflows(workflows.map(w =>
      w.id === selectedWorkflow
        ? { ...w, steps: [...w.steps, newStep] }
        : w
    ));
  };

  const updateStep = (stepId: string, config: AutomationStep['config']) => {
    if (!currentWorkflow) return;

    setWorkflows(workflows.map(w =>
      w.id === selectedWorkflow
        ? {
            ...w,
            steps: w.steps.map(s =>
              s.id === stepId ? { ...s, config: { ...s.config, ...config } } : s
            )
          }
        : w
    ));
  };

  const deleteStep = (stepId: string) => {
    if (!currentWorkflow) return;

    setWorkflows(workflows.map(w =>
      w.id === selectedWorkflow
        ? { ...w, steps: w.steps.filter(s => s.id !== stepId) }
        : w
    ));
  };

  const toggleWorkflow = (workflowId: string) => {
    setWorkflows(workflows.map(w =>
      w.id === workflowId ? { ...w, active: !w.active } : w
    ));
  };

  const saveWorkflow = async () => {
    if (!currentWorkflow) return;

    setSaving(true);
    const toastId = toast.loading('Saving automation workflow...');

    try {
      // Save workflow (API endpoint would be implemented)
      await api.post('/email-automation/workflows', currentWorkflow);
      
      toast.success('Workflow saved successfully!', { id: toastId });
    } catch (error: any) {
      toast.error('Failed to save workflow', { id: toastId });
    } finally {
      setSaving(false);
    }
  };

  const createNewWorkflow = () => {
    const newWorkflow: AutomationWorkflow = {
      id: `w${Date.now()}`,
      name: 'New Workflow',
      description: 'Describe your automation',
      active: false,
      steps: []
    };

    setWorkflows([...workflows, newWorkflow]);
    setSelectedWorkflow(newWorkflow.id);
  };

  const renderStep = (step: AutomationStep, index: number) => {
    const isExpanded = expanded[step.id];

    return (
      <div key={step.id} className="relative">
        {/* Connection Line */}
        {index > 0 && (
          <div className="absolute left-6 -top-6 w-0.5 h-6 bg-gray-300" />
        )}

        <div className="bg-white border-2 border-gray-200 rounded-2xl overflow-hidden hover:border-[#0066CC] transition-colors">
          {/* Step Header */}
          <div
            className="p-4 cursor-pointer flex items-center justify-between"
            onClick={() => setExpanded({ ...expanded, [step.id]: !isExpanded })}
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${
                step.type === 'trigger' ? 'bg-blue-50' :
                step.type === 'email' ? 'bg-green-50' :
                step.type === 'delay' ? 'bg-amber-50' :
                'bg-purple-50'
              }`}>
                {step.type === 'trigger' && <Zap className="w-5 h-5 text-blue-600" />}
                {step.type === 'email' && <Mail className="w-5 h-5 text-green-600" />}
                {step.type === 'delay' && <Clock className="w-5 h-5 text-amber-600" />}
                {step.type === 'condition' && <ChevronRight className="w-5 h-5 text-purple-600" />}
              </div>
              <div>
                <div className="text-sm font-semibold text-[#1D1D1F] capitalize">
                  {step.type === 'trigger' && 'Trigger'}
                  {step.type === 'email' && 'Send Email'}
                  {step.type === 'delay' && 'Wait'}
                  {step.type === 'condition' && 'Condition'}
                </div>
                <div className="text-xs text-[#1D1D1F]/60">
                  {step.type === 'trigger' && (TRIGGER_OPTIONS.find(t => t.value === step.config.trigger)?.label || 'Select trigger')}
                  {step.type === 'email' && (step.config.subject || 'Configure email')}
                  {step.type === 'delay' && `${step.config.delayDays || 0} day${step.config.delayDays !== 1 ? 's' : ''}`}
                  {step.type === 'condition' && 'Configure condition'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteStep(step.id);
                }}
                className="p-2 hover:bg-red-50 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4 text-red-600" />
              </button>
              {isExpanded ? (
                <ChevronDown className="w-5 h-5 text-[#1D1D1F]/40" />
              ) : (
                <ChevronRight className="w-5 h-5 text-[#1D1D1F]/40" />
              )}
            </div>
          </div>

          {/* Step Configuration */}
          {isExpanded && (
            <div className="p-4 pt-0 space-y-4">
              {step.type === 'trigger' && (
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Select Trigger
                  </label>
                  <select
                    value={step.config.trigger || ''}
                    onChange={(e) => updateStep(step.id, { trigger: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm"
                  >
                    <option value="">Choose a trigger event...</option>
                    {TRIGGER_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {step.type === 'email' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                      Email Template
                    </label>
                    <select
                      value={step.config.emailTemplate || ''}
                      onChange={(e) => updateStep(step.id, { emailTemplate: e.target.value })}
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm"
                    >
                      <option value="">Select template...</option>
                      {EMAIL_TEMPLATES.map(template => (
                        <option key={template.value} value={template.value}>
                          {template.label} - {template.description}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                      Subject Line
                    </label>
                    <input
                      type="text"
                      value={step.config.subject || ''}
                      onChange={(e) => updateStep(step.id, { subject: e.target.value })}
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm"
                      placeholder="Enter email subject..."
                    />
                  </div>
                </div>
              )}

              {step.type === 'delay' && (
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Wait Duration (days)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="365"
                    value={step.config.delayDays || 0}
                    onChange={(e) => updateStep(step.id, { delayDays: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#1D1D1F] mb-2">
            Email Automation Workflows
          </h2>
          <p className="text-[#1D1D1F]/60">
            Create automated email sequences for your clients
          </p>
        </div>
        
        <button
          onClick={createNewWorkflow}
          className="flex items-center gap-2 px-4 py-2 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Workflow
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Workflows List */}
        <div className="lg:col-span-1 bg-white border border-gray-200 rounded-3xl p-4">
          <h3 className="text-sm font-semibold text-[#1D1D1F] mb-4 uppercase tracking-wider">
            Workflows
          </h3>
          <div className="space-y-2">
            {workflows.map(workflow => (
              <div
                key={workflow.id}
                onClick={() => setSelectedWorkflow(workflow.id)}
                className={`p-3 rounded-xl cursor-pointer transition-colors ${
                  selectedWorkflow === workflow.id
                    ? 'bg-blue-50 border-2 border-[#0066CC]'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-[#1D1D1F]">
                    {workflow.name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleWorkflow(workflow.id);
                    }}
                    className={`w-8 h-5 rounded-full transition-colors ${
                      workflow.active ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  >
                    <div
                      className={`w-3 h-3 bg-white rounded-full transition-transform ${
                        workflow.active ? 'translate-x-4' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                <p className="text-xs text-[#1D1D1F]/60 truncate">
                  {workflow.description}
                </p>
                <div className="text-xs text-[#1D1D1F]/40 mt-1">
                  {workflow.steps.length} step{workflow.steps.length !== 1 ? 's' : ''}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Workflow Builder */}
        <div className="lg:col-span-3 space-y-6">
          {currentWorkflow ? (
            <>
              {/* Workflow Info */}
              <div className="bg-white border border-gray-200 rounded-3xl p-6">
                <input
                  type="text"
                  value={currentWorkflow.name}
                  onChange={(e) => setWorkflows(workflows.map(w =>
                    w.id === currentWorkflow.id ? { ...w, name: e.target.value } : w
                  ))}
                  className="text-2xl font-bold text-[#1D1D1F] mb-2 w-full border-none outline-none bg-transparent"
                  placeholder="Workflow Name"
                />
                <input
                  type="text"
                  value={currentWorkflow.description}
                  onChange={(e) => setWorkflows(workflows.map(w =>
                    w.id === currentWorkflow.id ? { ...w, description: e.target.value } : w
                  ))}
                  className="text-[#1D1D1F]/60 w-full border-none outline-none bg-transparent"
                  placeholder="Add a description..."
                />
              </div>

              {/* Steps */}
              <div className="bg-gray-50 border border-gray-200 rounded-3xl p-6">
                <h3 className="text-lg font-semibold text-[#1D1D1F] mb-6">
                  Workflow Steps
                </h3>

                <div className="space-y-6">
                  {currentWorkflow.steps.map((step, index) => renderStep(step, index))}

                  {currentWorkflow.steps.length === 0 && (
                    <div className="text-center py-8 text-[#1D1D1F]/40">
                      Add steps to build your automation workflow
                    </div>
                  )}
                </div>

                {/* Add Step Buttons */}
                <div className="mt-6 flex flex-wrap gap-2">
                  <button
                    onClick={() => addStep('trigger')}
                    disabled={currentWorkflow.steps.some(s => s.type === 'trigger')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-xl text-sm font-medium hover:bg-blue-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Zap className="w-4 h-4" />
                    Add Trigger
                  </button>
                  <button
                    onClick={() => addStep('email')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-xl text-sm font-medium hover:bg-green-100 transition-colors"
                  >
                    <Mail className="w-4 h-4" />
                    Add Email
                  </button>
                  <button
                    onClick={() => addStep('delay')}
                    className="flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-xl text-sm font-medium hover:bg-amber-100 transition-colors"
                  >
                    <Clock className="w-4 h-4" />
                    Add Delay
                  </button>
                </div>
              </div>

              {/* Save Button */}
              <div className="flex justify-end">
                <button
                  onClick={saveWorkflow}
                  disabled={saving || currentWorkflow.steps.length === 0}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white rounded-2xl font-semibold hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      Save Workflow
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            <div className="bg-white border border-gray-200 rounded-3xl p-12 text-center">
              <Calendar className="w-16 h-16 text-[#1D1D1F]/20 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[#1D1D1F] mb-2">
                No Workflow Selected
              </h3>
              <p className="text-sm text-[#1D1D1F]/60">
                Select a workflow from the left or create a new one
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="bg-blue-50 border border-blue-100 rounded-3xl p-6">
        <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3">
          How Email Automation Works
        </h4>
        <ul className="text-sm text-[#1D1D1F]/70 space-y-2">
          <li>• <strong>Triggers</strong> start the workflow when specific events occur</li>
          <li>• <strong>Emails</strong> are automatically sent based on your templates</li>
          <li>• <strong>Delays</strong> control timing between steps</li>
          <li>• <strong>Active workflows</strong> run automatically in the background</li>
          <li>• Toggle workflows on/off anytime without losing your setup</li>
        </ul>
      </div>
    </div>
  );
}
