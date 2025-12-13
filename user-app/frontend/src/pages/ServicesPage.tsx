import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Plus, Edit2, Trash2, DollarSign, Clock, Settings, Eye } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import { useBrandedModal } from '../components/BrandedModal';

interface Service {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  duration_minutes?: number;
  is_public: boolean;
  category?: string;
  created_at: string;
}

export default function ServicesPage() {
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [showForm, setShowForm] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    currency: 'USD',
    duration_minutes: '',
    is_public: true,
    category: ''
  });

  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      const response = await api.get('/services');
      if (response.success && response.data) {
        setServices(response.data.services || []);
      }
    } catch (error) {
      toast.error('Failed to load services');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        duration_minutes: formData.duration_minutes ? parseInt(formData.duration_minutes) : undefined
      };

      let response;
      if (editingService) {
        response = await api.put(`/services/${editingService.id}`, payload);
      } else {
        response = await api.post('/services', payload);
      }

      if (response.success) {
        toast.success(editingService ? 'Service updated' : 'Service created');
        setShowForm(false);
        setEditingService(null);
        resetForm();
        loadServices();
      } else {
        toast.error(response.error || 'Failed to save service');
      }
    } catch (error) {
      toast.error('Failed to save service');
    }
  };

  const handleEdit = (service: Service) => {
    setEditingService(service);
    setFormData({
      name: service.name,
      description: service.description,
      price: service.price.toString(),
      currency: service.currency,
      duration_minutes: service.duration_minutes?.toString() || '',
      is_public: service.is_public,
      category: service.category || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (service: Service) => {
    const confirmed = await showConfirm(
      'Delete Service',
      `Delete "${service.name}"? This cannot be undone.`,
      'Delete',
      'Cancel'
    );

    if (!confirmed) return;

    try {
      const response = await api.delete(`/services/${service.id}`);
      if (response.success) {
        toast.success('Service deleted');
        loadServices();
      } else {
        toast.error('Failed to delete service');
      }
    } catch (error) {
      toast.error('Failed to delete service');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      price: '',
      currency: 'USD',
      duration_minutes: '',
      is_public: true,
      category: ''
    });
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingService(null);
    resetForm();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading services...</p>
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
              <Link to="/services" className="text-sm font-medium text-[#1D1D1F]">Services</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
            </nav>
          </div>
          <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] mb-2">Services</h1>
            <p className="text-[#1D1D1F]/60">Manage your photography services and packages</p>
          </div>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
            >
              <Plus className="w-4 h-4" />
              Add Service
            </button>
          )}
        </div>

        {/* Service Form */}
        {showForm && (
          <div className="bg-white rounded-3xl border border-gray-200 p-8 mb-8">
            <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">
              {editingService ? 'Edit Service' : 'New Service'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Service Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Wedding Photography"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Category
                  </label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Weddings, Portraits, etc."
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Description *
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Describe your service..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Price *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="1500.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Currency
                  </label>
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Duration (minutes)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.duration_minutes}
                    onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="480"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_public" className="text-sm text-[#1D1D1F]">
                  Show on public portfolio
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
                >
                  {editingService ? 'Update Service' : 'Create Service'}
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

        {/* Services List */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
          {services.length === 0 ? (
            <div className="p-12 text-center">
              <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No services yet</h3>
              <p className="text-[#1D1D1F]/60 mb-6">Create your first service to showcase on your portfolio.</p>
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
              >
                Create First Service
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {services.map((service) => (
                <div key={service.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F]">{service.name}</h3>
                        {service.is_public && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">
                            <Eye className="w-3 h-3" />
                            Public
                          </span>
                        )}
                        {service.category && (
                          <span className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                            {service.category}
                          </span>
                        )}
                      </div>
                      
                      <p className="text-sm text-[#1D1D1F]/70 mb-3">{service.description}</p>
                      
                      <div className="flex gap-6 text-sm text-[#1D1D1F]/60">
                        <div className="flex items-center gap-1.5">
                          <DollarSign className="w-4 h-4" />
                          {service.price.toLocaleString()} {service.currency}
                        </div>
                        {service.duration_minutes && (
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            {service.duration_minutes} min
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleEdit(service)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-all"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(service)}
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
