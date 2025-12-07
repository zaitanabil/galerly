import { useState, useEffect } from 'react';
import { Archive, Download, Clock, CheckCircle, AlertCircle, Trash2, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useBrandedModal } from '../components/BrandedModal';

interface VaultFile {
  id: string;
  original_filename: string;
  file_size_mb: number;
  camera_make?: string;
  camera_model?: string;
  status: 'archiving' | 'archived' | 'retrieving' | 'available';
  archived_at: string;
  retrieval_tier?: string;
  retrieval_completion_time?: string;
  storage_class: string;
}

export default function RAWVaultPage() {
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [vaultFiles, setVaultFiles] = useState<VaultFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalStorage, setTotalStorage] = useState({ mb: 0, gb: 0 });
  const [showRetrievalModal, setShowRetrievalModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<VaultFile | null>(null);
  const [retrievalTier, setRetrievalTier] = useState<'bulk' | 'standard' | 'expedited'>('bulk');

  useEffect(() => {
    loadVaultFiles();
    // Auto-refresh every 5 minutes to check retrieval status
    const interval = setInterval(loadVaultFiles, 300000);
    return () => clearInterval(interval);
  }, []);

  const loadVaultFiles = async () => {
    try {
      const response = await api.get('/raw-vault');
      if (response.success && response.data) {
        setVaultFiles(response.data.vault_files || []);
        setTotalStorage({
          mb: response.data.total_storage_mb || 0,
          gb: response.data.total_storage_gb || 0
        });
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('RAW Vault is an Ultimate plan feature');
      } else {
        console.error('Error loading vault files:', error);
        toast.error('Failed to load vault files');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRetrieval = async () => {
    if (!selectedFile) return;

    try {
      const response = await api.post(`/raw-vault/${selectedFile.id}/retrieve`, {
        tier: retrievalTier
      });

      if (response.success) {
        toast.success(`Retrieval initiated (${retrievalTier} tier)`);
        setShowRetrievalModal(false);
        setSelectedFile(null);
        loadVaultFiles();
      } else {
        toast.error(response.error || 'Failed to request retrieval');
      }
    } catch (error) {
      console.error('Error requesting retrieval:', error);
      toast.error('Failed to request retrieval');
    }
  };

  const handleDownload = async (file: VaultFile) => {
    try {
      const response = await api.get(`/raw-vault/${file.id}/download`);
      if (response.success && response.data?.download_url) {
        window.open(response.data.download_url, '_blank');
        toast.success('Download started');
      } else {
        toast.error('File not yet available for download');
      }
    } catch (error) {
      console.error('Error downloading file:', error);
      toast.error('Download failed');
    }
  };

  const handleDelete = async (file: VaultFile) => {
    const confirmed = await showConfirm(
      'Delete RAW File',
      `Permanently delete "${file.original_filename}" from vault? This cannot be undone.`,
      'Delete',
      'Cancel'
    );

    if (!confirmed) return;

    try {
      const response = await api.delete(`/raw-vault/${file.id}`);
      if (response.success) {
        toast.success('File deleted from vault');
        loadVaultFiles();
      } else {
        toast.error('Failed to delete file');
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      toast.error('Delete failed');
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      archiving: { color: 'bg-blue-100 text-blue-800', icon: RefreshCw, text: 'Archiving' },
      archived: { color: 'bg-gray-100 text-gray-800', icon: Archive, text: 'Archived' },
      retrieving: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, text: 'Retrieving' },
      available: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: 'Available' }
    };

    const badge = badges[status as keyof typeof badges] || badges.archived;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3.5 h-3.5" />
        {badge.text}
      </span>
    );
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-[#0066CC] animate-spin mx-auto mb-4" />
          <p className="text-[#1D1D1F]/60">Loading vault...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7] pt-32 pb-20 px-4 md:px-6">
      <ModalComponent />
      
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-medium text-[#1D1D1F] mb-2">RAW Vault</h1>
            <p className="text-[#1D1D1F]/60">Long-term cold storage for your RAW files</p>
          </div>
          <Link
            to="/dashboard"
            className="px-6 py-3 bg-[#1D1D1F] text-white rounded-full hover:bg-black transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>

        {/* Storage Stats */}
        <div className="glass-panel p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-[#1D1D1F]/60 mb-1">Total Files</p>
              <p className="text-3xl font-medium text-[#1D1D1F]">{vaultFiles.length}</p>
            </div>
            <div>
              <p className="text-sm text-[#1D1D1F]/60 mb-1">Total Storage</p>
              <p className="text-3xl font-medium text-[#1D1D1F]">{totalStorage.gb.toFixed(2)} GB</p>
            </div>
            <div>
              <p className="text-sm text-[#1D1D1F]/60 mb-1">Storage Class</p>
              <p className="text-lg font-medium text-[#1D1D1F]">Glacier Deep Archive</p>
            </div>
          </div>
        </div>

        {/* Files List */}
        {vaultFiles.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <Archive className="w-16 h-16 text-[#1D1D1F]/20 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No files in vault</h3>
            <p className="text-[#1D1D1F]/60 mb-6">
              Archive your RAW files here for long-term, cost-effective storage
            </p>
            <Link
              to="/galleries"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#0066CC] text-white rounded-full hover:bg-[#0052a3] transition-colors"
            >
              Go to Galleries
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {vaultFiles.map((file) => (
              <div key={file.id} className="glass-panel p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-[#1D1D1F]">{file.original_filename}</h3>
                      {getStatusBadge(file.status)}
                    </div>
                    
                    <div className="flex flex-wrap gap-4 text-sm text-[#1D1D1F]/60">
                      {file.camera_make && file.camera_model && (
                        <span>{file.camera_make} {file.camera_model}</span>
                      )}
                      <span>{file.file_size_mb.toFixed(2)} MB</span>
                      <span>Archived {formatDate(file.archived_at)}</span>
                    </div>

                    {file.status === 'retrieving' && file.retrieval_completion_time && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-yellow-700">
                        <Clock className="w-4 h-4" />
                        <span>Estimated completion: {formatDate(file.retrieval_completion_time)}</span>
                      </div>
                    )}

                    {file.status === 'available' && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-green-700">
                        <CheckCircle className="w-4 h-4" />
                        <span>File is available for download (7 days)</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {file.status === 'archived' && (
                      <button
                        onClick={() => {
                          setSelectedFile(file);
                          setShowRetrievalModal(true);
                        }}
                        className="px-4 py-2 bg-[#0066CC] text-white rounded-full hover:bg-[#0052a3] transition-colors text-sm font-medium"
                      >
                        Request Retrieval
                      </button>
                    )}

                    {file.status === 'available' && (
                      <button
                        onClick={() => handleDownload(file)}
                        className="px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    )}

                    <button
                      onClick={() => handleDelete(file)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Retrieval Modal */}
      {showRetrievalModal && selectedFile && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-lg w-full">
            <h2 className="text-2xl font-medium text-[#1D1D1F] mb-4">Request File Retrieval</h2>
            <p className="text-[#1D1D1F]/60 mb-6">
              Select retrieval speed for: <strong>{selectedFile.original_filename}</strong>
            </p>

            <div className="space-y-3 mb-6">
              {[
                { value: 'bulk', label: 'Bulk', time: '12-48 hours', cost: 'Cheapest' },
                { value: 'standard', label: 'Standard', time: '3-5 hours', cost: 'Moderate' },
                { value: 'expedited', label: 'Expedited', time: '1-5 minutes', cost: 'Most expensive' }
              ].map((tier) => (
                <button
                  key={tier.value}
                  onClick={() => setRetrievalTier(tier.value as any)}
                  className={`w-full p-4 rounded-2xl border-2 text-left transition-all ${
                    retrievalTier === tier.value
                      ? 'border-[#0066CC] bg-[#0066CC]/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-[#1D1D1F]">{tier.label}</span>
                    <span className="text-sm text-[#1D1D1F]/60">{tier.cost}</span>
                  </div>
                  <p className="text-sm text-[#1D1D1F]/60">{tier.time}</p>
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowRetrievalModal(false);
                  setSelectedFile(null);
                }}
                className="flex-1 px-6 py-3 bg-gray-100 text-[#1D1D1F] rounded-full hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRequestRetrieval}
                className="flex-1 px-6 py-3 bg-[#0066CC] text-white rounded-full hover:bg-[#0052a3] transition-colors"
              >
                Request Retrieval
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
