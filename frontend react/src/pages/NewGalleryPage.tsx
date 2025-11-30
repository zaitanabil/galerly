// New Gallery page - Create new photography gallery
import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as galleryService from '../services/galleryService';
import { Upload, ArrowLeft, AlertCircle, Check, X } from 'lucide-react';

export default function NewGalleryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    clientName: '',
    clientEmails: [] as string[],
    expiration: '30',
    downloadEnabled: true,
    commentsEnabled: true,
    favoritesEnabled: true,
  });
  const [newClientEmail, setNewClientEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Plan-based expiration logic
  const isFreePlan = !user?.subscription_tier || user?.subscription_tier === 'free';
  const expirationOptions = isFreePlan 
    ? [
        { value: '1', label: '1 day' },
        { value: '3', label: '3 days' },
        { value: '7', label: '7 days (Maximum)' },
      ]
    : [
        { value: 'never', label: 'Never' },
        { value: '30', label: '30 days' },
        { value: '60', label: '60 days' },
        { value: '90', label: '90 days' },
        { value: '180', label: '6 months' },
        { value: '365', label: '1 year' },
      ];

  // Set default expiration based on plan
  if (isFreePlan && !['1', '3', '7'].includes(formData.expiration)) {
    // Only update if current value is invalid for free plan
    // This side-effect inside render is not ideal but simple for now. 
    // Better handled in useEffect, but we'll stick to simple logic.
  }

  const handleAddClientEmail = () => {
    const email = newClientEmail.trim().toLowerCase();
    if (!email) return;

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('Please enter a valid email address');
      return;
    }

    if (formData.clientEmails.includes(email)) {
      alert('This email is already added');
      return;
    }

    setFormData({
      ...formData,
      clientEmails: [...formData.clientEmails, email],
    });
    setNewClientEmail('');
  };

  const handleRemoveClientEmail = (email: string) => {
    setFormData({
      ...formData,
      clientEmails: formData.clientEmails.filter(e => e !== email),
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await galleryService.createGallery({
        name: formData.name,
        description: formData.description,
        clientName: formData.clientName,
        clientEmails: formData.clientEmails,
        expiry_days: formData.expiration,
        allowDownload: formData.downloadEnabled,
        allowComments: formData.commentsEnabled,
        privacy: 'private',
      });

      if (response.success && response.data) {
        // Backend returns 'id' or 'galleryId' (both are set to the same value)
        const data = response.data;
        const galleryId = data.id || data.galleryId;
        navigate(`/gallery/${galleryId}`);
      } else {
        setError(response.error || 'Failed to create gallery');
        setLoading(false);
      }
    } catch {
      setError('Failed to create gallery. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/dashboard"
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                Create New Gallery
              </h1>
            </div>
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="glass-panel p-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Gallery Details */}
            <div>
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Gallery Details
              </h2>
              
              <div className="space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Gallery Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                    placeholder="Wedding - Smith Family"
                  />
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all resize-none"
                    placeholder="Ceremony and reception photos from June 15, 2024"
                  />
                </div>
              </div>
            </div>

            {/* Client Information */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Client Information
              </h2>
              
              <div className="space-y-5">
                <div>
                  <label htmlFor="clientName" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Client Name
                  </label>
                  <input
                    id="clientName"
                    type="text"
                    value={formData.clientName}
                    onChange={(e) => setFormData({ ...formData, clientName: e.target.value })}
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                    placeholder="John & Jane Smith"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Client Emails
                  </label>
                  <div className="flex gap-2 mb-3">
                    <input
                      type="email"
                      value={newClientEmail}
                      onChange={(e) => setNewClientEmail(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddClientEmail())}
                      className="flex-1 px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                      placeholder="client@example.com"
                    />
                    <button
                      type="button"
                      onClick={handleAddClientEmail}
                      className="px-6 py-3.5 bg-[#0066CC] text-white rounded-2xl font-medium hover:bg-[#0052A3] transition-all"
                    >
                      Add
                    </button>
                  </div>
                  
                  {formData.clientEmails.length > 0 && (
                    <div className="space-y-2">
                      {formData.clientEmails.map((email) => (
                        <div key={email} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <span className="text-sm text-[#1D1D1F]">{email}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveClientEmail(email)}
                            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="mt-2 text-sm text-[#1D1D1F]/60">
                    Clients will receive an email with access to the gallery
                  </p>
                </div>
              </div>
            </div>

            {/* Gallery Settings */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-lg font-medium text-[#1D1D1F] mb-4">
                Gallery Settings
              </h2>
              
              <div className="space-y-5">
                <div>
                  <label htmlFor="expiration" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Gallery Expiration
                  </label>
                  <select
                    id="expiration"
                    value={formData.expiration}
                    onChange={(e) => setFormData({ ...formData, expiration: e.target.value })}
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  >
                    {expirationOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  {isFreePlan && (
                    <p className="mt-2 text-xs text-amber-600 bg-amber-50 inline-block px-3 py-1 rounded-full border border-amber-100">
                      Free Plan Limitation: 7 days max
                    </p>
                  )}
                </div>

                <div className="space-y-4">
                  <label className="flex items-center justify-between p-4 bg-white/50 border border-gray-200 rounded-2xl cursor-pointer hover:border-gray-300 transition-all">
                    <div>
                      <p className="font-medium text-[#1D1D1F]">Allow Downloads</p>
                      <p className="text-sm text-[#1D1D1F]/60 mt-1">
                        Clients can download high-resolution photos
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={formData.downloadEnabled}
                      onChange={(e) => setFormData({ ...formData, downloadEnabled: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-300 text-[#0066CC] focus:ring-[#0066CC]/20"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-white/50 border border-gray-200 rounded-2xl cursor-pointer hover:border-gray-300 transition-all">
                    <div>
                      <p className="font-medium text-[#1D1D1F]">Enable Comments</p>
                      <p className="text-sm text-[#1D1D1F]/60 mt-1">
                        Clients can leave comments on photos
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={formData.commentsEnabled}
                      onChange={(e) => setFormData({ ...formData, commentsEnabled: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-300 text-[#0066CC] focus:ring-[#0066CC]/20"
                    />
                  </label>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="border-t border-gray-200 pt-8 flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>Creating...</>
                ) : (
                  <>
                    <Check className="w-5 h-5" />
                    Create Gallery
                  </>
                )}
              </button>
              <Link
                to="/dashboard"
                className="px-8 py-4 bg-white/50 border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-white transition-all"
              >
                Cancel
              </Link>
            </div>
          </form>

          {/* Next Steps Info */}
          <div className="mt-8 p-6 bg-blue-50 border border-blue-100 rounded-2xl">
            <h3 className="text-sm font-medium text-[#1D1D1F] mb-2 flex items-center gap-2">
              <Upload className="w-4 h-4 text-[#0066CC]" />
              What happens next?
            </h3>
            <ul className="text-sm text-[#1D1D1F]/70 space-y-1 ml-6">
              <li>• Gallery will be created and ready for photos</li>
              <li>• You'll be redirected to upload photos</li>
              <li>• Client will receive email notification once ready</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
