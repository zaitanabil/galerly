import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Workflow, Plus, Play, Pause, Edit2, Trash2, Settings, Mail, Clock } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import { useBrandedModal } from '../components/BrandedModal';

interface WorkflowStep {
  order: number;
  delay_hours: number;
  type: 'email';
  template: string;
  subject?: string;
  content: string;
}

interface OnboardingWorkflow {
  id: string;
  name: string;
  trigger: 'lead_converted' | 'contract_signed' | 'payment_received' | 'appointment_confirmed';
  steps: WorkflowStep[];
  active: boolean;
  created_at: string;
  execution_count: number;
}

const TRIGGER_OPTIONS = [
  { value: 'lead_converted', label: 'Lead Converted' },
  { value: 'contract_signed', label: 'Contract Signed' },
  { value: 'payment_received', label: 'Payment Received' },
  { value: 'appointment_confirmed', label: 'Appointment Confirmed' }
];

export default function OnboardingWorkflowsPage() {
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [workflows, setWorkflows] = useState<OnboardingWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<OnboardingWorkflow | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    trigger: 'lead_converted' as const,
    active: true,
    steps: [
      {
        order: 1,
        delay_hours: 0,
        type: 'email' as const,
        template: 'welcome',
        subject: 'Welcome! Here\'s what to expect',
        content: 'Hi {client_name},\n\nThank you for choosing {photographer_name}! We\'re excited to work with you.'
      }
    ]
  });

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await api.get('/onboarding/workflows');
      if (response.success && response.data) {
        setWorkflows(response.data.workflows || []);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Client Onboarding is a Pro/Ultimate feature');
      } else {
        toast.error('Failed to load workflows');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = editingWorkflow
        ? await api.put(`/onboarding/workflows/${editingWorkflow.id}`, formData)
        : await api.post('/onboarding/workflows', formData);

      if (response.success) {
        toast.success(editingWorkflow ? 'Workflow updated' : 'Workflow created');
        setShowForm(false);
        setEditingWorkflow(null);
        resetForm();
        loadWorkflows();
      } else {
        toast.error(response.error || 'Failed to save workflow');
      }
    } catch (error) {
      toast.error('Failed to save workflow');
    }
  };

  const handleEdit = (workflow: OnboardingWorkflow) => {
    setEditingWorkflow(workflow);
    setFormData({
      name: workflow.name,
      trigger: workflow.trigger,
      active: workflow.active,
      steps: workflow.steps
    });
    setShowForm(true);
  };

  const handleDelete = async (workflow: OnboardingWorkflow) => {
    const confirmed = await showConfirm(
      'Delete Workflow',
      `Delete "${workflow.name}"? This cannot be undone.`,
      'Delete',
      'Cancel'
    );

    if (!confirmed) return;

    try {
      const response = await api.delete(`/onboarding/workflows/${workflow.id}`);
      if (response.success) {
        toast.success('Workflow deleted');
        loadWorkflows();
      } else {
        toast.error('Failed to delete workflow');
      }
    } catch (error) {
      toast.error('Failed to delete workflow');
    }
  };

  const handleToggleActive = async (workflow: OnboardingWorkflow) => {
    try {
      const response = await api.put(`/onboarding/workflows/${workflow.id}`, {
        active: !workflow.active
      });

      if (response.success) {
        toast.success(workflow.active ? 'Workflow paused' : 'Workflow activated');
        loadWorkflows();
      } else {
        toast.error('Failed to update workflow');
      }
    } catch (error) {
      toast.error('Failed to update workflow');
    }
  };

  const addStep = () => {
    setFormData({
      ...formData,
      steps: [
        ...formData.steps,
        {
          order: formData.steps.length + 1,
          delay_hours: 24,
          type: 'email',
          template: 'follow_up',
          subject: '',
          content: ''
        }
      ]
    });
  };

  const updateStep = (index: number, updates: Partial<WorkflowStep>) => {
    const newSteps = [...formData.steps];
    newSteps[index] = { ...newSteps[index], ...updates };
    setFormData({ ...formData, steps: newSteps });
  };

  const removeStep = (index: number) => {
    setFormData({
      ...formData,
      steps: formData.steps.filter((_, i) => i !== index)
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      trigger: 'lead_converted',
      active: true,
      steps: [
        {
          order: 1,
          delay_hours: 0,
          type: 'email',
          template: 'welcome',
          subject: 'Welcome! Here\'s what to expect',
          content: 'Hi {client_name},\n\nThank you for choosing {photographer_name}!'
        }
      ]
    });
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingWorkflow(null);
    resetForm();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading workflows...</p>
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
              <Link to="/onboarding" className="text-sm font-medium text-[#1D1D1F]">Onboarding</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
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
            <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Client Onboarding Workflows</h1>
            <p className="text-[#1D1D1F]/60">Automate client communications with triggered email sequences</p>
          </div>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
            >
              <Plus className="w-4 h-4" />
              Create Workflow
            </button>
          )}
        </div>

        {/* Workflow Form */}
        {showForm && (
          <div className="bg-white rounded-3xl border border-gray-200 p-8 mb-8">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">
              {editingWorkflow ? 'Edit Workflow' : 'New Workflow'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Workflow Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Wedding Photography Onboarding"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Trigger Event *
                  </label>
                  <select
                    value={formData.trigger}
                    onChange={(e) => setFormData({ ...formData, trigger: e.target.value as any })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {TRIGGER_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Workflow Steps */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <label className="text-sm font-medium text-[#1D1D1F]">Email Steps</label>
                  <button
                    type="button"
                    onClick={addStep}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    + Add Step
                  </button>
                </div>

                <div className="space-y-4">
                  {formData.steps.map((step, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-2xl border border-gray-200">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-[#1D1D1F]">Step {index + 1}</span>
                        </div>
                        {index > 0 && (
                          <button
                            type="button"
                            onClick={() => removeStep(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>

                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs font-medium text-[#1D1D1F]/60 mb-1">
                            Delay (hours after trigger)
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={step.delay_hours}
                            onChange={(e) => updateStep(index, { delay_hours: parseInt(e.target.value) })}
                            className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-[#1D1D1F]/60 mb-1">
                            Subject Line
                          </label>
                          <input
                            type="text"
                            value={step.subject}
                            onChange={(e) => updateStep(index, { subject: e.target.value })}
                            className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Welcome to {business_name}"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-[#1D1D1F]/60 mb-1">
                            Email Content
                          </label>
                          <textarea
                            value={step.content}
                            onChange={(e) => updateStep(index, { content: e.target.value })}
                            rows={4}
                            className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono"
                            placeholder="Use variables: {client_name}, {photographer_name}, {business_name}"
                          />
                          <p className="text-xs text-[#1D1D1F]/40 mt-1">
                            Available variables: {'{client_name}'}, {'{photographer_name}'}, {'{business_name}'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
                >
                  {editingWorkflow ? 'Update Workflow' : 'Create Workflow'}
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

        {/* Workflows List */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
          {workflows.length === 0 ? (
            <div className="p-12 text-center">
              <Workflow className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No workflows yet</h3>
              <p className="text-[#1D1D1F]/60 mb-6">Create automated email sequences for client onboarding.</p>
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
              >
                Create First Workflow
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {workflows.map((workflow) => (
                <div key={workflow.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F]">{workflow.name}</h3>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          workflow.active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {workflow.active ? 'Active' : 'Paused'}
                        </span>
                      </div>

                      <div className="flex items-center gap-6 text-sm text-[#1D1D1F]/60 mb-3">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-4 h-4" />
                          Trigger: {TRIGGER_OPTIONS.find(t => t.value === workflow.trigger)?.label}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Mail className="w-4 h-4" />
                          {workflow.steps.length} step{workflow.steps.length !== 1 ? 's' : ''}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Play className="w-4 h-4" />
                          {workflow.execution_count} executions
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {workflow.steps.map((step, idx) => (
                          <div key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                            {step.delay_hours}h delay
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleToggleActive(workflow)}
                        className="p-2 text-purple-600 hover:bg-purple-50 rounded-full transition-all"
                        title={workflow.active ? 'Pause' : 'Activate'}
                      >
                        {workflow.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleEdit(workflow)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-all"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(workflow)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-all"
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
      </main>
    </div>
  );
}
