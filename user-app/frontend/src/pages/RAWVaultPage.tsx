import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Archive, HardDrive, Download, Trash2, Clock, CheckCircle, AlertCircle, Settings } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface VaultedFile {
  id: string;
  photo_id: string;
  filename: string;
  file_size: number;
  archived_at: string;
  retrieval_status?: 'pending' | 'in_progress' | 'completed';
  retrieval_initiated_at?: string;
  glacier_archive_id: string;
  estimated_retrieval_time?: string;
}

export default function RAWVaultPage() {
  const [vaultedFiles, setVaultedFiles] = useState<VaultedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_files: 0,
    total_size_gb: 0,
    pending_retrievals: 0
  });

  useEffect(() => {
    loadVaultedFiles();
  }, []);

  const loadVaultedFiles = async () => {
    try {
      const response = await api.get('/raw-vault/list');
      if (response.success && response.data) {
        const files = response.data.files || [];
        setVaultedFiles(files);
        
        // Calculate stats
        const totalSize = files.reduce((sum: number, f: VaultedFile) => sum + (f.file_size || 0), 0);
        const pending = files.filter((f: VaultedFile) => 
          f.retrieval_status === 'pending' || f.retrieval_status === 'in_progress'
        ).length;
        
        setStats({
          total_files: files.length,
          total_size_gb: +(totalSize / (1024 ** 3)).toFixed(2),
          pending_retrievals: pending
        });
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('RAW Vault is an Ultimate plan feature');
      } else {
        toast.error('Failed to load vaulted files');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInitiateRetrieval = async (fileId: string, filename: string) => {
    if (!confirm(`Initiate retrieval for "${filename}"? This will take 12-48 hours and may incur additional costs.`)) {
      return;
    }

    try {
      const response = await api.post(`/raw-vault/${fileId}/retrieve`);
      if (response.success) {
        toast.success('Retrieval initiated. You will be notified when ready.');
        loadVaultedFiles();
      } else {
        toast.error('Failed to initiate retrieval');
      }
    } catch (error) {
      toast.error('Failed to initiate retrieval');
    }
  };

  const handleCheckRetrievalStatus = async (fileId: string) => {
    try {
      const response = await api.get(`/raw-vault/${fileId}/status`);
      if (response.success && response.data) {
        const status = response.data.retrieval_status;
        const statusMessages: Record<string, string> = {
          pending: 'Retrieval is pending (12-48 hours)',
          in_progress: 'Retrieval in progress',
          completed: 'File is ready for download!'
        };
        toast.success(statusMessages[status] || 'Status unknown');
        loadVaultedFiles();
      }
    } catch (error) {
      toast.error('Failed to check status');
    }
  };

  const handleDownload = async (fileId: string, filename: string) => {
    try {
      const response = await api.get(`/raw-vault/${fileId}/download`);
      if (response.success && response.data?.download_url) {
        window.open(response.data.download_url, '_blank');
        toast.success('Download started');
      } else {
        toast.error('File not ready for download yet');
      }
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  const handleDelete = async (fileId: string, filename: string) => {
    if (!confirm(`Permanently delete "${filename}" from Glacier? This cannot be undone.`)) {
      return;
    }

    try {
      const response = await api.delete(`/raw-vault/${fileId}`);
      if (response.success) {
        toast.success('File deleted from vault');
        loadVaultedFiles();
      } else {
        toast.error('Failed to delete file');
      }
    } catch (error) {
      toast.error('Failed to delete file');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 ** 3) return `${(bytes / (1024 ** 2)).toFixed(1)} MB`;
    return `${(bytes / (1024 ** 3)).toFixed(2)} GB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (file: VaultedFile) => {
    if (!file.retrieval_status) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
          <Archive className="w-3.5 h-3.5" />
          Archived
        </span>
      );
    }

    const badges = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: Clock, label: 'Retrieval Pending' },
      in_progress: { color: 'bg-purple-100 text-purple-800 border-purple-200', icon: Clock, label: 'Retrieving' },
      completed: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle, label: 'Ready' }
    };

    const badge = badges[file.retrieval_status] || badges.pending;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
        <Icon className="w-3.5 h-3.5" />
        {badge.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading vault...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Dashboard</Link>
              <Link to="/raw-vault" className="text-sm font-medium text-[#1D1D1F]">RAW Vault</Link>
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
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-medium text-[#1D1D1F]">RAW Vault</h1>
            <span className="px-2.5 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">Ultimate</span>
          </div>
          <p className="text-[#1D1D1F]/60">Long-term cold storage for RAW and original files using AWS Glacier Deep Archive</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total Files', value: stats.total_files, color: 'text-blue-600', bg: 'bg-blue-50', icon: Archive },
            { label: 'Total Storage', value: `${stats.total_size_gb} GB`, color: 'text-purple-600', bg: 'bg-purple-50', icon: HardDrive },
            { label: 'Pending Retrievals', value: stats.pending_retrievals, color: 'text-yellow-600', bg: 'bg-yellow-50', icon: Clock }
          ].map((stat, i) => (
            <div key={i} className="bg-white p-5 rounded-3xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">{stat.label}</span>
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-3xl font-medium text-[#1D1D1F]">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-8">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-blue-900 mb-1">About Glacier Deep Archive</h3>
              <p className="text-sm text-blue-800">
                Files are stored in AWS Glacier Deep Archive for long-term, low-cost storage. 
                Retrieval takes 12-48 hours and incurs a small retrieval fee ($0.02/GB). 
                Perfect for archiving completed project RAW files you rarely need to access.
              </p>
            </div>
          </div>
        </div>

        {/* Vaulted Files List */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden">
          {vaultedFiles.length === 0 ? (
            <div className="p-12 text-center">
              <Archive className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No files in vault yet</h3>
              <p className="text-[#1D1D1F]/60 mb-6">Archive RAW and original files from your galleries to free up storage space.</p>
              <Link
                to="/dashboard"
                className="inline-block px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black"
              >
                Go to Galleries
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {vaultedFiles.map((file) => (
                <div key={file.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F]">{file.filename}</h3>
                        {getStatusBadge(file)}
                      </div>

                      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-[#1D1D1F]/60 mb-3">
                        <div className="flex items-center gap-1.5">
                          <HardDrive className="w-4 h-4" />
                          {formatFileSize(file.file_size)}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Archive className="w-4 h-4" />
                          Archived {formatDate(file.archived_at)}
                        </div>
                        {file.retrieval_initiated_at && (
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            Retrieval started {formatDate(file.retrieval_initiated_at)}
                          </div>
                        )}
                      </div>

                      {file.estimated_retrieval_time && file.retrieval_status !== 'completed' && (
                        <p className="text-xs text-[#1D1D1F]/40 mb-3">
                          Estimated ready: {formatDate(file.estimated_retrieval_time)}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {!file.retrieval_status && (
                        <button
                          onClick={() => handleInitiateRetrieval(file.id, file.filename)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-all"
                          title="Initiate retrieval (12-48 hours)"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                      
                      {(file.retrieval_status === 'pending' || file.retrieval_status === 'in_progress') && (
                        <button
                          onClick={() => handleCheckRetrievalStatus(file.id)}
                          className="p-2 text-purple-600 hover:bg-purple-50 rounded-full transition-all"
                          title="Check retrieval status"
                        >
                          <Clock className="w-4 h-4" />
                        </button>
                      )}
                      
                      {file.retrieval_status === 'completed' && (
                        <button
                          onClick={() => handleDownload(file.id, file.filename)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-full transition-all"
                          title="Download file"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDelete(file.id, file.filename)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-all"
                        title="Delete permanently"
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
