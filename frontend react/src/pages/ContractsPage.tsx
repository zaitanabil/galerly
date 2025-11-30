import { useState, useEffect } from 'react';
import { Plus, FileText, Send, Trash2, X, CheckCircle, Lock } from 'lucide-react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface Contract {
  id: string;
  title: string;
  client_name: string;
  client_email: string;
  status: 'draft' | 'sent' | 'signed';
  created_at: string;
  signed_at?: string;
}

export default function ContractsPage() {
  const { user } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Plan gating
  const isAllowed = user?.plan === 'pro' || user?.plan === 'ultimate';

  // New Contract Form
  const [newContract, setNewContract] = useState({
    title: 'Photography Agreement',
    client_name: '',
    client_email: '',
    content: `AGREEMENT TERMS
1. SERVICES: The Photographer agrees to provide photography services as discussed.
2. PAYMENT: The Client agrees to pay the total amount due before the delivery of images.
3. COPYRIGHT: The Photographer retains copyright of all images.
4. CANCELLATION: Cancellations must be made 48 hours in advance.

[Standard terms - customize as needed]`
  });

  useEffect(() => {
    if (isAllowed) {
      fetchContracts();
    } else {
      setLoading(false);
    }
  }, [isAllowed]);

  const fetchContracts = async () => {
    try {
      const response = await api.get('/contracts');
      setContracts(response.data.contracts);
    } catch (error) {
      console.error('Error fetching contracts:', error);
      toast.error('Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContract = async () => {
    try {
      if (!newContract.client_email || !newContract.content) {
        toast.error('Please fill in required fields');
        return;
      }

      await api.post('/contracts', newContract);
      toast.success('Contract created');
      setShowCreateModal(false);
      fetchContracts();
      // Reset (keep content template)
      setNewContract(prev => ({
        ...prev,
        client_name: '',
        client_email: ''
      }));
    } catch (error) {
      console.error('Error creating contract:', error);
      toast.error('Failed to create contract');
    }
  };

  const handleDeleteContract = async (id: string) => {
    if (!confirm('Are you sure you want to delete this contract?')) return;
    try {
      await api.delete(`/contracts/${id}`);
      toast.success('Contract deleted');
      setContracts(contracts.filter(c => c.id !== id));
    } catch (error) {
      console.error('Error deleting contract:', error);
      toast.error('Failed to delete contract');
    }
  };

  const handleSendContract = async (id: string) => {
    try {
      await api.post(`/contracts/${id}/send`);
      toast.success('Contract sent to client');
      fetchContracts();
    } catch (error) {
      console.error('Error sending contract:', error);
      toast.error('Failed to send contract');
    }
  };

  if (!isAllowed) {
    return (
      <div className="min-h-screen bg-[#F5F5F7]">
        <Header />
        <main className="pt-32 pb-20 px-4 md:px-6 max-w-7xl mx-auto text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-[#1D1D1F] mb-4">Contracts & Signatures</h1>
            <p className="text-[#1D1D1F]/70 text-lg mb-8">
              Protect your business with legally binding contracts. Collect digital signatures from clients before the shoot.
            </p>
            <div className="bg-white p-6 rounded-2xl border border-gray-200 mb-8 text-left">
              <h3 className="font-semibold text-[#1D1D1F] mb-4">Pro Plan Features:</h3>
              <ul className="space-y-3">
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  Digital Signatures (eSign)
                </li>
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  Contract Templates
                </li>
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  Audit Trail
                </li>
              </ul>
            </div>
            <Link 
              to="/billing" 
              className="inline-flex items-center justify-center px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Upgrade to Pro
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <Header />
      
      <main className="pt-24 pb-20 px-4 md:px-6 max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-[#1D1D1F]">Contracts</h1>
            <p className="text-[#1D1D1F]/60 mt-1">Legally binding agreements & eSignatures</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full hover:bg-black transition-colors"
          >
            <Plus className="w-4 h-4" /> New Contract
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div className="col-span-full text-center py-12 text-gray-400">Loading contracts...</div>
          ) : contracts.length === 0 ? (
            <div className="col-span-full bg-white rounded-3xl p-12 text-center border border-gray-100">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No contracts found. Create one to get started.</p>
            </div>
          ) : (
            contracts.map(contract => (
              <div key={contract.id} className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow relative group">
                <div className="flex justify-between items-start mb-4">
                  <div className={`p-3 rounded-2xl ${
                    contract.status === 'signed' ? 'bg-green-100 text-green-700' : 
                    contract.status === 'sent' ? 'bg-blue-100 text-blue-700' : 
                    'bg-gray-100 text-gray-700'
                  }`}>
                    <FileText className="w-6 h-6" />
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${
                    contract.status === 'signed' ? 'bg-green-50 text-green-700' : 
                    contract.status === 'sent' ? 'bg-blue-50 text-blue-700' : 
                    'bg-gray-100 text-gray-500'
                  }`}>
                    {contract.status}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-[#1D1D1F] mb-1 truncate">{contract.title}</h3>
                <p className="text-sm text-gray-500 mb-4">
                  {contract.client_name} • {contract.client_email}
                </p>

                <div className="text-xs text-gray-400 mb-6">
                  {contract.status === 'signed' 
                    ? `Signed on ${new Date(contract.signed_at!).toLocaleDateString()}`
                    : `Created on ${new Date(contract.created_at).toLocaleDateString()}`
                  }
                </div>

                <div className="flex gap-2">
                  {contract.status === 'draft' && (
                    <button
                      className="flex-1 py-2 bg-[#1D1D1F] text-white text-sm font-medium rounded-xl hover:bg-black transition-colors flex items-center justify-center gap-2"
                      onClick={() => handleSendContract(contract.id)}
                    >
                      <Send className="w-3.5 h-3.5" /> Send
                    </button>
                  )}
                  {contract.status === 'signed' && (
                    <button className="flex-1 py-2 bg-green-50 text-green-700 text-sm font-medium rounded-xl border border-green-100 flex items-center justify-center gap-2 cursor-default">
                      <CheckCircle className="w-3.5 h-3.5" /> Signed
                    </button>
                  )}
                  {contract.status === 'sent' && (
                    <button className="flex-1 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-xl border border-blue-100 flex items-center justify-center gap-2 cursor-default">
                      <Send className="w-3.5 h-3.5" /> Sent
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleDeleteContract(contract.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-[#1D1D1F]">New Contract</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contract Title</label>
                <input
                  type="text"
                  value={newContract.title}
                  onChange={e => setNewContract({...newContract, title: e.target.value})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Name</label>
                  <input
                    type="text"
                    value={newContract.client_name}
                    onChange={e => setNewContract({...newContract, client_name: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Email *</label>
                  <input
                    type="email"
                    value={newContract.client_email}
                    onChange={e => setNewContract({...newContract, client_email: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contract Terms</label>
                <textarea
                  value={newContract.content}
                  onChange={e => setNewContract({...newContract, content: e.target.value})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200 font-mono text-sm"
                  rows={10}
                />
                <p className="text-xs text-gray-500 mt-1">You can use Markdown for formatting.</p>
              </div>

              <div className="flex justify-end pt-4 gap-3">
                 <button
                   onClick={() => setShowCreateModal(false)}
                   className="px-6 py-2 bg-gray-100 text-gray-700 rounded-full font-medium hover:bg-gray-200"
                 >
                   Cancel
                 </button>
                 <button
                   onClick={handleCreateContract}
                   className="px-6 py-2 bg-[#1D1D1F] text-white rounded-full font-medium hover:bg-black"
                 >
                   Create Draft
                 </button>
              </div>
            </div>
          </div>
        </div>
      )}
      <Footer />
    </div>
  );
}

